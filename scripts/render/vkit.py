"""Shared kit for the vehicle films: primitives, the lofted body builder, materials, studio and rig.

Everything is built procedurally, in metres. A vehicle faces +X, +Y is its left side, the ground is z=0.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import damper as dm

TAU = math.tau


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    """0 before a, 1 after b, eased in between."""
    return smooth((t - a) / (b - a)) if b > a else float(t >= b)


def lerp(a, b, t):
    return a + (b - a) * t


def interp(x, pts):
    """Smooth (Catmull-Rom) interpolation through sorted (x, y) points."""
    if x <= pts[0][0]: return pts[0][1]
    if x >= pts[-1][0]: return pts[-1][1]
    for i in range(len(pts) - 1):
        if pts[i][0] <= x <= pts[i + 1][0]:
            x0, y0 = pts[i]; x1, y1 = pts[i + 1]
            t = (x - x0) / (x1 - x0)
            xm, ym = pts[i - 1] if i > 0 else (2 * x0 - x1, 2 * y0 - y1)
            xp, yp = pts[i + 2] if i + 2 < len(pts) else (2 * x1 - x0, 2 * y1 - y0)
            m0 = (y1 - ym) / (x1 - xm) * (x1 - x0)
            m1 = (yp - y0) / (xp - x0) * (x1 - x0)
            t2, t3 = t * t, t * t * t
            return (2 * t3 - 3 * t2 + 1) * y0 + (t3 - 2 * t2 + t) * m0 + (-2 * t3 + 3 * t2) * y1 + (t3 - t2) * m1
    return pts[-1][1]


def linterp(x, pts):
    if x <= pts[0][0]: return pts[0][1]
    for i in range(len(pts) - 1):
        if x <= pts[i + 1][0]:
            x0, y0 = pts[i]; x1, y1 = pts[i + 1]
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


# ───────────────────────── objects and primitives ─────────────────────────
def empty(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.parent = parent
    e.location = loc
    e.rotation_euler = rot
    return e


def new_obj(name, bm, mat, parent=None, smooth_shade=True, sharp=None, loc=None, rot=None):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    if smooth_shade:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat is not None:
        for m in (mat if isinstance(mat, (list, tuple)) else [mat]): me.materials.append(m)
    if parent is not None: ob.parent = parent
    if sharp is not None: me.set_sharp_from_angle(angle=math.radians(sharp))
    if loc is not None: ob.location = loc
    if rot is not None: ob.rotation_euler = rot
    return ob


def rbox(name, size, mat, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), r=0.01, seg=3, taper=None):
    """Rounded box. taper=(axis, k): scales the +axis end by k in the other two directions."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, verts=bm.verts, vec=size)
    if taper:
        ax, k = taper
        ks = k if isinstance(k, (tuple, list)) else (k, k)
        others = [i for i in range(3) if i != ax]
        for v in bm.verts:
            if v.co[ax] > 0:
                v.co[others[0]] *= ks[0]; v.co[others[1]] *= ks[1]
    if r > 0:
        r = min(r, min(size) * 0.49)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=r, segments=seg, affect='EDGES', profile=0.5)
    return new_obj(name, bm, mat, parent, sharp=40, loc=loc, rot=rot)


def cyl(name, r, depth, mat, parent=None, loc=(0, 0, 0), axis='Y', seg=48, r2=None, bevel=0.0, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    if bevel > 0:
        rim = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-6 and abs(abs(e.verts[0].co.z) - depth / 2) < 1e-6
               and e.verts[0].co.xy.length > 1e-6 and e.verts[1].co.xy.length > 1e-6]
        bmesh.ops.bevel(bm, geom=rim, offset=bevel, segments=3, affect='EDGES', profile=0.5)
    if axis == 'X': bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    if axis == 'Y': bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 3, 'X'))
    return new_obj(name, bm, mat, parent, sharp=40, loc=loc, rot=rot)


def lathe(name, profile, mat, parent=None, axis='Z', seg=96, rad=0.001, loc=None, rot=None, uv_z=None):
    """dm.lathe, with the axis laid along X, Y or Z."""
    ob = dm.lathe(name, profile, mat, parent, seg=seg, uv_z=uv_z, rad=rad)
    if axis == 'Y': ob.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'X'))
    if axis == 'X': ob.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Y'))
    if loc is not None: ob.location = loc
    if rot is not None: ob.rotation_euler = rot
    return ob


def tube(name, pts, r, mat, parent=None, smooth_path=True, res=8, cyclic=False):
    """A round tube along a path (exhausts, anti-roll bars, hoses)."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r; cu.bevel_resolution = 5; cu.use_fill_caps = True
    cu.resolution_u = res
    if smooth_path:
        sp = cu.splines.new('NURBS')
        sp.points.add(len(pts) - 1)
        for p, co in zip(sp.points, pts): p.co = (*co, 1)
        sp.use_endpoint_u = True; sp.order_u = 3; sp.use_cyclic_u = cyclic
    else:
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for p, co in zip(sp.points, pts): p.co = (*co, 1)
        sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    if mat is not None: cu.materials.append(mat)
    ob.parent = parent
    return ob


def extrude_poly(name, pts, depth, mat, parent=None, axis='Y', bevel=0.004, loc=None, rot=None, seg=2):
    """Extrude a 2D outline (list of (a, b)) by `depth`, centred. axis is the extrusion direction:
    'Y' reads pts as (x, z), 'X' as (y, z), 'Z' as (x, y)."""
    bm = bmesh.new()
    if axis == 'Y': vs = [bm.verts.new((a, -depth / 2, b)) for a, b in pts]; d = (0, depth, 0)
    elif axis == 'X': vs = [bm.verts.new((-depth / 2, a, b)) for a, b in pts]; d = (depth, 0, 0)
    else: vs = [bm.verts.new((a, b, -depth / 2)) for a, b in pts]; d = (0, 0, depth)
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, verts=[v for v in r['geom'] if isinstance(v, bmesh.types.BMVert)], vec=d)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=seg, affect='EDGES', profile=0.5)
    return new_obj(name, bm, mat, parent, sharp=35, loc=loc, rot=rot)


def subdivided(bm, levels):
    """Catmull-Clark a control cage and return the result as a new mesh datablock (material indices kept)."""
    me = bpy.data.meshes.new('cage')
    bm.to_mesh(me); bm.free()
    for i in range(64): me.materials.append(None)
    ob = bpy.data.objects.new('cage', me)
    bpy.context.scene.collection.objects.link(ob)
    md = ob.modifiers.new('ss', 'SUBSURF'); md.levels = levels; md.render_levels = levels
    md.boundary_smooth = 'ALL'
    dg = bpy.context.evaluated_depsgraph_get()
    out = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)
    return out


def split_panels(me, names, mats, parent, gap=0.0018, rim=0.014):
    """Split a subdivided skin into one object per material index: each gets a small gap and a turned-in rim,
    so shut lines read as on a real body. Returns {name: object}."""
    src = bmesh.new(); src.from_mesh(me)
    src.verts.ensure_lookup_table(); src.faces.ensure_lookup_table()
    out = {}
    by = {}
    for f in src.faces: by.setdefault(f.material_index, []).append(f)
    for idx, faces in by.items():
        if idx >= len(names) or names[idx] is None: continue
        bm = bmesh.new()
        vm = {}
        for f in faces:
            vs = []
            for v in f.verts:
                if v.index not in vm:
                    nv = bm.verts.new(v.co); vm[v.index] = nv
                vs.append(vm[v.index])
            nf = bm.faces.new(vs); nf.smooth = True
        bm.normal_update()
        bedges = [e for e in bm.edges if len(e.link_faces) == 1]
        bverts = set(v for e in bedges for v in e.verts)
        move = {}
        for v in bverts:
            acc = Vector(); n = 0
            for e in v.link_edges:
                o = e.other_vert(v)
                if o not in bverts: acc += (o.co - v.co).normalized(); n += 1
            if n == 0:
                for f in v.link_faces: acc += (f.calc_center_median() - v.co).normalized(); n += 1
            if n: move[v] = acc.normalized() * gap
        normals = {v: v.normal.copy() for v in bverts}
        for v, d in move.items(): v.co += d
        r = bmesh.ops.extrude_edge_only(bm, edges=bedges)
        newv = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
        # each new vert sits over the boundary vert it came from: find it through the connecting edge
        for nv in newv:
            base = None
            for e in nv.link_edges:
                o = e.other_vert(nv)
                if o in normals: base = o; break
            if base is not None: nv.co = base.co - normals[base] * rim
        for e in bedges: e.smooth = False
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces])
        ob = new_obj(names[idx], bm, mats[idx], parent)
        out[names[idx]] = ob
    src.free()
    bpy.data.meshes.remove(me)
    return out


def loft(stations, panel_of, creases=None):
    """Build the control cage of a body from half cross-sections.
    stations: list of dicts {x, pts:[(dx, y, z)...]} from the lower edge (row 0) up and over to the centre line (last row, y=0).
    panel_of(i, row, side) -> material index for the face between stations i and i+1 and rows row and row+1.
    Returns (bm, ring) where ring[i] is the list of BMVerts across station i: left rows 0..J-1, then right rows J-2..0."""
    bm = bmesh.new()
    J = len(stations[0]['pts'])
    ring = []
    for st in stations:
        row = []
        for j in range(J):
            dx, y, z = st['pts'][j]
            row.append(bm.verts.new((st['x'] + dx, y, z)))
        for j in range(J - 2, -1, -1):
            dx, y, z = st['pts'][j]
            row.append(bm.verts.new((st['x'] + dx, -y, z)))
        ring.append(row)
    K = 2 * J - 1
    for i in range(len(stations) - 1):
        for k in range(K - 1):
            rowi = k if k < J - 1 else (K - 2 - k)
            side = 'L' if k < J - 1 else 'R'
            f = bm.faces.new((ring[i][k], ring[i + 1][k], ring[i + 1][k + 1], ring[i][k + 1]))
            f.material_index = panel_of(i, rowi, side)
    return bm, ring


def cap(bm, ring_row, J, shoulder, panel_of, bulge, sign):
    """Close an end of the loft with a grid: rows follow the side rows 0..shoulder, columns the rows shoulder..centre.
    bulge(t, u) -> forward offset (m) for height fraction t and half-width fraction u (0 centre, 1 corner).
    sign=+1 for the nose (faces +X), -1 for the tail. panel_of(row, col) -> material index. Returns the grid of verts."""
    K = 2 * J - 1
    top = ring_row[shoulder:K - shoulder]              # across the top, left shoulder → right shoulder
    left = ring_row[0:shoulder + 1]
    right = ring_row[K - 1:K - 2 - shoulder:-1]
    ncol = len(top); nrow = shoulder + 1
    z0 = left[0].co.z
    ywid = abs(top[0].co.y) or 1.0
    grid = [[None] * ncol for _ in range(nrow)]
    for r in range(nrow):
        t = (left[r].co.z - z0) / (left[shoulder].co.z - z0)
        for c in range(ncol):
            if r == shoulder: grid[r][c] = top[c]
            elif c == 0: grid[r][c] = left[r]
            elif c == ncol - 1: grid[r][c] = right[r]
            else:
                tv = top[c]
                u = abs(tv.co.y) / ywid
                zb = lerp(left[0].co.z, right[0].co.z, c / (ncol - 1))
                z = lerp(zb, tv.co.z, t)
                xedge = lerp(left[r].co.x, right[r].co.x, c / (ncol - 1))
                x = xedge + (tv.co.x - lerp(top[0].co.x, top[-1].co.x, c / (ncol - 1))) + sign * bulge(t, u)
                grid[r][c] = bm.verts.new((x, tv.co.y, z))
    for r in range(nrow - 1):
        for c in range(ncol - 1):
            vs = (grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c])
            f = bm.faces.new(vs if sign < 0 else vs[::-1])
            f.material_index = panel_of(r, c)
    return grid


# ───────────────────────── materials ─────────────────────────
GHOSTS = []   # value nodes that turn a body material into its see-through state


def _ghost_mix(nt, solid_out, tint=(0.55, 0.62, 0.75), edge=0.55, body=0.035, glow=0.22):
    """Wrap a material so one value fades it from solid to a glassy see-through shell with bright edges."""
    val = nt.nodes.new('ShaderNodeValue'); val.label = 'ghost'; val.outputs[0].default_value = 0.0
    GHOSTS.append(val)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.22
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Color'].default_value = (*tint, 1); gl.inputs['Roughness'].default_value = 0.12
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*tint, 1); em.inputs['Strength'].default_value = glow
    add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(gl.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
    # how much of the shell shows: a little everywhere, more at grazing angles
    mth = nt.nodes.new('ShaderNodeMath'); mth.operation = 'MULTIPLY_ADD'
    mth.inputs[1].default_value = edge; mth.inputs[2].default_value = body
    nt.links.new(lw.outputs['Facing'], mth.inputs[0])
    fade = nt.nodes.new('ShaderNodeValue'); fade.label = 'fade'; fade.outputs[0].default_value = 0.0   # 1 = the shell is gone
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(fade.outputs[0], inv.inputs[1])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    nt.links.new(mth.outputs[0], mul.inputs[0]); nt.links.new(inv.outputs[0], mul.inputs[1])
    mth = mul
    shell = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(mth.outputs[0], shell.inputs[0]); nt.links.new(tr.outputs[0], shell.inputs[1]); nt.links.new(add.outputs[0], shell.inputs[2])
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(val.outputs[0], mix.inputs[0]); nt.links.new(solid_out, mix.inputs[1]); nt.links.new(shell.outputs[0], mix.inputs[2])
    out = nt.nodes['Material Output']
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return val


def paint(name, color, metallic=0.0, rough=0.32, flake=True, inner=(0.035, 0.036, 0.04), ghost=True):
    """Body paint with clear coat; the inside of a panel is dark primer. Optional ghost state."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = 1.0
    b.inputs['Coat Roughness'].default_value = 0.03
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    mixc = nt.nodes.new('ShaderNodeMix'); mixc.data_type = 'RGBA'
    mixc.inputs[6].default_value = (*color, 1); mixc.inputs[7].default_value = (*inner, 1)
    nt.links.new(geo.outputs['Backfacing'], mixc.inputs[0])
    nt.links.new(mixc.outputs[2], b.inputs['Base Color'])
    if flake and metallic > 0:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2600; nz.inputs['Detail'].default_value = 1
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.02; bp.inputs['Distance'].default_value = 0.0003
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
        nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    if ghost: _ghost_mix(nt, b.outputs[0])
    return m


def glass(name, tint=(0.10, 0.13, 0.14), ghost=True, clear=0.0):
    """Window glass: reflective by Fresnel, tinted see-through otherwise (cheap to render, no caustics)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    fr = nt.nodes.new('ShaderNodeFresnel'); fr.inputs['IOR'].default_value = 1.5
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = (*[lerp(c, 1, clear) for c in tint], 1)
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.02
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(fr.outputs[0], mix.inputs[0]); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(gl.outputs[0], mix.inputs[2])
    if ghost: _ghost_mix(nt, mix.outputs[0], edge=0.4, body=0.02)
    else: nt.links.new(mix.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    return m


def simple(name, base, rough, metal=0.0, coat=0.0, bump=None, spec=0.5, ghost=False, emit=None, ghost_kw=None):
    m = dm.principled(name, base, rough, metal=metal, coat=coat, bump=bump, spec=spec)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    if emit:
        b.inputs['Emission Color'].default_value = (*emit[0], 1); b.inputs['Emission Strength'].default_value = emit[1]
    if ghost: _ghost_mix(nt, b.outputs[0], **(ghost_kw or {}))
    return m


def set_ghost(mats, g):
    for m in mats:
        for n in m.node_tree.nodes:
            if n.type == 'VALUE' and n.label == 'ghost': n.outputs[0].default_value = g


# ───────────────────────── wheels ─────────────────────────
def tyre(name, R, W, rimR, mat, parent, blocks=64, grooves=3, seg=256):
    """Tyre about the Y axis, centred at the origin, with real circumferential grooves and shoulder blocks."""
    h = W / 2
    side = R - rimR
    prof = [(rimR - 0.004, -h * 0.80), (rimR + 0.010, -h * 0.86, 0.004), (rimR + side * 0.30, -h * 0.99, 0.02), (rimR + side * 0.62, -h * 1.0, 0.03),
            (R - 0.014, -h * 0.90, 0.018), (R - 0.002, -h * 0.76, 0.01)]
    gw = 0.0075 if R < 0.4 else 0.011
    gd = 0.008 if R < 0.4 else 0.013
    xs = [(-h * 0.76) + (h * 1.52) * (i + 1) / (grooves + 1) for i in range(grooves)]
    for gx in xs:
        prof += [(R, gx - gw - 0.004), (R, gx - gw, 0.001), (R - gd, gx - gw * 0.7, 0.001), (R - gd, gx + gw * 0.7, 0.001), (R, gx + gw, 0.001), (R, gx + gw + 0.004)]
    prof += [(R - 0.002, h * 0.76, 0.01), (R - 0.014, h * 0.90, 0.018), (rimR + side * 0.62, h * 1.0, 0.03), (rimR + side * 0.30, h * 0.99, 0.02), (rimR + 0.010, h * 0.86, 0.004), (rimR - 0.004, h * 0.80)]
    ob = dm.lathe(name, prof, mat, parent, seg=seg, rad=0.004)
    # shoulder and tread blocks: cut lateral grooves into the tread surface
    me = ob.data
    edge = xs[0] - gw if xs else 0
    for v in me.vertices:
        r = math.hypot(v.co.x, v.co.y)
        if r > R - 0.0045:
            a = (math.atan2(v.co.y, v.co.x) / TAU * blocks + (0.5 if v.co.z > 0 else 0.0) + 0.18 * abs(v.co.z) / h * blocks / 8) % 1.0
            if a < 0.26 and (abs(v.co.z) > abs(edge) + 0.002 or (int(abs(v.co.z) * 400) % 2 == 0 and a < 0.12)):
                k = (r - gd * 0.75) / r
                v.co.x *= k; v.co.y *= k
    me.transform(Matrix.Rotation(-math.pi / 2, 4, 'X'))
    return ob


def alloy_wheel(name, parent, M, R=0.33, W=0.215, rimR=0.218, spokes=5, loc=(0, 0, 0), flip=False, disc=True):
    """Car wheel: tyre, alloy rim with split spokes, brake disc. The outer face looks toward +Y (flip for the right side).
    Returns (holder, spinner): rotate `spinner` about Y to roll the wheel."""
    hold = empty(name, parent, loc)
    if flip: hold.rotation_euler = (0, 0, math.pi)
    spin = empty(name + '_spin', hold)
    tyre(name + '_tyre', R, W, rimR, M['tyre'], spin)
    h = W / 2 * 0.80
    barrel = [(rimR + 0.012, -h), (rimR + 0.012, -h + 0.006, 0.002), (rimR - 0.002, -h + 0.014, 0.004), (rimR - 0.004, -h + 0.03, 0.004), (rimR - 0.024, -h + 0.05, 0.008),
              (rimR - 0.024, h - 0.07, 0.008), (rimR - 0.006, h - 0.045, 0.006), (rimR - 0.004, h - 0.016, 0.004), (rimR + 0.012, h - 0.006, 0.002), (rimR + 0.012, h),
              (rimR + 0.004, h + 0.003, 0.002), (rimR - 0.014, h - 0.004, 0.003), (rimR - 0.030, h - 0.03, 0.006), (rimR - 0.034, -h + 0.05), (rimR - 0.014, -h + 0.02), (rimR + 0.012, -h)]
    lathe(name + '_barrel', barrel, M['alloy'], spin, axis='Y', seg=128, rad=0.002)
    # spokes: tapered, slightly dished, in pairs
    face = h - 0.012
    for i in range(spokes):
        for s in (-1, 1):
            bm = bmesh.new()
            r0, r1 = 0.052, rimR - 0.016
            w0, w1 = 0.017, 0.013
            off0, off1 = s * 0.024, s * 0.055
            pts = []
            for (r, w, off, y, t) in ((r0, w0, off0, face - 0.016, 0.03), (r0 + (r1 - r0) * 0.5, (w0 + w1) / 2, (off0 + off1) / 2, face - 0.006, 0.026), (r1, w1, off1, face - 0.002, 0.03)):
                pts.append([(off - w, y, r), (off + w, y, r), (off + w * 0.7, y - t, r), (off - w * 0.7, y - t, r)])
            vs = [[bm.verts.new(p) for p in sec] for sec in pts]
            for a in range(len(vs) - 1):
                for b in range(4):
                    bm.faces.new((vs[a][b], vs[a][(b + 1) % 4], vs[a + 1][(b + 1) % 4], vs[a + 1][b]))
            bm.faces.new(vs[0][::-1]); bm.faces.new(vs[-1])
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bmesh.ops.bevel(bm, geom=[e for e in bm.edges], offset=0.0035, segments=2, affect='EDGES', profile=0.5)
            ob = new_obj(f'{name}_spoke{i}{s}', bm, M['alloy'], spin, sharp=50)
            ob.rotation_euler = (0, TAU * i / spokes, 0)
    hub = [(0.0, face - 0.006), (0.030, face - 0.006, 0.004), (0.034, face - 0.012, 0.003), (0.070, face - 0.016, 0.006), (0.074, face - 0.034, 0.003), (0.0, face - 0.034)]
    lathe(name + '_hub', hub, M['alloy'], spin, axis='Y', seg=64, rad=0.002)
    lathe(name + '_cap', [(0.0, face - 0.003), (0.024, face - 0.003, 0.003), (0.028, face - 0.008, 0.002), (0.0, face - 0.008)], M['black_gloss'], spin, axis='Y', seg=48, rad=0.001)
    for i in range(5):
        a = TAU * (i + 0.5) / 5
        n = dm.hex_nut(f'{name}_lug{i}', M['zinc'], 0.0095, 0.012, 0, spin)
        n.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'X'))
        n.location = (0.052 * math.sin(a), face - 0.026, 0.052 * math.cos(a))
    if disc:
        dR = rimR - 0.050
        dprof = [(0.060, -0.004), (dR, -0.004, 0.001), (dR, 0.008, 0.001), (dR - 0.004, 0.010), (dR - 0.004, 0.016), (dR, 0.018, 0.001), (dR, 0.030, 0.001), (dR * 0.56, 0.030, 0.002), (dR * 0.52, 0.060, 0.004), (0.060, 0.060)]
        lathe(name + '_disc', dprof, M['disc'], spin, axis='Y', seg=96, rad=0.001, loc=(0, -0.035, 0))
        # caliper does not turn
        rbox(name + '_caliper', (0.15, 0.095, 0.075), M['caliper'], hold, loc=(-0.07 * 1.0, -0.02, dR - 0.048), rot=(0, math.radians(-32), 0), r=0.018, seg=4)
    return hold, spin


def truck_wheel(name, parent, M, R=0.52, W=0.29, rimR=0.286, loc=(0, 0, 0), flip=False, dual=False, front=True):
    """Truck steel wheel with hand holes and a hub with studs; dual=True adds the inner twin."""
    hold = empty(name, parent, loc)
    if flip: hold.rotation_euler = (0, 0, math.pi)
    spin = empty(name + '_spin', hold)
    offs = [0.0] if not dual else [0.0, -(W + 0.045)]
    for k, oy in enumerate(offs):
        t = tyre(f'{name}_tyre{k}', R, W, rimR, M['tyre'], spin, blocks=56, grooves=4)
        t.location.y = oy
        h = W / 2 * 0.80
        barrel = [(rimR + 0.016, -h), (rimR + 0.016, -h + 0.008, 0.003), (rimR - 0.002, -h + 0.02, 0.005), (rimR - 0.02, -h + 0.06, 0.01), (rimR - 0.02, h - 0.06, 0.01), (rimR - 0.002, h - 0.02, 0.005),
                  (rimR + 0.016, h - 0.008, 0.003), (rimR + 0.016, h), (rimR + 0.006, h + 0.003, 0.002), (rimR - 0.012, h - 0.01, 0.004), (rimR - 0.030, h - 0.06), (rimR - 0.030, -h + 0.06), (rimR + 0.016, -h)]
        b = lathe(f'{name}_barrel{k}', barrel, M['steel_wheel'], spin, axis='Y', seg=128, rad=0.003)
        b.location.y = oy
    # the disc: dished out on a front wheel, dished in on the outer of a dual pair
    h = W / 2 * 0.80
    q = rimR / 0.286
    if front and not dual:
        prof = [(0.0, h + 0.035), (0.085 * q, h + 0.035, 0.004), (0.10 * q, h + 0.022, 0.006), (0.145 * q, h + 0.022, 0.004), (0.165 * q, h + 0.004, 0.02), (rimR - 0.06 * q, h - 0.05, 0.03), (rimR - 0.026, h - 0.085, 0.01),
                (rimR - 0.026, h - 0.10), (rimR - 0.07 * q, h - 0.064, 0.03), (0.16 * q, h - 0.008, 0.02), (0.14 * q, h + 0.010), (0.0, h + 0.010)]
        studR, studY, hubY = 0.122 * q, h + 0.022, h + 0.035
    else:
        prof = [(0.0, h - 0.13), (0.10 * q, h - 0.13, 0.004), (0.105 * q, h - 0.150, 0.004), (0.165 * q, h - 0.150, 0.004), (0.19 * q, h - 0.14, 0.02), (rimR - 0.05 * q, h - 0.045, 0.03), (rimR - 0.026, h - 0.03, 0.01),
                (rimR - 0.026, h - 0.045), (rimR - 0.06 * q, h - 0.06, 0.03), (0.18 * q, h - 0.16, 0.02), (0.0, h - 0.16)]
        studR, studY, hubY = 0.135 * q, h - 0.150, h - 0.07
    d = lathe(name + '_dish', prof, M['steel_wheel'], spin, axis='Y', seg=96, rad=0.003)
    # hand holes
    nh = 8 if not (front and not dual) else 10
    for i in range(nh):
        a = TAU * i / nh
        rr = (rimR - 0.085 * q)
        cb = bmesh.new()
        bmesh.ops.create_cone(cb, cap_ends=True, segments=24, radius1=0.026 * q, radius2=0.026 * q, depth=0.5)
        bmesh.ops.rotate(cb, verts=cb.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
        bmesh.ops.translate(cb, verts=cb.verts, vec=(rr * math.sin(a), 0, rr * math.cos(a)))
        cut = new_obj(f'{name}_hh{i}', cb, None, spin, smooth_shade=False)
        cut.hide_render = True; cut.hide_viewport = True
        md = d.modifiers.new(f'h{i}', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cut; md.solver = 'EXACT'
    # hub and studs
    if front and not dual:
        lathe(name + '_hubcap', [(0.0, hubY + 0.075 * q), (0.045 * q, hubY + 0.075 * q, 0.01), (0.062 * q, hubY + 0.05 * q, 0.01), (0.07 * q, hubY, 0.004), (0.085 * q, hubY)], M['hub'], spin, axis='Y', seg=64, rad=0.003)
    else:
        lathe(name + '_hubcap', [(0.0, hubY + 0.16 * q), (0.06 * q, hubY + 0.16 * q, 0.012), (0.085 * q, hubY + 0.12 * q, 0.012), (0.095 * q, hubY - 0.06, 0.004), (0.10 * q, hubY - 0.06)], M['hub'], spin, axis='Y', seg=64, rad=0.003)
        for i in range(8):
            a = TAU * i / 8
            n = dm.hex_nut(f'{name}_hb{i}', M['zinc'], 0.011, 0.012, 0, spin)
            n.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'X'))
            n.location = (0.045 * q * math.sin(a), hubY + 0.16 * q + 0.006, 0.045 * q * math.cos(a))
    for i in range(10):
        a = TAU * (i + 0.5) / 10
        n = dm.hex_nut(f'{name}_stud{i}', M['zinc'], 0.017 * q, 0.024, 0, spin)
        n.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'X'))
        n.location = (studR * math.sin(a), studY + 0.012, studR * math.cos(a))
    return hold, spin


# ───────────────────────── studio ─────────────────────────
def area(name, loc, size, power, color=(1, 1, 1), target=(0, 0, 0), spread=None, visible=True):
    sc = bpy.context.scene
    L = bpy.data.lights.new(name, 'AREA')
    L.shape = 'RECTANGLE'; L.size, L.size_y = size
    L.energy = power; L.color = color
    if spread: L.spread = spread
    o = bpy.data.objects.new(name, L); sc.collection.objects.link(o)
    o.location = loc
    dirv = Vector(target) - Vector(loc)
    o.rotation_euler = dirv.to_track_quat('-Z', 'Y').to_euler()
    if not visible:
        o.visible_glossy = True; o.visible_camera = False
    return o


def spot(name, loc, target, power, size=0.6, blend=0.6, color=(1, 1, 1), radius=0.05):
    sc = bpy.context.scene
    L = bpy.data.lights.new(name, 'SPOT')
    L.energy = power; L.spot_size = size; L.spot_blend = blend; L.color = color; L.shadow_soft_size = radius
    o = bpy.data.objects.new(name, L); sc.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


def keep_off_floor(lights, fl, also=()):
    """Stop these lights from lighting the floor, so their glare does not pool on it in front of the camera.
    `also` names more objects to leave out, e.g. a windscreen that would mirror a whole softbox as a white slab."""
    coll = bpy.data.collections.new('off_floor')
    for o in [fl] + list(also): coll.objects.link(o)
    for co in coll.collection_objects: co.light_linking.link_state = 'EXCLUDE'
    for L in lights: L.light_linking.receiver_collection = coll


def floor(size=120.0):
    """A dark polished studio floor: it catches the reflection and the pool of light under the vehicle."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2)
    m = bpy.data.materials.new('floor'); m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.03, 0.03, 0.032, 1)
    b.inputs['Roughness'].default_value = 0.2
    b.inputs['Specular IOR Level'].default_value = 0.5
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.5; nz.inputs['Detail'].default_value = 4
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs[1].default_value = 0.3; mr.inputs[2].default_value = 0.7
    mr.inputs[3].default_value = 0.17; mr.inputs[4].default_value = 0.23
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'], mr.inputs[0]); nt.links.new(mr.outputs[0], b.inputs['Roughness'])
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 90; n2.inputs['Detail'].default_value = 3
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.035; bp.inputs['Distance'].default_value = 0.002
    nt.links.new(tc.outputs['Object'], n2.inputs['Vector']); nt.links.new(n2.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return new_obj('floor', bm, m, smooth_shade=False)


def world(strength=1.0, color=(0.006, 0.006, 0.007)):
    sc = bpy.context.scene
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (*color, 1); bg.inputs[1].default_value = strength
    return w


def camera(lens=60):
    sc = bpy.context.scene
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.clip_start = 0.1; cam.data.clip_end = 400
    cam.data.lens = lens; cam.data.sensor_width = 36; cam.data.sensor_fit = 'HORIZONTAL'
    cam.rotation_mode = 'QUATERNION'
    return cam


def cam_matrix(target, dist, az, el, roll=0.0):
    """Camera pose looking at `target` from `dist` away: az 0 looks along +Y from the -Y side, positive az swings toward +X."""
    a, b = math.radians(az), math.radians(el)
    t = Vector(target)
    pos = t + Vector((math.sin(a) * math.cos(b), -math.cos(a) * math.cos(b), math.sin(b))) * dist
    f = (t - pos).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    u = r.cross(f).normalized()
    ro = math.radians(roll)
    r2 = r * math.cos(ro) + u * math.sin(ro)
    u2 = -r * math.sin(ro) + u * math.cos(ro)
    m = Matrix((r2, u2, -f)).transposed().to_4x4()
    m.translation = pos
    return m


def use_gpu():
    """Switch Cycles to the graphics card (Metal on a Mac, OptiX or CUDA elsewhere). Returns the device names in use."""
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('METAL', 'OPTIX', 'CUDA', 'HIP', 'ONEAPI'):
        try:
            prefs.compute_device_type = kind
        except Exception:
            continue
        prefs.get_devices() if hasattr(prefs, 'get_devices') else prefs.refresh_devices()
        devs = [d for d in prefs.devices if d.type == kind]
        if devs:
            for d in prefs.devices: d.use = d.type == kind
            bpy.context.scene.cycles.device = 'GPU'
            return [d.name for d in devs]
    return []


def render_setup(res=1080, samples=96, blur=True, threshold=0.03, gpu=False):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    if gpu: print('GPU', use_gpu() or 'none found, rendering on the CPU', flush=True)
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = threshold
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8; sc.cycles.glossy_bounces = 5; sc.cycles.diffuse_bounces = 2
    sc.cycles.transparent_max_bounces = 24; sc.cycles.transmission_bounces = 6
    sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.sample_clamp_indirect = 6.0
    sc.render.threads_mode = 'AUTO'
    sc.render.film_transparent = False
    sc.render.resolution_x = res; sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    sc.render.use_motion_blur = blur
    sc.render.motion_blur_shutter = 0.5
    try:
        sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception as ex:
        print('view', ex)
    return sc


# ───────────────────────── animation: everything is keyed per frame so motion blur is real ─────────────────────────
def value_nodes(mats, label):
    return [n.outputs[0] for m in mats for n in m.node_tree.nodes if n.type == 'VALUE' and n.label == label]


def descendants(ob):
    out = []
    for c in ob.children: out.append(c); out += descendants(c)
    return out


def hide_from(objs, frame):
    """Take objects out of the render from `frame` on (once they have faded out there is no reason to trace them)."""
    for o in objs:
        o.hide_render = False; o.keyframe_insert('hide_render', frame=frame - 1)
        o.hide_render = True; o.keyframe_insert('hide_render', frame=frame)
    for o in objs: o.hide_render = False


class Rig:
    def __init__(self):
        self.ch = []      # (id_data, data_path, index, fn(t))

    def add(self, target, path, fn, index=-1):
        self.ch.append((target, path, index, fn))

    def key(self, frames, fps, pre=1):
        """Write a key on every frame (and one either side, for the blur)."""
        for f in range(frames[0] - pre, frames[-1] + pre + 1):
            t = f / fps
            for target, path, index, fn in self.ch:
                v = fn(t)
                if index >= 0:
                    cur = getattr(target, path); cur[index] = v
                else:
                    setattr(target, path, v)
                target.keyframe_insert(path, index=index, frame=f)
        for ob in list(bpy.data.objects) + list(bpy.data.lights) + [m.node_tree for m in bpy.data.materials if m.node_tree]:
            ad = getattr(ob, 'animation_data', None)
            if not ad or not ad.action: continue
            try:
                fcs = ad.action.fcurves
            except AttributeError:
                fcs = []
                for layer in ad.action.layers:
                    for strip in layer.strips:
                        for bag in strip.channelbags: fcs += list(bag.fcurves)
            for fc in fcs:
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
