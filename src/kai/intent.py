"""Intent engine: matches transcribed text against registered command patterns.

Patterns are plain phrases with optional ``{slot}`` placeholders:

    "open {app}"        -> matches "open firefox", slots {"app": "firefox"}
    "next track"        -> exact phrase (after normalization)

No cloud, no LLM — deterministic pattern matching (PRD v1 non-goal: no
conversational AI). Longer/more specific patterns win over shorter ones.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

Handler = Callable[[dict[str, str], "Context"], str | None]

_SLOT_RE = re.compile(r"\{(\w+)\}")
_APOSTROPHE_RE = re.compile(r"['’]")
# Punctuation runs that are NOT sandwiched between word characters — strips
# "song." and "open, firefox" but keeps "example.com" and "5:30".
_EDGE_PUNCT_RE = re.compile(r"(?<!\w)[^\w\s]+|[^\w\s]+(?!\w)")


def normalize(text: str) -> str:
    """Lowercase, drop apostrophes and edge punctuation, collapse whitespace.

    Word-internal punctuation survives so slot values like "example.com"
    stay intact.
    """
    text = _APOSTROPHE_RE.sub("", text.lower())
    text = _EDGE_PUNCT_RE.sub(" ", text)
    return " ".join(text.split())


def compile_pattern(pattern: str) -> re.Pattern[str]:
    """Compile a ``{slot}`` phrase into an anchored regex."""
    parts: list[str] = []
    pos = 0
    for match in _SLOT_RE.finditer(pattern):
        parts.append(re.escape(normalize(pattern[pos : match.start()])).replace(r"\ ", r"\s+"))
        parts.append(f"(?P<{match.group(1)}>.+?)")
        pos = match.end()
    parts.append(re.escape(normalize(pattern[pos:])).replace(r"\ ", r"\s+"))
    return re.compile(r"^\s*" + r"\s*".join(p for p in parts if p) + r"\s*$")


@dataclass
class Intent:
    name: str
    patterns: list[str]
    handler: Handler
    description: str = ""
    source: str = "builtin"  # builtin | custom | plugin name
    _compiled: list[tuple[str, re.Pattern[str]]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self._compiled = [(p, compile_pattern(p)) for p in self.patterns]

    def match(self, text: str) -> dict[str, str] | None:
        for _, regex in self._compiled:
            m = regex.match(text)
            if m:
                return {k: v.strip() for k, v in m.groupdict().items()}
        return None


@dataclass
class Match:
    intent: Intent
    slots: dict[str, str]


class Context:
    """Shared runtime state handed to every action handler."""

    def __init__(self, config: dict[str, Any], speaker: Any = None) -> None:
        self.config = config
        self.speaker = speaker  # tts Speaker or None
        self.state: dict[str, Any] = {}  # scratch space (e.g. dictation flag)

    def say(self, text: str) -> None:
        """Speak if TTS is available; the CLI also prints handler responses."""
        if self.speaker is not None:
            self.speaker.say(text)


def _specificity(intent: Intent, pattern_text: str) -> int:
    """Literal (non-slot) length — longer literals beat generic catch-alls."""
    return len(_SLOT_RE.sub("", pattern_text))


class IntentEngine:
    """Resolves free text to the best-matching registered intent."""

    def __init__(self) -> None:
        self._intents: dict[str, Intent] = {}

    def register(self, intent: Intent) -> None:
        if intent.name in self._intents:
            raise ValueError(f"Intent already registered: {intent.name}")
        self._intents[intent.name] = intent

    def unregister(self, name: str) -> None:
        self._intents.pop(name, None)

    @property
    def intents(self) -> list[Intent]:
        return list(self._intents.values())

    def resolve(self, text: str) -> Match | None:
        text = normalize(text)
        if not text:
            return None
        best: tuple[int, Intent, dict[str, str]] | None = None
        for intent in self._intents.values():
            for pattern_text, regex in intent._compiled:
                m = regex.match(text)
                if not m:
                    continue
                score = _specificity(intent, pattern_text)
                if best is None or score > best[0]:
                    best = (score, intent, {k: v.strip() for k, v in m.groupdict().items()})
        if best is None:
            return None
        return Match(intent=best[1], slots=best[2])
