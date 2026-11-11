"""The vehicle films: a vehicle drives in, comes apart and the camera finds the Alaina part inside.

usage: python films.py <car|cabin|axle|rear> <outdir> [--res N] [--samples N] [--threshold x] [--gpu] [--only a-b | i,j,k] [--force] [--noblur]
Frames are written as <prefix><nnn>.png (c car, b cabin, x axle, q rear); encode_films.py turns them into seq/film.
"""
import bpy, math, sys, os, time
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vkit as vk
from vkit import ramp, lerp, smooth

FPS = 18


def cam_channels(rig, cam, pose_at):
    """pose_at(t) -> (target, dist, az, el, fstop, focus). Keys the camera from it."""
    def mat(t):
        tg, dist, az, el = pose_at(t)[:4]
        return vk.cam_matrix(tg, dist, az, el)
    for i in range(3):
        rig.add(cam, 'location', (lambda t, i=i: mat(t).translation[i]), i)
    for i in range(4):
        rig.add(cam, 'rotation_quaternion', (lambda t, i=i: _quat(mat, t)[i]), i)
    cam.data.dof.use_dof = True
    rig.add(cam.data.dof, 'aperture_fstop', lambda t: pose_at(t)[4])
    rig.add(cam.data.dof, 'focus_distance', lambda t: pose_at(t)[5])


_qprev = {}


def _quat(mat, t):
    q = mat(t).to_quaternion()
    p = _qprev.get('q')
    if p is not None and q.dot(p) < 0: q.negate()
    _qprev['q'] = q
    return q


def mix_pose(a, b, k):
    return tuple(lerp(Vector(x), Vector(y), k)[:] if isinstance(x, (tuple, list)) else lerp(x, y, k) for x, y in zip(a, b))


def brake_pitch(t, T, th=0.022, on=0.25, w=math.tau * 1.55, zeta=4.2):
    """Nose dive while braking to a stop at T, then the rebound as the springs let go."""
    if t < T: return th * ramp(t, T - 1.35, T - 1.35 + on)
    d = t - T
    return th * math.exp(-zeta * d) * math.cos(w * d)


# ───────────────────────── the car: hero ─────────────────────────
# where the camera ends up: (target, distance, azimuth, elevation, f-stop, focus distance)
CLOSE = {'front': ((0.03, 0.61, 0.67), 1.45, 136, 16, 2.0, 1.45),
         'rear': ((-2.73, 0.60, 0.67), 1.45, 224, 16, 2.0, 1.45)}


def film_car(view='front'):
    import sedan as sd
    H = sd.build()
    rig = vk.Rig()
    T = 1.7; D = 9.0
    E0, E1 = 1.95, 3.15          # the body comes apart
    Z0, Z1 = 3.05, 4.25          # the camera goes in to the strut
    END = 4.3

    def xpos(t):
        u = min(1.0, max(0.0, t / T))
        return -D * (1 - u) ** 2

    pv = Vector((-sd.WB / 2, 0, 0.32))
    pitch = lambda t: brake_pitch(t, T)
    heave = lambda t: -0.006 * (pitch(t) / 0.022) if t < T else 0.004 * math.exp(-4 * (t - T)) * math.sin(math.tau * 1.55 * (t - T))
    rig.add(H['car'], 'location', xpos, 0)
    rig.add(H['sprung'], 'rotation_euler', pitch, 1)

    def sprung_loc(i):
        def f(t):
            R = Matrix.Rotation(pitch(t), 3, 'Y')
            v = pv - R @ pv + Vector((0, 0, heave(t)))
            return v[i]
        return f
    for i in (0, 2): rig.add(H['sprung'], 'location', sprung_loc(i), i)
    e = lambda t: (t - E0) / (E1 - E0)
    for nm, (off, dl) in sd.EXPLODE.items():
        for i in range(3):
            if off[i]: rig.add(H['carriers'][nm], 'location', (lambda t, o=off[i], dl=dl: o * ramp(e(t), dl, dl + 0.72)), i)
    for key, c in H['corners'].items():
        sg = c['sg']
        rig.add(c['spin'], 'rotation_euler', (lambda t, sg=sg: sg * xpos(t) / sd.WR), 1)
        rig.add(c['hubspin'], 'rotation_euler', (lambda t, sg=sg: sg * xpos(t) / sd.WR), 1)
        arm = (sd.WB / 2) if c['x'] == 0.0 else -(sd.WB / 2)
        comp = lambda t, arm=arm: pitch(t) * arm - heave(t)
        st = c['strut']
        rig.add(st['rod'], 'location', (lambda t, comp=comp: -comp(t)), 2)
        rig.add(st['spring'], 'scale', (lambda t, comp=comp, h=st['h']: (h - comp(t)) / h), 2)
    # the near front wheel slides off its hub so the strut is in the clear
    fl = H['corners']['FL' if view == 'front' else 'RL']
    rig.add(fl['off'], 'location', lambda t: 0.62 * ramp(t, E0 + 0.35, E1 + 0.1), 1)
    for s in vk.value_nodes(H['ghosts'], 'ghost'): rig.add(s, 'default_value', lambda t: ramp(t, E0 + 0.05, E1 - 0.1))
    for s in vk.value_nodes(H['wheel_ghosts'], 'ghost'): rig.add(s, 'default_value', lambda t: 0.93 * ramp(t, E0 + 0.3, E1))
    for s in vk.value_nodes(H['chassis_ghosts'], 'ghost'): rig.add(s, 'default_value', lambda t: ramp(t, Z0 - 0.1, Z0 + 0.5))
    # as the camera goes in, the shell and the chassis fade right out and leave the corner on its own
    FADE1 = Z0 + 0.8
    for s in vk.value_nodes(H['ghosts'] + H['wheel_ghosts'] + H['chassis_ghosts'], 'fade'): rig.add(s, 'default_value', lambda t: ramp(t, Z0 + 0.1, FADE1))
    gone = vk.descendants(H['sprung']) + vk.descendants(H['chassis']) + vk.descendants(fl['off'])
    vk.hide_from([o for o in gone if o.type in ('MESH', 'CURVE')], int(FADE1 * FPS) + 2)

    # studio
    fl = vk.floor(); vk.world()
    Ls = [vk.area('top', (-1.3, 0, 4.4), (8.0, 1.4), 820, target=(-1.3, 0, 0)),
          vk.area('side', (1.5, 7.0, 1.7), (8, 1.2), 330, target=(-1.2, 0, 0.6)),
          vk.area('front', (8.0, 2.0, 1.4), (3, 1.2), 150, target=(0, 0, 0.6)),
          vk.area('rim', (-7, -5, 2.8), (6, 1.0), 1300, (1.0, 0.62, 0.38), target=(-1.2, 0, 0.8)),
          vk.area('back', (-8, 4, 3.0), (4, 1.0), 1100, (0.80, 0.88, 1.0), target=(-1.2, 0, 0.8))]
    vk.keep_off_floor(Ls, fl, also=[H['panels']['windshield' if view == 'front' else 'backlight']])
    # studio reflection cards: long strips along the camera side draw streaks down the doors and shoulder,
    # a broad one overhead the roof and bonnet; none of them light the set or show on the floor
    cards = [vk.card('card_shoulder', (-2.0, 3.0, 4.2), (16.0, 0.9), 45.0, (-2.0, 0, 0.9), soft=0.45),
             vk.card('card_high', (-2.0, 4.2, 2.45), (16.0, 1.2), 9.0, (-2.0, 0, 1.0)),
             vk.card('card_top', (-1.3, 0.6, 3.6), (7.0, 1.6), 6.0, (-1.3, 0, 0.0)),
             vk.card('card_nose', (5.0, 1.2, 2.2), (2.2, 1.2), 10.0, (0.6, 0, 0.6)),
             vk.card('card_tail', (-7.6, 1.5, 2.2), (2.2, 1.2), 10.0, (-3.2, 0, 0.6))]
    vk.keep_off_floor(cards, fl)
    for c_ in cards:
        for nd in c_.data.materials[0].node_tree.nodes:
            if nd.type == 'MATH' and nd.operation == 'MULTIPLY' and nd.inputs[1].default_value > 1: rig.add(nd.inputs[1], 'default_value', (lambda t, s0=nd.inputs[1].default_value: s0 * (1 - ramp(t, Z0, Z1))))
    pool = vk.spot('pool', (-1.3, 0, 11), (-1.3, 0, 0), 30000, size=0.78, blend=1.0, radius=0.8)
    vk.floor_only([pool], fl)
    rig.add(pool.data, 'energy', lambda t: 30000 * (1 - 0.85 * ramp(t, Z0, Z1)))      # the floor steps back as the camera goes in
    sx = 0.0 if view == 'front' else -sd.WB
    kd = 1 if view == 'front' else -1          # the key light stands on the camera's side of the strut
    k1 = vk.area('key_strut', (sx + 1.4 * kd, 1.9, 1.5), (0.5, 0.9), 0, target=(sx, 0.6, 0.55)); vk.keep_off_floor([k1], fl)
    k2 = vk.area('rim_strut', (sx - 1.0 * kd, 0.2, 1.3), (0.3, 0.8), 0, (1.0, 0.45, 0.18), target=(sx, 0.6, 0.55)); vk.keep_off_floor([k2], fl)
    rig.add(k1.data, 'energy', lambda t: 340 * ramp(t, E0 + 0.3, Z1 - 0.2))
    rig.add(k2.data, 'energy', lambda t: 300 * ramp(t, E0 + 0.3, Z1 - 0.2))

    cam = vk.camera(70)
    if view == 'front':
        wide0 = ((-1.25, 0, 1.45), 9.7, 123, 8, 16.0, 9.7)
        wide1 = ((-1.25, 0, 1.50), 11.0, 117, 13, 16.0, 11.0)
        close = CLOSE['front']
    else:
        wide0 = ((-1.45, 0, 1.45), 9.7, 238, 8, 16.0, 9.7)
        wide1 = ((-1.45, 0, 1.50), 11.0, 243, 13, 16.0, 11.0)
        close = CLOSE['rear']

    def pose(t):
        p = mix_pose(wide0, wide1, ramp(t, 0.0, E1))
        return mix_pose(p, close, ramp(t, Z0, Z1))
    cam_channels(rig, cam, pose)
    n = int(round(END * FPS)) + 1
    return rig, n, ('c' if view == 'front' else 'q')


# ───────────────────────── the trucks: cabin dampers and axle shockers ─────────────────────────
def film_truck(kind):
    import truck as tk
    import damper as dm
    P = tk.HEAVY if kind == 'cabin' else tk.LIGHT
    H = tk.build(P)
    rig = vk.Rig()
    XF, CL, CW, WB, WR, FLOOR = (P[k] for k in ('XF', 'CL', 'CW', 'WB', 'WR', 'FLOOR'))
    T = 1.7; D = 10.0
    E0, E1 = 1.95, 3.1
    Z0, Z1 = 3.0, 4.1
    END = 4.15

    def xpos(t):
        u = min(1.0, max(0.0, t / T))
        return -D * (1 - u) ** 2
    rig.add(H['truck'], 'location', xpos, 0)
    # the cab nods on its dampers as the truck brakes, then rocks back and settles: this is the job the damper does
    cpitch = lambda t: brake_pitch(t, T, th=0.030, w=math.tau * 1.25, zeta=3.0)
    cheave = lambda t: -0.008 * (cpitch(t) / 0.03) if t < T else 0.006 * math.exp(-3 * (t - T)) * math.sin(math.tau * 1.25 * (t - T))
    pv = Vector((XF - CL / 2, 0, FLOOR))
    rig.add(H['cab'], 'rotation_euler', cpitch, 1)

    def cab_loc(i):
        def f(t):
            R = Matrix.Rotation(cpitch(t), 3, 'Y')
            return (pv - R @ pv + Vector((0, 0, cheave(t))))[i]
        return f
    for i in (0, 2): rig.add(H['cab'], 'location', cab_loc(i), i)
    for key, dmp in H['dampers'].items():
        arm = dmp['root'].location.x - pv.x
        comp = lambda t, arm=arm: cpitch(t) * arm - cheave(t)
        for g in ('rod', 'shield', 'top', 'tbush'):
            rig.add(dmp['G'][g], 'location', (lambda t, comp=comp: -comp(t)), 2)
        rig.add(dmp['spring'], 'scale', (lambda t, comp=comp, h=dmp['h']: (h - comp(t)) / h), 2)
    # the chassis dips a little on its leaf springs too
    apitch = lambda t: brake_pitch(t, T, th=0.007, w=math.tau * 1.8, zeta=5.0)
    for key, sh in H['shocks'].items():
        arm = (WB / 2) if key[0] == 'F' else -(WB / 2)
        rig.add(sh['upper'], 'location', (lambda t, arm=arm, c0=sh['c0']: -(c0 + apitch(t) * arm)), 2)
    for key, w in H['wheels'].items():
        rig.add(w['spin'], 'rotation_euler', (lambda t, sg=w['sg']: sg * xpos(t) / WR), 1)
        if w['hubspin']: rig.add(w['hubspin'], 'rotation_euler', (lambda t, sg=w['sg']: sg * xpos(t) / WR), 1)
    e = lambda t: (t - E0) / (E1 - E0)
    for nm, (off, dl) in tk.EXPLODE.items():
        for i in range(3):
            if off[i]: rig.add(H['carriers'][nm], 'location', (lambda t, o=off[i], dl=dl: o * ramp(e(t), dl, dl + 0.72)), i)
    ghosts = H['ghosts'] + H['extra_ghosts']
    for s in vk.value_nodes(ghosts, 'ghost'): rig.add(s, 'default_value', lambda t: ramp(t, E0 + 0.05, E1 - 0.1))
    FADE1 = Z0 + 0.8
    for s in vk.value_nodes(ghosts + H['wheel_ghosts'], 'fade'): rig.add(s, 'default_value', lambda t: ramp(t, Z0 + 0.1, FADE1))
    gone = [o for nm in tk.EXPLODE for o in vk.descendants(H['carriers'][nm])]
    fl_w = H['wheels']['FL']
    if kind == 'axle':
        rig.add(H['deck'], 'location', lambda t: 1.0 * ramp(e(t), 0.15, 0.9), 2)
        rig.add(fl_w['off'], 'location', lambda t: 0.85 * ramp(t, E0 + 0.35, E1 + 0.1), 1)
        for s in vk.value_nodes(H['wheel_ghosts'], 'ghost'): rig.add(s, 'default_value', lambda t: 0.93 * ramp(t, E0 + 0.3, E1))
        gone += vk.descendants(H['deck']) + vk.descendants(fl_w['off'])
    ghost_mats = set(m.name for m in ghosts + H['wheel_ghosts'])
    gone += [o for o in vk.descendants(H['truck']) if o.type in ('MESH', 'CURVE') and o.data.materials and o.data.materials[0] and o.data.materials[0].name in ghost_mats]
    vk.hide_from(list({o.name: o for o in gone if o.type in ('MESH', 'CURVE')}.values()), int(FADE1 * FPS_T) + 2)

    fl = vk.floor(); vk.world()
    cx = -WB / 2 + 0.2
    hgt = P['ZROOF']
    Ls = [vk.area('top', (cx, 0, hgt * 2.3), (9.0, 1.8), 850 if kind == 'cabin' else 700, target=(cx, 0, 0)),
          vk.area('side', (1.5, 8.0, hgt * 0.85), (9, 1.6), 520 if kind == 'cabin' else 420, target=(cx, 0, hgt * 0.4)),
          vk.area('front', (9.0, 2.0, hgt * 0.6), (3, 1.6), 420, target=(0, 0, hgt * 0.4)),
          vk.area('rim', (-8, -6, hgt * 1.2), (7, 1.2), 2600, (1.0, 0.42, 0.16), target=(cx, 0, hgt * 0.5)),
          vk.area('back', (-9, 5, hgt * 1.2), (5, 1.2), 900, (0.75, 0.84, 1.0), target=(cx, 0, hgt * 0.5))]
    vk.keep_off_floor(Ls, fl)
    # reflection cards: the cab sides are near vertical, so their streaks come from long low strips beside the truck
    cards = [vk.card('card_side_lo', (cx - 1.0, 5.2, hgt * 0.30), (20.0, 0.5), 40.0, (cx - 1.0, 0, hgt * 0.55), soft=0.5),
             vk.card('card_side_hi', (cx - 1.0, 4.6, hgt * 1.45), (20.0, 1.0), 14.0, (cx - 1.0, 0, hgt * 0.6)),
             vk.card('card_front', (8.0, 3.0, hgt * 0.25), (3.0, 0.6), 30.0, (XF, 0, hgt * 0.5), soft=0.5),
             vk.card('card_top', (cx, 0.8, hgt * 2.0), (9.0, 1.8), 6.0, (cx, 0, 0))]
    vk.keep_off_floor(cards, fl)
    for c_ in cards:
        for nd in c_.data.materials[0].node_tree.nodes:
            if nd.type == 'MATH' and nd.operation == 'MULTIPLY' and nd.inputs[1].default_value > 1: rig.add(nd.inputs[1], 'default_value', (lambda t, s0=nd.inputs[1].default_value: s0 * (1 - ramp(t, Z0, Z1))))
    pool = vk.spot('pool', (cx, 0, 15), (cx, 0, 0), 46000, size=0.72, blend=1.0, radius=0.8)
    rig.add(pool.data, 'energy', lambda t: 46000 * (1 - 0.8 * ramp(t, Z0, Z1)))
    vk.floor_only([pool], fl)
    L = XF + WB + P['REAR']
    if kind == 'cabin':
        d0 = H['dampers']['FL']['root'].location
        hero = Vector((d0.x, d0.y, d0.z + dm.D['topEyeZ'] / 2))
        wide0 = ((cx, 0, 2.5), 2.25 * L, 126, 6, 16.0, 2.25 * L)
        wide1 = ((cx + 0.2, 0, 2.6), 2.55 * L, 120, 10, 16.0, 2.55 * L)
        close = ((hero.x + 0.02, hero.y, hero.z + 0.02), 0.98, 137, 5, 2.4, 0.98)
    else:
        lo = Vector((0.17, P['RAILY'] + 0.16, WR + 0.02)); hi = Vector((0.20, P['RAILY'] + 0.10, WR + 0.475))
        hero = (lo + hi) / 2
        wide0 = ((cx, 0, 2.05), 2.35 * L, 140, 6, 16.0, 2.35 * L)
        wide1 = ((cx + 0.2, 0, 2.2), 2.62 * L, 134, 11, 16.0, 2.62 * L)
        close = ((hero.x + 0.03, hero.y, hero.z + 0.01), 1.12, 142, 6, 2.4, 1.12)
    # tight spots on the part, so it stands out from the frame around it
    k1 = vk.spot('key_part', (hero.x + 1.5, hero.y + 1.9, hero.z + 0.9), hero[:], 0, size=0.30, blend=0.7, radius=0.25)
    k2 = vk.spot('rim_part', (hero.x - 1.2, hero.y + 0.9, hero.z + 0.7), hero[:], 0, size=0.36, blend=0.7, color=(1.0, 0.42, 0.16), radius=0.2)
    k3 = vk.spot('fill_part', (hero.x + 2.0, hero.y + 0.5, hero.z - 0.1), hero[:], 0, size=0.30, blend=0.8, color=(0.8, 0.88, 1.0), radius=0.3)
    if kind == 'cabin':
        # the part lights see only the damper and its brackets, so it stands clear of the structure behind it
        hero_objs = [o for o in vk.descendants(H['dampers']['FL']['root']) if o.type in ('MESH', 'CURVE')]
        hero_objs += [o for o in bpy.data.objects if o.name.startswith(('cabmount_ear_FL', 'cabmount_top_FL', 'cabmount_pin_FL', 'cabmount_flange_FL', 'cabmount_bolt_FL'))]
        coll = bpy.data.collections.new('hero_part')
        for o in hero_objs: coll.objects.link(o)
        for co in coll.collection_objects: co.light_linking.link_state = 'INCLUDE'
        for L_ in (k1, k2, k3): L_.light_linking.receiver_collection = coll
        # and a low, soft light on the structure behind, so it reads in soft focus
        bgl = vk.area('bg_struct', (hero.x + 0.2, hero.y - 1.2, hero.z + 1.4), (1.2, 0.8), 0, (0.85, 0.9, 1.0), target=(hero.x - 0.3, 0.0, hero.z))
        rig.add(bgl.data, 'energy', lambda t: 120 * ramp(t, Z0, Z1))
    else:
        vk.keep_off_floor([k1, k2, k3], fl)
    rig.add(k1.data, 'energy', lambda t: 2600 * ramp(t, E0 + 0.3, Z1 - 0.2))
    rig.add(k2.data, 'energy', lambda t: 2200 * ramp(t, E0 + 0.3, Z1 - 0.2))
    rig.add(k3.data, 'energy', lambda t: 700 * ramp(t, E0 + 0.3, Z1 - 0.2))
    # in the close-up the set falls away and the part carries the light
    for L_, kf in zip(Ls, (0.85, 0.85, 0.85, 0.5, 0.5)): rig.add(L_.data, 'energy', (lambda t, e0=L_.data.energy, kf=kf: e0 * (1 - kf * ramp(t, Z0, Z1))))
    cam = vk.camera(70)

    def pose(t):
        p = mix_pose(wide0, wide1, ramp(t, 0.0, E1))
        return mix_pose(p, close, ramp(t, Z0, Z1))
    cam_channels(rig, cam, pose)
    # the wide shots sit the truck in the middle of the frame, clear of the edges that melt into the page
    shx, shy = (-0.055, -0.05) if kind == 'cabin' else (0.0, -0.05)
    rig.add(cam.data, 'shift_x', lambda t: shx * (1 - ramp(t, Z0, Z1)))
    rig.add(cam.data, 'shift_y', lambda t: shy * (1 - ramp(t, Z0, Z1)))
    n = int(round(END * FPS_T)) + 1
    return rig, n, ('b' if kind == 'cabin' else 'x'), FPS_T


FPS_T = 14
FILMS = {'car': lambda: film_car('front') + (FPS,), 'rear': lambda: film_car('rear') + (FPS,), 'cabin': lambda: film_truck('cabin'), 'axle': lambda: film_truck('axle')}


def main():
    argv = sys.argv[1:]
    name, out = argv[0], argv[1]
    def opt(k, dflt):
        return type(dflt)(argv[argv.index(k) + 1]) if k in argv else dflt
    res = opt('--res', 1080); samples = opt('--samples', 96); only = opt('--only', '')
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    rig, n, prefix, fps = FILMS[name]()
    sc.render.fps = fps
    sc = vk.render_setup(res=res, samples=samples, blur='--noblur' not in argv, threshold=opt('--threshold', 0.03), gpu='--gpu' in argv)
    frames = list(range(n))
    rig.key(frames, fps)
    sc.frame_start = 0; sc.frame_end = n - 1
    if only:
        if '-' in only:
            a, b = only.split('-'); sel = set(range(int(a), int(b) + 1))
        else: sel = set(int(x) for x in only.split(','))
    else: sel = None
    print('FRAMES', n, flush=True)
    for f in frames:
        if sel is not None and f not in sel: continue
        dst = os.path.join(out, f'{prefix}{f:03d}.png')
        if os.path.exists(dst) and '--force' not in argv: continue
        sc.frame_set(f)
        sc.render.filepath = dst
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print('RENDERED', f, round(time.time() - t0, 1), flush=True)


if __name__ == '__main__':
    main()
