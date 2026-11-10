"""Encode rendered PNG frames into the site's seq/ folder (two sizes, WebP with alpha).

usage: encode.py <frames dir> seq
       encode.py --partner <partner.png> images     (writes partner-x.webp and partner-x-720.webp)
"""
import sys, os, glob
from PIL import Image
if sys.argv[1] == '--partner':
    im = Image.open(sys.argv[2]).convert('RGBA')
    im.save(sys.argv[3] + '/partner-x.webp', quality=84, method=6)
    im.resize((720, 720), Image.LANCZOS).save(sys.argv[3] + '/partner-x-720.webp', quality=80, method=6)
    sys.exit()
src, dst = sys.argv[1], sys.argv[2]
for size, q in ((720, 74), (1080, 78)):
    os.makedirs(f'{dst}/{size}', exist_ok=True)
tot = {720: 0, 1080: 0}; n = 0
for f in sorted(glob.glob(src + '/*.png')):
    name = os.path.basename(f)[:-4]
    for size, q in ((720, 74), (1080, 78)):
        out = f'{dst}/{size}/{name}.webp'
        if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(f):
            im = Image.open(f).convert('RGBA')
            if size != im.width: im = im.resize((size, size), Image.LANCZOS)
            im.save(out, 'WEBP', quality=q, method=6, alpha_quality=88)
        tot[size] += os.path.getsize(out)
    n += 1
# stills shown before the frames arrive, and kept when motion is switched off
for frame, still in (('h04', 'poster'), ('k15', 'shock'), ('t15', 'strut')):
    if os.path.exists(f'{src}/{frame}.png'):
        im = Image.open(f'{src}/{frame}.png').convert('RGBA')
        im.save(f'{dst}/{still}.webp', 'WEBP', quality=80, method=6, alpha_quality=90)
print(n, 'frames', {k: round(v / 1e6, 2) for k, v in tot.items()}, 'MB')
