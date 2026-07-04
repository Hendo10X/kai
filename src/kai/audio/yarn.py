"""YarnGPT text-to-speech: Nigerian-accented voices via https://yarngpt.ai.

Cloud API (opt-in): only the text Kai speaks is sent — never microphone
audio. Synthesized clips are cached on disk so repeated phrases (persona
acknowledgments, common replies) cost one API call ever.

Voices (per https://www.yarngpt.ai/api-docs): Idera (default), Emma, Zainab,
Osagie, Wura, Jude, Chinenye, Tayo, Regina, Femi, Adaora, Umar, Mary, Nonso,
Remi, Adam.
"""

from __future__ import annotations

import hashlib
import io
import logging
import os
import wave
from pathlib import Path
from typing import Any

from platformdirs import user_cache_dir

from kai.audio.tts import _QueueSpeaker

log = logging.getLogger(__name__)

API_URL = "https://yarngpt.ai/api/v1/tts"
MAX_CHARS = 2000


class YarnSpeaker(_QueueSpeaker):
    def __init__(self, config: dict[str, Any], persona: Any = None) -> None:
        try:
            import requests  # noqa: F401
            import numpy  # noqa: F401
            import sounddevice  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "YarnGPT TTS requires requests, numpy and sounddevice — "
                "install with: pip install kai[voice]"
            ) from exc

        yarn_cfg = config.get("yarngpt") or {}
        self._api_key = yarn_cfg.get("api_key") or os.environ.get("YARNGPT_API_KEY", "")
        if not self._api_key:
            raise RuntimeError(
                "YarnGPT needs an API key: set tts.yarngpt.api_key in config.yaml "
                "or the YARNGPT_API_KEY environment variable (get one at yarngpt.ai)"
            )
        self.voice = (
            yarn_cfg.get("voice")
            or (getattr(persona, "yarn_voice", None) if persona else None)
            or "Idera"
        )
        self._timeout = float(yarn_cfg.get("timeout", 30))
        self._cache_dir = Path(user_cache_dir("kai", appauthor=False)) / "tts"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        super().__init__()

    # ------------------------------------------------------------ synthesis

    def _cache_path(self, text: str) -> Path:
        digest = hashlib.sha1(f"{self.voice}:{text}".encode("utf-8")).hexdigest()
        return self._cache_dir / f"{self.voice.lower()}-{digest}.wav"

    def _synthesize(self, text: str) -> bytes:
        path = self._cache_path(text)
        if path.exists():
            return path.read_bytes()

        import requests

        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"text": text[:MAX_CHARS], "voice": self.voice, "response_format": "wav"},
            timeout=self._timeout,
        )
        response.raise_for_status()
        audio = response.content
        try:
            path.write_bytes(audio)
        except OSError:
            log.debug("could not cache TTS audio", exc_info=True)
        return audio

    # ------------------------------------------------------------- playback

    def _play(self, wav_bytes: bytes) -> None:
        import numpy as np
        import sounddevice as sd

        with wave.open(io.BytesIO(wav_bytes)) as w:
            frames = w.readframes(w.getnframes())
            dtype = {1: np.uint8, 2: np.int16, 4: np.int32}[w.getsampwidth()]
            data = np.frombuffer(frames, dtype=dtype)
            channels = w.getnchannels()
            if channels > 1:
                data = data.reshape(-1, channels)
            sd.play(data, w.getframerate())
            sd.wait()

    def _speak(self, text: str) -> None:
        self._play(self._synthesize(text))

    def _interrupt(self) -> None:
        import sounddevice as sd

        sd.stop()
