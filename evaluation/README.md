# RootCause AI — Evaluation & Benchmark Framework (Phase B)

The RootCause AI Evaluation & Benchmark Framework provides an automated, reproducible measurement suite for assessing business root-cause attribution accuracy, mathematical grounding, and autonomous investigation efficiency.

---

## 1. Directory Structure

```text
evaluation/
├── scenarios/
│   ├── models.py          # GroundTruthScenario & GroundTruthRootCause schema
│   ├── registry.py        # Controlled incident scenario definitions (SCN-001 to SCN-006)
│   └── __init__.py
├── metrics/
│   ├── models.py          # EvaluationResult & BenchmarkSummary schema
│   ├── evaluator.py       # Deterministic Top-K, MRR, grounding & error evaluator
│   └── __init__.py
├── runners/
│   ├── run_benchmark.py   # Benchmark runner CLI & Markdown generator
│   └── __init__.py
├── reports/
│   ├── latest_benchmark.md    # Formatted executive benchmark report
│   └── latest_benchmark.json  # Machine-readable evaluation results
└── README.md
```

---

## 2. Benchmark Incident Scenarios

| Scenario ID | Name | Target Metric | Primary Ground-Truth Cause | Expected Direction |
| :--- | :--- | :--- | :--- | :--- |
| **`SCN-001`** | Warehouse Capacity Contraction | `late_delivery_rate_pct` | Logistics / Fulfillment Bottleneck (`delivery`) | `increase` |
| **`SCN-002`** | Marketing Spend Contraction | `total_gmv` | Order Volume Drop (`order_volume`) | `decrease` |
| **`SCN-003`** | Product Pricing & Basket Shift | `total_gmv` | Basket Value Expansion (`average_order_value`) | `increase` |
| **`SCN-004`** | Delivery Partner Degradation | `late_delivery_rate_pct` | Carrier Transit SLA Degradation (`delivery`) | `increase` |
| **`SCN-005`** | Payment Friction & Basket Shift | `total_gmv` | Average Order Value Contraction (`average_order_value`) | `decrease` |
| **`SCN-006`** | Customer Acquisition Surge | `total_gmv` | Order Volume Surge (`order_volume`) | `increase` |

---

## 3. Evaluation Metrics

1. **Top-1 Accuracy**: Percentage of scenarios where the ground-truth primary root cause is ranked at position 1.
2. **Top-3 Accuracy**: Percentage of scenarios where the ground-truth primary cause is ranked in the top 3.
3. **Mean Reciprocal Rank (MRR)**: Average reciprocal rank:
   $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
4. **False Positive Rate (FPR)**: Proportion of top-ranked causes that match neither the primary nor valid secondary causes.
5. **Mean Contribution Error**: Absolute difference between quantitative ground-truth driver contribution and agent calculation.
6. **Evidence Grounding Rate**: Percentage of scenarios where all claimed causes are supported by deterministic query evidence.
7. **Unsupported Claim Rate**: Proportion of narrative statements without numerical backing.
8. **Hallucination Rate**: Rate of invented or contradictory claims (strictly targeted at 0.0).

---

## 4. Running the Benchmark

### Run the full benchmark suite
```bash
uv run python -m evaluation.runners.run_benchmark
```

### Run a single scenario
```bash
uv run python -m evaluation.runners.run_benchmark --scenario SCN-006
```

### Verbose mode with custom output paths
```bash
uv run python -m evaluation.runners.run_benchmark --verbose --output-md evaluation/reports/custom.md --output-json evaluation/reports/custom.json
```

---

## 5. Automated Tests

```bash
uv run pytest tests/evaluation/ -v
```
