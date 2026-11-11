"""A generic mid-size saloon, built procedurally: lofted body split into real panels, glass, lamps, wheels,
a rolling chassis underneath and four Alaina struts. Faces +X, front axle at x=0, ground at z=0."""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import damper as dm
import lines as ln
import vkit as vk
import parts as pt
from vkit import lerp, interp, linterp, smooth, rbox, cyl, lathe, tube, empty, extrude_poly

XN = 0.93            # nose is this far ahead of the front axle
WB = 2.70            # wheelbase
LEN = 4.65
TR = 0.775           # half track
WR = 0.335           # tyre radius
ARCH = 0.378

W_PTS = [(0.0, 0.67), (0.06, 0.76), (0.15, 0.815), (0.30, 0.86), (0.55, 0.89), (0.93, 0.90), (1.5, 0.905), (2.5, 0.905), (3.3, 0.90), (3.63, 0.895), (4.1, 0.87), (4.4, 0.835), (4.58, 0.78), (4.65, 0.70)]
ZB_PTS = [(0.0, 0.715), (0.15, 0.755), (0.5, 0.82), (0.93, 0.875), (1.42, 0.925), (2.0, 0.95), (2.8, 0.97), (3.5, 0.995), (4.1, 1.01), (4.45, 1.005), (4.65, 0.97)]
ZT_PTS = [(0.0, 0.765), (0.06, 0.80), (0.15, 0.83), (0.5, 0.90), (0.93, 0.95), (1.30, 0.982), (1.42, 0.995), (2.20, 1.395), (2.42, 1.442), (2.74, 1.46), (3.10, 1.45), (3.36, 1.415), (3.53, 1.365),
          (4.10, 1.105), (4.30, 1.095), (4.50, 1.08), (4.60, 1.062), (4.65, 1.02)]
COWL, HEAD, RHEAD, DECK = 1.42, 2.20, 3.53, 4.10
DOOR0, BPIL0, BPIL1, DOOR2 = 1.62, 2.66, 2.72, 3.41


def z_low(s):
    for sc in (XN, XN + WB):
        d = s - sc
        if abs(d) <= ARCH + 1e-6: return WR + math.sqrt(max(0.0, ARCH * ARCH - d * d)) * 1.0
    if s < XN: return 0.19
    if s < XN + WB: return 0.185
    return linterp(s, [(XN + WB + 0.41, 0.255), (4.65, 0.30)])


def in_arch(s):
    return any(abs(s - sc) <= ARCH + 1e-6 for sc in (XN, XN + WB))


def station(s):
    w = interp(s, W_PTS)
    zb = interp(s, ZB_PTS)
    if s < COWL: zt = interp(s, [p for p in ZT_PTS if p[0] <= COWL])
    elif s > DECK: zt = interp(s, [p for p in ZT_PTS if p[0] >= DECK])
    else: zt = linterp(s, ZT_PTS)
    z0 = z_low(s)
    flare = 0.024 if in_arch(s) else 0.0
    z3 = max(zb - 0.105, z0 + 0.03)
    ysh = w - 0.05
    pts = [(0, w - 0.05 + flare, z0), (0, w - 0.014 + flare * 0.5, lerp(z0, z3, 0.2)), (0, w, lerp(z0, z3, 0.58)), (0, w - 0.004, z3), (0, ysh, zb)]
    if s < COWL or s > DECK:
        nose = max(0.0, 1 - s / 0.30) if s < COWL else 0.0
        pts += [(0.03 * nose, ysh * 0.82, lerp(zb, zt, 0.62)), (0.05 * nose, ysh * 0.45, lerp(zb, zt, 0.94)), (0.056 * nose, 0.0, zt)]
    else:
        zc, zh, zr, zd = (linterp(q, ZT_PTS) for q in (COWL, HEAD, RHEAD, DECK))
        RY5, RY6 = 0.715, 0.61          # half widths of the top of the side glass and of the roof panel
        if s < HEAD:
            t = (s - COWL) / (HEAD - COWL)
            p5 = (lerp(ysh - 0.03, RY5, t), lerp(zb + 0.012, zh - 0.078, t)); p6 = (lerp(0.75, RY6, t), lerp(zc - 0.006, zh - 0.022, t))
        elif s <= RHEAD:
            p5 = (RY5, zt - 0.078); p6 = (RY6, zt - 0.022)
        else:
            t = (s - RHEAD) / (DECK - RHEAD)
            p5 = (lerp(RY5, ysh - 0.03, t), lerp(zr - 0.078, zb + 0.012, t)); p6 = (lerp(RY6, 0.73, t), lerp(zr - 0.022, zd - 0.006, t))
        pts += [(0, p5[0], p5[1]), (0, p6[0], p6[1]), (0, 0.0, zt)]
    return dict(x=XN - s, s=s, pts=pts)


PANELS = ['bumper_f', 'bumper_r', 'hood', 'trunk', 'roof', 'windshield', 'backlight',
          'fender_L', 'fender_R', 'door_f_L', 'door_f_R', 'door_r_L', 'door_r_R', 'quarter_L', 'quarter_R',
          'glass_f_L', 'glass_f_R', 'glass_r_L', 'glass_r_R', 'bpillar_L', 'bpillar_R', 'sail_L', 'sail_R',
          'lamp_f_L', 'lamp_f_R', 'lamp_r_L', 'lamp_r_R', 'grille', 'intake', 'plate_f', 'plate_r', 'trim_r']
PI = {n: i for i, n in enumerate(PANELS)}


def panel_of_factory(S):
    def panel_of(i, row, side):
        s = (S[i] + S[i + 1]) / 2
        if row <= 3:
            if row == 3 and s < 0.15: return PI['lamp_f_' + side]
            if row == 3 and s > 4.50: return PI['lamp_r_' + side]
            if s < 0.30 or (row <= 1 and s < XN - 0.40): return PI['bumper_f']
            if s > 4.50 or (row <= 1 and s > XN + WB + 0.40): return PI['bumper_r']
            if s < DOOR0: return PI['fender_' + side]
            if s < BPIL0 + 0.03: return PI['door_f_' + side]
            if s < DOOR2: return PI['door_r_' + side]
            return PI['quarter_' + side]
        if row == 4:
            if s < COWL: return PI['hood']
            if s < DOOR0: return PI['sail_' + side]
            if s < BPIL0: return PI['glass_f_' + side]
            if s < BPIL1: return PI['bpillar_' + side]
            if s < DOOR2: return PI['glass_r_' + side]
            if s < DECK: return PI['quarter_' + side]
            return PI['trunk']
        if row == 5:
            if s < COWL: return PI['hood']
            if s < DECK: return PI['roof']
            return PI['trunk']
        if s < COWL: return PI['hood']
        if s < HEAD: return PI['windshield']
        if s < RHEAD: return PI['roof']
        if s < DECK: return PI['backlight']
        return PI['trunk']
    return panel_of


def materials():
    M = {}
    M['paint'] = vk.paint('paint', (0.048, 0.052, 0.060), metallic=0.85, rough=0.26)
    M['glass'] = vk.glass('glass', tint=(0.30, 0.34, 0.36))
    M['lens'] = vk.glass('lens', tint=(0.8, 0.8, 0.8), clear=0.6)
    M['lens_red'] = vk.simple('lens_red', (0.45, 0.01, 0.01), 0.08, coat=1.0, ghost=True, emit=((1.0, 0.03, 0.02), 1.6))
    M['black_gloss'] = vk.simple('black_gloss', (0.012, 0.012, 0.014), 0.12, coat=0.6, ghost=True)
    M['black_trim'] = vk.simple('black_trim', (0.014, 0.014, 0.015), 0.5, ghost=True)
    M['chrome'] = vk.simple('chrome', (0.9, 0.9, 0.92), 0.08, metal=1.0, ghost=True)
    M['plate'] = vk.simple('plate', (0.85, 0.85, 0.82), 0.4, ghost=True)
    M['tyre'] = vk.simple('tyre', (0.014, 0.014, 0.015), 0.78, bump=(260, 0.04), spec=0.25)
    M['alloy'] = vk.simple('alloy', (0.78, 0.79, 0.81), 0.22, metal=1.0, coat=0.3)
    M['zinc'] = vk.simple('zinc', (0.72, 0.73, 0.75), 0.28, metal=1.0)
    M['disc'] = vk.simple('disc', (0.55, 0.55, 0.56), 0.32, metal=1.0, bump=(900, 0.02))
    M['caliper'] = vk.simple('caliper', (0.30, 0.31, 0.33), 0.38, metal=1.0)
    M['iron_c'] = vk.simple('iron_c', (0.045, 0.046, 0.05), 0.55, metal=0.6, bump=(700, 0.05), ghost=True, ghost_kw=dict(tint=(0.4, 0.45, 0.55), edge=0.10, body=0.0, glow=0.04))
    M['iron'] = vk.simple('iron', (0.045, 0.046, 0.05), 0.55, metal=0.6, bump=(700, 0.05))
    M['steel'] = vk.simple('steel', (0.20, 0.205, 0.22), 0.38, metal=1.0, bump=(1500, 0.02), ghost=True, ghost_kw=dict(tint=(0.4, 0.45, 0.55), edge=0.10, body=0.0, glow=0.04))
    M['steel_h'] = vk.simple('steel_h', (0.30, 0.31, 0.33), 0.38, metal=1.0, bump=(1500, 0.02))
    M['alu'] = vk.simple('alu', (0.16, 0.165, 0.175), 0.46, metal=1.0, bump=(500, 0.06), ghost=True, ghost_kw=dict(tint=(0.4, 0.45, 0.55), edge=0.10, body=0.0, glow=0.04))
    M['ecoat'] = vk.simple('ecoat', (0.03, 0.031, 0.034), 0.5, metal=0.3, ghost=True, ghost_kw=dict(tint=(0.4, 0.45, 0.55), edge=0.10, body=0.0, glow=0.04))
    M['plastic'] = vk.simple('plastic', (0.02, 0.02, 0.022), 0.6, bump=(1200, 0.02), ghost=True, ghost_kw=dict(tint=(0.4, 0.45, 0.55), edge=0.10, body=0.0, glow=0.04))
    M['seat'] = vk.simple('seat', (0.035, 0.035, 0.038), 0.7, bump=(400, 0.06), spec=0.3, ghost=True, ghost_kw=dict(tint=(0.4, 0.45, 0.55), edge=0.10, body=0.0, glow=0.04))
    M['rubber'] = vk.simple('rubber', (0.016, 0.016, 0.017), 0.72, bump=(600, 0.05), spec=0.3)
    M['drl'] = vk.simple('drl', (1, 1, 1), 0.3, emit=((1.0, 0.97, 0.92), 14.0), ghost=True)
    M['amber'] = vk.simple('amber', (1, 0.4, 0.05), 0.3, emit=((1.0, 0.35, 0.03), 3.0), ghost=True)
    M['red_led'] = vk.simple('red_led', (1, 0.02, 0.01), 0.3, emit=((1.0, 0.02, 0.01), 9.0), ghost=True)
    M['mirror'] = vk.simple('mirror', (0.9, 0.9, 0.92), 0.02, metal=1.0, ghost=True)
    M['disc_face'] = pt.machined('disc_face', (0.42, 0.42, 0.43), 0.30)
    M['disc_core'] = pt.cast('disc_core', (0.10, 0.098, 0.095), 0.7, metal=0.7)
    M['disc_hub'] = pt.machined('disc_hub', (0.30, 0.30, 0.31), 0.34, rings=900)
    M['caliper'] = vk.simple('caliper', (0.035, 0.036, 0.04), 0.42, metal=0.3, coat=0.5)
    M['pad'] = pt.cast('pad', (0.03, 0.03, 0.03), 0.8, metal=0.1)
    M['cast'] = pt.cast('cast', (0.11, 0.112, 0.118), 0.6, metal=0.6)
    M['cast_dark'] = pt.cast('cast_dark', (0.03, 0.031, 0.034), 0.55, metal=0.5)
    M['ecoat_arm'] = vk.simple('ecoat_arm', (0.022, 0.023, 0.025), 0.42, metal=0.4, coat=0.3, bump=(900, 0.03))
    M['chrome_dark'] = vk.simple('chrome_dark', (0.30, 0.31, 0.33), 0.12, metal=1.0, ghost=True)
    M['screen'] = vk.simple('screen', (0.01, 0.012, 0.016), 0.08, coat=1.0, ghost=True, emit=((0.35, 0.55, 0.9), 0.6), ghost_kw=dict(tint=(0.4, 0.45, 0.55), edge=0.10, body=0.0, glow=0.04))
    M['black_satin'] = vk.simple('black_satin', (0.014, 0.014, 0.016), 0.38, ghost=True)
    return M


def build_body(M, sprung):
    S = [0.0, 0.06, 0.15, 0.30, XN - 0.41, XN - ARCH, XN - 0.33, XN - 0.22, XN - 0.10, XN, XN + 0.10, XN + 0.22, XN + 0.33, XN + ARCH, XN + 0.41,
         COWL, DOOR0, 1.90, HEAD, 2.42, BPIL0, BPIL1, 2.98, XN + WB - 0.41, XN + WB - ARCH, XN + WB - 0.33, XN + WB - 0.22, XN + WB - 0.10, XN + WB, XN + WB + 0.10, XN + WB + 0.22,
         XN + WB + 0.33, XN + WB + ARCH, XN + WB + 0.41, DECK, 4.30, 4.50, 4.60, 4.65]
    # the stations just outside each arch sit at sill height, so the arch edge drops straight down to the sill
    st = [station(s) for s in S]
    for a in st:
        for sc in (XN, XN + WB):
            if abs(abs(a['s'] - sc) - 0.41) < 1e-6:
                pass
    bm, ring = vk.loft(st, panel_of_factory(S))
    J = 8

    def nose_bulge(t, u):
        return 0.06 * (1 - u ** 2.6) * (0.6 + 0.4 * math.sin(math.pi * min(1.0, t * 1.1))) + 0.025 * (1 - u * u)

    def nose_panel(r, c):
        mid = c in (2, 3); inner = c in (1, 2, 3, 4)
        if r == 3: return PI['grille'] if inner else (PI['lamp_f_L'] if c == 0 else PI['lamp_f_R'])
        if r == 2: return PI['plate_f'] if mid else PI['bumper_f']
        return PI['intake'] if inner else PI['bumper_f']

    def tail_bulge(t, u):
        return 0.05 * (1 - u ** 2.4) * (0.6 + 0.4 * math.sin(math.pi * t))

    def tail_panel(r, c):
        mid = c in (2, 3)
        if r == 3: return PI['trim_r'] if c in (1, 2, 3, 4) else (PI['lamp_r_L'] if c == 0 else PI['lamp_r_R'])
        if r == 2: return PI['plate_r'] if mid else PI['trunk']
        return PI['bumper_r']

    gf = vk.cap(bm, ring[0], J, 4, nose_panel, nose_bulge, +1)
    gr = vk.cap(bm, ring[-1], J, 4, tail_panel, tail_bulge, -1)
    class _P:
        def __init__(self, co): self.co = co.copy()
    gf = [[_P(v.co) for v in row] for row in gf]
    gr = [[_P(v.co) for v in row] for row in gr]
    bm.normal_update()
    # recess the grille, intake and number plates so they are real openings, not paint
    for names, thick, depth in ((('grille',), 0.012, 0.03), (('intake',), 0.02, 0.05), (('plate_f', 'plate_r'), 0.012, 0.012)):
        for nm in names:
            faces = [f for f in bm.faces if f.material_index == PI[nm]]
            if not faces: continue
            host = PI['bumper_f'] if nm in ('grille', 'intake', 'plate_f') else PI['trunk']
            r = bmesh.ops.inset_region(bm, faces=faces, thickness=thick, depth=-depth, use_even_offset=True, use_boundary=True)
            for f in r['faces']: f.material_index = host
    cr = bm.edges.layers.float.new('crease_edge')
    bm.verts.ensure_lookup_table()
    # a crisper shoulder line along the body side
    for i in range(len(ring) - 1):
        for k in (4, 2 * J - 2 - 4):
            e = bm.edges.get((ring[i][k], ring[i + 1][k]))
            if e and COWL - 0.2 < S[i] < DECK + 0.3: e[cr] = 0.45
        for k in (3, 2 * J - 2 - 3):
            e = bm.edges.get((ring[i][k], ring[i + 1][k]))
            if e: e[cr] = 0.3
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = vk.subdivided(bm, 3)
    mats = [M['paint']] * len(PANELS)
    for nm, mt in (('windshield', 'glass'), ('backlight', 'glass'), ('glass_f_L', 'glass'), ('glass_f_R', 'glass'), ('glass_r_L', 'glass'), ('glass_r_R', 'glass'),
                   ('bpillar_L', 'black_gloss'), ('bpillar_R', 'black_gloss'), ('sail_L', 'black_gloss'), ('sail_R', 'black_gloss'),
                   ('lamp_f_L', 'lens'), ('lamp_f_R', 'lens'), ('lamp_r_L', 'lens_red'), ('lamp_r_R', 'lens_red'),
                   ('grille', 'black_gloss'), ('intake', 'black_trim'), ('plate_f', 'plate'), ('plate_r', 'plate'), ('trim_r', 'chrome')):
        mats[PI[nm]] = M[mt]
    P = vk.split_panels(me, PANELS, mats, sprung)
    return P, gf, gr


# how far each panel travels when the car comes apart (metres, in the car's frame) and when it leaves (0..1 of the move)
EXPLODE = {
    'hood': ((0.45, 0, 0.62), 0.00), 'windshield': ((0.16, 0, 0.78), 0.06), 'roof': ((-0.05, 0, 0.92), 0.10), 'backlight': ((-0.30, 0, 0.74), 0.14), 'trunk': ((-0.52, 0, 0.56), 0.18),
    'bumper_f': ((0.62, 0, 0.02), 0.02), 'bumper_r': ((-0.62, 0, 0.02), 0.20),
    'fender_L': ((0.20, 0.52, 0.10), 0.04), 'fender_R': ((0.20, -0.52, 0.10), 0.04),
    'door_f_L': ((0.0, 0.70, 0.04), 0.08), 'door_f_R': ((0.0, -0.70, 0.04), 0.08),
    'door_r_L': ((-0.06, 0.66, 0.04), 0.12), 'door_r_R': ((-0.06, -0.66, 0.04), 0.12),
    'quarter_L': ((-0.26, 0.50, 0.12), 0.16), 'quarter_R': ((-0.26, -0.50, 0.12), 0.16),
}
FOLLOW = {'glass_f_L': 'door_f_L', 'glass_f_R': 'door_f_R', 'glass_r_L': 'door_r_L', 'glass_r_R': 'door_r_R', 'bpillar_L': 'door_r_L', 'bpillar_R': 'door_r_R',
          'sail_L': 'door_f_L', 'sail_R': 'door_f_R', 'lamp_f_L': 'bumper_f', 'lamp_f_R': 'bumper_f', 'lamp_r_L': 'bumper_r', 'lamp_r_R': 'bumper_r',
          'grille': 'bumper_f', 'intake': 'bumper_f', 'plate_f': 'bumper_f', 'plate_r': 'trunk', 'trim_r': 'trunk'}


DECAL_TURN = {'FL': -0.14, 'RL': -0.38}   # turn the print on the hero struts toward the close-up camera


def strut_unit(name, parent, M, loc, side, decal=0.0):
    """An Alaina strut as fitted: body and bracket, coil spring, bump stop and top mount. side=+1 left, -1 right.
    Returns a dict with the parts that move when the suspension works."""
    root, G, SM = ln.build_strut(reset=False)
    root.name = name
    if decal: vk.turn_decal(SM['body'], decal)
    root.parent = parent
    root.location = loc
    root.rotation_euler = (math.radians(9 * side), math.radians(-3), math.radians(90 * side))
    d = ln.ST
    z0 = d['seatZ'] + 0.012
    h = 0.196
    spring_mat = dm.principled(name + '_spring', (0.010, 0.010, 0.012), 0.26, coat=0.7, coat_rough=0.06, bump=(900, 0.02))
    hold = empty(name + '_springhold', root, (0.004, 0, z0))
    coil = dm.coil_mesh(name + '_coil', spring_mat, 0.057, 0.0066, h, turns=4.7, parent=hold)
    top = G['rod']
    zt = z0 + h
    seat = [(0.012, zt + 0.004), (0.045, zt + 0.004, 0.003), (0.062, zt - 0.006, 0.006), (0.070, zt - 0.006, 0.002), (0.072, zt + 0.002, 0.002), (0.064, zt + 0.004, 0.003),
            (0.050, zt + 0.014, 0.006), (0.012, zt + 0.014, 0.002)]
    lathe(name + '_topseat', seat, SM['paint'], top, rad=0.0015)
    lathe(name + '_mount', [(0.012, zt + 0.014), (0.052, zt + 0.014, 0.004), (0.058, zt + 0.030, 0.008), (0.040, zt + 0.046, 0.006), (0.012, zt + 0.046)], SM['rubber'], top, rad=0.003)
    lathe(name + '_plate', [(0.012, zt + 0.046), (0.070, zt + 0.046, 0.002), (0.070, zt + 0.051, 0.002), (0.012, zt + 0.051)], SM['zinc'], top, rad=0.001)
    for i in range(3):
        a = vk.TAU * i / 3 + 0.5
        n = dm.hex_nut(f'{name}_tn{i}', SM['zinc'], 0.0075, 0.007, zt + 0.051, top)
        n.location = (0.055 * math.cos(a), 0.055 * math.sin(a), 0)
    lathe(name + '_bump', [(0.0112, zt - 0.070), (0.020, zt - 0.070, 0.004), (0.024, zt - 0.05, 0.006), (0.021, zt - 0.036, 0.003), (0.026, zt - 0.018, 0.006), (0.024, zt + 0.002, 0.003), (0.0112, zt + 0.002)],
          dm.principled(name + '_pu', (0.86, 0.23, 0.035), 0.62, bump=(700, 0.12), spec=0.35), top, rad=0.002)
    return dict(root=root, rod=top, spring=hold, h=h, mats=SM)


def pt_cache():
    d = os.path.join(HERE, 'hdri'); os.makedirs(d, exist_ok=True); return d


def build(M=None):
    """Build the whole car into the open scene. Returns a dict of handles for the film to drive."""
    M = M or materials()
    car = empty('car')
    sprung = empty('sprung', car)
    P, gf, gr = build_body(M, sprung)
    # panels ride on carriers so a detail (handle, mirror, lamp unit) leaves with its panel
    C = {}
    for nm in EXPLODE:
        C[nm] = empty('carry_' + nm, sprung)
    for nm, ob in P.items():
        ob.parent = C.get(nm) or C.get(FOLLOW.get(nm, ''), sprung)

    # ── details on the body ──
    for side, sg in (('L', 1), ('R', -1)):
        w = interp(1.55, W_PTS)
        mx = XN - 1.58
        rbox('mirror_' + side, (0.075, 0.21, 0.125), M['paint'], C['door_f_' + side], loc=(mx, sg * (w + 0.10), 1.005), rot=(0, 0, sg * math.radians(-12)), r=0.035, seg=5)
        rbox('mirror_arm_' + side, (0.05, 0.10, 0.03), M['black_gloss'], C['door_f_' + side], loc=(mx - 0.005, sg * (w - 0.02), 0.975), r=0.012)
        rbox('mirror_glass_' + side, (0.004, 0.17, 0.095), M['mirror'], C['door_f_' + side], loc=(mx - 0.039, sg * (w + 0.10), 1.005), rot=(0, 0, sg * math.radians(-12)), r=0.0015)
        for dn, hs in (('door_f_', 2.50), ('door_r_', 3.27)):
            wh = interp(hs, W_PTS)
            rbox(f'handle_{dn}{side}', (0.17, 0.022, 0.026), M['chrome'], C[dn + side], loc=(XN - hs, sg * (wh + 0.004), interp(hs, ZB_PTS) - 0.085), r=0.009)
        # daytime running light: a blade behind the lens, following the corner
        row3, row4 = gf[3], gf[4]
        cols = (0, 1, 2) if sg > 0 else (6, 5, 4)
        pts = []
        s0 = station(0.0); s1 = station(0.10)
        pts.append((XN - 0.13, sg * (interp(0.13, W_PTS) - 0.035), lerp(s1['pts'][3][2], s1['pts'][4][2], 0.5)))
        for c in cols:
            a, b = row3[c].co, row4[c].co
            pts.append(((a.x + b.x) / 2 - 0.028, (a.y + b.y) / 2 * 0.985, (a.z + b.z) / 2 + 0.002))
        tube('drl_' + side, pts[:3] + [lerp(Vector(pts[2]), Vector(pts[3]), 0.55)[:]], 0.0065, M['drl'], C['bumper_f'])
        back = [(p[0] - 0.035, p[1] * 0.97, p[2]) for p in pts]
        tube('lampback_' + side, back, 0.036, M['chrome_dark'], C['bumper_f'])
        for k, f in enumerate((0.35, 0.72)):
            p = lerp(Vector(pts[1]), Vector(pts[2]), f)
            lathe(f'proj_{side}{k}', [(0.0, 0.0), (0.016, -0.004, 0.006), (0.021, -0.016, 0.004), (0.021, -0.03)], M['chrome'], C['bumper_f'], axis='X', seg=32, rad=0.002, loc=(p.x - 0.004, p.y, p.z + 0.012))
        # rear light bar behind the red lens
        rpts = []
        r3, r4 = gr[3], gr[4]
        s2 = station(4.56)
        rpts.append((XN - 4.53, sg * (interp(4.53, W_PTS) - 0.03), lerp(s2['pts'][3][2], s2['pts'][4][2], 0.5)))
        for c in ((0, 1) if sg > 0 else (6, 5)):
            a, b = r3[c].co, r4[c].co
            rpts.append(((a.x + b.x) / 2 + 0.024, (a.y + b.y) / 2 * 0.985, (a.z + b.z) / 2))
        tube('tail_' + side, rpts, 0.006, M['red_led'], C['bumper_r'])
    rbox('grille_bar', (0.02, 0.86, 0.012), M['chrome'], C['bumper_f'], loc=(gf[3][3].co.x - 0.012, 0, (gf[3][3].co.z + gf[4][3].co.z) / 2), r=0.004)
    for k in range(3):
        rbox(f'intake_bar{k}', (0.02, 0.9, 0.012), M['black_gloss'], C['bumper_f'], loc=(gf[0][3].co.x - 0.035, 0, lerp(gf[0][3].co.z, gf[2][3].co.z, 0.25 + 0.25 * k)), r=0.004)
    rbox('fin', (0.16, 0.035, 0.05), M['black_gloss'], C['roof'], loc=(XN - 3.36, 0, linterp(3.36, ZT_PTS) + 0.012), r=0.014, taper=(0, (0.5, 0.4)))

    # grille and lower intake: a fine slatted mesh behind the openings
    def row_x(r0, r1, y):
        cols = sorted(range(len(gf[r0])), key=lambda c: gf[r0][c].co.y)
        ys = [gf[r0][c].co.y for c in cols]
        xs = [(gf[r0][c].co.x + gf[r1][c].co.x) / 2 for c in cols]
        return linterp(y, list(zip(ys, xs)))
    for nm, r0, r1, depth, pitch in (('grille', 3, 4, 0.024, 0.026), ('intake', 0, 2, 0.045, 0.030)):
        y0, y1 = sorted((gf[r0][1].co.y, gf[r0][5].co.y))
        z0 = min(gf[r0][3].co.z, gf[r1][3].co.z); z1 = max(gf[r0][3].co.z, gf[r1][3].co.z)
        n = int((y1 - y0) / pitch)
        for k in range(n + 1):
            y = lerp(y0 + 0.01, y1 - 0.01, k / n)
            rbox(f'{nm}_slat{k}', (0.022, 0.005, (z1 - z0) * 0.80), M['black_gloss'], C['bumper_f'], loc=(row_x(r0, r1, y) - depth, y, (z0 + z1) / 2), rot=(0, 0, math.radians(30)), r=0.0015, seg=1)
    # number plates, front and back
    for nm, host, sign, txt in (('plate_f', 'bumper_f', 1, 'MH 12 AL 2026'), ('plate_r', 'trunk', -1, 'MH 12 AL 2026')):
        vs = [v.co for v in P[nm].data.vertices]
        cy = sum(v.y for v in vs) / len(vs); cz = sum(v.z for v in vs) / len(vs)
        xe = max(v.x for v in vs) if sign > 0 else min(v.x for v in vs)
        pm = pt.label('plate_art_' + nm, os.path.join(pt_cache(), 'plate.png'), (1040, 230), pt.plate_art(txt), base=(0.86, 0.86, 0.84), face=sign)
        M['plate_art_' + nm] = pm
        if sign > 0:
            nt = pm.node_tree; nt.links.new(nt.nodes['Separate XYZ'].outputs[1], nt.nodes['Combine XYZ'].inputs[0])
        rbox(nm + '_board', (0.006, 0.50, 0.11), pm, C[FOLLOW.get(nm, host)] if FOLLOW.get(nm) in C else C[host], loc=(xe + sign * 0.002, cy, cz), r=0.002, seg=1)
    # wipers parked along the foot of the windscreen
    up = Vector((0.40, 0, 0.78)).normalized(); WPM = dict(M, rubber=M['black_satin'])
    pt.wiper('wiper_d', C['windshield'], WPM, (-0.555, -0.40, 1.040), (-0.640, 0.28, 1.072), up=up[:])
    pt.wiper('wiper_p', C['windshield'], WPM, (-0.555, 0.06, 1.040), (-0.630, 0.64, 1.052), up=up[:])

    # ── rolling chassis ──
    ch = empty('chassis', car)
    rbox('floor', (3.25, 1.50, 0.05), M['ecoat'], ch, loc=(-1.42, 0, 0.215), r=0.02)
    rbox('tunnel', (2.2, 0.26, 0.16), M['ecoat'], ch, loc=(-1.25, 0, 0.30), r=0.06, seg=4)
    for sg in (1, -1):
        rbox('sill', (2.0, 0.13, 0.15), M['ecoat'], ch, loc=(-1.35, sg * 0.76, 0.27), r=0.04, seg=4)
        rbox('rail_f', (1.05, 0.085, 0.11), M['ecoat'], ch, loc=(0.32, sg * 0.42, 0.40), r=0.02)
        rbox('rail_r', (1.0, 0.085, 0.10), M['ecoat'], ch, loc=(-3.1, sg * 0.50, 0.36), r=0.02)
    rbox('crash_beam', (0.07, 1.30, 0.11), M['steel'], ch, loc=(0.80, 0, 0.44), r=0.02)
    rbox('rear_beam', (0.07, 1.30, 0.11), M['steel'], ch, loc=(-3.58, 0, 0.44), r=0.02)
    rbox('firewall', (0.06, 1.46, 0.50), M['ecoat'], ch, loc=(-0.52, 0, 0.50), r=0.02)
    rbox('subframe', (0.62, 1.02, 0.07), M['iron_c'], ch, loc=(-0.02, 0, 0.21), r=0.025)
    # power unit, across the car
    rbox('engine', (0.46, 0.60, 0.42), M['alu'], ch, loc=(0.10, -0.10, 0.52), r=0.03)
    rbox('engine_cover', (0.40, 0.56, 0.06), M['plastic'], ch, loc=(0.10, -0.10, 0.76), r=0.025, seg=4)
    for k in range(6):
        rbox(f'cover_rib{k}', (0.30, 0.018, 0.012), M['plastic'], ch, loc=(0.10, -0.33 + 0.092 * k, 0.795), r=0.005)
    for k, (py, pz, pr) in enumerate(((-0.42, 0.42, 0.075), (-0.42, 0.62, 0.05), (-0.42, 0.52, 0.035))):
        lathe(f'pulley{k}', [(0.0, 0.0), (pr, 0.0, 0.003), (pr, 0.008), (pr - 0.008, 0.012), (pr - 0.008, 0.022), (pr, 0.026), (pr, 0.034, 0.003), (0.0, 0.034)], M['steel'], ch, axis='Y', seg=48, rad=0.002, loc=(0.10 + 0.12 * (k - 1), py - 0.02, pz), rot=(0, 0, math.pi))
    rbox('gearbox', (0.38, 0.34, 0.34), M['alu'], ch, loc=(0.08, 0.37, 0.46), r=0.08, seg=5)
    lathe('manifold', [(0.0, -0.26), (0.035, -0.26, 0.01), (0.035, 0.26, 0.01), (0.0, 0.26)], M['steel'], ch, axis='Y', rad=0.008, loc=(0.36, -0.10, 0.62))
    rbox('radiator', (0.05, 0.72, 0.40), M['iron_c'], ch, loc=(0.70, 0, 0.52), r=0.008)
    rbox('battery', (0.24, 0.17, 0.19), M['plastic'], ch, loc=(-0.22, 0.48, 0.68), r=0.012)
    rbox('airbox', (0.26, 0.22, 0.16), M['plastic'], ch, loc=(0.20, -0.50, 0.70), r=0.03, seg=4)
    tube('intake_pipe', [(0.20, -0.42, 0.72), (0.24, -0.30, 0.80), (0.14, -0.14, 0.80)], 0.035, M['rubber'], ch)
    # cabin
    rbox('dash', (0.34, 1.40, 0.26), M['plastic'], ch, loc=(-0.74, 0, 0.83), r=0.08, seg=5)
    for sg in (1, -1):
        for xs, nm in ((-1.52, 'f'), (-2.42, 'r')):
            rbox(f'seat_c_{nm}{sg}', (0.50, 0.50, 0.14), M['seat'], ch, loc=(xs, sg * 0.37, 0.36 if nm == 'f' else 0.38), r=0.06, seg=5)
            rbox(f'seat_b_{nm}{sg}', (0.13, 0.48, 0.62), M['seat'], ch, loc=(xs - 0.30, sg * 0.37, 0.68), rot=(0, math.radians(-16), 0), r=0.055, seg=5)
            rbox(f'seat_h_{nm}{sg}', (0.09, 0.24, 0.17), M['seat'], ch, loc=(xs - 0.40, sg * 0.37, 1.08), rot=(0, math.radians(-14), 0), r=0.04, seg=5)
    sw = empty('steering', ch, (-0.98, -0.37, 0.93), (0, math.radians(68), 0))
    lathe('sw_rim', [(0.168, -0.014), (0.183, -0.016, 0.008), (0.196, -0.006, 0.008), (0.196, 0.006, 0.008), (0.183, 0.016, 0.008), (0.168, 0.012, 0.008), (0.164, -0.002, 0.006), (0.168, -0.014)], M['seat'], sw, axis='Z', seg=64, rad=0.0)
    lathe('sw_hub', [(0.0, 0.03), (0.055, 0.03, 0.015), (0.07, 0.0, 0.012), (0.06, -0.04, 0.01), (0.0, -0.04)], M['plastic'], sw, axis='Z', seg=48, rad=0.0)
    for a in (90, 210, 330):
        ar = math.radians(a)
        rbox(f'sw_spoke{a}', (0.12, 0.034, 0.014), M['plastic'], sw, loc=(0.115 * math.cos(ar), 0.115 * math.sin(ar), -0.004), rot=(0, 0, ar), r=0.006)
    # instrument screen in a hooded binnacle, the centre display and the vents
    rbox('binnacle', (0.16, 0.42, 0.10), M['plastic'], ch, loc=(-0.72, -0.37, 0.99), r=0.035, seg=4)
    rbox('cluster', (0.006, 0.36, 0.11), M['screen'], ch, loc=(-0.80, -0.37, 0.975), rot=(0, math.radians(-20), 0), r=0.003)
    rbox('display', (0.006, 0.30, 0.17), M['screen'], ch, loc=(-0.80, 0.0, 0.95), rot=(0, math.radians(-22), 0), r=0.004)
    for yv in (-0.62, -0.08, 0.08, 0.62):
        rbox(f'vent{yv}', (0.02, 0.10, 0.04), M['chrome_dark'], ch, loc=(-0.585, yv, 0.90), r=0.006)
    rbox('console', (0.55, 0.20, 0.20), M['plastic'], ch, loc=(-1.20, 0, 0.47), r=0.05, seg=4)
    lathe('shifter', [(0.0, 0.0), (0.018, 0.0, 0.002), (0.012, 0.07), (0.022, 0.09, 0.008), (0.018, 0.12, 0.008), (0.0, 0.125)], M['plastic'], ch, axis='Z', seg=32, rad=0.0, loc=(-1.05, 0, 0.57))
    cyl('column', 0.028, 0.36, M['plastic'], ch, loc=(-0.83, -0.37, 0.87), axis='X', rot=(0, math.radians(-22), 0))
    # back end
    rbox('tank', (0.55, 0.95, 0.20), M['plastic'], ch, loc=(-2.25, 0, 0.30), r=0.06, seg=4)
    tube('exhaust', [(0.34, -0.10, 0.40), (-0.2, -0.05, 0.22), (-1.2, 0.04, 0.17), (-2.2, 0.10, 0.17), (-2.9, 0.32, 0.20), (-3.2, 0.42, 0.24)], 0.028, M['steel'], ch)
    lathe('muffler', [(0.0, -0.26), (0.085, -0.26, 0.03), (0.085, 0.26, 0.03), (0.0, 0.26)], M['steel'], ch, axis='X', rad=0.02, loc=(-3.28, 0.42, 0.27))
    lathe('tailpipe', [(0.030, -0.12), (0.034, -0.12, 0.001), (0.034, 0.12, 0.001), (0.030, 0.12), (0.030, -0.12)], M['chrome'], ch, axis='X', rad=0.001, loc=(-3.62, 0.42, 0.26))
    tube('rear_axle', [(-WB + 0.02, -0.66, 0.30), (-WB + 0.16, -0.40, 0.29), (-WB + 0.16, 0.40, 0.29), (-WB + 0.02, 0.66, 0.30)], 0.036, M['iron'], ch)
    tube('arb', [(-0.045, -0.50, 0.30), (0.10, -0.46, 0.25), (0.14, 0.0, 0.25), (0.10, 0.46, 0.25), (-0.045, 0.50, 0.30)], 0.011, M['iron'], ch)
    lathe('rack', [(0.0, -0.36), (0.026, -0.36, 0.006), (0.026, 0.36, 0.006), (0.0, 0.36)], M['alu'], ch, axis='Y', rad=0.006, loc=(-0.16, 0, 0.30))

    # ── corners: wheel, hub, arms and the strut ──
    WM = {'FL': dict(M), 'FR': M, 'RL': M, 'RR': M}
    WM['FL']['tyre'] = vk.simple('tyre_fl', (0.014, 0.014, 0.015), 0.78, bump=(260, 0.04), spec=0.25, ghost=True)
    WM['FL']['alloy'] = vk.simple('alloy_fl', (0.78, 0.79, 0.81), 0.22, metal=1.0, coat=0.3, ghost=True)
    WM['FL']['black_gloss'] = vk.simple('black_gloss_fl', (0.012, 0.012, 0.014), 0.12, coat=0.6, ghost=True)
    WM['FL']['zinc'] = vk.simple('zinc_fl', (0.72, 0.73, 0.75), 0.28, metal=1.0, ghost=True)
    corners = {}
    for key, x, sg in (('FL', 0.0, 1), ('FR', 0.0, -1), ('RL', -WB, 1), ('RR', -WB, -1)):
        c = empty('corner_' + key, car, (x, 0, 0))
        off = empty('wheel_off_' + key, c)
        hold, spin = vk.alloy_wheel('wheel_' + key, off, WM[key], R=WR, loc=(0, sg * TR, WR), flip=sg < 0, disc=False)
        # the brake and the knuckle stay on the car when the wheel comes off
        front = x == 0.0
        hubh = empty('hub_' + key, c, (0, sg * TR, WR), (0, 0, 0 if sg > 0 else math.pi))
        hubs = empty('hubspin_' + key, hubh)
        dR, dt = (0.168, 0.026) if front else (0.150, 0.012)
        pt.vented_disc('disc_' + key, hubs, M, dR, t=dt, hat=0.05, loc=(0, -0.020, 0), vanes=40 if front else 0)
        lathe('hubface_' + key, [(0.0, 0.034), (0.068, 0.034, 0.003), (0.072, 0.026, 0.002), (0.072, 0.0)], M['disc_hub'], hubs, axis='Y', seg=64, rad=0.0)
        for i in range(5):
            a = vk.TAU * i / 5
            lathe(f'stud_{key}{i}', [(0.0, 0.0), (0.0062, 0.0, 0.0004), (0.0062, 0.036), (0.004, 0.040), (0.0, 0.040)], M['zinc'], hubs, axis='Y', seg=16, rad=0.0,
                  loc=(0.052 * math.sin(a), 0.020, 0.052 * math.cos(a)))
        lathe('hubnose_' + key, [(0.0, 0.066), (0.020, 0.066, 0.003), (0.026, 0.034)], M['disc_hub'], hubs, axis='Y', seg=32, rad=0.0)
        a0, a1 = (112, 168) if sg > 0 else (12, 68)
        pt.caliper('caliper_' + key, hubh, M, dR, dt, a0, a1, loc=(0, -0.020, 0))
        # cast knuckle: bearing housing, an upright to the strut clamp, the steering arm and the ball-joint arm
        lathe('bearing_' + key, [(0.030, -0.052), (0.074, -0.052, 0.008), (0.078, -0.072, 0.006), (0.074, -0.104, 0.008), (0.046, -0.112, 0.004), (0.030, -0.112)], M['cast'], hubh, axis='Y', seg=64, rad=0.0)
        ky = sg * (TR - 0.088)
        tube('knuckle_up_' + key, [(0.0, ky, WR + 0.05), (0.004, sg * 0.672, WR + 0.11), (0.0, sg * 0.669, 0.395)], 0.026, M['cast'], c)
        rbox('knuckle_boss_' + key, (0.05, 0.032, 0.085), M['cast'], c, loc=(0.0, sg * 0.669, 0.365), r=0.010, seg=3)
        tube('knuckle_lo_' + key, [(0.0, ky, WR - 0.05), (-0.004, sg * 0.672, WR - 0.08), (-0.004, sg * 0.660, 0.252)], 0.024, M['cast'], c)
        if front:
            tube('steer_arm_' + key, [(-0.05, ky, WR + 0.01), (-0.10, sg * 0.676, 0.322), (-0.150, sg * 0.662, 0.318)], 0.016, M['cast'], c)
            # lower arm: a pressed steel wishbone with a bonded bush at each pivot and the ball joint at the knuckle
            extrude_poly('arm_' + key, [(0.03, sg * 0.66), (0.075, sg * 0.36), (-0.02, sg * 0.35), (-0.29, sg * 0.37), (-0.33, sg * 0.42), (-0.06, sg * 0.62), (-0.03, sg * 0.67)], 0.036,
                         M['ecoat_arm'], c, axis='Z', bevel=0.012, seg=3, loc=(0, 0, 0.215))
            pt.bush('arm_bushf_' + key, c, M, (0.045, sg * 0.335, 0.215), axis='X', r=0.030, w=0.07)
            pt.bush('arm_bushr_' + key, c, M, (-0.31, sg * 0.385, 0.215), axis='Z', r=0.042, w=0.05)
            pt.ball_joint('balljoint_' + key, c, M, (-0.004, sg * 0.660, 0.226), (0, 0, 1), r=0.017, stud=0.035)
            # steering: rack gaiter, tie rod, the outer track-rod end
            pt.bellows('rackboot_' + key, c, M, 0.028, 0.012, 0.12, folds=7, depth=0.007, axis='Y', loc=(-0.16, sg * 0.36, 0.30), rot=(0, 0, 0 if sg > 0 else math.pi))
            tube('tierod_' + key, [(-0.16, sg * 0.47, 0.30), (-0.152, sg * 0.62, 0.312)], 0.0095, M['steel_h'], c, smooth_path=False)
            dm.hex_nut('tierod_nut_' + key, M['zinc'], 0.012, 0.012, 0, c).rotation_euler = (math.pi / 2, 0, 0)
            bpy.data.objects['tierod_nut_' + key].location = (-0.153, sg * 0.605, 0.311)
            pt.ball_joint('tre_' + key, c, M, (-0.150, sg * 0.645, 0.300), (0, 0, 1), r=0.015, stud=0.03)
            # drive shaft: plunging inner joint, two boots, the bar and the outer bell into the hub
            lathe('shaft_' + key, [(0.0, 0.30), (0.040, 0.30, 0.006), (0.046, 0.34, 0.006), (0.042, 0.40, 0.004), (0.020, 0.405), (0.0, 0.405)], M['cast'], c, axis='Y', seg=48, rad=0.0,
                  loc=(0, 0, WR), rot=(0, 0, 0 if sg > 0 else math.pi))
            pt.bellows('cvboot_in_' + key, c, M, 0.040, 0.016, 0.075, folds=5, depth=0.006, axis='Y', loc=(0, sg * 0.40, WR), rot=(0, 0, 0 if sg > 0 else math.pi))
            cyl('shaft_bar_' + key, 0.0135, 0.14, M['steel_h'], c, loc=(0, sg * 0.53, WR), axis='Y', seg=32)
            pt.bellows('cvboot_out_' + key, c, M, 0.016, 0.044, 0.085, folds=6, depth=0.006, axis='Y', loc=(0, sg * 0.585, WR), rot=(0, 0, 0 if sg > 0 else math.pi))
            base = (0.0, sg * 0.615, 0.305)
        else:
            # trailing arm forward to its bush, the beam behind it
            tube('trail_' + key, [(0.0, sg * (TR - 0.10), WR - 0.02), (0.20, sg * 0.66, 0.30), (0.42, sg * 0.62, 0.33)], 0.030, M['ecoat_arm'], c)
            pt.bush('trail_bush_' + key, c, M, (0.45, sg * 0.62, 0.33), axis='Y', r=0.036, w=0.06)
            base = (0.03, sg * 0.60, 0.30)
        st = strut_unit('strut_' + key, c, M, base, sg, decal=DECAL_TURN.get(key, 0.0))
        # where the strut's welded tabs are, in the corner's frame
        R0 = Matrix.Translation(base) @ Euler(st['root'].rotation_euler).to_matrix().to_4x4()
        link_top = R0 @ Vector((-(ln.ST['R'] + 0.015), 0.003, 0.150))
        hose_top = R0 @ Vector((-0.004, ln.ST['R'] + 0.013, 0.170))
        if front:
            # anti-roll bar drop link: ball joint at the bar, ball joint at the strut tab
            lo = Vector((link_top.x - 0.004, link_top.y + sg * 0.004, 0.318))
            tube('droplink_' + key, [lo[:], link_top[:]], 0.0058, M['steel_h'], c, smooth_path=False)
            for k, (p, d) in enumerate(((lo, (0, 0, 1)), (link_top, (0, 0, -1)))):
                lathe(f'droplink_ball{k}_{key}', [(0.0, -0.016), (0.012, -0.012, 0.004), (0.014, 0.0, 0.004), (0.010, 0.012, 0.003), (0.006, 0.016), (0.0, 0.016)], M['rubber'], c, axis='Z', seg=24, rad=0.0, loc=(p + Vector(d) * 0.012)[:])
            tube('arb_end_' + key, [(link_top.x - 0.004, sg * 0.50, 0.30), (link_top.x - 0.004, lo.y, 0.31)], 0.011, M['iron'], c, smooth_path=False)
        # brake hose from the strut bracket down to the caliper, with a lazy loop
        am = math.radians((a0 + a1) / 2) if sg > 0 else math.radians(180 - (a0 + a1) / 2)
        cp = Vector((math.cos(am) * (dR - 0.03), sg * (TR - 0.085), WR + math.sin(am) * (dR - 0.03)))
        pt.hose('hose_' + key, c, M, [hose_top[:], (hose_top + Vector((-0.04, sg * 0.02, 0.03)))[:], (cp + Vector((-0.07, -sg * 0.03, 0.09)))[:], (cp + Vector((-0.01, -sg * 0.01, 0.03)))[:], cp[:]])
        corners[key] = dict(root=c, off=off, spin=spin, hubspin=hubs, strut=st, sg=sg, x=x)
    ghosts = [M[k] for k in ('paint', 'glass', 'lens', 'lens_red', 'black_gloss', 'black_trim', 'chrome', 'plate', 'mirror', 'drl', 'amber', 'red_led', 'chrome_dark', 'black_satin', 'plate_art_plate_f', 'plate_art_plate_r')]
    wheel_ghosts = [WM['FL'][k] for k in ('tyre', 'alloy', 'black_gloss', 'zinc')]
    chassis_ghosts = [M[k] for k in ('ecoat', 'alu', 'plastic', 'seat', 'steel', 'iron_c', 'screen')]
    return dict(car=car, sprung=sprung, chassis=ch, carriers=C, panels=P, corners=corners, M=M, ghosts=ghosts, wheel_ghosts=wheel_ghosts, chassis_ghosts=chassis_ghosts)
