"""Photoreal cabin damper, built procedurally and rendered with Cycles.

usage: python damper.py <outdir> <spec.json> [--res N] [--samples N] [--only i,j,k]
spec.json: list of frames {name, c, e, spin, cam:{t:[x,y,z], S, az, el, roll}}
"""
import bpy, bmesh, math, sys, json, os
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
TAU = math.tau

# ───────────────────────── geometry helpers ─────────────────────────
def fillet(pts, r=0.0012, seg=5):
    """Round the interior corners of an open (r,z) polyline."""
    out = [pts[0][:2]]
    for i in range(1, len(pts) - 1):
        a, b, c = Vector(pts[i - 1][:2]), Vector(pts[i][:2]), Vector(pts[i + 1][:2])
        rr = pts[i][2] if len(pts[i]) > 2 else r
        u, v = (a - b), (c - b)
        lu, lv = u.length, v.length
        if rr <= 0 or lu < 1e-7 or lv < 1e-7:
            out.append(tuple(b)); continue
        u /= lu; v /= lv
        cosang = max(-1, min(1, u.dot(v)))
        ang = math.acos(cosang)
        if ang > math.pi - 0.02 or ang < 0.02:
            out.append(tuple(b)); continue
        d = min(rr / math.tan(ang / 2), 0.45 * lu, 0.45 * lv)
        rr2 = d * math.tan(ang / 2)
        p0, p1 = b + u * d, b + v * d
        bis = (u + v).normalized()
        cen = b + bis * (rr2 / math.sin(ang / 2))
        a0 = math.atan2(p0.y - cen.y, p0.x - cen.x)
        a1 = math.atan2(p1.y - cen.y, p1.x - cen.x)
        da = a1 - a0
        while da > math.pi: da -= TAU
        while da < -math.pi: da += TAU
        for k in range(seg + 1):
            t = a0 + da * k / seg
            out.append((cen.x + rr2 * math.cos(t), cen.y + rr2 * math.sin(t)))
    out.append(pts[-1][:2])
    return out


def new_obj(name, bm, mat, parent=None, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat: me.materials.append(mat)
    if parent: ob.parent = parent
    return ob


def lathe(name, profile, mat, parent=None, seg=160, uv_z=None, rad=0.0012):
    """Revolve an (r,z) profile about Z. uv_z=(z0,z1) maps v along z, u around (seam at the back, +Y)."""
    prof = fillet(profile, rad)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    for (r, z) in prof:
        r = max(r, 1e-5)
        ring = [bm.verts.new((r * math.cos(math.pi / 2 + TAU * i / seg), r * math.sin(math.pi / 2 + TAU * i / seg), z)) for i in range(seg)]
        rings.append(ring)
    for j in range(len(rings) - 1):
        for i in range(seg):
            i2 = (i + 1) % seg
            f = bm.faces.new((rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i]))
            us = (i / seg, (i + 1) / seg, (i + 1) / seg, i / seg)
            zs = (prof[j][1], prof[j][1], prof[j + 1][1], prof[j + 1][1])
            for l, u, z in zip(f.loops, us, zs):
                v = (z - uv_z[0]) / (uv_z[1] - uv_z[0]) if uv_z else 0.5
                l[uvl].uv = (u, v)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(name, bm, mat, parent)


def ring_y(name, profile, mat, parent=None, seg=128, rad=0.0012):
    """Lathe about Z then lay it down so its axis is Y (eye rings, bushes)."""
    ob = lathe(name, profile, mat, parent, seg, rad=rad)
    ob.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    return ob


def helix_z(theta, wire_r, pitch, turns, dead=0.85):
    """Height of a closed-end coil at angle theta. Dead coils sit at wire pitch, active ones at `pitch`."""
    p0 = wire_r * 2.04
    n = theta / TAU
    def pitch_at(x):
        e = min(x, turns - x)
        k = max(0.0, min(1.0, (e - dead * 0.6) / (dead * 0.8)))
        k = k * k * (3 - 2 * k)
        return p0 + (pitch - p0) * k
    # integrate numerically
    steps = max(2, int(n * 48))
    z = 0.0
    for s in range(steps):
        z += pitch_at((s + 0.5) / steps * n) * (n / steps)
    return z


def coil_mesh(name, mat, R, wire_r, height, turns=7.4, parent=None, seg_turn=72, seg_wire=20):
    """Coil spring of total centre-to-centre height `height`."""
    # find active pitch by bisection so the coil has the wanted height
    lo, hi = wire_r * 2.04, 0.2
    for _ in range(40):
        mid = (lo + hi) / 2
        if helix_z(turns * TAU, wire_r, mid, turns) > height: hi = mid
        else: lo = mid
    pitch = (lo + hi) / 2
    N = int(turns * seg_turn)
    # cumulative z table
    p0 = wire_r * 2.04
    dead = 0.85
    zs = [0.0]
    for s in range(N):
        x = (s + 0.5) / N * turns
        e = min(x, turns - x)
        k = max(0.0, min(1.0, (e - dead * 0.6) / (dead * 0.8)))
        k = k * k * (3 - 2 * k)
        zs.append(zs[-1] + (p0 + (pitch - p0) * k) * (turns / N))
    sc = height / zs[-1]
    zs = [z * sc for z in zs]
    bm = bmesh.new()
    rings = []
    for s in range(N + 1):
        th = s / N * turns * TAU
        c = Vector((R * math.cos(th), R * math.sin(th), zs[s]))
        dz = (zs[min(s + 1, N)] - zs[max(s - 1, 0)]) / ((min(s + 1, N) - max(s - 1, 0)) / N * turns * TAU)
        tan = Vector((-R * math.sin(th), R * math.cos(th), dz)).normalized()
        nrm = Vector((math.cos(th), math.sin(th), 0))
        bn = tan.cross(nrm).normalized()
        # ground ends: flatten the wire toward the seat on the last 3/4 turn
        ring = []
        for k in range(seg_wire):
            a = TAU * k / seg_wire
            p = c + (nrm * math.cos(a) + bn * math.sin(a)) * wire_r
            ring.append(bm.verts.new(p))
        rings.append(ring)
    for s in range(N):
        for k in range(seg_wire):
            k2 = (k + 1) % seg_wire
            bm.faces.new((rings[s][k], rings[s][k2], rings[s + 1][k2], rings[s + 1][k]))
    for ring, flip in ((rings[0], False), (rings[-1], True)):
        f = bm.faces.new(ring if flip else ring[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = new_obj(name, bm, mat, parent)
    # clip to flat ground ends
    return ob


def hex_nut(name, mat, r, h, z, parent=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r, depth=h)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=h * 0.09, segments=3, affect='EDGES')
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, z + h / 2))
    ob = new_obj(name, bm, mat, parent, smooth=True)
    ob.data.set_sharp_from_angle(angle=math.radians(35))
    return ob


# ───────────────────────── materials ─────────────────────────
def principled(name, base, rough, metal=0.0, coat=0.0, coat_rough=0.1, bump=None, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Coat Roughness'].default_value = coat_rough
    b.inputs['Specular IOR Level'].default_value = spec
    if bump:
        scale, strength = bump
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = scale
        nz.inputs['Detail'].default_value = 3
        bp = nt.nodes.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = strength
        bp.inputs['Distance'].default_value = 0.0004
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
        nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def body_material(name, decal_path, paint, rough):
    m = principled(name, paint, rough, coat=0.35, coat_rough=0.12, bump=(1400, 0.035))
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    img = nt.nodes.new('ShaderNodeTexImage')
    img.image = bpy.data.images.load(decal_path)
    img.extension = 'CLIP'
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs[6].default_value = (*paint, 1)
    nt.links.new(img.outputs['Color'], mix.inputs[7])
    nt.links.new(img.outputs['Alpha'], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    # printed ink is a touch rougher than the paint
    mr = nt.nodes.new('ShaderNodeMix')
    mr.data_type = 'FLOAT'
    mr.inputs[2].default_value = rough
    mr.inputs[3].default_value = 0.5
    nt.links.new(img.outputs['Alpha'], mr.inputs[0])
    nt.links.new(mr.outputs[0], b.inputs['Roughness'])
    return m


# ───────────────────────── build ─────────────────────────
D = dict(
    eyeR=0.0300, eyeRi=0.0212, eyeW=0.040,
    bodyR=0.0275, body0=0.026, body1=0.212,
    seatZ=0.150, seatR=0.0475,
    wire=0.0060, coilR=0.0386,
    topSeatZ=0.332, rodR=0.0088, rod0=0.098, rod1=0.350,
    topEyeZ=0.388,
)


def build(reset=True):
    """reset=False builds the damper into the scene that is already open (the vehicle films do this)."""
    if reset: bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    M = {}
    M['paint'] = principled('paint', (0.011, 0.011, 0.013), 0.36, coat=0.35, coat_rough=0.12, bump=(1400, 0.035))
    M['body'] = body_material('body', os.path.join(HERE, 'decal.png'), (0.011, 0.011, 0.013), 0.36)
    M['spring'] = principled('spring', (0.009, 0.009, 0.010), 0.30, coat=0.6, coat_rough=0.08, bump=(900, 0.02))
    M['chrome'] = principled('chrome', (0.92, 0.92, 0.93), 0.07, metal=1.0)
    M['zinc'] = principled('zinc', (0.70, 0.71, 0.73), 0.30, metal=1.0, bump=(2500, 0.02))
    M['steel_dark'] = principled('steel_dark', (0.16, 0.16, 0.17), 0.42, metal=1.0)
    M['rubber'] = principled('rubber', (0.016, 0.016, 0.017), 0.72, bump=(600, 0.05), spec=0.3)
    M['pu'] = principled('pu', (0.86, 0.23, 0.035), 0.62, bump=(700, 0.12), spec=0.35)
    M['shield'] = principled('shield', (0.013, 0.013, 0.015), 0.5, coat=0.15, coat_rough=0.3, bump=(1200, 0.03))

    root = bpy.data.objects.new('root', None); sc.collection.objects.link(root)
    G = {}
    for g in ('lower', 'lbush', 'spring', 'rod', 'shield', 'top', 'tbush'):
        e = bpy.data.objects.new('G_' + g, None); sc.collection.objects.link(e); e.parent = root; G[g] = e

    d = D
    # eye ring profile (r, z): a welded steel eye with chamfered faces
    w = d['eyeW'] / 2
    eye_prof = [(d['eyeRi'], -w), (d['eyeR'] - 0.002, -w), (d['eyeR'], -w + 0.002), (d['eyeR'], w - 0.002), (d['eyeR'] - 0.002, w), (d['eyeRi'], w), (d['eyeRi'], -w)]
    bush_prof = [(0.0102, -0.023), (0.0165, -0.023, 0.002), (0.0200, -0.0205, 0.0025), (0.0212, -0.017, 0.001), (0.0212, 0.017, 0.001), (0.0200, 0.0205, 0.0025), (0.0165, 0.023, 0.002), (0.0102, 0.023), (0.0102, -0.023)]
    slv_prof = [(0.0066, -0.026), (0.0098, -0.026, 0.0006), (0.0104, -0.0252, 0.0006), (0.0104, 0.0252, 0.0006), (0.0098, 0.026, 0.0006), (0.0066, 0.026), (0.0066, -0.026)]
    for g, gb, z in (('lower', 'lbush', 0.0), ('top', 'tbush', d['topEyeZ'])):
        o = ring_y('eye_' + g, eye_prof, M['paint'], G[g], rad=0.0009); o.location.z = z
        o = ring_y('bush_' + g, bush_prof, M['rubber'], G[gb]); o.location.z = z
        o = ring_y('sleeve_' + g, slv_prof, M['zinc'], G[gb], rad=0.0004); o.location.z = z

    R = d['bodyR']
    # body tube: domed base welded to the eye, rolled closure at the top
    body_prof = [(0.0, d['body0']), (0.017, d['body0'], 0.004), (R, d['body0'] + 0.010, 0.006), (R, d['body1'] - 0.012, 0.002),
                 (R + 0.0008, d['body1'] - 0.010, 0.0008), (R + 0.0008, d['body1'] - 0.005, 0.003), (R - 0.004, d['body1'], 0.002),
                 (0.0145, d['body1'], 0.001), (0.0145, d['body1'] + 0.005, 0.0015), (0.0105, d['body1'] + 0.005, 0.0005), (0.0105, d['body1'] + 0.001), (d['rodR'], d['body1'] + 0.001)]
    lathe('body', body_prof, M['body'], G['lower'], uv_z=(0.036, 0.126))
    # weld bead between eye and base
    weld = [(0.014, 0.0285), (0.019, 0.0262, 0.002), (0.0215, 0.0285, 0.002), (0.019, 0.031, 0.002), (0.014, 0.0285)]
    lathe('weld', weld, M['paint'], G['lower'], rad=0.0015)
    # rod seal (rubber wiper) sitting in the closure
    lathe('seal', [(d['rodR'], d['body1'] + 0.0005), (0.0118, d['body1'] + 0.0005, 0.0008), (0.0118, d['body1'] + 0.0068, 0.0015), (d['rodR'] + 0.0006, d['body1'] + 0.0082, 0.0006), (d['rodR'], d['body1'] + 0.006)], M['rubber'], G['lower'], rad=0.0006)
    # lower spring seat: sleeve welded to the body, flange with a raised lip
    sz = d['seatZ']; sr = d['seatR']
    seat_prof = [(R, sz - 0.022), (R + 0.0022, sz - 0.020, 0.0012), (R + 0.0022, sz - 0.004, 0.003), (sr, sz - 0.004, 0.002), (sr + 0.0022, sz - 0.002, 0.0012), (sr + 0.0022, sz + 0.005, 0.0008),
                 (sr, sz + 0.005, 0.0008), (sr, sz, 0.0015), (R + 0.0045, sz, 0.002), (R + 0.0045, sz + 0.006, 0.0012), (R, sz + 0.006)]
    lathe('seat_lower', seat_prof, M['paint'], G['lower'])

    # rod with piston and valve stack (only seen when exploded)
    rp = d['rodR']
    rod_prof = [(0.0, d['rod0'] - 0.012), (0.006, d['rod0'] - 0.012, 0.001), (0.006, d['rod0'] - 0.006), (rp, d['rod0'] - 0.006, 0.0005), (rp, d['rod1'] - 0.012, 0.0006), (0.0065, d['rod1'] - 0.010, 0.0004), (0.0065, d['rod1'], 0.0008), (0.0, d['rod1'])]
    lathe('rod', rod_prof, M['chrome'], G['rod'], seg=96, rad=0.0004)
    pr = R - 0.0032
    pz = d['rod0']
    piston = [(rp, pz - 0.004), (pr - 0.004, pz - 0.004, 0.0008), (pr, pz - 0.002, 0.0006), (pr, pz + 0.003, 0.0004), (pr - 0.0012, pz + 0.0036, 0.0003), (pr - 0.0012, pz + 0.0074, 0.0003), (pr, pz + 0.008, 0.0004),
              (pr, pz + 0.014, 0.0006), (pr - 0.004, pz + 0.016, 0.0008), (rp, pz + 0.016)]
    lathe('piston', piston, M['zinc'], G['rod'], rad=0.0005)
    lathe('piston_band', [(pr - 0.0013, pz + 0.0037), (pr + 0.0002, pz + 0.0039, 0.0003), (pr + 0.0002, pz + 0.0071, 0.0003), (pr - 0.0013, pz + 0.0073)], M['steel_dark'], G['rod'], rad=0.0003)
    # shim stack + nut under the piston
    lathe('shims', [(0.0061, pz - 0.0105), (0.016, pz - 0.0105, 0.0002), (0.016, pz - 0.0092, 0.0002), (0.013, pz - 0.0092, 0.0002), (0.013, pz - 0.0080, 0.0002), (0.019, pz - 0.0080, 0.0002), (0.019, pz - 0.0045, 0.0002), (0.0061, pz - 0.0045)], M['steel_dark'], G['rod'], rad=0.0002)
    hex_nut('piston_nut', M['zinc'], 0.0105, 0.006, pz - 0.0168, G['rod'])
    # rebound stop + bump stop (cellular PU) high on the rod
    bz = d['topSeatZ'] - 0.046
    bump = [(rp + 0.0004, bz), (0.0135, bz, 0.003), (0.0185, bz + 0.010, 0.004), (0.0165, bz + 0.016, 0.002), (0.0205, bz + 0.024, 0.004), (0.0185, bz + 0.031, 0.002), (0.0215, bz + 0.040, 0.003), (0.0215, bz + 0.044, 0.001), (rp + 0.0004, bz + 0.044)]
    lathe('bump_stop', bump, M['pu'], G['rod'], rad=0.002)

    # dust shield hanging from the top seat
    tz = d['topSeatZ']
    shield = [(0.0288, tz - 0.074), (0.0303, tz - 0.074, 0.0005), (0.0303, tz - 0.004, 0.002), (0.024, tz + 0.001, 0.002), (0.012, tz + 0.001), (0.012, tz - 0.001), (0.0235, tz - 0.001, 0.002), (0.0288, tz - 0.005, 0.002), (0.0288, tz - 0.074)]
    lathe('shield', shield, M['shield'], G['shield'], rad=0.001)
    # upper spring seat (pressed steel cup, lip down)
    tseat = [(0.0115, tz + 0.0012), (0.030, tz + 0.0012, 0.002), (0.034, tz - 0.0025, 0.003), (sr, tz - 0.0025, 0.002), (sr + 0.0022, tz - 0.004, 0.0012), (sr + 0.0022, tz - 0.010, 0.0008), (sr + 0.0002, tz - 0.010, 0.0008),
             (sr + 0.0002, tz - 0.005, 0.0012), (0.034, tz + 0.0005 - 0.0055, 0.002), (0.034, tz + 0.005, 0.003), (0.030, tz + 0.0075, 0.002), (0.0115, tz + 0.0075, 0.0008), (0.0115, tz + 0.0012)]
    lathe('seat_upper', tseat, M['paint'], G['shield'])

    # top mount: washer, nut, stem, eye
    lathe('washer', [(0.0066, tz + 0.0076), (0.0165, tz + 0.0076, 0.0004), (0.0165, tz + 0.0100, 0.0004), (0.0066, tz + 0.0100)], M['zinc'], G['top'], rad=0.0004)
    hex_nut('top_nut', M['zinc'], 0.0125, 0.0085, tz + 0.0102, G['top'])
    te = d['topEyeZ']
    lathe('stem', [(0.0, tz + 0.016), (0.0115, tz + 0.016, 0.001), (0.0115, tz + 0.022, 0.002), (0.014, te - d['eyeR'] - 0.004, 0.003), (0.018, te - d['eyeR'] + 0.004, 0.002), (0.0, te - d['eyeR'] + 0.004)], M['paint'], G['top'], seg=96)
    lathe('weld_top', [(0.013, te - 0.0285), (0.019, te - 0.0262, 0.002), (0.0215, te - 0.0285, 0.002), (0.019, te - 0.031, 0.002), (0.013, te - 0.0285)], M['paint'], G['top'], rad=0.0015)
    return root, G, M


def set_pose(G, M, c, e, spin, root):
    """c: compression (m, + is shorter). e: 0..1 exploded. spin: degrees about the damper axis."""
    d = D
    s = lambda x: x * x * (3 - 2 * x)
    es = s(max(0.0, min(1.0, e)))
    # staged explode so parts leave in order
    def st(a, b):
        return s(max(0.0, min(1.0, (e - a) / (b - a))))
    G['rod'].location.z = -c + 0.262 * st(0.05, 0.9)
    G['shield'].location.z = -c + 0.385 * st(0.0, 0.85)
    G['top'].location.z = -c + 0.445 * st(0.0, 0.8)
    G['tbush'].location.z = -c + 0.445 * st(0.0, 0.8)
    G['tbush'].location.y = -0.085 * st(0.35, 1.0)
    G['lbush'].location.y = -0.085 * st(0.35, 1.0)
    G['spring'].location.z = 0.0
    old = bpy.data.objects.get('coil')
    if old:
        me = old.data; bpy.data.objects.remove(old); bpy.data.meshes.remove(me)
    z0 = d['seatZ'] + d['wire']
    # when exploded the spring relaxes to its free length
    z1 = d['topSeatZ'] - 0.0025 - d['wire'] - c * (1 - es) + 0.022 * es
    ob = coil_mesh('coil', M['spring'], d['coilR'], d['wire'], z1 - z0, parent=G['spring'])
    ob.location.z = z0
    root.rotation_euler = (0, 0, math.radians(spin))


def lights():
    sc = bpy.context.scene
    def area(name, loc, size, power, color=(1, 1, 1), target=(0, 0, 0.19), spread=None):
        L = bpy.data.lights.new(name, 'AREA')
        L.shape = 'RECTANGLE'; L.size, L.size_y = size
        L.energy = power; L.color = color
        if spread: L.spread = spread
        o = bpy.data.objects.new(name, L); sc.collection.objects.link(o)
        o.location = loc
        dirv = Vector(target) - Vector(loc)
        o.rotation_euler = dirv.to_track_quat('-Z', 'Y').to_euler()
        return o
    Ls = {}
    # long strips parallel to the damper give the unbroken highlights product shots rely on
    Ls['key'] = area('key', (-0.62, -0.55, 0.30), (0.22, 1.5), 12)
    Ls['rimR'] = area('rimR', (0.60, 0.42, 0.22), (0.10, 1.6), 26, (0.86, 0.92, 1.0))
    Ls['rimL'] = area('rimL', (-0.52, 0.50, 0.20), (0.10, 1.6), 14, (1.0, 0.42, 0.16))
    Ls['top'] = area('top', (0.10, -0.25, 1.15), (0.9, 0.9), 7)
    Ls['fill'] = area('fill', (0.55, -0.80, 0.05), (0.5, 1.2), 2)
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.03, 0.032, 0.036, 1); bg.inputs[1].default_value = 1.0
    return Ls


def set_cam(cam, t, S, az, el, roll, lens=105):
    cam.data.lens = lens
    cam.data.sensor_width = 36; cam.data.sensor_fit = 'HORIZONTAL'
    dist = S * lens / 36.0
    a, b = math.radians(az), math.radians(el)
    t = Vector(t)
    pos = t + Vector((math.sin(a) * math.cos(b), -math.cos(a) * math.cos(b), math.sin(b))) * dist
    f = (t - pos).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    u = r.cross(f).normalized()
    ro = math.radians(roll)
    r2 = r * math.cos(ro) + u * math.sin(ro)
    u2 = -r * math.sin(ro) + u * math.cos(ro)
    m = Matrix((r2, u2, -f)).transposed().to_4x4()
    m.translation = pos
    cam.matrix_world = m


def main():
    argv = sys.argv[1:]
    out, specf = argv[0], argv[1]
    def opt(k, dflt):
        return type(dflt)(argv[argv.index(k) + 1]) if k in argv else dflt
    res = opt('--res', 1080); samples = opt('--samples', 96); only = opt('--only', '')
    os.makedirs(out, exist_ok=True)
    frames = json.load(open(specf))
    root, G, M = build()
    Ls = lights()
    sc = bpy.context.scene
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.clip_start = 0.05; cam.data.clip_end = 20
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.03
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6; sc.cycles.glossy_bounces = 4; sc.cycles.diffuse_bounces = 2
    sc.render.threads_mode = 'AUTO'
    sc.render.film_transparent = True
    sc.render.resolution_x = res; sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    try:
        sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception as ex:
        print('view', ex)
    sel = set(only.split(',')) if only else None
    for i, fr in enumerate(frames):
        if sel and fr['name'] not in sel and str(i) not in sel: continue
        dst = os.path.join(out, fr['name'] + '.png')
        if os.path.exists(dst) and '--force' not in argv: continue
        set_pose(G, M, fr.get('c', 0.0), fr.get('e', 0.0), fr.get('spin', 0.0), root)
        c = fr['cam']
        set_cam(cam, c['t'], c['S'], c['az'], c['el'], c['roll'], c.get('lens', 105))
        sc.render.filepath = dst
        bpy.context.view_layer.update()
        bpy.ops.render.render(write_still=True)
        print('RENDERED', fr['name'], flush=True)


if __name__ == '__main__':
    main()
