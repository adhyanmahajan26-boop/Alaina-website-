#!/usr/bin/env python3
"""Square Alaina 'A' mark as crawlable favicons at the site root."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
ACCENT = (255, 74, 26, 255)  # --accent #FF4A1A from style.css .brand-mark
WHITE = (255, 255, 255, 255)
FONT = Path("/usr/share/fonts/truetype/macos/Inter-Bold.ttf")
MASTER = 1024


def glyph_svg_path(view: int = 32, pad_ratio: float = 0.18) -> str:
    font = TTFont(str(FONT))
    gs = font.getGlyphSet()
    g = gs["A"]
    bp = BoundsPen(gs)
    g.draw(bp)
    xmin, ymin, xmax, ymax = bp.bounds
    w, h = xmax - xmin, ymax - ymin
    inner = view * (1 - 2 * pad_ratio)
    scale = inner / max(w, h)
    dx = (view - w * scale) / 2 - xmin * scale
    # SVG Y is down; font Y is up
    dy = (view - h * scale) / 2 + ymax * scale
    pen = SVGPathPen(gs)
    g.draw(TransformPen(pen, Transform(scale, 0, 0, -scale, dx, dy)))
    return pen.getCommands()


def write_svg() -> None:
    d = glyph_svg_path()
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32" role="img" aria-label="Alaina">
  <title>Alaina</title>
  <rect width="32" height="32" fill="#FF4A1A"/>
  <path fill="#FFFFFF" d="{d}"/>
</svg>
"""
    (ROOT / "favicon.svg").write_text(svg, encoding="utf-8")


def render_mark(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), ACCENT)
    draw = ImageDraw.Draw(img)
    # Match .brand-mark: heavy A, optically centred in the orange square
    font_size = int(size * 0.72)
    font = ImageFont.truetype(str(FONT), font_size)
    bbox = draw.textbbox((0, 0), "A", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1] - size * 0.02
    draw.text((x, y), "A", font=font, fill=WHITE)
    return img.convert("RGB")


def write_rasters() -> None:
    master = render_mark(MASTER)
    mapping = {
        "favicon-48x48.png": 48,
        "apple-touch-icon.png": 180,
        "favicon-192x192.png": 192,
        "favicon-512x512.png": 512,
    }
    for name, size in mapping.items():
        master.resize((size, size), Image.Resampling.LANCZOS).save(ROOT / name, "PNG", optimize=True)

    master.save(
        ROOT / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
    )


def write_manifest() -> None:
    (ROOT / "site.webmanifest").write_text(
        json.dumps(
            {
                "name": "Alaina Shockers",
                "short_name": "Alaina",
                "description": "Cabin dampers, shock absorbers and rare struts. Technical Catalogue No.04.",
                "start_url": "/",
                "scope": "/",
                "display": "browser",
                "lang": "en-IN",
                "background_color": "#0A0A0B",
                "theme_color": "#FF4A1A",
                "icons": [
                    {
                        "src": "/favicon-192x192.png",
                        "sizes": "192x192",
                        "type": "image/png",
                        "purpose": "any",
                    },
                    {
                        "src": "/favicon-512x512.png",
                        "sizes": "512x512",
                        "type": "image/png",
                        "purpose": "any",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


FAVICON_LINKS = """<link rel="icon" href="/favicon.ico" sizes="48x48"/>
<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48x48.png"/>
<link rel="icon" type="image/svg+xml" href="/favicon.svg"/>
<link rel="icon" type="image/png" sizes="192x192" href="/favicon-192x192.png"/>
<link rel="icon" type="image/png" sizes="512x512" href="/favicon-512x512.png"/>
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png"/>
<link rel="manifest" href="/site.webmanifest"/>
<meta name="theme-color" content="#FF4A1A"/>"""


def main() -> None:
    write_svg()
    write_rasters()
    write_manifest()
    print("wrote favicon.ico svg pngs apple-touch-icon site.webmanifest")


if __name__ == "__main__":
    main()
