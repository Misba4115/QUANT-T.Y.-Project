"""Deterministic connector used for contract and end-to-end tests."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.connectors.base import ConnectorCapabilities, NormalizedHolding


class SandboxConnector:
    provider = "sandbox"

    def __init__(self, holdings: list[dict[str, Any]] | None = None):
        self._holdings = holdings or []

    def get_capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(background_sync=True)

    def get_profile(self) -> dict[str, Any]:
        return {"user_id": "sandbox-user", "user_name": "Sandbox Investor"}

    def get_holdings(self) -> list[NormalizedHolding]:
        now = datetime.now(timezone.utc)
        return [
            NormalizedHolding(
                provider_item_id=str(row.get("provider_item_id") or row["symbol"]),
                asset_type=str(row.get("asset_type") or "equity"),
                instrument_key=str(row["symbol"]).upper(),
                name=str(row.get("name") or row["symbol"]),
                quantity=float(row["quantity"]),
                average_price=float(row["average_price"]),
                exchange=str(row.get("exchange") or "NSE"),
                isin=row.get("isin"),
                source_timestamp=now,
                raw_payload=dict(row),
            )
            for row in self._holdings
        ]

    def get_positions(self) -> list[dict[str, Any]]:
        return []

    def get_transactions(self, date_from: str, date_to: str) -> list[dict[str, Any]]:
        del date_from, date_to
        return []

    def get_orders(self) -> list[dict[str, Any]]:
        return []

    def revoke(self) -> None:
        return None
