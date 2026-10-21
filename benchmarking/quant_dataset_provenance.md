# QUANT dataset provenance and limitations

## 1. Bottom line
- **Real records included: 0.** All 977 rows are synthetic (`data_origin=synthetic`).
- **No third-party dataset rows were copied, adapted or resampled.** Candidate public datasets were researched (section 2) but none was usable here.
- Labels are AI/scenario-proposed. No human has reviewed them; none is a verified or source-provided ground truth.
- This package cannot establish real-world accuracy. Under `prepare_holdout.py` any synthetic row forces a `diagnostic_only` package.

## 2. Public sources researched
Information below comes from web-search result snippets only; licences must be re-verified at the source before any use.
I could not fetch the Mendeley page (blocked by bot detection) or download any file in this environment.

| Source | Real / synthetic | Row-level? | Licence as listed | Why not used |
|---|---|---|---|---|
| Kaggle "UPI Transactions 2024 Dataset" (skullagos5246) | Synthetic (generator script) | Yes: id, type P2P/P2M/Bill/Recharge, amount, status, timestamp | CC0 | No merchant narrations or categories; synthetic; no anomaly labels |
| Kaggle "UPI Payment Transactions Dataset" (devildyno) | Simulated, 1,000 rows | Yes: sender/receiver names and UPI IDs, amount, status | MIT | Simulated; carries name/UPI-ID style fields; no categories or anomaly labels |
| Kaggle "Pattern-Based UPI Transaction Risk Dataset 2026" (kalpitlabs) | Synthetic, risk-oriented | Yes (not inspected in detail) | CC BY-NC-SA 4.0 | Non-commercial + share-alike; synthetic; rule-derived risk labels, not independent |
| Kaggle NPCI UPI ecosystem statistics (unknwn20); UPI monthly data 2016-2025; UPI-India-Payment-Data | Real **aggregates** from NPCI | No | Apache 2.0; CC BY-SA 4.0; unknown | Aggregate counts only; unusable for transaction categorisation |
| Kaggle "UPI Digital Payment Fraud in India (FY2023-FY2025)" | Not inspected | Unknown | Unknown | Appeared only as a title in a listing; not evaluated |
| PaySim / Kaggle "Synthetic Financial Datasets For Fraud Detection" | Synthetic, calibrated from one month of mobile-money logs from an African country | Yes | Not captured in my search results | Not Indian, no narrations/categories; "fraud" is a simulator rule (e.g. transfers above 200,000) |
| MoneyData / MoneyVis (Mendeley DOI 10.17632/dnxtg6n4rv.1; Eurographics DOI 10.2312/evs.20231052) | Described as real, anonymised retail bank transactions | Yes: date, type, description, debit/credit, balance; >6,500 rows over 7 years from July 2015, categorised | Paper page lists CC BY 4.0; **dataset licence not verified** | Could not access; country/bank and whether it spans one or many accounts are not stated in what I saw; no anomaly labels mentioned. **Best real-data lead** for categorisation, needs manual verification |
| IEEE DataPort deposit dataset (Caio Souza) | Real de-identified Brazilian deposits plus 1,000 synthetic fraudsters | Yes | Not verified | Deposits only; Brazil; synthetic fraudster injection |
| Hugging Face `mitulshah/transaction-categorization` | Mixed/uncertain sources, 4.5M rows, 10 categories | Yes | MIT (as listed) | Provenance of merged sources unclear; taxonomy differs; not India-specific |
| Hugging Face `DoDataThings/us-bank-transaction-categories-v2` | Synthetic, US formats | Yes | Apache-2.0 (model card) | US bank formats |
| Commercial panels (e.g. Yodlee) | Real, de-identified, US/UK | Yes | Paid licence | Not open data |

**Finding:** I found no public dataset that is simultaneously real, Indian/UPI-style, row-level with merchant narrations, and independently anomaly-labelled.
Real, consented data from volunteers' own statements (or a data-sharing agreement) is the only route to the intended independent holdout.

## 3. How the synthetic data was produced
- Script: `tools/generate_quant_candidate.py`, deterministic, seed `20261008`. `tools/build_package.py` writes the CSVs and runs checks.
- 12 pseudonymous accounts (`acct_q01`..`acct_q12`) with profiles: salaried (x5), student (x2), family household, retiree (x2), freelancer (x2).
- Window: 2026-07-01 to 2026-09-28 (90 days), all timestamps in IST (+05:30), single quarter only.
- Merchant names are real brand names used purely as narration text (no endorsement, no actual transactions). Person names are common first name + initial, fictional; any resemblance is coincidental.
- Narration styles imitate Indian statements (`UPI/P2M/<ref>/<MERCHANT>`, `POS XX1234 <MERCHANT> <CITY>`, `NEFT-...`, `IMPS-...`, `ACH D- ...`, `BBPS-...`) but were written from general knowledge, not copied from any statement.
- Category labels come from the merchant template; ambiguous templates are labelled with lower confidence and flagged.
- Anomaly labels come only from injected scenarios (`scenario_id` in the candidate file): 64 positives, plus 27 hard-negative decoys and 13 duplicate originals labelled normal.

### Label provenance columns (candidate file)
- `category_label_source`: `generator_merchant_template` (AI/template-proposed) or `ai_proposed_ambiguous_template` / `ai_proposed_taxonomy_rule` (ambiguous).
- `anomaly_label_source`: `generator_scenario_injected` (positive by construction), `generator_scenario_decoy_normal`, `generator_scenario_pair_original_normal`, or `generator_scenario_base_normal`.
- **No label in this package is "source-provided" or human-verified.**

## 4. Known limitations
1. Synthetic: distributions, merchant mixes, amounts and timings are my assumptions, not measurements. Anomaly prevalence (6.6%) is far above realistic fraud/anomaly rates, so precision, false-alert and F1 numbers from this set will not transfer.
2. Anomalies are constructed by simple rules, so a rule-based detector may do well or badly for reasons unrelated to real-world performance. I could not see the Guardian code, so I cannot say whether any scenario resembles its internal rules; independence from the implementation cannot be claimed.
3. Reference numbers are 6-9 digits. Real UPI RRNs are 12 digits, and `prepare_holdout.py` rejects any 10-18 digit number as PII, so real exports will need reference masking before they pass.
4. All timestamps carry seconds and a +05:30 offset; real statements often have date only. Clock-dependent claims (odd_hour, duplicate) are therefore only possible on this synthetic data.
5. Each account has one 90-day window and no earlier history, which limits the first-seen definition; several repeated fixed narrations (`SMS ALERT CHARGES`, `GST ON BANK CHARGES`, `ANNUAL DEBIT CARD FEE`) recur by design.
6. Overlap with QUANT's exposed development set (`cashflow_categorization_test_set.json`, 45 repeated descriptions) was **not checked**: **pending repository-side verification**. The generator was written without access to that file, but merchant names such as Zomato or Netflix may coincide with it.
7. `consent_confirmed` is `false` in the draft because no data subject exists; whether to treat that as not-applicable is the project's decision (see handoff).

## 5. Licence of this package
These files are original synthetic output created for QUANT; no third-party licence obligations apply because no third-party data was incorporated. Apply the project's own licence.
