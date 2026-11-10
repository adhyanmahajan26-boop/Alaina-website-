#!/usr/bin/env python3
"""Square Alaina mark as crawlable favicons at the site root.

The mark is the same one the header uses (scripts/site_chrome.py): an "A" whose
crossbar is a damper rod running out of the letter. Drawn from its geometry, so
no font files are needed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from site_chrome import MARK_INNER  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ACCENT = (255, 74, 26)  # --accent #FF4A1A
WHITE = (255, 255, 255)
INK = (16, 17, 20)
MASTER = 1536
# Same shapes as MARK_INNER, on its 48 x 48 grid.
LETTER = [(10, 37.5), (20.4, 10.5), (27.6, 10.5), (38, 37.5), (31.1, 37.5), (24, 17.6), (16.9, 37.5)]
ROD = [(17.2, 27.2), (40.5, 27.2), (40.5, 31.8), (15.4, 31.8)]


def write_svg() -> None:
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48" role="img" aria-label="Alaina">
  <title>Alaina</title>
  {MARK_INNER}
</svg>
"""
    (ROOT / "favicon.svg").write_text(svg, encoding="utf-8")


def render_mark(size: int) -> Image.Image:
    """Full-bleed square (no rounded corners) so launchers and search results can mask it themselves."""
    img = Image.new("RGB", (size, size), ACCENT)
    draw = ImageDraw.Draw(img)
    k = size / 48
    draw.polygon([(x * k, y * k) for x, y in LETTER], fill=WHITE)
    draw.polygon([(x * k, y * k) for x, y in ROD], fill=INK)
    return img


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
                "description": "Alaina shockers, shock absorbers and cabin dampers. Technical Catalogue No.04.",
                "id": "https://alainashockabsorbers.com/",
                "start_url": "https://alainashockabsorbers.com/",
                "scope": "https://alainashockabsorbers.com/",
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
