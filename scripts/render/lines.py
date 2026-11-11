"""The other two product lines, rendered the same way as the cabin damper:
   a twin-tube shocker (pickup and LCV) and a strut (rare struts).

usage: python lines.py <shock|strut> <outdir> <spec.json> [--res N] [--samples N] [--only a,b] [--force]
       python lines.py --spec <spec.json>            write the frame list for both
spec.json: list of frames {name, model, c, spin, cam:{t, S, az, el, roll}}
"""
import bpy, bmesh, math, sys, json, os
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import damper as dm
from damper import lathe, ring_y, hex_nut, principled, body_material, new_obj

HERE = os.path.dirname(os.path.abspath(__file__))
TAU = math.tau


def materials():
    M = {}
    M['paint'] = principled('paint', (0.011, 0.011, 0.013), 0.34, coat=0.4, coat_rough=0.1, bump=(1400, 0.03))
    M['body'] = body_material('body', os.path.join(HERE, 'decal.png'), (0.011, 0.011, 0.013), 0.34)
    M['cover'] = principled('cover', (0.012, 0.012, 0.014), 0.42, coat=0.25, coat_rough=0.2, bump=(1200, 0.03))
    M['chrome'] = principled('chrome', (0.92, 0.92, 0.93), 0.07, metal=1.0)
    M['zinc'] = principled('zinc', (0.72, 0.73, 0.75), 0.28, metal=1.0, bump=(2500, 0.02))
    M['steel_dark'] = principled('steel_dark', (0.16, 0.16, 0.17), 0.42, metal=1.0)
    M['pressed'] = principled('pressed', (0.014, 0.014, 0.016), 0.52, coat=0.12, coat_rough=0.35, bump=(1000, 0.04))
    M['rubber'] = principled('rubber', (0.016, 0.016, 0.017), 0.72, bump=(600, 0.05), spec=0.3)
    return M


def groups(names):
    sc = bpy.context.scene
    root = bpy.data.objects.new('root', None); sc.collection.objects.link(root)
    G = {}
    for g in names:
        e = bpy.data.objects.new('G_' + g, None); sc.collection.objects.link(e); e.parent = root; G[g] = e
    return root, G


def eye(M, parent, z, R=0.024, W=0.034):
    """Welded eye with a rubber bush and a zinc sleeve, axis along Y."""
    k = R / 0.030
    w = W / 2
    Ri = R * 0.70
    eye_prof = [(Ri, -w), (R - 0.0016, -w), (R, -w + 0.0016), (R, w - 0.0016), (R - 0.0016, w), (Ri, w), (Ri, -w)]
    bw = w + 0.003
    bush = [(Ri * 0.5, -bw), (Ri * 0.8, -bw, 0.0016), (Ri * 0.95, -bw + 0.002, 0.002), (Ri, -w + 0.002, 0.001), (Ri, w - 0.002, 0.001),
            (Ri * 0.95, bw - 0.002, 0.002), (Ri * 0.8, bw, 0.0016), (Ri * 0.5, bw), (Ri * 0.5, -bw)]
    sw = bw + 0.0025
    slv = [(Ri * 0.32, -sw), (Ri * 0.48, -sw, 0.0005), (Ri * 0.51, -sw + 0.0007, 0.0005), (Ri * 0.51, sw - 0.0007, 0.0005), (Ri * 0.48, sw, 0.0005), (Ri * 0.32, sw), (Ri * 0.32, -sw)]
    for nm, prof, mat, rad in (('eye', eye_prof, M['paint'], 0.0008), ('bush', bush, M['rubber'], 0.0012), ('sleeve', slv, M['zinc'], 0.0004)):
        o = ring_y(nm, prof, mat, parent, rad=rad); o.location.z = z
    return k


# ───────────────────────── twin-tube shocker ─────────────────────────
SH = dict(R=0.0232, body0=0.021, body1=0.262, coverR=0.0282, cover0=0.232, top=0.440, rodR=0.0072)


def build_shock():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = materials()
    root, G = groups(('lower', 'upper'))
    d = SH; R = d['R']
    eye(M, G['lower'], 0.0)
    body = [(0.0, d['body0']), (0.014, d['body0'], 0.004), (R, d['body0'] + 0.009, 0.006), (R, d['body1'] - 0.010, 0.002),
            (R + 0.0007, d['body1'] - 0.008, 0.0007), (R + 0.0007, d['body1'] - 0.004, 0.0025), (R - 0.0035, d['body1'], 0.002),
            (0.012, d['body1'], 0.001), (0.012, d['body1'] + 0.004, 0.0012), (d['rodR'], d['body1'] + 0.004)]
    lathe('body', body, M['body'], G['lower'], uv_z=(0.048, 0.125))
    lathe('weld', [(0.012, 0.0225), (0.016, 0.0205, 0.002), (0.0185, 0.0225, 0.002), (0.016, 0.0245, 0.002), (0.012, 0.0225)], M['paint'], G['lower'], rad=0.0013)
    # a rolled groove where the base valve is crimped in
    lathe('crimp', [(R - 0.0002, 0.037), (R + 0.0006, 0.0378, 0.0006), (R + 0.0006, 0.0392, 0.0006), (R - 0.0002, 0.040)], M['paint'], G['lower'], rad=0.0005)

    # everything that moves with the rod
    rp = d['rodR']; top = d['top']; cr = d['coverR']
    lathe('rod', [(0.0, 0.110), (rp, 0.110, 0.0005), (rp, top + 0.004, 0.0005), (0.0, top + 0.004)], M['chrome'], G['upper'], seg=96, rad=0.0004)
    cover = [(cr - 0.0012, d['cover0']), (cr, d['cover0'], 0.0004), (cr, top - 0.010, 0.002), (cr - 0.003, top - 0.002, 0.004), (0.013, top, 0.002),
             (0.013, top + 0.003, 0.001), (rp, top + 0.003), (rp, top - 0.0012), (0.0125, top - 0.0012, 0.001), (cr - 0.0042, top - 0.0032, 0.004), (cr - 0.0012, top - 0.011, 0.002), (cr - 0.0012, d['cover0'])]
    lathe('cover', cover, M['cover'], G['upper'], rad=0.001)
    # a pressed bead near the cover's open end
    lathe('bead', [(cr - 0.0002, d['cover0'] + 0.010), (cr + 0.0007, d['cover0'] + 0.0108, 0.0006), (cr + 0.0007, d['cover0'] + 0.0122, 0.0006), (cr - 0.0002, d['cover0'] + 0.013)], M['cover'], G['upper'], rad=0.0005)
    # stem mount: cup washers, two rubber bushes that clamp the chassis bracket, and a lock nut
    z = top + 0.003
    lathe('shoulder', [(0.0, z), (0.0100, z, 0.001), (0.0100, z + 0.006, 0.001), (0.0, z + 0.006)], M['paint'], G['upper'], seg=96)
    z += 0.006
    def washer(nm, z0, up):
        s = 1 if up else -1
        zz = z0 if up else z0 + 0.0042
        lathe(nm, [(0.0052, zz), (0.0125, zz, 0.0008), (0.0178, zz + s * 0.0026, 0.0012), (0.0190, zz + s * 0.0042, 0.0004), (0.0178, zz + s * 0.0042, 0.0004),
                   (0.0122, zz + s * 0.0016, 0.0012), (0.0052, zz + s * 0.0016)], M['zinc'], G['upper'], rad=0.0006)
    def bush(nm, z0, h=0.0125):
        lathe(nm, [(0.0052, z0), (0.0130, z0, 0.002), (0.0158, z0 + h * 0.5, 0.006), (0.0130, z0 + h, 0.002), (0.0052, z0 + h)], M['rubber'], G['upper'], rad=0.002)
    washer('washer_a', z, True)
    bush('bush_a', z + 0.0022)
    bush('bush_b', z + 0.0022 + 0.0125 + 0.0030)
    zt = z + 0.0022 + 0.0125 * 2 + 0.0030
    washer('washer_b', zt - 0.0020, False)
    hex_nut('stem_nut', M['zinc'], 0.0088, 0.0068, zt + 0.0024, G['upper'])
    th = [(0.0, z)]
    zz = z
    while zz < zt + 0.022:
        th += [(0.0044, zz), (0.0050, zz + 0.0004), (0.0044, zz + 0.0008)]
        zz += 0.001
    th += [(0.0038, zz + 0.0008), (0.0, zz + 0.0008)]
    lathe('stem_thread', th, M['zinc'], G['upper'], seg=64, rad=0.0)
    return root, G, M


def pose_shock(G, c, spin, root):
    G['upper'].location.z = -c
    root.rotation_euler = (0, 0, math.radians(spin))


# ───────────────────────── strut ─────────────────────────
ST = dict(R=0.0258, body1=0.300, seatZ=0.236, rodR=0.0108, rodTop=0.455)


def clamp_bracket(name, mat, R, t, z0, z1, ear_x, g, parent, holes):
    """Pressed-steel knuckle bracket: wraps the back of the tube, two ears run out along +X."""
    Rc = R + t / 2
    a0 = math.asin(g / Rc)
    path = [(ear_x, g)]
    n = 40
    for i in range(n + 1):
        a = a0 + (TAU - 2 * a0) * i / n
        path.append((Rc * math.cos(a), Rc * math.sin(a)))
    path.append((ear_x, -g))
    P = [Vector(p) for p in path]
    outer, inner = [], []
    for i, p in enumerate(P):
        a = P[max(i - 1, 0)]; b = P[min(i + 1, len(P) - 1)]
        tan = (b - a).normalized()
        nrm = Vector((tan.y, -tan.x))
        outer.append(p + nrm * t / 2); inner.append(p - nrm * t / 2)
    loop = outer + inner[::-1]
    bm = bmesh.new()
    vs = [bm.verts.new((p.x, p.y, z0)) for p in loop]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, verts=[v for v in r['geom'] if isinstance(v, bmesh.types.BMVert)], vec=(0, 0, z1 - z0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = new_obj(name, bm, mat, parent, smooth=True)
    ob.data.set_sharp_from_angle(angle=math.radians(40))
    for i, (hx, hz, hr) in enumerate(holes):
        cb = bmesh.new()
        bmesh.ops.create_cone(cb, cap_ends=True, segments=40, radius1=hr, radius2=hr, depth=0.2)
        bmesh.ops.rotate(cb, verts=cb.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
        bmesh.ops.translate(cb, verts=cb.verts, vec=(hx, 0, hz))
        cut = new_obj(f'{name}_cut{i}', cb, None, parent, smooth=False)
        cut.hide_render = True; cut.display_type = 'WIRE'
        mod = ob.modifiers.new(f'hole{i}', 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.object = cut; mod.solver = 'EXACT'
    # clip the outer corners of the ears, as on a pressed bracket
    for i, (cz, sg) in enumerate(((z0, 1), (z1, -1))):
        cb = bmesh.new()
        bmesh.ops.create_cube(cb, size=1.0)
        bmesh.ops.scale(cb, verts=cb.verts, vec=(0.06, 0.2, 0.06))
        bmesh.ops.rotate(cb, verts=cb.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(sg * 38), 3, 'Y'))
        bmesh.ops.translate(cb, verts=cb.verts, vec=(ear_x + 0.012, 0, cz - sg * 0.020))
        cut = new_obj(f'{name}_clip{i}', cb, None, parent, smooth=False)
        cut.hide_render = True
        mod = ob.modifiers.new(f'clip{i}', 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.object = cut; mod.solver = 'EXACT'
    bv = ob.modifiers.new('bevel', 'BEVEL'); bv.width = t * 0.32; bv.segments = 3; bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(40)
    return ob


def tab(name, mat, parent, size, loc, hole=0.0):
    """A small welded tab (brake hose or sensor bracket). The hole goes through its thinnest side."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, verts=bm.verts, vec=size)
    ob = new_obj(name, bm, mat, parent, smooth=True)
    ob.data.set_sharp_from_angle(angle=math.radians(40))
    ob.location = loc
    if hole:
        thin = min(range(3), key=lambda i: size[i])
        long = max(range(2), key=lambda i: size[i])
        cb = bmesh.new()
        bmesh.ops.create_cone(cb, cap_ends=True, segments=32, radius1=hole, radius2=hole, depth=0.1)
        if thin == 0: bmesh.ops.rotate(cb, verts=cb.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
        if thin == 1: bmesh.ops.rotate(cb, verts=cb.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
        off = [0, 0, 0]; off[long] = size[long] * 0.2 * (1 if loc[long] > 0 else -1)
        bmesh.ops.translate(cb, verts=cb.verts, vec=off)
        cut = new_obj(name + '_cut', cb, None, ob, smooth=False)
        cut.hide_render = True
        mod = ob.modifiers.new('hole', 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.object = cut; mod.solver = 'EXACT'
    bv = ob.modifiers.new('bevel', 'BEVEL'); bv.width = min(size) * 0.3; bv.segments = 3; bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(40)
    return ob


def build_strut():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = materials()
    root, G = groups(('lower', 'rod'))
    d = ST; R = d['R']; b1 = d['body1']
    body = [(0.0, 0.0), (0.016, 0.0, 0.004), (R, 0.010, 0.007), (R, b1 - 0.014, 0.002), (R - 0.0035, b1 - 0.004, 0.004), (0.0205, b1, 0.002), (0.0205, b1 + 0.001)]
    lathe('body', body, M['body'], G['lower'], uv_z=(0.128, 0.213))
    # gland nut and seal housing, bright against the black tube
    gl = [(0.012, b1 - 0.002), (0.0212, b1 - 0.002, 0.0006), (0.0212, b1 + 0.006, 0.001), (0.0222, b1 + 0.007, 0.0006), (0.0222, b1 + 0.026, 0.0015),
          (0.0190, b1 + 0.030, 0.0015), (0.0190, b1 + 0.036, 0.001), (0.0150, b1 + 0.040, 0.001), (d['rodR'] + 0.0012, b1 + 0.040, 0.0006), (d['rodR'] + 0.0012, b1 + 0.043, 0.0006), (d['rodR'], b1 + 0.043)]
    lathe('gland', gl, M['zinc'], G['lower'], rad=0.0008)
    for i in range(5):  # spanner grooves read as fine rings at this size
        z = b1 + 0.010 + i * 0.0032
        lathe(f'gland_ring{i}', [(0.0220, z), (0.0226, z + 0.0004, 0.0003), (0.0226, z + 0.0012, 0.0003), (0.0220, z + 0.0016)], M['steel_dark'], G['lower'], rad=0.0002)
    # spring seat: a pressed dish, tilted like the real thing
    sz = d['seatZ']
    seat = [(R, -0.026), (R + 0.0024, -0.024, 0.001), (R + 0.0024, -0.006, 0.004), (0.046, -0.001, 0.006), (0.066, 0.004, 0.006), (0.0725, 0.013, 0.003), (0.0745, 0.0135, 0.0008),
            (0.0745, 0.0115, 0.0008), (0.069, 0.0025, 0.005), (0.046, -0.0035, 0.006), (R + 0.006, -0.0085, 0.004), (R + 0.0048, -0.024, 0.001), (R, -0.026)]
    so = lathe('seat', seat, M['paint'], G['lower'], rad=0.0015)
    so.location = (0.006, 0, sz); so.rotation_euler = (0, math.radians(-8), 0)
    # knuckle bracket with its two bolt holes, and the small tabs welded to the tube
    clamp_bracket('bracket', M['pressed'], R, 0.0042, 0.016, 0.108, 0.070, 0.0170, G['lower'], holes=[(0.054, 0.038, 0.0072), (0.054, 0.090, 0.0072)])
    tab('hose_tab', M['pressed'], G['lower'], (0.003, 0.030, 0.024), (-0.004, R + 0.013, 0.170), hole=0.0042)
    tab('link_tab', M['pressed'], G['lower'], (0.034, 0.0035, 0.030), (-(R + 0.015), 0.003, 0.150), hole=0.0052)
    lathe('weld_seat', [(R - 0.0005, sz - 0.030), (R + 0.003, sz - 0.0285, 0.0015), (R + 0.003, sz - 0.0255, 0.0015), (R - 0.0005, sz - 0.024)], M['paint'], G['lower'], rad=0.0012)

    rp = d['rodR']; rt = d['rodTop']
    rod = [(0.0, 0.150), (rp, 0.150, 0.0005), (rp, rt, 0.0008), (0.0082, rt + 0.002, 0.0006), (0.0082, rt + 0.012, 0.0006), (0.0066, rt + 0.014, 0.0005), (0.0066, rt + 0.046, 0.0008), (0.0048, rt + 0.048, 0.0005), (0.0048, rt + 0.054, 0.0006), (0.0, rt + 0.054)]
    lathe('rod', rod, M['chrome'], G['rod'], seg=96, rad=0.0004)
    # rolled thread, drawn as fine rings
    th = []
    z = rt + 0.0165
    while z < rt + 0.044:
        th += [(0.0064, z), (0.0071, z + 0.00045), (0.0064, z + 0.0009)]
        z += 0.0011
    lathe('thread', th, M['zinc'], G['rod'], seg=64, rad=0.0)
    hex_nut('top_nut', M['zinc'], 0.0108, 0.008, rt + 0.021, G['rod'])
    return root, G, M


def pose_strut(G, c, spin, root):
    G['rod'].location.z = -c
    root.rotation_euler = (0, 0, math.radians(spin))


MODELS = {'shock': (build_shock, pose_shock), 'strut': (build_strut, pose_strut)}


def write_spec(path):
    s = lambda x: x * x * (3 - 2 * x)
    out = []
    N = 30
    for i in range(N):
        t = i / (N - 1)
        # the shocker takes one full stroke as it turns; the camera eases in
        c = 0.092 * math.sin(math.pi * s(t)) ** 2
        out.append(dict(name=f'k{i:02d}', model='shock', c=round(c, 5), spin=round(-34 + 62 * s(t), 3),
                        cam=dict(t=[0, 0, 0.252 - c / 2], S=round(0.53 - 0.04 * s(t), 4), az=round(26 - 14 * t, 3), el=10, roll=48)))
    for i in range(N):
        t = i / (N - 1)
        c = 0.085 * s(t)
        out.append(dict(name=f't{i:02d}', model='strut', c=round(c, 5), spin=round(-62 + 118 * s(t), 3),
                        cam=dict(t=[0, 0, 0.250 - c / 2], S=round(0.54 - 0.05 * s(t), 4), az=round(24 - 10 * t, 3), el=12, roll=48)))
    json.dump(out, open(path, 'w'), indent=0)
    print('wrote', len(out), 'frames to', path)


def main():
    argv = sys.argv[1:]
    if argv[0] == '--spec':
        return write_spec(argv[1])
    model, out, specf = argv[0], argv[1], argv[2]
    def opt(k, dflt):
        return type(dflt)(argv[argv.index(k) + 1]) if k in argv else dflt
    res = opt('--res', 1080); samples = opt('--samples', 96); only = opt('--only', '')
    os.makedirs(out, exist_ok=True)
    frames = [f for f in json.load(open(specf)) if f.get('model') == model]
    build, pose = MODELS[model]
    root, G, M = build()
    dm.lights()
    sc = bpy.context.scene
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.clip_start = 0.05; cam.data.clip_end = 20
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6; sc.cycles.glossy_bounces = 4; sc.cycles.diffuse_bounces = 2
    sc.render.film_transparent = True
    sc.render.resolution_x = res; sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    try:
        sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception as ex:
        print('view', ex)
    sel = set(only.split(',')) if only else None
    for fr in frames:
        if sel and fr['name'] not in sel: continue
        dst = os.path.join(out, fr['name'] + '.png')
        if os.path.exists(dst) and '--force' not in argv: continue
        pose(G, fr.get('c', 0.0), fr.get('spin', 0.0), root)
        c = fr['cam']
        dm.set_cam(cam, c['t'], c['S'], c['az'], c['el'], c['roll'], c.get('lens', 105))
        sc.render.filepath = dst
        bpy.context.view_layer.update()
        bpy.ops.render.render(write_still=True)
        print('RENDERED', fr['name'], flush=True)


if __name__ == '__main__':
    main()
