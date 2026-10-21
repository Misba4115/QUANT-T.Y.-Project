# Benchmark Test Sets — Handoff Notes

The consolidated paper-ready results are in
[`results/FUNCTIONAL_BENCHMARK_SUMMARY.md`](results/FUNCTIONAL_BENCHMARK_SUMMARY.md),
and the reproducible multi-account run is provided by
`bench_functional_stress.py`.

The revised GC-SEC development fixture is generated without changing the
frozen v1 input or results:

```powershell
python benchmarking/build_gc_sec_test_set_v2.py
python benchmarking/bench_gc_sec_ablation.py --dataset benchmarking/gc_sec_test_set_v2.json --output-prefix gc_sec_ablation_v2
```

Its 62-case result and provenance are in
`results/gc_sec_ablation_v2_summary.json`. This fixture was revised after v1
failures were inspected and is not an independent holdout.

These files are synthetic development sets, not independent validation. The
current audited results, remaining limitations, and holdout protocol are in
[`VALIDATION_STATUS.md`](VALIDATION_STATUS.md). Benchmark outputs must not be
presented as real-world accuracy without the separate evaluation described
there.

## Files and what to do with each

### 1. `reference_user_profile.json`
Anchor dataset. Load this as the active "test user" before running `rag_chatbot_answer_test_set.json`, since those questions' correct answers are derived directly from these numbers. Not a test set on its own.

### 2. `guardian_anomaly_test_set.json`
510 synthetic transactions, 60 labeled anomalous across 5 anomaly types (amount spikes, duplicates, odd-hour transactions, first-seen high-risk categories, large round transfers).
**Script should:** run Guardian's detector on every transaction, compare predicted flag to `is_anomaly`, compute Precision/Recall/F1/ROC-AUC/false-positive-rate. Break results down by `anomaly_type` too — some types (e.g. duplicates) are usually easier to catch than others (e.g. odd-hour), and reporting that breakdown makes a stronger presentation slide than one blended number.

### 3. `portfolio_analytics_test_set.json`
20 synthetic portfolios (returns, volatility, correlation matrix per asset).
**Script should:** feed each portfolio's inputs into both your Portfolio Analytics Engine and a reference library (PyPortfolioOpt — `pip install PyPortfolioOpt`), compare resulting weights and Sharpe ratio, report % deviation. This is a correctness check, not an accuracy %.

### 4. `tax_engine_test_set.json`
18 capital-gains scenarios + 5 Section 80C scenarios, each with a computed `expected_output`.
**⚠️ Read the `IMPORTANT_DISCLAIMER` field in the file before using this.** The rates used to compute `expected_output` (LTCG exemption, LTCG/STCG rates, 80C cap) are illustrative placeholders — verify them against the current official rates for your assessment year, and regenerate `expected_output` if they differ, before treating this as ground truth.
**Script should:** run Tax Engine on each scenario's `inputs`, compare to `expected_output` field-by-field, report exact-match rate. A rule-based engine should be at/near 100% — anything less is a bug to fix, not a number to present as-is.

### 5. `cashflow_categorization_test_set.json`
200 labeled transactions across 11 categories.
**Script should:** run the categorizer on `raw_description`, compare to `correct_category`, report overall accuracy plus a confusion matrix — categories aren't evenly represented, so overall accuracy alone can hide a category the model is bad at.

### 6. `rag_retrieval_test_set.json`
30 template questions. **`expected_source_chunk_id` is a placeholder — fill it in against your real ingested documents before running this**, since I don't have access to your actual knowledge base content.
**Script should:** run each question through your retriever, check whether the correct chunk appears in the top-k results (Recall@k) and how highly it ranks (MRR).

### 7. `rag_chatbot_answer_test_set.json`
50 questions with known-correct facts, tied to `reference_user_profile.json`.
**Script should:** load the reference profile as test data, run each question through the full chatbot pipeline, then:
- Compare the answer against `expected_answer_facts` (near-match is fine, doesn't need to be exact wording)
- Run RAGAS (`pip install ragas`) for faithfulness/answer-relevancy/context-precision using the retrieved context
- Also log how often your Grounding Checker corrected or flagged something — that rejection rate is a genuinely strong, unique metric for your presentation

## Suggested script structure (same shape for all seven)

```
load test_set.json
for each item:
    run component under test
    compare output to expected
    log result
compute aggregate metrics
write results to results/<component>_results.json
print summary table
```

Keeping every script in this same shape means you end up with one consistent results format across all six components, which makes building your final comparison slide much easier.
