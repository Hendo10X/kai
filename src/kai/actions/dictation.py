"""Dictation: type spoken text into the focused window.

"type {text}" types once. "start dictation" flips a mode flag the voice loop
checks — while active, every utterance is typed verbatim instead of being
interpreted as a command, until "stop dictation".
"""

from __future__ import annotations

from kai.actions.registry import ActionRegistry
from kai.intent import Context

DICTATION_KEY = "dictation_active"


def type_text(text: str) -> None:
    import pyautogui

    pyautogui.write(text, interval=0.01)


def _type_once(slots: dict[str, str], ctx: Context) -> None:
    type_text(slots["text"])
    return None


def _start(slots: dict[str, str], ctx: Context) -> str:
    ctx.state[DICTATION_KEY] = True
    return "Dictation on. Say 'stop dictation' to finish."


def _stop(slots: dict[str, str], ctx: Context) -> str:
    ctx.state[DICTATION_KEY] = False
    return "Dictation off."


def register(registry: ActionRegistry) -> None:
    registry.register(
        "dictation.type",
        ["type {text}", "write {text}"],
        _type_once,
        "Type the given text into the focused window",
    )
    registry.register(
        "dictation.start",
        ["start dictation", "start dictating", "take dictation"],
        _start,
        "Type every following utterance until stopped",
    )
    registry.register(
        "dictation.stop",
        ["stop dictation", "stop dictating", "end dictation"],
        _stop,
        "Stop dictation mode",
    )
