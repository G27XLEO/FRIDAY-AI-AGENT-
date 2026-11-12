#!/usr/bin/env bash
# Install the voice worker locally; never overwrite an existing configuration.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
umask 077
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m livekit.agents download-files
if [[ ! -e .env ]]; then
  cp .env.example .env
  echo "Created .env. Add your LiveKit, Groq and ElevenLabs credentials there."
fi
echo "Dependencies installed. Checking configuration (no network calls)..."
python -m friday_agent.doctor
