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
            "You can coordinate tools, reason across models, summarize findings, write code, "
            "and ask short clarifying questions only when truly blocked."
        ),
    )
    # OmniRoute exposes an OpenAI-compatible endpoint. Keep these configurable so the
    # same FRIDAY image can use a local Android/Termux server or a remote OmniRoute host.
    omniroute_base_url: str = os.getenv("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1")
    omniroute_api_key: str = os.getenv("OMNIROUTE_API_KEY", "")
    omniroute_model: str = os.getenv("OMNIROUTE_MODEL", "auto")
    use_omniroute: bool = os.getenv("USE_OMNIROUTE", "true").lower() in {"1", "true", "yes", "on"}

    groq_llm_model: str = os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
    groq_stt_model: str = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
    elevenlabs_voice: str = os.getenv(
        "ELEVENLABS_VOICE_LINK",
        os.getenv("ELEVENLABS_VOICE_ID", ""),
    )

    @property
    def elevenlabs_voice_id(self) -> str:
        """ElevenLabs voice ID parsed from ELEVENLABS_VOICE_LINK or ELEVENLABS_VOICE_ID."""
        return _elevenlabs_voice_id(self.elevenlabs_voice)


config = FridayConfig()
