"""Microphone capture with simple energy-based end-of-utterance detection."""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)

SAMPLE_RATE = 16_000  # what faster-whisper expects


def _resolve_device(spec: int | str | None) -> int | None:
    if spec is None or isinstance(spec, int):
        return spec
    import sounddevice as sd

    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0 and str(spec).lower() in dev["name"].lower():
            return i
    log.warning("Microphone %r not found; using system default", spec)
    return None


def record_utterance(
    max_seconds: float = 10.0,
    silence_seconds: float = 1.2,
    device: int | str | None = None,
    energy_threshold: float = 0.01,
):
    """Record from the mic until trailing silence or *max_seconds*.

    Returns a float32 numpy array at 16 kHz mono.
    """
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError(
            "Recording requires sounddevice + numpy — install with: pip install kai[voice]"
        ) from exc

    block = int(SAMPLE_RATE * 0.1)  # 100 ms blocks
    max_blocks = int(max_seconds / 0.1)
    silence_blocks_needed = max(1, int(silence_seconds / 0.1))

    chunks: list[np.ndarray] = []
    silent_run = 0
    heard_speech = False

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=block,
        device=_resolve_device(device),
    ) as stream:
        for _ in range(max_blocks):
            data, _overflow = stream.read(block)
            mono = data[:, 0]
            chunks.append(mono.copy())
            rms = float(np.sqrt(np.mean(mono**2)))
            if rms >= energy_threshold:
                heard_speech = True
                silent_run = 0
            else:
                silent_run += 1
                if heard_speech and silent_run >= silence_blocks_needed:
                    break

    return np.concatenate(chunks) if chunks else np.zeros(0, dtype="float32")
