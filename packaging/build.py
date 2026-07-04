"""Build a standalone Kai executable with PyInstaller.

Run from the repo root: python packaging/build.py
Output: dist/kai.exe (Windows) or dist/kai (macOS/Linux).

The binary bundles the core + desktop + voice (namespot/faster-whisper)
stack. openWakeWord and Porcupine are excluded to keep size down — the
default namespot wake engine doesn't need them. Whisper models still
download to the user's cache on first use.
"""

import sys

import PyInstaller.__main__

args = [
    "packaging/entry.py",
    "--noconfirm",
    "--clean",
    "--onefile",
    "--console",
    "--name", "kai",
    "--paths", "src",
    "--collect-all", "ctranslate2",
    "--collect-all", "faster_whisper",
    "--collect-submodules", "pyttsx3.drivers",
    "--hidden-import", "sounddevice",
    "--hidden-import", "keyboard",
    "--exclude-module", "openwakeword",
    "--exclude-module", "pvporcupine",
    "--exclude-module", "pvrecorder",
    "--exclude-module", "onnxruntime",
]

if sys.platform == "win32":
    args += ["--hidden-import", "comtypes", "--hidden-import", "pyttsx3.drivers.sapi5"]
elif sys.platform == "darwin":
    args += ["--hidden-import", "pyttsx3.drivers.nsss"]
else:
    args += ["--hidden-import", "pyttsx3.drivers.espeak"]

# Forward extra flags, e.g. --workpath/--distpath to build on another drive.
args += sys.argv[1:]

PyInstaller.__main__.run(args)
