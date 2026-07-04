"""Plugin system (v1 foundation)."""

from kai.plugins.base import KaiPlugin
from kai.plugins.loader import load_plugins

__all__ = ["KaiPlugin", "load_plugins"]
