"""Kai command-line interface.

    kai run                 full assistant (wake word or push-to-talk)
    kai tray                same, with a system tray icon
    kai listen              one-shot: record, transcribe, execute
    kai exec "open notes"   run a single command from text
    kai repl                interactive text mode (no mic needed)
    kai commands            list everything Kai understands
    kai config [--init]     show or create the config file
"""

from __future__ import annotations

import argparse
import logging
import sys

from kai import __version__
from kai import config as config_module


def _build_app(enable_tts: bool = True):
    from kai.app import KaiApp

    return KaiApp(enable_tts=enable_tts)


def cmd_run(args) -> int:
    app = _build_app()
    try:
        app.run_voice_loop()
    except KeyboardInterrupt:
        print()
    return 0


def cmd_tray(args) -> int:
    from kai.tray import run_with_tray

    run_with_tray(_build_app())
    return 0


def cmd_hear(args) -> int:
    """Wake-word diagnostic: live mic level + what the name spotter hears."""
    app = _build_app(enable_tts=False)
    from kai.audio.wake import NameSpotterListener

    listener = NameSpotterListener(app.wake_config())
    print(f"Wake name: '{listener.keyword}'  aliases: {', '.join(listener.aliases)}")
    print("Speak normally — say the wake name a few times. Ctrl+C to quit.")
    print("Calibrating ambient noise (stay quiet for a second)...")

    counter = [0]

    def on_level(rms: float, threshold: float) -> None:
        counter[0] += 1
        if counter[0] % 3:
            return
        bar = "#" * min(40, int(rms * 800))
        gate = "OPEN " if rms >= threshold else "     "
        print(f"\rlevel {rms:.4f} |{bar:<40}| gate {threshold:.4f} {gate}", end="", flush=True)

    try:
        for text, matched in listener.utterances(on_level=on_level):
            verdict = "WAKE MATCH ✓" if matched else "no match"
            print(f"\nheard: {text!r:40} -> {verdict}")
    except KeyboardInterrupt:
        print()
    return 0


def cmd_listen(args) -> int:
    app = _build_app()
    reply = app.listen_once()
    if reply:
        print(reply)
    return 0


def cmd_exec(args) -> int:
    app = _build_app(enable_tts=not args.quiet)
    reply = app.respond(" ".join(args.text))
    if reply:
        print(reply)
    return 0


def cmd_repl(args) -> int:
    app = _build_app(enable_tts=not args.quiet)
    print(f"Kai {__version__} — type commands, 'help' to list them, Ctrl+C to quit")
    while True:
        try:
            line = input("kai> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return 0
        if not line:
            continue
        if line in ("help", "?"):
            _print_commands(app)
            continue
        if line in ("quit", "exit"):
            return 0
        reply = app.respond(line)
        if reply:
            print(reply)


def _print_commands(app) -> None:
    by_source: dict[str, list] = {}
    for intent in app.registry.list_intents():
        by_source.setdefault(intent.source, []).append(intent)
    for source in sorted(by_source):
        print(f"\n[{source}]")
        for intent in sorted(by_source[source], key=lambda i: i.name):
            patterns = ", ".join(f'"{p}"' for p in intent.patterns[:3])
            print(f"  {intent.name:24} {patterns}")
            if intent.description:
                print(f"  {'':24} {intent.description}")


def cmd_commands(args) -> int:
    _print_commands(_build_app(enable_tts=False))
    return 0


def cmd_config(args) -> int:
    if args.init:
        path = config_module.init_config(force=args.force)
        print(f"Config file: {path}")
    else:
        path = config_module.config_path()
        print(f"Config file: {path} ({'exists' if path.exists() else 'not created yet — run: kai config --init'})")
        if path.exists():
            print()
            print(path.read_text(encoding="utf-8"))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kai",
        description="Kai — local-first voice-powered desktop automation",
    )
    parser.add_argument("--version", action="version", version=f"kai {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("run", help="run the assistant (wake word or push-to-talk)").set_defaults(func=cmd_run)
    sub.add_parser("tray", help="run the assistant with a system tray icon").set_defaults(func=cmd_tray)
    sub.add_parser("listen", help="record and execute a single voice command").set_defaults(func=cmd_listen)
    sub.add_parser("hear", help="wake-word diagnostic: shows mic level and what Kai hears").set_defaults(func=cmd_hear)

    p_exec = sub.add_parser("exec", help="execute a command from text")
    p_exec.add_argument("text", nargs="+", help="the command, e.g. open notepad")
    p_exec.add_argument("-q", "--quiet", action="store_true", help="no speech output")
    p_exec.set_defaults(func=cmd_exec)

    p_repl = sub.add_parser("repl", help="interactive text mode")
    p_repl.add_argument("-q", "--quiet", action="store_true", help="no speech output")
    p_repl.set_defaults(func=cmd_repl)

    sub.add_parser("commands", help="list all registered commands").set_defaults(func=cmd_commands)

    p_cfg = sub.add_parser("config", help="show or create the config file")
    p_cfg.add_argument("--init", action="store_true", help="write the starter config")
    p_cfg.add_argument("--force", action="store_true", help="overwrite an existing config")
    p_cfg.set_defaults(func=cmd_config)

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    try:
        return args.func(args)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
