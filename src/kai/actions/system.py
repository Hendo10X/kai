"""System controls: lock, screenshot, time/date."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from kai.actions.registry import ActionRegistry
from kai.intent import Context


def _lock(slots: dict[str, str], ctx: Context) -> str:
    if sys.platform == "win32":
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=False)
    elif sys.platform == "darwin":
        subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to keystroke "q" using {command down, control down}'],
            check=False,
        )
    else:
        subprocess.run(["loginctl", "lock-session"], check=False)
    return "Locking."


def _screenshot(slots: dict[str, str], ctx: Context) -> str:
    import pyautogui

    out_dir = Path.home() / "Pictures" / "kai"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"screenshot-{datetime.now():%Y%m%d-%H%M%S}.png"
    pyautogui.screenshot(str(path))
    return f"Screenshot saved to {path}"


def _time(slots: dict[str, str], ctx: Context) -> str:
    return "It's " + datetime.now().strftime("%I:%M %p.").lstrip("0")


def _date(slots: dict[str, str], ctx: Context) -> str:
    return datetime.now().strftime("Today is %A, %B %d.")


def register(registry: ActionRegistry) -> None:
    registry.register(
        "system.lock",
        ["lock screen", "lock computer", "lock my computer", "lock it"],
        _lock,
        "Lock the workstation",
    )
    registry.register(
        "system.screenshot",
        ["take a screenshot", "screenshot", "capture screen"],
        _screenshot,
        "Save a screenshot to Pictures/kai",
    )
    registry.register(
        "system.time",
        ["what time is it", "whats the time", "current time"],
        _time,
        "Say the current time",
    )
    registry.register(
        "system.date",
        ["whats the date", "whats todays date", "what day is it"],
        _date,
        "Say today's date",
    )
