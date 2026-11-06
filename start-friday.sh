#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if ! python -c 'import livekit.agents' >/dev/null 2>&1; then
  echo "FRIDAY dependencies are not installed. Installing now..."
  python -m pip install --user -r requirements.txt
  python -m livekit.agents download-files
fi

required=(LIVEKIT_URL LIVEKIT_API_KEY LIVEKIT_API_SECRET GROQ_API_KEY ELEVENLABS_API_KEY)
missing=()
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    missing+=("$name")
  fi
done

if (( ${#missing[@]} )); then
  echo "ERROR: Missing required environment variables:"
  printf '  %s\n' "${missing[@]}"
  exit 1
fi

MCP_PID=""
if [[ "${FRIDAY_MCP_ENABLED:-true}" =~ ^(1|true|yes|on)$ ]]; then
  echo "Starting FRIDAY MCP capability server..."
  python -m friday_agent.mcp_server >/tmp/friday-mcp.log 2>&1 &
  MCP_PID=$!
  trap 'if [[ -n "${MCP_PID:-}" ]]; then kill "$MCP_PID" 2>/dev/null || true; fi' EXIT
  sleep 1
fi

echo ""
echo "=============================================="
echo "        FRIDAY AI — LIVEKIT + MCP             "
echo "=============================================="
echo "Realtime voice agent and capability server online."
echo ""

exec python -m friday_agent.livekit_agent dev
