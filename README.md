# Kai

**Local-first, voice-powered desktop automation.** Control your computer with natural voice commands — no cloud, no accounts, no data leaving your machine.

```
Wake Word → Speech Recognition → Intent Engine → Action Registry → Plugin System → Execution Layer
```

Everything runs locally: openWakeWord for wake-word detection (no account or API key needed), faster-whisper for speech recognition, your OS's own voices for speech output.

## Download

Standalone builds — no Python needed:

- [Windows (x64)](https://github.com/Hendo10X/kai/releases/latest/download/kai-windows-x64.exe)
- [macOS (Apple Silicon)](https://github.com/Hendo10X/kai/releases/latest/download/kai-macos-arm64)
- [macOS (Intel)](https://github.com/Hendo10X/kai/releases/latest/download/kai-macos-x64)
- [Linux (x64)](https://github.com/Hendo10X/kai/releases/latest/download/kai-linux-x64)

Run `kai run` from a terminal (macOS: `chmod +x kai-macos-*` first, and on first launch right-click → Open to get past Gatekeeper since builds are unsigned). The Whisper speech model downloads automatically on first use.

## Install from source

```bash
# Core (text mode — works everywhere, no audio needed)
pip install -e .

# + desktop actions (media keys, typing, screenshots, TTS, tray icon)
pip install -e ".[desktop]"

# + voice (wake word, local speech recognition, push-to-talk)
pip install -e ".[voice]"
```

Or with pipx: `pipx install ".[desktop,voice]"`.

## Wake word & voice

Wake Kai by saying **"hey kai"**. The default wake engine (`namespot`) transcribes short speech snippets with a tiny local Whisper model and fuzzy-matches the name — accent-tolerant, and any wake name works via `wake_word.keyword`. Alternatives: `openwakeword` (lower CPU, but limited to its pre-trained phrases like "hey jarvis") and `porcupine` (needs a Picovoice key; the free tier was retired in June 2026 — install `.[porcupine]`). Run `kai hear` to see live mic levels and what the spotter hears.

**Nigerian voices:** set `tts.engine: yarngpt` and add an API key from [yarnpgt.ai](https://www.yarngpt.ai) to have Kai speak with a Nigerian-accented voice (Tayo by default; pick any of YarnGPT's 16 voices with `tts.yarngpt.voice`). Note this sends Kai's *replies* to the YarnGPT cloud API (never your microphone audio); synthesized clips are cached locally so repeated phrases cost one call. The default `pyttsx3` engine remains fully offline.

## Quick start

```bash
kai config --init      # create the config file
kai repl               # try it in text mode first
kai run                # full assistant: say "hey kai", then your command
kai tray               # same, minimized to the system tray
```

Things to say (or type):

| You say | Kai does |
|---|---|
| `open firefox` | launches the app |
| `search for rust lifetimes` | opens a web search |
| `next track` / `pause` / `volume up` | media keys |
| `type hello world` | types into the focused window |
| `start dictation` … `stop dictation` | types everything you say |
| `read clipboard` | reads it aloud |
| `take a screenshot` | saves to Pictures/kai |
| `lock screen` / `what time is it` | system controls |

`kai commands` lists everything, including your custom commands and plugins.

## Custom commands

Edit the config file (`kai config` shows the path):

```yaml
commands:
  - phrase: deploy status
    run: kubectl get pods
  - phrase: open standup notes
    open: "C:/notes/standup.md"
  - phrase: save everything
    keys: ctrl+shift+s
  - phrase: ping {host}
    run: "ping -n 1 {host}"
```

Each command needs a `phrase` (with optional `{slots}`) and exactly one action: `run` (shell), `open` (file/app/URL), `keys` (hotkey), or `say` (response).

## Plugins

Drop a `.py` file into `<config dir>/plugins/`:

```python
def register(registry, ctx):
    registry.register(
        "greeter.hello", ["say hello"],
        lambda slots, ctx: "Hello from my plugin!",
        source="greeter",
    )
```

See [examples/plugins/timer.py](examples/plugins/timer.py) for a slot-based example. Installed packages can also register via the `kai.plugins` entry-point group.

## Configuration

`kai config --init` writes a commented starter file. Highlights:

```yaml
persona: kai
wake_word:
  engine: auto              # namespot (any name) | openwakeword | porcupine
  sensitivity: 0.5          # higher = triggers more easily
stt:
  model: base.en            # tiny.en for speed, small.en for accuracy
push_to_talk:
  hotkey: ctrl+shift+space
apps:
  notes: notepad.exe        # aliases for "open notes"
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

Layout:

```
src/kai/
  intent.py        # pattern → intent matching (no cloud, no LLM)
  config.py        # YAML config, deep-merged over defaults
  app.py           # orchestrator: wires the whole pipeline
  cli.py           # kai run/tray/listen/exec/repl/commands/config
  actions/         # action registry + built-in packs
  audio/           # wake word, STT, TTS, mic — all optional at runtime
  plugins/         # plugin base class + loader
```

## Roadmap

V1 core assistant (this) → V1.5 context awareness & custom commands → V2 plugin SDK → V2.5 workflow engine → V3 optional local LLM → V4 community marketplace.

## License

MIT
