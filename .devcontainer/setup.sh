#!/usr/bin/env bash
set -euo pipefail

python -m pip install --user -r requirements.txt
python -m livekit.agents download-files

if [ -f web/package.json ]; then
  cd web
  npm install
  npm run build
  cd ..
fi

cat <<'EOF'

FRIDAY Codespace is ready.

Dashboard:  python -m friday_agent.web_server
Worker:     python -m friday_agent.livekit_agent start
Tests:      python -m unittest discover -s tests -p 'test_*.py' -v

Configure these Codespaces secrets/environment variables before starting the LiveKit worker:
LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, GROQ_API_KEY, ELEVENLABS_API_KEY
EOF
