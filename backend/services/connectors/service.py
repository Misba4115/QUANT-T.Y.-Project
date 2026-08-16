"""OAuth state, connector lifecycle, preview, and idempotent synchronization."""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import uuid4

from core.config import get_settings
from repositories.base import SupabaseRepository
from services.connectors.base import AuthorizationRequired, BrokerConnector, ConnectorError, NormalizedHolding
from services.connectors.sandbox import SandboxConnector
from services.connectors.upstox import UpstoxConnector
from services.secrets import SecretBox


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _fingerprint(provider: str, holding: NormalizedHolding) -> str:
    canonical = {
        "provider": provider,
        "provider_item_id": holding.provider_item_id,
        "asset_type": holding.asset_type,
        "instrument": holding.instrument_key,
        "quantity": round(holding.quantity, 8),
        "average_price": round(holding.average_price, 6),
    }
    return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode("utf-8")).hexdigest()


class ConnectorService:
    def __init__(
        self,
        db: Any,
        *,
        secret_box: SecretBox | None = None,
        connector_factory: Callable[[dict[str, Any]], BrokerConnector] | None = None,
    ):
        self.db = db
        self.repo = SupabaseRepository(db)
        self.settings = get_settings()
        self.secret_box = secret_box or SecretBox()
        self.connector_factory = connector_factory

    def list_accounts(self, user_id: str) -> list[dict[str, Any]]:
        return [self._public_account(row) for row in self.repo.list_for_user("connector_accounts", user_id)]

    def begin_upstox_authorization(self, user_id: str) -> dict[str, str]:
        if not self.settings.upstox_client_id or not self.settings.upstox_client_secret:
            raise ConnectorError("Upstox is not configured by the application operator")
        state = secrets.token_urlsafe(32)
        self.db.table("connector_oauth_states").insert(
            {
                "oauth_state_id": str(uuid4()),
                "user_id": user_id,
                "provider": "upstox",
                "state_hash": _hash(state),
                "expires_at": (_utcnow() + timedelta(minutes=10)).isoformat(),
            }
        ).execute()
        return {
            "provider": "upstox",
            "authorization_url": UpstoxConnector.authorization_url(
                self.settings.upstox_client_id, self.settings.upstox_redirect_uri, state
            ),
        }

    def complete_upstox_authorization(self, code: str, state: str) -> tuple[str, dict[str, Any]]:
        rows = self.repo.find("connector_oauth_states", [("state_hash", _hash(state)), ("provider", "upstox")], limit=1)
        if not rows:
            raise ConnectorError("OAuth state is invalid")
        row = rows[0]
        expiry = datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
        if row.get("consumed_at") or expiry <= _utcnow():
            raise ConnectorError("OAuth state has expired or was already used")
        self.db.table("connector_oauth_states").update({"consumed_at": _utcnow().isoformat()}).eq(
            "oauth_state_id", row["oauth_state_id"]
        ).execute()
        token = UpstoxConnector.exchange_code(
            code=code,
            client_id=str(self.settings.upstox_client_id),
            client_secret=str(self.settings.upstox_client_secret),
            redirect_uri=self.settings.upstox_redirect_uri,
        )
        connector = UpstoxConnector(str(token["access_token"]))
        profile = connector.get_profile()
        provider_account_id = str(profile.get("user_id") or profile.get("user_code") or "unknown")
        account = self._upsert_account(
            user_id=row["user_id"],
            provider="upstox",
            provider_account_id=provider_account_id,
            display_name=str(profile.get("user_name") or "Upstox account"),
            capabilities=connector.get_capabilities().to_dict(),
            credentials={"access_token": token["access_token"]},
            capability_mode="interactive",
        )
        return row["user_id"], self._public_account(account)

    def create_sandbox_account(self, user_id: str, holdings: list[dict[str, Any]]) -> dict[str, Any]:
        if self.settings.quant_env == "production":
            raise ConnectorError("Sandbox connectors are disabled in production")
        connector = SandboxConnector(holdings)
        row = self._upsert_account(
            user_id=user_id,
            provider="sandbox",
            provider_account_id="sandbox-user",
            display_name="Sandbox portfolio",
            capabilities=connector.get_capabilities().to_dict(),
            credentials={"holdings": holdings},
            capability_mode="sandbox",
        )
        return self._public_account(row)

    def preview_sync(self, connector_account_id: str, user_id: str) -> dict[str, Any]:
        account = self.repo.get_for_user("connector_accounts", connector_account_id, user_id)
        if not account or account.get("status") == "revoked":
            raise ConnectorError("Connector account was not found or is revoked")
        connector = self._connector(account)
        try:
            holdings = connector.get_holdings()
        except AuthorizationRequired as exc:
            self.db.table("connector_accounts").update(
                {"status": "reauthorization_required", "last_error": str(exc), "updated_at": _utcnow().isoformat()}
            ).eq("connector_account_id", connector_account_id).eq("user_id", user_id).execute()
            raise

        existing = {
            ("equity", str(row.get("symbol") or "").upper()): row
            for row in self.repo.list_for_user("equity_holdings", user_id)
        }
        existing.update({
            ("mf", str(row.get("scheme_code") or row.get("isin") or "").upper()): row
            for row in self.repo.list_for_user("mutual_fund_holdings", user_id)
        })
        preview: list[dict[str, Any]] = []
        counts = {"additions": 0, "updates": 0, "duplicates": 0, "conflicts": 0}
        sync_run_id = str(uuid4())
        self.db.table("connector_sync_runs").insert(
            {
                "connector_sync_run_id": sync_run_id,
                "user_id": user_id,
                "connector_account_id": connector_account_id,
                "status": "preview",
                **counts,
                "preview": [],
            }
        ).execute()
        for holding in holdings:
            key = ("mf" if holding.asset_type in {"mf", "mutual_fund"} else "equity", holding.instrument_key.upper())
            current = existing.get(key)
            action = "add"
            if current:
                quantity_key = "units" if key[0] == "mf" else "quantity"
                average_key = "avg_nav" if key[0] == "mf" else "avg_price"
                same = abs(float(current.get(quantity_key) or 0) - holding.quantity) < 1e-8 and abs(
                    float(current.get(average_key) or 0) - holding.average_price
                ) < 1e-6
                action = "duplicate" if same else "update"
            counts[{"add": "additions", "update": "updates", "duplicate": "duplicates"}[action]] += 1
            item = {**holding.preview(), "action": action, "fingerprint": _fingerprint(account["provider"], holding)}
            preview.append(item)
            self.db.table("connector_sync_items").insert(
                {
                    "connector_sync_item_id": str(uuid4()),
                    "user_id": user_id,
                    "connector_sync_run_id": sync_run_id,
                    "provider_item_id": holding.provider_item_id,
                    "fingerprint": item["fingerprint"],
                    "canonical_table": "mutual_fund_holdings" if key[0] == "mf" else "equity_holdings",
                    "action": action,
                    "source_timestamp": item.get("source_timestamp"),
                    "raw_payload": holding.raw_payload,
                    "purge_after": (_utcnow() + timedelta(days=30)).isoformat(),
                }
            ).execute()
        self.db.table("connector_sync_runs").update({**counts, "preview": preview}).eq(
            "connector_sync_run_id", sync_run_id
        ).eq("user_id", user_id).execute()
        return {"connector_sync_run_id": sync_run_id, "status": "preview", **counts, "preview": preview}

    def commit_sync(self, sync_run_id: str, user_id: str) -> dict[str, Any]:
        run = self.repo.get_for_user("connector_sync_runs", sync_run_id, user_id)
        if not run:
            raise ConnectorError("Sync preview not found")
        if run.get("status") == "completed":
            return self._public_sync(run)
        if run.get("status") != "preview":
            raise ConnectorError("Only a preview sync can be committed")
        account = self.repo.get_for_user("connector_accounts", run["connector_account_id"], user_id)
        if not account:
            raise ConnectorError("Connector account not found")
        self.db.table("connector_sync_runs").update({"status": "processing"}).eq(
            "connector_sync_run_id", sync_run_id
        ).eq("user_id", user_id).execute()
        errors: list[str] = []
        for item in run.get("preview") or []:
            if item["action"] == "duplicate":
                continue
            try:
                self._commit_holding(account, item, user_id)
                from services.guardian_stream import GuardianStreamService

                occurred = _utcnow()
                if item.get("source_timestamp"):
                    occurred = datetime.fromisoformat(str(item["source_timestamp"]).replace("Z", "+00:00"))
                    if occurred.tzinfo is None:
                        occurred = occurred.replace(tzinfo=timezone.utc)
                GuardianStreamService(self.db).ingest(
                    user_id=user_id,
                    event_id=f"connector:{account['provider']}:{item['fingerprint']}",
                    asset_type="mutual_fund" if item["asset_type"] in {"mf", "mutual_fund"} else "equity",
                    event_type="holding_synchronized",
                    occurred_at=occurred,
                    payload={"quantity": item["quantity"], "amount": float(item["quantity"]) * float(item["average_price"]), "source": account["provider"]},
                    enqueue=False,
                )
            except Exception as exc:
                errors.append(f"{item.get('instrument_key')}: {exc}")
        status = "partial" if errors else "completed"
        completed = _utcnow().isoformat()
        updated = self.db.table("connector_sync_runs").update(
            {"status": status, "error": "; ".join(errors) or None, "completed_at": completed}
        ).eq("connector_sync_run_id", sync_run_id).eq("user_id", user_id).execute().data[0]
        if status == "completed":
            self.db.table("connector_accounts").update(
                {"status": "connected", "last_successful_sync_at": completed, "last_error": None, "updated_at": completed}
            ).eq("connector_account_id", account["connector_account_id"]).eq("user_id", user_id).execute()
            from services.jobs import JobService

            JobService(self.db).enqueue_once("price_sync", user_id, {"reason": "connector_material_change"})
            JobService(self.db).enqueue_once("guardian_events", user_id, {"connector_sync_run_id": sync_run_id})
        return self._public_sync(updated)

    def revoke(self, connector_account_id: str, user_id: str) -> None:
        account = self.repo.get_for_user("connector_accounts", connector_account_id, user_id)
        if not account:
            raise ConnectorError("Connector account not found")
        try:
            self._connector(account).revoke()
        finally:
            self.db.table("connector_accounts").update(
                {"status": "revoked", "encrypted_credentials": None, "updated_at": _utcnow().isoformat()}
            ).eq("connector_account_id", connector_account_id).eq("user_id", user_id).execute()

    def _connector(self, account: dict[str, Any]) -> BrokerConnector:
        if self.connector_factory:
            return self.connector_factory(account)
        credentials = self.secret_box.decrypt_json(account["encrypted_credentials"])
        if account["provider"] == "upstox":
            return UpstoxConnector(credentials["access_token"])
        if account["provider"] == "sandbox":
            return SandboxConnector(credentials.get("holdings") or [])
        raise ConnectorError(f"Unsupported connector provider: {account['provider']}")

    def _upsert_account(self, **values: Any) -> dict[str, Any]:
        user_id = values.pop("user_id")
        provider = values["provider"]
        provider_account_id = values["provider_account_id"]
        credentials = values.pop("credentials")
        payload = {
            **values,
            "user_id": user_id,
            "status": "connected",
            "encrypted_credentials": self.secret_box.encrypt_json(credentials),
            "updated_at": _utcnow().isoformat(),
        }
        rows = self.repo.find(
            "connector_accounts",
            [("user_id", user_id), ("provider", provider), ("provider_account_id", provider_account_id)],
            limit=1,
        )
        if rows:
            result = self.db.table("connector_accounts").update(payload).eq(
                "connector_account_id", rows[0]["connector_account_id"]
            ).eq("user_id", user_id).execute()
        else:
            payload["connector_account_id"] = str(uuid4())
            result = self.db.table("connector_accounts").insert(payload).execute()
        if not result.data:
            raise ConnectorError("Connector account could not be stored")
        return result.data[0]

    def _commit_holding(self, account: dict[str, Any], item: dict[str, Any], user_id: str) -> None:
        provider_label = account["provider"].title()
        if item["asset_type"] in {"mf", "mutual_fund"}:
            table, id_field, key_field = "mutual_fund_holdings", "mf_holding_id", "scheme_code"
            payload = {
                "mf_name": item["name"], "scheme_code": item["instrument_key"], "isin": item.get("isin"),
                "units": item["quantity"], "avg_nav": item["average_price"], "platform": provider_label,
                "source_provider": account["provider"], "source_provider_item_id": item["provider_item_id"],
                "source_timestamp": item.get("source_timestamp"),
            }
        else:
            table, id_field, key_field = "equity_holdings", "equity_holding_id", "symbol"
            exchange = item.get("exchange") if item.get("exchange") in {"NSE", "BSE"} else "NSE"
            payload = {
                "symbol": item["instrument_key"], "equity_name": item["name"], "exchange": exchange,
                "quantity": item["quantity"], "avg_price": item["average_price"], "broker": provider_label,
                "source_provider": account["provider"], "source_provider_item_id": item["provider_item_id"],
                "source_timestamp": item.get("source_timestamp"),
            }
        rows = self.repo.find(table, [("user_id", user_id), (key_field, item["instrument_key"])], limit=1)
        if rows:
            self.db.table(table).update(payload).eq(id_field, rows[0][id_field]).eq("user_id", user_id).execute()
        else:
            self.db.table(table).insert({**payload, "user_id": user_id}).execute()

    @staticmethod
    def _public_account(row: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in row.items() if key not in {"encrypted_credentials"}}

    @staticmethod
    def _public_sync(row: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in row.items() if key not in {"cursor_before", "cursor_after"}}
