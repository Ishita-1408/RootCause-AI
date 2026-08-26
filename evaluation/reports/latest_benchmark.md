# RootCause AI Benchmark Report (Structured Causal Evaluator v2)

## Overall Results

| Metric | Score |
|---|---:|
| Scenarios Evaluated | 6 |
| Top-1 Accuracy | 100.0% |
| Top-3 Accuracy | 100.0% |
| Mean Reciprocal Rank (MRR) | 1.0000 |
| False Positive Rate | 0.333 |
| Mean Contribution Error | 29.3% |
| Evidence Grounding Rate | 100.0% |
| Unsupported Claim Rate | 0.000 |
| Hallucination Rate | 0.000 |
| Avg Investigation Steps | 4.0 |
| Avg Analytical Tool Calls | 3.7 |
| Avg Execution Time | 443.9 ms |

## Scenario Results

| Scenario | Ground Truth | Top-1 | Top-3 | MRR | Error | Grounded |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **SCN-001** | `logistics_fulfillment_bottleneck` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-002** | `order_volume_drop` | ✓ | ✓ | 1.000 | 1.5% | ✓ |
| **SCN-003** | `average_order_value_expansion` | ✓ | ✓ | 1.000 | 9.0% | ✓ |
| **SCN-004** | `carrier_sla_degradation` | ✓ | ✓ | 1.000 | N/A | ✓ |
| **SCN-005** | `average_order_value_contraction` | ✓ | ✓ | 1.000 | 69.5% | ✓ |
| **SCN-006** | `order_volume_surge` | ✓ | ✓ | 1.000 | 37.1% | ✓ |

## Investigation Efficiency

| Scenario | Steps | Tools | Branches | Pruned | Execution Time |
|---|---:|---:|---:|---:|---:|
| **SCN-001** | 4 | 3 | 1 | 1 | 481.9 ms |
| **SCN-002** | 5 | 5 | 2 | 0 | 455.9 ms |
| **SCN-003** | 4 | 3 | 1 | 1 | 609.6 ms |
| **SCN-004** | 3 | 3 | 1 | 0 | 363.9 ms |
| **SCN-005** | 3 | 3 | 0 | 0 | 304.6 ms |
| **SCN-006** | 5 | 5 | 2 | 0 | 447.2 ms |

## Failure Analysis

All evaluated benchmark scenarios met Top-1 accuracy and evidence grounding criteria with zero hallucinations.