"""Alaina cabin damper crossed with a Superlift gas spring: the partnership image.
usage: python partner.py <out.png> [--res N] [--samples N]"""
import bpy, math, sys, os
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import damper as dm

def gas_spring(M):
    sc = bpy.context.scene
    g = bpy.data.objects.new('strut', None); sc.collection.objects.link(g)
    tube = dm.body_material('sl_tube', os.path.join(dm.HERE, 'sldecal.png'), (0.010, 0.010, 0.012), 0.22)
    R = 0.0105
    z0, z1 = 0.030, 0.270
    # socket ends: a moulded ball socket with a flat face, on a short threaded neck
    eye = [(0.0046, -0.0065), (0.0098, -0.0065, 0.0015), (0.0112, -0.004, 0.002), (0.0112, 0.004, 0.002), (0.0098, 0.0065, 0.0015), (0.0046, 0.0065), (0.0046, -0.0065)]
    ball = [(0.0, -0.0075), (0.0046, -0.0075, 0.001), (0.0046, 0.0075, 0.001), (0.0, 0.0075)]
    for nm, z in (('a', 0.0), ('b', 0.428)):
        o = dm.ring_y('sl_eye_' + nm, eye, M['rubber'], g, rad=0.0008); o.location.z = z
        o = dm.ring_y('sl_ball_' + nm, ball, M['zinc'], g, rad=0.0006); o.location.z = z
    dm.lathe('sl_neck_a', [(0.0, 0.008), (0.0058, 0.008, 0.0008), (0.0058, 0.024, 0.0005), (0.0072, 0.024, 0.0004), (0.0072, z0 + 0.002), (0.0, z0 + 0.002)], M['rubber'], g, rad=0.0006)
    dm.lathe('sl_tube', [(0.0, z0), (0.0075, z0, 0.002), (R, z0 + 0.004, 0.003), (R, z1 - 0.022, 0.001), (R - 0.0011, z1 - 0.019, 0.0012), (R - 0.0011, z1 - 0.016, 0.0012), (R, z1 - 0.013, 0.001),
                         (R, z1 - 0.003, 0.002), (R - 0.003, z1, 0.0012), (0.0052, z1, 0.0006), (0.0052, z1 - 0.001)], tube, g, uv_z=(0.052, 0.245), rad=0.001)
    dm.lathe('sl_rod', [(0.0, z1 - 0.004), (0.0042, z1 - 0.004), (0.0042, 0.406), (0.0, 0.406)], M['chrome'], g, rad=0.0003)
    dm.lathe('sl_neck_b', [(0.0, 0.398), (0.0050, 0.398, 0.0005), (0.0072, 0.402, 0.0006), (0.0072, 0.412, 0.0006), (0.0058, 0.414, 0.0005), (0.0058, 0.421), (0.0, 0.421)], M['rubber'], g, rad=0.0006)
    return g

def main():
    argv = sys.argv[1:]
    out = argv[0]
    def opt(k, d): return type(d)(argv[argv.index(k) + 1]) if k in argv else d
    res, samples = opt('--res', 1280), opt('--samples', 128)
    root, G, M = dm.build()
    dm.set_pose(G, M, 0.0, 0.0, 0.0, root)
    Ls = dm.lights()
    g = gas_spring(M)
    # the damper stands on Z; the gas spring lies across it on X, just in front
    C = Vector((0.0, 0.0, 0.194))
    g.rotation_euler = (0, math.radians(90), 0)
    g.scale = (1.2, 1.2, 1.2)
    g.location = C + Vector((-0.257, -0.072, 0.0))
    # the cool rim goes Superlift blue, and two strips run along the gas spring for its long highlights
    Ls['rimR'].data.color = (0.62, 0.76, 1.0); Ls['rimR'].data.energy = 24
    sc = bpy.context.scene
    def strip(name, loc, size, power, color=(1, 1, 1)):
        L = bpy.data.lights.new(name, 'AREA'); L.shape = 'RECTANGLE'; L.size, L.size_y = size; L.energy = power; L.color = color
        o = bpy.data.objects.new(name, L); sc.collection.objects.link(o); o.location = loc
        o.rotation_euler = (Vector(C) + Vector((0, -0.068, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return o
    strip('slTop', (0.0, -0.45, 0.62), (1.5, 0.10), 16)
    strip('slLow', (0.0, -0.30, -0.22), (1.5, 0.08), 10, (0.30, 0.52, 1.0))
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.clip_start = 0.05; cam.data.clip_end = 20
    dm.set_cam(cam, (0, -0.02, 0.194), 0.42, 14, 9, 45)
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6; sc.cycles.glossy_bounces = 4; sc.cycles.diffuse_bounces = 2
    sc.render.film_transparent = True
    sc.render.resolution_x = res; sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    try:
        sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception as ex: print('view', ex)
    sc.render.filepath = out
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    print('RENDERED', out)

main()
