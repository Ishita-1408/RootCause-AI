# RootCause AI — Evaluation & Benchmark Framework (Phase B)

The RootCause AI Evaluation & Benchmark Framework provides an automated, reproducible measurement suite for assessing business root-cause attribution accuracy, mathematical grounding, and autonomous investigation efficiency.

---

## 1. Directory Structure

```text
evaluation/
├── scenarios/
│   ├── models.py          # GroundTruthScenario & GroundTruthRootCause schema
│   ├── registry.py        # Authoritative incident scenario definitions (115 scenarios: SCN-001 to SCN-115)
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

The evaluation suite contains **115 authoritative scenarios** stratified across three difficulty tiers:
- **Easy (45 scenarios):** Clear, dominant single driver (e.g. concentrated volume surge or single carrier SLA degradation).
- **Medium (48 scenarios):** Multi-factor drivers with interacting volume, pricing, or regional shifts.
- **Hard (22 scenarios):** Competing drivers, countervailing noise, distractor slices, and ambiguous signals.

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
