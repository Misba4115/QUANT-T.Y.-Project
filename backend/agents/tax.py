"""Tax agent wrapper around the shared evidence-bound tax calculator."""
from __future__ import annotations

from typing import Any

from services.tax_analytics import calculate_tax_metrics


def run_tax_agent(user_id: str, db: Any) -> dict:
    return calculate_tax_metrics(user_id, db)
