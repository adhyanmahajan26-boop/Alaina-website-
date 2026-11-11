"""Encode the vehicle film frames (films.py) into the site: seq/film/<prefix><nnn>.webp, plus a still for each film.

usage: encode_films.py <frames dir> seq [--size 720]

The films are rendered on a dark studio floor, not on a transparent background, so each frame is melted into the
page colour at its edges here; on the page a soft mask finishes the job.
"""
import sys, os, glob
import numpy as np
from PIL import Image

BG = np.array([10, 10, 11], dtype=np.float32)        # --deep in style.css
STILLS = {'c': 'car', 'x': 'axle', 'q': 'rear'}                    # last frame of the film: shown before it loads, and with motion off


def edge_weight(n, margin=0.13, bottom=0.15):
    """1 in the middle of the frame, easing to 0 at the edges (a deeper fade at the bottom, where the floor runs out)."""
    def ease(d, m):
        t = np.clip(d / m, 0, 1)
        return t * t * (3 - 2 * t)
    a = (np.arange(n) + 0.5) / n
    wx = ease(np.minimum(a, 1 - a), margin)
    wy = np.minimum(ease(a, margin), ease(1 - a, bottom))
    return np.outer(wy, wx)[..., None].astype(np.float32)


def melt(im):
    a = np.asarray(im.convert('RGB'), dtype=np.float32)
    w = edge_weight(a.shape[0])
    a = np.maximum(a, BG)                       # never darker than the page
    a = BG + (a - BG) * w
    return Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8))


def main():
    src, dst = sys.argv[1], sys.argv[2]
    size = int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 720
    os.makedirs(f'{dst}/film', exist_ok=True)
    tot = {}
    last = {}
    for f in sorted(glob.glob(src + '/[cbxq][0-9][0-9][0-9].png')):
        name = os.path.basename(f)[:-4]
        out = f'{dst}/film/{name}.webp'
        if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(f):
            im = Image.open(f)
            if im.width != size: im = im.resize((size, size), Image.LANCZOS)
            melt(im).save(out, 'WEBP', quality=70, method=6)
        tot[name[0]] = tot.get(name[0], 0) + os.path.getsize(out)
        last[name[0]] = f
    for p, f in last.items():
        if p in STILLS:
            im = Image.open(f)
            if im.width != 800: im = im.resize((800, 800), Image.LANCZOS)
            melt(im).save(f'{dst}/{STILLS[p]}.webp', 'WEBP', quality=80, method=6)
    print({k: round(v / 1e6, 2) for k, v in tot.items()}, 'MB')


if __name__ == '__main__':
    main()
