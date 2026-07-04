"""Example Kai plugin: "set a timer for {minutes} minutes".

Install by copying into <config dir>/plugins/ (see `kai config` for the path).
"""

import threading


def _set_timer(slots, ctx):
    try:
        minutes = float(slots["minutes"])
    except ValueError:
        return f"'{slots['minutes']}' isn't a number of minutes."

    def fire():
        ctx.say(f"Timer done: {minutes:g} minutes are up.")

    threading.Timer(minutes * 60, fire).start()
    return f"Timer set for {minutes:g} minutes."


def register(registry, ctx):
    registry.register(
        "timer.set",
        ["set a timer for {minutes} minutes", "timer for {minutes} minutes"],
        _set_timer,
        "Set a countdown timer",
        source="timer",
    )
