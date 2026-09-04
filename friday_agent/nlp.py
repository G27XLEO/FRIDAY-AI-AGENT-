from __future__ import annotations

"""Lightweight NLP preprocessing for FRIDAY voice requests.

The module deliberately avoids a heavyweight NLP model in the realtime path.
It normalizes speech transcripts, extracts a small amount of intent metadata,
and produces a compact context block for the reasoning model.
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


_INTENT_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("status", ("status", "health", "online", "running", "system check")),
    ("planning", ("plan", "planning", "steps", "roadmap", "how should i")),
    ("code", ("code", "script", "program", "debug", "error", "repository", "github")),
    ("web", ("search", "look up", "find online", "website", "url", "latest")),
    ("file", ("file", "folder", "directory", "read", "write", "edit")),
    ("memory", ("remember", "recall", "forget", "memory")),
)

_URGENT_WORDS = {"urgent", "asap", "immediately", "critical", "emergency"}


def _normalize(text: str) -> str:
    """Normalize text: strip, collapse whitespace, convert to lowercase."""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text.casefold()


def _intent(text: str) -> str:
    """Extract intent from normalized text using keyword matching.
    
    Matches on word boundaries to avoid partial matches.
    Returns the first matching intent, or 'general' if no match.
    """
    if not text:
        return "general"
    
    for intent, keywords in _INTENT_PATTERNS:
        for keyword in keywords:
            # Use word boundary matching to avoid substring matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text, flags=re.IGNORECASE):
                return intent
    return "general"


def _entities(text: str) -> tuple[str, ...]:
    """Extract named entities (URLs, mentions, known services).
    
    Searches the original (non-normalized) text to preserve exact formatting.
    Limits results to 12 entities to keep output compact.
    """
    if not text:
        return ()
    
    found: list[str] = []
    patterns = (
        r"https?://[^\s\)]+",  # URLs with boundary checking
        r"@[A-Za-z0-9_.-]+",
        r"\b(?:FRIDAY|GitHub|LiveKit|Groq|ElevenLabs|MCP|Termux)\b",
    )
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            if match not in found:
                found.append(match)
    return tuple(found[:12])


def analyze(text: str) -> NLPResult:
    """Normalize a transcript and extract lightweight intent/entities.
    
    Handles empty/whitespace-only input gracefully.
    """
    text = text.strip() if text else ""
    normalized = _normalize(text)
    urgency = "high" if any(word in normalized for word in _URGENT_WORDS) else "normal"
    return NLPResult(
        text=text,
        normalized=normalized,
        intent=_intent(normalized),
        urgency=urgency,
        entities=_entities(text),
    )


def build_context(text: str) -> str:
    """Create compact structured NLP context for the LLM prompt.
    
    Handles empty input by returning a minimal valid context block.
    """
    result = analyze(text)
    entities = ", ".join(result.entities) if result.entities else "none"
    return (
        "NLP CONTEXT\n"
        f"intent={result.intent}\n"
        f"urgency={result.urgency}\n"
        f"entities={entities}\n"
        f"normalized_request={result.normalized}"
    )
