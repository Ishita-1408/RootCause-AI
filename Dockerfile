# syntax=docker/dockerfile:1
# -----------------------------------------------------------------------------
# RootCause AI — Backend Production Dockerfile
# Multi-stage Python 3.12 build using uv with non-root security execution.
# -----------------------------------------------------------------------------

# Stage 1: Build virtual environment with uv
FROM python:3.12-slim AS builder

# Install uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation and fast copy
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency definition
COPY pyproject.toml .

# Install dependencies into /app/.venv without dev packages
RUN uv venv /app/.venv && \
    uv pip install --no-cache -r pyproject.toml

# -----------------------------------------------------------------------------
# Stage 2: Minimal Production Runtime
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Security: Create dedicated non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -d /app appuser

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Copy application source code
COPY --chown=appuser:appgroup apps /app/apps
COPY --chown=appuser:appgroup pyproject.toml /app/pyproject.toml

# Set environment paths and python flags
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT="production"

# Switch to non-root user
USER appuser:appgroup

# Expose backend API port
EXPOSE 8000

# Health check using built-in Python urllib against liveness endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Production server entrypoint
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log"]
