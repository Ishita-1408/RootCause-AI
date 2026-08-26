#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# RootCause AI — Production Build Script for Render Free Web Service
# -----------------------------------------------------------------------------
set -e

echo "=== [1/3] Installing Python Dependencies with uv ==="
pip install uv
uv sync --no-dev

echo "=== [2/3] Installing Frontend Dependencies ==="
cd apps/web
npm ci

echo "=== [3/3] Building Production React Bundle ==="
npm run build
cd ../..

echo "=== Production Build Completed Successfully! ==="
