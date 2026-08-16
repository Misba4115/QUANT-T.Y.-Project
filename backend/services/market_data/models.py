from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal

PriceStatus = Literal["live", "delayed", "stored", "stale", "unavailable"]


@dataclass(frozen=True)
class PriceQuote:
    asset_type: str
    instrument_key: str
    price: float | None
    currency: str
    provider: str
    observed_at: datetime | None
    fetched_at: datetime
    status: PriceStatus
    error: str | None = None

    def to_dict(self) -> dict:
        value = asdict(self)
        value["observed_at"] = self.observed_at.isoformat() if self.observed_at else None
        value["fetched_at"] = self.fetched_at.isoformat()
        return value
