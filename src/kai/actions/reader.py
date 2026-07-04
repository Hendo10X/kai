"""Reading assistant: read the clipboard (or currently selected text) aloud."""

from __future__ import annotations

from kai.actions.registry import ActionRegistry
from kai.intent import Context


def get_clipboard() -> str:
    import tkinter

    root = tkinter.Tk()
    root.withdraw()
    try:
        return root.clipboard_get()
    except tkinter.TclError:
        return ""
    finally:
        root.destroy()


def _read_clipboard(slots: dict[str, str], ctx: Context) -> str | None:
    text = get_clipboard().strip()
    if not text:
        return "The clipboard is empty."
    ctx.say(text)
    return None if ctx.speaker else text  # print it when there's no TTS


def _read_selection(slots: dict[str, str], ctx: Context) -> str | None:
    # Copy the current selection, then read it.
    import pyautogui

    pyautogui.hotkey("ctrl", "c")
    return _read_clipboard(slots, ctx)


def _stop_reading(slots: dict[str, str], ctx: Context) -> None:
    if ctx.speaker is not None:
        ctx.speaker.stop()
    return None


def register(registry: ActionRegistry) -> None:
    registry.register(
        "reader.clipboard",
        ["read clipboard", "read the clipboard", "read this"],
        _read_clipboard,
        "Read clipboard contents aloud",
    )
    registry.register(
        "reader.selection",
        ["read selection", "read selected text", "read that"],
        _read_selection,
        "Copy the current selection and read it aloud",
    )
    registry.register(
        "reader.stop",
        ["stop reading", "stop talking", "be quiet"],
        _stop_reading,
        "Stop text-to-speech playback",
    )
