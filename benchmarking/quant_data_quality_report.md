# QUANT data quality report (draft package)

Scope: `quant_holdout_ready.csv` / `quant_candidate_dataset.csv` / `quant_human_review.csv`, 977 synthetic rows. Checks were run by `tools/build_package.py`,
re-implementing the structural rules of `prepare_holdout.py` from the attached source. **The real `prepare_holdout.py` has not been run on this data** (it needs the
QUANT repository for the development-set file), so treat this as a pre-check, not as validation.

## 1. Summary
| Check | Result |
|---|---|
| 16 required columns present, exact template order | PASS |
| Missing values (excluding blank `anomaly_type` on normal rows) | PASS  |
| Types: ISO dates, tz-aware timestamps, positive amounts, debit/credit, taxonomy membership | PASS (0 errors) |
| Unique `record_id` | PASS |
| `tx_date` equals local date of `occurred_at` | PASS |
| PII patterns used by `prepare_holdout.py` (email, UPI handle, phone, PAN, 10-18 digit number) | PASS 0 matches; names are fictional |
| Definition consistency re-check of all 64 anomaly positives from the emitted CSV | PASS (0 violations) |
| >= 500 records | PASS (977) |
| >= 10 accounts | PASS (12) |
| >= 20 records per account | PASS (min 66) |
| >= 30 anomalies | PASS (64) |
| >= 10 per reported anomaly type | PASS (min 12) |
| >= 20 per category | PASS (min 21) |
| Overlap with QUANT development descriptions | **PENDING repository-side verification** |
| Leakage-free | **NOT CLAIMED** (see section 7) |
| Independent human validation | **NOT DONE** |

Expected failures when `prepare_holdout.py` is run on `quant_holdout_ready.csv` as-is: `consent_confirmed must be true` and `final labels require an independent reviewer` on every row (by design), and `diagnostic_only` because all rows are synthetic.

## 2. Category distribution
| Category | Rows | Share |
|---|---|---|
| Food & Dining | 165 | 16.9% |
| Transfer | 132 | 13.5% |
| Groceries | 126 | 12.9% |
| Transport | 121 | 12.4% |
| Shopping | 97 | 9.9% |
| Utilities | 66 | 6.8% |
| Other | 61 | 6.2% |
| Entertainment | 59 | 6.0% |
| Salary/Income | 46 | 4.7% |
| Investment | 30 | 3.1% |
| Healthcare | 28 | 2.9% |
| Rent | 25 | 2.6% |
| EMI | 21 | 2.1% |

Imbalance: largest/smallest = 7.9x. EMI (21), Rent (25) and Healthcare (28) clear the 20-row minimum only narrowly and their per-class F1 will be noisy.
Rent, EMI, Investment and Salary/Income rows are largely recurring, near-identical monthly debits, so effective diversity is lower than the row count suggests.

## 3. Anomaly distribution
| Anomaly type | Positives |
|---|---|
| amount_spike | 14 |
| duplicate_transaction | 13 |
| large_round_transfer | 12 |
| odd_hour | 13 |
| unusual_category_first_seen | 12 |

Positives: 64/977 = 6.6%. Hard-negative decoys (labelled normal): 27. Duplicate originals (labelled normal): 13. `other_confirmed`: 0.
Every positive is scenario-defined and unverified against any real event ("unverifiable" in the real-world sense).

## 4. Accounts
| Account | Rows | Anomaly positives |
|---|---|---|
| acct_q01 | 86 | 5 |
| acct_q02 | 86 | 7 |
| acct_q03 | 87 | 7 |
| acct_q04 | 75 | 4 |
| acct_q05 | 77 | 4 |
| acct_q06 | 83 | 4 |
| acct_q07 | 68 | 6 |
| acct_q08 | 66 | 6 |
| acct_q09 | 90 | 6 |
| acct_q10 | 85 | 5 |
| acct_q11 | 86 | 5 |
| acct_q12 | 88 | 5 |

Profiles: salaried, student, family, retiree, freelancer. Every account has at least one positive, so per-account Guardian recall is defined for all 12.
Single window, single quarter, one city per account.

## 5. Scenario inventory
| scenario_id | Rows |
|---|---|
| base | 873 |
| amount_spike | 14 |
| duplicate_original | 13 |
| duplicate_copy | 13 |
| odd_hour | 13 |
| large_round_transfer | 12 |
| first_seen_category | 12 |
| decoy_scheduled_mandate_odd_hour | 6 |
| decoy_same_amount_hours_apart_pair | 6 |
| decoy_same_amount_hours_apart | 6 |
| decoy_first_seen_small | 3 |
| decoy_large_but_below_threshold | 2 |
| decoy_round_to_established_payee | 2 |
| decoy_large_nonround_new_payee | 2 |

## 6. Label confidence and review load
- Confidence: high 840, medium 116, low 21.
- Review priority: high 123, medium 59, standard 795.
- Expect `prepare_holdout.py` to add warnings for low-confidence rows and for `single_review` status; both clear only through genuine review/adjudication.

## 7. Duplicates, consistency, leakage
- Exact normalised-description duplicates: 16 groups. 13 are the injected duplicate pairs; the other 3 are fixed-text bank charges that recur on different dates and are legitimately repeated.
- Near-duplicates by design: 6 same-merchant/same-amount pairs hours apart (labelled normal).
- Inconsistent-label check: 0 definition violations. This only shows labels follow the written definitions, not that the definitions are right.
- Template reuse: 188 merchant strings, 486 distinct digit-normalised narration templates across 12 accounts. The same merchants appear across accounts, so **do not split these rows randomly across development and evaluation**.
- Construction leakage risk: anomalies were injected by simple rules I chose; if Guardian's design resembles them, performance is inflated and not independent evidence.
- Development-set overlap: **pending repository-side verification**. No claim of leakage-freedom is made.

## 8. Other observations
- Credits: 84 rows; the rest are debits. Amount range 17.70-200,000.00; median debit 630.00.
- Timing: only the 13 odd_hour positives and 6 scheduled-mandate decoys fall in 01:00-04:59; the unrealistically clean separation makes odd-hour detection easier than in real data.
- Salary credits carry paise values (e.g. 77,792.21), which is less realistic than round figures.
