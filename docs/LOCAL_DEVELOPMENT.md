# RootCause AI — Local Development & Deployment Guide

Welcome to the **RootCause AI** developer guide. This document provides step-by-step instructions to set up, initialize, run, test, and containerize the entire platform locally from scratch.

---

## 1. Prerequisites

Ensure the following tools are installed on your host machine:

| Component | Minimum Version | Installation / Recommendation |
| :--- | :--- | :--- |
| **Python** | 3.12+ | [python.org](https://www.python.org/) |
| **uv** (Package Manager) | Latest (0.4+) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (or `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"`) |
| **Node.js** | 20+ LTS | [nodejs.org](https://nodejs.org/) (includes `npm`) |
| **PostgreSQL** | 15+ or Supabase | Local Postgres or cloud Supabase instance |
| **Docker** (Optional) | 24+ | [docker.com](https://www.docker.com/) with Docker Compose |

---

## 2. Step-by-Step Local Setup

### Step 1: Clone Repository
```bash
git clone https://github.com/Ishita-1408/RootCause-AI.git
cd RootCause-AI
```

### Step 2: Configure Environment Variables
Copy the template configuration to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to configure your PostgreSQL credentials:
```ini
DATABASE_HOST="localhost"
DATABASE_PORT=5432
DATABASE_NAME="postgres"
DATABASE_USER="postgres"
DATABASE_PASSWORD="your-password"
```

### Step 3: Install Dependencies
```bash
# Install Python backend dependencies into virtual environment
uv sync --all-groups

# Install React frontend dependencies
cd apps/web && npm install && cd ../..
```

---

## 3. Database Initialization & Seed Data

RootCause AI uses deterministic analytical feature marts computed over e-commerce transactions:

### Step 1: Ingest Raw Datasets
```bash
uv run python scripts/ingest_olist.py
```

### Step 2: Build Analytical Marts
Compiles `fact_order_analytics`, `dim_customer_cohorts`, and `fact_daily_kpis`:
```bash
uv run python scripts/build_analytical_marts.py
```

### Step 3: Verify Database Connectivity
```bash
uv run python scripts/smoke_test.py
```

---

## 4. Running the Development Servers

### Option A: Simultaneous Development Servers
In Terminal 1 (Backend API on `http://localhost:8000`):
```bash
uv run uvicorn apps.api.main:app --reload --port 8000
```

In Terminal 2 (React Vite SPA on `http://localhost:5173`):
```bash
cd apps/web && npm run dev
```

### Option B: Unified Production Container (Docker Compose)
To launch the entire stack (PostgreSQL + FastAPI + React SPA) with a single command:
```bash
docker compose up --build
```
Access the application at `http://localhost:8000`.

---

## 5. Automated Verification & Quality Gates

RootCause AI provides a single unified quality gate script:
```bash
uv run python scripts/verify.py
```
Or via Makefile:
```bash
make verify
```

This runs all 8 tiers sequentially:
1. `uv run ruff format --check .` (Formatting)
2. `uv run ruff check .` (Linting)
3. `uv run mypy apps tests scripts evaluation` (Static type checking)
4. `uv run pytest -v` (Backend unit & integration tests, 269+ tests)
5. `npm test --prefix apps/web` (Frontend Vitest suite)
6. `npm run build --prefix apps/web` (Production Vite bundle)
7. `uv run python -m evaluation.runners.run_benchmark --verbose` (Causal benchmark)
8. `uv run python -m evaluation.runners.run_hallucination_benchmark --verbose` (Hallucination benchmark)

---

## 6. Running Independent Benchmarks

### Canonical Causal Accuracy Benchmark (Phase B)
```bash
uv run python -m evaluation.runners.run_benchmark --verbose
```
Expected Output:
- **Top-1 Accuracy:** 100.0%
- **Top-3 Accuracy:** 100.0%
- **MRR:** 1.0000
- **Evidence Grounding:** 100.0%
- **Hallucination Rate:** 0.000

### Claim-Level Hallucination Benchmark (Phase G)
```bash
uv run python -m evaluation.runners.run_hallucination_benchmark --verbose
```
Expected Output:
- **Claim Grounding Rate:** 100.0% (60/60 claims supported)
- **Hallucination Rate:** 0.0%
- **Numerical Accuracy:** 100.0%
- **Adversarial Detection Rate:** 100.0%

---

## 7. Production Deployment Guide

### Deploying to Render / Fly.io / VPS
1. Set the build command:
   ```bash
   chmod +x build.sh && ./build.sh
   ```
2. Set the start command:
   ```bash
   uv run uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT --workers 2
   ```
3. Set environment variables:
   - `DATABASE_URL` = Your production PostgreSQL / Supabase connection string.
   - `CORS_ORIGINS` = Allowed frontend domains (e.g. `'["*"]'`).
   - `LLM_API_KEY` = (Optional) OpenAI or Gemini API key for AI memo synthesis.
