"""Small user-scoped repository layer over the synchronous Supabase client."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


class RepositoryError(RuntimeError):
    pass


@dataclass(frozen=True)
class TableSpec:
    table: str
    id_field: str


TABLES: dict[str, TableSpec] = {
    "users": TableSpec("users", "user_id"),
    "banking_accounts": TableSpec("banking_accounts", "account_id"),
    "equity_holdings": TableSpec("equity_holdings", "equity_holding_id"),
    "mutual_fund_holdings": TableSpec("mutual_fund_holdings", "mf_holding_id"),
    "etf_holdings": TableSpec("etf_holdings", "etf_holding_id"),
    "crypto_holdings": TableSpec("crypto_holdings", "crypto_holding_id"),
    "bank_transactions": TableSpec("bank_transactions", "bank_tx_id"),
    "equity_transactions": TableSpec("equity_transactions", "equity_tx_id"),
    "mf_transactions": TableSpec("mf_transactions", "mf_tx_id"),
    "etf_transactions": TableSpec("etf_transactions", "etf_tx_id"),
    "crypto_transactions": TableSpec("crypto_transactions", "crypto_tx_id"),
    "goals": TableSpec("goals", "goal_id"),
    "chat_conversations": TableSpec("chat_conversations", "conversation_id"),
    "chat_messages": TableSpec("chat_messages", "message_id"),
    "dashboard_runs": TableSpec("dashboard_runs", "run_id"),
    "portfolio_snapshots": TableSpec("portfolio_snapshots", "snapshot_id"),
    "dashboard_configs": TableSpec("dashboard_configs", "dashboard_config_id"),
    "import_batches": TableSpec("import_batches", "import_batch_id"),
    "market_price_cache": TableSpec("market_price_cache", "price_cache_id"),
    "market_price_history": TableSpec("market_price_history", "price_history_id"),
    "connector_accounts": TableSpec("connector_accounts", "connector_account_id"),
    "connector_oauth_states": TableSpec("connector_oauth_states", "oauth_state_id"),
    "connector_sync_runs": TableSpec("connector_sync_runs", "connector_sync_run_id"),
    "connector_sync_items": TableSpec("connector_sync_items", "connector_sync_item_id"),
    "ingestion_inboxes": TableSpec("ingestion_inboxes", "ingestion_inbox_id"),
    "ingestion_messages": TableSpec("ingestion_messages", "ingestion_message_id"),
    "notifications": TableSpec("notifications", "notification_id"),
    "notification_deliveries": TableSpec("notification_deliveries", "notification_delivery_id"),
    "notification_preferences": TableSpec("notification_preferences", "notification_preference_id"),
    "job_schedules": TableSpec("job_schedules", "job_schedule_id"),
    "job_runs": TableSpec("job_runs", "job_run_id"),
    "guardian_events": TableSpec("guardian_events", "guardian_event_id"),
    "guardian_alerts": TableSpec("guardian_alerts", "guardian_alert_id"),
    "guardian_feedback": TableSpec("guardian_feedback", "guardian_feedback_id"),
    "risk_assessments": TableSpec("risk_assessments", "risk_assessment_id"),
    "user_preferences": TableSpec("user_preferences", "user_preference_id"),
    "report_exports": TableSpec("report_exports", "report_export_id"),
    "analytics_runs": TableSpec("analytics_runs", "analytics_run_id"),
    "knowledge_sources": TableSpec("knowledge_sources", "source_id"),
    "knowledge_document_versions": TableSpec("knowledge_document_versions", "knowledge_version_id"),
    "knowledge_reviews": TableSpec("knowledge_reviews", "knowledge_review_id"),
    "conversation_summaries": TableSpec("conversation_summaries", "summary_id"),
    "outcome_evaluations": TableSpec("outcome_evaluations", "outcome_evaluation_id"),
}


def _data(result: Any) -> list[dict[str, Any]]:
    return list(getattr(result, "data", None) or [])


class SupabaseRepository:
    def __init__(self, client: Any):
        self.client = client

    def list_for_user(
        self,
        table: str,
        user_id: str,
        *,
        order_by: str | None = None,
        descending: bool = False,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        query = self.client.table(table).select("*").eq("user_id", user_id)
        if order_by:
            query = query.order(order_by, desc=descending)
        if limit is not None:
            query = query.limit(limit)
        return _data(query.execute())

    def get_for_user(self, table: str, record_id: str, user_id: str) -> dict[str, Any] | None:
        spec = TABLES[table]
        rows = _data(
            self.client.table(table)
            .select("*")
            .eq(spec.id_field, record_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return rows[0] if rows else None

    def create_for_user(self, table: str, user_id: str, values: dict[str, Any]) -> dict[str, Any]:
        payload = {**values, "user_id": user_id}
        rows = _data(self.client.table(table).insert(payload).execute())
        if not rows:
            raise RepositoryError(f"Insert into {table} did not return a row")
        return rows[0]

    def update_for_user(
        self,
        table: str,
        record_id: str,
        user_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any] | None:
        spec = TABLES[table]
        if not values:
            return self.get_for_user(table, record_id, user_id)
        rows = _data(
            self.client.table(table)
            .update(values)
            .eq(spec.id_field, record_id)
            .eq("user_id", user_id)
            .execute()
        )
        return rows[0] if rows else None

    def delete_for_user(self, table: str, record_id: str, user_id: str) -> bool:
        spec = TABLES[table]
        rows = _data(
            self.client.table(table)
            .delete()
            .eq(spec.id_field, record_id)
            .eq("user_id", user_id)
            .execute()
        )
        return bool(rows)

    def find(self, table: str, filters: Iterable[tuple[str, Any]], *, limit: int | None = None) -> list[dict[str, Any]]:
        query = self.client.table(table).select("*")
        for field, value in filters:
            query = query.eq(field, value)
        if limit is not None:
            query = query.limit(limit)
        return _data(query.execute())


def get_repository(client: Any) -> SupabaseRepository:
    return SupabaseRepository(client)
