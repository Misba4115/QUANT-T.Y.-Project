"""Calendar-correct 12-month cashflow agent."""
from typing import Any

from repositories.base import SupabaseRepository
from services.dashboard_aggregator import DashboardAggregator


def run_cashflow_agent(user_id: str, db: Any) -> dict:
    rows = SupabaseRepository(db).list_for_user(
        "bank_transactions", user_id, order_by="tx_date", descending=True
    )
    result = DashboardAggregator._cashflow(rows)
    result.update(
        {
            "agent": "cashflow",
            "status": "available",
            "transaction_count": len(rows),
            "category_confidence": "deterministic_or_user_confirmed",
        }
    )
    return result
