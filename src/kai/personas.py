"""Persona: the assistant's identity — wake name, voice preference, and
response flavor.

Kai is the only persona for now; the structure supports adding more later
(each entry defines its own wake aliases, TTS voice, and phrasing).
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    name: str
    tagline: str
    voice_hints: tuple[str, ...]  # substrings of installed TTS voice names, in order
    yarn_voice: str  # YarnGPT voice used when tts.engine is yarngpt
    wake_aliases: tuple[str, ...]  # transcriptions that count as the wake name
    acks: tuple[str, ...]  # spoken right after the wake word is heard
    unknown: str  # {text} = what the user said
    error: str  # {error} = the exception
    greeting: str

    def ack(self) -> str:
        return random.choice(self.acks)


KAI = Persona(
    name="kai",
    tagline="casual and quick",
    voice_hints=("david", "mark", "male"),
    yarn_voice="Tayo",
    wake_aliases=("kai", "kye", "cai", "kay", "ki"),
    acks=("Yeah?", "What's up?", "Go ahead.", "Listening."),
    unknown="No idea what '{text}' means, boss.",
    error="Yeah, that didn't work: {error}",
    greeting="Kai here. Say the word.",
)

PERSONAS: dict[str, Persona] = {"kai": KAI}


def get_persona(name: str | None) -> Persona:
    """Look up a persona by name; unknown/empty names get Kai."""
    if not name:
        return KAI
    return PERSONAS.get(str(name).strip().lower(), KAI)
