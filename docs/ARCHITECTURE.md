# FRIDAY Architecture

## Overview

FRIDAY is a realtime, voice-first AI worker. LiveKit handles realtime media transport; the FRIDAY worker coordinates speech recognition, reasoning, voice synthesis, turn detection, and MCP-based operator tools.

```text
┌─────────────────────┐
│ Voice / LiveKit App │
└──────────┬──────────┘
           │ realtime audio
           ▼
┌────────────────────────────┐
│     LiveKit Cloud / SFU    │
└────────────┬───────────────┘
             ▼
┌────────────────────────────┐
│     FRIDAY Agent Worker    │
│                            │
│  VAD → STT → LLM → TTS     │
│       │          │         │
│       └────┬─────┘         │
│            ▼               │
│       MCP Tool Layer       │
└────────────┬───────────────┘
             ▼
┌────────────────────────────┐
│ Safe operator capabilities │
│ files / shell / URL /      │
│ memory / status / planning │
└────────────────────────────┘
```

## Components

### LiveKit worker

`friday_agent/livekit_agent.py` is the runtime entry point for the voice agent. It joins LiveKit rooms and processes realtime audio.

### Groq

Groq provides the configured speech-to-text and language-model intelligence through the LiveKit plugins.

### ElevenLabs

ElevenLabs provides text-to-speech output. The voice is configured by environment variables so credentials and voice selection remain deployment-specific.

### Silero VAD and turn detection

VAD determines when meaningful speech is present. Turn detection helps determine when the operator has finished speaking so FRIDAY can respond naturally.

### MCP server

`friday_agent/mcp_server.py` exposes a streamable HTTP MCP server. `mcp_tools.py` contains the tool implementation layer.

The tool layer is intentionally constrained:

- File access stays inside the configured workspace root.
- Shell execution uses an explicit command allow-list.
- URL responses are clipped.
- File writes have a maximum byte limit.
- Memory is stored as bounded JSON state.

## Data flow

1. Operator speaks through a LiveKit client.
2. LiveKit transports the audio to the FRIDAY worker.
3. VAD and turn detection identify usable speech and conversation boundaries.
4. Groq STT converts speech to text.
5. FRIDAY's LLM receives the operator request and available context.
6. If needed, the agent uses an MCP tool.
7. The resulting response is synthesized by ElevenLabs.
8. Audio is returned through LiveKit to the operator.

## Deployment boundary

The repository is intentionally worker-only. Android UI/application code is outside this runtime repository. A mobile device can be the operator/development endpoint while the worker is deployed as a Docker container.

## Security boundary

Treat MCP tools as privileged capabilities. Production deployments should add authentication, authorization, network restrictions, logging, and auditing before exposing the MCP server beyond a trusted network.

Never commit service credentials. GitHub Actions receives production credentials through repository/environment Secrets.
