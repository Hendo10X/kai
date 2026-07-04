"""System tray icon (pystray): status + quick actions while the loop runs."""

from __future__ import annotations

import threading


def _make_icon_image():
    from PIL import Image, ImageDraw

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=(30, 30, 46, 255))
    # Simple microphone glyph
    draw.rounded_rectangle([26, 14, 38, 36], radius=6, fill=(166, 227, 161, 255))
    draw.arc([20, 22, 44, 44], start=0, end=180, fill=(166, 227, 161, 255), width=3)
    draw.line([32, 44, 32, 50], fill=(166, 227, 161, 255), width=3)
    return img


def run_with_tray(app) -> None:
    """Run the voice loop with a tray icon. Blocks until Quit."""
    try:
        import pystray
    except ImportError as exc:
        raise RuntimeError(
            "Tray mode requires pystray + pillow — install with: pip install kai[desktop]"
        ) from exc

    stop = threading.Event()

    def on_listen(icon, item) -> None:
        threading.Thread(target=app.listen_once, daemon=True).start()

    def on_quit(icon, item) -> None:
        stop.set()
        icon.stop()

    icon = pystray.Icon(
        "kai",
        icon=_make_icon_image(),
        title="Kai — voice automation",
        menu=pystray.Menu(
            pystray.MenuItem("Listen now", on_listen),
            pystray.MenuItem("Quit", on_quit),
        ),
    )

    loop = threading.Thread(target=app.run_voice_loop, daemon=True, name="kai-voice")
    loop.start()
    icon.run()  # blocks until Quit
