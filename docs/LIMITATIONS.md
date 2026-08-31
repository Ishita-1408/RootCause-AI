# RootCause AI — Engineering Limitations & Design Assumptions

A rigorous Data Science and ML Engineering project requires transparency regarding assumptions, scope boundaries, and design trade-offs. This document outlines the engineering realities and intentional constraints of RootCause AI.

---

## 1. Causal Scope: Observational Ranking vs. Counterfactual Inference

- **Observational Causal Hypothesis Ranking:** RootCause AI performs mathematical variance decomposition, statistical association testing, and operational corroboration over observational transactional data.
- **Limitation:** The system does **not** claim randomized experimental proof (e.g., A/B testing) because observational data without random assignment cannot eliminate all unobserved confounding.
- **Language Guardrails:** The platform strictly enforces observational language (*"associated with"*, *"mechanistically explains"*, *"corroborated by"*) and prevents ungrounded assertions of true causation.

---

## 2. Benchmark Scope: 115 Enterprise Scenarios

- **Evaluation Suite:** RootCause AI achieves **87.0% Top-1 accuracy**, **96.5% Top-3 accuracy**, **0.9174 MRR**, and **0% claim hallucination** on **115 authoritative business scenarios** derived from the Brazilian E-Commerce public dataset (Olist).
- **Scope:** Scenarios span diverse anomaly types including logistics carrier delays, product pricing shifts, demand shocks, regional concentrations, and category mix variations across Easy, Medium, and Hard difficulty tiers.
- **Date Registry Integrity:** All scenarios execute against active Olist transaction windows. Exactly 6 scenarios (`SCN-053`, `SCN-062`, `SCN-067`, `SCN-079`, `SCN-086`, `SCN-109`) had their initial inactive late-2016 blackout dates moved to active 2017 transaction windows, and `SCN-094` was separately disambiguated from a duplicate date to `2017-04-20` (7 total date-adjusted records, with 6 migrating from inactive 2016 dates). Ground-truth causes, mechanisms, and labels remained 100% unchanged.

---

## 3. Statistical Assumptions & Sample Size Bounds

- **Welch $t$-Test:** Assumes approximate normality for moderate-to-large sample sizes ($n \ge 30$) under the Central Limit Theorem. On very low-volume anomaly dates ($n < 10$), the engine degrades gracefully to non-parametric bootstrap intervals.
- **Wilson Score Intervals:** Applied for operational proportions (late delivery rate, cancellation rate); provides reliable coverage even near 0% or 100%.

---

## 4. Application Access Model

- **Public Demo Deployment:** The demo environment is intentionally unauthenticated so that the FastAPI investigation endpoints, React dashboard, and benchmark evaluation suites can be inspected and run immediately without login barriers.
- **Credential Isolation:** Database connection secrets and optional LLM provider API keys are strictly maintained in server-side environment variables and never exposed to client-side code.

---

## 5. Database Architecture & Concurrency

- **Connection Management:** Backend requests execute against PostgreSQL via generator context managers (`get_db_connection()`) with configurable connection timeouts.
- **Concurrency Recommendation:** For production deployments exceeding 500 requests/second, integrating connection pooling via `psycopg_pool.ConnectionPool` or PgBouncer is recommended.

---

## 6. Analytical Mart Precomputation

- **Feature Marts:** RootCause AI queries precomputed analytical marts (`fact_order_analytics`, `fact_daily_kpis`, `dim_customer_cohorts`).
- **Limitation:** The platform assumes analytical data has been loaded into batch marts rather than subscribing directly to raw streaming message queues (e.g., Apache Kafka or Apache Flink).
