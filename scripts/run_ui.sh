#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log() { printf '\n[FRIDAY UI] %s\n' "$1"; }

command -v python >/dev/null 2>&1 || { echo "Python is required. Install it with: pkg install python"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "Node.js/npm is required. Install it with: pkg install nodejs"; exit 1; }

PYTHON=python

log "Installing Python dependencies"
"$PYTHON" -m pip install -r requirements.txt

if [ ! -d web/node_modules ]; then
  log "Installing web dependencies"
  (cd web && npm install)
fi

if [ ! -f web/dist/index.html ]; then
  log "Building FRIDAY web UI"
  (cd web && npm run build)
fi

mkdir -p .run

# Avoid duplicate UI servers when the command is run again.
if [ -f .run/ui.pid ] && kill -0 "$(cat .run/ui.pid)" 2>/dev/null; then
  log "FRIDAY UI is already running on port 8001 (PID $(cat .run/ui.pid))"
else
  log "Starting FRIDAY UI on http://127.0.0.1:8001"
  nohup "$PYTHON" -m friday_agent.web_server > .run/ui.log 2>&1 &
  echo $! > .run/ui.pid
  sleep 2
fi

if ! kill -0 "$(cat .run/ui.pid)" 2>/dev/null; then
  echo "FRIDAY UI failed to start. Check .run/ui.log"
  cat .run/ui.log
  exit 1
fi

log "FRIDAY UI is ready"
echo "Local:   http://127.0.0.1:8001"
echo "Android: open http://127.0.0.1:8001 in your browser"
echo "Logs:    .run/ui.log"
echo "Stop:    kill $(cat .run/ui.pid)"
