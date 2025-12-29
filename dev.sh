#!/usr/bin/env bash
set -e

############################################
# Godman Lab — Local Dev Launcher
############################################

# Ensure we are at repo root
if [[ ! -f ".env.example" ]]; then
  echo "❌ Must be run from repo root (missing .env.example)"
  exit 1
fi

# Ensure 1Password CLI is available
if ! command -v op >/dev/null 2>&1; then
  echo "❌ 1Password CLI (op) not found"
  exit 1
fi

# Ensure uvicorn is installed
if ! command -v uvicorn >/dev/null 2>&1; then
  echo "❌ uvicorn not installed (pip install uvicorn)"
  exit 1
fi

echo "🔐 Injecting secrets via 1Password..."
echo "🚀 Starting Godman AI API (FastAPI + uvicorn)"

exec op run --env-file .env.example -- \
  uvicorn godman_ai.server.api:app \
  --reload \
  --host 127.0.0.1 \
  --port 8000

