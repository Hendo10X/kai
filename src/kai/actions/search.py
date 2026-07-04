"""Web search: "search for {query}"."""

from __future__ import annotations

import urllib.parse
import webbrowser

from kai.actions.registry import ActionRegistry
from kai.intent import Context


def _search(slots: dict[str, str], ctx: Context) -> str:
    query = slots["query"]
    url_template = ctx.config.get("search_url", "https://www.google.com/search?q={query}")
    webbrowser.open(url_template.format(query=urllib.parse.quote_plus(query)))
    return f"Searching for {query}"


def register(registry: ActionRegistry) -> None:
    registry.register(
        "search.web",
        ["search for {query}", "search {query}", "google {query}", "look up {query}"],
        _search,
        "Search the web in the default browser",
    )
