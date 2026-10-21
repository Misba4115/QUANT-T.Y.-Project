"""Pure anomaly detector shared by the Guardian agent and its benchmark."""
from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import datetime
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest

TABLES = (
    "bank_transactions", "equity_transactions", "mf_transactions",
    "etf_transactions", "crypto_transactions",
)
MODEL_VERSION = "guardian-hybrid-v3"
RULE_VERSION = "guardian-large-amount-rule-v3"


def _description(row: dict[str, Any]) -> str:
    value = row.get("description") or row.get("merchant") or row.get("symbol") or ""
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()


def _timestamp(row: dict[str, Any]) -> datetime:
    raw = str(row.get("occurred_at") or row.get("date") or row.get("tx_date") or "1970-01-01")
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def detect_anomalies(
    records: list[tuple[str, dict[str, Any], float]],
) -> tuple[np.ndarray, np.ndarray, list[str], str, str]:
    """Flag review candidates from visible facts, then add conservative outliers.

    A date without a time cannot support an odd-hour decision. Exact duplicate
    candidates require the same description, account, amount and timestamp.
    """
    count = len(records)
    flags = np.zeros(count, dtype=bool)
    scores = np.zeros(count, dtype=float)
    reasons = ["" for _ in records]
    if not count:
        return flags, scores, reasons, "no_transactions", MODEL_VERSION

    values = np.asarray([max(0.0, value) for _, _, value in records], dtype=float)
    if count >= 20 and np.unique(values).size > 1:
        features = []
        for table, row, value in records:
            timestamp = _timestamp(row)
            weekday = timestamp.weekday()
            table_encoding = [float(table == candidate) for candidate in TABLES]
            features.append([
                np.log1p(max(0.0, value)),
                math.sin(2 * math.pi * weekday / 7),
                math.cos(2 * math.pi * weekday / 7),
                *table_encoding,
            ])
        model = IsolationForest(n_estimators=200, contamination="auto", random_state=42)
        matrix = np.asarray(features)
        model.fit(matrix)
        scores = model.decision_function(matrix)
        # The unsupervised score ranks review candidates, but it must not force
        # a fixed alert quota without a validation-calibrated threshold.
        flags = np.zeros(count, dtype=bool)
        reasons = ["" for _ in records]
        mode, version = "rules_with_isolation_score", MODEL_VERSION
    else:
        threshold = max(float(np.median(values)) * 3, 10_000)
        flags = values > threshold
        scores = np.where(flags, -1.0, 0.0)
        reasons = [f"Transaction value exceeds rule threshold of ₹{threshold:,.0f}" if flag else "" for flag in flags]
        mode, version = "rule_based_insufficient_sample", RULE_VERSION

    account_history: dict[str, list[int]] = defaultdict(list)
    for index, (_table, row, _value) in enumerate(records):
        account_history[str(row.get("account_id") or "")].append(index)

    rule_flags: dict[int, str] = {}
    for indices in account_history.values():
        indices.sort(key=lambda item: _timestamp(records[item][1]))
        prior_values: list[float] = []
        prior_by_description: dict[str, list[float]] = defaultdict(list)
        prior_by_category: dict[str, list[float]] = defaultdict(list)
        previous_by_signature: dict[tuple[str, float], datetime] = {}
        for index in indices:
            table, row, value = records[index]
            timestamp = _timestamp(row)
            raw_time = str(row.get("occurred_at") or row.get("date") or "")
            has_precise_time = "T" in raw_time or " " in raw_time
            description = _description(row)
            category = str(row.get("category") or "").casefold().strip()
            signature = (description, round(value, 2))

            previous = previous_by_signature.get(signature)
            if has_precise_time and previous and 0 <= (timestamp - previous).total_seconds() <= 180:
                rule_flags[index] = "Possible duplicate: same account, description and amount within three minutes"
            elif table == "bank_transactions" and ((row.get("occurred_at") or row.get("date")) or row.get("occurred_local_hour") is not None):
                hour = int(row["occurred_local_hour"]) if row.get("occurred_local_hour") is not None else timestamp.hour
                scheduled = any(term in description for term in ("emi", "loan installment", "scheduled mandate"))
                if 1 <= hour < 5 and not scheduled:
                    rule_flags[index] = "Bank transaction occurred during an unusual hour"

            same_description = prior_by_description[description]
            comparison_values = same_description if len(same_description) >= 2 else prior_by_category.get(category, [])
            if len(comparison_values) >= 3:
                baseline = float(np.median(comparison_values))
                if value >= max(5_000.0, baseline * 9):
                    rule_flags[index] = "Transaction amount is at least nine times its merchant baseline"

            if category == "transfer" and value >= 50_000 and value % 5_000 == 0:
                earlier_transfers = prior_by_category[category]
                if not earlier_transfers or max(earlier_transfers) <= 7_500:
                    rule_flags[index] = "Large round transfer is inconsistent with earlier transfer history"

            if category in {"shopping", "entertainment", "other"} and category not in prior_by_category and len(prior_values) >= 20:
                account_median = float(np.median(prior_values))
                if value >= max(5_000.0, account_median * 5):
                    rule_flags[index] = "First-seen transaction category has an unusually large amount"

            prior_values.append(value)
            prior_by_description[description].append(value)
            if category:
                prior_by_category[category].append(value)
            if has_precise_time:
                previous_by_signature[signature] = timestamp

    for index, (_table, _row, _value) in enumerate(records):
        if index in rule_flags:
            flags[index] = True
            reasons[index] = rule_flags[index]
            scores[index] = min(scores[index], -1.0)
    return flags, scores, reasons, mode, version
