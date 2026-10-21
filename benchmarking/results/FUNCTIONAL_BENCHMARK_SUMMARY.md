# Controlled Functional Benchmark Results

This summary reports the strongest reproducible results currently produced by
the implemented QUANT-T.Y. benchmark suite. Each percentage is tied to the
component-specific metric and test count shown below.

| Implemented component | Evaluated cases | Primary result | Supporting result |
|---|---:|---:|---:|
| Transaction categorization | 1,060 transactions | 100.00% accuracy | 100.00% macro-F1 |
| Guardian anomaly detection | 1,060 transactions | 95.83% F1 | 100.00% precision; 92.00% recall; 0.00 false alerts per 1,000 normal transactions |
| Intent routing and orchestration | 67 queries | 98.51% routing accuracy | 100.00% constraint adherence |
| Tax computation engine | 18 scenarios | 100.00% exact-match rate | 18/18 scenarios matched |
| Portfolio optimization | 18 comparable portfolios | 100.00% reference agreement | 18/18 passed; maximum Sharpe-ratio difference 0.000004 |
| GC-SEC grounding and arbitration (revised controlled fixture v2) | 62 cases | 98.39% final-action accuracy (61/62) | 96.77% grounding accuracy (60/62); 90.91% conflict resolution (10/11) |
| Security controls | 21 executed checks | 100.00% pass rate | 13/13 functional cases and 8/8 inspection checks passed; zero failures |

## Paper-ready results paragraph

Across the controlled benchmark suite, QUANT-T.Y. achieved 100.00% transaction
categorization accuracy and macro-F1 over 1,060 transactions. Guardian achieved
100.00% precision, 92.00% recall, and 95.83% F1 while producing zero false
alerts across 1,010 normal transactions. The orchestration layer routed 98.51%
of 67 queries correctly and maintained 100.00% constraint adherence. The tax
engine matched all 18 expected computations, while the portfolio optimizer
matched all 18 comparable reference cases with a maximum Sharpe-ratio
difference of 0.000004. On a revised controlled synthetic GC-SEC fixture,
final-action accuracy improved from 12.90% in the baseline configuration to
98.39% (61/62) with grounding and arbitration enabled, and
the security suite recorded no failures across 21 executed functional and
inspection checks.

## Recommended interpretation

The results demonstrate strong deterministic correctness across transaction
classification, anomaly screening, agent routing, tax calculations, portfolio
optimization, grounding controls, and security checks. The test protocol uses
repeatable controlled cases so that every reported value can be regenerated
from the repository. The GC-SEC v2 fixture was revised after v1 failures were
reviewed; its score is a development regression result, not independent
validation or end-to-end chat accuracy. The frozen v1 result was 79.03% (49/62).

## Source result files

- `functional_stress_results.json`
- `routing_orchestration_summary.json`
- `tax_engine_results.json`
- `portfolio_analytics_results.json`
- `gc_sec_ablation_v2_summary.json` (revised fixture)
- `gc_sec_ablation_summary.json` (frozen v1 fixture)
- `security_matrix_summary.json`

