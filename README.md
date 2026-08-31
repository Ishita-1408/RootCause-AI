# RootCause AI

### Autonomous Business Root-Cause Investigation

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-46E3B7.svg)](https://rootcause-ai-mcbj.onrender.com)
[![CI Quality Gate](https://github.com/Ishita-1408/RootCause-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/Ishita-1408/RootCause-AI/actions)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://reactjs.org/)
[![Top-1 Accuracy](https://img.shields.io/badge/Benchmark%20Top--1-87.0%25%20(115%20Scenarios)-brightgreen.svg)]()
[![Benchmark Hallucination](https://img.shields.io/badge/Benchmark%20Hallucination-0.0%25-brightgreen.svg)]()
[![Pytest](https://img.shields.io/badge/Pytest-269%20passed-success.svg)]()
[![Type Checked](https://img.shields.io/badge/Mypy-strict%20checked-blue.svg)]()

[**🚀 Live Demo**](https://rootcause-ai-mcbj.onrender.com) &nbsp;|&nbsp; [**💻 GitHub Repository**](https://github.com/Ishita-1408/RootCause-AI) &nbsp;|&nbsp; [**📊 Benchmark Report**](#evaluation--benchmark)

> **Why did revenue change?**<br>
> **What actually drove it?**<br>
> **What evidence supports the finding?**<br>
> **What should the business do next?**

RootCause AI automatically investigates business KPI anomalies, ranks competing root-cause hypotheses using multiple statistical and analytical signals, builds an interactive evidence graph, and produces evidence-backed recommendations.

**87.0% Top-1** &nbsp;|&nbsp; **96.5% Top-3** &nbsp;|&nbsp; **115 Scenarios** &nbsp;|&nbsp; **0% Benchmark Hallucination**

---

## Problem

Modern analytics, data science, and operational teams spend countless hours diagnosing executive questions like:
> *"Why did revenue decline 28.4% last Tuesday?"*

When organizations delegate these diagnostic investigations to generic LLMs, they encounter two fundamental failure modes:
1. **Numerical Hallucination:** LLMs invent plausible-sounding percentages, ungrounded baseline comparisons, and contradictory metrics not supported by underlying transactional data.
2. **Conflating Association with Causation:** LLMs routinely confuse *where* an anomaly concentrated (e.g., "São Paulo order volume fell") with *why* it occurred (e.g., "Carrier transit delays escalated +4.2 days, causing widespread SLA breaches").

---

## Solution

**RootCause AI** eliminates both failure modes through an architecture where **the LLM is NOT the source of numerical truth**.

All KPI calculations, mathematical variance decompositions, statistical hypothesis tests, change-point detections, and causal hypothesis rankings are computed by **deterministic Python and SQL analytical engines**. The optional LLM layer functions strictly as an executive narrator, bounded by an active **Evidence-Grounded Claim Firewall** ensuring a 0% hallucination rate on the 115-scenario benchmark.

RootCause AI answers four core business questions during every investigation:
- **What changed?** (Severity, observed vs rolling 7-day baseline, percentage delta)
- **Why did it change?** (Exact multiplicative Volume vs AOV decomposition, operational indicators, segment drill-down)
- **What evidence supports the conclusion?** (Deterministic Evidence Graph linking metrics to query provenance and statistical $p$-values)
- **What should the business do next?** (Evidence-grounded, prioritized operational recommendations)

---

## Key Capabilities

- **🔍 Autonomous Investigation Agent:** Dynamic priority planner that traverses dimensional branches (Category, State, Seller, Logistics) without manual query authoring.
- **➗ Exact Multiplicative Decomposition:** Mathematically decomposes GMV variance into Volume, Average Order Value (AOV), and Interaction effects down to the cent.
- **📊 Statistical Inference Engine:** Validates metric shifts with two-sample Welch $t$-tests ($p < 0.05$), Wilson score intervals for operational proportions, and PELT / CUSUM change-point detection.
- **🧭 Multi-Signal Causal Ranker:** Ranks root-cause candidates by fusing quantitative contribution, directional consistency, metric domain relevance, statistical confidence, and temporal change-point alignment. The system ranks evidence-supported causal hypotheses from observational business data; it does not claim experimental causal identification.
- **🛡️ Evidence-Grounded Claim Verification:** Intercepts executive summary generation, parses numerical and directional statements, and verifies each claim against the analytical evidence pool before rendering.
- **🕸️ Interactive Evidence Graph (DAG):** Directed Acyclic Graph tracing the causal provenance from incident down to verified transactional data.
- **⏪ Deterministic Investigation Replay:** Immutable snapshot engine for auditing and reproducing investigations step-by-step.
- **🥊 Executive Challenge Mode:** Counterfactual audit engine that systematically answers adversarial questions (*"Why not AOV?"*, *"What contradicts this?"*, *"Show weakest evidence"*).

---

## Investigation Workflow

```
Business Anomaly Detected
         ↓
KPI Multiplicative Decomposition (Volume vs. AOV Effects)
         ↓
Contributing-Driver & Dimensional Drill-Down (Category, State, Seller, Carrier)
         ↓
Multi-Signal Causal Ranking (Attribution × Directional Alignment × Statistical Confidence)
         ↓
Evidence Graph Construction (Provenance Tracking)
         ↓
Evidence-Grounded Claim Verification (0% Hallucination Rate on Benchmark)
         ↓
Evidence-Backed Narrative & Actionable Recommendations
```

---

## Architecture

```
                      React Dashboard (TypeScript + Vite)
                                      ↓
                              FastAPI Service
                                      ↓
                         Investigation Agent Engine
                                      ↓
                              Analytics Engine
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ • Anomaly Detection (Rolling Baselines & Z-Score Severity)             │
 │ • KPI Decomposition (Multiplicative Volume vs AOV Effects)              │
 │ • Change-Point Detection (PELT & CUSUM Regime Shifts)                  │
 │ • Statistical Analysis (Welch t-test, Wilson Score CI, p-values)        │
 │ • Causal Ranking (Multi-Signal Deterministic Hypothesis Scoring)        │
 └─────────────────────────────────────────────────────────────────────────┘
                                      ↓
                            Evidence Graph (DAG)
                                      ↓
                          PostgreSQL Data Layer
               (fact_order_analytics, fact_daily_kpis, marts)

 Optional Layer:
   Investigation Agent ──► LLM Executive Narrator (OpenAI / Gemini)
                       └──► Deterministic Rule Synthesizer (Fallback)
```

---

## Evidence Graph

The **Evidence Graph** provides a transparent, auditable causal DAG connecting each investigation finding:

$$\text{Incident} \longrightarrow \text{Anomaly} \longrightarrow \text{Driver Mechanism} \longrightarrow \text{Supporting Evidence} \longrightarrow \text{Affected Segment} \longrightarrow \text{Root Cause}$$

Every node contains verified mathematical metadata: observed values, baseline values, absolute deltas, percentage contributions, statistical significance flags ($p < 0.05$), and SQL execution provenance.

---

## Actionable Recommendations

RootCause AI generates prioritized, evidence-backed operational actions directly derived from the identified causal mechanism:
- **Logistics & Carrier SLA Degradation:** Audit regional dispatch hubs, trigger carrier penalty clauses, and re-route delayed fulfillment routes.
- **Order Volume Contraction:** Audit top affected demographic segments, inspect acquisition spend, and review conversion funnel friction.
- **AOV / Basket Size Contraction:** Evaluate category promotion discounting, adjust cross-sell bundles, and review high-ticket category inventory.
- **Customer Satisfaction Decline:** Review recent delivery lead times in affected categories and inspect merchant return / refund rates.

---

## Evaluation & Benchmark

RootCause AI is evaluated against an authoritative benchmark of **115 real-world business scenarios** derived from the Brazilian E-Commerce dataset (Olist). The system ranks evidence-supported causal hypotheses from observational business data; it does not claim experimental causal identification.

| Metric | Measured Score | Benchmark Definition |
| :--- | :---: | :--- |
| **Scenarios Evaluated** | **115** | Authoritative real-world business scenarios from Olist data |
| **Top-1 Root Cause Accuracy** | **87.0%** (100/115) | Primary causal mechanism correctly ranked at Rank #1 |
| **Top-3 Accuracy** | **96.5%** (111/115) | Primary causal mechanism ranked within Top-3 candidates |
| **Mean Reciprocal Rank (MRR)** | **0.9174** | Average reciprocal rank of true causal mechanism ($1/\text{rank}$) |
| **Evidence Grounding Rate** | **100.0%** | Proportion of analytical claims grounded in verified marts |
| **Claim Hallucination Rate** | **0.0%** | 0% hallucination rate on the 115-scenario benchmark |
| **Average Investigation Latency** | **719.9 ms** | End-to-end diagnostic pipeline execution time |

### Performance by Scenario Difficulty

- **Easy (45 scenarios):** Top-1 = **88.9%** (40/45) | Top-3 = 97.8% | MRR = **0.9333**
- **Medium (48 scenarios):** Top-1 = **89.6%** (43/48) | Top-3 = 97.9% | MRR = **0.9271**
- **Hard (22 scenarios):** Top-1 = **77.3%** (17/22) | Top-3 = 90.9% | MRR = **0.8636**

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Analytics & Engine** | Python 3.12, DuckDB, Polars, PyArrow, SciPy, Statsmodels, Scikit-Learn |
| **API & Backend** | FastAPI, Pydantic v2, Uvicorn, Psycopg 3, uv |
| **Database** | PostgreSQL (Supabase / Render) with dimensional analytics marts |
| **Frontend & UI** | React 18, TypeScript, Vite, TailwindCSS, Lucide Icons |
| **Quality & MLOps** | Pytest (269 tests), Mypy (strict), Ruff (linter & formatter), Docker |

---

## Repository Structure

```
RootCauseAI/
├── apps/
│   ├── ai/              # LLM provider abstractions & deterministic fallbacks
│   ├── analytics/       # Core analytics engine (decomposition, stats, ranker, graph)
│   ├── api/             # FastAPI routers and request schemas
│   └── web/             # React 18 frontend dashboard and visualization components
├── docs/                # Architecture specifications, limitations, and demo scripts
├── evaluation/          # Benchmark suite (115 scenarios, metrics, runner, reports)
├── scripts/             # Data ingestion and analytical mart builders
├── supabase/            # Database migrations and mart schema definitions
└── tests/               # 269 automated unit, integration, and benchmark tests
```

---

## Local Development

### 1. Prerequisites
- Python 3.12+ and [uv](https://github.com/astral-sh/uv)
- Node.js 18+ and npm
- PostgreSQL database (or local SQLite/DuckDB fallback)

### 2. Setup & Installation
```bash
# Clone repository
git clone https://github.com/Ishita-1408/RootCause-AI.git
cd RootCause-AI

# Configure environment
cp .env.example .env

# Install Python & Frontend dependencies
uv sync --all-groups
cd apps/web && npm install && cd ../..
```

### 3. Initialize Analytical Marts
```bash
uv run python scripts/ingest_olist.py
uv run python scripts/build_analytical_marts.py
```

### 4. Run Development Servers
```bash
# Terminal 1: FastAPI Backend (http://localhost:8000)
uv run uvicorn apps.api.main:app --reload --port 8000

# Terminal 2: React Frontend (http://localhost:5173)
cd apps/web && npm run dev
```

### 5. Run Tests & Validation
```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy apps evaluation tests
```

---

## Deployment

RootCause AI is containerized via Docker and deployable to cloud container platforms like Render:
```bash
# Build Docker image
docker build -t rootcause-ai .

# Run Docker container
docker run -p 8000:8000 --env-file .env rootcause-ai
```

---

## Limitations

- **Observational Causal Hypothesis Ranking:** The system ranks evidence-supported causal hypotheses from observational business data; it does not claim experimental causal identification.
- **Analytical Mart Ingestion:** Requires batch analytical marts (`fact_order_analytics`, `fact_daily_kpis`) rather than raw unbounded real-time message streams.
- **Demo Deployment:** The demo environment is public and unauthenticated to enable immediate benchmark and API inspection without login barriers.
