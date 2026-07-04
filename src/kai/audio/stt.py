"""Local speech recognition via faster-whisper. Model loads lazily on first use."""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError(
                    "Speech recognition requires faster-whisper — "
                    "install with: pip install kai[voice]"
                ) from exc
            name = self._config.get("model", "base.en")
            log.info("Loading whisper model %s (first run downloads it)...", name)
            self._model = WhisperModel(
                name,
                device=self._config.get("device", "cpu"),
                compute_type=self._config.get("compute_type", "int8"),
            )
        return self._model

    def transcribe(self, audio) -> str:
        """Transcribe a 16 kHz float32 numpy array to text."""
        if audio is None or len(audio) == 0:
            return ""
        segments, _info = self._load().transcribe(audio, beam_size=1, language="en")
        return " ".join(seg.text.strip() for seg in segments).strip()
