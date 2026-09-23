from __future__ import annotations

"""Fast deterministic NLP routing for the realtime voice path.

This is intentionally lightweight: it enriches the LLM context without loading a
large local NLP model into the latency-sensitive LiveKit worker.
"""

import re
from dataclasses import dataclass

@dataclass(frozen=True)
class NLPResult:
    text: str
    normalized: str
    intent: str
    urgency: str
    entities: tuple[str, ...]

_INTENT_PATTERNS = (
    ("status", ("status", "health", "online", "running", "system check")),
    ("planning", ("plan", "planning", "steps", "roadmap", "how should i")),
    ("code", ("code", "script", "program", "debug", "error", "repository", "github")),
    ("web", ("search", "look up", "find online", "website", "url", "latest")),
    ("file", ("file", "folder", "directory", "read", "write", "edit")),
    ("memory", ("remember", "recall", "forget", "memory")),
)
_URGENT_WORDS = {"urgent", "asap", "immediately", "critical", "emergency"}

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).casefold() if text else ""

def _intent(text: str) -> str:
    for intent, keywords in _INTENT_PATTERNS:
        if any(re.search(r"\b" + re.escape(keyword) + r"\b", text) for keyword in keywords):
            return intent
    return "general"

def _entities(text: str) -> tuple[str, ...]:
    if not text:
        return ()
    patterns = (
        r"https?://[^\s\)]+",
        r"@[A-Za-z0-9_.-]+",
        r"\b(?:FRIDAY|JARVIS|GitHub|LiveKit|Groq|ElevenLabs|MCP|NLP|Termux)\b",
    )
    found = []
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            if match not in found:
                found.append(match)
    return tuple(found[:12])

def analyze(text: str) -> NLPResult:
    raw = text.strip() if text else ""
    normalized = _normalize(raw)
    entities = _entities(raw)
    intent = "web" if any(e.lower().startswith("http") for e in entities) else _intent(normalized)
    urgency = "high" if any(re.search(r"\b" + re.escape(word) + r"\b", normalized) for word in _URGENT_WORDS) else "normal"
    return NLPResult(raw, normalized, intent, urgency, entities)

def build_context(text: str) -> str:
    result = analyze(text)
    entities = ", ".join(result.entities) if result.entities else "none"
    return (
        "NLP CONTEXT\n"
        f"intent={result.intent}\n"
        f"urgency={result.urgency}\n"
        f"entities={entities}\n"
        f"normalized_request={result.normalized}"
    )
