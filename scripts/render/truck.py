"""A cab-over truck, built procedurally in two sizes: a heavy 4x2 tractor (cabin dampers) and a light cargo truck (axle shockers).
Faces +X, front axle at x=0, ground at z=0. The cab rides on four Alaina cabin dampers; each front wheel has an Alaina shocker."""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import damper as dm
import lines as ln
import vkit as vk
import parts as pt
from vkit import lerp, interp, linterp, smooth, rbox, cyl, lathe, tube, empty, extrude_poly

HEAVY = dict(kind='heavy', XF=1.40, CL=2.25, CW=1.23, ZB=1.02, ZBELT=1.80, ZRAIL=2.74, ZROOF=2.88, WR=0.52, WW=0.29, RIM=0.286, WB=3.55, TR=1.03,
             RAILY=0.43, RAILTOP=1.00, RAILH=0.27, REAR=1.15, FLOOR=1.42, ARCH=0.68, RAKE=0.30)
LIGHT = dict(kind='light', XF=1.12, CL=1.78, CW=0.99, ZB=0.80, ZBELT=1.43, ZRAIL=2.13, ZROOF=2.24, WR=0.40, WW=0.215, RIM=0.215, WB=3.35, TR=0.83,
             RAILY=0.38, RAILTOP=0.78, RAILH=0.20, REAR=1.75, FLOOR=1.10, ARCH=0.53, RAKE=0.25)

PANELS = ['front', 'windshield', 'roof', 'back', 'door_L', 'door_R', 'side_L', 'side_R', 'glass_L', 'glass_R', 'bpillar_L', 'bpillar_R', 'qglass_L', 'qglass_R', 'grille', 'visor']
PI = {n: i for i, n in enumerate(PANELS)}
EXPLODE = {'front': ((0.85, 0, 0.10), 0.0), 'windshield': ((0.55, 0, 0.55), 0.05), 'roof': ((-0.05, 0, 1.0), 0.10), 'back': ((-0.85, 0, 0.25), 0.2),
           'door_L': ((0.05, 0.85, 0.12), 0.08), 'door_R': ((0.05, -0.85, 0.12), 0.08), 'side_L': ((-0.35, 0.70, 0.22), 0.14), 'side_R': ((-0.35, -0.70, 0.22), 0.14)}
FOLLOW = {'glass_L': 'door_L', 'glass_R': 'door_R', 'bpillar_L': 'door_L', 'bpillar_R': 'door_R', 'qglass_L': 'side_L', 'qglass_R': 'side_R', 'grille': 'front', 'visor': 'windshield'}


def materials(P):
    M = {}
    if P['kind'] == 'heavy':
        M['paint'] = vk.paint('cab_paint', (0.22, 0.225, 0.23), metallic=0.75, rough=0.27)
    else:
        M['paint'] = vk.paint('cab_paint', (0.018, 0.040, 0.085), metallic=0.75, rough=0.28)
    M['glass'] = vk.glass('cab_glass', tint=(0.30, 0.34, 0.36))
    M['rubber_t'] = vk.simple('t_rubber_hose', (0.012, 0.012, 0.013), 0.55, bump=(800, 0.03), spec=0.35)
    M['cast_dark'] = pt.cast('t_cast_dark', (0.03, 0.031, 0.034), 0.55, metal=0.5)
    M['loom'] = pt.corrugated('t_loom') if hasattr(pt, 'corrugated') else vk.simple('t_loom', (0.012, 0.012, 0.013), 0.5)
    M['airline'] = vk.simple('t_airline', (0.30, 0.03, 0.02), 0.35, coat=0.4)
    M['rad_core'] = pt.fins('t_rad_core')
    M['chamber'] = vk.simple('t_chamber', (0.02, 0.021, 0.024), 0.45, coat=0.3, bump=(700, 0.03))
    M['black_gloss'] = vk.simple('t_black_gloss', (0.012, 0.012, 0.014), 0.14, coat=0.6, ghost=True)
    M['black_trim'] = vk.simple('t_black_trim', (0.018, 0.018, 0.02), 0.55, bump=(900, 0.03), ghost=True)
    M['chrome'] = vk.simple('t_chrome', (0.9, 0.9, 0.92), 0.08, metal=1.0, ghost=True)
    M['visor'] = vk.simple('t_visor', (0.02, 0.02, 0.022), 0.2, coat=0.5, ghost=True)
    M['tyre'] = vk.simple('t_tyre', (0.014, 0.014, 0.015), 0.8, bump=(220, 0.05), spec=0.25)
    M['steel_wheel'] = vk.simple('steel_wheel', (0.62, 0.63, 0.65), 0.36, metal=0.9, coat=0.2)
    M['hub'] = vk.simple('hubm', (0.10, 0.10, 0.11), 0.42, metal=0.8)
    M['zinc'] = vk.simple('t_zinc', (0.72, 0.73, 0.75), 0.28, metal=1.0)
    M['frame'] = vk.simple('frame', (0.016, 0.0165, 0.018), 0.5, metal=0.2, bump=(500, 0.04), spec=0.35)
    M['iron'] = vk.simple('t_iron', (0.05, 0.051, 0.055), 0.55, metal=0.6, bump=(700, 0.05))
    M['steel'] = vk.simple('t_steel', (0.24, 0.245, 0.26), 0.4, metal=1.0, bump=(1500, 0.02))
    M['alu'] = vk.simple('t_alu', (0.66, 0.67, 0.69), 0.3, metal=1.0, bump=(300, 0.08))
    M['plastic'] = vk.simple('t_plastic', (0.02, 0.02, 0.022), 0.6, bump=(1200, 0.02))
    M['engine'] = vk.simple('t_engine', (0.11, 0.115, 0.125), 0.5, metal=0.9, bump=(500, 0.06))
    M['seat'] = vk.simple('t_seat', (0.04, 0.04, 0.045), 0.7, bump=(400, 0.06), spec=0.3)
    M['rubber'] = vk.simple('t_rubber', (0.016, 0.016, 0.017), 0.72, bump=(600, 0.05), spec=0.3)
    M['lens'] = vk.glass('t_lens', tint=(0.8, 0.8, 0.8), clear=0.7, ghost=False)
    M['lamp'] = vk.simple('t_lamp', (1, 1, 1), 0.3, emit=((1.0, 0.96, 0.9), 16.0))
    M['amber'] = vk.simple('t_amber', (1, 0.4, 0.05), 0.3, emit=((1.0, 0.36, 0.03), 5.0))
    M['red'] = vk.simple('t_red', (1, 0.02, 0.01), 0.3, emit=((1.0, 0.02, 0.01), 6.0))
    M['reflector'] = vk.simple('t_reflector', (0.85, 0.85, 0.88), 0.12, metal=1.0)
    M['mirror'] = vk.simple('t_mirror', (0.9, 0.9, 0.92), 0.02, metal=1.0)
    M['deck'] = vk.paint('deck_paint', (0.30, 0.32, 0.35), metallic=0.0, rough=0.42)
    M['wood'] = vk.simple('deckfloor', (0.10, 0.085, 0.07), 0.6, bump=(60, 0.2), ghost=True)
    return M


def build_cab(P, M, cab):
    XF, CL, CW, ZB, ZBELT, ZRAIL, ZROOF = (P[k] for k in ('XF', 'CL', 'CW', 'ZB', 'ZBELT', 'ZRAIL', 'ZROOF'))
    WR, ARCH = P['WR'], P['ARCH']
    k = CL / 2.25
    D0, D1 = 0.27 * k, 1.20 * k            # door
    S = sorted(set([0.0, 0.09, D0, 0.52 * k, 0.86 * k, D1 - 0.07, D1, XF - ARCH * 0.95, XF - ARCH * 0.7, XF - ARCH * 0.35, XF, XF + ARCH * 0.35, XF + ARCH * 0.7, CL - 0.09, CL]))
    S = [s for s in S if s <= CL]
    S = [s for i, s in enumerate(S) if i == 0 or s - S[i - 1] > 0.05]

    def z_low(s):
        d = s - XF
        if abs(d) < ARCH:
            return max(ZB, WR + math.sqrt(ARCH * ARCH - d * d) * 0.72 + 0.10)
        return ZB

    def station(s):
        # rounded front corners, a gentle taper at the back wall
        w = CW - 0.20 * (1 - min(1, s / 0.36)) ** 2 - 0.035 * max(0.0, (s - (CL - 0.14)) / 0.14)
        z0 = z_low(s)
        rake = P['RAKE'] * (1 - smooth(s / (0.62 * k)))
        fl = 0.035 * max(0.0, 1 - abs(s - XF) / (ARCH * 1.05)) ** 0.5     # wheel-arch flare
        pts = [(0, w - 0.03 + fl, z0), (0, w + fl * 0.8, lerp(z0, ZBELT, 0.26)), (0, w + fl * 0.3, lerp(z0, ZBELT, 0.63)), (-0.10 * rake, w - 0.014, ZBELT),
               (-rake, w - 0.12, ZRAIL), (-rake * 0.97, w - 0.24, ZROOF - 0.045), (-rake * 0.92, w * 0.55, ZROOF + 0.045), (-rake * 0.90, 0.0, ZROOF + 0.065)]
        return dict(x=XF - s, s=s, pts=pts)

    def panel_of(i, row, side):
        s = (S[i] + S[i + 1]) / 2
        if row <= 2:
            if s < D0: return PI['front']
            if s < D1: return PI['door_' + side]
            return PI['side_' + side]
        if row == 3:
            if s < D0: return PI['front']
            if s < D1 - 0.07: return PI['glass_' + side]
            if s < D1: return PI['bpillar_' + side]
            if s < CL - 0.09 and P['kind'] == 'heavy': return PI['qglass_' + side]
            return PI['side_' + side]
        return PI['roof']

    st = [station(s) for s in S]
    bm, ring = vk.loft(st, panel_of)
    J = 8

    def nose_panel(r, c):
        inner = c in (1, 2, 3, 4)
        if r == 3: return PI['windshield'] if inner else PI['front']
        if r == 1 and inner: return PI['grille']
        return PI['front']

    gf = vk.cap(bm, ring[0], J, 4, nose_panel, lambda t, u: 0.085 * (1 - u ** 2.0) * (1 - 0.35 * t), +1)
    gr = vk.cap(bm, ring[-1], J, 4, lambda r, c: PI['back'], lambda t, u: 0.012 * (1 - u * u), -1)

    class _P:
        def __init__(self, co): self.co = co.copy()
    gf = [[_P(v.co) for v in row] for row in gf]
    bm.normal_update()
    faces = [f for f in bm.faces if f.material_index == PI['grille']]
    r = bmesh.ops.inset_region(bm, faces=faces, thickness=0.03, depth=-0.035, use_even_offset=True, use_boundary=True)
    for f in r['faces']: f.material_index = PI['front']
    cr = bm.edges.layers.float.new('crease_edge')
    # cab-overs are crisp boxes: hold the corners
    for row in ring:
        for a in range(len(row) - 1):
            e = bm.edges.get((row[a], row[a + 1]))
            if e and row is ring[0]: e[cr] = 0.12
            if e and row is ring[-1]: e[cr] = 0.35
    for i in range(len(ring) - 1):
        for kk in (3, 2 * J - 2 - 3):
            e = bm.edges.get((ring[i][kk], ring[i + 1][kk]))
            if e: e[cr] = 0.38          # the belt line stays crisp
        for kk in (4, 2 * J - 2 - 4):
            e = bm.edges.get((ring[i][kk], ring[i + 1][kk]))
            if e: e[cr] = 0.2
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = vk.subdivided(bm, 3)
    mats = [M['paint']] * len(PANELS)
    for nm, mt in (('windshield', 'glass'), ('glass_L', 'glass'), ('glass_R', 'glass'), ('qglass_L', 'glass'), ('qglass_R', 'glass'),
                   ('bpillar_L', 'black_gloss'), ('bpillar_R', 'black_gloss'), ('grille', 'black_trim')):
        mats[PI[nm]] = M[mt]
    Pn = vk.split_panels(me, PANELS, mats, cab, gap=0.0025, rim=0.02)
    return Pn, gf, (D0, D1)


def leaf_spring(name, parent, M, length, loc, leaves=6, width=0.075, camber=0.07):
    """A leaf pack along X, eyes at both ends, bowed down in the middle where it clamps to the axle."""
    g = empty(name, parent, loc)
    t = 0.012
    for i in range(leaves):
        L = length * (1 - 0.14 * i)
        n = 16
        top, bot = [], []
        for a in range(n + 1):
            x = -L / 2 + L * a / n
            z = camber * (2 * x / length) ** 2 - i * (t + 0.0015)
            top.append((x, z)); bot.append((x, z - t))
        extrude_poly(f'{name}_leaf{i}', top + bot[::-1], width, M['steel'], g, axis='Y', bevel=0.002, seg=1)
    for sgn in (-1, 1):
        lathe(f'{name}_eye{sgn}', [(0.012, -width / 2), (0.026, -width / 2, 0.002), (0.026, width / 2, 0.002), (0.012, width / 2), (0.012, -width / 2)], M['steel'], g, axis='Y', seg=32, rad=0.002,
              loc=(sgn * length / 2, 0, camber + 0.014))
    for sgn in (-1, 1):
        tube(f'{name}_ubolt{sgn}', [(sgn * 0.055, -width / 2 - 0.012, -0.16), (sgn * 0.055, -width / 2 - 0.012, 0.03), (sgn * 0.055, width / 2 + 0.012, 0.03), (sgn * 0.055, width / 2 + 0.012, -0.16)],
             0.009, M['zinc'], g, smooth_path=False)
    rbox(name + '_plate', (0.17, width + 0.05, 0.02), M['iron'], g, loc=(0, 0, 0.022), r=0.004)
    rbox(name + '_lowplate', (0.15, width + 0.06, 0.018), M['iron'], g, loc=(0, 0, -0.15), r=0.004)
    for sgn in (-1, 1):
        for sy in (-1, 1):
            dm.hex_nut(f'{name}_ubn{sgn}{sy}', M['zinc'], 0.0135, 0.016, -0.176, g).location = (sgn * 0.055, sy * (width / 2 + 0.012), 0)
    # rebound clips around the pack
    for sgn in (-1, 1):
        x = sgn * length * 0.28
        tube(f'{name}_clip{sgn}', [(x, -width / 2 - 0.006, camber * (2 * x / length) ** 2 - leaves * 0.0135 - 0.004), (x, -width / 2 - 0.006, camber * (2 * x / length) ** 2 + 0.008),
                                   (x, width / 2 + 0.006, camber * (2 * x / length) ** 2 + 0.008), (x, width / 2 + 0.006, camber * (2 * x / length) ** 2 - leaves * 0.0135 - 0.004)], 0.004, M['steel'], g, smooth_path=False)
    return g


M_SH = {}


def shock_unit(name, parent, loc, top, sg=1, face=(0.62, 0.78, 0.0)):
    """An Alaina shocker between a lower eye at `loc` and an upper mount at `top`, its printed side turned toward `face`.
    Returns the handles that move."""
    root, G, SM = ln.build_shock(reset=False)
    root.name = name; root.parent = parent
    v = Vector(top) - Vector(loc)
    L = v.length
    z = v.normalized()
    f = Vector(face); f = (f - f.dot(z) * z).normalized()
    y = -f; x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(loc)
    root.matrix_local = m
    # through-bolts with nuts at both eyes, along the eye axis
    ax = Vector(y)
    for k, p in enumerate((Vector(loc), Vector(top))):
        o = cyl(f'{name}_bolt{k}', 0.0075, 0.11, M_SH['zinc'], parent, loc=p[:], axis='Z', seg=16)
        o.rotation_euler = ax.to_track_quat('Z', 'Y').to_euler()
        for e, hh in ((-1, 0.0125), (1, 0.011)):
            n = dm.hex_nut(f'{name}_bn{k}{e}', M_SH['zinc'], hh, 0.010, -0.005, parent)
            n.location = (p + ax * e * 0.050)[:]; n.rotation_euler = ax.to_track_quat('Z', 'Y').to_euler()
    rest = 0.482                      # eye to the top of the stem, fully out
    return dict(root=root, upper=G['upper'], c0=max(0.0, rest - L), mats=SM)


def cabin_damper(name, parent, loc, yaw=0.0):
    """An Alaina cabin damper standing on its lower eye. Returns handles: rod/shield/top move down by the compression."""
    root, G, DM = dm.build(reset=False)
    root.name = name; root.parent = parent; root.location = loc
    root.rotation_euler = (0, 0, yaw)
    d = dm.D
    z0 = d['seatZ'] + d['wire']
    h = d['topSeatZ'] - 0.0025 - d['wire'] - z0
    hold = empty(name + '_spring', G['spring'], (0, 0, z0))
    dm.coil_mesh(name + '_coil', DM['spring'], d['coilR'], d['wire'], h, parent=hold)
    return dict(root=root, G=G, spring=hold, h=h, mats=DM)


def ARCHX(P):
    return P['ARCH'] * 0.98


def snapper(objs):
    """Nearest point (and its normal) on a set of panel meshes, in the cab's frame."""
    from mathutils.kdtree import KDTree
    pts = [(v.co.copy(), v.normal.copy()) for o in objs for v in o.data.vertices]
    kd = KDTree(len(pts))
    for i, (co, _) in enumerate(pts): kd.insert(co, i)
    kd.balance()
    def snap(p):
        co, i, _ = kd.find(Vector(p))
        return co, pts[i][1]
    return snap


def gasket(name, ob, mat, parent, r=0.011, out=0.006):
    """A rubber surround along a panel's open edge (windscreen, door glass)."""
    me = ob.data
    edges = [e for e in me.edges if e.is_loose is False]
    count = {}
    for poly in me.polygons:
        for ek in poly.edge_keys: count[ek] = count.get(ek, 0) + 1
    bnd = [ek for ek, n in count.items() if n == 1]
    if not bnd: return None
    adj = {}
    for a, b in bnd: adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    start = bnd[0][0]; loop = [start]; prev = None; cur = start
    while True:
        nxt = [v for v in adj[cur] if v != prev]
        if not nxt or nxt[0] == start or len(loop) > len(adj) + 1: break
        prev, cur = cur, nxt[0]; loop.append(cur)
    vs = me.vertices
    co = [vs[i].co + vs[i].normal * (0.020 + out) for i in loop]
    co = co[::max(1, len(co) // 160)]
    return tube(name, [c[:] for c in co], r, mat, parent, smooth_path=True, cyclic=True)


def air_brake(name, parent, M, pos, sg, line_to, k=1.0, spring=True):
    """Air brake chamber on its bracket, push rod to a slack adjuster on the camshaft, and the air line up to the frame."""
    p = Vector(pos)
    r = 0.075 * (0.8 + 0.2 * k)
    prof = [(0.0, 0.0), (r * 0.9, 0.0, 0.01), (r, 0.03, 0.01), (r * 1.06, 0.045, 0.004), (r * 1.06, 0.052, 0.002), (r, 0.066, 0.01), (r * 0.95, 0.10, 0.012), (0.0, 0.11)]
    if spring: prof = prof[:-1] + [(r * 0.95, 0.16, 0.01), (r * 1.0, 0.175, 0.004), (r * 0.9, 0.24, 0.02), (0.0, 0.245)]
    lathe(name + '_can', prof, M['chamber'], parent, axis='X', seg=48, rad=0.0, loc=(p.x + 0.02, p.y, p.z), rot=(0, 0, math.pi))
    lathe(name + '_clamp', [(r * 1.06, 0.042), (r * 1.12, 0.044, 0.003), (r * 1.12, 0.054, 0.003), (r * 1.06, 0.056)], M['zinc'], parent, axis='X', seg=48, rad=0.0, loc=(p.x + 0.02, p.y, p.z), rot=(0, 0, math.pi))
    cyl(name + '_rod', 0.008, 0.10, M['zinc'], parent, loc=(p.x + 0.07, p.y, p.z), axis='X', seg=16)
    rbox(name + '_slack', (0.035, 0.03, 0.17), M['cast_dark'], parent, loc=(p.x + 0.12, p.y, p.z - 0.06), rot=(0, math.radians(-12), 0), r=0.008)
    cyl(name + '_cam', 0.02, 0.22, M['iron'], parent, loc=(p.x + 0.13, p.y + sg * 0.10, p.z - 0.13), axis='Y', seg=24)
    rbox(name + '_bracket', (0.012, 0.16, 0.16), M['cast_dark'], parent, loc=(p.x + 0.035, p.y, p.z), r=0.004)
    q = Vector(line_to)
    pt.hose(name + '_line', parent, dict(M, rubber=M['rubber_t']), [(p.x - 0.03, p.y, p.z + r * 0.8), (p.x - 0.06, p.y, p.z + 0.16), ((p.x + q.x) / 2, (p.y + q.y) / 2, q.z + 0.02), (q.x, q.y + sg * 0.04, q.z)], r=0.007)


def build(P):
    M = materials(P)
    M_SH.clear(); M_SH.update(M)
    XF, CL, CW, ZB, ZBELT, ZRAIL, ZROOF = (P[k] for k in ('XF', 'CL', 'CW', 'ZB', 'ZBELT', 'ZRAIL', 'ZROOF'))
    WR, WW, RIM, WB, TR = (P[k] for k in ('WR', 'WW', 'RIM', 'WB', 'TR'))
    RY, RT, RH, FLOOR = P['RAILY'], P['RAILTOP'], P['RAILH'], P['FLOOR']
    heavy = P['kind'] == 'heavy'
    k = CL / 2.25
    truck = empty('truck')
    cab = empty('cab', truck)                    # everything that rides on the cabin dampers
    Pn, gf, (D0, D1) = build_cab(P, M, cab)
    C = {nm: empty('carry_' + nm, cab) for nm in EXPLODE}
    for nm, ob in Pn.items():
        ob.parent = C.get(nm) or C.get(FOLLOW.get(nm, ''), cab)

    # ── cab details ──
    wsz = ZRAIL - ZBELT
    for side, sg in (('L', 1), ('R', -1)):
        # tall mirrors on arms
        mx = XF - 0.10
        tube('mirror_arm_' + side, [(mx - 0.12, sg * (CW - 0.03), ZBELT + wsz * 0.9), (mx + 0.06, sg * (CW + 0.20), ZBELT + wsz * 0.86), (mx + 0.06, sg * (CW + 0.22), ZBELT + wsz * 0.2), (mx - 0.12, sg * (CW - 0.01), ZBELT + wsz * 0.08)],
             0.011, M['black_trim'], C['door_' + side], smooth_path=False)
        rbox('mirror_' + side, (0.07, 0.19 * k + 0.02, 0.40 * k), M['black_trim'], C['door_' + side], loc=(mx + 0.06, sg * (CW + 0.24), ZBELT + wsz * 0.56), rot=(0, 0, sg * math.radians(-14)), r=0.03, seg=4)
        rbox('mirror_glass_' + side, (0.004, 0.16 * k + 0.01, 0.35 * k), M['mirror'], C['door_' + side], loc=(mx + 0.022, sg * (CW + 0.23), ZBELT + wsz * 0.56), rot=(0, 0, sg * math.radians(-14)), r=0.0015)
        rbox('handle_' + side, (0.16, 0.025, 0.04), M['black_trim'], C['door_' + side], loc=(XF - D1 + 0.16, sg * (CW + 0.004), ZBELT - 0.14), r=0.012)
        # mudguard over the wheel and the steps up to the door
        n = 14
        arc = [(P['ARCH'] * 0.98 * math.cos(math.pi * a / n), WR + P['ARCH'] * 0.72 * math.sin(math.pi * a / n) + 0.085) for a in range(n + 1)]
        inner = [(x * 0.94, z - 0.03) for x, z in arc[::-1]]
        extrude_poly('mudguard_' + side, arc + inner, WW + 0.10, M['black_trim'], truck, axis='Y', bevel=0.006, loc=(0, sg * (TR - 0.01), 0))
        for i, zf in enumerate((0.42, 0.72)):
            rbox(f'step_{side}{i}', (0.36 * k, 0.20, 0.035), M['black_trim'], truck, loc=(XF - (D0 + D1) / 2 + 0.16 * k, sg * (CW - 0.11), lerp(0.36, ZB, zf)), r=0.01)
        rbox('stepbox_' + side, (0.42 * k, 0.24, ZB - 0.42), M['black_trim'], truck, loc=(XF - (D0 + D1) / 2 + 0.16 * k, sg * (CW - 0.22), (ZB + 0.42) / 2 + 0.01), r=0.03)
        rbox('marker_' + side, (0.05, 0.02, 0.03), M['amber'], C['roof'], loc=(XF - P['RAKE'] - 0.12, sg * (CW - 0.22), ZROOF + 0.015), r=0.008)
    for i in (-1, 0, 1):
        rbox(f'marker_c{i}', (0.04, 0.07, 0.022), M['amber'], C['roof'], loc=(XF - P['RAKE'] * 0.93 - 0.05, i * 0.22, ZROOF + 0.045), r=0.008)
    # sun visor and wipers
    vz = ZRAIL - 0.03
    snap = snapper([Pn['windshield'], Pn['roof'], Pn['front']])
    q, n = snap((XF, 0, ZRAIL + 0.02))
    rbox('visor', (0.24, 2 * (CW - 0.20), 0.022), M['visor'], C['windshield'], loc=(q.x + 0.10, 0, q.z + 0.03), rot=(0, math.radians(9), 0), r=0.010, taper=(0, (0.92, 0.6)))
    for sgn in (-1, 1):
        rbox(f'visor_bracket{sgn}', (0.12, 0.03, 0.05), M['visor'], C['windshield'], loc=(q.x + 0.02, sgn * (CW - 0.40), q.z + 0.02), r=0.008)
    for sgn in (-1, 1):
        rake_ang = math.atan2(P['RAKE'], ZRAIL - ZBELT)
        ws = snapper([Pn['windshield']])
        pa, na = ws((XF + 0.1, sgn * 0.42 - 0.18, ZBELT + 0.06)); pb, nb = ws((XF, sgn * 0.42 + 0.30, ZBELT + 0.40 * k))
        pt.wiper(f'wiper{sgn}', C['windshield'], dict(M, black_satin=M['black_trim'], rubber=M['black_trim']), (pa + na * 0.004)[:], (pb + nb * 0.004)[:], up=((na + nb) / 2)[:], arm_r=0.008)
    # grille bars and badge plate
    gz0, gz1 = gf[1][3].co.z, gf[2][3].co.z
    gx = gf[1][3].co.x
    for i in range(4):
        rbox(f'grille_bar{i}', (0.03, 2 * (CW - 0.30), 0.022), M['chrome'] if i == 3 else M['black_gloss'], C['front'], loc=(gx - 0.012, 0, lerp(gz0, gz1, 0.14 + 0.24 * i)), r=0.008)
    rbox('badge', (0.012, 0.42, 0.075), M['chrome'], C['front'], loc=(gf[2][3].co.x + 0.004, 0, lerp(gf[2][3].co.z, gf[3][3].co.z, 0.5)), r=0.004)

    # rubber surrounds on the screen and the door glass
    gasket('gasket_ws', Pn['windshield'], M['black_trim'], C['windshield'], r=0.013)
    for side in ('L', 'R'):
        gasket('gasket_' + side, Pn['glass_' + side], M['black_trim'], C['door_' + side], r=0.010)
    side_snap = snapper([Pn['side_L'], Pn['side_R'], Pn['door_L'], Pn['door_R'], Pn['front']])
    for side, sg in (('L', 1), ('R', -1)):
        # grab handle on the A-pillar edge beside the door
        a, na = side_snap((XF - D0 + 0.03, sg * CW, ZBELT - 0.32)); b, nb = side_snap((XF - D0 + 0.03, sg * CW, ZBELT + 0.18))
        tube('grab_' + side, [a[:], (a + na * 0.05)[:], (b + nb * 0.05)[:], b[:]], 0.013, M['chrome'], C['door_' + side], smooth_path=True)
        # cab-side air intake behind the door (heavy cab), a slatted grille set into the side panel
        if heavy:
            c, nc = side_snap((XF - D1 - 0.24 * k, sg * CW, lerp(ZBELT, ZRAIL, 0.35)))
            yaw = math.atan2(nc.y, nc.x) - math.pi / 2 * sg
            rbox('intake_' + side, (0.34 * k, 0.03, 0.46), M['black_gloss'], C['side_' + side], loc=(c - nc * 0.004)[:], rot=(0, 0, yaw + math.pi / 2 * sg - math.pi / 2 * sg), r=0.02)
            for i in range(9):
                rbox(f'intake_slat_{side}{i}', (0.30 * k, 0.03, 0.012), M['black_trim'], C['side_' + side], loc=(c.x, c.y + nc.y * 0.008, c.z - 0.19 + i * 0.0475), rot=(math.radians(-25) * sg, 0, 0), r=0.004)
        # wide-angle mirror under the main head
        mx = XF - 0.10
        rbox('mirror_wide_' + side, (0.07, 0.17 * k + 0.02, 0.17 * k), M['black_trim'], C['door_' + side], loc=(mx + 0.06, sg * (CW + 0.24), ZBELT + wsz * 0.18), rot=(0, 0, sg * math.radians(-18)), r=0.03, seg=4)
        rbox('mirror_wide_glass_' + side, (0.004, 0.15 * k + 0.01, 0.15 * k - 0.01), M['mirror'], C['door_' + side], loc=(mx + 0.022, sg * (CW + 0.235), ZBELT + wsz * 0.18), rot=(0, 0, sg * math.radians(-18)), r=0.0015)
        # mudflap behind the front wheel
        rbox('mudflap_' + side, (0.012, WW + 0.06, 0.36), M['black_trim'], truck, loc=(-ARCHX(P) - 0.02, sg * (TR - 0.01), 0.36), r=0.004)

    # ── cab floor and interior (stay on the dampers when the panels leave) ──
    rbox('cab_floor', (CL - 0.12, 2 * CW - 0.14, 0.07), M['frame'], cab, loc=(XF - CL / 2, 0, FLOOR), r=0.02)
    rbox('cab_tunnel', (CL * 0.62, 0.78 * k, 0.26 * k), M['plastic'], cab, loc=(XF - CL * 0.52, 0, FLOOR + 0.15 * k), r=0.07, seg=4)
    rbox('dash', (0.36 * k, 2 * CW - 0.3, 0.30 * k), M['plastic'], cab, loc=(XF - 0.36 * k, 0, ZBELT - 0.12 * k), r=0.09 * k, seg=5)
    for sg in (1, -1):
        sx = XF - 1.15 * k
        rbox(f'seat_c{sg}', (0.50, 0.50, 0.14), M['seat'], cab, loc=(sx, sg * (CW - 0.50), FLOOR + 0.36 * k), r=0.06, seg=5)
        rbox(f'seat_base{sg}', (0.34, 0.36, 0.26 * k), M['plastic'], cab, loc=(sx, sg * (CW - 0.50), FLOOR + 0.16 * k), r=0.03)
        rbox(f'seat_b{sg}', (0.13, 0.48, 0.66), M['seat'], cab, loc=(sx - 0.30, sg * (CW - 0.50), FLOOR + 0.36 * k + 0.36), rot=(0, math.radians(-12), 0), r=0.055, seg=5)
        rbox(f'seat_h{sg}', (0.09, 0.26, 0.18), M['seat'], cab, loc=(sx - 0.37, sg * (CW - 0.50), FLOOR + 0.36 * k + 0.78), rot=(0, math.radians(-10), 0), r=0.04, seg=5)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.22 * (0.8 + 0.2 * k), minor_radius=0.017, major_segments=48, minor_segments=12)
    t = bpy.context.active_object; t.name = 'steering_wheel'; t.parent = cab; t.data.materials.append(M['plastic'])
    for p in t.data.polygons: p.use_smooth = True
    t.location = (XF - 0.68 * k, -(CW - 0.50), ZBELT + 0.02); t.rotation_euler = (0, math.radians(40), 0)
    cyl('column', 0.025, 0.5 * k, M['plastic'], cab, loc=(XF - 0.54 * k, -(CW - 0.50), ZBELT - 0.16 * k), axis='X', rot=(0, math.radians(-50), 0))

    # ── chassis ──
    ch = empty('chassis', truck)
    xr = -WB - P['REAR']
    x0 = XF - 0.30
    for sg in (1, -1):
        prof = [(-0.04, RT), (0.04, RT), (0.04, RT - 0.012), (-0.028, RT - 0.012), (-0.028, RT - RH + 0.012), (0.04, RT - RH + 0.012), (0.04, RT - RH), (-0.04, RT - RH)]
        ob = extrude_poly('rail' + str(sg), [(sg * a, b) for a, b in prof] if sg > 0 else [(-a, b) for a, b in prof][::-1], x0 - xr, M['frame'], ch, axis='X', bevel=0.003, seg=1, loc=((x0 + xr) / 2, sg * RY, 0))
    nx = 6
    for i in range(nx):
        cx = lerp(x0 - 0.05, xr + 0.08, i / (nx - 1))
        if abs(cx - (-WB)) < 0.3: cx += 0.42
        rbox(f'xmember{i}', (0.09, 2 * RY - 0.04, RH * 0.7), M['frame'], ch, loc=(cx, 0, RT - RH / 2), r=0.012)
    # bumper with lamps
    bz0, bz1 = (0.42, ZB - 0.04)
    bx = XF - 0.02
    # sculpted bumper: a chin lip, a lamp shelf and corners that wrap back, with a step in each corner
    prof = [(-0.34, bz0 + 0.04), (-0.04, bz0), (0.035, bz0 + 0.035), (0.05, lerp(bz0, bz1, 0.42)), (0.03, lerp(bz0, bz1, 0.48)), (0.04, bz1 - 0.07), (0.0, bz1), (-0.34, bz1)]
    extrude_poly('bumper', prof, 2 * CW - 0.52, M['black_trim'], ch, axis='Y', bevel=0.02, seg=4, loc=(bx - 0.02, 0, 0))
    for sg in (1, -1):
        o = extrude_poly(f'bumper_corner{sg}', prof, 0.36, M['black_trim'], ch, axis='Y', bevel=0.02, seg=4, loc=(bx - 0.13, sg * (CW - 0.11), 0))
        o.rotation_euler = (0, 0, sg * math.radians(38))
        rbox(f'bumper_step{sg}', (0.16, 0.24, 0.05), M['black_gloss'], ch, loc=(bx - 0.03, sg * (CW - 0.30), lerp(bz0, bz1, 0.30)), r=0.01)
        rbox(f'bumper_tread{sg}', (0.17, 0.22, 0.012), M['alu'], ch, loc=(bx - 0.02, sg * (CW - 0.30), lerp(bz0, bz1, 0.30) + 0.026), r=0.004)
    rbox('bumper_cap', (0.10, 2 * CW - 0.62, 0.05), M['paint'], ch, loc=(bx - 0.01, 0, bz1 - 0.02), r=0.02)
    rbox('bumper_face', (0.04, 2 * CW - 0.9, (bz1 - bz0) * 0.36), M['black_gloss'], ch, loc=(bx + 0.045, 0, lerp(bz0, bz1, 0.36)), r=0.015)
    pm = pt.label('t_plate', os.path.join(vk.HDRI_DIR, 'plate_%s.png' % P['kind']), (1040, 230), pt.plate_art('MH 14 GT 7045' if heavy else 'MH 12 LT 3318'), base=(0.92, 0.74, 0.06), ghost=False)
    nt = pm.node_tree; nt.links.new(nt.nodes['Separate XYZ'].outputs[1], nt.nodes['Combine XYZ'].inputs[0])
    rbox('plate', (0.012, 0.50, 0.12), pm, ch, loc=(bx + 0.07, 0, lerp(bz0, bz1, 0.36)), r=0.004)
    for sg in (1, -1):
        ly = sg * (CW - 0.30)
        rbox(f'lamp_pod{sg}', (0.10, 0.44, (bz1 - bz0) * 0.52), M['black_gloss'], ch, loc=(bx + 0.012, ly, lerp(bz0, bz1, 0.62)), r=0.035, seg=4)
        for j, (dy, mat) in enumerate(((0.09, 'lamp'), (-0.10, 'reflector'))):
            lathe(f'lamp{sg}{j}', [(0.0, 0.0), (0.045, 0.0, 0.004), (0.078, 0.022, 0.01), (0.082, 0.034)], M['reflector'], ch, axis='X', seg=48, rad=0.003, loc=(bx + 0.03, ly + sg * dy, lerp(bz0, bz1, 0.64)))
            lathe(f'bulb{sg}{j}', [(0.0, 0.016), (0.03 if mat == 'lamp' else 0.02, 0.016, 0.006), (0.034 if mat == 'lamp' else 0.022, 0.004)], M['lamp'], ch, axis='X', seg=32, rad=0.003, loc=(bx + 0.03, ly + sg * dy, lerp(bz0, bz1, 0.64)))
            lathe(f'lens{sg}{j}', [(0.0, 0.040), (0.06, 0.040, 0.02), (0.084, 0.034, 0.004), (0.084, 0.03)], M['lens'], ch, axis='X', seg=48, rad=0.002, loc=(bx + 0.03, ly + sg * dy, lerp(bz0, bz1, 0.64)))
        rbox(f'indicator{sg}', (0.03, 0.10, 0.05), M['amber'], ch, loc=(bx + 0.05, sg * (CW - 0.07), lerp(bz0, bz1, 0.64)), r=0.012)
        rbox(f'fog{sg}', (0.03, 0.13, 0.05), M['lamp'], ch, loc=(bx + 0.055, sg * (CW - 0.36), lerp(bz0, bz1, 0.2)), r=0.014)
    # power unit under the cab
    ez = RT - RH - 0.12
    rbox('engine', (1.15 * k, 0.56, 0.62 * k), M['engine'], ch, loc=(XF - 1.1 * k, 0, ez + 0.36 * k), r=0.04)
    rbox('head', (1.05 * k, 0.40, 0.14), M['steel'], ch, loc=(XF - 1.1 * k, 0, ez + 0.72 * k + 0.05), r=0.03)
    rbox('sump', (0.8 * k, 0.40, 0.18), M['engine'], ch, loc=(XF - 1.1 * k, 0, ez + 0.02), r=0.05, seg=4)
    # radiator: a finned core between plastic side tanks, in a shroud
    rw, rh = 0.82 * k + 0.1, 0.78 * k
    rz = ez + 0.44 * k
    rbox('radiator', (0.06, rw - 0.12, rh - 0.06), M['rad_core'], ch, loc=(XF - 0.34, 0, rz), r=0.004, seg=1)
    for sgn in (-1, 1):
        rbox(f'rad_tank{sgn}', (0.09, 0.07, rh), M['plastic'], ch, loc=(XF - 0.34, sgn * (rw / 2 - 0.03), rz), r=0.015)
        cyl(f'rad_neck{sgn}', 0.025, 0.08, M['plastic'], ch, loc=(XF - 0.40, sgn * (rw / 2 - 0.03), rz + sgn * rh * 0.3), axis='X', seg=24)
    rbox('rad_top', (0.08, rw - 0.10, 0.04), M['plastic'], ch, loc=(XF - 0.34, 0, rz + rh / 2), r=0.01)
    tube('rad_hose_top', [(XF - 0.40, rw / 2 - 0.03, rz + rh * 0.3), (XF - 0.55, rw / 2 - 0.12, rz + rh * 0.32), (XF - 0.80 * k, 0.12, ez + 0.70 * k)], 0.028, M['rubber_t'], ch)
    tube('rad_hose_bot', [(XF - 0.40, -(rw / 2 - 0.03), rz - rh * 0.3), (XF - 0.60, -(rw / 2 - 0.15), rz - rh * 0.36), (XF - 0.85 * k, -0.15, ez + 0.20 * k)], 0.028, M['rubber_t'], ch)
    lathe('fan', [(0.0, 0.0), (0.30 * k, 0.0, 0.004), (0.30 * k, 0.03, 0.004), (0.0, 0.03)], M['plastic'], ch, axis='X', seg=48, rad=0.003, loc=(XF - 0.45, 0, ez + 0.44 * k))
    lathe('fan_shroud', [(0.31 * k, 0.0), (0.36 * k, 0.0, 0.01), (0.36 * k, 0.10, 0.01), (0.33 * k, 0.12)], M['plastic'], ch, axis='X', seg=64, rad=0.0, loc=(XF - 0.50, 0, ez + 0.44 * k))
    lathe('gearbox', [(0.0, 0.0), (0.24 * k, 0.0, 0.03), (0.26 * k, 0.25, 0.02), (0.18 * k, 0.45, 0.04), (0.16 * k, 0.75 * k, 0.03), (0.07, 0.80 * k, 0.01), (0.0, 0.80 * k)], M['alu'], ch, axis='X', seg=48, rad=0.01,
          loc=(XF - 1.7 * k, 0, ez + 0.30 * k), rot=(0, 0, math.pi))
    px0 = XF - 1.7 * k - 0.80 * k
    cyl('propshaft', 0.045, abs(-WB + 0.35 - px0), M['steel'], ch, loc=((px0 + (-WB + 0.35)) / 2, 0, lerp(ez + 0.30 * k, WR, 0.5)), axis='X',
        rot=(0, math.atan2(ez + 0.30 * k - WR, abs(-WB + 0.35 - px0)) * -1, 0))
    tube('exhaust', [(XF - 1.3 * k, -0.30, ez + 0.5 * k), (XF - 1.9 * k, -0.34, ez + 0.2), (XF - CL - 0.2, -RY - 0.25, RT - 0.3)], 0.05, M['steel'], ch)
    # tanks and boxes along the frame
    tx = XF - CL - 0.75 if heavy else -1.15
    tl = 1.05 if heavy else 0.8
    tr_ = 0.30 if heavy else 0.21
    lathe('fuel_tank', [(0.0, -tl / 2), (tr_, -tl / 2, 0.06), (tr_, tl / 2, 0.06), (0.0, tl / 2)], M['alu'], ch, axis='X', seg=64, rad=0.04, loc=(tx, RY + tr_ + 0.08, RT - RH * 0.5 - 0.06))
    for sgn in (-1, 1):
        lathe(f'tank_strap{sgn}', [(tr_ + 0.002, -0.025), (tr_ + 0.007, -0.025, 0.001), (tr_ + 0.007, 0.025, 0.001), (tr_ + 0.002, 0.025)], M['steel'], ch, axis='X', seg=64, rad=0.001, loc=(tx + sgn * tl * 0.28, RY + tr_ + 0.08, RT - RH * 0.5 - 0.06))
    lathe('tank_cap', [(0.0, 0.03), (0.045, 0.03, 0.006), (0.045, 0.0)], M['plastic'], ch, axis='Z', seg=32, rad=0.004, loc=(tx + tl * 0.2, RY + tr_ + 0.08, RT - RH * 0.5 - 0.06 + tr_))
    rbox('battery_box', (0.62 * k, 0.42 * k, 0.44 * k), M['black_trim'], ch, loc=(tx, -(RY + 0.30 * k), RT - RH * 0.5 - 0.06), r=0.03)
    for i in range(2):
        lathe(f'air_tank{i}', [(0.0, -0.3 * k), (0.11 * k, -0.3 * k, 0.05), (0.11 * k, 0.3 * k, 0.05), (0.0, 0.3 * k)], M['frame'], ch, axis='X', seg=48, rad=0.04, loc=(tx - 0.95 * k, -(RY + 0.16 + 0.25 * i * k), RT - RH - 0.06))
    if heavy:
        rbox('muffler', (0.36, 0.34, 0.62), M['steel'], ch, loc=(XF - CL - 0.26, -(RY + 0.30), RT + 0.36), r=0.05, seg=4)
        cyl('stack', 0.062, 1.1, M['steel'], ch, loc=(XF - CL - 0.26, -(RY + 0.30), RT + 1.20), axis='Z')
        lathe('stack_tip', [(0.062, 0.0), (0.072, 0.0, 0.002), (0.072, 0.18, 0.002), (0.062, 0.18), (0.062, 0.0)], M['chrome'], ch, axis='Z', seg=48, rad=0.002, loc=(XF - CL - 0.26, -(RY + 0.30), RT + 1.66))
        # fifth wheel
        fx = -WB + 0.25
        rbox('fw_base', (0.9, 2 * RY + 0.2, 0.06), M['frame'], ch, loc=(fx, 0, RT + 0.03), r=0.012)
        lathe('fifth_wheel', [(0.0, 0.0), (0.46, 0.0, 0.01), (0.47, 0.045, 0.012), (0.0, 0.045)], M['iron'], ch, axis='Z', seg=64, rad=0.006, loc=(fx, 0, RT + 0.16), rot=(0, math.radians(2), 0))
        for sg in (1, -1):
            rbox(f'fw_leg{sg}', (0.34, 0.07, 0.11), M['iron'], ch, loc=(fx, sg * 0.30, RT + 0.11), r=0.02)
            rbox(f'ramp{sg}', (0.70, 0.24, 0.06), M['frame'], ch, loc=(xr + 0.42, sg * RY, RT + 0.02), rot=(0, math.radians(7), 0), r=0.012)
            # rear mudguards
            n = 12
            arc = [((WR + 0.13) * math.cos(math.pi * a / n), WR + (WR + 0.13) * math.sin(math.pi * a / n)) for a in range(n + 1)]
            inner = [(x * 0.965, WR + (z - WR) * 0.965) for x, z in arc[::-1]]
            extrude_poly(f'rear_guard{sg}', arc + inner, 2 * WW + 0.12, M['black_trim'], ch, axis='Y', bevel=0.005, loc=(-WB, sg * (TR - WW / 2 - 0.02), 0))
        rbox('rear_bar', (0.07, 2 * TR + 0.3, 0.12), M['frame'], ch, loc=(xr + 0.02, 0, RT - RH / 2), r=0.02)
        for sg in (1, -1):
            rbox(f'tail{sg}', (0.03, 0.30, 0.10), M['red'], ch, loc=(xr - 0.02, sg * (TR - 0.05), RT - RH / 2), r=0.02)
        deckC = None
    else:
        # dropside cargo deck on a subframe
        deckC = empty('carry_deck', truck)
        dx0 = XF - CL - 0.08; dl = dx0 - xr; dw = CW * 2 + 0.06; dz = RT + 0.12
        for sg in (1, -1):
            rbox(f'sub{sg}', (dl - 0.1, 0.07, 0.10), M['frame'], ch, loc=((dx0 + xr) / 2, sg * RY, RT + 0.05), r=0.01)
        rbox('deck_floor', (dl, dw, 0.05), M['wood'], deckC, loc=((dx0 + xr) / 2, 0, dz + 0.025), r=0.008)
        for i in range(7):
            rbox(f'deck_bearer{i}', (0.06, dw - 0.04, 0.06), M['deck'], deckC, loc=(lerp(dx0 - 0.1, xr + 0.1, i / 6), 0, dz - 0.03), r=0.008)
        sh = 0.46
        for sg in (1, -1):
            rbox(f'side{sg}', (dl - 0.06, 0.035, sh), M['deck'], deckC, loc=((dx0 + xr) / 2, sg * (dw / 2 - 0.018), dz + 0.05 + sh / 2), r=0.008)
            for i in range(3):
                rbox(f'side_rib{sg}{i}', (dl - 0.10, 0.012, 0.035), M['deck'], deckC, loc=((dx0 + xr) / 2, sg * (dw / 2 + 0.004), dz + 0.05 + sh * (0.2 + 0.3 * i)), r=0.005)
            for i in range(4):
                rbox(f'post{sg}{i}', (0.06, 0.05, sh + 0.06), M['deck'], deckC, loc=(lerp(dx0 - 0.03, xr + 0.03, i / 3), sg * (dw / 2 - 0.012), dz + 0.05 + sh / 2), r=0.008)
        rbox('headboard', (0.04, dw, sh + 0.42), M['deck'], deckC, loc=(dx0 - 0.02, 0, dz + 0.05 + (sh + 0.42) / 2), r=0.008)
        rbox('tailgate', (0.035, dw - 0.08, sh), M['deck'], deckC, loc=(xr + 0.02, 0, dz + 0.05 + sh / 2), r=0.008)
        for sg in (1, -1):
            rbox(f'tail{sg}', (0.03, 0.22, 0.09), M['red'], ch, loc=(xr - 0.0, sg * (CW - 0.2), RT - RH - 0.02), r=0.02)
            n = 12
            arc = [((WR + 0.10) * math.cos(math.pi * a / n), WR + (WR + 0.10) * math.sin(math.pi * a / n)) for a in range(n + 1)]
            inner = [(x * 0.965, WR + (z - WR) * 0.965) for x, z in arc[::-1]]
            extrude_poly(f'rear_guard{sg}', arc + inner, 2 * WW + 0.10, M['black_trim'], ch, axis='Y', bevel=0.005, loc=(-WB, sg * (TR - WW / 2 - 0.02), 0))
        rbox('rear_bar', (0.06, 2 * CW - 0.1, 0.10), M['frame'], ch, loc=(xr + 0.02, 0, RT - RH - 0.02), r=0.02)

    # ── axles, springs, wheels, shockers ──
    WM = dict(M)
    WM['tyre'] = vk.simple('t_tyre_fl', (0.014, 0.014, 0.015), 0.8, bump=(220, 0.05), spec=0.25, ghost=True)
    WM['steel_wheel'] = vk.simple('steel_wheel_fl', (0.62, 0.63, 0.65), 0.36, metal=0.9, coat=0.2, ghost=True)
    WM['hub'] = vk.simple('hub_fl', (0.10, 0.10, 0.11), 0.42, metal=0.8, ghost=True)
    WM['zinc'] = vk.simple('t_zinc_fl', (0.72, 0.73, 0.75), 0.28, metal=1.0, ghost=True)
    wheels = {}
    # front axle: I-beam, dropped in the middle
    az = WR - 0.02
    tube('front_axle', [(0, -TR + 0.22, az), (0, -RY - 0.12, az), (0, -RY + 0.05, az - 0.10), (0, RY - 0.05, az - 0.10), (0, RY + 0.12, az), (0, TR - 0.22, az)], 0.05 * (0.8 + 0.2 * k), M['iron'], ch, smooth_path=False)
    shocks = {}
    for key, sg in (('FL', 1), ('FR', -1)):
        off = empty('wheel_off_' + key, truck)
        hold, spin = vk.truck_wheel('wheel_' + key, off, WM if key == 'FL' else M, R=WR, W=WW, rimR=RIM, loc=(0, sg * TR, WR), flip=sg < 0, front=True)
        hubh = empty('hub_' + key, truck, (0, sg * TR, WR), (0, 0, 0 if sg > 0 else math.pi))
        hubs = empty('hubspin_' + key, hubh)
        dr = RIM - 0.04
        lathe('drum_' + key, [(0.0, -0.02), (dr, -0.02, 0.004), (dr, -0.02 - WW * 0.55, 0.008), (dr - 0.03, -0.02 - WW * 0.6, 0.004), (0.09, -0.02 - WW * 0.6)], M['iron'], hubs, axis='Y', seg=64, rad=0.004)
        lathe('hubflange_' + key, [(0.0, 0.05), (0.10, 0.05, 0.004), (0.165, 0.02, 0.004), (0.165, -0.02)], M['hub'], hubs, axis='Y', seg=48, rad=0.003)
        for i in range(10):
            a = vk.TAU * (i + 0.5) / 10
            cyl(f'hstud_{key}{i}', 0.011, 0.09, M['zinc'], hubs, loc=((0.122 if heavy else 0.122 * 0.8) * math.sin(a), 0.05, (0.122 if heavy else 0.122 * 0.8) * math.cos(a)), axis='Y', seg=12)
        sl = 1.35 * (0.75 + 0.25 * k)
        leaf_spring('leaf_' + key, ch, M, sl, (0, sg * RY, az + 0.075), leaves=7 if heavy else 5, width=0.09 if heavy else 0.07, camber=0.075)
        for sgn in (-1, 1):
            rbox(f'hanger_{key}{sgn}', (0.10, 0.11, RT - RH - (az + 0.15) + 0.06), M['frame'], ch, loc=(sgn * sl / 2, sg * RY, (RT - RH + az + 0.15) / 2 + 0.02), r=0.012)
        # the shocker: lower eye beside the spring seat on the axle, top on a bracket high on the frame rail
        lo = (0.17, sg * (RY + 0.16), az + 0.04)
        hi = (0.20, sg * (RY + 0.10), az + 0.04 + 0.455)
        rbox('shock_lo_' + key, (0.10, 0.20, 0.07), M['iron'], ch, loc=(0.13, sg * (RY + 0.10), az + 0.0), r=0.014)
        rbox('shock_hi_' + key, (0.12, 0.14, 0.20), M['frame'], ch, loc=(0.20, sg * (RY + 0.06), az + 0.04 + 0.44), r=0.014)
        shocks[key] = shock_unit('shock_' + key, ch, lo, hi, sg)
        wheels[key] = dict(off=off, spin=spin, hubspin=hubs, sg=sg)
        air_brake('brake_' + key, ch, M, (-0.17, sg * (TR - 0.36), az + 0.05), sg, (-0.10, sg * RY, RT - RH * 0.6), k)
    # rear axle with differential, dual wheels
    lathe('rear_axle', [(0.0, -TR + 0.1), (0.07, -TR + 0.1, 0.01), (0.075, -0.30, 0.02), (0.11, -0.22, 0.03), (0.11, 0.22, 0.03), (0.075, 0.30, 0.02), (0.07, TR - 0.1, 0.01), (0.0, TR - 0.1)], M['iron'], ch, axis='Y', seg=48, rad=0.01,
          loc=(-WB, 0, WR))
    lathe('diff', [(0.0, -0.20), (0.15, -0.16, 0.06), (0.24 * (0.7 + 0.3 * k), 0.0, 0.10), (0.15, 0.16, 0.06), (0.10, 0.28, 0.03), (0.0, 0.30)], M['iron'], ch, axis='X', seg=48, rad=0.03, loc=(-WB + 0.02, 0, WR))
    for key, sg in (('RL', 1), ('RR', -1)):
        off = empty('wheel_off_' + key, truck)
        hold, spin = vk.truck_wheel('wheel_' + key, off, M, R=WR, W=WW, rimR=RIM, loc=(-WB, sg * (TR + WW * 0.35), WR), flip=sg < 0, dual=True, front=False)
        sl = 1.45 * (0.75 + 0.25 * k)
        leaf_spring('leaf_' + key, ch, M, sl, (-WB, sg * RY, WR + 0.11), leaves=9 if heavy else 6, width=0.09 if heavy else 0.07, camber=0.06)
        for sgn in (-1, 1):
            rbox(f'hanger_{key}{sgn}', (0.10, 0.11, max(0.08, RT - RH - (WR + 0.17) + 0.06)), M['frame'], ch, loc=(-WB + sgn * sl / 2, sg * RY, (RT - RH + WR + 0.17) / 2 + 0.02), r=0.012)
        lo = (-WB - 0.20, sg * (RY + 0.15), WR + 0.02)
        hi = (-WB - 0.26, sg * (RY + 0.09), WR + 0.02 + 0.455)
        rbox('shock_lo_' + key, (0.10, 0.20, 0.07), M['iron'], ch, loc=(-WB - 0.16, sg * (RY + 0.10), WR - 0.02), r=0.014)
        rbox('shock_hi_' + key, (0.12, 0.14, 0.20), M['frame'], ch, loc=(-WB - 0.26, sg * (RY + 0.05), WR + 0.02 + 0.44), r=0.014)
        shocks[key] = shock_unit('shock_' + key, ch, lo, hi, sg)
        wheels[key] = dict(off=off, spin=spin, hubspin=None, sg=sg)
        air_brake('brake_' + key, ch, M, (-WB + 0.17, sg * (TR - 0.42), WR + 0.06), sg, (-WB + 0.45, sg * RY, RT - RH * 0.6), k, spring=True)

    # ── cabin dampers: two at the front corners, two under the back wall ──
    dampers = {}
    dz = FLOOR - 0.035 - dm.D['topEyeZ']           # lower eye height so the top eye meets the cab floor
    for key, x, y in (('FL', XF - 0.34, CW - 0.30), ('FR', XF - 0.34, -(CW - 0.30)), ('RL', XF - CL + 0.16, CW - 0.42), ('RR', XF - CL + 0.16, -(CW - 0.42))):
        dampers[key] = cabin_damper('cabdamper_' + key, ch, (x, y, dz), yaw=math.pi / 2)
        sgy = 1 if y > 0 else -1
        # outrigger from the frame rail to the lower eye, and the cab-side bracket above
        rbox('cabmount_arm_' + key, (0.12, abs(y) - RY + 0.10, 0.08), M['frame'], ch, loc=(x, sgy * (RY + abs(y)) / 2, dz - 0.075), r=0.014)
        rbox('cabmount_post_' + key, (0.10, 0.10, max(0.05, dz - 0.04 - (RT - RH / 2))), M['frame'], ch, loc=(x, sgy * (RY + 0.03), (dz - 0.04 + RT - RH / 2) / 2), r=0.014)
        for e in (-1, 1):
            rbox(f'cabmount_ear_{key}{e}', (0.012, 0.075, 0.09), M['frame'], ch, loc=(x + e * 0.036, y, dz - 0.012), r=0.004)
            rbox(f'cabmount_top_{key}{e}', (0.012, 0.075, 0.10), M['frame'], cab, loc=(x + e * 0.036, y, dz + dm.D['topEyeZ'] + 0.008), r=0.004)
        cyl('cabmount_pin_' + key, 0.0085, 0.11, M['zinc'], ch, loc=(x, y, dz), axis='X', seg=16)
        ztop = dz + dm.D['topEyeZ']
        rbox('cabmount_flange_' + key, (0.15, 0.12, 0.012), M['frame'], cab, loc=(x, y, ztop + 0.060), r=0.003)
        for ex in (-1, 1):
            for ey in (-1, 1):
                dm.hex_nut(f'cabmount_bolt_{key}{ex}{ey}', M['zinc'], 0.0085, 0.008, ztop + 0.050 - 0.008, cab).location = (x + ex * 0.055, y + ey * 0.042, 0)
        # bolted bracket on the outer web of the rail where the outrigger meets it, with a row of bolt heads
        rbox('railplate_' + key, (0.26, 0.012, RH * 0.85), M['frame'], ch, loc=(x, sgy * (RY + 0.046), RT - RH / 2), r=0.004)
        for ex in (-0.09, -0.03, 0.03, 0.09):
            for ez_ in (-0.06, 0.06):
                n = dm.hex_nut(f'railbolt_{key}{ex}{ez_}', M['zinc'], 0.010, 0.010, 0, ch)
                n.rotation_euler = (-sgy * math.pi / 2, 0, 0); n.location = (x + ex, sgy * (RY + 0.052), RT - RH / 2 + ez_)
        for ex in (-0.04, 0.04):
            dm.hex_nut(f'armbolt_{key}{ex}', M['zinc'], 0.010, 0.009, dz - 0.035, ch).location = (x + ex, sgy * (RY + 0.08), 0)
    # the cab floor crossmembers the front mounts hang from
    for xc in (XF - 0.34, XF - CL + 0.16):
        rbox(f'cab_xmember{xc:.2f}', (0.11, 2 * CW - 0.30, 0.075), M['frame'], cab, loc=(xc - 0.15, 0, FLOOR - 0.035 - 0.040), r=0.008)
        for i in range(9):
            dm.hex_nut(f'xm_bolt{xc:.2f}_{i}', M['zinc'], 0.008, 0.007, FLOOR - 0.035 - 0.085, cab).location = (xc - 0.15 + 0.035 * (1 if i % 2 else -1), lerp(-(CW - 0.25), CW - 0.25, i / 8), 0)
    # wiring loom and air lines along the outside of both rails, held in P-clips
    for sg in (1, -1):
        y0 = sg * (RY + 0.065)
        for nm, dy, dz_, r_, mat in (('loom', 0.0, -0.05, 0.013, M['loom']), ('airline_a', 0.012, 0.035, 0.0065, M['airline']), ('airline_b', 0.026, 0.035, 0.0065, M['rubber_t'])):
            tube(f'{nm}{sg}', [(XF - 0.05, y0 + sg * dy, RT + dz_ - 0.02), (XF - 0.6, y0 + sg * dy, RT + dz_), (XF - 1.6, y0 + sg * dy, RT + dz_), (XF - CL - 0.6, y0 + sg * dy, RT + dz_ + 0.01)], r_, mat, ch)
        for i in range(7):
            xc = XF - 0.25 - i * 0.32
            rbox(f'pclip{sg}{i}', (0.018, 0.05, 0.12), M['zinc'], ch, loc=(xc, y0 + sg * 0.01, RT - 0.005), r=0.004)
    cab_ghosts = [M[kk] for kk in ('paint', 'glass', 'black_gloss', 'black_trim', 'chrome', 'visor')]
    extra_ghosts = [M['deck'], M['wood']]
    wheel_ghosts = [WM[kk] for kk in ('tyre', 'steel_wheel', 'hub', 'zinc')]
    return dict(truck=truck, cab=cab, chassis=ch, carriers=C, panels=Pn, wheels=wheels, shocks=shocks, dampers=dampers, deck=deckC, M=M, P=P,
                ghosts=cab_ghosts, extra_ghosts=extra_ghosts, wheel_ghosts=wheel_ghosts)
