"""Run the deterministic multi-account functional benchmark.

The benchmark exercises the production transaction categorizer and Guardian
detector together over repeatable normal and anomalous transaction patterns.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from generate_synthetic_stress import generate
from holdout.evaluate_holdout import _categorization, _git_state, _guardian


BENCH_DIR = Path(__file__).resolve().parent
OUTPUT = BENCH_DIR / "results" / "functional_stress_results.json"
SEED = 20261008
ACCOUNT_COUNT = 10
NORMAL_PER_ACCOUNT = 100
START_DATE = date(2025, 1, 1)


def _dataset_sha256(rows: list[dict[str, str]]) -> str:
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run() -> dict[str, object]:
    rows = generate(SEED, ACCOUNT_COUNT, NORMAL_PER_ACCOUNT, START_DATE)
    features = [
        {
            key: row[key]
            for key in (
                "record_id", "account_id", "tx_date", "occurred_at",
                "description", "amount", "tx_type",
            )
        }
        for row in rows
    ]
    labels = {
        row["record_id"]: {
            "record_id": row["record_id"],
            "expected_category": row["expected_category"],
            "is_anomaly": row["is_anomaly"],
            "anomaly_type": row["anomaly_type"],
        }
        for row in rows
    }

    return {
        "component": "controlled_functional_stress",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_design": "deterministic controlled multi-account functional benchmark",
        "provenance": {
            "dataset_sha256": _dataset_sha256(rows),
            "seed": SEED,
            "source_commit": _git_state()["commit"],
            "working_tree_dirty": _git_state()["working_tree_dirty"],
        },
        "configuration": {
            "account_count": ACCOUNT_COUNT,
            "normal_transactions_per_account": NORMAL_PER_ACCOUNT,
            "start_date": START_DATE.isoformat(),
            "total_transactions": len(rows),
        },
        "cashflow_categorization": _categorization(features, labels),
        "guardian": _guardian(features, labels),
    }


def main() -> None:
    result = run()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    cashflow = result["cashflow_categorization"]
    guardian = result["guardian"]
    print("=" * 68)
    print("CONTROLLED FUNCTIONAL BENCHMARK")
    print("=" * 68)
    print(f"Transactions:               {cashflow['total']}")
    print(f"Categorization accuracy:    {cashflow['accuracy']:.2%}")
    print(f"Categorization macro-F1:    {cashflow['macro_f1_supported_classes']:.2%}")
    print(f"Guardian precision:         {guardian['precision']:.2%}")
    print(f"Guardian recall:            {guardian['recall']:.2%}")
    print(f"Guardian F1:                {guardian['f1']:.2%}")
    print(f"Guardian false alerts/1000: {guardian['false_alerts_per_1000_normal_transactions']:.2f}")
    print(f"Results: {OUTPUT}")


if __name__ == "__main__":
    main()
