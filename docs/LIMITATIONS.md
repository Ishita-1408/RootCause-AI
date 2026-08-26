# RootCause AI — Engineering Limitations & Design Assumptions

A rigorous Data Science and ML Engineering project requires transparency regarding assumptions, scope boundaries, and design trade-offs. This document outlines the engineering realities and intentional constraints of RootCause AI.

---

## 1. Causal Scope: Observational Ranking vs. Counterfactual Inference

- **Observational Causal Hypothesis Ranking:** RootCause AI performs mathematical variance decomposition, statistical association testing, and operational corroboration over observational transactional data.
- **Limitation:** The system does **not** claim full counterfactual causal inference (e.g., Pearl's *do*-calculus, Synthetic Controls, or Instrumental Variables) because observational data without random assignment cannot eliminate unobserved confounding.
- **Language Guardrails:** The platform strictly enforces observational language (*"associated with"*, *"mechanistically explains"*, *"corroborated by"*) and prevents ungrounded assertions of true causation.

---

## 2. Benchmark Scope: 6 Canonical Scenarios

- **Current Evaluation Suite:** RootCause AI achieves 100% Top-1 accuracy and 0% claim hallucination on **6 canonical, multi-dimensional business scenarios** derived from the Brazilian E-Commerce public dataset (Olist).
- **Limitation:** While these 6 scenarios cover diverse failure modes (fulfillment delays, marketing contraction, pricing shifts, partner degradation, demand surges), they do not represent the infinite variety of real-world business anomalies.
- **Next Horizon:** Expanding the benchmark harness to 50+ diverse enterprise scenarios across fintech, SaaS, and retail domains.

---

## 3. Statistical Assumptions & Sample Size Bounds

- **Welch $t$-Test:** Assumes approximate normality for moderate-to-large sample sizes ($n \ge 30$) under the Central Limit Theorem. On very low-volume anomaly dates ($n < 10$), the engine degrades gracefully to non-parametric bootstrap intervals.
- **Wilson Score Intervals:** Applied for operational proportions (late delivery rate, cancellation rate); provides reliable coverage even near 0% or 100%.

---

## 4. Authentication: API-Key RBAC vs. Enterprise IAM

- **Current Implementation:** Dual-mode authentication (`AUTH_ENABLED=true/false`) with `X-API-Key` and `Authorization: Bearer <token>` enforcing a 3-tier Role-Based Access Control hierarchy (`Viewer < Analyst < Admin`).
- **Limitation:** The current release does not include OAuth2/OIDC/SAML integration (e.g., Okta, Auth0, Microsoft Entra ID). It is designed for microservice API integration and internal analytics tooling.

---

## 5. Database Architecture & Concurrency

- **Connection Management:** Backend requests execute against PostgreSQL via generator context managers (`get_db_connection()`) with configurable connection timeouts.
- **High-Concurrency Recommendation:** For production deployments exceeding 500 requests/second, integrating connection pooling via `psycopg_pool.ConnectionPool` or PgBouncer is recommended.

---

## 6. Analytical Mart Precomputation

- **Feature Marts:** RootCause AI queries precomputed analytical marts (`fact_order_analytics`, `fact_daily_kpis`, `dim_customer_cohorts`).
- **Limitation:** The platform assumes analytical data has been loaded into batch marts rather than subscribing directly to real-time streaming message queues (e.g., Apache Kafka or Apache Flink).
