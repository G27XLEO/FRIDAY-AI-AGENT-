# FRIDAY AI Agent

A production-oriented realtime voice agent built around **LiveKit Agents**, **Groq**, **ElevenLabs**, **Silero VAD**, turn detection, and a custom **MCP server**.

FRIDAY is designed as a mission-control style assistant: concise, proactive, technically precise, calm under pressure, and suitable for voice-first operation.

> **Security:** Never commit API keys, LiveKit credentials, OAuth tokens, or other secrets. Use `.env` locally and GitHub Actions Secrets for CI/CD.

## Current status

- **Runtime:** LiveKit voice worker
- **AI:** Groq STT + LLM
- **Voice:** ElevenLabs TTS
- **Audio:** Silero VAD + turn detection
- **Tools:** Custom MCP server with workspace, command, URL, memory, status, and planning tools
- **Container:** Docker / Python 3.12
- **CI:** GitHub Actions builds and validates the worker image
- **Android app:** Not included; this repository intentionally deploys the LiveKit worker
- **Publishing:** Release/deployment is intentionally a separate later step

## Architecture

```text
Voice Client
     │
     ▼
  LiveKit Cloud
     │
     ▼
FRIDAY LiveKit Worker
     ├── Groq STT ──────────► speech recognition
     ├── Groq LLM ──────────► reasoning / responses
     ├── Silero VAD ────────► voice activity detection
     ├── Turn Detector ─────► conversation turn handling
     ├── ElevenLabs TTS ────► voice output
     │
     └── MCP Server
          ├── system status
          ├── URL fetching
          ├── safe shell commands
          ├── workspace files
          ├── memory
          └── task planning
```

## Features

### Realtime voice agent

`friday_agent/livekit_agent.py` runs the realtime worker and connects the LiveKit audio pipeline to Groq and ElevenLabs.

### MCP automation layer

`friday_agent/mcp_server.py` exposes FRIDAY tools through streamable HTTP. The tool layer includes:

| Capability | MCP tool/resource | Purpose |
| --- | --- | --- |
| Runtime status | `system_status`, `friday://status` | Runtime/platform information |
| URL access | `fetch_url` | Fetch public URLs with limits |
| Shell | `run_shell` | Execute only allow-listed commands |
| Files | `read_workspace_file`, `write_workspace_file`, `list_workspace_files` | Workspace-scoped UTF-8 file operations |
| Memory | `remember`, `recall` | Small persistent JSON facts |
| Planning | `plan_task` | Compact execution plans |
| Operator prompt | `friday_operator_prompt` | Standardized mission prompt |

### God's Eye View integration

The optional `FRIDAY_GODS_EYE_VIEW_URL` setting can point FRIDAY at a deployed God's Eye View web console. The integration is optional and should not prevent the core voice worker from starting.

## Repository layout

```text
.
├── .github/workflows/friday-build.yml  # CI validation
├── docs/                               # Architecture, deployment and release docs
├── friday_agent/
│   ├── livekit_agent.py                # Realtime voice worker
│   ├── mcp_server.py                   # MCP HTTP server
│   └── mcp_tools.py                    # Tool implementations
├── scripts/
│   └── run_background.sh               # Local background runner
├── tests/                              # Unit/environment tests
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Environment configuration

Copy `.env.example` to `.env` and fill in your own credentials.

### Required

| Variable | Purpose |
| --- | --- |
| `LIVEKIT_URL` | LiveKit WebSocket URL |
| `LIVEKIT_API_KEY` | LiveKit worker API key |
| `LIVEKIT_API_SECRET` | LiveKit worker API secret |
| `GROQ_API_KEY` | Groq API access |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS access |

### Model and voice configuration

| Variable | Purpose |
| --- | --- |
| `GROQ_LLM_MODEL` | Groq LLM model name |
| `GROQ_STT_MODEL` | Groq speech-to-text model name |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice ID |
| `ELEVENLABS_VOICE_LINK` | Optional shared ElevenLabs voice URL |

### Optional runtime controls

| Variable | Default | Purpose |
| --- | --- | --- |
| `FRIDAY_IDENTITY` | `friday-ai-agent` | Agent identity |
| `FRIDAY_INSTRUCTIONS` | FRIDAY default prompt | Agent behavior |
| `FRIDAY_WORKSPACE_ROOT` | Current directory | MCP workspace boundary |
| `FRIDAY_MEMORY_PATH` | `.run/memory.json` | Memory storage |
| `FRIDAY_ALLOWED_COMMANDS` | `pwd,python,python3,git,find,rg,cat` | Shell allow-list |
| `FRIDAY_MAX_TEXT_CHARS` | `6000` | Output size limit |
| `FRIDAY_MAX_WRITE_BYTES` | `1000000` | File-write size limit |
| `FRIDAY_GODS_EYE_VIEW_URL` | Empty | Optional web console |

## Local setup

Python 3.12 is the project target.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials.
set -a && source .env && set +a
```

### Start the MCP server

```bash
python -m friday_agent.mcp_server
```

### Start the LiveKit worker

```bash
python -m friday_agent.livekit_agent dev
```

### Start both locally

```bash
./scripts/run_background.sh
```

The runner stores runtime logs and PIDs under `.run/`.

## Docker deployment

The Docker image uses Python 3.12, installs the LiveKit dependencies, downloads required LiveKit model files during image build, compiles the application, and runs as a non-root `friday` user.

Build:

```bash
docker build --pull -t friday-ai-agent .
```

Run with an environment file:

```bash
docker run --rm --env-file .env friday-ai-agent
```

For production, inject secrets through the hosting platform's secret manager rather than baking them into an image.

## GitHub Actions / CI

`.github/workflows/friday-build.yml` runs on pushes to `main` and pull requests. It:

1. Checks out the repository.
2. Builds the Docker image.
3. Inspects the image.
4. Runs the unit-test suite inside the image.
5. Runs protected runtime environment validation when the required GitHub Secrets are configured.

Required GitHub Actions Secrets:

```text
LIVEKIT_URL
LIVEKIT_API_KEY
LIVEKIT_API_SECRET
GROQ_API_KEY
ELEVENLABS_API_KEY
```

Do not place secret values in workflow YAML or committed files.

## Testing

Run the local checks before deployment:

```bash
python -m unittest discover -v
python -m compileall friday_agent tests
git diff --check
docker build --pull -t friday-ai-agent .
```

## Security model

FRIDAY's MCP shell access is intentionally allow-listed. File operations are constrained to the configured workspace root, and output/write limits reduce accidental resource consumption.

For production:

- Store secrets in a secret manager.
- Rotate credentials if they were ever committed or exposed.
- Keep the shell allow-list minimal.
- Use a dedicated workspace for MCP operations.
- Run the container as a non-root user.
- Restrict network access where practical.
- Do not expose the MCP endpoint publicly without authentication and transport controls.

## Termux / Android development

The project can be developed from Termux, but the runtime architecture is **server/worker-first**. The repository does not build an Android application. A phone can act as the development/operator environment while the LiveKit worker runs in Docker or another supported server environment.

See `docs/DEPLOYMENT.md` for the recommended development and production paths.

## Publishing and release plan

Publishing is intentionally **not performed as part of this documentation update**.

When FRIDAY is ready to publish, the recommended sequence is:

1. Verify secrets are absent from tracked files and repository history where applicable.
2. Run unit, compile, Docker, and environment validation checks.
3. Build and tag an immutable container image.
4. Push the image to the selected container registry.
5. Configure production secrets in the deployment platform.
6. Deploy the LiveKit worker.
7. Verify LiveKit connectivity, STT, LLM, TTS, MCP tools, logs, and health.
8. Create a versioned GitHub release and changelog.
9. Publish only after the production smoke test passes.

See `docs/RELEASE.md` for the release checklist.

## Roadmap

### Near term

- Harden MCP authentication and authorization.
- Improve runtime health/status reporting.
- Add stronger environment validation and startup diagnostics.
- Improve voice latency and audio reliability.
- Expand automated CI coverage.

### Mid term

- Production container registry workflow.
- Automated versioning and release artifacts.
- More connector/tool integrations through MCP.
- Better memory and task-state management.
- God's Eye View production integration.

### Long term

- Universal connector/tool registry.
- Permission-aware automation layer.
- Multi-service orchestration.
- Reliable background tasks and event-driven automation.
- Production-grade observability and audit trails.

## License / usage

Review the repository's license and third-party service terms before public distribution. Use only voices, credentials, models, and integrations that you are authorized to use.
