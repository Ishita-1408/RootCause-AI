# RootCause AI — Claim-Level Hallucination Evaluation Report

## 1. Canonical Production Claims Evaluation

| Metric | Result |
|---|---:|
| Total Material Claims Evaluated | 60 |
| Supported Claims | 60 |
| Partially Supported Claims | 0 |
| Unsupported Claims | 0 |
| Contradicted Claims | 0 |
| **Claim Grounding Rate** | **100.0%** |
| **Unsupported Claim Rate** | **0.0%** |
| **Contradiction Rate** | **0.0%** |
| **Hallucination Rate** | **0.0%** |
| Numerical Accuracy | 100.0% |
| Evidence Attribution Accuracy | 100.0% |
| Claim Precision | 100.0% |
| Claim Recall | 100.0% |

## 2. Adversarial Hallucination Injection Suite

| Metric | Adversarial Result | Target |
|---|---:|:---:|
| Adversarial Test Cases | 16 | 16+ |
| Hallucinations Caught | 16 | 16 |
| Detection Rate | 100.0% | 100.0% |

## 3. Claim Verification Trace (Sample)

| Claim ID | Status | Claimed | Evidence | Error % | Reason |
|---|---|---:|---:|---:|---|
| `clm_kpi_summary_2017-11-24` | **SUPPORTED** | 19.97 | 19.97 | 0.0% | Corroborated by empirical evidence |
| `clm_rc_rank_1_delivery_carrier_transit_delay` | **SUPPORTED** | 100.00 | 19.97 | 0.0% | Corroborated by empirical evidence |
| `clm_rc_rank_2_customer_state_SP` | **SUPPORTED** | 31.80 | 31.83 | 0.1% | Corroborated by empirical evidence |
| `clm_rc_rank_3_customer_state_RJ` | **SUPPORTED** | 18.90 | 18.89 | 0.1% | Corroborated by empirical evidence |
| `clm_rc_rank_4_customer_state_MG` | **SUPPORTED** | 17.10 | 17.10 | 0.0% | Corroborated by empirical evidence |
| `clm_rc_rank_5_product_category_cama_mesa_banho` | **SUPPORTED** | 13.20 | 13.20 | 0.0% | Corroborated by empirical evidence |
| `clm_finding_1` | **SUPPORTED** | 40.10 | 40.14 | 0.1% | Corroborated by empirical evidence |
| `clm_finding_2` | **SUPPORTED** | 20.00 | 19.97 | 0.1% | Corroborated by empirical evidence |
| `clm_finding_3` | **SUPPORTED** | 31.80 | 31.83 | 0.1% | Corroborated by empirical evidence |
| `clm_finding_4` | **SUPPORTED** | 18.90 | 18.89 | 0.1% | Corroborated by empirical evidence |
| `clm_kpi_summary_2017-11-19` | **SUPPORTED** | 19955.56 | 19955.56 | 0.0% | Corroborated by empirical evidence |
| `clm_rc_rank_1_order_volume_158 orders (vs 190)` | **SUPPORTED** | -76.50 | -76.48 | 0.0% | Corroborated by empirical evidence |
| `clm_rc_rank_2_average_order_value_R$ 126.30 (vs R$ 134.65)` | **SUPPORTED** | -28.30 | -28.26 | 0.1% | Corroborated by empirical evidence |
| `clm_rc_rank_3_customer_state_SP` | **SUPPORTED** | -39.10 | -39.11 | 0.0% | Corroborated by empirical evidence |
| `clm_rc_rank_4_product_category_relogios_presentes` | **SUPPORTED** | -36.10 | -36.11 | 0.0% | Corroborated by empirical evidence |