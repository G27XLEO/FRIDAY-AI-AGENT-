#!/usr/bin/env bash
set -euo pipefail

# Make the one-command launcher executable inside the Codespace.
chmod +x .devcontainer/setup.sh start-friday.sh 2>/dev/null || true

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

ONE-COMMAND START:
  ./start-friday.sh

Dashboard:
  python -m friday_agent.web_server

Tests:
  python -m unittest discover -s tests -p 'test_*.py' -v

Configure these Codespaces secrets/environment variables before starting FRIDAY:
LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, GROQ_API_KEY, ELEVENLABS_API_KEY
EOF
