"""Wake-word detection.

Three engines, picked by ``wake_word.engine``:

- ``namespot`` — listens for speech, transcribes the snippet with a small
  local Whisper model, and fuzzy-matches your wake name. Works with ANY name
  and is much more accent-tolerant than trained wake-word models. No account
  or key needed.
- ``openwakeword`` — open-source trained detector; lower CPU but limited to
  its pre-trained phrases ("hey jarvis", "alexa", "hey mycroft") and trained
  mostly on US-accented synthetic speech.
- ``porcupine`` — Picovoice Porcupine; requires an access key
  (``wake_word.access_key`` or PICOVOICE_ACCESS_KEY). Picovoice retired its
  free tier in June 2026, so this is only useful if you already have a key.

``engine: auto``: Porcupine if a key is configured; openWakeWord if the
keyword is one of its pre-trained phrases; otherwise namespot.
"""

from __future__ import annotations

import difflib
import logging
import os
from typing import Any, Protocol

from kai.intent import normalize

log = logging.getLogger(__name__)

OWW_PRETRAINED = {"hey jarvis", "alexa", "hey mycroft", "hey rhasspy", "timer", "weather"}
_ATTENTION_WORDS = {"hey", "ok", "okay", "yo", "hi", "hello", "so"}


def matches_wake_phrase(transcript: str, aliases: tuple[str, ...] | list[str],
                        ratio: float = 0.75) -> bool:
    """True if *transcript* is (close to) one of the wake *aliases*.

    Tolerant of attention words ("hey kai"), trailing punctuation, and
    near-miss transcriptions ("kye" for "kai") via fuzzy matching.
    """
    tokens = normalize(transcript).split()
    while tokens and tokens[0] in _ATTENTION_WORDS:
        tokens.pop(0)
    if not tokens or len(tokens) > 4:  # a whole sentence is not a wake call
        return False
    candidates = {" ".join(tokens[i:j])
                  for i in range(len(tokens))
                  for j in range(i + 1, min(i + 3, len(tokens)) + 1)}
    for alias in aliases:
        alias_n = normalize(alias)
        for cand in candidates:
            if cand == alias_n or difflib.SequenceMatcher(None, alias_n, cand).ratio() >= ratio:
                return True
    return False


class Listener(Protocol):
    keyword: str

    def wait(self) -> None: ...
    def close(self) -> None: ...


class NameSpotterListener:
    """Wake on any spoken name: energy-gated recording -> tiny Whisper ->
    fuzzy match. Idle cost is just RMS checks on 100 ms mic blocks."""

    SAMPLE_RATE = 16_000
    BLOCK = 1600  # 100 ms

    def __init__(self, config: dict[str, Any]) -> None:
        try:
            import numpy  # noqa: F401
            import sounddevice  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "Wake word requires sounddevice + numpy — "
                "install with: pip install kai[voice]"
            ) from exc
        from kai.audio.stt import Transcriber

        self.keyword = str(config.get("keyword") or "kai")
        aliases = config.get("aliases") or [self.keyword]
        self.aliases = tuple(dict.fromkeys([self.keyword, *aliases]))
        # sensitivity 0..1 -> fuzzy ratio 0.9..0.6 (higher sensitivity = looser match)
        sens = float(config.get("sensitivity", 0.5))
        self.ratio = 0.9 - 0.3 * max(0.0, min(1.0, sens))
        # None = auto-calibrate from ambient noise when listening starts
        raw_threshold = config.get("energy_threshold")
        self.energy_threshold: float | None = (
            float(raw_threshold) if raw_threshold is not None else None
        )
        self._device = config.get("device")
        # A dedicated small model keeps wake checks fast; the main STT model
        # (base.en by default) is only used for the actual command.
        self._transcriber = Transcriber({
            "model": config.get("spot_model", "tiny.en"),
            "device": "cpu",
            "compute_type": "int8",
        })
        self._transcriber._load()  # eager, so the first wake isn't slow

    def _calibrate(self, stream, np) -> float:
        """Measure ~1 s of ambient noise; gate a bit above it."""
        levels = []
        for _ in range(10):
            data, _ = stream.read(self.BLOCK)
            levels.append(float(np.sqrt(np.mean(data[:, 0] ** 2))))
        ambient = float(np.median(levels))
        # Low-gain mic arrays can have ambient near zero, so the floor matters
        # more than the multiplier — keep it low enough for quiet voices.
        threshold = max(0.0015, ambient * 6)
        log.info("mic ambient rms=%.4f -> energy threshold %.4f", ambient, threshold)
        return threshold

    def utterances(self, on_level=None):
        """Generator yielding (transcript, matched) per detected utterance.

        ``on_level(rms, threshold)`` is called for every 100 ms block —
        used by `kai hear` to show a live level meter.
        """
        from collections import deque

        import numpy as np
        import sounddevice as sd

        with sd.InputStream(
            samplerate=self.SAMPLE_RATE, channels=1, dtype="float32",
            blocksize=self.BLOCK, device=self._device,
        ) as stream:
            if self.energy_threshold is None:
                self.energy_threshold = self._calibrate(stream, np)
            preroll: deque = deque(maxlen=3)  # 300 ms so the name's onset isn't clipped
            while True:
                data, _ = stream.read(self.BLOCK)
                mono = data[:, 0].copy()
                rms = float(np.sqrt(np.mean(mono**2)))
                if on_level is not None:
                    on_level(rms, self.energy_threshold)
                if rms < self.energy_threshold:
                    preroll.append(mono)
                    continue
                # Speech started — capture up to ~2.5 s, stop on 0.5 s of quiet.
                chunks = [*preroll, mono]
                preroll.clear()
                quiet = 0
                for _ in range(25):
                    data, _ = stream.read(self.BLOCK)
                    mono = data[:, 0].copy()
                    chunks.append(mono)
                    rms = float(np.sqrt(np.mean(mono**2)))
                    if on_level is not None:
                        on_level(rms, self.energy_threshold)
                    if rms < self.energy_threshold:
                        quiet += 1
                        if quiet >= 5:
                            break
                    else:
                        quiet = 0
                text = self._transcriber.transcribe(np.concatenate(chunks))
                if text:
                    yield text, matches_wake_phrase(text, self.aliases, self.ratio)

    def wait(self) -> None:
        for text, matched in self.utterances():
            log.debug("namespot heard: %r (match=%s)", text, matched)
            if matched:
                return

    def close(self) -> None:
        pass


class OpenWakeWordListener:
    """openWakeWord-based listener. No API key required."""

    SAMPLE_RATE = 16_000
    FRAME = 1280  # 80 ms — what openWakeWord expects

    def __init__(self, config: dict[str, Any]) -> None:
        try:
            import openwakeword
            from openwakeword.model import Model
            import sounddevice  # noqa: F401 — fail early if missing
        except ImportError as exc:
            raise RuntimeError(
                "Wake word requires openwakeword + sounddevice — "
                "install with: pip install kai[voice]"
            ) from exc

        keyword = str(config.get("keyword", "hey jarvis")).lower()
        model_name = keyword.replace(" ", "_")
        try:
            openwakeword.utils.download_models(model_names=[model_name])
            self._model = Model(wakeword_models=[model_name], inference_framework="onnx")
        except Exception:
            fallback = "hey_jarvis"
            if model_name != fallback:
                log.warning(
                    "openWakeWord has no pre-trained model for %r; using 'hey jarvis'",
                    keyword,
                )
                openwakeword.utils.download_models(model_names=[fallback])
                self._model = Model(wakeword_models=[fallback], inference_framework="onnx")
                keyword = "hey jarvis"
            else:
                raise
        self.keyword = keyword
        self.threshold = float(config.get("sensitivity", 0.5))
        self._device = config.get("device")

    def wait(self) -> None:
        import sounddevice as sd

        self._model.reset()
        with sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=self.FRAME,
            device=self._device,
        ) as stream:
            while True:
                data, _overflow = stream.read(self.FRAME)
                scores = self._model.predict(data[:, 0])
                if max(scores.values()) >= self.threshold:
                    return

    def close(self) -> None:
        pass


class PorcupineListener:
    """Porcupine-based listener (needs a Picovoice access key)."""

    def __init__(self, config: dict[str, Any]) -> None:
        try:
            import pvporcupine
            from pvrecorder import PvRecorder
        except ImportError as exc:
            raise RuntimeError(
                "Porcupine wake word requires pvporcupine + pvrecorder — "
                "install with: pip install kai[voice]"
            ) from exc

        access_key = config.get("access_key") or os.environ.get("PICOVOICE_ACCESS_KEY", "")
        if not access_key:
            raise RuntimeError(
                "Porcupine needs a Picovoice access key (wake_word.access_key "
                "or PICOVOICE_ACCESS_KEY). Note: Picovoice retired its free "
                "tier in June 2026 — use engine: openwakeword instead."
            )

        keyword = config.get("keyword", "porcupine")
        self._porcupine = pvporcupine.create(
            access_key=access_key,
            keywords=[keyword],
            sensitivities=[float(config.get("sensitivity", 0.5))],
        )
        self._recorder = PvRecorder(frame_length=self._porcupine.frame_length)
        self.keyword = keyword

    def wait(self) -> None:
        self._recorder.start()
        try:
            while True:
                frame = self._recorder.read()
                if self._porcupine.process(frame) >= 0:
                    return
        finally:
            self._recorder.stop()

    def close(self) -> None:
        self._recorder.delete()
        self._porcupine.delete()


# Backwards-compatible alias (pre-openWakeWord versions exposed this name).
WakeWordListener = PorcupineListener


def create_listener(config: dict[str, Any]) -> Listener:
    """Build the configured wake-word listener.

    Raises RuntimeError with an actionable message if no engine can start.
    """
    engine = str(config.get("engine", "auto")).lower()
    has_key = bool(config.get("access_key") or os.environ.get("PICOVOICE_ACCESS_KEY"))
    keyword = str(config.get("keyword") or "").lower()

    if engine == "porcupine" or (engine == "auto" and has_key):
        try:
            return PorcupineListener(config)
        except RuntimeError:
            if engine == "porcupine":
                raise
            log.warning("Porcupine unavailable; trying other engines")
    if engine == "openwakeword" or (engine == "auto" and keyword in OWW_PRETRAINED):
        return OpenWakeWordListener(config)
    return NameSpotterListener(config)
