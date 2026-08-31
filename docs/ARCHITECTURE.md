# FRIDAY Architecture

## Overview

FRIDAY is a realtime, voice-first AI worker. LiveKit handles realtime media transport; the FRIDAY worker coordinates speech recognition, reasoning, voice synthesis, turn detection, and MCP-based software tools.

The architecture follows the software layers in the JARVIS-style setup reference: Python/core libraries, speech recognition, language understanding, LLM reasoning, TTS, API serving, and real-time orchestration. Hardware/IoT is explicitly excluded from the FRIDAY core.

```text
┌──────────────────────────────┐
│   Software Clients           │
│ Web / Android / iOS /        │
│ Desktop / Termux / CLI       │
└──────────────┬───────────────┘
               │ LiveKit / HTTP
               ▼
┌──────────────────────────────┐
│ Realtime + API               │
│ LiveKit + FastAPI/Uvicorn    │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│      FRIDAY Agent Worker     │
│                              │
│ VAD → Turn Detection → STT   │
│                 ↓            │
│                LLM            │
│                 ↓            │
│                TTS            │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│      FRIDAY MCP Layer        │
│ files / safe shell / URL /   │
│ memory / status / planning   │
└──────────────────────────────┘

        HARDWARE / IoT: NOT INCLUDED
```

## Components

### Python runtime

Python is the core implementation language for the worker, MCP server, configuration, tests, and supporting services.

### LiveKit worker

`friday_agent/livekit_agent.py` is the runtime entry point for the voice agent. It joins LiveKit rooms and processes realtime audio.

### Groq

Groq provides the configured speech-to-text and language-model intelligence through the LiveKit plugins.

### Language understanding

FRIDAY uses an LLM-first approach rather than requiring a separate NLP service. The reference guide notes that a separate NLP stage can be skipped for a simple assistant when the LLM handles understanding directly. fileciteturn0file0L44-L51

### ElevenLabs

ElevenLabs provides text-to-speech output. The voice is configured by environment variables so credentials and voice selection remain deployment-specific.

### Silero VAD and turn detection

VAD determines when meaningful speech is present. Turn detection helps determine when the operator has finished speaking so FRIDAY can respond naturally.

### FastAPI / API serving

The API layer exposes software-side assistant functionality to clients over HTTP/ASGI. The reference guide identifies FastAPI as the service layer for an STT → LLM → TTS pipeline. fileciteturn0file0L67-L71

### MCP server

`friday_agent/mcp_server.py` exposes a streamable HTTP MCP server. `mcp_tools.py` contains the tool implementation layer.

The tool layer is intentionally constrained:

- File access stays inside the configured workspace root.
- Shell execution uses an explicit command allow-list.
- URL responses are clipped.
- File writes have a maximum byte limit.
- Memory is stored as bounded JSON state.

## Data flow

1. Operator speaks through a software LiveKit client.
2. LiveKit transports the audio to the FRIDAY worker.
3. VAD and turn detection identify usable speech and conversation boundaries.
4. Groq STT converts speech to text.
5. FRIDAY's LLM receives the operator request and available context.
6. If needed, the agent uses an MCP software tool.
7. The resulting response is synthesized by ElevenLabs.
8. Audio is returned through LiveKit to the software client.

## Deployment boundary

The repository is intentionally software-only. Android UI/application code is outside this runtime repository. A mobile device can be the operator/development endpoint while the worker is deployed as a Docker container or Linux/Python service.

**There is no Raspberry Pi integration, GPIO layer, microcontroller layer, sensor layer, MQTT home-control layer, or other physical-device dependency in the FRIDAY core.**

The reference guide lists hardware/IoT as an optional seventh layer, but FRIDAY deliberately ends its core architecture at the software/runtime layer. fileciteturn0file0L72-L83

## Security boundary

Treat MCP tools as privileged capabilities. Production deployments should add authentication, authorization, network restrictions, logging, and auditing before exposing the MCP server beyond a trusted network.

Never commit service credentials. GitHub Actions receives production credentials through repository/environment Secrets.

## Reference build order

FRIDAY follows this software-oriented sequence from the supplied setup reference:

1. Python/core environment.
2. Speech recognition (STT).
3. LLM-based language understanding.
4. LLM reasoning and tool calls.
5. TTS.
6. FastAPI/API serving.
7. MCP tool/action layer.
8. LiveKit/asyncio real-time orchestration.

The reference guide describes this progression and identifies LiveKit/Python asyncio as a suitable real-time runtime. fileciteturn0file0L85-L94
