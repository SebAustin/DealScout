#!/usr/bin/env bash
# One-command demo launcher for judges
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PY="${PY:-python3.12}"
if ! command -v "$PY" &>/dev/null; then PY=python3; fi

if [ ! -d .venv ]; then
  "$PY" -m venv .venv
  source .venv/bin/activate
  pip install --index-url https://pypi.org/simple -r requirements.txt
  pip install --index-url https://pypi.org/simple -e .
else
  source .venv/bin/activate
fi

[ -f .env ] || cp .env.example .env

export PYTHONPATH="$ROOT"
export DEMO_MODE="${DEMO_MODE:-true}"
API_PORT="${API_PORT:-8000}"

_free_port() {
  local pids
  pids=$(lsof -ti:"$API_PORT" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "Freeing port $API_PORT (old API process)..."
    kill -9 $pids 2>/dev/null || true
    sleep 1
  fi
}

_uvicorn_args=(
  api.main:app
  --host 0.0.0.0
  --port "$API_PORT"
  --reload
  --reload-dir "$ROOT"
)

case "${1:-all}" in
  api)
    _free_port
    echo "DealPulse Scout API (demo pipeline v2) on :$API_PORT"
    uvicorn "${_uvicorn_args[@]}"
    ;;
  ui)
    streamlit run ui/app.py
    ;;
  all)
    _free_port
    echo "DealPulse Scout API (demo pipeline v2) on :$API_PORT + UI on :8501 (DEMO_MODE=$DEMO_MODE)"
    uvicorn "${_uvicorn_args[@]}" &
    sleep 2
    streamlit run ui/app.py
    ;;
  *)
    echo "Usage: ./run.sh [api|ui|all]"
    exit 1
    ;;
esac
