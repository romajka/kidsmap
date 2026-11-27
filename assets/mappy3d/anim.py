# Mappy body animations + GLB export.  python3 anim.py
# Facial expressions are morph targets driven at runtime, so clips only move the skeleton.
import bpy, math
from mathutils import Vector, Quaternion

bpy.ops.wm.open_mainfile(filepath='/home/claude/mappy3d/mappy.blend')
sc = bpy.context.scene
FPS = 30; sc.render.fps = FPS
rig = bpy.data.objects['Mappy_Rig']
P = rig.pose.bones
BONES = [b.name for b in rig.data.bones]
REST = {b.name: b.matrix_local.to_quaternion() for b in rig.data.bones}
for pb in P: pb.rotation_mode = 'QUATERNION'

def q_of(bone, rots):
    """rots: list of (axis_in_armature_space, degrees), applied in order, as a local quaternion"""
    R = REST[bone]; q = Quaternion()
    for axis, deg in rots:
        q = (R.inverted() @ Quaternion(Vector(axis), math.radians(deg)) @ R) @ q
    return q

X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
# handy named poses for arms (relative to the A-pose rest)
def arm(L, up=0, fwd=0, elbow=0, twist=0, front=0, bend=0):
    """up: raise sideways from the A-pose (47 = horizontal), fwd: swing a hanging arm forward/back,
    front: sweep a raised arm toward the front, elbow: bend the forearm upward, bend: bend it toward the front"""
    s = 1 if L == 'R' else -1
    return {f'upperarm.{L}': [(Y, -s * up), (X, fwd), (Z, -s * front)], f'forearm.{L}': [(Y, -s * elbow), (Z, -s * bend), (Z, s * twist)]}

def clip(name, dur, keys, loop=False):
    """keys: list of (time_s, {bone: rots | 'loc': vec | 'scale': vec}); bones not keyed stay at rest"""
    act = bpy.data.actions.new(name)
    rig.animation_data_create(); rig.animation_data.action = act
    used = set()
    for _, k in keys: used |= {b for b in k if b in BONES or b.split(':')[0] in BONES}
    for t, k in keys:
        f = 1 + round(t * FPS)
        for b in BONES:
            pb = P[b]
            pb.rotation_quaternion = q_of(b, k.get(b, []))
            pb.location = Vector(k.get(b + ':loc', (0, 0, 0)))
            pb.scale = Vector(k.get(b + ':scale', (1, 1, 1)))
            pb.keyframe_insert('rotation_quaternion', frame=f)
            if b == 'root' or b + ':loc' in k or any((b + ':loc') in kk for _, kk in keys): pb.keyframe_insert('location', frame=f)
            if any((b + ':scale') in kk for _, kk in keys): pb.keyframe_insert('scale', frame=f)
    act.use_fake_user = True
    if loop:
        for fc in act.fcurves if hasattr(act, 'fcurves') else []:
            m = fc.modifiers.new('CYCLES')
    trk = rig.animation_data.nla_tracks.new(); trk.name = name
    st = trk.strips.new(name, 1, act); st.action_frame_end = 1 + round(dur * FPS)
    rig.animation_data.action = None
    print('clip', name, dur)

def merge(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            if isinstance(v, list): out[k] = out.get(k, []) + v
            else: out[k] = v
    return out

REL = merge(arm('L', -22), arm('R', -22))          # arms relaxed down a bit from the A-pose
def relaxed(**extra): return merge(REL, extra)

# ------------------------------------------------------------------ idle (loop 3 s): breathe, sway, ear twitch
clip('idle', 3.0, [
    (0.0, relaxed(spine=[(X, 0)], head=[(Y, 0)], **{'root:scale': (1, 1, 1)})),
    (0.75, relaxed(spine=[(X, -2)], head=[(Y, 3), (X, -2)], **{'ear.L': [(Y, -6)], 'root:scale': (1.01, 1.01, 0.985)})),
    (1.5, relaxed(spine=[(X, 0)], head=[(Y, 0)], **{'root:scale': (1, 1, 1)})),
    (2.25, relaxed(spine=[(X, -2)], head=[(Y, -3), (X, -2)], **{'ear.R': [(Y, 6)], 'root:scale': (1.01, 1.01, 0.985)})),
    (3.0, relaxed(spine=[(X, 0)], head=[(Y, 0)], **{'root:scale': (1, 1, 1)})),
], loop=True)

# ------------------------------------------------------------------ wave (2.4 s)
def wv(a): return merge(arm('L', -22), arm('R', 64, 0, 52 + a, front=18), {'hand.R': [(Y, -a * 0.5)], 'head': [(Y, 7), (X, -3)], 'spine': [(Y, 3)]})
clip('wave', 2.4, [
    (0.0, REL), (0.35, wv(0)), (0.6, wv(-30)), (0.85, wv(10)), (1.1, wv(-30)), (1.35, wv(10)), (1.6, wv(-25)), (1.9, wv(0)), (2.4, REL),
])

# ------------------------------------------------------------------ jump (1.3 s): crouch, launch, hang, land squash
def jp(z, sq, arms_up, tuck=0):
    return merge(arm('L', arms_up * 1.6, 0, max(0, arms_up) * 0.6), arm('R', arms_up * 1.6, 0, max(0, arms_up) * 0.6), {'root:loc': (0, 0, z), 'root:scale': sq,
                 'thigh.L': [(X, tuck)], 'thigh.R': [(X, tuck)], 'head': [(X, -arms_up * 0.1)]})
clip('jump', 1.3, [
    (0.0, jp(0, (1, 1, 1), -22)),
    (0.22, jp(0, (1.12, 1.12, 0.82), -35)),
    (0.42, jp(0.55, (0.93, 0.93, 1.14), 40, 20)),
    (0.62, jp(0.75, (1, 1, 1), 48, 25)),
    (0.82, jp(0.2, (0.96, 0.96, 1.06), 20)),
    (0.92, jp(0, (1.14, 1.14, 0.8), -30)),
    (1.08, jp(0, (0.97, 0.97, 1.04), -22)),
    (1.3, jp(0, (1, 1, 1), -22)),
])

# ------------------------------------------------------------------ spin (1.4 s): hop and full turn
def sp(z, ang, sq=(1, 1, 1), up=10):
    return merge(arm('L', up * 1.4), arm('R', up * 1.4), {'root': [(Z, ang)], 'root:loc': (0, 0, z), 'root:scale': sq})
clip('spin', 1.4, [
    (0.0, sp(0, 0, up=-22)), (0.18, sp(0, -10, (1.1, 1.1, 0.86), -30)), (0.4, sp(0.35, 90, (0.95, 0.95, 1.08), 30)),
    (0.62, sp(0.45, 180, up=40)), (0.84, sp(0.35, 270, up=30)), (1.02, sp(0, 360, (1.12, 1.12, 0.84), -20)), (1.2, sp(0, 360, (0.97, 0.97, 1.03), -22)), (1.4, sp(0, 360, up=-22)),
])

# ------------------------------------------------------------------ dance (loop 2 s): sway with alternating arms
def dn(side, bob):
    s = 1 if side else -1
    return merge(arm('L', 66 if side else 10, 0, 45 if side else 0, front=10), arm('R', 10 if side else 66, 0, 0 if side else 45, front=10),
                 {'root': [(Y, 7 * s)], 'head': [(Y, -10 * s)], 'root:loc': (0, 0, bob), 'root:scale': (1, 1, 1 - bob * 0.5),
                  'thigh.L': [(Y, 4 * s)], 'thigh.R': [(Y, 4 * s)], 'ear.L': [(Y, 8 * s)], 'ear.R': [(Y, 8 * s)]})
clip('dance', 2.0, [(0.0, dn(True, 0)), (0.25, dn(True, 0.06)), (0.5, dn(False, 0)), (0.75, dn(False, 0.06)), (1.0, dn(True, 0)),
                    (1.25, dn(True, 0.06)), (1.5, dn(False, 0)), (1.75, dn(False, 0.06)), (2.0, dn(True, 0))], loop=True)

# ------------------------------------------------------------------ sleep (loop 4 s): head droops, slow breath
def sl(br):
    return merge(arm('L', -30, -8), arm('R', -30, -8), {'head': [(X, 16 + br * 3), (Y, 10)], 'neck': [(X, 6)], 'spine': [(X, 4 + br * 2)],
                 'ear.L': [(Y, -8)], 'ear.R': [(Y, 8)], 'root:scale': (1 + br * 0.015, 1 + br * 0.015, 1 - br * 0.02)})
clip('sleep', 4.0, [(0, sl(0)), (2.0, sl(1)), (4.0, sl(0))], loop=True)

# ------------------------------------------------------------------ point (1.8 s): points to the side (e.g. at the map)
PT = merge(arm('L', -22), arm('R', 52, 0, 0, front=12), {'head': [(Z, 20), (X, -4)], 'spine': [(Z, 8)]})
clip('point', 1.8, [(0, REL), (0.3, PT), (0.55, merge(PT, {'forearm.R': [(Y, -10)]})), (0.8, PT), (1.4, PT), (1.8, REL)])

# ------------------------------------------------------------------ walk (loop 0.8 s)
def wk(ph):
    s = math.sin(ph * 2 * math.pi); c = abs(math.cos(ph * 2 * math.pi))
    return merge(arm('L', -26, 30 * s), arm('R', -26, -30 * s),
                 {'thigh.L': [(X, -28 * s)], 'thigh.R': [(X, 28 * s)], 'foot.L': [(X, 12 * max(0, s))], 'foot.R': [(X, 12 * max(0, -s))],
                  'root:loc': (0, 0, 0.05 * c), 'root': [(Y, 4 * s)], 'head': [(Y, -3 * s)], 'ear.L': [(Y, -5 * c)], 'ear.R': [(Y, 5 * c)]})
clip('walk', 0.8, [(t, wk(t / 0.8)) for t in (0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)], loop=True)

# ------------------------------------------------------------------ look around (2.6 s)
clip('look', 2.6, [(0, REL), (0.4, relaxed(head=[(Z, 20), (X, -5)], spine=[(Z, 5)])), (1.1, relaxed(head=[(Z, 20), (X, -5)], spine=[(Z, 5)])),
                   (1.5, relaxed(head=[(Z, -20), (X, -5)], spine=[(Z, -5)])), (2.2, relaxed(head=[(Z, -20), (X, -5)], spine=[(Z, -5)])), (2.6, REL)])

# ------------------------------------------------------------------ surprised (1.0 s): small hop back, arms up
clip('surprised', 1.0, [(0, REL), (0.12, merge(arm('L', 62, 0, 40, front=20), arm('R', 62, 0, 40, front=20), {'root:loc': (0, 0.08, 0.12), 'head': [(X, 8)], 'ear.L': [(Y, -15)], 'ear.R': [(Y, 15)]})),
                        (0.3, merge(arm('L', 62, 0, 40, front=20), arm('R', 62, 0, 40, front=20), {'root:loc': (0, 0.10, 0), 'root:scale': (1.06, 1.06, 0.92), 'head': [(X, 6)]})),
                        (0.6, merge(arm('L', 40, 0, 25, front=15), arm('R', 40, 0, 25, front=15), {'root:loc': (0, 0.10, 0)})), (1.0, merge(REL, {'root:loc': (0, 0.0, 0)}))])

# ------------------------------------------------------------------ poke (0.7 s): squash and shake it off
clip('poke', 0.7, [(0, REL), (0.08, relaxed(**{'root:scale': (1.12, 1.12, 0.84), 'head': [(X, 6)]})), (0.2, relaxed(**{'root:scale': (0.95, 0.95, 1.07), 'head': [(Y, 10)]})),
                   (0.32, relaxed(head=[(Y, -9)])), (0.44, relaxed(head=[(Y, 6)])), (0.56, relaxed(head=[(Y, -3)])), (0.7, REL)])

# ------------------------------------------------------------------ bye / love: hug yourself (1.6 s)
HUG = merge(arm('L', 30, 0, 0, front=78, bend=72), arm('R', 30, 0, 0, front=78, bend=72), {'head': [(Y, 10), (X, -6)], 'spine': [(X, -4)]})
clip('hug', 1.6, [(0, REL), (0.3, HUG), (0.6, merge(HUG, {'root': [(Z, 8)]})), (0.9, merge(HUG, {'root': [(Z, -8)]})), (1.2, HUG), (1.6, REL)])

# ------------------------------------------------------------------ pat (1.3 s): pressed on the head, he sinks under the hand and enjoys it
def pt_(d, tilt=0):
    return relaxed(head=[(X, 15 * d), (Y, tilt)], neck=[(X, 6 * d)], spine=[(X, 4 * d)], **{'root:scale': (1 + 0.07 * d, 1 + 0.07 * d, 1 - 0.10 * d), 'ear.L': [(Y, -22 * d)], 'ear.R': [(Y, 22 * d)]})
clip('pat', 1.3, [(0, REL), (0.12, pt_(1)), (0.32, pt_(0.35, 5)), (0.5, pt_(1, -4)), (0.72, pt_(0.3, 4)), (0.9, pt_(0.7)), (1.3, REL)])

# ------------------------------------------------------------------ boop (1.2 s): nose pressed, head recoils, quick shake
clip('boop', 1.2, [(0, REL), (0.1, relaxed(head=[(X, -18)], neck=[(X, -8)], spine=[(X, -5)], **{'root:loc': (0, 0.07, 0), 'ear.L': [(Y, 12)], 'ear.R': [(Y, -12)]})),
                   (0.35, relaxed(head=[(X, -6)], **{'root:loc': (0, 0.03, 0)})), (0.5, relaxed(head=[(Z, 14)])), (0.64, relaxed(head=[(Z, -14)])),
                   (0.78, relaxed(head=[(Z, 9)])), (0.92, relaxed(head=[(Z, -5)])), (1.2, REL)])

# ------------------------------------------------------------------ giggle (1.6 s): belly tickled, hands to tummy, shaking with laughter
def gg(b, t):
    return merge(arm('L', 12, 0, 0, front=70, bend=80), arm('R', 12, 0, 0, front=70, bend=80),
                 {'spine': [(X, 6), (Y, t)], 'head': [(X, -8), (Y, -t * 1.5)], 'root:loc': (0, 0, 0.03 * b), 'root:scale': (1 + 0.03 * (1 - b), 1 + 0.03 * (1 - b), 1 - 0.04 * (1 - b))})
clip('giggle', 1.6, [(0, REL), (0.18, gg(0, 0))] + [(0.18 + 0.11 * i, gg(i % 2, 5 if i % 4 < 2 else -5)) for i in range(1, 10)] + [(1.3, gg(0, 0)), (1.6, REL)])

# ------------------------------------------------------------------ highfive (1.2 s): paw pressed, he slaps back
HF0 = merge(arm('L', -22), arm('R', 40, 0, 30, front=60), {'spine': [(Z, 6)]})
HF1 = merge(arm('L', -22), arm('R', 48, 0, 5, front=88), {'spine': [(Z, -10)], 'root:loc': (0, -0.05, 0.04)})
clip('highfive', 1.2, [(0, REL), (0.22, HF0), (0.36, HF1), (0.5, merge(HF1, {'root:scale': (1.04, 1.04, 0.95)})), (0.8, HF0), (1.2, REL)])

# ------------------------------------------------------------------ earflick (0.9 s): ear pressed
clip('earflick', 0.9, [(0, REL), (0.1, relaxed(head=[(Y, 12)], **{'ear.L': [(Y, -25)], 'ear.R': [(Y, -25)]})), (0.3, relaxed(head=[(Y, -8)], **{'ear.L': [(Y, 18)], 'ear.R': [(Y, 18)]})),
                       (0.5, relaxed(head=[(Y, 5)], **{'ear.L': [(Y, -10)], 'ear.R': [(Y, -10)]})), (0.7, relaxed(**{'ear.L': [(Y, 5)], 'ear.R': [(Y, 5)]})), (0.9, REL)])


# ------------------------------------------------------------------ export
for x in bpy.context.selected_objects: x.select_set(False)
rig.animation_data.action = None
for pb in P:
    pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/mappy3d/mappy_anim.blend')
bpy.ops.export_scene.gltf(
    filepath='/home/claude/mappy3d/mappy.glb', export_format='GLB',
    export_animations=True, export_animation_mode='NLA_TRACKS', export_force_sampling=True, export_frame_step=1,
    export_morph=True, export_morph_normal=False, export_skins=True, export_def_bones=False,
    export_yup=True, export_apply=False, export_texcoords=False, export_normals=True,
    export_draco_mesh_compression_enable=False, export_extras=False, export_cameras=False, export_lights=False,
)
import os; print('glb', os.path.getsize('/home/claude/mappy3d/mappy.glb'))
