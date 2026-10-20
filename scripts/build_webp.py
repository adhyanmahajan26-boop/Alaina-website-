#!/usr/bin/env python3
"""Write pixel-identical (lossless) WebP copies of every catalogue photo to images/webp/.

The 2026-10-13 fix removed lossy WebP because it flattened transparent PNGs onto
grey and softened the photos. These copies are lossless: every visible pixel and
the whole alpha channel decode back to the original PNG. Only the hidden colour
of fully transparent pixels is dropped, which no browser ever shows. The build
checks that before it keeps a copy, and skips any copy that is not smaller.

Originals stay untouched and remain what the sitemaps, og:image and JSON-LD use.

    python3 scripts/build_webp.py          # convert new or changed photos
    python3 scripts/build_webp.py --verify # re-check every copy against its PNG
    python3 scripts/build_webp.py --force  # re-encode every copy
"""
from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEBP_DIR = ROOT / "images" / "webp"


def webp_path(img: str) -> Path:
    return WEBP_DIR / (Path(img).stem + ".webp")


def photo_list() -> list[str]:
    text = (ROOT / "index.html").read_text(encoding="utf-8")
    products = json.loads(re.search(r"const PRODUCTS = (\[.*?\]);", text).group(1))
    imgs = {p["img"] for p in products if p.get("img")}
    return sorted(i for i in imgs if (ROOT / i).exists())


def same_pixels(src: Path, dest: Path) -> bool:
    """Same alpha everywhere and same colour wherever the pixel is not fully transparent."""
    import numpy as np
    from PIL import Image

    with Image.open(src) as a, Image.open(dest) as b:
        a = np.asarray(a.convert("RGBA"))
        b = np.asarray(b.convert("RGBA"))
    if a.shape != b.shape or not np.array_equal(a[..., 3], b[..., 3]):
        return False
    seen = a[..., 3] > 0
    return np.array_equal(a[..., :3][seen], b[..., :3][seen])


def convert(img: str) -> tuple[str, str]:
    from PIL import Image

    src = ROOT / img
    dest = webp_path(img)
    if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime and not {"--verify", "--force"} & set(sys.argv):
        return img, "kept"
    if "--force" in sys.argv or not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
        with Image.open(src) as im:
            im.save(dest, "WEBP", lossless=True, quality=100, method=6)
    if not same_pixels(src, dest):
        dest.unlink()
        return img, "FAILED pixel check, removed"
    if dest.stat().st_size >= src.stat().st_size:
        dest.unlink()
        return img, "not smaller, removed"
    return img, f"{src.stat().st_size // 1024} KB -> {dest.stat().st_size // 1024} KB"


def main() -> None:
    WEBP_DIR.mkdir(parents=True, exist_ok=True)
    imgs = photo_list()
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(convert, imgs))
    for img, status in results:
        print(f"{img}: {status}")
    failed = [i for i, s in results if s.startswith("FAILED")]
    if failed:
        raise SystemExit(f"{len(failed)} WebP copies did not match their PNG")


if __name__ == "__main__":
    main()
