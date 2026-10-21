# Independent holdout evaluation

This directory contains the reproducible workflow needed to turn reviewed,
de-identified bank records into a locked evaluation package. It deliberately
does not contain real transactions or final labels.

## What someone outside the implementation work must provide

Copy `templates/reviewer_labels_template.csv` to a location outside Git and
replace the example row with consented, de-identified records. Use pseudonymous
account IDs such as `acct_001`; remove names, account numbers, phone numbers,
emails, UPI handles, PANs, addresses, and free-text reviewer notes containing
identifiers. A reviewer who did not tune the categorizer or Guardian must fill
the labels and resolve uncertain cases.

For categorization, every row needs `expected_category`. For Guardian, every
row needs `is_anomaly`; positive rows also need `anomaly_type`. A timestamp with
an explicit timezone is required for `odd_hour` and `duplicate_transaction`.
Date-only records are valid but cannot be used to claim performance on those
two anomaly types.

Recommended minimums for a final paper run:

- 500 transactions across at least 10 pseudonymous accounts;
- at least 20 records per evaluated Guardian account;
- at least 30 confirmed anomalies overall and at least 10 examples of each
  anomaly type being reported separately;
- at least 20 examples of each transaction category being reported;
- account separation from all development data, with labels frozen before the
  final implementation commit is selected.

These are practical minimums, not a statistical guarantee. Report all class
supports and confidence intervals produced by the evaluator.

## Prepare and lock the private package

From the repository root:

```powershell
python benchmarking/holdout/prepare_holdout.py `
  --input C:\private\reviewed_transactions.csv `
  --output benchmarking/private_holdout/final_v1
```

The preparer validates the schema, rejects common forms of direct identifiers,
checks exact description overlap with the exposed development set, and writes:

- `features.csv`: inputs visible to the production components;
- `labels.csv`: labels used only by the evaluator;
- `manifest.json`: SHA-256 hashes, counts, taxonomy, and warnings.

Keep the entire output directory private. Committing `features.csv` can still
leak financial descriptions even though labels are separated. The repository's
`.gitignore` excludes the default private location.

## Freeze and evaluate

1. Commit the implementation to be evaluated.
2. Do not inspect or edit the sealed labels.
3. Verify the manifest and run:

```powershell
python benchmarking/holdout/evaluate_holdout.py `
  --package benchmarking/private_holdout/final_v1 `
  --output benchmarking/holdout/results/final_v1.json
```

The evaluator refuses altered packages, calls the production categorizer and
Guardian detector, groups Guardian records by account, and emits aggregate and
per-class metrics without copying raw descriptions into the result. The output
is also git-ignored by default so results can be reviewed before publication.

## What may be claimed

This workflow supports an **independent, de-identified holdout evaluation** only
when the labels were prepared and frozen without implementation-driven tuning.
The existing synthetic benchmarks remain development and stress tests. If the
same person modifies labels after seeing errors, describe the result as a
development evaluation and prepare a new final holdout.

## Published synthetic generator

For a reproducible stress test—not a final accuracy claim—generate a fresh
multi-account synthetic corpus with a recorded seed:

```powershell
python benchmarking/generate_synthetic_stress.py
python benchmarking/holdout/prepare_holdout.py `
  --input benchmarking/generated/synthetic_stress.csv `
  --output benchmarking/private_holdout/synthetic_stress `
  --allow-small
python benchmarking/holdout/evaluate_holdout.py `
  --package benchmarking/private_holdout/synthetic_stress `
  --output benchmarking/holdout/results/synthetic_stress.json `
  --diagnostic
```

The generator is deterministic for a given seed and marks every row as
`data_origin=synthetic`, which forces the package to remain diagnostic-only.
