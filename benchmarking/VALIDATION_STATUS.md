# Benchmark validation status (2026-10-21)

These reruns are **development diagnostics**, not independent validation. The
synthetic cases and labels were visible while the implementation was revised.
Do not copy the improved percentages into the paper as real-world accuracy.
Each regenerated JSON records the dataset SHA-256, source commit, dirty-tree
state, and evaluation scope. Re-run from a clean, pinned commit for publication.

| Component | Current development result | What it establishes | What it does not establish |
| --- | --- | --- | --- |
| Cashflow categorizer | 196/200 (98.0%) | Production categorizer now covers categories absent before; label mapping no longer converts `Other`/`EMI` to `Transfer`. | Generalization to unseen merchants, UPI narrations, accounts, or manually labeled bank records. The 200 rows repeat only 45 descriptions; `Other` and `EMI` have zero true support. |
| Guardian | 44 TP, 2 FP, 16 FN, 448 TN; F1 83.0% | Benchmark imports the production detector; date-only data is not treated as having a clock time. | Deployment accuracy or calibrated alert rate. The 510 transactions are one synthetic pooled corpus without account IDs and the detector fits on that same corpus. Duplicate accuracy therefore assumes a single account; amount-spike recall is only 2/10. |
| Routing | 66/67 (98.5%) | Production router handles the exposed cases after an underspecified-follow-up fix. | Successful end-to-end responses. `task_success_rate` is a routing-selection proxy. The remaining “Explain current tax guidance” case appears to have a questionable user-specific oracle. |
| GC-SEC | Revised v2 fixture: baseline 12.9%, grounding-only 82.3%, grounding+arbitration 98.4% (61/62) final-action accuracy | Explicit market timestamps, corrected calculation fixtures and safety oracles, and the live backend improve the controlled regression result. The frozen v1 result was 79.0%. | Real-world grounding or end-to-end chat quality. V2 was revised after v1 failures were inspected. One conflict case (TC_051) still fails; the chat path uses a different response-grounding check. Independent adjudication and holdout evaluation remain necessary. |
| Tax | 18/18 scenario matches | Production formula helpers match the illustrative scenarios. | Accuracy of the complete tax workflow or current legal compliance. Scenario expected values are illustrative and need an authoritative assessment-year review. |

The historical security matrix is **not** a verified security score: it recorded
13 functional passes, 8 inspection-only checks, and 7 cases not run. Its claim
that the full app could not load because NumPy was unavailable is stale in the
current environment. Rebuild it against a disposable Supabase test project with
real RLS/storage policies, two users, signed URLs, cookies, malformed uploads,
and hostile connector payloads. Do not include inspection or not-run rows in a
functional pass rate.

The portfolio benchmark directly calls the production optimizer, but its
reference comparison is limited to the cases where the reference solver
returned a solution. Report the comparable-case denominator and the actual
weight/Sharpe deviations; do not turn that comparison into a broad “accuracy”
percentage.

## Independent evaluation protocol before paper revision

1. Freeze the implementation and record the commit, environment, dataset hash,
   metric code, taxonomy, and decision threshold. Do not tune on the final set.
2. Collect consented, de-identified bank data with human-reviewed categories
   and anomaly labels. Keep account/time blocks separate between development
   and final evaluation. Do not split repeated merchant templates randomly
   across both sides. Synthetic data may remain as a stress-test supplement.
3. Use a reviewer who did not implement the rules to adjudicate ambiguous
   labels. Report unknown/abstain and class support, not just overall accuracy.
4. For Guardian, evaluate per account and per time window with only prior data
   available at each decision; tune thresholds on development accounts only.
   Report precision, recall, false alerts per 1000 transactions, confidence
   intervals, and results by anomaly type. Clock-based claims require actual
   timestamps. Apply migration `007_guardian_transaction_time.sql` before
   importing timestamps; existing date-only records cannot support odd-hour or
   exact-timestamp duplicate detection.
5. For routing and GC-SEC, run full response workflows on a separately written
   holdout with adjudicated expected actions and winning claims. Keep routing
   selection accuracy distinct from answer/task success. Review the 62-case
   GC-SEC fixture's missing calculation traces and market observation times
   rather than weakening the checker to match labels.
6. Only after that rerun, replace Section VI onward: identify synthetic versus
   real data, give denominators/uncertainty, name the exact production path,
   and remove unsupported security, grounding, and end-to-end claims.

No final independent holdout was available in this workspace at this point.
