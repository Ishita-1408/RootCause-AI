# syntax=docker/dockerfile:1
# -----------------------------------------------------------------------------
# RootCause AI — Unified Production Dockerfile
# Multi-stage build combining Node 20 (React SPA) and Python 3.12 (FastAPI + uv)
# -----------------------------------------------------------------------------

# =============================================================================
# Stage 1: Build React Frontend SPA
# =============================================================================
FROM node:20-slim AS frontend-builder

WORKDIR /app/apps/web

COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

COPY apps/web/ ./
RUN npm run build

# =============================================================================
# Stage 2: Build Python Backend Virtual Environment with uv
# =============================================================================
FROM python:3.12-slim AS backend-builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml .
RUN uv venv /app/.venv && \
    uv pip install --no-cache -r pyproject.toml

# =============================================================================
# Stage 3: Minimal Production Runtime
# =============================================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Security: Create non-root system group and user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -d /app appuser

# Copy virtual environment from backend builder
COPY --from=backend-builder --chown=appuser:appgroup /app/.venv /app/.venv

# Copy application source code
COPY --chown=appuser:appgroup apps /app/apps
COPY --chown=appuser:appgroup pyproject.toml /app/pyproject.toml

# Copy compiled frontend SPA static assets to be served by FastAPI
COPY --from=frontend-builder --chown=appuser:appgroup /app/apps/web/dist /app/apps/web/dist

# Environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT="production"

# Switch to non-root user
USER appuser:appgroup

# Expose backend API / SPA port
EXPOSE 8000

# Health check against liveness endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Production server entrypoint
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log"]
