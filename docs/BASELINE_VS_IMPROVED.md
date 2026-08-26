# Baseline vs. Improved Agent Experiment

**Experiment Objective:** Quantitatively demonstrate the performance gains achieved by moving from an unconstrained baseline AI investigation agent to RootCause AI's deterministic causal decomposition, statistical significance testing, and online Claim Verification Firewall.

---

## 1. Experimental Methodology & Invariants

Both agents are evaluated under identical conditions:
- **Same Canonical Scenarios:** 6 real-world business failure scenarios from the Olist Brazilian E-Commerce dataset (`SCN-001` through `SCN-006`).
- **Same Scenario Inputs:** Identical target anomaly dates, baseline comparison windows, and target business metrics.
- **Same Underlying Data Marts:** `fact_order_analytics`, `dim_customer_cohorts`, and `fact_daily_kpis`.
- **Same Automated Evaluator:** `StructuredCausalEvaluator` and `ClaimHallucinationEvaluator`.

```
┌─────────────────────────────────────────────────────────────┐
│                 6 Canonical Business Scenarios              │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│       BASELINE AGENT        │ │ IMPROVED ROOTCAUSE AI AGENT │
│ • Unconstrained LLM claims  │ │ • Deterministic decomposition│
│ • No multiplicative decomp  │ │ • Welch t-test & Wilson CI  │
│ • Saliency heuristic ranking│ │ • Causal hypothesis ranking │
│ • No Claim Firewall         │ │ • Online Claim Firewall     │
└──────────────┬──────────────┘ └──────────────┬──────────────┘
               │                               │
               └───────────────┬───────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  STRICT AUTOMATED EVALUATORS                │
│  Top-1 Accuracy · Top-3 · MRR · Evidence Grounding · Claims │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Quantitative Comparison Results

| Evaluation Metric | Baseline Agent | Improved RootCause AI Agent | Absolute Improvement | Target Benchmark |
| :--- | :---: | :---: | :---: | :---: |
| **Top-1 Root Cause Accuracy** | 50.0% (3/6) | **100.0% (6/6)** | **+50.0%** | 100.0% |
| **Top-3 Accuracy** | 83.3% (5/6) | **100.0% (6/6)** | **+16.7%** | 100.0% |
| **Mean Reciprocal Rank (MRR)** | 0.6389 | **1.0000** | **+0.3611** | 1.0000 |
| **Evidence Grounding Rate** | 100.0% | **100.0%** | 0.0% (Maintained) | 100.0% |
| **Claim Grounding Rate** | 66.7% | **100.0% (60/60)** | **+33.3%** | 100.0% |
| **Unsupported Claims Rate** | 3.3% | **0.0%** | **-3.3%** | 0.0% |
| **Contradiction Rate** | 30.0% | **0.0%** | **-30.0%** | 0.0% |
| **Claim Hallucination Rate** | 33.3% | **0.0%** | **-33.3%** | 0.0% (Zero Target) |
| **Numerical Accuracy** | 60.4% | **100.0%** | **+39.6%** | 100.0% |
| **Adversarial Detection Rate**| N/A | **100.0%** | **100.0%** | 100.0% |
| **Average Investigation Latency**| 850 ms | **649 ms** | **-201 ms** | $< 1000$ ms |

---

## 3. Detailed Failure Mode Analysis of Baseline Agent

### 1. Conflating Geographic Concentration with Mechanism
- **Baseline Error:** In `SCN-001` (Warehouse fulfillment delay), the baseline agent attributed the revenue drop to the **State of São Paulo** because SP accounted for the highest absolute volume drop.
- **Improved RootCause AI Correction:** Correctly separated the *demographic segment* (SP) from the *causal mechanism* (**Carrier Transit SLA Breach**, which jumped by +4.2 days across carrier routes).

### 2. Numerical Inconsistency in Narrative Claims
- **Baseline Error:** The baseline natural language memo asserted: *"Average order value dropped by 18.4%"*, when the actual transactional mart showed AOV was unchanged (-0.2%) and Order Volume was down 28.2%.
- **Improved RootCause AI Correction:** The **Claim Verification Firewall** parsed the drafted statement, detected that AOV shift was contradicted by the evidence pool, and forced the synthesis to report exact mathematical figures.

---

## 4. How to Reproduce this Experiment

Run the automated baseline comparison test suite:
```bash
uv run pytest tests/evaluation/test_agent_comparison.py -v
```

Or run the full benchmark runners:
```bash
# Canonical Causal Benchmark
uv run python -m evaluation.runners.run_benchmark --verbose

# Claim-Level Hallucination Evaluator
uv run python -m evaluation.runners.run_hallucination_benchmark --verbose
```
