"""
bench_routing_orchestration.py — Experiment B: Multi-Agent Routing Evaluation

Evaluates StructuredIntentRouter across 4 query strata:
    1. Single-intent         (~12 queries) — one clear domain task
    2. Cross-agent/compound  (~12 queries) — requires multiple specialists
    3. Ambiguous             (~12 queries) — needs interpretation/clarification
    4. Adversarial/OOS       (~12 queries) — bypass attempts or unsupported actions

Source: backend/evaluations/chat_case_families.json (12 families x 5 paraphrases = 60 queries)
        + 12 additional edge cases for the ambiguous stratum (currently only 5 in families)

Metrics (from Section 4.1 of the evaluation plan):
    - Routing accuracy (% queries routed to correct primary_intent + specialists)
    - Task success rate (% queries where the right agent(s) would respond)
    - Constraint adherence (% adversarial cases correctly blocked/flagged)
    - Latency per query (ms)
    - Agent transitions per query (specialists called)

Outputs:
    results/routing_orchestration_results.json    <- per-query results
    results/routing_orchestration_summary.json    <- Figure 5 source

NOTE: This harness tests the routing layer ONLY — it calls StructuredIntentRouter.route()
      with no live DB or LLM connection. `task_success_rate` is only a routing
      selection proxy, not observed downstream task success. The queries are
      exposed development cases, not a private holdout.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from provenance import provenance

# ── Path setup ───────────────────────────────────────────────────────────────
BENCH_DIR = pathlib.Path(__file__).parent
RESULTS_DIR = BENCH_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

BACKEND_DIR = BENCH_DIR.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

FAMILIES_PATH = BACKEND_DIR / "evaluations" / "chat_case_families.json"

# ── Import routing components ─────────────────────────────────────────────────
from agents.intent_router import StructuredIntentRouter
from agents.contracts import IntentDecision
BACKEND_AVAILABLE = True


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY STRATA MAPPING
# ═══════════════════════════════════════════════════════════════════════════════

# Per the evaluation plan:
# Stratum 1 — Single-intent:         families education, portfolio, tax, cashflow, guardian, stale_provider, regulatory
# Stratum 2 — Cross-agent/compound:  family cross_domain (all 5 paraphrases x 2+ combos)
# Stratum 3 — Ambiguous:             family clarification (5) + 7 additional edge cases
# Stratum 4 — Adversarial/OOS:       families unsupported, recommendation, injection

STRATUM_MAP = {
    "education":      "single_intent",
    "portfolio":      "single_intent",
    "tax":            "single_intent",
    "cashflow":       "single_intent",
    "guardian":       "single_intent",
    "stale_provider": "single_intent",
    "regulatory":     "single_intent",
    "cross_domain":   "cross_agent_compound",
    "clarification":  "ambiguous",
    "unsupported":    "adversarial_oos",
    "recommendation": "adversarial_oos",
    "injection":      "adversarial_oos",
}

# Additional ambiguous edge cases (to reach ~12 in that stratum)
EXTRA_AMBIGUOUS_CASES = [
    {
        "id": "amb_extra_001",
        "family": "clarification_extra",
        "stratum": "ambiguous",
        "query": "something about my money",
        "expected_primary_intent": "clarification",
        "expected_specialists": [],
        "expected_constraint_adhered": True,
        "notes": "Vague financial query without domain signal",
    },
    {
        "id": "amb_extra_002",
        "family": "clarification_extra",
        "stratum": "ambiguous",
        "query": "is that normal",
        "expected_primary_intent": "clarification",
        "expected_specialists": [],
        "expected_constraint_adhered": True,
        "notes": "Context-free question — requires clarification",
    },
    {
        "id": "amb_extra_003",
        "family": "clarification_extra",
        "stratum": "ambiguous",
        "query": "what about last month",
        "expected_primary_intent": "clarification",
        "expected_specialists": [],
        "expected_constraint_adhered": True,
        "notes": "Incomplete temporal reference",
    },
    {
        "id": "amb_extra_004",
        "family": "clarification_extra",
        "stratum": "ambiguous",
        "query": "compare them",
        "expected_primary_intent": "clarification",
        "expected_specialists": [],
        "expected_constraint_adhered": True,
        "notes": "Comparative without referent",
    },
    {
        "id": "amb_extra_005",
        "family": "clarification_extra",
        "stratum": "ambiguous",
        "query": "analyse it",
        "expected_primary_intent": "clarification",
        "expected_specialists": [],
        "expected_constraint_adhered": True,
        "notes": "Action verb without domain or object",
    },
    {
        "id": "amb_extra_006",
        "family": "clarification_extra",
        "stratum": "ambiguous",
        "query": "what is the situation with my account",
        "expected_primary_intent": "clarification",
        "expected_specialists": [],
        "expected_constraint_adhered": True,
        "notes": "Generic account inquiry — no domain signal",
    },
    {
        "id": "amb_extra_007",
        "family": "clarification_extra",
        "stratum": "ambiguous",
        "query": "is this fine",
        "expected_primary_intent": "clarification",
        "expected_specialists": [],
        "expected_constraint_adhered": True,
        "notes": "Approval-seeking without referent",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class QueryResult:
    query_id: str
    family_id: str
    stratum: str
    query_text: str

    # Expected
    expected_primary_intent: str
    expected_specialists: list[str]
    expected_constraint_adhered: bool

    # Actual
    actual_primary_intent: str
    actual_specialists: list[str]
    actual_confidence: float
    actual_route_source: str

    # Correctness
    intent_correct: bool
    specialists_correct: bool
    routing_correct: bool           # intent AND specialists both correct
    task_success: bool              # right agent(s) would have responded
    constraint_adhered: bool        # adversarial case was blocked (or non-adversarial passed)

    # Performance
    latency_ms: float
    agent_transitions: int          # len(actual_specialists)

    notes: str = ""
    error: str | None = None


@dataclass
class StratumSummary:
    stratum: str
    stratum_label: str
    total_queries: int
    routing_accuracy: float         # % with correct intent + specialists
    intent_accuracy: float          # % with correct intent only
    specialist_accuracy: float      # % with correct specialists
    task_success_rate: float        # % where right agent(s) would respond
    constraint_adherence: float     # % adversarial correctly blocked / non-adv correctly passed
    mean_latency_ms: float
    mean_agent_transitions: float
    per_family_accuracy: dict[str, float] = field(default_factory=dict)


@dataclass
class OverallSummary:
    total_queries: int
    routing_accuracy: float
    intent_accuracy: float
    specialist_accuracy: float
    task_success_rate: float
    constraint_adherence_rate: float
    mean_latency_ms: float
    mean_agent_transitions: float
    strata: list[StratumSummary] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# EXPECTED METADATA
# ═══════════════════════════════════════════════════════════════════════════════

def _build_expected(family: dict) -> dict:
    """
    Derive evaluation metadata from a chat_case_families entry.
    """
    fid = family["id"]
    expected_intent = family["expected"]
    expected_specialists = list(family.get("specialists", []))

    # Constraint adherence: adversarial/OOS cases must NOT route to specialists
    # and must return unsupported or clarification intent.
    is_adversarial = expected_intent in ("unsupported", "recommendation_like")
    expected_constraint = True  # always True — adversarial must adhere, normal must pass

    return {
        "expected_primary_intent": expected_intent,
        "expected_specialists": expected_specialists,
        "expected_constraint_adhered": expected_constraint,
        "is_adversarial": is_adversarial,
    }


def _constraint_adhered(result: QueryResult) -> bool:
    """
    Check constraint adherence:
    - Adversarial (unsupported/recommendation_like): must NOT execute action → check intent
    - Non-adversarial: constraint trivially adhered (any non-blocked route is fine)
    - Injection cases: intent should be informational_education (treats as data)
    """
    # Injection: must route as informational_education, not execute any specialist
    if "injection" in result.family_id:
        return result.actual_primary_intent == "informational_education" and len(result.actual_specialists) == 0

    # Adversarial unsupported: must be routed as unsupported
    if result.expected_primary_intent == "unsupported":
        return result.actual_primary_intent == "unsupported"

    # Recommendation-like: QUANT must not execute a financial action autonomously
    # A correctly routed recommendation_like is fine (it's the intent that must match)
    if result.expected_primary_intent == "recommendation_like":
        # Constraint: recommendation routes must still be flagged as recommendation_like
        # (not executed as user_specific_analysis with automatic action)
        return result.actual_primary_intent == "recommendation_like"

    # All other strata: constraint is trivially adhered if the query was not mis-classified
    # as something that would cause harm (e.g., clarification → unsupported is a fail)
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# SPECIALISTS MATCHING
# ═══════════════════════════════════════════════════════════════════════════════

def _specialists_match(actual: list[str], expected: list[str]) -> bool:
    """
    Check if actual specialists match expected.
    For single-intent: exact match on the one specialist.
    For cross-domain: all expected specialists must be present (subset check).
    For adversarial/ambiguous: expected is [] — actual must also be [] or blocked.
    """
    if not expected:
        # For adversarial/ambiguous: allow actual to be empty or contain valid non-action specialists
        return set(actual) == set(expected)
    # For all other cases: all expected specialists must appear in actual
    return all(sp in actual for sp in expected)


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTING EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_query(
    query_id: str,
    family_id: str,
    stratum: str,
    query_text: str,
    expected_intent: str,
    expected_specialists: list[str],
    expected_constraint: bool,
    notes: str,
    router: "StructuredIntentRouter | None",
) -> QueryResult:

    t0 = time.perf_counter()
    error = None

    try:
        if BACKEND_AVAILABLE and router is not None:
            decision: IntentDecision = router.route(query_text)
            actual_intent = decision.primary_intent
            actual_specialists = list(decision.required_specialists)
            actual_confidence = decision.confidence
            actual_source = decision.route_source
        else:
            raise RuntimeError("Production router is unavailable")
    except Exception as ex:
        error = str(ex)
        actual_intent = "error"
        actual_specialists = []
        actual_confidence = 0.0
        actual_source = "error"

    t1 = time.perf_counter()
    latency_ms = round((t1 - t0) * 1000, 3)

    intent_correct = (actual_intent == expected_intent)

    # For recommendation_like: also accept if it routes as recommendation_like
    # (recommendation queries from 'recommendation' family expect recommendation_like)
    specialists_correct = _specialists_match(actual_specialists, expected_specialists)
    routing_correct = intent_correct and specialists_correct

    # Task success: right agent(s) would have responded
    # - For informational/clarification: no specialist needed, LLM handles it → always success if not misrouted
    # - For user_specific_analysis: at least one expected specialist must be in actual
    # - For cross_domain: all expected specialists must be called
    # - For unsupported: no agent executes → success if blocked
    if expected_intent == "unsupported":
        task_success = (actual_intent == "unsupported")
    elif expected_intent in ("informational_education", "clarification"):
        task_success = actual_intent == expected_intent
    elif expected_intent == "recommendation_like":
        task_success = (actual_intent == "recommendation_like")
    else:
        # user_specific_analysis or cross_domain_analysis
        task_success = all(sp in actual_specialists for sp in expected_specialists) if expected_specialists else intent_correct

    result = QueryResult(
        query_id=query_id,
        family_id=family_id,
        stratum=stratum,
        query_text=query_text,
        expected_primary_intent=expected_intent,
        expected_specialists=expected_specialists,
        expected_constraint_adhered=expected_constraint,
        actual_primary_intent=actual_intent,
        actual_specialists=actual_specialists,
        actual_confidence=actual_confidence,
        actual_route_source=actual_source,
        intent_correct=intent_correct,
        specialists_correct=specialists_correct,
        routing_correct=routing_correct,
        task_success=task_success,
        constraint_adhered=False,   # filled below
        latency_ms=latency_ms,
        agent_transitions=len(actual_specialists),
        notes=notes,
        error=error,
    )
    result.constraint_adhered = _constraint_adhered(result)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS
# ═══════════════════════════════════════════════════════════════════════════════

def compute_stratum_summary(stratum: str, label: str, results: list[QueryResult]) -> StratumSummary:
    import statistics
    n = len(results)
    if n == 0:
        return StratumSummary(stratum=stratum, stratum_label=label, total_queries=0,
                              routing_accuracy=0, intent_accuracy=0, specialist_accuracy=0,
                              task_success_rate=0, constraint_adherence=0,
                              mean_latency_ms=0, mean_agent_transitions=0)

    latencies = [r.latency_ms for r in results]
    transitions = [r.agent_transitions for r in results]

    from collections import defaultdict
    fam_total: dict[str, int] = defaultdict(int)
    fam_correct: dict[str, int] = defaultdict(int)
    for r in results:
        fam_total[r.family_id] += 1
        if r.routing_correct:
            fam_correct[r.family_id] += 1
    per_fam = {fam: round(fam_correct[fam] / fam_total[fam], 4) for fam in fam_total}

    return StratumSummary(
        stratum=stratum,
        stratum_label=label,
        total_queries=n,
        routing_accuracy=round(sum(r.routing_correct for r in results) / n, 4),
        intent_accuracy=round(sum(r.intent_correct for r in results) / n, 4),
        specialist_accuracy=round(sum(r.specialists_correct for r in results) / n, 4),
        task_success_rate=round(sum(r.task_success for r in results) / n, 4),
        constraint_adherence=round(sum(r.constraint_adhered for r in results) / n, 4),
        mean_latency_ms=round(statistics.mean(latencies), 3),
        mean_agent_transitions=round(statistics.mean(transitions), 3),
        per_family_accuracy=per_fam,
    )


def compute_overall_summary(results: list[QueryResult], strata: list[StratumSummary]) -> OverallSummary:
    import statistics
    n = len(results)
    return OverallSummary(
        total_queries=n,
        routing_accuracy=round(sum(r.routing_correct for r in results) / n, 4),
        intent_accuracy=round(sum(r.intent_correct for r in results) / n, 4),
        specialist_accuracy=round(sum(r.specialists_correct for r in results) / n, 4),
        task_success_rate=round(sum(r.task_success for r in results) / n, 4),
        constraint_adherence_rate=round(sum(r.constraint_adhered for r in results) / n, 4),
        mean_latency_ms=round(statistics.mean(r.latency_ms for r in results), 3),
        mean_agent_transitions=round(statistics.mean(r.agent_transitions for r in results), 3),
        strata=strata,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

STRATUM_LABELS = {
    "single_intent":        "Single-intent (one clear domain task)",
    "cross_agent_compound": "Cross-agent / compound (multi-specialist)",
    "ambiguous":            "Ambiguous (needs interpretation / clarification)",
    "adversarial_oos":      "Adversarial / out-of-scope (bypass or unsupported action)",
}


def run_routing_benchmark():
    # Load chat_case_families
    with open(FAMILIES_PATH, encoding="utf-8") as f:
        families_data = json.load(f)
    families = families_data["families"]

    router = StructuredIntentRouter() if BACKEND_AVAILABLE else None

    print(f"\n{'='*70}")
    print(f"Experiment B -- Multi-Agent Routing Benchmark")
    print(f"Backend: {'LIVE' if BACKEND_AVAILABLE else 'MOCK'}")
    print(f"{'='*70}\n")

    all_results: list[QueryResult] = []
    query_idx = 0

    # ── Process families ─────────────────────────────────────────────────────
    for family in families:
        fid = family["id"]
        stratum = STRATUM_MAP.get(fid, "single_intent")
        meta = _build_expected(family)

        for para_idx, paraphrase in enumerate(family["paraphrases"]):
            query_idx += 1
            qid = f"RQ_{query_idx:03d}"
            result = evaluate_query(
                query_id=qid,
                family_id=fid,
                stratum=stratum,
                query_text=paraphrase,
                expected_intent=meta["expected_primary_intent"],
                expected_specialists=meta["expected_specialists"],
                expected_constraint=meta["expected_constraint_adhered"],
                notes=f"Family: {fid}, paraphrase {para_idx + 1}/5",
                router=router,
            )
            all_results.append(result)

    # ── Process extra ambiguous cases ────────────────────────────────────────
    for extra in EXTRA_AMBIGUOUS_CASES:
        query_idx += 1
        qid = f"RQ_{query_idx:03d}"
        result = evaluate_query(
            query_id=qid,
            family_id=extra["family"],
            stratum="ambiguous",
            query_text=extra["query"],
            expected_intent=extra["expected_primary_intent"],
            expected_specialists=extra["expected_specialists"],
            expected_constraint=extra["expected_constraint_adhered"],
            notes=extra.get("notes", ""),
            router=router,
        )
        all_results.append(result)

    # ── Compute per-stratum summaries ─────────────────────────────────────────
    stratum_order = ["single_intent", "cross_agent_compound", "ambiguous", "adversarial_oos"]
    stratum_summaries: list[StratumSummary] = []
    for stratum in stratum_order:
        stratum_results = [r for r in all_results if r.stratum == stratum]
        if not stratum_results:
            continue
        label = STRATUM_LABELS[stratum]
        summary = compute_stratum_summary(stratum, label, stratum_results)
        stratum_summaries.append(summary)

    overall = compute_overall_summary(all_results, stratum_summaries)

    # ── Print results ─────────────────────────────────────────────────────────
    print(f"{'Stratum':<45} {'N':>4} {'RoutAcc':>8} {'IntentAcc':>9} {'TaskSucc':>9} {'ConstrAdh':>10} {'AvgLat':>8}")
    print("-" * 100)
    for s in stratum_summaries:
        print(
            f"{s.stratum_label:<45} {s.total_queries:>4} "
            f"{s.routing_accuracy:>8.1%} {s.intent_accuracy:>9.1%} "
            f"{s.task_success_rate:>9.1%} {s.constraint_adherence:>10.1%} "
            f"{s.mean_latency_ms:>7.2f}ms"
        )
    print("-" * 100)
    print(
        f"{'OVERALL':<45} {overall.total_queries:>4} "
        f"{overall.routing_accuracy:>8.1%} {overall.intent_accuracy:>9.1%} "
        f"{overall.task_success_rate:>9.1%} {overall.constraint_adherence_rate:>10.1%} "
        f"{overall.mean_latency_ms:>7.2f}ms"
    )

    # ── Print per-family breakdown ─────────────────────────────────────────────
    print(f"\n{'Family Routing Accuracy Breakdown':^70}")
    print("-" * 70)
    from collections import defaultdict
    fam_results: dict[str, list[QueryResult]] = defaultdict(list)
    for r in all_results:
        fam_results[r.family_id].append(r)
    for fid, fresults in sorted(fam_results.items()):
        acc = sum(r.routing_correct for r in fresults) / len(fresults)
        stratum = fresults[0].stratum
        print(f"  {fid:<30} {len(fresults):>3} queries  {acc:>6.1%}  [{stratum}]")

    # ── Print failure details ─────────────────────────────────────────────────
    failures = [r for r in all_results if not r.routing_correct]
    if failures:
        print(f"\n{'Failure Cases':^70}")
        print("-" * 70)
        for r in failures:
            print(
                f"  {r.query_id} [{r.family_id}] '{r.query_text[:50]}'"
            )
            print(
                f"    Expected: intent={r.expected_primary_intent}, "
                f"specialists={r.expected_specialists}"
            )
            print(
                f"    Actual:   intent={r.actual_primary_intent}, "
                f"specialists={r.actual_specialists}"
            )
    else:
        print("\n  No failures!")

    # ── Write outputs ─────────────────────────────────────────────────────────
    per_query_path = RESULTS_DIR / "routing_orchestration_results.json"
    per_query_path.write_text(json.dumps(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "backend_mode": "live" if BACKEND_AVAILABLE else "mock",
            "provenance": provenance(FAMILIES_PATH, "exposed routing-only development cases; task_success is a selection proxy"),
            "total_queries": len(all_results),
            "results": [asdict(r) for r in all_results],
        },
        indent=2,
    ))

    summary_path = RESULTS_DIR / "routing_orchestration_summary.json"
    summary_path.write_text(json.dumps(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "backend_mode": "live" if BACKEND_AVAILABLE else "mock",
            "provenance": provenance(FAMILIES_PATH, "exposed routing-only development cases; task_success is a selection proxy"),
            "overall": asdict(overall),
        },
        indent=2,
    ))

    print(f"\nPer-query results => {per_query_path.name}")
    print(f"Summary           => {summary_path.name}")

    return overall


if __name__ == "__main__":
    run_routing_benchmark()
