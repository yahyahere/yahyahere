#!/usr/bin/env python3
"""Convert a grayscale image into a self-typing monochrome ASCII SVG.

Usage: python scripts/make_ascii_svg.py [image] [output.svg]
Defaults: source-prepped.png, ascii-portrait.svg
Set STATIC=1 to write a frozen frame with no animation.
"""
import os
import sys
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageFilter

RAMP = " .`:-=+*cs#%@"  # dark (blank) -> bright (dense), for light glyphs on a dark panel

WIDTH, HEIGHT = 325, 480  # same height as the info card so the two columns line up
PAD = 14
COLS = 72
FONT_RATIO = 0.6  # monospace glyph width / font size
LINE_RATIO = 1.15  # line height / font size

BG, BORDER, INK, CURSOR = "#0d1117", "#30363d", "#c9d1d9", "#39d353"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"

ROW_DUR = 0.28
ROW_STAGGER = 0.055


def to_rows(path: str) -> tuple[list[str], float, float]:
    inner_w, inner_h = WIDTH - 2 * PAD, HEIGHT - 2 * PAD
    cell_w = inner_w / COLS
    font = cell_w / FONT_RATIO
    line = font * LINE_RATIO

    img = Image.open(path).convert("L")
    max_rows = int(inner_h // line)
    rows = round(COLS * (img.height / img.width) * (cell_w / line))
    cols = COLS
    if rows > max_rows:  # tall image: keep the aspect ratio and centre horizontally
        cols = round(COLS * max_rows / rows)
        rows = max_rows

    # Light sharpening so eyes and glasses survive the shrink. Much more leaves a halo around the head.
    img = img.filter(ImageFilter.UnsharpMask(radius=max(img.width // 150, 2), percent=70, threshold=2))
    img = img.resize((cols, rows), Image.LANCZOS)
    small = np.asarray(img, dtype=np.float32) / 255.0
    small = small ** 1.1  # keep midtones sparse so the face stands out from the clothes
    idx = np.clip((small * len(RAMP)).astype(int), 0, len(RAMP) - 1)
    left = " " * ((COLS - cols) // 2)
    lines = [left + "".join(RAMP[i] for i in row).rstrip() for row in idx]
    return lines, font, line


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    dst = sys.argv[2] if len(sys.argv) > 2 else "ascii-portrait.svg"
    static = os.environ.get("STATIC") == "1"

    rows, font, line = to_rows(src)
    cell_w = font * FONT_RATIO
    y0 = (HEIGHT - line * len(rows)) / 2

    defs, body = [], []
    t = 0.2
    for i, text in enumerate(rows):
        if not text.strip():
            continue
        y = y0 + line * i
        base = y + line * 0.8
        # textLength locks the width, so a different fallback font cannot distort the picture.
        attrs = (
            f'x="{PAD}" y="{base:.2f}" textLength="{len(text) * cell_w:.2f}" '
            f'lengthAdjust="spacing" xml:space="preserve"'
        )
        row_w = len(text) * cell_w
        if static:
            body.append(f"<text {attrs}>{escape(text)}</text>")
            continue
        begin = f"{t:.2f}s"
        defs.append(
            f'<clipPath id="r{i}"><rect x="{PAD}" y="{y:.2f}" width="0" height="{line + 1:.2f}">'
            f'<animate attributeName="width" from="0" to="{row_w:.2f}" begin="{begin}" '
            f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
        )
        body.append(f'<g clip-path="url(#r{i})"><text {attrs}>{escape(text)}</text></g>')
        body.append(
            f'<rect x="{PAD}" y="{y:.2f}" width="{cell_w:.2f}" height="{line:.2f}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + row_w:.2f}" begin="{begin}" '
            f'dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="1" begin="{begin}" dur="{ROW_DUR}s"/></rect>'
        )
        t += ROW_STAGGER

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="ASCII portrait">'
        f'<defs>{"".join(defs)}</defs>'
        f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>'
        f'<g font-family="{FONT}" font-size="{font:.2f}" fill="{INK}">{"".join(body)}</g>'
        "</svg>"
    )
    with open(dst, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {dst}: {len(rows)} rows, {len(svg) // 1024} KB")


if __name__ == "__main__":
    main()
