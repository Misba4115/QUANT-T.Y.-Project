"""
Benchmark: Cashflow Engine — Auto-Categorization
=================================================
Runs the project's `categorise()` function on every `raw_description` in
cashflow_categorization_test_set.json, compares predicted category to
`correct_category`, and reports:
  - Overall accuracy
  - Per-category precision, recall, F1
  - Full confusion matrix

Results are written to results/cashflow_categorization_results.json

HOW TO RUN (from the repo root):
    python benchmarking/bench_cashflow_categorization.py

No database connection is required — the categoriser is a pure function.

NOTE: The test set uses fine-grained category labels (e.g. "Food & Dining")
while the current categorise() function uses coarser labels (e.g. "Food").
The script builds a mapping between them automatically, but you can also
extend CATEGORY_ALIASES below if you have updated the categorise() function.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

# -- Adjust path so we can import from backend --------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# pyrefly: ignore [missing-import]
from services.statement_parser import categorise  # noqa: E402


# -- File paths ---------------------------------------------------------------

TEST_SET_PATH = Path(__file__).parent / "cashflow_categorization_test_set.json"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_PATH = RESULTS_DIR / "cashflow_categorization_results.json"


# -- Alias map: normalise both predicted and expected to a canonical label ----

CATEGORY_ALIASES: dict[str, str] = {
    # legacy -> canonical (test-set label)
    "Food": "Food & Dining",
    "Salary": "Salary/Income",
    "Other": "Transfer",
    "EMI": "Transfer",
}


def normalise(label: str) -> str:
    """Map legacy label to the canonical test-set label where known."""
    return CATEGORY_ALIASES.get(label, label)


# -- Metrics helpers ----------------------------------------------------------


def precision_recall_f1(
    tp: int,
    fp: int,
    fn: int,
) -> tuple[float, float, float]:

    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    return round(p, 4), round(r, 4), round(f1, 4)


def build_confusion_matrix(
    labels: list[str],
    records: list[dict],
) -> dict[str, dict[str, int]]:

    matrix: dict[str, dict[str, int]] = {
        label: {l2: 0 for l2 in labels}
        for label in labels
    }

    for record in records:

        true_label = record["correct_category"]
        pred_label = record["predicted_category"]

        if (
            true_label in matrix
            and pred_label in matrix[true_label]
        ):
            matrix[true_label][pred_label] += 1

    return matrix


# -- Main ---------------------------------------------------------------------


def main() -> None:

    print("=" * 60)
    print("BENCHMARK: Cashflow Engine -- Auto-Categorization")
    print("=" * 60)

    # -------------------------------------------------------------------------
    # Load test set
    # -------------------------------------------------------------------------

    with open(TEST_SET_PATH, encoding="utf-8") as f:
        test_set = json.load(f)

    transactions = test_set["transactions"]
    all_categories: list[str] = test_set["categories"]

    print(
        f"\nLoaded {len(transactions)} transactions, "
        f"{len(all_categories)} categories.\n"
    )

    # -------------------------------------------------------------------------
    # Run categoriser
    # -------------------------------------------------------------------------

    results: list[dict] = []
    correct = 0

    for tx in transactions:

        raw_desc = tx["raw_description"]
        expected = tx["correct_category"]

        predicted_raw = categorise(raw_desc)
        predicted = normalise(predicted_raw)

        is_correct = predicted == expected

        if is_correct:
            correct += 1

        results.append(
            {
                "transaction_id": tx["transaction_id"],
                "raw_description": raw_desc,
                "correct_category": expected,
                "predicted_category_raw": predicted_raw,
                "predicted_category": predicted,
                "correct": is_correct,
            }
        )

    # -------------------------------------------------------------------------
    # Overall accuracy
    # -------------------------------------------------------------------------

    total = len(transactions)

    accuracy = (
        round(correct / total, 4)
        if total > 0
        else 0.0
    )

    print(
        f"Overall Accuracy : "
        f"{correct}/{total}  ->  {accuracy * 100:.2f}%\n"
    )

    # -------------------------------------------------------------------------
    # Per-category metrics
    # -------------------------------------------------------------------------

    per_cat: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "tp": 0,
            "fp": 0,
            "fn": 0,
        }
    )

    for record in results:

        true_label = record["correct_category"]
        pred_label = record["predicted_category"]

        if true_label == pred_label:

            per_cat[true_label]["tp"] += 1

        else:

            per_cat[true_label]["fn"] += 1
            per_cat[pred_label]["fp"] += 1

    per_category_metrics: dict[str, dict] = {}

    print(
        f"{'Category':<22} "
        f"{'P':>6} "
        f"{'R':>6} "
        f"{'F1':>6}  "
        f"{'TP':>4} "
        f"{'FP':>4} "
        f"{'FN':>4}"
    )

    print("-" * 62)

    for cat in all_categories:

        counts = per_cat[cat]

        p, r, f1 = precision_recall_f1(
            counts["tp"],
            counts["fp"],
            counts["fn"],
        )

        per_category_metrics[cat] = {
            "precision": p,
            "recall": r,
            "f1": f1,
            **counts,
        }

        print(
            f"{cat:<22} "
            f"{p:>6.4f} "
            f"{r:>6.4f} "
            f"{f1:>6.4f}  "
            f"{counts['tp']:>4} "
            f"{counts['fp']:>4} "
            f"{counts['fn']:>4}"
        )

    # -------------------------------------------------------------------------
    # Confusion matrix
    # -------------------------------------------------------------------------

    confusion_matrix = build_confusion_matrix(
        all_categories,
        results,
    )

    # -------------------------------------------------------------------------
    # Failures
    # -------------------------------------------------------------------------

    failures = [
        r for r in results
        if not r["correct"]
    ]

    print(
        f"\nMis-categorized transactions: "
        f"{len(failures)}/{total}"
    )

    if failures:

        print("\nSample failures (first 10):")

        for r in failures[:10]:

            print(
                f"  [{r['transaction_id']}] "
                f"'{r['raw_description']}' -> "
                f"got '{r['predicted_category']}', "
                f"expected '{r['correct_category']}'"
            )

    # -------------------------------------------------------------------------
    # Write results
    # -------------------------------------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "component": "cashflow_categorization",
        "total": total,
        "correct": correct,
        "overall_accuracy": accuracy,
        "per_category_metrics": per_category_metrics,
        "confusion_matrix": confusion_matrix,
        "failures": failures,
        "all_results": results,
    }

    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"\nResults written to: {RESULTS_PATH}"
    )

    print("=" * 60)


# -- Entry point --------------------------------------------------------------

if __name__ == "__main__":
    main()