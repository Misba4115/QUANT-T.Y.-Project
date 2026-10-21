"""
Benchmark: Guardian Anomaly Detection
======================================
Runs the same rule-based + IsolationForest detector imported by the production
Guardian agent on every transaction in
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
import sys
from collections import defaultdict
from pathlib import Path
from sklearn.metrics import roc_auc_score
from provenance import provenance

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))
from services.guardian_detector import detect_anomalies  # noqa: E402

# -- File paths ---------------------------------------------------------------
TEST_SET_PATH = Path(__file__).parent / "guardian_anomaly_test_set.json"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_PATH = RESULTS_DIR / "guardian_anomaly_results.json"

def run_detector(transactions: list[dict]) -> tuple[list[bool], list[float], str]:
    """Call the same detector as Guardian, without database persistence."""
    records = [("bank_transactions", tx, float(tx.get("amount") or 0)) for tx in transactions]
    flags, scores, _reasons, mode, _version = detect_anomalies(records)
    return flags.tolist(), scores.tolist(), mode


# -- Metrics ------------------------------------------------------------------

def compute_roc_auc(y_true: list[int], scores: list[float]) -> float:
    """Compute ROC-AUC using ranking of scores (lower = more anomalous)."""
    if not any(y_true) or all(y_true):
        return 0.5
    return round(float(roc_auc_score(y_true, [-score for score in scores])), 4)


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
        "benchmark_scope": "synthetic development set; detector fitted on this corpus; not independent validation",
        "provenance": provenance(TEST_SET_PATH, "exposed synthetic development set"),
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
