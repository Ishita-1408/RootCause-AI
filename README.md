# RootCause AI

RootCause AI is an autonomous business investigation platform.

It investigates business questions such as:

> Why did revenue decline?

The system combines:
- Business intelligence
- SQL analytics
- Statistical analysis
- Machine learning
- Anomaly detection
- Forecasting
- Root-cause analysis
- Agentic AI
- Evidence-based explanations

## Project Status

🚧 Phase 0: Project Foundation

## Planned Architecture

```
Next.js
  ↓
FastAPI
  ↓
Investigation Engine
  ↓
Analytics Engine
  ↓
Statistics / ML
  ↓
Supabase PostgreSQL
  ↓
DuckDB
```

## Getting Started (Backend)

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package and project manager

### Setup

1. Clone the repository and navigate to the project root:
   ```bash
   cd RootCauseAI
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. Install dependencies using `uv`:
   ```bash
   uv sync
   ```

### Running the API Server

Start the local development server:
```bash
uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

Access the health check endpoint:
```bash
curl http://127.0.0.1:8000/health
```

Interactive API documentation will be available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Testing and Code Quality

Run tests:
```bash
uv run pytest -v
```

Format code:
```bash
uv run ruff format .
```

Lint code:
```bash
uv run ruff check .
```

Type check:
```bash
uv run mypy apps tests
```
