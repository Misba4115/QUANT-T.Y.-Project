"""
Guardian Agent — Anomaly Detection using Isolation Forest
"""
# from sklearn.ensemble import IsolationForest
# import pandas as pd
# from db.postgres import get_db  # will use in actual implementation


def run_guardian(user_id: str, db) -> dict:
    """
    Detect anomalous transactions across all transaction tables for a given user.

    Steps:
      1. Fetch all equity, MF, ETF, crypto, and bank transactions for user_id
      2. Build a feature matrix: [amount, day_of_week, category_encoded, ...]
      3. Fit IsolationForest (contamination=0.05)
      4. Flag rows with score < threshold as anomalies
      5. Update is_anomaly=True and anomaly_score in the respective DB tables
      6. Return list of flagged transactions for the dashboard alerts panel

    Returns:
        {
            "anomaly_count": int,
            "alerts": [{"tx_id": ..., "table": ..., "amount": ..., "reason": ...}]
        }

    TODO: implement
    """
    raise NotImplementedError("Guardian agent not implemented yet")
