from __future__ import annotations

"""Conservative, dependency-free multilingual NLP hints for FRIDAY.

These hints are NOT authorizations for tools or a replacement for an LLM.
Supported intent keywords: English (en), Hindi (hi), Marathi (mr).
"""

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class NLPResult:
    text: str
    normalized: str
    intent: str
    urgency: str
    entities: tuple[str, ...]
    language: str = "en"


_INTENT_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("status", (
        "status", "health", "online", "running", "system check",
        "सिस्टम की स्थिति", "सिस्टम चेक", "सिस्टम की जांच",
        "सिस्टमची स्थिती", "सिस्टम तपासा", "स्थिती",
    )),
    ("planning", (
        "plan", "planning", "steps", "roadmap", "how should i",
        "योजना", "प्लान बनाओ", "कैसे करें", "कदम",
        "नियोजन", "आराखडा", "कसे करावे", "पायऱ्या",
    )),
    ("code", (
        "code", "script", "program", "debug", "error", "repository", "github",
        "कोड", "त्रुटि", "प्रोग्राम", "रिपॉजिटरी", "त्रुटी",
    )),
    ("web", (
        "search", "look up", "find online", "website", "url", "latest",
        "इंटरनेट पर खोजो", "वेबसाइट", "ताज़ा",
        "इंटरनेटवर शोधा", "शोधा", "ताज्या",
    )),
    ("file", (
        "file", "folder", "directory", "read", "write", "edit",
        "फ़ाइल", "फाइल", "फ़ोल्डर", "पढ़ो", "लिखो",
        "फाईल", "फोल्डर", "वाचा", "लिहा", "संपादित करा",
    )),
    ("memory", (
        "remember", "recall", "forget", "memory",
        "याद रखो", "याद दिलाओ", "भूल जाओ", "याद",
        "लक्षात ठेव", "आठवण", "विसर",
    )),
)

_URGENT_WORDS = (
    "urgent", "asap", "immediately", "critical", "emergency",
    "तुरंत", "जल्दी", "आपातकाल", "अत्यावश्यक",
    "तातडीने", "लवकर", "आपत्कालीन",
)
_MARATHI_MARKERS = (
    "काय", "आहे", "आहेत", "माझा", "माझी", "मला", "कृपया",
    "उघडा", "उघड", "तपासा", "सांगा", "करा", "शोधा", "नियोजन",
    "कसे", "पायऱ्या", "तातडीने", "लवकर", "स्थिती",
)
_HINDI_MARKERS = (
    "क्या", "है", "हैं", "मेरी", "मेरा", "मुझे", "खोलो",
    "बताओ", "करो", "ढूंढो", "योजना", "तुरंत", "जल्दी",
    "स्थिति", "जांच",
)
_URL = re.compile(r"https?://[^\s\)]+", re.IGNORECASE)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text).strip()).casefold()


def _contains_phrase(text: str, term: str) -> bool:
    """Match complete words/phrases, including Devanagari combining marks."""
    term = re.escape(term)
    return bool(re.search(r"(?<!\w)" + term + r"(?!\w)", text, re.UNICODE))


def detect_language(text: str) -> str:
    """Best-effort language hint; mixed/ambiguous Devanagari defaults to Hindi."""
    normalized = _normalize(text)
    if not re.search(r"[\u0900-\u097f]", normalized):
        return "en"
    marathi = sum(_contains_phrase(normalized, word) for word in _MARATHI_MARKERS)
    hindi = sum(_contains_phrase(normalized, word) for word in _HINDI_MARKERS)
    return "mr" if marathi > hindi else "hi"


def _intent(text: str) -> str:
    for intent, terms in _INTENT_PATTERNS:
        if any(_contains_phrase(text, term) for term in terms):
            return intent
    return "general"


def _entities(text: str) -> tuple[str, ...]:
    found: list[str] = []
    for pattern in (
        _URL, re.compile(r"@[A-Za-z0-9_.-]+"),
        re.compile(r"\b(?:FRIDAY|GitHub|LiveKit|Groq|ElevenLabs|MCP|Termux)\b", re.I)
    ):
        for match in pattern.finditer(text):
            entity = match.group(0)
            if entity not in found:
                found.append(entity)
    return tuple(found[:12])


def analyze(text: str) -> NLPResult:
    original = text.strip() if text else ""
    normalized = _normalize(original)
    entities = _entities(original)
    intent = "web" if any(entity.lower().startswith("http") for entity in entities) else _intent(normalized)
    urgency = "high" if any(_contains_phrase(normalized, term) for term in _URGENT_WORDS) else "normal"
    return NLPResult(
        text=original, normalized=normalized, intent=intent,
        urgency=urgency, entities=entities, language=detect_language(original),
    )


def build_context(text: str) -> str:
    result = analyze(text)
    entities = ", ".join(result.entities) if result.entities else "none"
    return (
        "NLP CONTEXT\n"
        f"language={result.language}\n"
        f"intent={result.intent}\n"
        f"urgency={result.urgency}\n"
        f"entities={entities}\n"
        f"normalized_request={result.normalized}"
    )
