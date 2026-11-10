#!/usr/bin/env python3
"""Copy the Superlift gas spring catalogue from the Mahajan Motors India site.

Alaina does not make gas springs. Superlift is the partner line sold by the same
distributor, and /alaina-x-superlift/ shows its catalogue. The data lives in the
MMI website repo, so this script is run by hand when that catalogue changes:

    python3 scripts/import_superlift.py /path/to/mmi-website/artifacts/mahajan-motors

It writes scripts/superlift.json and WebP photos under images/superlift/. Both are
committed, so scripts/build_seo.py and CI never need the MMI repo. No prices are
copied: this site does not publish list prices.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "images" / "superlift"
MAX_W = 720
# Spelling fixes for names as they appear in the source catalogue. Slugs are left
# alone so links to the matching page on mahajanmotorsindia.com keep working.
MAKE_FIX = {
    "Wolkswagon": "Volkswagen",
    "Mitsubushi": "Mitsubishi",
    "Morris Garage": "MG",
    "KIA": "Kia",
    "GM": "Chevrolet",
    "Zetta": "Jetta",
    "Compaas": "Compass",
    "Mobilo": "Mobilio",
    "Porshe": "Porsche",
    "Supern": "Superb",
    "Breeza": "Brezza",
    "Ecco": "Eeco",
    "Estillo": "Estilo",
}
NOTE_FIX = {"N/M": "New model", "O/M": "Old model"}
BRAND_ASSETS = {
    "brand-identity/superlift-banner.webp": "superlift-banner.webp",
    "brand-videos/superlift-m.mp4": "superlift-film.mp4",
    "brand-videos/superlift-poster.jpg": "superlift-film-poster.jpg",
}


def fix_make(text: str) -> str:
    for bad, good in MAKE_FIX.items():
        text = re.sub(rf"\b{re.escape(bad)}\b", good, text)
    return text


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    mmi = Path(sys.argv[1]).resolve()
    raw = subprocess.run(
        ["node", str(ROOT / "scripts" / "superlift_dump.mjs"), str(mmi)],
        check=True, capture_output=True, text=True,
    ).stdout
    rows = json.loads(raw)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wanted: set[str] = set(BRAND_ASSETS.values())
    done: dict[str, tuple[str, int, int]] = {}
    out = []
    for r in rows:
        img = w = h = None
        if r["img"]:
            src = mmi / "public" / r["img"].lstrip("/")
            if r["img"] in done:
                img, w, h = done[r["img"]]
            elif src.exists():
                name = re.sub(r"[^a-z0-9-]+", "-", src.stem.lower()).strip("-") + ".webp"
                im = Image.open(src).convert("RGB")
                if im.width > MAX_W:
                    im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.Resampling.LANCZOS)
                im.save(OUT_DIR / name, "WEBP", quality=80, method=6)
                img, w, h = f"images/superlift/{name}", im.width, im.height
                done[r["img"]] = (img, w, h)
            if img:
                wanted.add(Path(img).name)
        brand = fix_make(r["brand"])
        car = re.sub(r"^Others ", "", fix_make(r["car"]))
        out.append(
            {
                "pn": r["pn"],
                "car": car,
                "slug": r["slug"],
                "brand": brand,
                "app": r["app"],
                "pos": r["pos"],
                "set": r["set"],
                "note": NOTE_FIX.get(r["note"], r["note"]),
                "oe": r["oe"],
                "img": img or "",
                "w": w or 0,
                "h": h or 0,
                "alt": fix_make(r["alt"]) if r["alt"] else "",
            }
        )
    for src_rel, name in BRAND_ASSETS.items():
        src = mmi / "public" / src_rel
        if src.exists():
            (OUT_DIR / name).write_bytes(src.read_bytes())
    for old in OUT_DIR.iterdir():
        if old.name not in wanted:
            old.unlink()
    (ROOT / "scripts" / "superlift.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=0).replace("\n", "").replace("},{", "},\n{") + "\n",
        encoding="utf-8",
    )
    print(f"superlift: {len(out)} part numbers, {len(done)} photos, {len({r['slug'] for r in out})} cars")


if __name__ == "__main__":
    main()
