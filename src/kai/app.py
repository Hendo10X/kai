"""Application orchestrator: wires config -> registry -> audio -> execution."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from kai import config as config_module
from kai.actions import custom as custom_actions
from kai.actions import dictation, launcher, media, reader, search, system
from kai.actions.registry import ActionRegistry
from kai.intent import Context
from kai.personas import get_persona
from kai.plugins.loader import load_plugins

log = logging.getLogger(__name__)


class KaiApp:
    def __init__(self, config: dict[str, Any] | None = None, enable_tts: bool = True) -> None:
        self.config = config if config is not None else config_module.load_config()
        self.registry = ActionRegistry()
        self.persona = get_persona(self.config.get("persona"))

        speaker = None
        if enable_tts:
            from kai.audio.tts import make_speaker

            speaker = make_speaker(self.config.get("tts", {}), persona=self.persona)
        self.ctx = Context(self.config, speaker=speaker)

        # Built-in action packs
        for pack in (media, launcher, search, dictation, reader, system):
            pack.register(self.registry)

        # User custom commands
        n_custom = custom_actions.register(self.registry, self.config.get("commands", []))
        if n_custom:
            log.info("Registered %d custom command(s)", n_custom)

        # Plugins
        plugins_cfg = self.config.get("plugins", {})
        if plugins_cfg.get("enabled", True):
            plugin_dir = plugins_cfg.get("dir")
            plugin_dir = Path(plugin_dir) if plugin_dir else config_module.config_dir() / "plugins"
            n_plugins = load_plugins(self.registry, self.ctx, plugin_dir)
            if n_plugins:
                log.info("Loaded %d plugin(s)", n_plugins)

    # ------------------------------------------------------------------ text

    def execute(self, text: str) -> str | None:
        """Run one command. In dictation mode, type the text instead —
        unless it's the stop-dictation phrase."""
        if self.ctx.state.get(dictation.DICTATION_KEY):
            match = self.registry.resolve(text)
            if match and match.intent.name == "dictation.stop":
                return match.intent.handler(match.slots, self.ctx)
            dictation.type_text(text + " ")
            return None
        return self.registry.execute(text, self.ctx)

    def respond(self, text: str) -> str:
        """Execute and produce the user-facing/spoken reply."""
        try:
            reply = self.execute(text)
        except LookupError:
            reply = self.persona.unknown.format(text=text)
        except Exception as exc:
            log.exception("Command failed: %s", text)
            reply = self.persona.error.format(error=exc)
        if reply:
            self.ctx.say(reply)
        return reply or ""

    # ----------------------------------------------------------------- voice

    def listen_once(self) -> str:
        """Record one utterance, transcribe it, execute it. Returns the reply."""
        from kai.audio.mic import record_utterance
        from kai.audio.stt import Transcriber

        stt_cfg = self.config.get("stt", {})
        transcriber = self.ctx.state.setdefault("_transcriber", Transcriber(stt_cfg))
        audio = record_utterance(
            max_seconds=float(stt_cfg.get("max_seconds", 10)),
            silence_seconds=float(stt_cfg.get("silence_seconds", 1.2)),
            device=self.config.get("microphone", {}).get("device"),
        )
        text = transcriber.transcribe(audio)
        if not text:
            return ""
        print(f"» {text}")
        return self.respond(text)

    def wake_config(self) -> dict[str, Any]:
        """The wake_word config section with persona name/aliases filled in."""
        wake_cfg = dict(self.config.get("wake_word", {}))
        if not wake_cfg.get("keyword"):
            wake_cfg["keyword"] = self.persona.name
        wake_cfg.setdefault("aliases", list(self.persona.wake_aliases))
        wake_cfg.setdefault("device", self.config.get("microphone", {}).get("device"))
        return wake_cfg

    def run_voice_loop(self) -> None:
        """Main assistant loop: wake word if configured, else push-to-talk."""
        wake_cfg = self.wake_config()
        listener = None
        if wake_cfg.get("enabled", True):
            try:
                from kai.audio.wake import create_listener

                listener = create_listener(wake_cfg)
                print(f"{self.persona.greeting}" if self.persona.tagline else "Ready.")
                print(f"Listening for wake word: '{listener.keyword}' (Ctrl+C to quit)")
            except RuntimeError as exc:
                log.warning("%s — falling back to push-to-talk", exc)

        if listener is not None:
            try:
                while True:
                    listener.wait()
                    print(f"({listener.keyword})")
                    self._acknowledge()
                    self.listen_once()
            finally:
                listener.close()
        else:
            self._run_push_to_talk()

    def _acknowledge(self) -> None:
        """Speak a short persona ack, blocking so it isn't recorded as the command."""
        ack = self.persona.ack()
        if self.ctx.speaker is not None:
            self.ctx.speaker.say_sync(ack, timeout=5.0)
        else:
            print(ack)

    def _run_push_to_talk(self) -> None:
        hotkey = self.config.get("push_to_talk", {}).get("hotkey", "ctrl+shift+space")
        try:
            import keyboard
        except ImportError as exc:
            raise RuntimeError(
                "Push-to-talk requires the 'keyboard' package — "
                "install with: pip install kai[voice]"
            ) from exc
        print(f"Push-to-talk: press {hotkey}, speak, pause (Ctrl+C to quit)")
        while True:
            keyboard.wait(hotkey)
            print("(listening)")
            self.listen_once()
