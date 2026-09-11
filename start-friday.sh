#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

# Reuse the Codespace environment prepared by .devcontainer/setup.sh.
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
  echo "ERROR: Missing required Codespaces secrets/environment variables:"
  printf '  %s\n' "${missing[@]}"
  echo
  echo "Add them in GitHub Codespaces Secrets, then recreate/restart the Codespace."
  exit 1
fi

echo ""
echo "=============================================="
echo "        FRIDAY AI — LIVEKIT WORKER           "
echo "=============================================="
echo "Starting realtime voice agent..."
echo "Press Ctrl+C to stop."
echo ""

exec python -m friday_agent.livekit_agent dev
