#!/usr/bin/env bash
# One-command demo launcher for judges
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PY="${PY:-python3.12}"
if ! command -v "$PY" &>/dev/null; then PY=python3; fi

VENV="$ROOT/.venv"
VENV_PY="$VENV/bin/python"
VENV_UVICORN="$VENV/bin/uvicorn"
VENV_STREAMLIT="$VENV/bin/streamlit"

_venv_ok() {
  [ -x "$VENV_PY" ] && "$VENV_PY" -c "import fastapi, streamlit, langgraph" &>/dev/null
}

if [ ! -d "$VENV" ] || ! _venv_ok; then
  echo "Creating virtualenv in .venv (Python: $PY)..."
  rm -rf "$VENV"
  "$PY" -m venv "$VENV"
  "$VENV_PY" -m pip install --index-url https://pypi.org/simple -r requirements.txt
fi

[ -f .env ] || cp .env.example .env

export PYTHONPATH="$ROOT"
export DEMO_MODE="${DEMO_MODE:-true}"
export PATH="$VENV/bin:$PATH"
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
    exec "$VENV_UVICORN" "${_uvicorn_args[@]}"
    ;;
  ui)
    exec "$VENV_STREAMLIT" run ui/app.py
    ;;
  all)
    _free_port
    echo "DealPulse Scout API (demo pipeline v2) on :$API_PORT + UI on :8501 (DEMO_MODE=$DEMO_MODE)"
    "$VENV_UVICORN" "${_uvicorn_args[@]}" &
    sleep 2
    exec "$VENV_STREAMLIT" run ui/app.py
    ;;
  *)
    echo "Usage: ./run.sh [api|ui|all]"
    exit 1
    ;;
esac
