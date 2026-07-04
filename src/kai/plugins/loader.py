"""Discover and load plugins from the plugin directory and entry points."""

from __future__ import annotations

import importlib.metadata
import importlib.util
import inspect
import logging
from pathlib import Path

from kai.actions.registry import ActionRegistry
from kai.intent import Context
from kai.plugins.base import KaiPlugin

log = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "kai.plugins"


def _register_module(module, registry: ActionRegistry, ctx: Context, origin: str) -> bool:
    """Wire up one plugin module. Returns True on success."""
    plugin_classes = [
        obj for _, obj in inspect.getmembers(module, inspect.isclass)
        if issubclass(obj, KaiPlugin) and obj is not KaiPlugin
    ]
    try:
        if plugin_classes:
            for cls in plugin_classes:
                cls().register(registry, ctx)
        elif hasattr(module, "register"):
            module.register(registry, ctx)
        else:
            log.warning("Plugin %s has no register() or KaiPlugin subclass", origin)
            return False
    except Exception:
        log.exception("Plugin %s failed to register", origin)
        return False
    log.info("Loaded plugin: %s", origin)
    return True


def load_plugins(registry: ActionRegistry, ctx: Context, plugin_dir: Path | None = None) -> int:
    """Load all plugins. Returns the number successfully loaded."""
    loaded = 0

    # 1. Directory plugins: <config dir>/plugins/*.py
    if plugin_dir and plugin_dir.is_dir():
        for path in sorted(plugin_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(f"kai_plugin_{path.stem}", path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except Exception:
                log.exception("Plugin %s failed to import", path.name)
                continue
            loaded += _register_module(module, registry, ctx, path.name)

    # 2. Installed packages exposing a kai.plugins entry point
    try:
        entry_points = importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)
    except Exception:
        entry_points = []
    for ep in entry_points:
        try:
            module = ep.load()
        except Exception:
            log.exception("Entry point plugin %s failed to import", ep.name)
            continue
        loaded += _register_module(module, registry, ctx, f"{ep.name} ({ep.value})")

    return loaded
