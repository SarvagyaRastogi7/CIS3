#!/usr/bin/env bash
# Start backend + frontend dev servers. Picks the first free port from 8000 upward.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
DEFAULT_PORT=8000

pick_uvicorn() {
  if [[ -x "$BACKEND_DIR/.venv/bin/uvicorn" ]]; then
    echo "$BACKEND_DIR/.venv/bin/uvicorn"
    return
  fi
  if command -v uvicorn >/dev/null 2>&1; then
    command -v uvicorn
    return
  fi
  echo "uvicorn not found. Create a venv in backend/ and run: pip install -r requirements.txt" >&2
  exit 1
}

BACKEND_PORT="$(python3 "$ROOT/scripts/find_free_port.py" "$DEFAULT_PORT")"
UVICORN="$(pick_uvicorn)"

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm install)
fi

if [[ ! -f "$BACKEND_DIR/.env" && -f "$BACKEND_DIR/.env.example" ]]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi

cleanup() {
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Backend:  http://127.0.0.1:${BACKEND_PORT}  (docs: /docs)"
echo "Frontend: http://localhost:5173  (proxy /api -> :${BACKEND_PORT})"
echo "Press Ctrl+C to stop both servers."
echo

(cd "$BACKEND_DIR" && "$UVICORN" app.main:app --reload --host 127.0.0.1 --port "$BACKEND_PORT") &
BACKEND_PID=$!

export BACKEND_PORT
(cd "$FRONTEND_DIR" && npm run dev) &
FRONTEND_PID=$!

wait "$BACKEND_PID" "$FRONTEND_PID"
