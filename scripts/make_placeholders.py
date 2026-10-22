"""Create simple JPEG placeholders so the gallery works without stock photos."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PALETTES = [
    ("counter.jpg", (62, 39, 28), (196, 149, 110), "The morning counter"),
    ("pour.jpg", (48, 32, 24), (232, 196, 148), "A slow pour-over"),
    ("breakfast.jpg", (90, 58, 36), (244, 224, 196), "Eggs, toast, and light"),
    ("seats.jpg", (36, 44, 38), (168, 186, 164), "Window seats"),
]


def ensure_placeholders(upload_dir: Path):
    upload_dir.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.load_default()
    except OSError:
        font = None

    for filename, bg, fg, caption in PALETTES:
        path = upload_dir / filename
        if path.exists():
            continue
        img = Image.new("RGB", (1200, 800), bg)
        draw = ImageDraw.Draw(img)
        draw.rectangle([80, 80, 1120, 720], outline=fg, width=4)
        draw.text((120, 360), caption, fill=fg, font=font)
        img.save(path, "JPEG", quality=88)
