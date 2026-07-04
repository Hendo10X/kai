from kai.actions import dictation
from kai.app import KaiApp
from kai.config import DEFAULTS


def make_app(**overrides):
    cfg = {**DEFAULTS, **overrides, "plugins": {"enabled": False}}
    return KaiApp(config=cfg, enable_tts=False)


def test_builtin_intents_registered():
    app = make_app()
    names = {i.name for i in app.registry.list_intents()}
    for expected in (
        "media.play_pause", "launcher.open", "search.web",
        "dictation.start", "reader.clipboard", "system.time",
    ):
        assert expected in names


def test_respond_unknown_command_uses_persona_flavor():
    app = make_app()  # default persona: kai
    reply = app.respond("frobnicate the widget")
    assert reply == "No idea what 'frobnicate the widget' means, boss."


def test_missing_persona_falls_back_to_kai():
    app = make_app(persona=None)
    assert app.persona.name == "kai"


def test_time_command_end_to_end():
    app = make_app()
    reply = app.respond("what time is it")
    assert ":" in reply


def test_custom_command_from_config():
    app = make_app(commands=[{"phrase": "test phrase", "say": "test response"}])
    assert app.respond("test phrase") == "test response"


def test_dictation_mode_types_instead_of_executing(monkeypatch):
    typed = []
    monkeypatch.setattr(dictation, "type_text", lambda t: typed.append(t))
    app = make_app()
    app.respond("start dictation")
    assert app.ctx.state[dictation.DICTATION_KEY] is True
    app.respond("what time is it")  # would normally be a command
    assert typed == ["what time is it "]
    reply = app.respond("stop dictation")
    assert app.ctx.state[dictation.DICTATION_KEY] is False
    assert "off" in reply.lower()
