"""Application launching: "open {app}" / "launch {app}"."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from kai.actions.registry import ActionRegistry
from kai.intent import Context


def launch(target: str) -> None:
    """Open a path, URL, or executable in a platform-appropriate way."""
    if target.startswith(("http://", "https://")):
        import webbrowser

        webbrowser.open(target)
        return

    path = Path(target).expanduser()
    if path.exists():
        if sys.platform == "win32":
            import os

            os.startfile(path)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return

    exe = shutil.which(target)
    if exe:
        subprocess.Popen([exe])
        return

    if sys.platform == "win32":
        # Let the shell resolve app names like "notepad" or store aliases.
        subprocess.Popen(f'start "" "{target}"', shell=True)  # noqa: S602
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-a", target])
    else:
        raise FileNotFoundError(f"Could not find application: {target}")


def _open_app(slots: dict[str, str], ctx: Context) -> str:
    name = slots["app"]
    aliases = ctx.config.get("apps") or {}
    target = aliases.get(name.lower(), name)
    launch(target)
    return f"Opening {name}"


def register(registry: ActionRegistry) -> None:
    registry.register(
        "launcher.open",
        ["open {app}", "launch {app}", "start {app}"],
        _open_app,
        "Open an application, file, or URL (uses `apps:` aliases from config)",
    )
