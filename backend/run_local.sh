#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

source .venv/bin/activate
set -a
[ -f .env ] && source .env
set +a

uvicorn app.main:app --reload --host "${HOST:-0.0.0.0}" --port "${PORT:-5050}"
