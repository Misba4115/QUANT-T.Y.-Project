# Handoff: validating the QUANT draft dataset and passing it to Codex

Nothing here has been frozen, independently validated or evaluated. All 977 rows are **synthetic** with AI/scenario-proposed labels.

## What this package is (and is not)
- It is a reviewer-ready **synthetic supplement / stress test** with hard negatives. It is **not** the real, consented, independent holdout the README calls for, and the existing workflow will always mark it `diagnostic_only` because of `data_origin=synthetic`.
- For the paper's real-world claim you still need consented, de-identified real statements. Start from the leads in `quant_dataset_provenance.md` (MoneyData needs manual licence/country verification; it has no anomaly labels) or collect volunteers' statements, masking 10+ digit references first.

## Steps for your teammate
1. Read `quant_labeling_guidelines.md`. The reviewer must not be someone who tuned the categorizer or Guardian, and must not run QUANT on the rows first.
2. Complete `quant_human_review.csv` (`human_category`, `human_is_anomaly`, `human_anomaly_type`, `reviewer_comments`, `review_status`, `reviewer_id` as `reviewer_<pseudonym>`). Do `high` priority rows first (123), then `medium` (59), then `standard` (795).
3. Recommended: a second reviewer labels at least 20% (all decoys included); resolve differences and report agreement.
4. Build the final CSV from `quant_holdout_ready.csv`, keeping the exact 16 column names:
   - `expected_category`, `is_anomaly`, `anomaly_type` <- the human columns (drop or fix `flagged` rows, never silently keep proposals);
   - `label_confidence` <- your own confidence;
   - `reviewer_id` <- real pseudonym; `reviewer_independent` <- `true` **only if** the reviewer meets the independence condition;
   - `adjudication_status` <- `adjudicated` only if disagreements were genuinely resolved;
   - `consent_confirmed`: there are no data subjects. `prepare_holdout.py` rejects `false`. Either the project decides to record `true` with a written "synthetic, not applicable" justification, or Codex adds a synthetic exemption to the validator. This was left `false` rather than asserting something unverified.
   - `data_origin` stays `synthetic`.
5. Save as e.g. `quant_holdout_final.csv`.

## Files to give Codex
| Give | Purpose |
|---|---|
| `quant_holdout_final.csv` (your reviewed version) | Input to `prepare_holdout.py` (`--allow-small`, which will be needed because of synthetic rows) |
| Completed `quant_human_review.csv` | Audit trail of accepted/corrected/flagged labels |
| `quant_labeling_guidelines.md`, `quant_dataset_provenance.md`, `quant_data_quality_report.md` | Documentation; reviewers' decisions on rules G1-G9 |
| `tools/generate_quant_candidate.py`, `tools/build_package.py` | Reproducibility (seed 20261008) |

**Do not give Codex or the QUANT dev environment** `quant_candidate_dataset.csv` or the unreviewed `ai_reasoning_notes`: they reveal how anomalies were constructed and could be used to tune the detector before freezing. Keep the package private (the README already git-ignores `benchmarking/private_holdout`).

## What Codex must still do
- Run `prepare_holdout.py`; the overlap warning is the missing leakage check (**pending repository-side verification**). Record the overlap count, and if it is non-zero, report or drop those rows rather than relabel.
- Freeze/commit the implementation **before** looking at results, per the README. Report class supports, Wilson intervals and the synthetic caveat; describe results as a diagnostic stress test, not independent real-world accuracy.
