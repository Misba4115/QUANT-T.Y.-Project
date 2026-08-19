"""Read-only, user-scoped financial context assembly with stable evidence IDs."""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from agents.contracts import ContextRequirement, ContextSection, ContextSnapshot, EvidenceRef


SECTION_TABLES: dict[ContextSection, tuple[str, ...]] = {
    "profile": ("users",),
    "goals": ("goals",),
    "risk": ("risk_assessments",),
    "cashflow": ("banking_accounts", "bank_transactions"),
    "holdings": ("equity_holdings", "mutual_fund_holdings", "etf_holdings", "crypto_holdings"),
    "transactions": ("equity_transactions", "mf_transactions", "etf_transactions", "crypto_transactions"),
    "guardian": ("guardian_alerts",),
    # Global quote cache is deliberately excluded; user-scoped history reveals only owned instruments.
    "market": ("market_price_history",),
    "conversation": ("conversation_summaries",),
    "preferences": ("user_preferences",),
}

ID_FIELDS = {
    "users": "user_id", "banking_accounts": "account_id", "bank_transactions": "bank_tx_id",
    "equity_holdings": "equity_holding_id", "mutual_fund_holdings": "mf_holding_id",
    "etf_holdings": "etf_holding_id", "crypto_holdings": "crypto_holding_id",
    "equity_transactions": "equity_tx_id", "mf_transactions": "mf_tx_id",
    "etf_transactions": "etf_tx_id", "crypto_transactions": "crypto_tx_id",
    "goals": "goal_id", "risk_assessments": "risk_assessment_id",
    "guardian_alerts": "guardian_alert_id", "market_price_cache": "price_cache_id",
    "market_price_history": "price_history_id", "conversation_summaries": "summary_id",
    "user_preferences": "user_preference_id",
}

DENIED_FIELDS = {
    "password_hash", "email", "name", "phone", "account_number", "demat_account",
    "wallet_address", "encrypted_credentials", "access_token", "refresh_token", "oauth_payload",
    "storage_key", "raw_content", "attachment_content",
}

SECTION_ALLOWED_FIELDS: dict[str, set[str]] = {
    "users": {"user_id", "age", "monthly_income", "monthly_expenses", "primary_goal", "risk_profile", "updated_at"},
    "bank_transactions": {"bank_tx_id", "account_id", "tx_date", "amount", "tx_type", "category", "is_anomaly", "anomaly_score", "anomaly_model_version", "created_at"},
    "conversation_summaries": {"summary_id", "conversation_id", "summary", "summary_version", "message_count", "updated_at"},
}


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=_json_default)


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        try:
            return datetime.combine(date.fromisoformat(str(value)), datetime.min.time(), tzinfo=timezone.utc)
        except (TypeError, ValueError):
            return None


class UserFinancialContextAssembler:
    def __init__(self, db: Any):
        self.db = db

    def assemble(self, user_id: str, requirement: ContextRequirement) -> ContextSnapshot:
        assembled_at = datetime.now(timezone.utc)
        sections: dict[str, list[dict[str, Any]]] = {}
        evidence: list[EvidenceRef] = []
        observed: list[datetime] = []
        missing: list[str] = []

        for section in sorted(requirement.required_sections):
            records: list[dict[str, Any]] = []
            for table in SECTION_TABLES[section]:
                rows = self._read_user_rows(table, user_id, requirement.max_records_per_section)
                for row in rows:
                    safe = self._safe_record(table, row)
                    records.append({"record_type": table, **safe})
                    reference = self._evidence(table, user_id, safe, assembled_at)
                    evidence.append(reference)
                    if reference.observed_at:
                        observed.append(reference.observed_at)
            records = sorted(records, key=_canonical)
            sections[section] = records
            if not records:
                missing.append(f"missing_{section}")

        blockers = self._blockers(requirement, missing)
        sections, evidence, compacted = self._compact(
            sections, evidence, requirement.max_serialized_chars
        )
        digest_payload = {
            "requirement": requirement.model_dump(mode="json"),
            "sections": sections,
            "evidence_ids": [item.evidence_id for item in evidence],
            "missing": missing,
        }
        context_version = "ctx:v1:" + hashlib.sha256(_canonical(digest_payload).encode()).hexdigest()
        return ContextSnapshot(
            context_version=context_version,
            user_id=user_id,
            assembled_at=assembled_at,
            data_as_of=max(observed) if observed else None,
            requirement=requirement,
            sections=sections,
            evidence=evidence,
            missing_context_codes=missing,
            blockers=blockers,
            compacted=compacted,
        )

    def _read_user_rows(self, table: str, user_id: str, limit: int) -> list[dict[str, Any]]:
        query = self.db.table(table).select("*").eq("user_id", user_id).limit(limit)
        return list(query.execute().data or [])

    @staticmethod
    def _safe_record(table: str, row: dict[str, Any]) -> dict[str, Any]:
        allowed = SECTION_ALLOWED_FIELDS.get(table)
        output = {}
        for key, value in row.items():
            if key == "user_id" or key in DENIED_FIELDS or key.lower().endswith(("_secret", "_password", "_token")):
                continue
            if allowed is not None and key not in allowed:
                continue
            output[key] = value
        return output

    @staticmethod
    def _evidence(table: str, user_id: str, row: dict[str, Any], retrieved_at: datetime) -> EvidenceRef:
        record_id = str(row.get(ID_FIELDS.get(table, "id"), "unknown"))
        content_hash = hashlib.sha256(_canonical(row).encode()).hexdigest()
        opaque_id = hashlib.sha256(f"{user_id}:{table}:{record_id}:{content_hash}".encode()).hexdigest()
        observed_at = next(
            (_parse_datetime(row.get(key)) for key in ("source_timestamp", "price_date", "tx_date", "assessed_at", "updated_at", "created_at") if row.get(key)),
            None,
        )
        evidence_type = "market_observation" if table.startswith("market_price") else "private_record"
        return EvidenceRef(
            evidence_id=f"private:{opaque_id}",
            evidence_type=evidence_type,
            source_name=table,
            record_locator=f"{table}:{record_id}",
            observed_at=observed_at,
            retrieved_at=retrieved_at,
            freshness="unknown",
            content_hash=content_hash,
        )

    @staticmethod
    def _blockers(requirement: ContextRequirement, missing: list[str]) -> list[str]:
        if not requirement.financial_action:
            return []
        important = {"missing_goals", "missing_risk", "missing_cashflow", "missing_holdings", "missing_transactions"}
        return sorted(f"decision_context_incomplete:{code}" for code in important.intersection(missing))

    @staticmethod
    def _compact(
        sections: dict[str, list[dict[str, Any]]],
        evidence: list[EvidenceRef],
        budget: int,
    ) -> tuple[dict[str, list[dict[str, Any]]], list[EvidenceRef], bool]:
        compacted = False
        while len(_canonical(sections)) > budget:
            candidates = [(len(rows), name) for name, rows in sections.items() if rows]
            if not candidates:
                break
            _, section = max(candidates)
            sections[section].pop()
            compacted = True
        retained = {
            (record["record_type"], str(record.get(ID_FIELDS.get(record["record_type"], "id"), "unknown")))
            for records in sections.values() for record in records
        }
        evidence = [
            item for item in evidence
            if tuple((item.record_locator or ":").split(":", 1)) in retained
        ]
        return sections, evidence, compacted
