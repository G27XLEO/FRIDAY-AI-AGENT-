from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

# Load only this checkout's .env; deployment environment values take precedence.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


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

    identity: str = field(default_factory=lambda: os.getenv("FRIDAY_IDENTITY", "friday-ai-agent"))
    instructions: str = field(default_factory=lambda: os.getenv(
        "FRIDAY_INSTRUCTIONS",
        (
            "You are FRIDAY, a real-time mission-control AI assistant. "
            "Be concise, technically precise, proactive, and calm under pressure. "
            "Use a polished, confident, lightly British-inspired tone without claiming "
            "to be any copyrighted character or cloning a real performer's voice. "
            "You can coordinate tools, reason across models, summarize findings, write code, "
            "and ask short clarifying questions only when truly blocked."
        ),
    ))
    groq_llm_model: str = field(default_factory=lambda: os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile"))
    groq_stt_model: str = field(default_factory=lambda: os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo"))
    elevenlabs_voice: str = field(default_factory=lambda: (
        os.getenv("ELEVENLABS_VOICE_LINK", "").strip()
        or os.getenv("ELEVENLABS_VOICE_ID", "").strip()
    ))
    elevenlabs_model: str = field(default_factory=lambda: os.getenv("ELEVENLABS_TTS_MODEL", "eleven_flash_v2_5"))

    @property
    def elevenlabs_voice_id(self) -> str:
        """ElevenLabs voice ID parsed from ELEVENLABS_VOICE_LINK or ELEVENLABS_VOICE_ID."""
        return _elevenlabs_voice_id(self.elevenlabs_voice)


config = FridayConfig()
