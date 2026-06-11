#!/usr/bin/env bash
# Start the Cashflow API and pre-built frontend on one port (default 8000).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT/backend"
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

if [[ ! -f "$BACKEND_DIR/.env" && -f "$BACKEND_DIR/.env.example" ]]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi

if [[ ! -d "$ROOT/frontend/dist" ]]; then
  echo "Missing frontend/dist. Rebuild the UI once with Node.js: cd frontend && npm install && npm run build" >&2
  exit 1
fi

echo "App:      http://127.0.0.1:${BACKEND_PORT}"
echo "API docs: http://127.0.0.1:${BACKEND_PORT}/docs"
echo "Press Ctrl+C to stop."
echo

cd "$BACKEND_DIR"
exec "$UVICORN" app.main:app --reload --host 127.0.0.1 --port "$BACKEND_PORT"
