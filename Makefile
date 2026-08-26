# -----------------------------------------------------------------------------
# RootCause AI — Makefile
# Unified Developer Workflow & Quality Gates
# -----------------------------------------------------------------------------

.PHONY: help setup dev-backend dev-frontend lint format test test-frontend build-frontend benchmark hallucination verify docker-build docker-up clean

PYTHON := uv run python
NPM := npm

help:
	@echo "========================================================================"
	@echo " RootCause AI — Developer Command Reference"
	@echo "========================================================================"
	@echo "  make setup          : Install backend and frontend dependencies"
	@echo "  make dev-backend    : Start FastAPI backend server on :8000"
	@echo "  make dev-frontend   : Start Vite React SPA on :5173"
	@echo "  make lint           : Run Ruff and Mypy static analysis"
	@echo "  make format         : Format code using Ruff"
	@echo "  make test           : Run full Pytest backend test suite (269+ tests)"
	@echo "  make test-frontend  : Run Vitest frontend tests"
	@echo "  make build-frontend : Compile production React bundle in apps/web/dist"
	@echo "  make benchmark      : Run 6-scenario canonical causal benchmark"
	@echo "  make hallucination  : Run 60-claim hallucination evaluator"
	@echo "  make verify         : Execute complete 8-tier verification suite"
	@echo "  make docker-build   : Build production Docker image"
	@echo "  make docker-up      : Start full stack with Docker Compose"
	@echo "========================================================================"

setup:
	uv sync --all-groups
	cd apps/web && $(NPM) install

dev-backend:
	uv run uvicorn apps.api.main:app --reload --port 8000

dev-frontend:
	cd apps/web && $(NPM) run dev

lint:
	uv run ruff check .
	uv run mypy apps tests scripts evaluation

format:
	uv run ruff format .
	uv run ruff check --fix .

test:
	uv run pytest -v

test-frontend:
	cd apps/web && $(NPM) test

build-frontend:
	cd apps/web && $(NPM) run build

benchmark:
	$(PYTHON) -m evaluation.runners.run_benchmark --verbose

hallucination:
	$(PYTHON) -m evaluation.runners.run_hallucination_benchmark --verbose

verify:
	$(PYTHON) scripts/verify.py

docker-build:
	docker build -t rootcause-ai:latest .

docker-up:
	docker compose up --build

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache apps/web/dist
