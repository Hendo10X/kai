"""Action registry: the single place intents are registered and executed.

Built-in packs, user custom commands, and plugins all register through this,
which keeps the execution layer uniform (PRD: Intent Engine -> Action
Registry -> Plugin System -> Execution Layer).
"""

from __future__ import annotations

import logging

from kai.intent import Context, Handler, Intent, IntentEngine, Match

log = logging.getLogger(__name__)


class ActionRegistry:
    def __init__(self) -> None:
        self.engine = IntentEngine()

    def register(
        self,
        name: str,
        patterns: list[str],
        handler: Handler,
        description: str = "",
        source: str = "builtin",
    ) -> Intent:
        intent = Intent(
            name=name, patterns=patterns, handler=handler,
            description=description, source=source,
        )
        self.engine.register(intent)
        return intent

    def resolve(self, text: str) -> Match | None:
        return self.engine.resolve(text)

    def execute(self, text: str, ctx: Context) -> str | None:
        """Resolve *text* and run its handler. Returns the handler's response.

        Raises LookupError when nothing matches so callers can phrase their
        own "not understood" response.
        """
        match = self.resolve(text)
        if match is None:
            raise LookupError(f"No command matches: {text!r}")
        log.info("intent=%s slots=%s", match.intent.name, match.slots)
        return match.intent.handler(match.slots, ctx)

    def list_intents(self) -> list[Intent]:
        return self.engine.intents
