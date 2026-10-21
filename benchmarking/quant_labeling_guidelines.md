# QUANT labeling guidelines (draft for human review)

Status: **provisional AI/scenario-proposed labels. Not human-verified, not frozen, not evaluated.**
All 977 records are `data_origin=synthetic`. Taxonomy and anomaly types are exactly those in `prepare_holdout.py`
(13 categories, 6 anomaly types). Where the attachments did not define a category precisely, the definition below is
**this package's own choice** and is listed as such; the QUANT repository's definitions could not be consulted.

## 1. Category definitions (taxonomy fixed by `prepare_holdout.py`)

| Category | Definition used here | Typical narrations |
|---|---|---|
| Food & Dining | Restaurants, cafes, food delivery, takeaway | Zomato, Swiggy, Starbucks |
| Groceries | Supermarkets, quick-commerce groceries, kirana, dairy | BigBasket, Blinkit, DMart |
| Transport | Cabs, fuel, tolls, metro/bus/rail, intercity tickets | Uber, FASTag, IRCTC, petrol pump |
| Shopping | Retail and e-commerce goods and apparel, electronics, jewellery | Flipkart, Myntra, Croma |
| Utilities | Electricity, water, gas, mobile/broadband/DTH bills and prepaid recharges | BESCOM, Airtel recharge |
| Entertainment | Streaming, cinema, events, games, subscriptions for leisure | Netflix, PVR, BookMyShow |
| Healthcare | Pharmacy, clinics, diagnostics, hospitals | Apollo Pharmacy, Lal PathLabs |
| Investment | Mutual-fund SIPs, stock/broker fund adds, NPS, PPF, RD/FD instalments | `ACH D- SIP ...`, broker fund add |
| Rent | Housing rent paid to a landlord | `.../RENT JUL` |
| Salary/Income | Salary, pension, stipend, client/freelance payments, **interest credits** | `... SALARY JUL`, `PENSION CREDIT` |
| Transfer | Person-to-person, self and family transfers (debit or credit), wallet loads | `UPI/P2A/<ref>/<NAME>` |
| Other | Cash withdrawals, bank charges, insurance, card bill payments, government fees, uninformative narrations | `ATM WDL`, `SMS ALERT CHARGES` |
| EMI | Recurring loan instalments paid by mandate | `ACH D- <LENDER> EMI` |

### Package-specific decision rules (reviewer may overrule; record disagreements)
- **G1 Wallet loads** (Paytm / Amazon Pay top-ups) -> Transfer, confidence low.
- **G2 Credit-card bill payments** -> Other, confidence medium (Transfer and EMI are defensible).
- **G3 Insurance premiums** (e.g. LIC) -> Other, confidence medium (Investment is defensible for endowment products).
- **G4 Gym / fitness memberships** -> Entertainment, confidence medium (Healthcare is defensible).
- **G5 Hypermarkets** (Reliance Smart) -> Groceries, confidence medium (Shopping is defensible).
- **G6 Non-informative narrations** (`PAYMENT TO MERCHANT`) -> Other, confidence low; the true category is unknowable from the text.
- **G7 Refund credits** take the category of the original merchant (Shopping), confidence medium; Other/Transfer are defensible.
- **G8 Interest credits** -> Salary/Income (the taxonomy has no separate income class), confidence medium.
- **G9 Cash withdrawals and bank fees** -> Other, confidence high.
- If you disagree with a rule, change the label **and** note the rule id in `reviewer_comments` so systematic disagreements can be counted.

## 2. Anomaly definitions used to build the labels

Anomaly labels exist only because a documented synthetic scenario was injected. **No label here is a confirmed fraud or a real-world event.**
Unusual size, timing, repetition or novelty is never treated as fraud by itself; the definitions below are narrow on purpose.

| Type | Positive definition (what the generator injected) | Hard negatives included (labelled normal) |
|---|---|---|
| amount_spike | Debit at a merchant already used in the account, amount >= 9x the account's median for that category (base transactions) and >= 5,000 | Same-merchant purchases at 3.5-6x the median (`decoy_large_but_below_threshold`) |
| duplicate_transaction | A second posting with identical narration (incl. reference) and amount, 25-150 s after the original, same account. The original is labelled normal. | Same merchant and amount, different reference, hours apart (`decoy_same_amount_hours_apart`) |
| large_round_transfer | Debit Transfer, amount a multiple of 5,000 and >= 50,000, to a payee not seen earlier in the account (all prior transfers <= 7,500) | Round 50-60k to an established payee; large non-round transfer to a new payee (`decoy_*`) |
| odd_hour | Customer-initiated debit between 01:00 and 04:59 IST in an account with no other customer-initiated activity in that window | Scheduled NACH/ACH mandate debits timestamped 01:00-04:59 (`decoy_scheduled_mandate_odd_hour`); students' habitual 23:00-00:45 food orders are ordinary base rows |
| unusual_category_first_seen | First-ever transaction of a category in the account's history **within this 90-day window** and >= 5x the account's median debit | First-ever category use with a small amount (`decoy_first_seen_small`) |
| other_confirmed | **Not used.** Nothing here is an independently confirmed anomaly. | n/a |

The first-seen rule only sees the 90-day window; there is no earlier history, so "first seen" means "first in this window".

## 3. Review procedure (for the human teammate)

You are expected to be someone who did **not** build or tune the QUANT categorizer or Guardian detector. Do not run QUANT on these rows before labelling.

1. Open `quant_human_review.csv`. Columns `proposed_*` are AI/scenario proposals. Fill the blank columns.
2. For every row set `human_category` (one of the 13), `human_is_anomaly` (true/false), `human_anomaly_type` (blank when false) and `review_status`:
   - `accepted`: you agree with all proposed labels (copy them into the human columns; do not leave them blank);
   - `corrected`: you changed something, with a reason in `reviewer_comments`;
   - `flagged`: genuinely undecidable; explain. Flagged rows should be excluded or adjudicated by a second reviewer.
3. Review order: all `review_priority=high` rows first (anomaly positives, every hard-negative decoy, duplicate originals, low-confidence), then `medium`, then `standard`. Cover every row; if you cannot, record the sampling plan and error rate honestly.
4. For anomaly rows, judge against the **definitions in section 2**, using the account's surrounding rows (sort by `account_id`, `occurred_at`). Disagreeing with a definition is a finding to record, not a reason to quietly relabel.
5. Optional but recommended: a second reviewer independently labels at least 20% of rows (include all decoys); report agreement and resolve disagreements (`adjudication_status=adjudicated` in the final CSV).
6. Never copy real customer data into this file. Reviewer identities must be pseudonyms (`reviewer_<id>`).

## 4. Fields that stay unresolved until you act
`reviewer_id`, `reviewer_independent`, `adjudication_status` and `consent_confirmed` in `quant_holdout_ready.csv` are deliberately set to
`reviewer_PENDING / false / single_review / false`. Do not change them to `true` unless it is true; see the handoff file for the synthetic-consent question.
