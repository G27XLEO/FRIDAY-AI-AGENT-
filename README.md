# FRIDAY AI Agent

A realtime LiveKit voice agent powered by Groq for speech/model intelligence, ElevenLabs for voice output, and a custom MCP server for operator tools.

This project is inspired by a polished mission-control assistant style: concise, proactive, technically capable, and calm. It does **not** clone a copyrighted character or a real performer's voice. Use a licensed ElevenLabs voice that you own or are allowed to use.

## Features

- **Realtime voice agent**: `friday_agent/livekit_agent.py` joins LiveKit rooms with Groq STT/LLM, ElevenLabs TTS, Silero VAD, and turn detection.
- **Custom MCP server**: `friday_agent/mcp_server.py` exposes FRIDAY tools, a status resource, and an operator prompt over streamable HTTP.
- **Safe tool core**: `friday_agent/mcp_tools.py` provides workspace-limited file access, allow-listed shell commands, URL fetching, memory, status, and planning helpers.
- **Background runner**: `scripts/run_background.sh` starts the MCP server and LiveKit worker, then stores logs and process IDs under `.run/`.
- **Container support**: `Dockerfile` builds a deployable LiveKit worker image.

## Required environment

Copy `.env.example` to `.env` and fill in only these service values:

| Variable | Required | Description |
| --- | --- | --- |
| `LIVEKIT_URL` | Yes | Your LiveKit Cloud or self-hosted WebSocket URL. |
| `LIVEKIT_API_KEY` | Yes | LiveKit API key for the agent worker. |
| `LIVEKIT_API_SECRET` | Yes | LiveKit API secret for the agent worker. |
| `GROQ_API_KEY` | Yes | Groq API key used by speech-to-text and LLM plugins. |
| `ELEVENLABS_API_KEY` | Yes | ElevenLabs API key used for text-to-speech. |
| `ELEVENLABS_VOICE_LINK` | Recommended | ElevenLabs voice-library/share URL containing `voiceId=...`. |

`ELEVENLABS_VOICE_ID` is still accepted for compatibility if you prefer to provide the raw voice ID directly, but the example file uses `ELEVENLABS_VOICE_LINK`.

## LiveKit-only deployment

This repository is intentionally **LiveKit worker-only**. The Android application and Android CI build have been removed. The deployable runtime is the LiveKit voice agent in `friday_agent/livekit_agent.py`, with Docker and GitHub Actions support.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your LiveKit, Groq, and ElevenLabs values.
set -a && source .env && set +a
./scripts/run_background.sh
```

The background runner writes:

- `.run/mcp.log` and `.run/mcp.pid` for the MCP server.
- `.run/livekit.log` and `.run/livekit.pid` for the LiveKit worker.

## Run components manually

Start only the MCP server:

```bash
python -m friday_agent.mcp_server
```

Start only the LiveKit voice worker:

```bash
python -m friday_agent.livekit_agent dev
```

## Custom MCP server capabilities

The MCP server provides these capabilities:

| Capability | MCP name | Purpose |
| --- | --- | --- |
| Runtime status | `system_status`, `friday://status` | Inspect UTC time, platform, Python version, workspace, and memory path. |
| Live context | `fetch_url` | Fetch a public URL with timeout and clipped output. |
| Workspace commands | `run_shell` | Execute only commands allowed by `FRIDAY_ALLOWED_COMMANDS`. |
| Workspace files | `read_workspace_file`, `write_workspace_file`, `list_workspace_files` | Read, write, and list UTF-8 files without path traversal outside `FRIDAY_WORKSPACE_ROOT`. |
| Memory | `remember`, `recall` | Store and retrieve small JSON-serializable facts in `.run/memory.json` by default. |
| Planning | `plan_task` | Produce a compact execution plan for an operator goal. |
| Prompting | `friday_operator_prompt` | Generate a standard mission prompt for MCP clients. |

## Optional advanced MCP settings

These are intentionally not included in `.env.example` because you asked to keep it limited to LiveKit, Groq, and ElevenLabs. They are still available for deployments that need more control:

| Variable | Default | Purpose |
| --- | --- | --- |
| `FRIDAY_WORKSPACE_ROOT` | Current working directory | Root directory MCP file tools are allowed to access. |
| `FRIDAY_MEMORY_PATH` | `.run/memory.json` | JSON file used by the memory tools. |
| `FRIDAY_ALLOWED_COMMANDS` | `pwd,python,python3,git,find,rg,cat` | Comma-separated command allow-list for `run_shell`. |
| `FRIDAY_MAX_TEXT_CHARS` | `6000` | Maximum text returned by URL, shell, and file tools. |
| `FRIDAY_MAX_WRITE_BYTES` | `1000000` | Maximum size (in bytes) `write_workspace_file` will accept. |

## Test

```bash
python -m unittest discover -v
python -m compileall friday_agent tests
git diff --check

docker build -t friday-ai-agent .
```

## Notes

- Python 3.10+ is required by LiveKit Agents; this project targets Python 3.12.
- Keep shell access limited to trusted deployments. Even allow-listed command execution should only run in trusted workspaces.
- Keep API keys out of git. `.env` is ignored; `.env.example` contains placeholders only.
