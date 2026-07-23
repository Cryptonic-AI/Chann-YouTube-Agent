"""
compose_thumbnail.py
----------------------
Takes the AI-generated thumbnail background (no text) and overlays the
bold title/subtitle text using a real font — AI models render text
unreliably, so compositing it separately guarantees it's crisp and
readable.

Input:  data/slides/thumbnail_bg.png
Output: data/slides/thumbnail.png
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")
SLIDES_DIR = os.path.join(BASE_DIR, "data", "slides")
FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "Anton-Regular.ttf")

W, H = 1920, 1080
BLACK = (15, 15, 15)
WHITE = (255, 255, 255)


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def draw_outlined_text(draw, text, center_x, y, font_obj, fill, outline, outline_width=6):
    w = draw.textlength(text, font=font_obj)
    x = center_x - w / 2
    for dx in range(-outline_width, outline_width + 1, 2):
        for dy in range(-outline_width, outline_width + 1, 2):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font_obj, fill=outline)
    draw.text((x, y), text, font=font_obj, fill=fill)


def wrap_text(draw, text, font_obj, max_width):
    words, lines, current = text.split(), [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=font_obj) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def main():
    with open(SCRIPT_PATH, encoding="utf-8") as f:
        script = json.load(f)

    bg_path = os.path.join(SLIDES_DIR, "thumbnail_bg.png")
    img = Image.open(bg_path).convert("RGB").resize((W, H))
    draw = ImageDraw.Draw(img)

    top_lines = wrap_text(draw, script["thumbnail_text_top"], font(110), W - 140)
    y = 50
    for line in top_lines:
        draw_outlined_text(draw, line, W / 2, y, font(110), WHITE, BLACK)
        y += 120

    if script.get("thumbnail_text_bottom"):
        bottom_lines = wrap_text(draw, script["thumbnail_text_bottom"], font(80), W - 140)
        y = H - 110 * len(bottom_lines) - 40
        for line in bottom_lines:
            draw_outlined_text(draw, line, W / 2, y, font(80), WHITE, BLACK)
            y += 95

    img.save(os.path.join(SLIDES_DIR, "thumbnail.png"))
    print("Composed thumbnail.png")


if __name__ == "__main__":
    main()
