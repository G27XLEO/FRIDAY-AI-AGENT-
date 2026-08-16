#!/usr/bin/env bash
set -euo pipefail

mkdir -p .run
: "${LIVEKIT_URL:?Set LIVEKIT_URL}"
: "${LIVEKIT_API_KEY:?Set LIVEKIT_API_KEY}"
: "${LIVEKIT_API_SECRET:?Set LIVEKIT_API_SECRET}"
: "${GROQ_API_KEY:?Set GROQ_API_KEY}"
: "${ELEVENLABS_API_KEY:?Set ELEVENLABS_API_KEY}"

python -m friday_agent.mcp_server > .run/mcp.log 2>&1 &
echo $! > .run/mcp.pid

python -m friday_agent.livekit_agent dev > .run/livekit.log 2>&1 &
echo $! > .run/livekit.pid

echo "FRIDAY MCP and LiveKit agent started in background. Logs: .run/*.log"
