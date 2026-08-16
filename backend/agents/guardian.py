"""Cross-asset anomaly detection with persisted evidence and model metadata."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest

from repositories.base import SupabaseRepository, TABLES

TABLES_TO_ANALYZE = [
    "bank_transactions", "equity_transactions", "mf_transactions", "etf_transactions", "crypto_transactions"
]
MODEL_VERSION = "guardian-isolation-forest-v1"
RULE_VERSION = "guardian-large-amount-rule-v1"


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

    values = np.array([value for _table, _row, value in records], dtype=float)
    flags = np.zeros(len(records), dtype=bool)
    scores = np.zeros(len(records), dtype=float)
    reasons = ["" for _ in records]
    if len(records) >= 20 and np.unique(values).size > 1:
        features = []
        for table, row, value in records:
            tx_date = str(row.get("tx_date") or "1970-01-01")
            weekday = datetime.fromisoformat(tx_date[:10]).weekday()
            table_index = TABLES_TO_ANALYZE.index(table)
            features.append([np.log1p(value), weekday, table_index])
        model = IsolationForest(n_estimators=200, contamination="auto", random_state=42)
        predictions = model.fit_predict(np.asarray(features))
        scores = model.decision_function(np.asarray(features))
        flags = predictions == -1
        reasons = ["Isolation Forest outlier across amount, weekday, and asset type" if flag else "" for flag in flags]
        model_version = MODEL_VERSION
        mode = "isolation_forest"
    else:
        median = float(np.median(values))
        threshold = max(median * 3, 10_000)
        flags = values > threshold
        scores = np.where(flags, -1.0, 0.0)
        reasons = [f"Transaction value exceeds transparent rule threshold of ₹{threshold:,.0f}" if flag else "" for flag in flags]
        model_version = RULE_VERSION
        mode = "rule_based_insufficient_sample"

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
