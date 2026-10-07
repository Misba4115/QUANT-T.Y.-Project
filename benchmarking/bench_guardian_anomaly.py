"""
Benchmark: Guardian Anomaly Detection
======================================
Runs Guardian's detector logic (the standalone rule-based + IsolationForest
core extracted from agents/guardian.py) on every transaction in
guardian_anomaly_test_set.json, then computes:
  - Precision, Recall, F1
  - ROC-AUC
  - False-Positive Rate
  - Per-anomaly-type breakdown

Results are written to results/guardian_anomaly_results.json

HOW TO RUN (from the repo root):
    python benchmarking/bench_guardian_anomaly.py

No database connection is required — the script runs the detection logic
directly, bypassing the DB persistence layer.

IMPORTANT: The production guardian (agents/guardian.py) uses IsolationForest
only when >= 20 samples exist with diverse values; otherwise it falls back to a
median-based rule.  The test set has 510 transactions, so IsolationForest will
run.  However, the model sees the full corpus at once (no per-user history), so
scores reflect an unsupervised model trained on the test set itself — exactly as
it would run in production for a user whose 510 transactions were fed in.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

# -- File paths ---------------------------------------------------------------
TEST_SET_PATH = Path(__file__).parent / "guardian_anomaly_test_set.json"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_PATH = RESULTS_DIR / "guardian_anomaly_results.json"

# -- Detection logic (mirrors agents/guardian.py, DB-free) --------------------

MODEL_VERSION = "guardian-isolation-forest-v1"
RULE_VERSION = "guardian-large-amount-rule-v1"


def _build_features(transactions: list[dict]) -> np.ndarray:
    features = []
    for tx in transactions:
        amount = float(tx.get("amount") or 0)
        date_str = str(tx.get("date") or "1970-01-01")
        weekday = datetime.fromisoformat(date_str[:10]).weekday()
        # table_index is always 0 for bank_transactions in this test set
        features.append([np.log1p(amount), weekday, 0])
    return np.asarray(features, dtype=float)


def run_detector(transactions: list[dict]) -> tuple[list[bool], list[float], str]:
    """Return (predicted_flags, anomaly_scores, mode_used)."""
    values = np.array([float(tx.get("amount") or 0) for tx in transactions], dtype=float)

    if len(transactions) >= 20 and np.unique(values).size > 1:
        from sklearn.ensemble import IsolationForest
        features = _build_features(transactions)
        model = IsolationForest(n_estimators=200, contamination="auto", random_state=42)
        predictions = model.fit_predict(features)
        scores = model.decision_function(features)
        flags = [bool(p == -1) for p in predictions]
        return flags, scores.tolist(), "isolation_forest"
    else:
        median = float(np.median(values))
        threshold = max(median * 3, 10_000)
        flags = [v > threshold for v in values]
        scores = [-1.0 if f else 0.0 for f in flags]
        return flags, scores, "rule_based_insufficient_sample"


# -- Metrics ------------------------------------------------------------------

def compute_roc_auc(y_true: list[int], scores: list[float]) -> float:
    """Compute ROC-AUC using ranking of scores (lower = more anomalous)."""
    # IsolationForest: lower decision_function score = more anomalous
    # Negate so higher score = more anomalous for standard AUC calculation
    neg_scores = [-s for s in scores]
    pairs = sorted(zip(neg_scores, y_true), reverse=True)
    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    tp_cum = fp_cum = 0
    auc = 0.0
    prev_fp = 0
    prev_tp = 0
    for _, label in pairs:
        if label == 1:
            tp_cum += 1
        else:
            fp_cum += 1
            auc += (tp_cum + prev_tp) / 2 * (fp_cum - prev_fp) / (n_pos * n_neg)
            prev_fp = fp_cum
            prev_tp = tp_cum
    return round(auc, 4)


def main() -> None:
    print("=" * 60)
    print("BENCHMARK: Guardian Anomaly Detection")
    print("=" * 60)

    with open(TEST_SET_PATH, encoding="utf-8") as f:
        test_set = json.load(f)

    transactions = test_set["transactions"]
    total = len(transactions)
    labeled_anomalies = sum(1 for t in transactions if t["is_anomaly"])
    print(f"\nLoaded {total} transactions  ({labeled_anomalies} labeled anomalous).\n")

    # Run detector
    pred_flags, scores, mode = run_detector(transactions)

    print(f"Detection mode   : {mode}")
    print(f"Predicted anomalies: {sum(pred_flags)}\n")

    # -- Per-transaction comparison ----------------------------------------
    results = []
    tp = fp = fn = tn = 0
    anomaly_type_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})

    for tx, flag, score in zip(transactions, pred_flags, scores):
        true_label = tx["is_anomaly"]
        atype = tx.get("anomaly_type") or "normal"

        if flag and true_label:
            tp += 1
            anomaly_type_counts[atype]["tp"] += 1
        elif flag and not true_label:
            fp += 1
            anomaly_type_counts["normal"]["fp"] += 1
        elif not flag and true_label:
            fn += 1
            anomaly_type_counts[atype]["fn"] += 1
        else:
            tn += 1
            anomaly_type_counts["normal"]["tn"] += 1

        results.append(
            {
                "transaction_id": tx["transaction_id"],
                "merchant": tx.get("merchant"),
                "amount": tx.get("amount"),
                "date": tx.get("date"),
                "anomaly_type": tx.get("anomaly_type"),
                "true_is_anomaly": true_label,
                "predicted_is_anomaly": flag,
                "anomaly_score": round(float(score), 6),
                "correct": flag == true_label,
            }
        )

    # -- Aggregate metrics -------------------------------------------------
    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall    = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    f1        = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) > 0 else 0.0
    fpr       = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
    y_true    = [1 if t["is_anomaly"] else 0 for t in transactions]
    roc_auc   = compute_roc_auc(y_true, scores)

    print(f"{'Metric':<25} {'Value':>8}")
    print("-" * 35)
    print(f"{'Precision':<25} {precision:>8.4f}")
    print(f"{'Recall':<25} {recall:>8.4f}")
    print(f"{'F1 Score':<25} {f1:>8.4f}")
    print(f"{'ROC-AUC':<25} {roc_auc:>8.4f}")
    print(f"{'False Positive Rate':<25} {fpr:>8.4f}")
    print(f"{'TP':>25} {tp:>8}")
    print(f"{'FP':>25} {fp:>8}")
    print(f"{'FN':>25} {fn:>8}")
    print(f"{'TN':>25} {tn:>8}")

    # -- Per-anomaly-type breakdown ----------------------------------------
    print("\nPer-Anomaly-Type Breakdown:")
    print(f"{'Type':<35} {'TP':>4} {'FN':>4} {'Recall':>8}")
    print("-" * 55)

    per_type_metrics: dict[str, dict] = {}
    anomaly_types = sorted(t for t in anomaly_type_counts if t != "normal")
    for atype in anomaly_types:
        c = anomaly_type_counts[atype]
        type_recall = round(c["tp"] / (c["tp"] + c["fn"]), 4) if (c["tp"] + c["fn"]) > 0 else 0.0
        print(f"{atype:<35} {c['tp']:>4} {c['fn']:>4} {type_recall:>8.4f}")
        per_type_metrics[atype] = {**c, "recall": type_recall}

    # -- Write results --------------------------------------------------------
    RESULTS_DIR.mkdir(exist_ok=True)
    output = {
        "component": "guardian_anomaly",
        "detection_mode": mode,
        "total": total,
        "labeled_anomalies": labeled_anomalies,
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "roc_auc": roc_auc,
            "false_positive_rate": fpr,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        },
        "per_anomaly_type": per_type_metrics,
        "all_results": results,
    }
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults written to: {RESULTS_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
