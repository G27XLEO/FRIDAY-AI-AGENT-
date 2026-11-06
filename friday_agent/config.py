from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import parse_qs, urlparse


def _elevenlabs_voice_id(value: str) -> str:
    """Return an ElevenLabs voice ID from either a raw ID or a shared voice URL."""
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
            marker_index = path_parts.index(marker)
            if marker_index + 1 < len(path_parts):
                return path_parts[marker_index + 1]

    return value


@dataclass(frozen=True)
class FridayConfig:
    """Runtime configuration for the realtime assistant."""

    identity: str = os.getenv("FRIDAY_IDENTITY", "friday-ai-agent")
    instructions: str = os.getenv(
        "FRIDAY_INSTRUCTIONS",
        (
            "You are FRIDAY, a real-time mission-control AI assistant. "
            "Be concise, technically precise, proactive, and calm under pressure. "
            "Use a polished, confident, lightly British-inspired tone without claiming "
            "to be any copyrighted character or cloning a real performer's voice. "
            "Treat the operator as the authority. "
            "Before taking consequential software actions, verify the requested scope. "
            "Prefer tools over pretending an action was completed. "
            "After a tool call, summarize the result in one or two spoken sentences. "
            "For urgent requests, stay calm, prioritize safety, and state the next action clearly."
        ),
    )
    groq_llm_model: str = os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
    groq_stt_model: str = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
    elevenlabs_voice: str = os.getenv(
        "ELEVENLABS_VOICE_LINK",
        os.getenv("ELEVENLABS_VOICE_ID", ""),
    )
    mcp_url: str = os.getenv("FRIDAY_MCP_URL", "")
    mcp_auth_token: str = os.getenv("FRIDAY_MCP_AUTH_TOKEN", "")
    mcp_timeout_seconds: float = float(os.getenv("FRIDAY_MCP_TIMEOUT_SECONDS", "20"))
    max_tool_steps: int = int(os.getenv("FRIDAY_MAX_TOOL_STEPS", "5"))
    max_tool_result_chars: int = int(os.getenv("FRIDAY_MAX_TOOL_RESULT_CHARS", "4000"))

    @property
    def elevenlabs_voice_id(self) -> str:
        """ElevenLabs voice ID parsed from ELEVENLABS_VOICE_LINK or ELEVENLABS_VOICE_ID."""
        return _elevenlabs_voice_id(self.elevenlabs_voice)


config = FridayConfig()
