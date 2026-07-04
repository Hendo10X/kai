"""Media controls via OS media keys (pyautogui)."""

from __future__ import annotations

from kai.actions.registry import ActionRegistry
from kai.intent import Context


def _press(key: str, times: int = 1) -> None:
    import pyautogui

    for _ in range(times):
        pyautogui.press(key)


def register(registry: ActionRegistry) -> None:
    registry.register(
        "media.play_pause",
        ["play", "pause", "play music", "pause music", "resume"],
        lambda s, c: (_press("playpause"), None)[1],
        "Toggle media playback",
    )
    registry.register(
        "media.next",
        ["next track", "next song", "skip", "skip song"],
        lambda s, c: (_press("nexttrack"), None)[1],
        "Next track",
    )
    registry.register(
        "media.previous",
        ["previous track", "previous song", "go back a song"],
        lambda s, c: (_press("prevtrack"), None)[1],
        "Previous track",
    )
    registry.register(
        "media.volume_up",
        ["volume up", "turn it up", "louder"],
        lambda s, c: (_press("volumeup", 4), None)[1],
        "Raise volume",
    )
    registry.register(
        "media.volume_down",
        ["volume down", "turn it down", "quieter"],
        lambda s, c: (_press("volumedown", 4), None)[1],
        "Lower volume",
    )
    registry.register(
        "media.mute",
        ["mute", "unmute", "mute volume"],
        lambda s, c: (_press("volumemute"), None)[1],
        "Toggle mute",
    )
