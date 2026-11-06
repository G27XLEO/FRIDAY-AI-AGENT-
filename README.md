# FRIDAY AI Agent

A production-oriented realtime voice-first AI assistant built around **LiveKit Agents**, **Groq**, **ElevenLabs**, **Silero VAD**, turn detection, **FastAPI**, and a custom **MCP server**.

FRIDAY is a cross-platform mission-control assistant: concise, proactive, technically precise, calm under pressure, and suitable for local development or server deployment.

> **Scope:** FRIDAY is a software-only assistant. This repository does **not** add Raspberry Pi, GPIO, microcontrollers, sensors, smart-home, MQTT, Bluetooth/BLE, or other hardware/IoT control.

> **Security:** Never commit API keys, LiveKit credentials, OAuth tokens, or other secrets. Use `.env` locally and GitHub Actions Secrets for CI/CD.

## Current status

- **Runtime:** LiveKit realtime voice worker + optional MCP server
- **AI / STT:** Groq speech recognition
- **Reasoning:** Groq LLM
- **Voice:** ElevenLabs TTS
- **Audio:** Silero VAD + turn detection
- **API:** FastAPI/ASGI support through the existing web server
- **Tools:** Custom MCP server with workspace, command, URL, memory, status, and planning tools
- **Container:** Docker / Python 3.12
- **Development hosts:** Linux, macOS, Windows, WSL2, and Android/Termux
- **Server deployment:** Docker or a supported Linux/Python host
- **CI:** GitHub Actions builds and validates the worker image
- **Clients:** Web, Android, iOS, desktop, terminal/CLI clients can act as software endpoints through LiveKit or the API
- **Hardware/IoT:** **Intentionally out of scope**

## Reference architecture

The uploaded JARVIS-style setup guide describes the assistant as a layered software pipeline: language/core libraries → speech recognition → language understanding → reasoning → speech synthesis → API service → real-time runtime. It also lists hardware/IoT as an optional extension; FRIDAY deliberately stops before that extension and remains software-only.

```text
┌──────────────────────────────────────────────────────────────┐
│                    FRIDAY SOFTWARE CLIENTS                   │
│       Web │ Android │ iOS │ Desktop │ Termux │ CLI           │
└──────────────────────────────┬───────────────────────────────┘
                               │ LiveKit / API
                               ▼
                    ┌──────────────────────┐
                    │ Realtime / API Layer │
                    │ LiveKit + FastAPI    │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │   FRIDAY Worker      │
                    ├──────────────────────┤
                    │ Silero VAD           │
                    │ Turn Detection       │
                    │ Groq STT             │
                    │ Groq LLM             │
                    │ ElevenLabs TTS       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    FRIDAY MCP        │
                    ├──────────────────────┤
                    │ Status / URL         │
                    │ Safe shell           │
                    │ Workspace files      │
                    │ Memory               │
                    │ Planning             │
                    └──────────────────────┘

             NO HARDWARE / NO HOME-IOT LAYER
```

## Software stack

| Layer | FRIDAY implementation | Purpose |
| --- | --- | --- |
| Language & core | Python | Application glue and runtime |
| Speech-to-text | Groq STT | Converts voice to text |
| Language understanding | LLM-first routing | Intent and context understanding without a mandatory separate NLP service |
| Reasoning | Groq LLM | Answers, plans, decisions, tool calls |
| Text-to-speech | ElevenLabs | Natural spoken responses |
| API | FastAPI / Uvicorn | HTTP/WebSocket service access |
| Tool/action layer | MCP | Controlled software actions |
| Real-time runtime | LiveKit + Python asyncio | Audio streaming, sessions, concurrency |
| Deployment | Docker | Reproducible server runtime |

The reference guide notes that a separate NLP stage can be skipped for a simple assistant when the LLM handles understanding directly; FRIDAY follows that simpler LLM-first approach. fileciteturn0file0L44-L51

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

### API layer

The repository includes a web server for exposing software-side assistant functionality over HTTP/ASGI. The reference guide identifies FastAPI as the service layer for exposing an STT → LLM → TTS pipeline to software clients. fileciteturn0file0L67-L71

## Cross-platform support

FRIDAY is a **Python/LiveKit worker**, so the development/client environment can be separated from the production worker.

| Platform | Development | Worker | Recommended path |
| --- | --- | --- | --- |
| Linux | ✅ | ✅ | Python or Docker |
| macOS | ✅ | ✅ | Python or Docker |
| Windows | ✅ | ⚠️ | WSL2 or Docker recommended |
| WSL2 | ✅ | ✅ | Python or Docker |
| Android / Termux | ✅ | ⚠️ | Termux for development; Docker/server for worker |
| Web | Client | N/A | LiveKit web client / API |
| iOS | Client | N/A | LiveKit client / API |
| Docker hosts | N/A | ✅ | Recommended production runtime |

The table distinguishes **development/host support** from **software client support**. The core repository is not a native Android/iOS application and does not require physical hardware.

## Repository layout

```text
.
├── .github/workflows/friday-build.yml  # CI validation
├── docs/
│   ├── ARCHITECTURE.md                # System architecture
│   ├── DEPLOYMENT.md                  # Deployment paths
│   ├── INSTALL.md                     # Platform install commands
│   ├── RELEASE.md                     # Future publishing/release process
│   ├── UI_DEMO.md                     # UI review notes
│   └── assets/friday-ui-demo.svg      # Static UI demo snapshot
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

## Install on supported development platforms

The complete platform command reference is in `docs/INSTALL.md`.

### Linux / macOS / WSL2

```bash
git clone https://github.com/G27XLEO/FRIDAY-AI-AGENT-.git
cd FRIDAY-AI-AGENT-
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

### Windows PowerShell

```powershell
git clone https://github.com/G27XLEO/FRIDAY-AI-AGENT-.git
Set-Location FRIDAY-AI-AGENT-
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### Android / Termux

```bash
pkg update -y
pkg install -y git python
pkg install -y clang make pkg-config

git clone https://github.com/G27XLEO/FRIDAY-AI-AGENT-.git
cd FRIDAY-AI-AGENT-
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

If a native Python dependency is unavailable on a particular Android/Termux build, use Termux as the control/development environment and run the LiveKit worker in Docker or on a Linux server. No Raspberry Pi or other physical device is required.

## Start FRIDAY

### MCP server

```bash
python -m friday_agent.mcp_server
```

### LiveKit worker

```bash
python -m friday_agent.livekit_agent dev
```

### Both locally

```bash
./scripts/run_background.sh
```

The runner stores runtime logs and PIDs under `.run/`.

## Docker

Build:

```bash
docker build --pull -t friday-ai-agent .
```

Run:

```bash
docker run --rm --env-file .env friday-ai-agent
```

For production, inject secrets through the hosting platform's secret manager rather than baking them into an image.

## GitHub Actions / CI

`.github/workflows/friday-build.yml` runs on pushes to `main` and pull requests. It builds the Docker image, inspects it, runs the unit tests inside the image, and performs protected runtime environment validation when GitHub Secrets are configured.

Required GitHub Actions Secrets:

```text
LIVEKIT_URL
LIVEKIT_API_KEY
LIVEKIT_API_SECRET
GROQ_API_KEY
ELEVENLABS_API_KEY
```

## Testing

```bash
python -m unittest discover -v
python -m compileall friday_agent tests
git diff --check
docker build --pull -t friday-ai-agent .
```

## Security

- Never commit secrets.
- Rotate credentials that were previously exposed.
- Keep MCP shell access allow-listed.
- Keep file operations inside a trusted workspace.
- Run production containers as non-root.
- Protect any publicly exposed MCP endpoint with authentication and transport controls.
- Treat voice credentials and third-party service tokens as production secrets.
- Do not add physical-device credentials or home-IoT control paths to the software-only core.

## Publishing later

Publishing is **not performed by this update**. When ready, use the release gates in `docs/RELEASE.md`: security review → tests → immutable container build → registry push → production secrets → deployment → smoke test → versioned GitHub release.

## Roadmap

- Harden MCP authentication and authorization.
- Improve health/status reporting and startup diagnostics.
- Reduce voice latency and improve audio reliability.
- Add more software MCP connectors and permission-aware automation.
- Improve FastAPI/WebSocket client integration.
- Add production container registry and release automation.
- Expand client integrations for web, Android, iOS, desktop, and terminal workflows.
- Add production observability, audit trails, and task-state management.
- **No hardware/IoT roadmap item is planned for the core FRIDAY repository.**

## Reference source

The uploaded JARVIS-style setup guide identifies Python, STT, NLP/LLM understanding, an LLM reasoning engine, TTS, FastAPI, and a real-time runtime as the main software layers. It describes hardware/IoT separately as an optional extension; FRIDAY intentionally does not implement that extension. fileciteturn0file0L2-L20 fileciteturn0file0L72-L94

## License / usage

Review the repository license and third-party service terms before public distribution. Use only voices, credentials, models, and integrations that you are authorized to use.


## Astra architecture upgrade

The current architecture is optimized as a JARVIS-style software assistant while keeping the project name FRIDAY. It adds three latency-focused layers:

Voice/API client -> LiveKit realtime worker -> lightweight NLP router -> Groq reasoning -> first-class MCP tool loop -> ElevenLabs speech.

The NLP layer uses deterministic intent, urgency and entity extraction before the LLM turn. The MCP layer reuses a pooled async HTTP client, with configurable connection limits and timeouts, while retaining workspace boundaries, command allow-listing and bounded outputs.

### NLP vs. NCP

The assistant uses **NLP (Natural Language Processing)** as the fast pre-processing layer. No heavyweight NLP model is loaded into the realtime audio path.

### Fast MCP controls

`FRIDAY_HTTP_MAX_CONNECTIONS`, `FRIDAY_HTTP_MAX_KEEPALIVE`, and `FRIDAY_HTTP_TIMEOUT` control the pooled HTTP client used by MCP URL tools. `FRIDAY_MCP_URL` enables first-class LiveKit MCP tool calling, while `FRIDAY_MCP_AUTH_TOKEN`, `FRIDAY_MCP_TIMEOUT_SECONDS`, `FRIDAY_MAX_TOOL_STEPS`, and `FRIDAY_MAX_TOOL_RESULT_CHARS` control authentication, latency, tool-loop depth, and context size.

## JARVIS-style agentic runtime

FRIDAY now connects the realtime LiveKit agent directly to the repository's MCP server through LiveKit's first-class MCP toolset. When `FRIDAY_MCP_URL` is configured, the LLM can discover and invoke the server's software tools during a voice conversation instead of treating MCP as a separate service.

```text
Voice
  ↓
LiveKit realtime session
  ↓
Fast deterministic NLP context
  ↓
Groq reasoning
  ↓
MCP tool loop ──→ status / web / files / memory / planning / safe shell
  ↓
ElevenLabs voice response
```

The tool loop is bounded by `FRIDAY_MAX_TOOL_STEPS`, MCP calls have a configurable timeout, and large results are truncated before entering the voice model context. MCP remains optional so the voice worker can still start when the MCP server is unavailable. LiveKit documents MCPToolset/MCPServerHTTP as the native Python integration for exposing MCP tools to an agent. citeturn2view0

### Enable the FRIDAY MCP brain

Add to `.env`:

```text
FRIDAY_MCP_URL=http://127.0.0.1:8000/mcp
FRIDAY_MCP_TIMEOUT_SECONDS=20
FRIDAY_MAX_TOOL_STEPS=5
FRIDAY_MAX_TOOL_RESULT_CHARS=4000
# Optional:
# FRIDAY_MCP_AUTH_TOKEN=...
```

Start the MCP server first:

```bash
python -m friday_agent.mcp_server
```

Then start the LiveKit worker:

```bash
python -m friday_agent.livekit_agent dev
```

For production, place MCP behind authenticated HTTPS rather than exposing an unauthenticated local-style endpoint.
