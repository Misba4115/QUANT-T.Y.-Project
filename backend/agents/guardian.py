"""Cross-asset anomaly detection with persisted evidence and model metadata."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from repositories.base import SupabaseRepository, TABLES
from services.guardian_detector import detect_anomalies

TABLES_TO_ANALYZE = [
    "bank_transactions", "equity_transactions", "mf_transactions", "etf_transactions", "crypto_transactions"
]


def _transaction_value(table: str, row: dict[str, Any]) -> float:
    if table == "bank_transactions":
        return float(row.get("amount") or 0)
    quantity = float(row.get("units") or row.get("quantity") or 0)
    price = float(row.get("nav") or row.get("price") or 0)
    return abs(quantity * price)


def run_guardian(user_id: str, db: Any) -> dict:
    repo = SupabaseRepository(db)
    records: list[tuple[str, dict[str, Any], float]] = []
    for table in TABLES_TO_ANALYZE:
        for row in repo.list_for_user(table, user_id):
            records.append((table, row, _transaction_value(table, row)))

    for table, row, _value in records:
        db.table(table).update(
            {"is_anomaly": False, "anomaly_score": None, "anomaly_model_version": None, "anomaly_detected_at": None}
        ).eq(TABLES[table].id_field, row[TABLES[table].id_field]).eq("user_id", user_id).execute()

    if not records:
        return {"agent": "guardian", "status": "no_transactions", "anomaly_count": 0, "alerts": [], "model_version": None}

    flags, scores, reasons, mode, model_version = detect_anomalies(records)

    alerts = []
    detected_at = datetime.now(timezone.utc).isoformat()
    for index, (table, row, value) in enumerate(records):
        if not flags[index]:
            continue
        id_field = TABLES[table].id_field
        db.table(table).update(
            {
                "is_anomaly": True,
                "anomaly_score": float(scores[index]),
                "anomaly_model_version": model_version,
                "anomaly_detected_at": detected_at,
            }
        ).eq(id_field, row[id_field]).eq("user_id", user_id).execute()
        alerts.append(
            {
                "tx_id": row[id_field],
                "table": table,
                "value": round(value, 2),
                "reason": reasons[index],
                "score": float(scores[index]),
            }
        )
    return {
        "agent": "guardian",
        "status": "available",
        "mode": mode,
        "sample_count": len(records),
        "anomaly_count": len(alerts),
        "alerts": alerts,
        "model_version": model_version,
    }
