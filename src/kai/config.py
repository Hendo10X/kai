"""YAML-based configuration.

Config lives at <user config dir>/kai/config.yaml and is deep-merged over
built-in defaults, so a user file only needs the keys it overrides.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml
from platformdirs import user_config_dir

APP_NAME = "kai"

DEFAULTS: dict[str, Any] = {
    "persona": "kai",  # only kai for now; more personas can be added later
    "wake_word": {
        "enabled": True,
        "engine": "auto",  # auto | namespot | openwakeword | porcupine
        "keyword": None,  # None = the persona's name; any name works via namespot
        "access_key": "",  # Porcupine only (Picovoice retired its free tier 2026-06)
        "sensitivity": 0.5,
        "spot_model": "tiny.en",  # whisper model used by the namespot engine
        "energy_threshold": None,  # None = auto-calibrate from ambient noise
    },
    "microphone": {
        "device": None,  # None = system default; index or name substring otherwise
    },
    "stt": {
        "model": "base.en",  # any faster-whisper model id
        "device": "cpu",
        "compute_type": "int8",
        "max_seconds": 10,
        "silence_seconds": 1.2,
    },
    "tts": {
        "enabled": True,
        "engine": "pyttsx3",  # pyttsx3 (offline) | yarngpt (Nigerian voices, cloud)
        "rate": 180,
        "volume": 1.0,
        "voice": None,  # substring of a voice name, e.g. "Zira"
        "yarngpt": {
            "api_key": "",  # or env YARNGPT_API_KEY (get one at yarngpt.ai)
            "voice": None,  # None = persona's voice (Tayo/Regina/Wura); else e.g. Idera
            "timeout": 30,
        },
    },
    "push_to_talk": {
        "enabled": True,
        "hotkey": "ctrl+shift+space",
    },
    "apps": {},  # alias -> executable/path, e.g. {"browser": "firefox"}
    "search_url": "https://www.google.com/search?q={query}",
    "commands": [],  # custom commands, see actions/custom.py
    "plugins": {
        "enabled": True,
        "dir": None,  # None = <config dir>/plugins
    },
}


def config_dir() -> Path:
    return Path(user_config_dir(APP_NAME, appauthor=False))


def config_path() -> Path:
    return config_dir() / "config.yaml"


def _deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load config from *path* (default: user config file), merged over defaults."""
    path = path or config_path()
    if path.exists():
        user = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(user, dict):
            raise ValueError(f"Config root must be a mapping: {path}")
        return _deep_merge(DEFAULTS, user)
    return copy.deepcopy(DEFAULTS)


DEFAULT_CONFIG_TEMPLATE = """\
# Kai configuration — every key is optional; unset keys use built-in defaults.

# Your assistant's identity — sets the wake name, voice, and response style.
# Only "kai" for now (casual and quick, wake with "hey kai").
persona: kai

wake_word:
  enabled: true
  engine: auto              # auto | namespot (any name) | openwakeword | porcupine
  keyword: null             # null = your persona's name
  sensitivity: 0.5          # higher = triggers more easily
  spot_model: tiny.en       # whisper model for name spotting (tiny.en = fastest)
  energy_threshold: null    # null = auto-calibrate; run `kai hear` to tune

microphone:
  device: null              # null = system default

stt:
  model: base.en            # tiny.en | base.en | small.en | medium | large-v3
  device: cpu
  compute_type: int8

tts:
  enabled: true
  engine: pyttsx3           # pyttsx3 (offline) | yarngpt (Nigerian voices, cloud API)
  rate: 180
  voice: null               # substring of an installed voice name (pyttsx3 only)
  yarngpt:                  # only used when engine: yarngpt
    api_key: ""             # or set env YARNGPT_API_KEY — get a key at yarngpt.ai
    voice: null             # null = Kai's voice (Tayo); others: Idera, Emma, Zainab,
                            # Osagie, Wura, Jude, Chinenye, Regina, Femi, Adaora,
                            # Umar, Mary, Nonso, Remi, Adam

push_to_talk:
  enabled: true
  hotkey: ctrl+shift+space

# App aliases for "open <name>"
apps:
  # notes: notepad.exe
  # browser: firefox

search_url: "https://www.google.com/search?q={query}"

# Custom voice commands. Each needs a phrase and exactly one action:
#   run:  shell command        open: file/app/url
#   keys: hotkey combo         say:  spoken response
commands:
  # - phrase: deploy status
  #   run: kubectl get pods
  # - phrase: open standup notes
  #   open: "C:/notes/standup.md"
  # - phrase: save everything
  #   keys: ctrl+s
"""


def init_config(force: bool = False) -> Path:
    """Write the starter config file. Returns its path."""
    path = config_path()
    if path.exists() and not force:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
    return path
