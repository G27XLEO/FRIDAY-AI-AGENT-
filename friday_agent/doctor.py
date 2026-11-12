"""Offline voice configuration checks. Never display credential values."""
from __future__ import annotations

import argparse
import os
from collections.abc import Mapping
from urllib.parse import urlparse

from friday_agent.config import FridayConfig, _elevenlabs_voice_id

REQUIRED = (
    "LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET",
    "GROQ_API_KEY", "ELEVENLABS_API_KEY",
)


def is_placeholder(value: str) -> bool:
    value = value.strip().lower()
    return (not value or value.startswith(("your_", "your-", "replace_", "replace-"))
            or value in {"changeme", "change-me", "todo", "..."})


def configuration_errors(
    environ: Mapping[str, str] | None = None, *, console: bool = False
) -> list[str]:
    env = os.environ if environ is None else environ
    errors = []
    required = REQUIRED[3:] if console else REQUIRED
    for name in required:
        if is_placeholder(env.get(name, "")):
            errors.append(f"{name}: missing or still a placeholder")
    if not console and not is_placeholder(env.get("LIVEKIT_URL", "")):
        try:
            url = urlparse(env["LIVEKIT_URL"].strip())
            valid = (url.scheme in {"ws", "wss"} and url.hostname
                     and not url.username and not url.password
                     and not url.query and not url.fragment
                     and not url.hostname.startswith("your-")
                     and url.port != 0)
        except ValueError:
            valid = False
        if not valid:
            errors.append("LIVEKIT_URL: use your project's ws:// or wss:// URL")
    voice = env.get("ELEVENLABS_VOICE_LINK", "").strip() or env.get("ELEVENLABS_VOICE_ID", "").strip()
    if voice:
        try:
            voice_id = _elevenlabs_voice_id(voice)
        except ValueError:
            voice_id = ""
        if is_placeholder(voice_id) or not voice_id.isalnum():
            errors.append("ELEVENLABS_VOICE_ID/LINK: use a voice ID or supported share link, or leave blank for the default voice")
    for name in ("FRIDAY_IDENTITY", "GROQ_LLM_MODEL", "GROQ_STT_MODEL", "ELEVENLABS_TTS_MODEL"):
        if name in env and is_placeholder(env[name]):
            errors.append(f"{name}: must not be blank or a placeholder")
    return errors


def require_voice_configuration(*, console: bool = False) -> None:
    errors = configuration_errors(console=console)
    if errors:
        raise ValueError("Voice configuration is incomplete:\n  " + "\n  ".join(errors)
                         + "\nSet values in the repository .env or deployment environment. "
                         "Run: python -m friday_agent.doctor")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--console", action="store_true", help="Check Groq and ElevenLabs for local microphone testing; LiveKit Cloud is not required")
    args = parser.parse_args()
    errors = configuration_errors(console=args.console)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        print("Edit .env or deployment environment settings. Never paste keys into chat or commit them.")
        return 1
    settings = FridayConfig()
    print("PASS Voice configuration is present and locally valid.")
    print(f"Agent: {settings.identity}; Groq: {settings.groq_stt_model} / {settings.groq_llm_model}; TTS: {settings.elevenlabs_model}")
    print("This offline check does not verify credentials, model access, quotas, or connectivity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
