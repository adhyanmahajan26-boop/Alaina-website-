"""Contact sheets for rendered films: one <prefix>_sheet.jpg per film prefix found in the frames folder.

usage: python contact.py <frames dir> [--cols 10] [--thumb 288]
"""
import sys, os, glob, re
from PIL import Image, ImageDraw


def main():
    src = sys.argv[1]
    cols = int(sys.argv[sys.argv.index('--cols') + 1]) if '--cols' in sys.argv else 10
    tw = int(sys.argv[sys.argv.index('--thumb') + 1]) if '--thumb' in sys.argv else 288
    films = {}
    for p in sorted(glob.glob(os.path.join(src, '*.png'))):
        m = re.match(r'([a-z])(\d{3})\.png$', os.path.basename(p))
        if m: films.setdefault(m.group(1), []).append(p)
    for k, ps in films.items():
        rows = (len(ps) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * tw, rows * tw), (10, 10, 11))
        d = ImageDraw.Draw(sheet)
        for i, p in enumerate(ps):
            im = Image.open(p).convert('RGB'); im.thumbnail((tw, tw))
            x, y = (i % cols) * tw, (i // cols) * tw
            sheet.paste(im, (x, y)); d.text((x + 6, y + 4), os.path.basename(p)[:-4], fill=(200, 200, 200))
        out = os.path.join(src, f'{k}_sheet.jpg'); sheet.save(out, quality=90); print(out, len(ps))


if __name__ == '__main__':
    main()
