"""Text-to-speech engines.

- ``pyttsx3`` (default): fully offline, uses the OS's installed voices.
- ``yarngpt``: Nigerian voices via the YarnGPT cloud API (yarngpt.ai).
  Opt-in — the text Kai speaks is sent to the API; mic audio never is.

Both run on a background worker thread so speech never blocks listening.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Any

log = logging.getLogger(__name__)


class _QueueSpeaker:
    """Base: serial background playback queue with sync/async speak."""

    def __init__(self) -> None:
        self._queue: queue.Queue[tuple[str, threading.Event | None] | None] = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True, name="kai-tts")
        self._thread.start()

    def _worker(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                return
            text, done = item
            try:
                self._speak(text)
            except Exception:
                log.exception("TTS playback failed")
            finally:
                if done is not None:
                    done.set()

    def _speak(self, text: str) -> None:
        raise NotImplementedError

    def _interrupt(self) -> None:
        pass

    def say(self, text: str) -> None:
        self._queue.put((text, None))

    def say_sync(self, text: str, timeout: float = 30.0) -> None:
        """Speak and block until playback finishes — used for wake
        acknowledgments so the mic doesn't record Kai's own voice."""
        done = threading.Event()
        self._queue.put((text, done))
        done.wait(timeout)

    def stop(self) -> None:
        """Drop queued speech and interrupt the current utterance."""
        while not self._queue.empty():
            try:
                item = self._queue.get_nowait()
                if item and item[1] is not None:
                    item[1].set()
            except queue.Empty:
                break
        try:
            self._interrupt()
        except Exception:
            pass

    def close(self) -> None:
        self.stop()
        self._queue.put(None)


class Pyttsx3Speaker(_QueueSpeaker):
    """Offline TTS using the OS voices."""

    def __init__(self, config: dict[str, Any]) -> None:
        try:
            import pyttsx3
        except ImportError as exc:
            raise RuntimeError(
                "TTS requires pyttsx3 — install with: pip install kai[desktop]"
            ) from exc

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", config.get("rate", 180))
        self._engine.setProperty("volume", config.get("volume", 1.0))
        # `voice` (explicit) wins over `voice_hints` (persona preference list).
        hints = [config["voice"]] if config.get("voice") else list(config.get("voice_hints") or [])
        voices = self._engine.getProperty("voices")
        for hint in hints:
            chosen = next((v for v in voices if hint.lower() in v.name.lower()), None)
            if chosen:
                self._engine.setProperty("voice", chosen.id)
                break
        super().__init__()

    def _speak(self, text: str) -> None:
        self._engine.say(text)
        self._engine.runAndWait()

    def _interrupt(self) -> None:
        self._engine.stop()


# Backwards-compatible name
Speaker = Pyttsx3Speaker


def make_speaker(config: dict[str, Any], persona: Any = None):
    """Build the configured TTS engine; None if disabled or unavailable.

    Falls back from yarngpt to pyttsx3 (with a warning) so a missing API key
    or network problem never silences the assistant entirely.
    """
    if not config.get("enabled", True):
        return None

    engine = str(config.get("engine", "pyttsx3")).lower()
    if engine == "yarngpt":
        try:
            from kai.audio.yarn import YarnSpeaker

            return YarnSpeaker(config, persona)
        except RuntimeError as exc:
            log.warning("%s — falling back to local pyttsx3 voices", exc)

    cfg = dict(config)
    if not cfg.get("voice") and persona is not None and getattr(persona, "voice_hints", None):
        cfg["voice_hints"] = list(persona.voice_hints)
    try:
        return Pyttsx3Speaker(cfg)
    except RuntimeError as exc:
        log.warning("%s — continuing without speech output", exc)
        return None
