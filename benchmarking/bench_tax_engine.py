"""
Benchmark: Tax Engine
======================
Runs the Tax Engine's calculation logic on every scenario in
tax_engine_test_set.json, compares each output field to expected_output,
and reports an exact-match rate.

Results are written to results/tax_engine_results.json

HOW TO RUN (from the repo root):
    python benchmarking/bench_tax_engine.py

No database connection is required.

IMPORTANT DISCLAIMER (reproduced from test set):
  The LTCG exemption, LTCG rate, STCG rate, and 80C cap used to compute
  expected_output are illustrative placeholders. Verify against current
  official rates for the assessment year before treating expected_output
  as ground truth.

ENGINE CALL CONTRACT:
  The production tax engine (services/tax_analytics.py) computes realized
  gains from actual DB transactions. For unit testing with synthetic inputs
  we call the underlying rule functions directly using the scenario inputs.
  Two helpers are implemented below:
    - compute_capital_gains_tax(inputs) -- for TAX001-TAX013
    - compute_section_80c(inputs)        -- for TAX014-TAX018
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any
from provenance import provenance

# -- Adjust path so we can import from backend --------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND))
from services.tax_analytics import (  # noqa: E402
    SECTION_80C_LIMIT, _rule, calculate_80c_scenario, calculate_equity_gain_scenario,
)

# -- File paths ---------------------------------------------------------------
TEST_SET_PATH = Path(__file__).parent / "tax_engine_test_set.json"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_PATH = RESULTS_DIR / "tax_engine_results.json"

# -- Tax rule constants (mirrors tax_engine_test_set expected_output logic) ---
#    NOTE: These are the placeholder rates used in the test set.
#    Update them to match the production rates in services/tax_analytics.py
#    and re-generate expected_output values if they differ.

BENCHMARK_SALE_DATE = date(2025, 4, 1)
ACTIVE_RULE = _rule(BENCHMARK_SALE_DATE)
LTCG_EXEMPTION = ACTIVE_RULE["ltcg_exemption"]
LTCG_RATE = ACTIVE_RULE["ltcg_rate"]
STCG_RATE = ACTIVE_RULE["stcg_rate"]
SECTION_80C_CAP = SECTION_80C_LIMIT

# Equity MF: LTCG if holding_period_days > 365 (strict greater-than)
EQUITY_LTCG_THRESHOLD_DAYS = 365


# -- Computation helpers -------------------------------------------------------

def compute_capital_gains_tax(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Compute gain_type, taxable_gain, tax_amount, exemption_applied
    for a capital-gains scenario.

    Supports asset_type in:
      equity_mf, equity_mf_elss, direct_equity
    """
    if inputs["asset_type"] not in {"equity_mf", "equity_mf_elss", "direct_equity"}:
        raise ValueError("Scenario is outside the benchmark's eligible equity scope")
    return calculate_equity_gain_scenario(
        holding_period_days=int(inputs["holding_period_days"]),
        capital_gain=float(inputs["capital_gain"]),
        exemption_used=float(inputs.get("ltcg_exemption_used_ytd", 0)),
        sale_date=BENCHMARK_SALE_DATE,
    )


def compute_section_80c(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Compute eligible_deduction_from_this_investment and total_80c_used_after.
    """
    if float(inputs.get("section_80c_cap", SECTION_80C_CAP)) != SECTION_80C_CAP:
        raise ValueError("Scenario cap differs from the production Section 80C limit")
    return calculate_80c_scenario(
        new_investment=float(inputs["new_80c_investment"]),
        used_ytd=float(inputs["section_80c_used_ytd"]),
    )


# -- Field comparison ---------------------------------------------------------

NUMERIC_FIELDS = {"taxable_gain", "tax_amount", "exemption_applied",
                  "eligible_deduction_from_this_investment", "total_80c_used_after"}
TOLERANCE = 0.01  # rupee-level tolerance for float rounding


def fields_match(predicted: dict, expected: dict) -> tuple[bool, list[str]]:
    """Return (all_match, list_of_mismatches)."""
    # Only compare fields present in expected (ignore 'note' etc.)
    mismatches = []
    fields_to_check = [k for k in expected if k not in ("note",)]
    for field in fields_to_check:
        exp_val = expected[field]
        pred_val = predicted.get(field)
        if pred_val is None:
            mismatches.append(f"{field}: missing in prediction")
            continue
        if field in NUMERIC_FIELDS:
            if abs(float(pred_val) - float(exp_val)) > TOLERANCE:
                mismatches.append(f"{field}: predicted={pred_val}, expected={exp_val}")
        else:
            if str(pred_val) != str(exp_val):
                mismatches.append(f"{field}: predicted={pred_val!r}, expected={exp_val!r}")
    return len(mismatches) == 0, mismatches


# -- Main ---------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("BENCHMARK: Tax Engine")
    print("=" * 60)
    print("\nDISCLAIMER: Rates are illustrative placeholders.")
    print("  Verify against official rates before presenting results.\n")

    with open(TEST_SET_PATH, encoding="utf-8") as f:
        test_set = json.load(f)

    print(f"IMPORTANT_DISCLAIMER: {test_set.get('IMPORTANT_DISCLAIMER', '')}\n")

    scenarios = test_set["scenarios"]
    print(f"Loaded {len(scenarios)} scenarios.\n")

    results = []
    exact_matches = 0

    print(f"{'ID':<10} {'Description':<48} {'Match?':>7}")
    print("-" * 68)

    for sc in scenarios:
        sid = sc["scenario_id"]
        inputs = sc["inputs"]
        expected = sc["expected_output"]

        # Route to the correct calculation
        if "new_80c_investment" in inputs:
            predicted = compute_section_80c(inputs)
        else:
            predicted = compute_capital_gains_tax(inputs)

        matched, mismatches = fields_match(predicted, expected)
        if matched:
            exact_matches += 1
        status = "PASS" if matched else "FAIL"
        desc = sc.get("description", "")[:47]
        print(f"{sid:<10} {desc:<48} {status:>7}")
        if mismatches:
            for m in mismatches:
                print(f"           MISMATCH: {m}")

        results.append(
            {
                "scenario_id": sid,
                "description": sc.get("description"),
                "inputs": inputs,
                "expected_output": expected,
                "predicted_output": predicted,
                "matched": matched,
                "mismatches": mismatches,
                "status": status,
            }
        )

    # -- Summary ---------------------------------------------------------------
    total = len(scenarios)
    exact_match_rate = round(exact_matches / total, 4) if total > 0 else 0.0
    print(f"\nExact-Match Rate: {exact_matches}/{total}  ->  {exact_match_rate * 100:.2f}%")
    if exact_matches < total:
        print("NOTE: Any FAIL is a bug to investigate, not a number to present as-is.")

    # -- Write results --------------------------------------------------------
    RESULTS_DIR.mkdir(exist_ok=True)
    output = {
        "component": "tax_engine",
        "provenance": provenance(TEST_SET_PATH, "illustrative formula scenarios, not end-to-end tax return validation"),
        "total": total,
        "exact_matches": exact_matches,
        "exact_match_rate": exact_match_rate,
        "rate_config": {
            "ltcg_exemption": LTCG_EXEMPTION,
            "ltcg_rate": LTCG_RATE,
            "stcg_rate": STCG_RATE,
            "section_80c_cap": SECTION_80C_CAP,
        },
        "scenarios": results,
    }
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults written to: {RESULTS_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
