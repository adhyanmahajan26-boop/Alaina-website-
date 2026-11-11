"""Running-gear details shared by the car and the trucks: vented discs, calipers, rubber boots, ball joints, bushes,
hoses, wipers and number plates. All in metres; every builder parents to the object it is given."""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import damper as dm
import vkit as vk
from vkit import lerp, rbox, cyl, lathe, tube, empty, extrude_poly

TAU = math.tau


# ───────────────────────── materials ─────────────────────────
def machined(name, base=(0.50, 0.50, 0.51), rough=0.30, rings=520.0, ghost=False):
    """Turned metal: fine concentric tool marks (for disc faces and hubs, whose axis is the object's Y)."""
    m = dm.principled(name, base, rough, metal=1.0)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    ln = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(sep.outputs[0], ln.inputs[0]); nt.links.new(sep.outputs[2], ln.inputs[1])
    vl = nt.nodes.new('ShaderNodeVectorMath'); vl.operation = 'LENGTH'; nt.links.new(ln.outputs[0], vl.inputs[0])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = rings
    nt.links.new(vl.outputs['Value'], mul.inputs[0])
    sn = nt.nodes.new('ShaderNodeMath'); sn.operation = 'SINE'; nt.links.new(mul.outputs[0], sn.inputs[0])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60; nz.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.35
    nt.links.new(nz.outputs['Fac'], ad.inputs[0]); nt.links.new(sn.outputs[0], ad.inputs[2])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.10; bp.inputs['Distance'].default_value = 0.0002
    nt.links.new(ad.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    rm = nt.nodes.new('ShaderNodeMapRange'); rm.inputs[3].default_value = rough - 0.08; rm.inputs[4].default_value = rough + 0.10
    nt.links.new(nz.outputs['Fac'], rm.inputs[0]); nt.links.new(rm.outputs[0], b.inputs['Roughness'])
    if ghost: vk._ghost_mix(nt, b.outputs[0])
    return m


def cast(name, base=(0.075, 0.076, 0.08), rough=0.62, metal=0.55, ghost_kw=None):
    """Cast iron / cast aluminium: a grainy sand-cast skin with mottled roughness."""
    m = dm.principled(name, base, rough, metal=metal)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 900; n1.inputs['Detail'].default_value = 4
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 18; n2.inputs['Detail'].default_value = 3
    for n in (n1, n2): nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.22; bp.inputs['Distance'].default_value = 0.0004
    nt.links.new(n1.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    rm = nt.nodes.new('ShaderNodeMapRange'); rm.inputs[3].default_value = rough - 0.12; rm.inputs[4].default_value = rough + 0.1
    nt.links.new(n2.outputs['Fac'], rm.inputs[0]); nt.links.new(rm.outputs[0], b.inputs['Roughness'])
    cm = nt.nodes.new('ShaderNodeMix'); cm.data_type = 'RGBA'; cm.inputs[6].default_value = (*base, 1)
    cm.inputs[7].default_value = (*[c * 0.7 for c in base], 1)
    nt.links.new(n2.outputs['Fac'], cm.inputs[0]); nt.links.new(cm.outputs[2], b.inputs['Base Color'])
    if ghost_kw is not None: vk._ghost_mix(nt, b.outputs[0], **ghost_kw)
    return m


def label(name, path, size_px, draw, base=(0.9, 0.9, 0.88), rough=0.35, ghost=True, face=1):
    """A flat printed part (number plate): PIL draws the artwork, mapped over the object's Generated Y/Z box.
    draw(img, ImageDraw) paints into an RGB image of size_px."""
    if not os.path.exists(path):
        from PIL import Image, ImageDraw
        im = Image.new('RGB', size_px, tuple(int(c * 255) for c in base))
        draw(im, ImageDraw.Draw(im))
        im.save(path)
    m = dm.principled(name, base, rough, coat=0.4, coat_rough=0.08)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    flip = nt.nodes.new('ShaderNodeMath'); flip.operation = 'SUBTRACT'; flip.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs[1], flip.inputs[1])
    uv = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(flip.outputs[0], uv.inputs[0]); nt.links.new(sep.outputs[2], uv.inputs[1])
    img = nt.nodes.new('ShaderNodeTexImage'); img.image = bpy.data.images.load(path); img.extension = 'EXTEND'
    m['uv_flip'] = flip.name
    nt.links.new(uv.outputs[0], img.inputs[0])
    # print only on the face that looks along +X (face=1) or -X (face=-1); the back and edges stay plain
    nrm = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Normal'], nrm.inputs[0])
    fm = nt.nodes.new('ShaderNodeMath'); fm.operation = 'MULTIPLY'; fm.inputs[1].default_value = float(face)
    nt.links.new(nrm.outputs[0], fm.inputs[0])
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5
    nt.links.new(fm.outputs[0], gt.inputs[0])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (*base, 1)
    nt.links.new(gt.outputs[0], mx.inputs[0]); nt.links.new(img.outputs['Color'], mx.inputs[7])
    nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    if ghost: vk._ghost_mix(nt, b.outputs[0])
    return m


def plate_art(text, sub=None):
    """Indian-style white number plate: black border and characters (no maker's names)."""
    def draw(im, d):
        from PIL import ImageFont
        W, H = im.size
        d.rounded_rectangle((6, 6, W - 7, H - 7), radius=18, outline=(10, 10, 10), width=7)
        font = None
        for f in ('/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                  '/Library/Fonts/Arial Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
            if os.path.exists(f):
                try: font = ImageFont.truetype(f, int(H * 0.70)); break
                except Exception: pass
        font = font or ImageFont.load_default()
        bb = d.textbbox((0, 0), text, font=font)
        d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], (H - (bb[3] - bb[1])) / 2 - bb[1]), text, fill=(12, 12, 12), font=font)
        d.text((22, H / 2 - 14), 'IND', fill=(30, 50, 140), font=ImageFont.truetype(font.path, 26) if hasattr(font, 'path') else None)
    return draw


# ───────────────────────── brakes ─────────────────────────
def vented_disc(name, parent, M, R, t=0.024, hat=0.045, vanes=36, loc=(0, 0, 0), inner=0.60):
    """A vented disc about the Y axis, braking faces at y in [-t, 0] (outboard face at y=0), hat stepping out to +Y."""
    g = empty(name, parent, loc)
    ri = R * inner
    pl = t * 0.32
    for k, (y0, y1) in enumerate(((-pl, 0.0), (-t, -t + pl))):
        lathe(f'{name}_face{k}', [(ri, y0), (R, y0, 0.0008), (R, y1, 0.0008), (ri, y1)] + [(ri, y0)], M['disc_face'], g, axis='Y', seg=128, rad=0.0)
    for i in range(vanes):
        a = TAU * i / vanes
        ob = rbox(f'{name}_vane{i}', ((R - ri) * 0.94, t - 2 * pl + 0.001, 0.0045), M['disc_core'], g, loc=(0, -t / 2, 0), r=0.0008, seg=1)
        ob.data.transform(Matrix.Translation(((R + ri) / 2, 0, 0)))
        ob.rotation_euler = (0, a + 0.12, 0)
    # the hat: a pressed top hat out to the hub face
    hr = ri * 0.92
    lathe(name + '_hat', [(0.035, hat), (hr - 0.012, hat, 0.003), (hr, hat - 0.012, 0.004), (hr, 0.0, 0.002), (hr + 0.006, -0.002), (hr + 0.006, 0.002),
                          (hr - 0.004, hat - 0.006, 0.003), (0.035, hat - 0.006)], M['disc_core'], g, axis='Y', seg=96, rad=0.0008)
    return g


def caliper(name, parent, M, R, t, a0=100, a1=160, loc=(0, 0, 0), bracket=True):
    """A floating caliper straddling the disc rim between angles a0..a1 (degrees in the XZ plane, 0 = +X, 90 = up).
    The disc's braking faces sit at y in [-t, 0]."""
    g = empty(name, parent, loc)
    def sector(r0, r1, b0, b1, n=14):
        out = [(r1 * math.cos(math.radians(lerp(b0, b1, i / n))), r1 * math.sin(math.radians(lerp(b0, b1, i / n)))) for i in range(n + 1)]
        inn = [(r0 * math.cos(math.radians(lerp(b1, b0, i / n))), r0 * math.sin(math.radians(lerp(b1, b0, i / n)))) for i in range(n + 1)]
        return out + inn
    ow = 0.030       # outboard body width
    # bridge over the rim, the outboard fist and the inboard piston housing
    extrude_poly(name + '_bridge', sector(R - 0.004, R + 0.020, a0 + 6, a1 - 6), t + 0.030, M['caliper'], g, axis='Y', bevel=0.004, seg=3, loc=(0, -t / 2, 0))
    extrude_poly(name + '_fist', sector(R - 0.058, R + 0.016, a0, a1), ow * 0.6, M['caliper'], g, axis='Y', bevel=0.006, seg=3, loc=(0, 0.012 + ow * 0.3, 0))
    extrude_poly(name + '_housing', sector(R - 0.062, R + 0.014, a0 - 2, a1 + 2), 0.046, M['caliper'], g, axis='Y', bevel=0.007, seg=3, loc=(0, -t - 0.026, 0))
    # pads, just visible at the rim
    for y in (0.003, -t - 0.003):
        extrude_poly(name + f'_pad{y > 0}', sector(R - 0.050, R - 0.004, a0 + 4, a1 - 4), 0.006, M['pad'], g, axis='Y', bevel=0.0008, seg=1, loc=(0, y + (0.003 if y > 0 else -0.003), 0))
    am = math.radians((a0 + a1) / 2)
    c = Vector((math.cos(am), 0, math.sin(am)))
    # guide-pin bolts and the bleed nipple
    for a in (a0 - 6, a1 + 6):
        ar = math.radians(a)
        p = Vector((math.cos(ar) * (R - 0.024), -t - 0.03, math.sin(ar) * (R - 0.024)))
        cyl(f'{name}_pinboot{a}', 0.012, 0.026, M['rubber'], g, loc=p[:], axis='Y', seg=24, bevel=0.003)
        n = dm.hex_nut(f'{name}_pin{a}', M['zinc'], 0.0085, 0.010, 0, g)
        n.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X')); n.location = (p.x, -t - 0.050, p.z)
    pb = c * (R + 0.010) + Vector((0, -t - 0.040, 0))
    lathe(name + '_bleed', [(0.0, 0.0), (0.0045, 0.0, 0.0005), (0.0045, 0.010), (0.0060, 0.012), (0.0060, 0.018), (0.0030, 0.020), (0.0, 0.020)], M['zinc'], g, axis='Z', seg=20, rad=0.0004,
          loc=pb[:], rot=(0, -(am - math.pi / 2), 0))
    lathe(name + '_cap', [(0.0, 0.020), (0.0052, 0.020, 0.001), (0.0052, 0.030, 0.002), (0.0, 0.031)], M['rubber'], g, axis='Z', seg=20, rad=0.0006, loc=pb[:], rot=(0, -(am - math.pi / 2), 0))
    if bracket:
        extrude_poly(name + '_carrier', sector(R - 0.075, R - 0.050, a0 - 14, a1 + 14), 0.012, M['cast_dark'], g, axis='Y', bevel=0.003, seg=2, loc=(0, -t - 0.056, 0))
    return g


# ───────────────────────── rubber, joints, hoses ─────────────────────────
def bellows(name, parent, M, r0, r1, length, folds=7, depth=0.006, axis='Y', loc=(0, 0, 0), rot=None):
    """A convoluted rubber boot from radius r0 at 0 to r1 at `length` along `axis`."""
    pts = [(r0 * 0.75, 0.0), (r0, 0.0, 0.001), (r0, length * 0.06, 0.002)]
    n = folds * 2
    for i in range(1, n):
        f = i / n
        z = lerp(length * 0.08, length * 0.92, f)
        r = lerp(r0, r1, f) + (depth if i % 2 else -depth * 0.2)
        pts.append((r, z, depth * 0.45))
    pts += [(r1, length * 0.94, 0.002), (r1, length, 0.001), (r1 * 0.75, length)]
    return lathe(name, pts, M['rubber'], parent, axis=axis, seg=48, rad=0.0, loc=loc, rot=rot)


def ball_joint(name, parent, M, pos, axis_vec, r=0.016, stud=0.07):
    """A ball joint: forged housing, rubber boot and a tapered stud along axis_vec (a unit-ish vector, toward the part it holds)."""
    g = empty(name, parent, pos)
    g.rotation_euler = Vector(axis_vec).to_track_quat('Z', 'Y').to_euler()
    lathe(name + '_house', [(0.0, -r * 1.2), (r * 0.9, -r * 1.2, r * 0.3), (r * 1.15, -r * 0.4, r * 0.3), (r * 1.1, r * 0.25, r * 0.2), (r * 0.7, r * 0.3)], M['cast_dark'], g, seg=40, rad=0.0)
    lathe(name + '_boot', [(r * 0.75, r * 0.25), (r * 1.15, r * 0.6, r * 0.4), (r * 1.05, r * 1.25, r * 0.3), (r * 0.45, r * 1.6, r * 0.12), (r * 0.36, r * 1.6)], M['rubber'], g, seg=40, rad=0.0)
    lathe(name + '_stud', [(0.0, r), (r * 0.42, r, 0.0005), (r * 0.30, stud), (0.0, stud)], M['zinc'], g, seg=24, rad=0.0)
    n = dm.hex_nut(name + '_nut', M['zinc'], r * 0.62, r * 0.55, stud - r * 0.9, g)
    return g


def bush(name, parent, M, pos, axis='X', r=0.032, w=0.05):
    """A rubber-bonded pivot bush: steel outer sleeve, rubber with voids, inner tube and a bolt head."""
    g = empty(name, parent, pos)
    lathe(name + '_outer', [(r * 0.86, -w / 2), (r, -w / 2, 0.002), (r, w / 2, 0.002), (r * 0.86, w / 2), (r * 0.86, -w / 2)], M['cast_dark'], g, axis=axis, seg=48, rad=0.0)
    lathe(name + '_rubber', [(r * 0.38, -w / 2 - 0.004), (r * 0.86, -w / 2 + 0.002, 0.004), (r * 0.86, w / 2 - 0.002, 0.004), (r * 0.38, w / 2 + 0.004), (r * 0.38, -w / 2 - 0.004)], M['rubber'], g, axis=axis, seg=48, rad=0.0)
    lathe(name + '_inner', [(0.0, -w / 2 - 0.012), (r * 0.38, -w / 2 - 0.012, 0.001), (r * 0.38, w / 2 + 0.012, 0.001), (0.0, w / 2 + 0.012)], M['zinc'], g, axis=axis, seg=32, rad=0.0)
    return g


def hose(name, parent, M, pts, r=0.0055, fittings=True):
    """A rubber brake hose with crimped steel ends."""
    tube(name, pts, r, M['rubber'], parent)
    if fittings:
        for k, (a, b) in enumerate(((pts[0], pts[1]), (pts[-1], pts[-2]))):
            d = (Vector(b) - Vector(a)).normalized()
            p = Vector(a) + d * 0.012
            o = lathe(f'{name}_crimp{k}', [(0.0, -0.014), (r * 1.6, -0.014, 0.0006), (r * 1.6, 0.014, 0.0006), (0.0, 0.014)], M['zinc'], parent, axis='Z', seg=24, rad=0.0, loc=p[:])
            o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()


def wiper(name, parent, M, pivot, tip, up=(0, 0, 1), arm_r=0.0065):
    """A flat-blade wiper lying on the glass from pivot to tip; `up` is the glass normal."""
    p, q, n = Vector(pivot), Vector(tip), Vector(up).normalized()
    d = q - p; L = d.length; d.normalize()
    side = n.cross(d).normalized()
    # the arm, slightly raised over the blade, with its spindle cap
    tube(name + '_arm', [(p + n * 0.012)[:], (p + d * L * 0.5 + n * 0.022)[:], (q - d * 0.04 + n * 0.018)[:]], arm_r, M['black_satin'], parent)
    lathe(name + '_cap', [(0.0, 0.026), (0.016, 0.024, 0.006), (0.018, 0.0)], M['black_satin'], parent, axis='Z', seg=32, rad=0.0, loc=p[:],
          rot=n.to_track_quat('Z', 'Y').to_euler())
    # the blade: a spine with a tapered aero spoiler and the rubber lip
    bl = L * 0.78
    c = p + d * (L - bl / 2 - 0.01) + n * 0.010
    rot = Matrix((d, side, n)).transposed().to_euler()
    rbox(name + '_blade', (bl, 0.016, 0.014), M['black_satin'], parent, loc=c[:], rot=rot, r=0.005, seg=2, taper=None)
    rbox(name + '_lip', (bl - 0.01, 0.004, 0.006), M['rubber'], parent, loc=(c - n * 0.009)[:], rot=rot, r=0.0015, seg=1)
