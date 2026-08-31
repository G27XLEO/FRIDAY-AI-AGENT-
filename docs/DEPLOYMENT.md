# FRIDAY Deployment Guide

## Scope

FRIDAY is a software-only realtime voice assistant. It does not require or include Raspberry Pi, GPIO, microcontrollers, sensors, MQTT home automation, Bluetooth/BLE device control, or other physical hardware integrations.

The supplied JARVIS-style reference separates hardware/IoT from the main voice-assistant software pipeline. FRIDAY intentionally does not implement that optional hardware layer. fileciteturn0file0L72-L83

## 1. Development

Recommended local sequence:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill .env with your own credentials
set -a && source .env && set +a
python -m unittest discover -v
```

Run the worker:

```bash
python -m friday_agent.livekit_agent dev
```

Run the MCP server separately when tool access is required:

```bash
python -m friday_agent.mcp_server
```

## 2. Docker

Build the worker image:

```bash
docker build --pull -t friday-ai-agent:local .
```

Run locally:

```bash
docker run --rm --env-file .env friday-ai-agent:local
```

The Dockerfile targets Python 3.12 and runs the final process as a non-root `friday` user.

## 3. GitHub Actions

The repository workflow builds the Docker image and runs the unit suite. Runtime validation is enabled when all required secrets are present.

Configure these GitHub Actions Secrets:

```text
LIVEKIT_URL
LIVEKIT_API_KEY
LIVEKIT_API_SECRET
GROQ_API_KEY
ELEVENLABS_API_KEY
```

Do not use `.env` as a CI secret store.

## 4. Production deployment

A production deployment should use a container registry and a managed container/server platform capable of running a long-lived LiveKit worker.

Generic sequence:

```text
GitHub main
   │
   ▼
CI tests + Docker build
   │
   ▼
Container registry
   │
   ▼
Production runtime
   │
   ├── inject secrets
   ├── start FRIDAY worker
   ├── monitor logs/health
   └── verify LiveKit session
```

Keep the image immutable and deploy by version/digest rather than relying only on a mutable `latest` tag.

## 5. Production checks

Before accepting traffic, verify:

- LiveKit worker registers successfully.
- Agent joins a test room.
- Speech-to-text returns usable transcripts.
- LLM responses are generated.
- ElevenLabs audio is returned clearly.
- VAD and turn detection behave correctly.
- MCP tools are reachable only through the intended security boundary.
- File operations cannot escape the workspace root.
- Shell execution is restricted to the allow-list.
- Logs contain no API keys or secrets.
- Container runs without root privileges.
- No physical hardware is required for the deployment.

## 6. Termux / Android

Termux is suitable for source control, development, testing, and operator-side work. It is not required to be the production host.

Typical development flow:

```bash
git clone <repository>
cd FRIDAY-AI-AGENT-
python --version
pip install -r requirements.txt
cp .env.example .env
```

For production, move the worker to a supported server/container environment and use the Android device as the voice/operator client where appropriate. The Android device is a software endpoint, not a required home-control hub.

## 7. Secrets incident response

If a credential is ever committed:

1. Revoke or rotate the affected credential immediately.
2. Replace the value in local/CI secret stores.
3. Remove the secret from tracked files.
4. Review repository history and logs.
5. Check for unauthorized use.
6. Re-run security and deployment validation.

Removing a secret from the current file does not by itself remove it from Git history.
