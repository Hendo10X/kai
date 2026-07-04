from kai.audio.wake import matches_wake_phrase
from kai.personas import KAI, PERSONAS, get_persona


def test_kai_persona_is_complete():
    assert set(PERSONAS) == {"kai"}
    assert KAI.acks and KAI.wake_aliases and KAI.greeting
    assert "{text}" in KAI.unknown
    assert "{error}" in KAI.error
    assert KAI.yarn_voice == "Tayo"


def test_lookup_is_case_insensitive_and_safe():
    assert get_persona("Kai") is KAI
    assert get_persona(None) is KAI
    assert get_persona("voldemort") is KAI  # unknown names fall back to Kai


def test_wake_match_exact_and_with_hey():
    assert matches_wake_phrase("kai", KAI.wake_aliases)
    assert matches_wake_phrase("Hey, Kai!", KAI.wake_aliases)
    assert matches_wake_phrase("okay kai", KAI.wake_aliases)


def test_wake_match_fuzzy_mistranscriptions():
    assert matches_wake_phrase("Kye", KAI.wake_aliases)
    assert matches_wake_phrase("hey kay", KAI.wake_aliases)


def test_wake_match_rejects_other_speech():
    assert not matches_wake_phrase("what time is it", KAI.wake_aliases)
    assert not matches_wake_phrase("thank you", KAI.wake_aliases)
    assert not matches_wake_phrase("can you turn the volume up for me please", KAI.wake_aliases)
    assert not matches_wake_phrase("", KAI.wake_aliases)
    assert not matches_wake_phrase("hey edith", KAI.wake_aliases)
