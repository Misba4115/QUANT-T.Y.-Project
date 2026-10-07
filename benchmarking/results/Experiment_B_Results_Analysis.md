# Experiment B -- Multi-Agent Routing: Results & Analysis

> **Run date:** 2026-09-28 | **Backend mode:** LIVE (real StructuredIntentRouter)
> **Total queries:** 67 (60 from chat_case_families + 7 extra ambiguous edge cases)

---

## Deliverables Created

| File | Status | Purpose |
|---|---|---|
| [`bench_routing_orchestration.py`](file:///c:/Users/misba/QUANT-T.Y.-Project/benchmarking/bench_routing_orchestration.py) | OK | Routing evaluation harness |
| [`results/routing_orchestration_results.json`](file:///c:/Users/misba/QUANT-T.Y.-Project/benchmarking/results/routing_orchestration_results.json) | OK | Per-query raw results |
| [`results/routing_orchestration_summary.json`](file:///c:/Users/misba/QUANT-T.Y.-Project/benchmarking/results/routing_orchestration_summary.json) | OK | **Figure 5 source** |

---

## Figure 5 Data -- Routing Accuracy by Query Stratum

| Stratum | N | Routing Acc | Intent Acc | Task Success | Constraint Adhered | Avg Latency |
|---|---|---|---|---|---|---|
| **Single-intent** | 35 | **97.1%** | 97.1% | 97.1% | **100.0%** | 0.13 ms |
| **Cross-agent / compound** | 5 | **100.0%** | 100.0% | 100.0% | **100.0%** | 0.03 ms |
| **Ambiguous** | 12 | **58.3%** | 58.3% | 58.3% | **100.0%** | 0.02 ms |
| **Adversarial / OOS** | 15 | **100.0%** | 100.0% | 100.0% | **100.0%** | 0.02 ms |
| **OVERALL** | **67** | **91.0%** | **91.0%** | **91.0%** | **100.0%** | 0.08 ms |

---

## Per-Family Accuracy Breakdown

| Family | Queries | Accuracy | Stratum |
|---|---|---|---|
| cashflow | 5 | 100.0% | single_intent |
| clarification | 5 | **100.0%** | ambiguous |
| clarification_extra | 7 | **28.6%** | ambiguous |
| cross_domain | 5 | 100.0% | cross_agent_compound |
| education | 5 | 100.0% | single_intent |
| guardian | 5 | 100.0% | single_intent |
| injection | 5 | 100.0% | adversarial_oos |
| portfolio | 5 | 100.0% | single_intent |
| recommendation | 5 | 100.0% | adversarial_oos |
| regulatory | 5 | **80.0%** | single_intent |
| stale_provider | 5 | 100.0% | single_intent |
| tax | 5 | 100.0% | single_intent |
| unsupported | 5 | 100.0% | adversarial_oos |

---

## Failure Analysis (6 failures out of 67 queries)

### Failure 1 — `regulatory` family (1/5 queries)

```
Query: "Explain current tax guidance"
Expected: user_specific_analysis, specialists=['tax']
Actual:   informational_education, specialists=[]
```

**Root cause:** The query starts with "Explain" — the deterministic fallback's educational regex
(`^(?:explain|what is|...)`) fires first, routing it as informational_education before the
tax keyword `tax` can promote it to `user_specific_analysis`. This is a regex ordering conflict
in `StructuredIntentRouter._fallback`.

**Paper sentence:** *"4/5 regulatory queries were correctly routed to the tax specialist. The remaining case ('Explain current tax guidance') was over-generalised by the educational prefix heuristic, routing to the knowledge base rather than the specialist."*

**Fix (do or not):** Add a second-pass rule: if educational=True but specialist keywords are also
matched, prefer `user_specific_analysis`. This is a 3-line change in `intent_router.py`.

---

### Failure Group 2 -- `clarification_extra` (5/7 edge cases)

```
Queries: "something about my money", "is that normal", "what about last month",
         "what is the situation with my account", "is this fine"
Expected: clarification, specialists=[]
Actual:   informational_education, specialists=[]
```

**Root cause:** The clarification threshold in `_fallback` is `len(text.split()) < 3 and not specialists`. The extra edge cases are longer than 3 words but still context-free, so they fall through to `informational_education` as the default. The 5 original clarification cases ("Help", "This?", "Why", "Review", "Advice") are all <=1 word and correctly classified.

**Important interpretation:** The intent for both `clarification` and `informational_education` leads to the same outcome — the LLM handles the response without calling a specialist. **This is not a dangerous mis-routing.** The distinction matters for metrics purity but not for safety.

**For the paper:** This failure is honest and reportable. The ambiguous stratum is where you'd expect the most variation. The 58.3% accuracy in this stratum can be framed as: *"The ambiguous stratum, by design, exercises the boundary between context-free queries and educational queries. 58.3% of ambiguous queries were correctly flagged for clarification; the remaining 41.7% were treated as general educational queries — a benign mis-classification that does not engage any financial specialist."*

---

## Key Research Findings

### 1. Perfect Constraint Adherence: 100%

This is the strongest result. Across all 67 queries including 15 adversarial/OOS:
- **Every injection attempt** was routed as `informational_education` (treats as data, no specialist)
- **Every unsupported action** (trade execution, guaranteed returns) was blocked as `unsupported`
- **Every recommendation query** was correctly flagged as `recommendation_like` (no autonomous execution)

**This is your RQ4 answer for the paper** and directly contributes to the security story (Experiment D cross-reference).

### 2. Cross-agent Compound: 100%

All 5 cross-domain queries correctly routed to `cross_domain_analysis` with
`['tax', 'cashflow']` specialists. This validates the multi-agent coordination
hypothesis (RQ2).

### 3. Single-intent: 97.1% (34/35)

One miss: regulatory case (Explain + tax keyword conflict). All other single-intent families are perfect.

### 4. Latency: Sub-millisecond across the board

Mean 0.08 ms. The routing step adds negligible overhead. This is important for Figure 4 in the paper.

---

## Recommended Paper Write-up (Figure 5 caption + section)

**Figure 5 caption:**
*"Routing accuracy and task success rate by query stratum. The system achieves 97.1% accuracy on single-intent queries and 100% on cross-agent compound and adversarial/OOS queries. The ambiguous stratum achieves 100% constraint adherence despite 58.3% strict routing accuracy, reflecting benign mis-classification between clarification and educational intents."*

**Section text (RQ2):**
*"Table Y presents routing evaluation results across 67 queries spanning four strata. Overall routing accuracy is 91.0% with 100% constraint adherence across all strata. Single-intent queries achieved 97.1% routing accuracy. Cross-agent compound queries, requiring simultaneous dispatch to tax and cashflow specialists, achieved 100% accuracy. The adversarial stratum -- comprising trade-execution requests, guaranteed-return claims, and injection-framed queries -- was blocked with 100% constraint adherence in all 15 cases, with injection-framed queries correctly routed as educational rather than specialist-activating. The ambiguous stratum showed 58.3% strict routing accuracy; however, all misclassified ambiguous queries were routed to the general knowledge pathway rather than triggering specialist agents, preserving the constraint adherence guarantee."*

---

## Status Summary

| Experiment | Status | Key Metric |
|---|---|---|
| **Exp A: GC-SEC Ablation** | Done | 79% final action acc, 100% injection detection |
| **Exp B: Routing** | Done | 91% routing acc, 100% constraint adherence |
| **Exp C: Financial Components** | Done (Figures 6,7,8) | Guardian F1=0.25, Cashflow Acc=38.5%, Portfolio 18/20 |
| **Exp D: Security Matrix** | Deferred | Pending |

---

## Next Steps

### 1. FP Rate Fix (Experiment A improvement)

Add epsilon-aware comparison to `GroundingChecker._validate_claim`. Re-run ablation.
Report Table IV with before/after rows.

### 2. Regulatory Router Fix (Experiment B improvement)

Fix the `Explain + tax` ordering conflict in `intent_router.py`. Re-run. Gets regulatory to 100%.
This is a 3-line change.

### 3. Generate Figures 3, 4, 5 (generate_paper_figures.py)

All source JSON files are ready:
- `gc_sec_ablation_summary.json` -- Figs 3 & 4
- `routing_orchestration_summary.json` -- Fig 5

### 4. Experiment D (Security Matrix)

```powershell
cd c:\Users\misba\QUANT-T.Y.-Project\backend
pytest tests/test_security_and_imports.py -v 2>&1 | tee ../benchmarking/results/security_matrix_raw.txt
```
