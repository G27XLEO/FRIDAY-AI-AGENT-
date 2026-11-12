#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [[ -x .venv/bin/python ]]; then
  source .venv/bin/activate
fi
python -m friday_agent.doctor
mkdir -p .run

python -m friday_agent.mcp_server > .run/mcp.log 2>&1 &
echo $! > .run/mcp.pid

python -m friday_agent.livekit_agent dev > .run/livekit.log 2>&1 &
echo $! > .run/livekit.pid

echo "FRIDAY MCP and LiveKit agent started in background. Logs: .run/*.log"
