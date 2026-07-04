"""Plugin API.

A plugin is either:

1. A module exposing ``register(registry, ctx)`` — the simple form, or
2. A subclass of :class:`KaiPlugin` named in the module.

Distribution: drop a ``.py`` file into ``<config dir>/plugins/``, or ship a
package with a ``kai.plugins`` entry point.
"""

from __future__ import annotations

from kai.actions.registry import ActionRegistry
from kai.intent import Context


class KaiPlugin:
    """Base class for class-style plugins."""

    name: str = "unnamed"
    version: str = "0.0.0"

    def register(self, registry: ActionRegistry, ctx: Context) -> None:
        """Register intents/actions. Called once at startup."""
        raise NotImplementedError
