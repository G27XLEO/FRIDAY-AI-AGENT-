#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ -x .venv/bin/python ]]; then
  source .venv/bin/activate
fi

# Reuse the Codespace environment prepared by .devcontainer/setup.sh.
if ! python -c 'import livekit.agents' >/dev/null 2>&1; then
  echo "FRIDAY dependencies are not installed. Installing now..."
  python -m pip install -r requirements.txt
  python -m livekit.agents download-files
fi

python -m friday_agent.doctor

echo ""
echo "=============================================="
echo "        FRIDAY AI — LIVEKIT WORKER           "
echo "=============================================="
echo "Starting realtime voice agent..."
echo "Press Ctrl+C to stop."
echo ""

exec python -m friday_agent.livekit_agent dev
