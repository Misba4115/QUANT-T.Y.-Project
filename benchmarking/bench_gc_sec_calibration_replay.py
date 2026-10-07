"""
bench_gc_sec_calibration_replay.py — Experiment A: Step-3 Simulated Calibration

Purpose:
    Demonstrates the GC-SEC Step-3 uncertainty-parameter (theta_u) update rule
    using controlled prediction-outcome pairs. This is a SIMULATED HISTORICAL REPLAY,
    not live validation.

    Per the evaluation plan (Section 3.3): "Do not manufacture live outcomes. If
    longitudinal data is unavailable, run a clearly labelled simulated historical
    replay with controlled prediction-outcome pairs. Report the update rule and a
    small parameter-evolution trace as simulated calibration, not live validation."

Update rule:
    theta_u(t+1) = theta_u(t) + alpha * (outcome(t) - prediction(t))

    where:
        theta_u = uncertainty/confidence calibration parameter (0.0–1.0 range)
        alpha   = learning rate (0.1)
        outcome = 1.0 if the claim was accepted by the user as correct, 0.0 if rejected
        prediction = theta_u(t) (the model's confidence at time t)

Output:
    results/gc_sec_calibration_replay.json

Label: SIMULATED CALIBRATION — NOT LIVE VALIDATION
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

RESULTS_DIR = pathlib.Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)
OUT = RESULTS_DIR / "gc_sec_calibration_replay.json"

# ── Hyperparameters ───────────────────────────────────────────────────────────
ALPHA = 0.10              # Learning rate
THETA_U_INIT = 0.85       # Starting uncertainty calibration (reflects ~85% acceptance)

# ── Controlled prediction-outcome pairs ───────────────────────────────────────
# Each pair represents one simulated time step.
# prediction_t = theta_u at time t (model's estimated acceptance probability)
# outcome_t    = 1.0 if user accepted the claim as correct, 0.0 if rejected
# scenario     = human-readable description of the scenario type

REPLAY_PAIRS = [
    # Step 1 — Positive control: verified claim accepted
    {
        "step": 1,
        "scenario": "Positive control: correct portfolio_value claim accepted by user",
        "claim_type": "positive_control",
        "prediction_t": None,         # set from theta_u(t) at runtime
        "outcome_t": 1.0,
        "notes": "User confirmed the Rs.487,500 portfolio value was correct.",
    },
    # Step 2 — Incorrect numeric: flagged claim, user confirmed flag was correct
    {
        "step": 2,
        "scenario": "Incorrect numeric: flagged Rs.500,000 → user confirmed Rs.487,500 was right",
        "claim_type": "incorrect_numeric",
        "prediction_t": None,
        "outcome_t": 1.0,
        "notes": "Grounding caught the error; user agreed with corrected value.",
    },
    # Step 3 — False positive: model flagged a valid claim incorrectly
    {
        "step": 3,
        "scenario": "False positive: model over-flagged a borderline epsilon case",
        "claim_type": "inside_epsilon",
        "prediction_t": None,
        "outcome_t": 0.0,
        "notes": "User indicated the flagged claim (0.51% deviation) was actually acceptable.",
    },
    # Step 4 — Stale evidence accepted: user aware of staleness, accepted anyway
    {
        "step": 4,
        "scenario": "Stale evidence: user accepted stale NAV with explicit disclaimer",
        "claim_type": "stale_evidence",
        "prediction_t": None,
        "outcome_t": 0.7,
        "notes": "User acknowledged stale data. Partial acceptance (0.7) reflects qualified approval.",
    },
    # Step 5 — Missing evidence: blocked claim was correct block
    {
        "step": 5,
        "scenario": "Missing evidence: block was correct, user confirmed claim was unsupported",
        "claim_type": "missing_evidence",
        "prediction_t": None,
        "outcome_t": 1.0,
        "notes": "User confirmed the claim should not have been shown without evidence.",
    },
    # Step 6 — Currency mismatch: correct flag, but user wanted explanation not block
    {
        "step": 6,
        "scenario": "Currency mismatch: flag correct but user wanted more context before block",
        "claim_type": "currency_mismatch",
        "prediction_t": None,
        "outcome_t": 0.5,
        "notes": "Partial acceptance: flagging was right but blocking was too aggressive for this case.",
    },
    # Step 7 — Conflict resolution: winning claim was correct
    {
        "step": 7,
        "scenario": "Conflict resolved: calculation beat private_record, user confirmed",
        "claim_type": "conflict_calc_vs_private",
        "prediction_t": None,
        "outcome_t": 1.0,
        "notes": "User confirmed calculation-engine value was correct over stale DB record.",
    },
    # Step 8 — Injection: correctly treated as data, not executed
    {
        "step": 8,
        "scenario": "Injection: CAS import instruction correctly blocked/treated as data",
        "claim_type": "injection_imported_data",
        "prediction_t": None,
        "outcome_t": 1.0,
        "notes": "Security test: no instruction was executed, user confirmed correct handling.",
    },
    # Step 9 — Compound fault: over-blocked a valid claim with minor compound issues
    {
        "step": 9,
        "scenario": "Compound fault: block over-aggressive for stale + minor unit variation",
        "claim_type": "compound_fault",
        "prediction_t": None,
        "outcome_t": 0.3,
        "notes": "User felt block was too strict; stale NAV + small unit notation difference should show warning not block.",
    },
    # Step 10 — Unresolved tie: correct to block when two equal-rank sources disagree
    {
        "step": 10,
        "scenario": "Unresolved tie: blocking was correct, user appreciated explicit uncertainty",
        "claim_type": "unresolved_tie",
        "prediction_t": None,
        "outcome_t": 1.0,
        "notes": "User agreed: better to block and request clarification than guess between NSE and BSE feed.",
    },
    # Step 11 — Outside epsilon: flag-and-replace accepted by user
    {
        "step": 11,
        "scenario": "Outside epsilon: corrected value Rs.487,500 accepted, original Rs.495,000 was wrong",
        "claim_type": "outside_epsilon",
        "prediction_t": None,
        "outcome_t": 1.0,
        "notes": "User confirmed corrected value was accurate.",
    },
    # Step 12 — Unknown evidence ID: block was correct
    {
        "step": 12,
        "scenario": "Unknown evidence ID: block was correct, hallucinated reference caught",
        "claim_type": "unknown_evidence_id",
        "prediction_t": None,
        "outcome_t": 1.0,
        "notes": "Phantom EV_HALLUCINATED_999 correctly rejected.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# CALIBRATION REPLAY LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ReplayStep:
    step: int
    scenario: str
    claim_type: str
    theta_u_before: float
    prediction_t: float
    outcome_t: float
    delta: float
    theta_u_after: float
    notes: str
    error_signal: float  # outcome - prediction


def run_replay(
    pairs: list[dict],
    theta_init: float = THETA_U_INIT,
    alpha: float = ALPHA,
) -> list[ReplayStep]:
    theta_u = theta_init
    steps: list[ReplayStep] = []

    for pair in pairs:
        theta_before = round(theta_u, 6)
        prediction_t = theta_u   # at time t, model predicts theta_u
        outcome_t = pair["outcome_t"]
        error_signal = outcome_t - prediction_t
        delta = alpha * error_signal
        theta_u = max(0.0, min(1.0, theta_u + delta))  # clamp [0,1]

        steps.append(ReplayStep(
            step=pair["step"],
            scenario=pair["scenario"],
            claim_type=pair["claim_type"],
            theta_u_before=theta_before,
            prediction_t=round(prediction_t, 6),
            outcome_t=outcome_t,
            delta=round(delta, 6),
            theta_u_after=round(theta_u, 6),
            notes=pair["notes"],
            error_signal=round(error_signal, 6),
        ))

    return steps


def main():
    print("=" * 70)
    print("GC-SEC Step-3 Calibration — Simulated Historical Replay")
    print("LABEL: SIMULATED CALIBRATION -- NOT LIVE VALIDATION")
    print("=" * 70)
    print(f"Initial theta_u:  {THETA_U_INIT}")
    print(f"Learning rate:    {ALPHA}")
    print(f"Update rule:      theta_u(t+1) = theta_u(t) + {ALPHA} * (outcome(t) - theta_u(t))")
    print()

    steps = run_replay(REPLAY_PAIRS, THETA_U_INIT, ALPHA)

    # Print evolution trace
    print(f"{'Step':<5} {'Claim Type':<30} {'theta_u(t)':<12} {'outcome(t)':<12} {'delta':<10} {'theta_u(t+1)':<14}")
    print("-" * 85)
    for s in steps:
        print(
            f"{s.step:<5} {s.claim_type:<30} {s.theta_u_before:<12.6f} "
            f"{s.outcome_t:<12.2f} {s.delta:<10.6f} {s.theta_u_after:<14.6f}"
        )

    theta_final = steps[-1].theta_u_after
    theta_change = theta_final - THETA_U_INIT
    avg_error = sum(s.error_signal for s in steps) / len(steps)
    positive_outcomes = sum(1 for s in steps if s.outcome_t >= 0.7)

    print()
    print(f"Initial theta_u:    {THETA_U_INIT:.6f}")
    print(f"Final theta_u:      {theta_final:.6f}")
    print(f"Net change:         {theta_change:+.6f}")
    print(f"Avg error signal:   {avg_error:.6f}")
    print(f"High-acceptance steps (outcome >= 0.7): {positive_outcomes}/{len(steps)}")
    print()
    print("NOTE: This is a simulated calibration trace. theta_u values reflect")
    print("      the parameter evolution under the specified update rule applied")
    print("      to controlled hypothetical outcomes. They do not represent")
    print("      measurements from live user interactions.")

    # Write output
    output = {
        "label": "SIMULATED CALIBRATION -- NOT LIVE VALIDATION",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology": (
            "Simulated historical replay with controlled prediction-outcome pairs. "
            "Per evaluation plan Section 3.3: longitudinal live data is unavailable, "
            "so this replay demonstrates the update rule and parameter evolution "
            "without claiming live calibration effectiveness."
        ),
        "update_rule": "theta_u(t+1) = theta_u(t) + alpha * (outcome(t) - theta_u(t))",
        "hyperparameters": {
            "theta_u_initial": THETA_U_INIT,
            "alpha": ALPHA,
            "theta_u_clamp": [0.0, 1.0],
        },
        "summary": {
            "total_steps": len(steps),
            "theta_u_initial": THETA_U_INIT,
            "theta_u_final": theta_final,
            "net_change": round(theta_change, 6),
            "avg_error_signal": round(avg_error, 6),
            "high_acceptance_steps": positive_outcomes,
            "step_outcomes_summary": {
                "outcome_1.0 (full acceptance)": sum(1 for s in steps if s.outcome_t == 1.0),
                "outcome_0.7 (partial acceptance)": sum(1 for s in steps if s.outcome_t == 0.7),
                "outcome_0.5 (qualified acceptance)": sum(1 for s in steps if s.outcome_t == 0.5),
                "outcome_0.3 (marginal rejection)": sum(1 for s in steps if s.outcome_t == 0.3),
                "outcome_0.0 (full rejection)": sum(1 for s in steps if s.outcome_t == 0.0),
            },
        },
        "evolution_trace": [asdict(s) for s in steps],
        "interpretation_rules": [
            "Do not claim live calibration improvement from this simulated replay.",
            "Do not interpret theta_u drift as evidence of real user behaviour.",
            "The update rule is presented for methodological transparency only.",
            "Step-3 would require longitudinal deployment data for live validation.",
        ],
    }

    OUT.write_text(json.dumps(output, indent=2))
    print(f"\nOutput written to: {OUT.name}")
    return output


if __name__ == "__main__":
    main()
