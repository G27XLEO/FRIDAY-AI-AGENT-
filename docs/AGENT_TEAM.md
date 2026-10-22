# FRIDAY Agent Team (free local MVP)

An optional multi-agent workspace in the existing FRIDAY React UI and FastAPI service.
It does not require LiveKit, ElevenLabs, paid subscriptions or cloud API keys.

## What works

- Six built-in specialists plus custom agents (up to 12).
- Group conversation with an auto-router or up to three selected specialists.
- Parallel specialist responses, then a FRIDAY coordinator synthesis.
- SQLite-backed conversation history and agent instructions.
- A protected API and a React interface with agent roster, threads and messages.

**Not included:** autonomous browser/computer operations, background jobs, web research,
app sign-ins, workflow recording, fact verification, voice/audio or full Grok Bot parity.
Agents generate *proposals* and do not run shell commands or interact with third-party
accounts. Replies should never be treated as evidence of completed work.

## Run on a computer / Linux host

Install [Ollama](https://ollama.com) and pull a local model:

\`\`\`bash
ollama pull llama3.2
ollama serve
\`\`\`

In a separate terminal from the repository root:

\`\`\`bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn httpx
export FRIDAY_TEAM_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export FRIDAY_OLLAMA_MODEL=llama3.2
python -m uvicorn friday_agent.web_server:app --host 127.0.0.1 --port 8001
\`\`\`

Keep the printed/configured token somewhere private in that session. For subsequent
restarts, use the same token or create a new one and reconnect the UI.

Start the React development UI in a third terminal:

\`\`\`bash
cd web
npm install
npm run dev
\`\`\`

Open http://localhost:3000, choose **Agent Team**, and enter the
FRIDAY_TEAM_API_TOKEN. Vite proxies only /api/team to the local FastAPI service.

### Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| FRIDAY_TEAM_API_TOKEN | unset | Required Bearer token for private chat/agent APIs |
| FRIDAY_TEAM_DB | .friday/team.sqlite3 | SQLite conversations and roles |
| FRIDAY_OLLAMA_URL | http://127.0.0.1:11434 | Trusted Ollama server address |
| FRIDAY_OLLAMA_MODEL | llama3.2 | Locally downloaded chat model |

Ollama itself is free to run locally, but needs enough RAM/CPU and electricity;
there is no guaranteed free 24/7 hosting. A phone can access a running desktop/
server interface over a secure tunnel or trusted network. Native Ollama inference
on ordinary Android/Termux devices is not assumed.

### Security

Keep Ollama bound to localhost, use a long random FRIDAY_TEAM_API_TOKEN,
do not publish the API directly to the internet, and terminate TLS/auth in a
trusted reverse proxy if remote access is required. The browser keeps the
token in sessionStorage for the current tab, not as a permanent account login.
This MVP is **single-user**, not a multi-tenant team service.

If a full FRIDAY backend environment is already installed, no new Python
dependencies are required. Run the focused tests with:

\`\`\`bash
python -m pytest -q tests/test_team_api.py
\`\`\`
