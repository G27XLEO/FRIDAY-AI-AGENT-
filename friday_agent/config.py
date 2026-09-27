from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import parse_qs, urlparse


def _elevenlabs_voice_id(value: str) -> str:
    value = value.strip()
    if not value:
        return ""

    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return value

    query_voice_id = parse_qs(parsed.query).get("voiceId")
    if query_voice_id and query_voice_id[0].strip():
        return query_voice_id[0].strip()

    path_parts = [part for part in parsed.path.split("/") if part]
    for marker in ("voice", "voices"):
        if marker in path_parts:
            index = path_parts.index(marker)
            if index + 1 < len(path_parts):
                return path_parts[index + 1]

    return value


@dataclass(frozen=True)
class FridayConfig:
    identity: str = os.getenv("FRIDAY_IDENTITY", "friday-ai-agent")

    instructions: str = os.getenv(
        "FRIDAY_INSTRUCTIONS",
        "You are FRIDAY, a realtime mission-control AI. Address the operator as boss.",
    )

    groq_llm_model: str = os.getenv(
        "GROQ_LLM_MODEL", "llama-3.3-70b-versatile"
    )
    groq_stt_model: str = os.getenv(
        "GROQ_STT_MODEL", "whisper-large-v3-turbo"
    )

    elevenlabs_voice: str = os.getenv(
        "ELEVENLABS_VOICE_LINK",
        os.getenv("ELEVENLABS_VOICE_ID", ""),
    )

    mcp_enabled: bool = os.getenv("FRIDAY_MCP_ENABLED", "true").lower() in {
        "1", "true", "yes", "on"
    }
    mcp_server_url: str = os.getenv(
        "FRIDAY_MCP_SERVER_URL", "http://127.0.0.1:8000/mcp"
    )
    mcp_transport: str = os.getenv(
        "FRIDAY_MCP_TRANSPORT", "streamable-http"
    )
    mcp_timeout_seconds: float = float(
        os.getenv("FRIDAY_MCP_TIMEOUT_SECONDS", "30")
    )

    @property
    def elevenlabs_voice_id(self) -> str:
        return _elevenlabs_voice_id(self.elevenlabs_voice)


config = FridayConfig()
