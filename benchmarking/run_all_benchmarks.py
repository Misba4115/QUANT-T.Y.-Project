"""
Run All Benchmarks
==================
Convenience script to run all benchmark tests in sequence.
Produces a final summary table across all components.

HOW TO RUN (from the repo root):
    python benchmarking/run_all_benchmarks.py

You can also pass --skip flags to skip specific benchmarks:
    python benchmarking/run_all_benchmarks.py --skip rag_retrieval --skip rag_chatbot

Available skip targets:
    cashflow_categorization
    guardian_anomaly
    portfolio_analytics
    tax_engine
    rag_retrieval
    rag_chatbot

NOTES:
  - bench_cashflow_categorization.py : No external deps.  Should always run.
  - bench_guardian_anomaly.py        : Requires scikit-learn.
  - bench_portfolio_analytics.py     : Requires PyPortfolioOpt.
  - bench_tax_engine.py              : No external deps.  Should always run.
  - bench_rag_retrieval.py           : Requires Qdrant + sentence-transformers.
  - bench_rag_chatbot_answer.py      : Requires Qdrant + LLM + ragas + datasets.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

BENCH_DIR = Path(__file__).parent
RESULTS_DIR = BENCH_DIR / "results"

BENCHMARKS = [
    {
        "id": "cashflow_categorization",
        "script": "bench_cashflow_categorization.py",
        "results_file": "cashflow_categorization_results.json",
        "key_metrics": ["overall_accuracy"],
    },
    {
        "id": "guardian_anomaly",
        "script": "bench_guardian_anomaly.py",
        "results_file": "guardian_anomaly_results.json",
        "key_metrics": ["metrics.precision", "metrics.recall", "metrics.f1_score", "metrics.roc_auc"],
    },
    {
        "id": "portfolio_analytics",
        "script": "bench_portfolio_analytics.py",
        "results_file": "portfolio_analytics_results.json",
        "key_metrics": ["passed", "failed", "errored"],
    },
    {
        "id": "tax_engine",
        "script": "bench_tax_engine.py",
        "results_file": "tax_engine_results.json",
        "key_metrics": ["exact_match_rate"],
    },
    {
        "id": "rag_retrieval",
        "script": "bench_rag_retrieval.py",
        "results_file": "rag_retrieval_results.json",
        "key_metrics": ["metrics.mrr", "metrics.recall_at_1", "metrics.recall_at_3", "metrics.recall_at_5"],
    },
    {
        "id": "rag_chatbot",
        "script": "bench_rag_chatbot_answer.py",
        "results_file": "rag_chatbot_answer_results.json",
        "key_metrics": ["fact_check_accuracy", "grounding_correction_rate",
                        "avg_faithfulness", "avg_answer_relevancy"],
    },
]


def get_nested(data: dict, dotpath: str):
    """Fetch a value using dot-notation path, e.g. 'metrics.precision'."""
    parts = dotpath.split(".")
    for part in parts:
        if isinstance(data, dict):
            data = data.get(part)
        else:
            return None
    return data


def run_benchmark(bench: dict, python: str) -> tuple[bool, float]:
    """Run a single benchmark script; return (success, elapsed_seconds)."""
    script_path = BENCH_DIR / bench["script"]
    t0 = time.time()
    result = subprocess.run(
        [python, str(script_path)],
        capture_output=False,
    )
    elapsed = time.time() - t0
    return result.returncode == 0, elapsed


def print_summary(results_collected: list[dict]) -> None:
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"{'Component':<32} {'Status':>8}  {'Key Metrics'}")
    print("-" * 70)

    for entry in results_collected:
        bid = entry["id"]
        status = entry.get("run_status", "SKIPPED")
        metrics_str = ""

        if status == "PASS" and entry.get("results_path"):
            results_path = Path(entry["results_path"])
            if results_path.exists():
                with open(results_path, encoding="utf-8") as f:
                    data = json.load(f)
                parts = []
                for metric_path in entry.get("key_metrics", []):
                    val = get_nested(data, metric_path)
                    short_name = metric_path.split(".")[-1]
                    if isinstance(val, float):
                        parts.append(f"{short_name}={val:.4f}")
                    elif val is not None:
                        parts.append(f"{short_name}={val}")
                metrics_str = "  |  ".join(parts)

        print(f"{bid:<32} {status:>8}  {metrics_str}")

    print("=" * 70)
    print(f"\nResults saved in: {RESULTS_DIR}/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all QUANT-TY benchmarks")
    parser.add_argument("--skip", action="append", default=[], help="Benchmark ID to skip (repeatable)")
    args = parser.parse_args()

    python = sys.executable
    skipped_ids = set(args.skip)

    print("=" * 60)
    print("QUANT-TY — Running All Benchmarks")
    print("=" * 60)
    print(f"Python: {python}")
    print(f"Skip:   {skipped_ids or 'none'}\n")

    RESULTS_DIR.mkdir(exist_ok=True)

    results_collected = []

    for bench in BENCHMARKS:
        bid = bench["id"]
        entry = {
            "id": bid,
            "key_metrics": bench["key_metrics"],
            "results_path": str(RESULTS_DIR / bench["results_file"]),
        }

        if bid in skipped_ids:
            print(f"\n[SKIP] {bid}")
            entry["run_status"] = "SKIPPED"
            results_collected.append(entry)
            continue

        print(f"\n[RUN ] {bid}")
        print("-" * 40)

        success, elapsed = run_benchmark(bench, python)
        entry["run_status"] = "PASS" if success else "FAIL"
        entry["elapsed_seconds"] = round(elapsed, 1)
        results_collected.append(entry)

        print(f"\n  -> {entry['run_status']}  ({elapsed:.1f}s)")

    print_summary(results_collected)

    # Write meta-results
    meta_path = RESULTS_DIR / "run_all_summary.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(results_collected, f, indent=2)
    print(f"Meta-summary: {meta_path}")


if __name__ == "__main__":
    main()
