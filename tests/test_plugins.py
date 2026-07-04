import textwrap

from kai.actions.registry import ActionRegistry
from kai.intent import Context
from kai.plugins.loader import load_plugins


def test_function_style_plugin(tmp_path):
    (tmp_path / "greeter.py").write_text(textwrap.dedent("""
        def register(registry, ctx):
            registry.register(
                "greeter.hello", ["say hello"],
                lambda slots, ctx: "Hello from plugin!",
                source="greeter",
            )
    """), encoding="utf-8")

    registry = ActionRegistry()
    n = load_plugins(registry, Context({}), tmp_path)
    assert n == 1
    assert registry.execute("say hello", Context({})) == "Hello from plugin!"


def test_class_style_plugin(tmp_path):
    (tmp_path / "clsplug.py").write_text(textwrap.dedent("""
        from kai.plugins import KaiPlugin

        class MyPlugin(KaiPlugin):
            name = "myplugin"
            def register(self, registry, ctx):
                registry.register(
                    "myplugin.ping", ["plugin ping"],
                    lambda slots, ctx: "pong", source=self.name,
                )
    """), encoding="utf-8")

    registry = ActionRegistry()
    n = load_plugins(registry, Context({}), tmp_path)
    assert n == 1
    assert registry.execute("plugin ping", Context({})) == "pong"


def test_broken_plugin_does_not_crash(tmp_path):
    (tmp_path / "broken.py").write_text("raise ImportError('boom')", encoding="utf-8")
    (tmp_path / "good.py").write_text(
        "def register(registry, ctx):\n"
        "    registry.register('good.x', ['good x'], lambda s, c: 'x')\n",
        encoding="utf-8",
    )
    registry = ActionRegistry()
    n = load_plugins(registry, Context({}), tmp_path)
    assert n == 1  # only the good one


def test_underscore_files_ignored(tmp_path):
    (tmp_path / "_helpers.py").write_text("raise RuntimeError('should not import')", encoding="utf-8")
    registry = ActionRegistry()
    assert load_plugins(registry, Context({}), tmp_path) == 0
