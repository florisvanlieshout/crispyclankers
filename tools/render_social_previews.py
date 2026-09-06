"""Regenerate the committed share cards; Pillow is an optional authoring dependency.

Usage: python3 tools/render_social_previews.py --font /path/to/bold.ttf
The font must be available locally; deployed pages never fetch it.
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BG, INK, AMBER, MUTED = "#0e0f11", "#f3f1ea", "#f5b642", "#a7a49a"
COPY = {
    "nl": ("Machines die", "het werk echt doen.", "AI-AGENTS + ROBOTS", "Digitaal en fysiek. Grotendeels ongevaarlijk."),
    "en": ("Machines that", "actually do the work.", "AI AGENTS + ROBOTS", "Digital and physical. Mostly harmless."),
}

def render(locale, font_path):
    # Supersample once for crisp type, even when messaging apps shrink the card.
    scale = 2
    image = Image.new("RGB", (1200 * scale, 630 * scale), BG)
    draw = ImageDraw.Draw(image)
    def box(coords, fill, radius=0, outline=None, width=1):
        draw.rounded_rectangle(tuple(int(x * scale) for x in coords), radius=radius * scale,
                               fill=fill, outline=outline, width=width * scale)
    def text(x, y, value, size, fill=INK):
        font = ImageFont.truetype(font_path, size * scale)
        draw.text((x * scale, y * scale), value, font=font, fill=fill, anchor="lt")
    box((0, 0, 1200, 8), AMBER)
    box((45, 44, 1155, 586), None, 26, "#26282c", 2)
    text(80, 84, "Crispy Clankers", 32)
    text(80, 175, COPY[locale][2], 18, AMBER)
    text(76, 229, COPY[locale][0], 58)
    text(76, 305, COPY[locale][1], 58, AMBER)
    text(80, 425, COPY[locale][3], 21, MUTED)
    text(80, 528, "crispyclankers.com", 19)
    # The site's own amber robot mark, enlarged; no third-party imagery.
    box((874, 254, 1114, 440), "#1c1e22", 40)
    box((860, 240, 1100, 426), AMBER, 38)
    box((839, 293, 860, 369), AMBER, 7)
    box((1100, 293, 1121, 369), AMBER, 7)
    box((970, 199, 990, 240), AMBER, 5)
    box((963, 180, 997, 214), AMBER, 17)
    box((904, 294, 944, 334), BG, 20)
    box((1016, 294, 1056, 334), BG, 20)
    box((928, 368, 1032, 383), BG, 7)
    image = image.resize((1200, 630), Image.Resampling.LANCZOS)
    dest = ROOT / "assets" / f"social-preview-{locale}-v1.png"
    dest.parent.mkdir(exist_ok=True)
    image.save(dest, optimize=True)
    print(f"{dest.name}: {dest.stat().st_size} bytes")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", required=True, help="Path to a locally installed bold TrueType/OpenType font")
    args = parser.parse_args()
    for locale in COPY:
        render(locale, args.font)
