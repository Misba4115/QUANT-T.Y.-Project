"""Read-only comparison of the configured Supabase REST schema and QUANT runtime needs."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Final

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import get_settings


EXPECTED: Final[dict[str, set[str]]] = {
    "users": {"user_id", "email", "password_hash", "name", "phone", "age", "monthly_income", "monthly_expenses", "primary_goal", "risk_profile", "created_at", "updated_at"},
    "banking_accounts": {"account_id", "user_id", "account_type", "account_name", "institution", "account_number", "current_balance", "currency", "is_primary", "import_batch_id", "source_row_hash", "created_at", "updated_at"},
    "equity_holdings": {"equity_holding_id", "user_id", "symbol", "equity_name", "exchange", "quantity", "avg_price", "broker", "demat_account", "current_price", "current_value", "price_source", "source_timestamp", "last_synced_at", "import_batch_id", "source_row_hash", "created_at", "updated_at"},
    "mutual_fund_holdings": {"mf_holding_id", "user_id", "mf_name", "scheme_code", "isin", "fund_house", "category", "units", "avg_nav", "platform", "folio_number", "current_nav", "current_value", "price_source", "source_timestamp", "last_synced_at", "import_batch_id", "source_row_hash", "created_at", "updated_at"},
    "etf_holdings": {"etf_holding_id", "user_id", "symbol", "etf_name", "isin", "exchange", "category", "quantity", "avg_price", "broker", "demat_account", "current_price", "current_value", "price_source", "source_timestamp", "last_synced_at", "import_batch_id", "source_row_hash", "created_at", "updated_at"},
    "crypto_holdings": {"crypto_holding_id", "user_id", "symbol", "crypto_name", "network", "quantity", "avg_price", "exchange", "wallet_address", "current_price", "current_value", "price_source", "source_timestamp", "last_synced_at", "import_batch_id", "source_row_hash", "created_at", "updated_at"},
    "goals": {"goal_id", "user_id", "goal_name", "goal_type", "target_amount", "current_saved", "target_date", "import_batch_id", "source_row_hash", "created_at", "updated_at"},
    "bank_transactions": {"bank_tx_id", "user_id", "account_id", "tx_date", "description", "amount", "tx_type", "category", "source", "source_row_hash", "import_batch_id", "is_anomaly", "anomaly_score", "anomaly_model_version", "anomaly_detected_at", "created_at"},
    "equity_transactions": {"equity_tx_id", "user_id", "tx_date", "symbol", "quantity", "price", "tx_type", "fees", "source", "source_row_hash", "import_batch_id", "is_anomaly", "anomaly_score", "anomaly_model_version", "anomaly_detected_at", "created_at"},
    "mf_transactions": {"mf_tx_id", "user_id", "tx_date", "scheme_code", "mf_name", "units", "nav", "tx_type", "source", "source_row_hash", "import_batch_id", "is_anomaly", "anomaly_score", "anomaly_model_version", "anomaly_detected_at", "created_at"},
    "etf_transactions": {"etf_tx_id", "user_id", "tx_date", "symbol", "quantity", "price", "tx_type", "fees", "source", "source_row_hash", "import_batch_id", "is_anomaly", "anomaly_score", "anomaly_model_version", "anomaly_detected_at", "created_at"},
    "crypto_transactions": {"crypto_tx_id", "user_id", "tx_date", "symbol", "quantity", "price", "tx_type", "fees", "source", "source_row_hash", "import_batch_id", "is_anomaly", "anomaly_score", "anomaly_model_version", "anomaly_detected_at", "created_at"},
    "chat_conversations": {"conversation_id", "user_id", "conversation_title", "created_at", "updated_at"},
    "chat_messages": {"message_id", "conversation_id", "role", "content", "metadata", "created_at"},
    "import_batches": {"import_batch_id", "user_id", "filename", "content_hash", "source_type", "target_type", "parser_version", "status", "preview_rows", "column_mapping", "valid_count", "error_count", "committed_count", "error_message", "created_at", "updated_at"},
    "import_row_errors": {"import_row_error_id", "import_batch_id", "row_number", "code", "message", "raw_row", "created_at"},
    "market_price_cache": {"price_cache_id", "asset_type", "instrument_key", "price", "currency", "provider", "source_timestamp", "fetched_at", "status"},
    "price_sync_runs": {"price_sync_run_id", "user_id", "status", "requested_count", "updated_count", "failed_count", "errors", "started_at", "completed_at"},
    "portfolio_snapshots": {"snapshot_id", "user_id", "snapshot_date", "net_worth", "allocation", "valuation_coverage", "source_status", "created_at"},
    "market_price_history": {"price_history_id", "user_id", "asset_type", "instrument_key", "price_date", "adjusted_close", "currency", "provider", "fetched_at"},
    "dashboard_runs": {"run_id", "user_id", "status", "params", "result", "error", "processing_time_ms", "created_at", "completed_at"},
    "dashboard_configs": {"dashboard_config_id", "user_id", "widgets", "time_period", "updated_at"},
}


def main() -> None:
    settings = get_settings()
    if not settings.database_configured:
        raise SystemExit("Supabase is not configured")
    headers = {
        "apikey": settings.supabase_runtime_key,
        "Authorization": f"Bearer {settings.supabase_runtime_key}",
        "Accept": "application/openapi+json",
    }
    started = time.perf_counter()
    response = httpx.get(f"{settings.supabase_url.rstrip('/')}/rest/v1/", headers=headers, timeout=30)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    response.raise_for_status()
    document = response.json()
    definitions = document.get("definitions", {})
    missing_tables: list[str] = []
    missing_columns: dict[str, list[str]] = {}
    for table, expected_columns in EXPECTED.items():
        definition = definitions.get(table)
        if not definition:
            missing_tables.append(table)
            continue
        actual_columns = set((definition.get("properties") or {}).keys())
        absent = sorted(expected_columns - actual_columns)
        if absent:
            missing_columns[table] = absent
    result = {
        "connected": True,
        "latency_ms": elapsed_ms,
        "expected_table_count": len(EXPECTED),
        "present_table_count": len(EXPECTED) - len(missing_tables),
        "missing_tables": missing_tables,
        "missing_columns": missing_columns,
        "ignored_legacy_objects": ["document_embeddings", "match_documents"],
        "limitations": ["RLS policies, indexes, foreign keys, triggers, and extensions are not exposed by PostgREST OpenAPI."],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
