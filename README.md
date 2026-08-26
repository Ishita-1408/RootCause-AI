# RootCause AI

> **Autonomous Business Investigation Platform for Evidence-Backed Root-Cause Analysis**

RootCause AI automatically monitors e-commerce and business metrics, detects anomalous performance swings, isolates mathematical root causes, and synthesizes executive decision memos without hallucinating numerical evidence.

---

## The Problem RootCause AI Solves

When critical Key Performance Indicators (KPIs) like Gross Merchandise Value (GMV), conversion rate, or order volume experience sudden drops or surges, business leaders need immediate answers:
- *Why did revenue decline by 28% yesterday?*
- *Was the decline driven by transaction volume drops or smaller basket sizes (AOV)?*
- *Which specific product categories, regions, or merchant corridors caused the shift?*
- *Were delivery delays or operational bottlenecks contributing factors?*

Traditional business intelligence requires hours of manual SQL slicing by analysts, while generic LLM chatbots frequently invent numbers and confuse correlation with causation. 

**RootCause AI bridges this gap**: all mathematical calculations, decompositions, and multi-dimensional contributions are computed deterministically in PostgreSQL and Python. The AI layer is strictly constrained to interpreting verified numerical evidence, delivering audit-trailed executive insights in seconds.

---

## Key Capabilities

- **Daily Anomaly Detection**: Statistical rolling-baseline anomaly detector with zero-lookahead Z-score scoring across core business metrics.
- **Deterministic Root-Cause Investigation**: Multi-dimensional contribution analysis calculating exact percentage shares and absolute deviations.
- **Exact Volume vs. AOV Decomposition**: Isolates the mathematical identity:
  $$\Delta \text{Revenue} = (\Delta \text{Volume} \times \text{AOV}_{\text{base}}) + (\text{Volume}_{\text{base}} \times \Delta \text{AOV}) + (\Delta \text{Volume} \times \Delta \text{AOV})$$
- **Dimensional Contribution Ranking**: Evaluates and ranks macro drivers across product categories, customer regional states, payment methods, and logistics corridors.
- **AI Executive Investigation Memo**: Generates structured business memos (executive summaries, verified key findings, non-causal business interpretations, and actionable next steps) directly from database evidence.
- **Multi-Step Investigation Agent**: Autonomous state-machine investigation agent that schedules adaptive diagnostic branches, prunes low-signal slices, and maintains an immutable audit trace.
- **Interactive Web Dashboard**: Production React interface featuring interactive time-series anomaly charts, KPI summary cards, dimensional drill-down drawers, AI memo summaries, and agent execution logs.

---

## High-Level Architecture

```
                       ┌─────────────────────────────────────────┐
                       │        React + TypeScript Dashboard     │
                       │    (Executive KPIs, Timelines, Memos)   │
                       └────────────────────┬────────────────────┘
                                            │
                                            │ Typed REST Requests (JSON)
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     FastAPI Backend Engine                                      │
│                                                                                                 │
│  ┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────────────────┐  │
│  │   Anomaly Detector    │   │  Root-Cause Engine    │   │    Autonomous Investigation Agent │  │
│  │ (Rolling Z-Score Band)│   │ (Volume/AOV & Slices) │   │     (Adaptive State Machine)      │  │
│  └───────────┬───────────┘   └───────────┬───────────┘   └─────────────────┬─────────────────┘  │
│              │                           │                                 │                    │
│              └───────────────────────────┴────────────────┬────────────────┘                    │
│                                                           │                                     │
│                                                           ▼                                     │
│                                       ┌───────────────────────────────────────┐                 │
│                                       │     AI Narrative Synthesis Layer      │                 │
│                                       │ (Google Gemini / OpenAI / Fallback)   │                 │
│                                       └───────────────────────────────────────┘                 │
└───────────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                                    │
                                                    │ High-Performance SQL (psycopg v3)
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Supabase PostgreSQL Database                                  │
│                                                                                                 │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐  ┌───────────────────────┐  │
│  │    fact_order_analytics      │  │       fact_daily_kpis        │  │  dim_customer_cohorts │  │
│  │ (Grain: 1 row per order_id)  │  │(Grain: date x product_cat)   │  │(Grain: customer_uid)  │  │
│  └──────────────────────────────┘  └──────────────────────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, Uvicorn, psycopg v3
- **Data Engine**: PostgreSQL / Supabase, analytical dimensional marts & views
- **AI / LLM Integration**: OpenAI-compatible API provider (Google Gemini, OpenAI, Local Ollama) + Deterministic Offline Fallback Rule Synthesizer
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons
- **Testing & Quality**: pytest (139 tests), vitest (3 tests), Ruff, mypy
- **Packaging & Deployment**: `uv` package manager, Docker, Docker Compose, Render PaaS

---

## Repository Structure

```
RootCauseAI/
├── apps/
│   ├── ai/                      # LLM provider abstractions, prompts, and narrative schemas
│   ├── analytics/               # Analytics engine, anomaly detector, diagnostics, agent
│   ├── api/                     # FastAPI application, routers, database connection pool, config
│   └── web/                     # React + TypeScript + Vite frontend dashboard
├── data/
│   └── raw/                     # Local data directory for raw dataset archives (.gitignored)
├── docs/                        # Technical architecture specifications & metric dictionaries
├── notebooks/                   # Exploratory data analysis notebooks
├── scripts/                     # Mart builders, ingestion pipelines, query runners, demos
├── supabase/
│   ├── migrations/              # PostgreSQL DDL migrations for raw schema & analytical marts
│   └── validation/              # Analytical mart integrity & revenue conservation tests
├── tests/                       # Complete backend unit and integration test suite
├── .env.example                 # Environment configuration template
├── Dockerfile                   # Multi-stage production backend Dockerfile
├── docker-compose.yml           # Multi-container full-stack deployment configuration
├── pyproject.toml               # Python project dependencies and tool configurations
├── render.yaml                  # Render Cloud PaaS web service specification
├── build.sh                     # Unified build script for Render deployment
└── uv.lock                      # Deterministic Python dependency lockfile
```

---

## Prerequisites

- **Python**: Version 3.12+ installed
- **Node.js**: Version 20+ with `npm`
- **Package Manager**: [uv](https://docs.astral.sh/uv/) (recommended) or `pip`
- **Database**: PostgreSQL 15+ or a [Supabase](https://supabase.com) project

---

## Local Setup

### 1. Configure Environment Variables

```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and configure your database connection parameters.

### 2. Install Python Dependencies

Using `uv` (recommended):
```bash
uv sync
```

Or using standard `pip`:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 3. Install Frontend Dependencies

```bash
# Windows PowerShell
npm.cmd --prefix apps/web install

# macOS / Linux
npm --prefix apps/web install
```

---

## Database Configuration (Supabase PostgreSQL)

RootCause AI relies on structured analytical data marts. Apply migrations in your Supabase SQL Editor in numerical order:

1. `supabase/migrations/001_create_datasets.sql` — Dataset registry table
2. `supabase/migrations/002_create_olist_schema.sql` — Raw operational tables
3. `supabase/migrations/003_create_analytical_marts.sql` — Core analytical marts (`fact_order_analytics`, `fact_daily_kpis`, `analytics_daily_kpis`, `dim_customer_cohorts`)

To populate or refresh analytical marts from the command line:
```bash
uv run python scripts/build_analytical_marts.py
```

---

## Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `"RootCause AI"` | Application display name |
| `ENVIRONMENT` | `"production"` | Environment (`development`, `staging`, `production`) |
| `HOST` | `"0.0.0.0"` | API server host interface |
| `PORT` | `8000` | API server port |
| `DATABASE_HOST` | `"localhost"` | Supabase / PostgreSQL host |
| `DATABASE_PORT` | `5432` | Database port (5432 or 6543 pooler) |
| `DATABASE_NAME` | `"postgres"` | Database name |
| `DATABASE_USER` | `"postgres"` | Database user |
| `DATABASE_PASSWORD` | `""` | Database password |
| `DATABASE_CONNECT_TIMEOUT` | `5` | Connection timeout in seconds |
| `LLM_API_KEY` | `""` | Optional LLM API key (activates live LLM if provided) |
| `LLM_MODEL` | `"gemini-2.0-flash"` | Target LLM model name |
| `LLM_BASE_URL` | `""` | LLM endpoint URL (Google Gemini or OpenAI) |
| `CORS_ORIGINS` | `"http://localhost:5173,..."` | Comma-separated list of allowed frontend origins |

---

## LLM Configuration (Google Gemini & OpenAI)

RootCause AI features a flexible provider architecture with a **zero-configuration deterministic fallback**:

### 1. Offline Deterministic Fallback (Zero API Key Needed)
- If `LLM_API_KEY` is omitted or empty, RootCause AI automatically activates the built-in **Deterministic Fallback Rule Synthesizer**.
- The platform remains 100% operational, generating structured, factual executive summaries offline with zero external API calls or latency.

### 2. Using Google Gemini (via OpenAI-Compatible Endpoint)
Set in `.env`:
```env
LLM_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
LLM_MODEL="gemini-2.0-flash"
LLM_API_KEY="your-gemini-api-key"
```

### 3. Using OpenAI
Set in `.env`:
```env
LLM_BASE_URL="https://api.openai.com/v1"
LLM_MODEL="gpt-4o-mini"
LLM_API_KEY="your-openai-api-key"
```

> **Security Reminder**: Never place your actual API key in `.env.example`, `README.md`, or any committed file.

---

## Running the Application

### Running the Backend

```bash
uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```
- API Base: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc UI: `http://localhost:8000/redoc`

### Running the Frontend (Development Server)

```bash
# Windows PowerShell
npm.cmd --prefix apps/web run dev

# macOS / Linux
npm --prefix apps/web run dev
```
- Web Dashboard: `http://localhost:5173` (automatically proxies API requests to `:8000`)

### Running the Complete Application (Unified Server)

In unified production mode, FastAPI serves the compiled React SPA and REST API from a single port:

```bash
# 1. Build React SPA
npm.cmd --prefix apps/web run build

# 2. Start Unified FastAPI Server
uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000` to access the full application.

### Running with Docker Compose

```bash
docker compose up --build
```

---

## Building the Production Frontend

```bash
# Windows PowerShell
npm.cmd --prefix apps/web run build

# macOS / Linux
npm --prefix apps/web run build
```
Build output is generated in `apps/web/dist/`.

---

## Running Tests & Quality Checks

```bash
# 1. Backend test suite (139 unit and integration tests)
uv run pytest tests/

# 2. Frontend test suite (Vitest)
npm.cmd --prefix apps/web test

# 3. Code formatting verification (Ruff)
uv run ruff format --check .

# 4. Code linting (Ruff)
uv run ruff check .

# 5. Static type verification (mypy)
uv run mypy apps tests scripts
```

---

## Free Render Deployment Instructions

RootCause AI is pre-configured for **100% free deployment** on [Render](https://render.com) as a single unified web service:

1. **Push to GitHub**: Push your repository to GitHub.
2. **Create Web Service on Render**:
   - Select **New +** → **Web Service** and connect your repository.
   - **Runtime**: `Python`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `python -m uv run uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT --workers 2`
   - **Plan**: `Free`
3. **Configure Environment Variables on Render**:
   - `PYTHON_VERSION`: `3.12.4`
   - `NODE_VERSION`: `20.18.0`
   - `ENVIRONMENT`: `production`
   - `DATABASE_HOST`: `aws-0-us-east-1.pooler.supabase.com`
   - `DATABASE_PORT`: `5432`
   - `DATABASE_NAME`: `postgres`
   - `DATABASE_USER`: `postgres.yourprojectref`
   - `DATABASE_PASSWORD`: `your-supabase-password`
   - `DATABASE_CONNECT_TIMEOUT`: `5`
   - `LLM_API_KEY`: *(Optional)*
   - `LLM_MODEL`: *(Optional)*
4. **Deploy**: Render executes `build.sh` (installs `uv`, syncs Python dependencies, builds the React frontend) and launches the application.

---

## API Documentation Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service liveness health check |
| `GET` | `/api/v1/ready` | Service readiness check verifying database connectivity |
| `GET` | `/api/v1/datasets` | List registered analytical datasets |
| `POST` | `/api/v1/anomalies/detect` | Detect time-series anomalies using rolling Z-scores |
| `POST` | `/api/v1/rootcause/investigate` | Root-cause analysis with exact volume/AOV decomposition |
| `POST` | `/api/v1/diagnostics/run` | Multi-dimensional diagnostic scoring & operational indicators |
| `POST` | `/api/v1/ai/investigate` | Synthesize structured AI executive memos from verified evidence |
| `POST` | `/api/v1/agent/investigate` | Execute autonomous multi-step investigation agent with trace |

Interactive API documentation is accessible at `/docs` (Swagger UI) and `/redoc` (ReDoc).

---

## Security Notes

- **Zero Secret Exposure**: `.env` and credentials are never committed. Secrets are excluded by `.gitignore` and `.dockerignore`.
- **Zero Frontend Secrets**: The client-side React SPA communicates solely through the backend API and never stores database credentials or service tokens.
- **Log Sanitization**: Database passwords and API keys are automatically sanitized from all server logs and error responses.

---

## Important Limitations

1. **Render Free Tier Cold Starts**: Free instances on Render spin down after 15 minutes of inactivity. Initial wake-up requests take 30–50 seconds.
2. **Correlation vs. Causality**: RootCause AI isolates mathematical contributions and statistical correlations. It does not establish direct causal certainty without controlled A/B experiments.
3. **Database Dependency**: Live analytical querying requires a connected PostgreSQL/Supabase database with populated analytical marts.

---

## Future Improvements

- Automated periodic Slack/Email anomaly digest alerts.
- Multi-dataset connector support (Shopify, BigQuery, Snowflake).
- Interactive natural language conversational interface over agent audit traces.
- Automated hypothesis back-testing against historical marketing and promotional calendars.

---

## License

This project currently has no explicit open-source license. All rights reserved.
