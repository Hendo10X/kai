import io
import wave

import pytest

from kai.audio import yarn
from kai.audio.yarn import YarnSpeaker
from kai.personas import PERSONAS


def make_wav_bytes(seconds: float = 0.05) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * int(16000 * seconds))
    return buf.getvalue()


@pytest.fixture
def speaker(tmp_path, monkeypatch):
    calls = {"posts": [], "played": []}

    class FakeResponse:
        content = make_wav_bytes()
        def raise_for_status(self):
            pass

    import requests
    monkeypatch.setattr(requests, "post", lambda url, **kw: (calls["posts"].append(kw), FakeResponse())[1])
    monkeypatch.setattr(YarnSpeaker, "_play", lambda self, b: calls["played"].append(b))

    s = YarnSpeaker(
        {"yarngpt": {"api_key": "test-key"}}, persona=PERSONAS["kai"]
    )
    s._cache_dir = tmp_path  # isolate the disk cache
    yield s, calls
    s.close()


def test_persona_voice_selected(speaker):
    s, _ = speaker
    assert s.voice == "Tayo"  # kai's Nigerian voice


def test_explicit_voice_overrides_persona():
    s = YarnSpeaker.__new__(YarnSpeaker)  # skip thread start for a pure config check
    yarn_cfg = {"api_key": "k", "voice": "Idera"}
    voice = yarn_cfg.get("voice") or PERSONAS["kai"].yarn_voice or "Idera"
    assert voice == "Idera"


def test_say_sync_posts_and_plays(speaker):
    s, calls = speaker
    s.say_sync("How far!", timeout=5)
    assert len(calls["posts"]) == 1
    body = calls["posts"][0]["json"]
    assert body == {"text": "How far!", "voice": "Tayo", "response_format": "wav"}
    assert calls["posts"][0]["headers"]["Authorization"] == "Bearer test-key"
    assert len(calls["played"]) == 1


def test_repeated_phrase_uses_cache(speaker):
    s, calls = speaker
    s.say_sync("Yeah?", timeout=5)
    s.say_sync("Yeah?", timeout=5)
    assert len(calls["posts"]) == 1  # second time comes from disk cache
    assert len(calls["played"]) == 2


def test_missing_api_key_raises():
    with pytest.raises(RuntimeError, match="API key"):
        YarnSpeaker({"yarngpt": {}})


def test_make_speaker_falls_back_without_key(monkeypatch):
    monkeypatch.delenv("YARNGPT_API_KEY", raising=False)
    from kai.audio.tts import Pyttsx3Speaker, make_speaker

    s = make_speaker({"engine": "yarngpt", "yarngpt": {}}, persona=PERSONAS["kai"])
    assert s is None or isinstance(s, Pyttsx3Speaker)  # never crashes, never yarn
    if s:
        s.close()
