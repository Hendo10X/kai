from kai.intent import Context, Intent, IntentEngine, compile_pattern, normalize


def make_intent(name, patterns):
    return Intent(name=name, patterns=patterns, handler=lambda s, c: name)


def test_normalize_strips_punctuation_and_case():
    assert normalize("  Open, Firefox!  ") == "open firefox"


def test_normalize_keeps_word_internal_punctuation():
    assert normalize("Search for example.com.") == "search for example.com"
    assert normalize("What's at 5:30?") == "whats at 5:30"


def test_exact_phrase_match():
    engine = IntentEngine()
    engine.register(make_intent("media.next", ["next track", "next song"]))
    match = engine.resolve("Next song.")
    assert match is not None
    assert match.intent.name == "media.next"
    assert match.slots == {}


def test_slot_extraction():
    engine = IntentEngine()
    engine.register(make_intent("launcher.open", ["open {app}"]))
    match = engine.resolve("open visual studio code")
    assert match is not None
    assert match.slots == {"app": "visual studio code"}


def test_multiple_slots():
    pattern = compile_pattern("remind me to {task} at {time}")
    m = pattern.match(normalize("remind me to stretch at 5 pm"))
    assert m is not None
    assert m.group("task") == "stretch"
    assert m.group("time") == "5 pm"


def test_specific_pattern_beats_generic_slot():
    engine = IntentEngine()
    engine.register(make_intent("launcher.open", ["open {app}"]))
    engine.register(make_intent("notes.open", ["open standup notes"]))
    match = engine.resolve("open standup notes")
    assert match.intent.name == "notes.open"
    # generic still works for everything else
    assert engine.resolve("open firefox").intent.name == "launcher.open"


def test_no_match_returns_none():
    engine = IntentEngine()
    engine.register(make_intent("media.next", ["next track"]))
    assert engine.resolve("make me a sandwich") is None
    assert engine.resolve("") is None


def test_duplicate_registration_rejected():
    engine = IntentEngine()
    engine.register(make_intent("a", ["x"]))
    try:
        engine.register(make_intent("a", ["y"]))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_context_say_without_speaker_is_noop():
    ctx = Context(config={})
    ctx.say("hello")  # must not raise
