# RootCause AI — Statistical Change-Point Detection Evaluation

## 1. Executive Summary

This evaluation benchmarks RootCause AI's statistical change-point detector across 7 diverse regime dynamics scenarios (isolated spikes, sustained mean shifts, variance expansion, gradual trends, constant series, missing dates, and insufficient data samples).

- **Overall Classification Accuracy**: **100.0%**
- **Change-Point Precision / Recall**: **100.0% / 100.0%**
- **False Positive Rate**: **0.0%**
- **Mean Detection Delay**: **0.7 days**
- **Mean Shift Estimation MAE**: **0.16%**
- **Variance Regime Accuracy**: **100.0%**
- **Insufficient Data Handling**: **100.0%**

## 2. Benchmark Metrics Summary

| Metric | Score | Target | Status |
|---|---:|:---:|:---:|
| **Scenarios Evaluated** | 10 | >= 5 | PASS |
| **Classification Accuracy** | 100.0% | 100.0% | PASS |
| **Precision (PPV)** | 100.0% | 100.0% | PASS |
| **Recall (Sensitivity)** | 100.0% | 100.0% | PASS |
| **False Positive Rate** | 0.0% | 0.0% | PASS |
| **Mean Detection Delay** | 0.7 days | <= 1 day | PASS |
| **Mean Shift Estimation MAE** | 0.16% | <= 5.0% | PASS |
| **Variance Shift Accuracy** | 100.0% | 100.0% | PASS |
| **Insufficient Data Handling** | 100.0% | 100.0% | PASS |

## 3. Scenario-Level Results

| Scenario ID | Name | Expected Regime | Predicted Regime | Detected | Date Delay | Shift Error | Match |
|---|---|---|---|:---:|:---:|:---:|:---:|
| **CP-SCN-01** | Clear Upward Regime Shift | `sustained_level_shift` | `sustained_level_shift` | Yes | 0d | 0.4% | **PASS** |
| **CP-SCN-02** | Clear Downward Regime Shift | `sustained_level_shift` | `sustained_level_shift` | Yes | 0d | 0.1% | **PASS** |
| **CP-SCN-03** | Temporary Spike with Baseline Reversion | `isolated_anomaly` | `isolated_anomaly` | No | 0d | N/A | **PASS** |
| **CP-SCN-04** | Gradual Linear Trend without Break | `gradual_trend` | `gradual_trend` | No | 0d | N/A | **PASS** |
| **CP-SCN-05** | Variance Regime Change (Volatility Expansion) | `variance_regime_shift` | `variance_regime_shift` | Yes | 7d | N/A | **PASS** |
| **CP-SCN-06** | Very Noisy Series without Structural Break | `normal` | `normal` | No | 0d | N/A | **PASS** |
| **CP-SCN-07** | Insufficient History | `insufficient_data` | `insufficient_data` | No | 0d | N/A | **PASS** |
| **CP-SCN-08** | Constant Series with Zero Variance | `normal` | `normal` | No | 0d | N/A | **PASS** |
| **CP-SCN-09** | Outlier Without Regime Change | `isolated_anomaly` | `isolated_anomaly` | No | 0d | N/A | **PASS** |
| **CP-SCN-10** | Change Point Preceding Anomaly with Missing Dates | `sustained_level_shift` | `sustained_level_shift` | Yes | 0d | 0.0% | **PASS** |

## 4. Methodological Distinction

> [!IMPORTANT]
> **Temporal Statistical Evidence vs. Causal Explanation**:
> Change-point detection answers whether the mathematical regime of a > time series changed. It does NOT invent or substitute for a causal > root-cause explanation. RootCause AI uses change points as temporal > evidence while relying on deterministic SQL marts for causal ranking.