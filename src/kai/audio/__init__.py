"""Audio layer: wake word, speech-to-text, text-to-speech, microphone.

Everything here degrades gracefully — each component raises a clear
RuntimeError naming the missing optional dependency (`pip install kai[voice]`
/ `kai[desktop]`) instead of failing at import time, so the text-mode core
works without any audio hardware or ML models.
"""
