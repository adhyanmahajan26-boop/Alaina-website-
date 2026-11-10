#!/usr/bin/env python3
"""Studio cut-outs for product cards.

The catalogue photos in images/ were shot at every angle and scale. This turns
each one into the same flat-lay: the part lies on one diagonal, fills the same
square with the same margin and carries the same soft shadow, on a transparent
background so the card plate can follow the theme.

    python3 scripts/build_cards.py

Reads  images/<name>.png  (the originals are never modified)
Writes images/cards/<name>.webp (640 px) and images/cards/<name>@2x.webp (1280 px)

Four photos have a backdrop baked in; their cut-out masks live in
scripts/card_masks/. Output is deterministic, so re-running changes nothing.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "images"
OUT = SRC / "cards"
MASKS = Path(__file__).resolve().parent / "card_masks"

ANGLE = 30.0      # degrees above horizontal, rising to the right
PAD = 0.085       # margin, as a share of the canvas
SIZES = (("", 640), ("@2x", 1280))
EXTRA_TURN = {"camry-rear-rh": 180}   # photographed upside down


def premult(im: Image.Image) -> Image.Image:
    a = np.asarray(im, dtype=np.float32)
    a[..., :3] *= a[..., 3:4] / 255.0
    return Image.fromarray(a.round().astype(np.uint8), "RGBA")


def unpremult(im: Image.Image) -> Image.Image:
    a = np.asarray(im, dtype=np.float32)
    al = np.maximum(a[..., 3:4], 1.0)
    a[..., :3] = np.minimum(255.0, a[..., :3] * 255.0 / al)
    return Image.fromarray(a.round().astype(np.uint8), "RGBA")


def axis_angle(alpha: np.ndarray) -> float:
    """Angle of the long axis, degrees, measured counter-clockwise on screen, in (-90, 90]."""
    ys, xs = np.nonzero(alpha > 40)
    if len(xs) > 60000:
        step = len(xs) // 60000 + 1
        xs, ys = xs[::step], ys[::step]
    x = xs - xs.mean()
    y = -(ys - ys.mean())
    cov = np.cov(np.stack([x, y]))
    w, v = np.linalg.eigh(cov)
    vx, vy = v[:, int(np.argmax(w))]
    ang = math.degrees(math.atan2(vy, vx))
    while ang <= -90:
        ang += 180
    while ang > 90:
        ang -= 180
    return ang


def studio(name: str) -> Image.Image:
    im = Image.open(SRC / f"{name}.png").convert("RGBA")
    mask = MASKS / f"{name}.png"
    if mask.exists():
        im.putalpha(Image.open(mask).convert("L").resize(im.size))
    # work at a sane size
    if max(im.size) > 1600:
        im.thumbnail((1600, 1600), Image.LANCZOS)
    alpha = np.asarray(im)[..., 3]
    turn = ANGLE - axis_angle(alpha)
    while turn <= -90:
        turn += 180
    while turn > 90:
        turn -= 180
    turn += EXTRA_TURN.get(name, 0)
    im = premult(im).rotate(turn, resample=Image.BICUBIC, expand=True)
    box = im.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    im = im.crop(box)
    big = SIZES[-1][1]
    room = int(round(big * (1 - 2 * PAD)))
    k = min(room / im.width, room / im.height)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    canvas = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    ox, oy = (big - im.width) // 2, (big - im.height) // 2
    canvas.paste(im, (ox, oy))
    # flat-lay shadow: a wide soft one and a tight contact one, both a little down and right
    a = canvas.getchannel("A")
    out = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    for blur, dx, dy, strength in ((big * 0.030, big * 0.012, big * 0.030, 0.30), (big * 0.008, big * 0.004, big * 0.010, 0.34)):
        sh = Image.new("L", (big, big), 0)
        sh.paste(a, (int(dx), int(dy)))
        sh = sh.filter(ImageFilter.GaussianBlur(blur)).point(lambda v, s=strength: int(v * s))
        layer = Image.new("RGBA", (big, big), (8, 8, 10, 0))
        layer.putalpha(sh)
        out = Image.alpha_composite(out, layer)
    out = Image.alpha_composite(out, unpremult(canvas))
    return out


def main() -> int:
    OUT.mkdir(exist_ok=True)
    # only photos the catalogue uses (each has a WebP sibling from build_webp.py)
    names = sorted(p.stem for p in (SRC / "webp").glob("*.webp") if (SRC / f"{p.stem}.png").exists())
    only = set(sys.argv[1:])
    n = 0
    for name in names:
        if only and name not in only:
            continue
        im = studio(name)
        for suffix, size in SIZES:
            dst = OUT / f"{name}{suffix}.webp"
            v = im if size == im.width else im.resize((size, size), Image.LANCZOS)
            v.save(dst, "WEBP", quality=82, method=6, alpha_quality=90)
        n += 1
    print(f"build_cards: {n} photos -> {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
