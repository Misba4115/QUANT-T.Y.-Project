"""Provider-neutral, read-only broker connector contracts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Protocol


class ConnectorError(RuntimeError):
    pass


class AuthorizationRequired(ConnectorError):
    pass


@dataclass(frozen=True)
class ConnectorCapabilities:
    accounts: bool = True
    holdings: bool = True
    positions: bool = False
    transactions: bool = False
    orders_reconciliation: bool = False
    background_sync: bool = False
    requires_static_ip: bool = False

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedHolding:
    provider_item_id: str
    asset_type: str
    instrument_key: str
    name: str
    quantity: float
    average_price: float
    exchange: str | None
    isin: str | None
    source_timestamp: datetime | None
    raw_payload: dict[str, Any]

    def preview(self) -> dict[str, Any]:
        return {
            "provider_item_id": self.provider_item_id,
            "asset_type": self.asset_type,
            "instrument_key": self.instrument_key,
            "name": self.name,
            "quantity": self.quantity,
            "average_price": self.average_price,
            "exchange": self.exchange,
            "isin": self.isin,
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
        }


class BrokerConnector(Protocol):
    provider: str

    def get_capabilities(self) -> ConnectorCapabilities: ...
    def get_profile(self) -> dict[str, Any]: ...
    def get_holdings(self) -> list[NormalizedHolding]: ...
    def get_positions(self) -> list[dict[str, Any]]: ...
    def get_transactions(self, date_from: str, date_to: str) -> list[dict[str, Any]]: ...
    def get_orders(self) -> list[dict[str, Any]]: ...
    def revoke(self) -> None: ...
