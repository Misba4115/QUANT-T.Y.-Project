"""Truthful provider capability and fallback metadata."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ProviderCapability:
    provider: str
    asset_types: tuple[str, ...]
    freshness: str
    licensed_exchange_grade: bool
    configured: bool
    fallback_provider: str | None
    limitations: tuple[str, ...]


CAPABILITIES = (
    ProviderCapability("yahoo_finance", ("Equity", "ETF"), "delayed", False, True, None, ("uncontracted_public_adapter", "single_provider")),
    ProviderCapability("mfapi", ("Mutual Fund",), "delayed", False, True, None, ("community_api", "single_provider")),
    ProviderCapability("coingecko", ("Crypto",), "live_or_delayed", False, True, None, ("rate_limited", "single_provider")),
)


def provider_capability_matrix() -> list[dict]:
    return [{**asdict(item), "status": "experimental"} for item in CAPABILITIES]
