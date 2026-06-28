#!/usr/bin/env python3
"""Render one line (or wrapped block) of text to a transparent PNG for ffmpeg overlay.

Use this when ffmpeg was built without drawtext (no libfreetype). Render the PNG,
then composite with ffmpeg `overlay`.

Features:
  - Font auto-fallback (PingFang / Arial Unicode / Noto CJK / DejaVu) so CJK text works
    on macOS and Linux without hardcoding one font.
  - Auto-wrap long text to a max width fraction; multi-line, bottom-anchored, centered.
  - Configurable canvas (supports vertical 9:16, e.g. --canvas 1080x1920).
  - Dark outline by default for readability of white text on bright footage.

Usage:
  render_text.py "字幕文字" out.png [--size 60] [--color white|#0023ff]
                 [--canvas 1920x1080] [--from-bottom 170] [--max-width 0.84]
                 [--outline black] [--font /path/to/font]
"""
import argparse, sys, os
from PIL import Image, ImageDraw, ImageFont

# Font candidates, first existing wins. Covers macOS + common Linux.
FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

def pick_font(explicit):
    for p in ([explicit] if explicit else []) + FONT_CANDIDATES:
        if p and os.path.exists(p):
            return p
    sys.exit("No usable font found. Pass --font /path/to/a/font.")

def parse_color(c):
    if c.startswith("#"):
        c = c[1:]
        return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)
    return {"white": (255, 255, 255, 255), "black": (0, 0, 0, 255)}.get(c, (255, 255, 255, 255))

def wrap(text, font, draw, max_px):
    """Greedy wrap. Works for CJK (no spaces) and spaced text."""
    if draw.textlength(text, font=font) <= max_px:
        return [text]
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) <= max_px or not cur:
            cur += ch
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text"); ap.add_argument("out")
    ap.add_argument("--size", type=int, default=60)
    ap.add_argument("--color", default="white")
    ap.add_argument("--canvas", default="1920x1080")
    ap.add_argument("--from-bottom", type=int, default=170)
    ap.add_argument("--max-width", type=float, default=0.84)  # fraction of canvas width
    ap.add_argument("--outline", default="black")
    ap.add_argument("--font", default=None)
    a = ap.parse_args()

    W, H = (int(x) for x in a.canvas.lower().split("x"))
    try:
        font = ImageFont.truetype(pick_font(a.font), a.size)
    except Exception:
        font = ImageFont.truetype(pick_font(a.font), a.size, index=0)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lines = wrap(a.text, font, d, W * a.max_width)

    asc, desc = font.getmetrics()
    line_h = asc + desc
    gap = int(line_h * 0.18)
    block_h = len(lines) * line_h + (len(lines) - 1) * gap
    y0 = H - getattr(a, "from_bottom") - block_h

    fill = parse_color(a.color)
    oc = parse_color(a.outline); oc = (oc[0], oc[1], oc[2], 175)
    for i, ln in enumerate(lines):
        lw = d.textlength(ln, font=font)
        x = (W - lw) / 2
        y = y0 + i * (line_h + gap)
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    d.text((x + dx, y + dy), ln, font=font, fill=oc)
        d.text((x, y), ln, font=font, fill=fill)
    img.save(a.out)
    print("ok", a.out, f"({len(lines)} line(s), {W}x{H})")

if __name__ == "__main__":
    main()
