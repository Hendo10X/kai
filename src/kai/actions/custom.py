"""User-defined commands from config.yaml.

Each entry under ``commands:`` needs a ``phrase`` (may contain {slots}) and
exactly one action key:

    run:  shell command (slots substituted with str.format)
    open: file, app, or URL
    keys: hotkey combo like "ctrl+shift+s"
    say:  spoken/printed response
"""

from __future__ import annotations

import logging
import subprocess
from typing import Any

from kai.actions.launcher import launch
from kai.actions.registry import ActionRegistry
from kai.intent import Context

log = logging.getLogger(__name__)

ACTION_KEYS = ("run", "open", "keys", "say")


def _make_handler(action: str, value: str):
    def handler(slots: dict[str, str], ctx: Context) -> str | None:
        rendered = value.format(**slots) if slots else value
        if action == "run":
            result = subprocess.run(
                rendered, shell=True, capture_output=True, text=True, timeout=60
            )
            output = (result.stdout or result.stderr or "").strip()
            return output.splitlines()[0] if output else "Done."
        if action == "open":
            launch(rendered)
            return f"Opening {rendered}"
        if action == "keys":
            import pyautogui

            pyautogui.hotkey(*[k.strip() for k in rendered.split("+")])
            return None
        if action == "say":
            return rendered
        return None

    return handler


def register(registry: ActionRegistry, commands: list[dict[str, Any]]) -> int:
    """Register custom commands. Returns how many were registered."""
    count = 0
    for i, entry in enumerate(commands or []):
        phrase = entry.get("phrase")
        actions = [k for k in ACTION_KEYS if k in entry]
        if not phrase or len(actions) != 1:
            log.warning(
                "Skipping custom command %d: needs 'phrase' and exactly one of %s",
                i, "/".join(ACTION_KEYS),
            )
            continue
        action = actions[0]
        registry.register(
            name=f"custom.{i}.{action}",
            patterns=[phrase],
            handler=_make_handler(action, str(entry[action])),
            description=entry.get("description", f"{action}: {entry[action]}"),
            source="custom",
        )
        count += 1
    return count
