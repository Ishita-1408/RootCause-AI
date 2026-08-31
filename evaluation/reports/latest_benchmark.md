# RootCause AI Benchmark Report (Structured Causal Evaluator v2)

## Overall Results

| Metric | Score |
|---|---:|
| Scenarios Evaluated | 115 |
| Top-1 Accuracy | 87.0% |
| Top-3 Accuracy | 96.5% |
| Mean Reciprocal Rank (MRR) | 0.9174 |
| False Positive Rate | 0.483 |
| Mean Contribution Error | 84.7% |
| Evidence Grounding Rate | 100.0% |
| Unsupported Claim Rate | 0.000 |
| Hallucination Rate | 0.000 |
| Avg Investigation Steps | 3.4 |
| Avg Analytical Tool Calls | 2.7 |
| Avg Execution Time | 719.9 ms |

> **Date Registry Integrity Note:** All 115 benchmark scenarios are evaluated against active Olist e-commerce transaction dates. Exactly 6 scenarios (`SCN-053`, `SCN-062`, `SCN-067`, `SCN-079`, `SCN-086`, `SCN-109`) had their inactive late-2016 blackout dates moved to active 2017 transaction windows, and `SCN-094` was separately disambiguated from a duplicate date to `2017-04-20` (7 scenario records with date-related changes in total, with 6 migrating from inactive 2016 dates). Ground-truth causes, mechanisms, distractors, and evaluation scoring remained 100% unchanged.

## Difficulty Stratification

| Tier | Scenarios | Top-1 Accuracy | MRR |
|---|---:|---:|---:|
| **Easy** (Clear Single Driver) | 45 | 88.9% | 0.9333 |
| **Medium** (Multi-Factor Drivers) | 48 | 89.6% | 0.9271 |
| **Hard** (Competing / Distractors / Noise) | 22 | 77.3% | 0.8636 |

## Scenario Results

| Scenario | Difficulty | Ground Truth | Top-1 | Top-3 | MRR | Error | Grounded |
|---|:---:|---|:---:|:---:|:---:|:---:|:---:|
| **SCN-001** | `easy` | `logistics_fulfillment_bottleneck` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-002** | `easy` | `order_volume_drop` | ✓ | ✓ | 1.000 | 1.5% | ✓ |
| **SCN-003** | `medium` | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 9.0% | ✓ |
| **SCN-004** | `easy` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-005** | `medium` | `average_order_value_contraction` | ✓ | ✓ | 1.000 | 69.5% | ✓ |
| **SCN-006** | `easy` | `order_volume_surge` | ✓ | ✓ | 1.000 | 37.1% | ✓ |
| **SCN-007** | `easy` | `order_volume_surge` | ✗ | ✗ | 0.000 | 70.0% | ✓ |
| **SCN-008** | `easy` | `average_order_value_expansion` | ✗ | ✓ | 0.500 | 55.2% | ✓ |
| **SCN-009** | `easy` | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 0.1% | ✓ |
| **SCN-010** | `medium` | `order_volume_surge` | ✓ | ✓ | 1.000 | 0.0% | ✓ |
| **SCN-011** | `hard` | `order_volume_drop` | ✗ | ✓ | 0.500 | 53.9% | ✓ |
| **SCN-012** | `easy` | `order_volume_drop` | ✗ | ✓ | 0.500 | 72.4% | ✓ |
| **SCN-013** | `easy` | `order_volume_surge` | ✓ | ✓ | 1.000 | 21.4% | ✓ |
| **SCN-014** | `medium` | `average_order_value_contraction` | ✓ | ✓ | 1.000 | 46.8% | ✓ |
| **SCN-015** | `easy` | `order_volume_drop` | ✓ | ✓ | 1.000 | 4.0% | ✓ |
| **SCN-016** | `medium` | `order_volume_surge` | ✓ | ✓ | 1.000 | 18.1% | ✓ |
| **SCN-017** | `easy` | `average_order_value_contraction` | ✓ | ✓ | 1.000 | 0.0% | ✓ |
| **SCN-018** | `easy` | `order_volume_surge` | ✓ | ✓ | 1.000 | 16.8% | ✓ |
| **SCN-019** | `medium` | `order_volume_surge` | ✓ | ✓ | 1.000 | 0.0% | ✓ |
| **SCN-020** | `medium` | `average_order_value_expansion` | ✗ | ✓ | 0.500 | 23.5% | ✓ |
| **SCN-021** | `medium` | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 0.0% | ✓ |
| **SCN-022** | `easy` | `order_volume_surge` | ✓ | ✓ | 1.000 | 21.0% | ✓ |
| **SCN-023** | `hard` | `order_volume_drop` | ✓ | ✓ | 1.000 | 205.2% | ✓ |
| **SCN-024** | `easy` | `order_volume_surge` | ✓ | ✓ | 1.000 | 4.1% | ✓ |
| **SCN-025** | `easy` | `order_volume_drop` | ✓ | ✓ | 1.000 | 79.6% | ✓ |
| **SCN-026** | `easy` | `order_volume_surge` | ✓ | ✓ | 1.000 | 13.6% | ✓ |
| **SCN-027** | `medium` | `order_volume_surge` | ✓ | ✓ | 1.000 | 41.6% | ✓ |
| **SCN-028** | `medium` | `order_volume_surge` | ✓ | ✓ | 1.000 | 68.1% | ✓ |
| **SCN-029** | `easy` | `order_volume_surge` | ✓ | ✓ | 1.000 | 7.5% | ✓ |
| **SCN-030** | `medium` | `order_volume_drop` | ✓ | ✓ | 1.000 | 1232.5% | ✓ |
| **SCN-031** | `medium` | `order_volume_surge` | ✓ | ✓ | 1.000 | 36.3% | ✓ |
| **SCN-032** | `easy` | `order_volume_surge` | ✓ | ✓ | 1.000 | 28.6% | ✓ |
| **SCN-033** | `easy` | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 72.3% | ✓ |
| **SCN-034** | `easy` | `average_order_value_contraction` | ✓ | ✓ | 1.000 | 194.7% | ✓ |
| **SCN-035** | `medium` | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 50.5% | ✓ |
| **SCN-036** | `medium` | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 7.5% | ✓ |
| **SCN-037** | `easy` | `average_order_value_contraction` | ✓ | ✓ | 1.000 | 7.8% | ✓ |
| **SCN-038** | `easy` | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 268.3% | ✓ |
| **SCN-039** | `medium` | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 26.9% | ✓ |
| **SCN-040** | `easy` | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 9.5% | ✓ |
| **SCN-041** | `easy` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-042** | `easy` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-043** | `medium` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-044** | `easy` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-045** | `medium` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-046** | `easy` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-047** | `medium` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-048** | `easy` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-049** | `easy` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-050** | `medium` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-051** | `easy` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-052** | `medium` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-053** | `easy` | `order_volume_surge` | ✓ | ✓ | 1.000 | 122.0% | ✓ |
| **SCN-054** | `easy` | `order_volume_drop` | ✗ | ✓ | 0.500 | 27.9% | ✓ |
| **SCN-055** | `easy` | `order_volume_surge` | ✓ | ✓ | 1.000 | 47.9% | ✓ |
| **SCN-056** | `easy` | `order_volume_drop` | ✓ | ✓ | 1.000 | 5.8% | ✓ |
| **SCN-057** | `easy` | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 103.1% | ✓ |
| **SCN-058** | `easy` | `average_order_value_contraction` | ✓ | ✓ | 1.000 | 37.4% | ✓ |
| **SCN-059** | `easy` | `logistics_fulfillment_bottleneck` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-060** | `easy` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-061** | `easy` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-062** | `easy` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-063** | `easy` | `order_volume_surge` | ✓ | ✓ | 1.000 | 69.1% | ✓ |
| **SCN-064** | `easy` | `order_volume_drop` | ✓ | ✓ | 1.000 | 24.2% | ✓ |
| **SCN-065** | `easy` | `average_order_value_expansion` | ✗ | ✓ | 0.500 | 22.3% | ✓ |
| **SCN-066** | `easy` | `order_volume_drop` | ✓ | ✓ | 1.000 | 64.1% | ✓ |
| **SCN-067** | `easy` | `order_volume_surge` | ✓ | ✓ | 1.000 | 2.4% | ✓ |
| **SCN-068** | `medium` | `order_volume_surge` | ✓ | ✓ | 1.000 | 122.0% | ✓ |
| **SCN-069** | `medium` | `average_order_value_contraction` | ✗ | ✗ | 0.000 | 50.4% | ✓ |
| **SCN-070** | `medium` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-071** | `medium` | `order_volume_surge` | ✓ | ✓ | 1.000 | 85.1% | ✓ |
| **SCN-072** | `medium` | `logistics_fulfillment_bottleneck` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-073** | `medium` | `order_volume_surge` | ✓ | ✓ | 1.000 | 148.5% | ✓ |
| **SCN-074** | `medium` | `order_volume_drop` | ✗ | ✓ | 0.500 | 40.8% | ✓ |
| **SCN-075** | `medium` | `order_volume_drop` | ✓ | ✓ | 1.000 | 19.8% | ✓ |
| **SCN-076** | `medium` | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 1098.3% | ✓ |
| **SCN-077** | `medium` | `order_volume_drop` | ✓ | ✓ | 1.000 | 10.6% | ✓ |
| **SCN-078** | `medium` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-079** | `medium` | `order_volume_surge` | ✓ | ✓ | 1.000 | 60.5% | ✓ |
| **SCN-080** | `medium` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-081** | `medium` | `average_order_value_expansion` | ✗ | ✓ | 0.500 | 40.7% | ✓ |
| **SCN-082** | `medium` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-083** | `medium` | `order_volume_drop` | ✓ | ✓ | 1.000 | 22.1% | ✓ |
| **SCN-084** | `medium` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-085** | `medium` | `average_order_value_contraction` | ✓ | ✓ | 1.000 | 14.7% | ✓ |
| **SCN-086** | `medium` | `order_volume_surge` | ✓ | ✓ | 1.000 | 31.1% | ✓ |
| **SCN-087** | `medium` | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 285.2% | ✓ |
| **SCN-088** | `medium` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-089** | `medium` | `order_volume_surge` | ✗ | ✗ | 0.000 | 58.6% | ✓ |
| **SCN-090** | `medium` | `logistics_fulfillment_bottleneck` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-091** | `medium` | `order_volume_surge` | ✓ | ✓ | 1.000 | 171.6% | ✓ |
| **SCN-092** | `medium` | `order_volume_drop` | ✓ | ✓ | 1.000 | 60.4% | ✓ |
| **SCN-093** | `medium` | `order_volume_drop` | ✓ | ✓ | 1.000 | 66.0% | ✓ |
| **SCN-094** | `medium` | `average_order_value_contraction` | ✓ | ✓ | 1.000 | 61.4% | ✓ |
| **SCN-095** | `medium` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-096** | `hard` | `order_volume_drop` | ✗ | ✗ | 0.000 | 38.7% | ✓ |
| **SCN-097** | `hard` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-098** | `hard` | `order_volume_drop` | ✓ | ✓ | 1.000 | 1.9% | ✓ |
| **SCN-099** | `hard` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-100** | `hard` | `order_volume_surge` | ✓ | ✓ | 1.000 | 24.6% | ✓ |
| **SCN-101** | `hard` | `average_order_value_contraction` | ✗ | ✓ | 0.500 | 597.2% | ✓ |
| **SCN-102** | `hard` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-103** | `hard` | `logistics_fulfillment_bottleneck` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-104** | `hard` | `order_volume_drop` | ✓ | ✓ | 1.000 | 23.4% | ✓ |
| **SCN-105** | `hard` | `order_volume_drop` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-106** | `hard` | `order_volume_drop` | ✓ | ✓ | 1.000 | 41.8% | ✓ |
| **SCN-107** | `hard` | `order_volume_surge` | ✓ | ✓ | 1.000 | 17.1% | ✓ |
| **SCN-108** | `hard` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-109** | `hard` | `customer_satisfaction_decline` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-110** | `hard` | `order_volume_drop` | ✓ | ✓ | 1.000 | 43.0% | ✓ |
| **SCN-111** | `hard` | `average_order_value_expansion` | ✗ | ✓ | 0.500 | 0.3% | ✓ |
| **SCN-112** | `hard` | `order_volume_surge` | ✗ | ✓ | 0.500 | 35.1% | ✓ |
| **SCN-113** | `hard` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-114** | `hard` | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-115** | `hard` | `order_volume_drop` | ✓ | ✓ | 1.000 | 19.2% | ✓ |

## Investigation Efficiency

| Scenario | Steps | Tools | Branches | Pruned | Execution Time |
|---|---:|---:|---:|---:|---:|
| **SCN-001** | 4 | 3 | 1 | 1 | 6310.5 ms |
| **SCN-002** | 5 | 5 | 2 | 0 | 3389.3 ms |
| **SCN-003** | 4 | 3 | 1 | 1 | 955.6 ms |
| **SCN-004** | 3 | 3 | 1 | 0 | 417.1 ms |
| **SCN-005** | 3 | 3 | 0 | 0 | 354.2 ms |
| **SCN-006** | 5 | 5 | 2 | 0 | 532.8 ms |
| **SCN-007** | 4 | 4 | 1 | 0 | 521.0 ms |
| **SCN-008** | 4 | 3 | 1 | 1 | 830.3 ms |
| **SCN-009** | 4 | 3 | 1 | 1 | 1047.1 ms |
| **SCN-010** | 4 | 3 | 1 | 1 | 614.5 ms |
| **SCN-011** | 3 | 3 | 0 | 0 | 556.5 ms |
| **SCN-012** | 4 | 4 | 1 | 0 | 592.9 ms |
| **SCN-013** | 4 | 3 | 1 | 1 | 599.4 ms |
| **SCN-014** | 4 | 4 | 1 | 0 | 583.5 ms |
| **SCN-015** | 4 | 4 | 1 | 0 | 2665.2 ms |
| **SCN-016** | 4 | 3 | 1 | 1 | 450.4 ms |
| **SCN-017** | 4 | 3 | 1 | 1 | 705.8 ms |
| **SCN-018** | 4 | 2 | 1 | 2 | 496.8 ms |
| **SCN-019** | 4 | 3 | 1 | 1 | 453.9 ms |
| **SCN-020** | 4 | 3 | 1 | 1 | 532.4 ms |
| **SCN-021** | 4 | 2 | 1 | 2 | 459.2 ms |
| **SCN-022** | 4 | 3 | 1 | 1 | 486.4 ms |
| **SCN-023** | 4 | 4 | 1 | 0 | 1602.8 ms |
| **SCN-024** | 3 | 3 | 1 | 0 | 433.7 ms |
| **SCN-025** | 3 | 2 | 1 | 1 | 629.4 ms |
| **SCN-026** | 3 | 3 | 1 | 0 | 389.5 ms |
| **SCN-027** | 3 | 3 | 1 | 0 | 426.4 ms |
| **SCN-028** | 3 | 2 | 1 | 1 | 452.3 ms |
| **SCN-029** | 3 | 2 | 1 | 1 | 432.3 ms |
| **SCN-030** | 3 | 3 | 1 | 0 | 460.6 ms |
| **SCN-031** | 3 | 2 | 1 | 1 | 2786.7 ms |
| **SCN-032** | 3 | 2 | 1 | 1 | 699.5 ms |
| **SCN-033** | 3 | 2 | 1 | 1 | 452.0 ms |
| **SCN-034** | 3 | 2 | 1 | 1 | 717.7 ms |
| **SCN-035** | 3 | 3 | 1 | 0 | 768.9 ms |
| **SCN-036** | 3 | 3 | 1 | 0 | 558.5 ms |
| **SCN-037** | 3 | 3 | 1 | 0 | 448.0 ms |
| **SCN-038** | 3 | 3 | 1 | 0 | 434.7 ms |
| **SCN-039** | 3 | 2 | 1 | 1 | 435.1 ms |
| **SCN-040** | 3 | 3 | 1 | 0 | 1798.5 ms |
| **SCN-041** | 3 | 3 | 1 | 0 | 1020.5 ms |
| **SCN-042** | 3 | 2 | 1 | 1 | 439.1 ms |
| **SCN-043** | 3 | 2 | 1 | 1 | 460.2 ms |
| **SCN-044** | 3 | 2 | 1 | 1 | 415.9 ms |
| **SCN-045** | 3 | 1 | 1 | 2 | 1085.4 ms |
| **SCN-046** | 3 | 2 | 1 | 1 | 679.1 ms |
| **SCN-047** | 3 | 3 | 1 | 0 | 551.9 ms |
| **SCN-048** | 2 | 1 | 0 | 1 | 417.4 ms |
| **SCN-049** | 2 | 2 | 0 | 0 | 432.5 ms |
| **SCN-050** | 3 | 1 | 1 | 2 | 830.0 ms |
| **SCN-051** | 2 | 1 | 0 | 1 | 505.6 ms |
| **SCN-052** | 3 | 2 | 1 | 1 | 600.2 ms |
| **SCN-053** | 4 | 4 | 1 | 0 | 495.4 ms |
| **SCN-054** | 4 | 2 | 1 | 2 | 1331.9 ms |
| **SCN-055** | 3 | 2 | 1 | 1 | 894.3 ms |
| **SCN-056** | 3 | 3 | 1 | 0 | 543.7 ms |
| **SCN-057** | 3 | 3 | 1 | 0 | 378.9 ms |
| **SCN-058** | 3 | 2 | 1 | 1 | 453.6 ms |
| **SCN-059** | 3 | 3 | 1 | 0 | 790.7 ms |
| **SCN-060** | 3 | 3 | 1 | 0 | 1607.8 ms |
| **SCN-061** | 3 | 2 | 1 | 1 | 1059.8 ms |
| **SCN-062** | 2 | 2 | 0 | 0 | 661.4 ms |
| **SCN-063** | 4 | 2 | 1 | 2 | 474.2 ms |
| **SCN-064** | 3 | 3 | 1 | 0 | 397.4 ms |
| **SCN-065** | 4 | 4 | 1 | 0 | 432.1 ms |
| **SCN-066** | 4 | 4 | 1 | 0 | 439.2 ms |
| **SCN-067** | 4 | 4 | 1 | 0 | 446.0 ms |
| **SCN-068** | 4 | 4 | 1 | 0 | 435.9 ms |
| **SCN-069** | 4 | 3 | 1 | 1 | 675.2 ms |
| **SCN-070** | 2 | 2 | 0 | 0 | 1490.5 ms |
| **SCN-071** | 4 | 3 | 1 | 1 | 447.9 ms |
| **SCN-072** | 3 | 3 | 1 | 0 | 441.7 ms |
| **SCN-073** | 4 | 4 | 1 | 0 | 458.5 ms |
| **SCN-074** | 4 | 3 | 1 | 1 | 998.6 ms |
| **SCN-075** | 3 | 1 | 1 | 2 | 586.8 ms |
| **SCN-076** | 3 | 3 | 1 | 0 | 456.9 ms |
| **SCN-077** | 4 | 3 | 1 | 1 | 497.6 ms |
| **SCN-078** | 3 | 2 | 1 | 1 | 559.5 ms |
| **SCN-079** | 3 | 2 | 1 | 1 | 1669.0 ms |
| **SCN-080** | 2 | 0 | 0 | 2 | 449.9 ms |
| **SCN-081** | 4 | 3 | 1 | 1 | 408.3 ms |
| **SCN-082** | 2 | 2 | 0 | 0 | 434.7 ms |
| **SCN-083** | 4 | 4 | 1 | 0 | 407.1 ms |
| **SCN-084** | 3 | 3 | 1 | 0 | 545.9 ms |
| **SCN-085** | 3 | 2 | 1 | 1 | 484.0 ms |
| **SCN-086** | 3 | 2 | 1 | 1 | 402.0 ms |
| **SCN-087** | 3 | 2 | 1 | 1 | 525.2 ms |
| **SCN-088** | 3 | 3 | 1 | 0 | 395.5 ms |
| **SCN-089** | 4 | 3 | 1 | 1 | 442.1 ms |
| **SCN-090** | 3 | 3 | 1 | 0 | 1417.8 ms |
| **SCN-091** | 3 | 2 | 1 | 1 | 396.3 ms |
| **SCN-092** | 4 | 3 | 1 | 1 | 395.5 ms |
| **SCN-093** | 3 | 3 | 1 | 0 | 757.1 ms |
| **SCN-094** | 3 | 1 | 1 | 2 | 474.4 ms |
| **SCN-095** | 2 | 0 | 0 | 2 | 449.6 ms |
| **SCN-096** | 4 | 4 | 1 | 0 | 480.6 ms |
| **SCN-097** | 3 | 2 | 1 | 1 | 489.8 ms |
| **SCN-098** | 3 | 2 | 1 | 1 | 537.6 ms |
| **SCN-099** | 3 | 1 | 1 | 2 | 696.7 ms |
| **SCN-100** | 4 | 4 | 1 | 0 | 583.0 ms |
| **SCN-101** | 4 | 3 | 1 | 1 | 497.6 ms |
| **SCN-102** | 3 | 3 | 1 | 0 | 534.2 ms |
| **SCN-103** | 3 | 3 | 1 | 0 | 584.6 ms |
| **SCN-104** | 4 | 3 | 1 | 1 | 575.0 ms |
| **SCN-105** | 2 | 2 | 0 | 0 | 372.2 ms |
| **SCN-106** | 5 | 4 | 2 | 1 | 519.5 ms |
| **SCN-107** | 4 | 2 | 1 | 2 | 513.2 ms |
| **SCN-108** | 4 | 3 | 2 | 1 | 801.0 ms |
| **SCN-109** | 5 | 4 | 3 | 1 | 549.2 ms |
| **SCN-110** | 3 | 2 | 1 | 1 | 461.7 ms |
| **SCN-111** | 4 | 3 | 1 | 1 | 414.9 ms |
| **SCN-112** | 4 | 2 | 1 | 2 | 500.0 ms |
| **SCN-113** | 3 | 2 | 1 | 1 | 456.1 ms |
| **SCN-114** | 3 | 1 | 1 | 2 | 382.5 ms |
| **SCN-115** | 4 | 3 | 1 | 1 | 408.7 ms |

## Failure & Ambiguity Analysis

### Scenario SCN-007: New Year E-Commerce Volume Expansion

- **Difficulty**: `easy`
- **Expected Cause**: `order_volume_surge`
- **Predicted Causes**: Average Order Value Expansion (average_order_value=R$ 239.15 (vs R$ 79.38)), Customer State: RJ (customer_state=RJ), Customer State: SP (customer_state=SP), Customer State: SC (customer_state=SC), Customer State: SE (customer_state=SE)
- **MRR Score**: 0.0000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'order_volume' (order_volume_surge) was not ranked #1. Actual top cause: 'Average Order Value Expansion (average_order_value=R$ 239.15 (vs R$ 79.38))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-008: High-End Watch Promotional Campaign

- **Difficulty**: `easy`
- **Expected Cause**: `average_order_value_expansion`
- **Predicted Causes**: Order Volume Surge (order_volume=108 orders (vs 86)), Average Order Value Contraction (average_order_value=R$ 138.88 (vs R$ 144.37)), Product Category: relogios_presentes (product_category=relogios_presentes), Product Category: esporte_lazer (product_category=esporte_lazer), Product Category: ferramentas_jardim (product_category=ferramentas_jardim)
- **MRR Score**: 0.5000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'average_order_value' (average_order_value_expansion) was not ranked #1. Actual top cause: 'Order Volume Surge (order_volume=108 orders (vs 86))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-011: Mid-Month Category Mix Shift

- **Difficulty**: `hard`
- **Expected Cause**: `order_volume_drop`
- **Predicted Causes**: Average Order Value Contraction (average_order_value=R$ 135.60 (vs R$ 141.88)), Order Volume Surge (order_volume=163 orders (vs 159))
- **MRR Score**: 0.5000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'order_volume' (order_volume_drop) was not ranked #1. Actual top cause: 'Average Order Value Contraction (average_order_value=R$ 135.60 (vs R$ 141.88))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-012: Post-Black Friday Demand Hangover

- **Difficulty**: `easy`
- **Expected Cause**: `order_volume_drop`
- **Predicted Causes**: Average Order Value Expansion (average_order_value=R$ 140.00 (vs R$ 130.61)), Order Volume Surge (order_volume=280 orders (vs 276)), Customer State: RS (customer_state=RS), Customer State: PE (customer_state=PE), Customer State: CE (customer_state=CE)
- **MRR Score**: 0.5000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'order_volume' (order_volume_drop) was not ranked #1. Actual top cause: 'Average Order Value Expansion (average_order_value=R$ 140.00 (vs R$ 130.61))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-020: Heavy Freight Furniture Basket Expansion

- **Difficulty**: `medium`
- **Expected Cause**: `average_order_value_expansion`
- **Predicted Causes**: Order Volume Surge (order_volume=246 orders (vs 215)), Average Order Value Expansion (average_order_value=R$ 164.10 (vs R$ 149.46)), Product Category: portateis_casa_forno_e_cafe (product_category=portateis_casa_forno_e_cafe), Product Category: telefonia (product_category=telefonia), Product Category: instrumentos_musicais (product_category=instrumentos_musicais)
- **MRR Score**: 0.5000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'average_order_value' (average_order_value_expansion) was not ranked #1. Actual top cause: 'Order Volume Surge (order_volume=246 orders (vs 215))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-054: September Post-Holiday Volume Contraction

- **Difficulty**: `easy`
- **Expected Cause**: `order_volume_drop`
- **Predicted Causes**: Average Order Value Contraction (average_order_value=R$ 116.38 (vs R$ 147.93)), Order Volume Contraction (order_volume=109 orders (vs 133)), Customer State: RJ (customer_state=RJ), Customer State: SP (customer_state=SP), Customer State: PR (customer_state=PR)
- **MRR Score**: 0.5000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'order_volume' (order_volume_drop) was not ranked #1. Actual top cause: 'Average Order Value Contraction (average_order_value=R$ 116.38 (vs R$ 147.93))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-065: Electronics Super-Sale AOV Spike

- **Difficulty**: `easy`
- **Expected Cause**: `average_order_value_expansion`
- **Predicted Causes**: Order Volume Contraction (order_volume=76 orders (vs 92)), Average Order Value Contraction (average_order_value=R$ 123.99 (vs R$ 143.50)), Product Category: beleza_saude (product_category=beleza_saude), Product Category: cama_mesa_banho (product_category=cama_mesa_banho), Product Category: relogios_presentes (product_category=relogios_presentes)
- **MRR Score**: 0.5000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'average_order_value' (average_order_value_expansion) was not ranked #1. Actual top cause: 'Order Volume Contraction (order_volume=76 orders (vs 92))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-069: Q3 Revenue Softening Mixed AOV and Volume Signal

- **Difficulty**: `medium`
- **Expected Cause**: `average_order_value_contraction`
- **Predicted Causes**: Order Volume Contraction (order_volume=104 orders (vs 148)), Product Category: cool_stuff (product_category=cool_stuff), Product Category: ferramentas_jardim (product_category=ferramentas_jardim), Product Category: informatica_acessorios (product_category=informatica_acessorios), Product Category: esporte_lazer (product_category=esporte_lazer)
- **MRR Score**: 0.0000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'average_order_value' (average_order_value_contraction) was not ranked #1. Actual top cause: 'Order Volume Contraction (order_volume=104 orders (vs 148))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-074: Post-Black Friday Demand Hangover with Category Rotation

- **Difficulty**: `medium`
- **Expected Cause**: `order_volume_drop`
- **Predicted Causes**: Average Order Value Contraction (average_order_value=R$ 119.26 (vs R$ 131.32)), Order Volume Contraction (order_volume=282 orders (vs 290)), Customer State: SP (customer_state=SP), Customer State: PR (customer_state=PR), Customer State: ES (customer_state=ES)
- **MRR Score**: 0.5000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'order_volume' (order_volume_drop) was not ranked #1. Actual top cause: 'Average Order Value Contraction (average_order_value=R$ 119.26 (vs R$ 131.32))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-081: Furniture and Decor Basket Mix Uplift

- **Difficulty**: `medium`
- **Expected Cause**: `average_order_value_expansion`
- **Predicted Causes**: Order Volume Contraction (order_volume=124 orders (vs 163)), Average Order Value Expansion (average_order_value=R$ 150.21 (vs R$ 145.14)), Product Category: informatica_acessorios (product_category=informatica_acessorios), Product Category: cama_mesa_banho (product_category=cama_mesa_banho), Product Category: beleza_saude (product_category=beleza_saude)
- **MRR Score**: 0.5000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'average_order_value' (average_order_value_expansion) was not ranked #1. Actual top cause: 'Order Volume Contraction (order_volume=124 orders (vs 163))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-089: Tech Accessories Volume Surge with Basket Compression

- **Difficulty**: `medium`
- **Expected Cause**: `order_volume_surge`
- **Predicted Causes**: Average Order Value Expansion (average_order_value=R$ 184.44 (vs R$ 140.57)), Product Category: pcs (product_category=pcs), Product Category: informatica_acessorios (product_category=informatica_acessorios), Product Category: ferramentas_jardim (product_category=ferramentas_jardim), Product Category: relogios_presentes (product_category=relogios_presentes)
- **MRR Score**: 0.0000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'order_volume' (order_volume_surge) was not ranked #1. Actual top cause: 'Average Order Value Expansion (average_order_value=R$ 184.44 (vs R$ 140.57))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-096: Near-Equal Volume vs AOV Split GMV Decline

- **Difficulty**: `hard`
- **Expected Cause**: `order_volume_drop`
- **Predicted Causes**: Average Order Value Expansion (average_order_value=R$ 182.27 (vs R$ 154.89)), Customer State: PR (customer_state=PR), Customer State: PE (customer_state=PE), Customer State: RS (customer_state=RS), Customer State: MA (customer_state=MA)
- **MRR Score**: 0.0000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'order_volume' (order_volume_drop) was not ranked #1. Actual top cause: 'Average Order Value Expansion (average_order_value=R$ 182.27 (vs R$ 154.89))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-101: Category Shift or Order Volume Drop Ambiguous GMV Decline

- **Difficulty**: `hard`
- **Expected Cause**: `average_order_value_contraction`
- **Predicted Causes**: Order Volume Surge (order_volume=153 orders (vs 137)), Average Order Value Contraction (average_order_value=R$ 114.26 (vs R$ 126.06)), Product Category: brinquedos (product_category=brinquedos), Product Category: informatica_acessorios (product_category=informatica_acessorios), Product Category: esporte_lazer (product_category=esporte_lazer)
- **MRR Score**: 0.5000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'average_order_value' (average_order_value_contraction) was not ranked #1. Actual top cause: 'Order Volume Surge (order_volume=153 orders (vs 137))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-111: Competing Category Mix Shifts in AOV Hard Attribution

- **Difficulty**: `hard`
- **Expected Cause**: `average_order_value_expansion`
- **Predicted Causes**: Order Volume Contraction (order_volume=136 orders (vs 142)), Average Order Value Expansion (average_order_value=R$ 132.26 (vs R$ 130.26)), Product Category: esporte_lazer (product_category=esporte_lazer), Product Category: cama_mesa_banho (product_category=cama_mesa_banho), Product Category: moveis_escritorio (product_category=moveis_escritorio)
- **MRR Score**: 0.5000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'average_order_value' (average_order_value_expansion) was not ranked #1. Actual top cause: 'Order Volume Contraction (order_volume=136 orders (vs 142))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.

### Scenario SCN-112: Volume-Led Revenue Recovery Ambiguous Segment Attribution

- **Difficulty**: `hard`
- **Expected Cause**: `order_volume_surge`
- **Predicted Causes**: Average Order Value Expansion (average_order_value=R$ 197.62 (vs R$ 154.49)), Order Volume Surge (order_volume=152 orders (vs 139)), Customer State: ES (customer_state=ES), Customer State: MG (customer_state=MG), Customer State: PI (customer_state=PI)
- **MRR Score**: 0.5000
- **Evidence Grounded**: Yes
- **Diagnosis**: Expected primary causal mechanism 'order_volume' (order_volume_surge) was not ranked #1. Actual top cause: 'Average Order Value Expansion (average_order_value=R$ 197.62 (vs R$ 154.49))'.
- **Stopping Reason**: Investigation completed: All scheduled branches evaluated.
