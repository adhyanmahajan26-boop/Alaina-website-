"""Label for the Superlift gas spring: u = around the tube, v = along it."""
from PIL import Image, ImageDraw, ImageFont
W, H = 1400, 4030
im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
BLUE = (47, 123, 255, 255); WHITE = (238, 240, 244, 255)
def along(text, font, fill, cx, cy, spacing=0):
    f = ImageFont.truetype(*font)
    w = int(sum(f.getlength(ch) + spacing for ch in text)); asc, desc = f.getmetrics()
    t = Image.new('RGBA', (w + 40, asc + desc + 20), (0, 0, 0, 0)); td = ImageDraw.Draw(t)
    x = 20
    for ch in text:
        td.text((x, 10), ch, font=f, fill=fill); x += f.getlength(ch) + spacing
    t = t.rotate(90, expand=True)
    im.alpha_composite(t, (int(cx - t.width / 2), int(cy - t.height / 2)))
# image y grows downward = v decreasing = towards the socket end
d.rectangle([0, 520, W, 610], fill=BLUE)            # ring near the rod end
d.rectangle([0, 3560, W, 3600], fill=BLUE)
along('SUPERLIFT', ('/usr/share/fonts/opentype/inter/Inter-BlackItalic.otf', 250), WHITE, W * 0.435, 1560, 10)
along('GAS SPRING  /  DICKY + BONNET', ('/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf', 58), (150, 190, 255, 255), W * 0.435, 2950, 8)
im.save('sldecal.png')
im.rotate(-90, expand=True).resize((1008, 350)).save('sldecal-prev.png')
