"""Measured provider probes with secret-safe error reporting."""
from __future__ import annotations

from time import perf_counter


def probe_provider(provider, instrument: str, **metadata) -> dict:
    started = perf_counter()
    quote = provider.fetch(instrument, **metadata)
    latency_ms = round((perf_counter() - started) * 1000)
    return {
        "provider": provider.name,
        "status": "available" if quote.price is not None else "provider_unavailable",
        "reason_code": "probe_passed" if quote.price is not None else "probe_failed",
        "latency_ms": latency_ms,
        "observed_at": quote.observed_at.isoformat() if quote.observed_at else None,
        "fetched_at": quote.fetched_at.isoformat(),
        "freshness": quote.status,
        "retryable": quote.price is None,
        "error_class": quote.error,
    }
