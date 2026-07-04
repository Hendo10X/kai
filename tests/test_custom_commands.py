from kai.actions import custom
from kai.actions.registry import ActionRegistry
from kai.intent import Context


def test_say_command():
    registry = ActionRegistry()
    n = custom.register(registry, [{"phrase": "hello there", "say": "General Kenobi"}])
    assert n == 1
    reply = registry.execute("hello there", Context({}))
    assert reply == "General Kenobi"


def test_run_command_with_slot(monkeypatch):
    calls = {}

    class FakeResult:
        stdout = "ok\n"
        stderr = ""

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        return FakeResult()

    monkeypatch.setattr(custom.subprocess, "run", fake_run)
    registry = ActionRegistry()
    custom.register(registry, [{"phrase": "ping {host}", "run": "ping -n 1 {host}"}])
    reply = registry.execute("ping example.com", Context({}))
    assert calls["cmd"] == "ping -n 1 example.com"
    assert reply == "ok"


def test_open_command(monkeypatch):
    opened = []
    monkeypatch.setattr(custom, "launch", lambda target: opened.append(target))
    registry = ActionRegistry()
    custom.register(registry, [{"phrase": "open my notes", "open": "C:/notes.md"}])
    registry.execute("open my notes", Context({}))
    assert opened == ["C:/notes.md"]


def test_invalid_entries_skipped():
    registry = ActionRegistry()
    n = custom.register(registry, [
        {"phrase": "no action"},                          # missing action
        {"run": "whoami"},                                # missing phrase
        {"phrase": "two", "run": "a", "say": "b"},        # ambiguous
        {"phrase": "valid", "say": "yes"},
    ])
    assert n == 1
