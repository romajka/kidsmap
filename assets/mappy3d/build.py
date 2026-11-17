# Mappy 3D: builds the plush bear, its skeleton and facial shape keys in Blender (headless).
# Run: python3 build.py   -> mappy.blend
# Axes: Z up, character faces -Y. Height ~2.0 units.
import bpy, bmesh, math
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

OUT = '/home/claude/mappy3d/'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
coll = scene.collection

# ------------------------------------------------------------------ materials
def mat(name, rgb, rough=0.6, sheen=0.0, sheen_tint=(1, 1, 1), spec=0.5, coat=0.0, emis=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = spec
    b.inputs['Sheen Weight'].default_value = sheen
    b.inputs['Sheen Roughness'].default_value = 0.35
    b.inputs['Sheen Tint'].default_value = (*sheen_tint, 1)
    b.inputs['Coat Weight'].default_value = coat
    if emis:
        b.inputs['Emission Color'].default_value = (*emis, 1); b.inputs['Emission Strength'].default_value = 1
    return m

def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)

M = {
    'fur': mat('fur', srgb('#18692f'), rough=0.9, sheen=0.7, sheen_tint=srgb('#7fcf8b'), spec=0.2),
    'cream': mat('cream', srgb('#ecdf96'), rough=0.9, sheen=0.5, sheen_tint=srgb('#fff6cc'), spec=0.2),
    'nose': mat('nose', srgb('#1b1d1c'), rough=0.25, spec=0.6, coat=0.6),
    'eye': mat('eye', srgb('#0e0f0e'), rough=0.35, spec=0.3, coat=0.25),
    'shine': mat('shine', (1, 1, 1), rough=0.3, emis=(1, 1, 1)),
    'line': mat('line', srgb('#102a18'), rough=0.6),
    'mouth': mat('mouth', srgb('#5a1f24'), rough=0.5),
    'tongue': mat('tongue', srgb('#f07a86'), rough=0.45),
    'blush': mat('blush', srgb('#f39aa0'), rough=0.9),
    'bow': mat('bow', srgb('#8b3fd6'), rough=0.7, sheen=0.6, sheen_tint=srgb('#d6b4ff'), spec=0.35),
    'pack': mat('pack', srgb('#efab1f'), rough=0.6, sheen=0.4, sheen_tint=srgb('#fff0b8'), spec=0.35),
    'packdark': mat('packdark', srgb('#d99a1c'), rough=0.6, spec=0.35),
}

# ------------------------------------------------------------------ helpers
def link(o):
    coll.objects.link(o); return o

def sphere(name, loc, rad, seg=24, rings=14, rot=None, material=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    S = Matrix.Diagonal((rad[0], rad[1], rad[2], 1))
    R = (rot or Quaternion()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation(loc) @ R @ S, verts=bm.verts)
    bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me))
    if material: me.materials.append(material)
    return o

def capsule(name, a, b, r, material=None, seg=24):
    a, b = Vector(a), Vector(b); d = b - a; L = d.length
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=16, radius=r)
    for v in bm.verts:
        if v.co.z > 0: v.co.z += L
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.transform(bm, matrix=Matrix.Translation(a) @ q.to_matrix().to_4x4(), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me))
    if material: me.materials.append(material)
    return o

def tube(name, pts, r, material=None, res=6, taper=None):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for p, c in zip(sp.bezier_points, pts):
        p.co = c; p.handle_left_type = p.handle_right_type = 'AUTO'
    cu.bevel_depth = r; cu.bevel_resolution = 2; cu.resolution_u = res; cu.use_fill_caps = True
    o = link(bpy.data.objects.new(name, cu))
    if material: cu.materials.append(material)
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.ops.object.convert(target='MESH')
    o = bpy.context.view_layer.objects.active
    if taper:
        for v in o.data.vertices: pass
    return o

def apply_all(o):
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True)
    for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)

def join(objs, name):
    for x in bpy.context.selected_objects: x.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join(); objs[0].name = name; objs[0].data.name = name
    return objs[0]

def smooth(o, angle=None):
    for p in o.data.polygons: p.use_smooth = True

# ------------------------------------------------------------------ the plush body: a core (head + torso) with limbs sewn on like a real toy.
# Each limb is its own mesh whose ball end sits inside the torso, so a shoulder or hip turns without stretching the body.
HEAD_C = Vector((0, 0, 1.40))
parts = [
    sphere('head', HEAD_C, (0.52, 0.45, 0.44), seg=48, rings=32),
    sphere('cheeks', (0, -0.05, 1.27), (0.47, 0.38, 0.30)),
    sphere('earL', (-0.40, 0.04, 1.78), (0.17, 0.10, 0.165), rot=Quaternion((0, 1, 0), math.radians(-28))),
    sphere('earR', (0.40, 0.04, 1.78), (0.17, 0.10, 0.165), rot=Quaternion((0, 1, 0), math.radians(28))),
    sphere('belly', (0, 0.0, 0.55), (0.42, 0.37, 0.40)),
    sphere('chest', (0, 0.0, 0.85), (0.33, 0.29, 0.28)),
    sphere('neck', (0, 0.0, 1.05), (0.24, 0.22, 0.14)),
    sphere('tail', (0, 0.36, 0.42), (0.08, 0.07, 0.08)),
]
body = join(parts, 'Mappy_Body')
rm = body.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = 0.016; rm.adaptivity = 0
apply_all(body)
# flatten foot soles so he stands
for v in body.data.vertices:
    if v.co.z < 0.0: v.co.z = 0.0
cs = body.modifiers.new('sm', 'CORRECTIVE_SMOOTH'); cs.factor = 0.5; cs.iterations = 6; cs.use_only_smooth = True
apply_all(body)
dec = body.modifiers.new('dec', 'DECIMATE'); dec.ratio = 0.13
apply_all(body)
smooth(body); body.data.materials.append(M['fur'])
print('body faces', len(body.data.polygons))

bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())

def surf(origin, direction, tree=None):
    hit = (tree or bvh).ray_cast(Vector(origin), Vector(direction).normalized())
    assert hit[0] is not None, (origin, direction)
    return hit[0], hit[1]

def limb(name, pieces, ratio=0.2):
    o = join(pieces, name)
    rm = o.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = 0.014; rm.adaptivity = 0
    apply_all(o)
    for v in o.data.vertices:
        if v.co.z < 0.0: v.co.z = 0.0
    cs = o.modifiers.new('sm', 'CORRECTIVE_SMOOTH'); cs.factor = 0.5; cs.iterations = 5; cs.use_only_smooth = True
    apply_all(o)
    dec = o.modifiers.new('dec', 'DECIMATE'); dec.ratio = ratio
    apply_all(o)
    smooth(o); o.data.materials.append(M['fur'])
    return o

SHOULDER = {s: Vector((s * 0.30, 0.0, 0.94)) for s in (-1, 1)}
ELBOW = {s: Vector((s * 0.455, -0.015, 0.775)) for s in (-1, 1)}
WRIST = {s: Vector((s * 0.60, -0.03, 0.62)) for s in (-1, 1)}
HAND = {s: Vector((s * 0.645, -0.04, 0.565)) for s in (-1, 1)}
HIP = {s: Vector((s * 0.20, 0.0, 0.36)) for s in (-1, 1)}
ANKLE = {s: Vector((s * 0.21, -0.02, 0.14)) for s in (-1, 1)}
arms, legs, bvh_arm, bvh_leg = {}, {}, {}, {}
for s, Ln in ((-1, 'L'), (1, 'R')):
    arms[s] = limb(f'Mappy_Arm{Ln}', [
        sphere('sh', SHOULDER[s], (0.135, 0.13, 0.135)),
        capsule('ua', SHOULDER[s], WRIST[s], 0.112),
        sphere('hand', HAND[s], (0.135, 0.125, 0.145)),
        sphere('thumb', HAND[s] + Vector((-s * 0.035, -0.095, 0.045)), (0.05, 0.05, 0.055)),
    ])
    legs[s] = limb(f'Mappy_Leg{Ln}', [
        sphere('hip', HIP[s], (0.17, 0.17, 0.17)),
        capsule('th', HIP[s], ANKLE[s], 0.15),
        sphere('foot', (s * 0.215, -0.08, 0.09), (0.16, 0.22, 0.10)),
    ])
    dg = bpy.context.evaluated_depsgraph_get()
    bvh_arm[s] = BVHTree.FromObject(arms[s], dg); bvh_leg[s] = BVHTree.FromObject(legs[s], dg)

def on_surface(name, origin, direction, rad, sink=0.3, material=None, seg=24, rings=12, spin=0.0):
    """ellipsoid whose thin axis (rad[1]) follows the surface normal, sunk into the surface"""
    p, n = surf(origin, direction)
    q = Vector((0, -1, 0)).rotation_difference(n)
    if spin: q = q @ Quaternion((0, 1, 0), spin)
    c = p + n * (rad[1] * (1 - 2 * sink))
    return sphere(name, c, rad, seg, rings, rot=q, material=material), p, n

# ------------------------------------------------------------------ face
FRONT = Vector((0, -1, 0))
INTO = Vector((0, 1, 0))
muzzle, mp, mn = on_surface('Mappy_Muzzle', (0, -2, 1.25), INTO, (0.205, 0.11, 0.15), sink=0.55, material=M['cream'], seg=32, rings=18)
smooth(muzzle)
bvh_m = BVHTree.FromObject(muzzle, bpy.context.evaluated_depsgraph_get())
def msurf(origin, d=INTO):
    h = bvh_m.ray_cast(Vector(origin), d); return h[0], h[1]

# nose: rounded, wider at top
np_, nn = msurf((0, -2, 1.31))
nose = sphere('Mappy_Nose', np_ + nn * 0.012, (0.072, 0.045, 0.052), rot=Vector((0, -1, 0)).rotation_difference(nn), material=M['nose'])
for v in nose.data.vertices:
    t = (v.co.z - (np_.z)) / 0.05
    v.co.x *= 1 + 0.25 * max(0, t)
smooth(nose)
sh_ = sphere('Mappy_NoseShine', np_ + nn * 0.05 + Vector((-0.022, 0, 0.022)), (0.016, 0.006, 0.011), material=M['shine'])

# mouth: the "ω" smile, drawn on the muzzle; shape keys bend it
def mouth_pts(k_smile):
    pts = []
    xs = [-0.11, -0.075, -0.035, 0.0, 0.035, 0.075, 0.11]
    for x in xs:
        u = abs(x) / 0.11
        dip = math.sin(min(1, u / 0.55) * math.pi * 0.5 if u < 0.55 else math.pi * 0.5 + (u - 0.55) / 0.45 * math.pi * 0.5) if u > 0 else 0
        # two bowls meeting at the centre: low in each bowl, high at centre and ends
        y = -0.045 * math.sin(u * math.pi) * k_smile
        z = 1.225 + y + (0.02 * (1 - u) ** 6) * k_smile
        pts.append((x, z))
    return pts

def mouth_mesh(k):
    pts3 = []
    for x, z in mouth_pts(k):
        p, n = msurf((x, -2, z)); pts3.append(p + n * 0.006)
    stem_top, n = msurf((0, -2, 1.28)); stem_bot, _ = msurf((0, -2, 1.225))
    return pts3, stem_top + n * 0.006, stem_bot + n * 0.006

pts3, st, sb = mouth_mesh(1.0)
mouth = tube('Mappy_Mouth', pts3, 0.011, M['line'])
stem = tube('Mappy_MouthStem', [st, (st + sb) / 2, sb], 0.011, M['line'])
mouth = join([mouth, stem], 'Mappy_Mouth')
smooth(mouth)

# open mouth: a dark oval with a tongue that grows from nothing (shape key 'open')
op, on = msurf((0, -2, 1.19))
mo = sphere('Mappy_MouthOpen', op + on * 0.004, (0.075, 0.02, 0.06), rot=Vector((0, -1, 0)).rotation_difference(on), material=M['mouth'])
tg = sphere('tongue', op + on * 0.016 + Vector((0, 0, -0.03)), (0.045, 0.012, 0.025), rot=Vector((0, -1, 0)).rotation_difference(on), material=M['tongue'])
mo = join([mo, tg], 'Mappy_MouthOpen'); smooth(mo)

# eyes, highlights, brows, blush
EYE = (0.062, 0.03, 0.078)
eyes, shines, brows, blush = [], [], [], []
for s in (-1, 1):
    e, ep, en = on_surface(f'Mappy_Eye{"L" if s < 0 else "R"}', (s * 0.175, -2, 1.47), INTO, EYE, sink=0.5, material=M['eye'])
    smooth(e); eyes.append((e, ep, en))
    hl = sphere(f'Mappy_EyeShine{"L" if s < 0 else "R"}', ep + en * 0.03 + Vector((s * -0.012 - 0.012, 0, 0.032)), (0.017, 0.008, 0.019), material=M['shine'])
    hl2 = sphere('hl2', ep + en * 0.03 + Vector((0.016, 0, -0.025)), (0.009, 0.004, 0.009), material=M['shine'])
    hl = join([hl, hl2], hl.name); shines.append(hl)
    pts = []
    for t in (-1, -0.5, 0, 0.5, 1):
        p, n = surf((s * 0.175 + t * 0.055, -2, 1.62 - 0.012 * t * t), INTO); pts.append(p + n * 0.008)
    b = tube(f'Mappy_Brow{"L" if s < 0 else "R"}', pts, 0.012, M['line']); smooth(b); brows.append(b)
    bl, _, _ = on_surface(f'Mappy_Blush{"L" if s < 0 else "R"}', (s * 0.33, -2, 1.30), INTO, (0.075, 0.012, 0.045), sink=0.2, material=M['blush'])
    smooth(bl); blush.append(bl)

# ears: cream inner discs
ear_inner = []
for s in (-1, 1):
    o = Vector((s * 0.40, -2, 1.78))
    p, n = surf(o, INTO)
    e = sphere(f'Mappy_EarIn{"L" if s < 0 else "R"}', p + n * 0.0, (0.105, 0.035, 0.10), rot=Vector((0, -1, 0)).rotation_difference(n), material=M['cream'])
    smooth(e); ear_inner.append(e)

# paw pads on both hands (palms face forward-down) and soles
pads = []
for s in (-1, 1):
    hc = HAND[s]
    d = Vector((0, -1, -0.35)).normalized()
    p, n = surf(hc + d * 1.0, -d, bvh_arm[s])
    pad = sphere(f'Mappy_Pad{"L" if s < 0 else "R"}', p + n * -0.012, (0.06, 0.02, 0.055), rot=Vector((0, -1, 0)).rotation_difference(n), material=M['cream'])
    smooth(pad); pads.append(pad)
    so, sn = surf(Vector((s * 0.215, -0.09, -1)), Vector((0, 0, 1)), bvh_leg[s])
    sole = sphere(f'Mappy_Sole{"L" if s < 0 else "R"}', so + Vector((0, 0, 0.004)), (0.11, 0.15, 0.012), material=M['cream'])
    smooth(sole); pads.append(sole)

# ------------------------------------------------------------------ outfit
# bow tie on the neck
bp, bn = surf((0, -2, 1.06), INTO)
qb = Vector((0, -1, 0)).rotation_difference(bn)
bow = []
for s in (-1, 1):
    lobe = sphere('lobe', bp + bn * 0.05 + qb @ Vector((s * 0.105, 0, 0)), (0.11, 0.05, 0.075), rot=qb @ Quaternion((0, 1, 0), s * 0.18), material=M['bow'])
    # pinch toward the knot
    for v in lobe.data.vertices:
        lx = (qb.inverted() @ (v.co - bp)).x * s
        k = max(0.0, 1 - lx / 0.11)
        rel = v.co - (bp + bn * 0.05)
        local = qb.inverted() @ rel
        local.z *= 1 - 0.55 * k * k
        v.co = bp + bn * 0.05 + qb @ local
    bow.append(lobe)
bow.append(sphere('knot', bp + bn * 0.075, (0.042, 0.035, 0.048), rot=qb, material=M['bow']))
bow = join(bow, 'Mappy_Bow'); smooth(bow)

# backpack: rounded box + flap + straps
pk = sphere('pack', (0, 0.38, 0.72), (0.31, 0.17, 0.32), seg=32, rings=18, material=M['pack'])
for v in pk.data.vertices:  # squarish
    for i, r in ((0, 0.31), (2, 0.32)):
        t = v.co[i] - (0, 0.38, 0.72)[i]
        v.co[i] = (0, 0.38, 0.72)[i] + math.copysign(abs(t / r) ** 0.75 * r, t)
flap = sphere('flap', (0, 0.47, 0.88), (0.28, 0.07, 0.13), material=M['packdark'])
pocket = sphere('pocket', (0, 0.53, 0.60), (0.19, 0.06, 0.13), material=M['packdark'])
straps = []
for s_ in (-1, 1):
    for side, ys in (('front', -1), ('back', 1)):
        pts = []
        for z, x in ((1.00, 0.235), (0.94, 0.265), (0.87, 0.29), (0.80, 0.305)):
            if side == 'back' and z < 0.86: continue
            p, n = surf((s_ * x, ys * 2, z), Vector((0, -ys, 0)))
            pts.append(p + n * 0.012)
        straps.append(tube('strap', pts, 0.042, M['pack']))
pack = join([pk, flap, pocket] + straps, 'Mappy_Backpack'); smooth(pack)

# ------------------------------------------------------------------ skeleton
arm = bpy.data.armatures.new('Mappy_Rig'); rig = link(bpy.data.objects.new('Mappy_Rig', arm))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
B = {}
def bone(name, h, t, parent=None, deform=True, roll=0):
    b = arm.edit_bones.new(name); b.head = h; b.tail = t; b.roll = roll; b.use_deform = deform
    if parent: b.parent = B[parent]
    B[name] = b; return b
bone('root', (0, 0, 0), (0, 0.3, 0), deform=False)
bone('hips', (0, 0, 0.42), (0, 0, 0.66), 'root')
bone('spine', (0, 0, 0.66), (0, 0, 0.92), 'hips')
bone('neck', (0, 0, 0.98), (0, 0, 1.14), 'spine')
bone('head', (0, 0, 1.14), (0, 0, 1.70), 'neck')
for s, L in ((-1, 'L'), (1, 'R')):
    bone(f'ear.{L}', (s * 0.33, 0.04, 1.68), (s * 0.47, 0.04, 1.90), 'head')
    bone(f'eye.{L}', (s * 0.175, -0.30, 1.47), (s * 0.175, -0.42, 1.47), 'head')
    bone(f'upperarm.{L}', SHOULDER[s], ELBOW[s], 'spine')
    bone(f'forearm.{L}', ELBOW[s], WRIST[s], f'upperarm.{L}')
    bone(f'hand.{L}', WRIST[s], (s * 0.69, -0.05, 0.50), f'forearm.{L}')
    bone(f'thigh.{L}', HIP[s], (s * 0.21, -0.01, 0.16), 'hips')
    bone(f'foot.{L}', (s * 0.21, -0.01, 0.16), (s * 0.215, -0.24, 0.06), f'thigh.{L}')
bone('tail', (0, 0.30, 0.44), (0, 0.44, 0.40), 'hips')
bone('pack', (0, 0.30, 0.66), (0, 0.30, 0.95), 'spine')
bpy.ops.object.mode_set(mode='OBJECT')

def skin_auto(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

def skin_rigid(o, bone_name):
    o.parent = rig
    vg = o.vertex_groups.new(name=bone_name); vg.add(range(len(o.data.vertices)), 1.0, 'REPLACE')
    md = o.modifiers.new('Armature', 'ARMATURE'); md.object = rig

def ss(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)

def bind(o):
    o.parent = rig
    md = o.modifiers.new('Armature', 'ARMATURE'); md.object = rig

def set_weights(o, fn):
    G = {}
    for v in o.data.vertices:
        W = fn(v.co); tot = sum(W.values())
        for k, w in sorted(W.items(), key=lambda kv: -kv[1])[:4]:
            if w / tot > 0.01:
                if k not in G: G[k] = o.vertex_groups.new(name=k)
                G[k].add([v.index], w / tot, 'REPLACE')

def soften(o, repeat=4):
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=0.5, repeat=repeat)
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
    bpy.ops.object.mode_set(mode='OBJECT')

def core_w(p):
    """a smooth vertical chain hips > spine > neck > head, with ears and tail blended in"""
    z = p.z; W = {}
    w_h = ss(0.56, 0.74, z); w_s = ss(0.86, 1.02, z); w_n = ss(1.08, 1.22, z)
    W['hips'] = 1 - w_h; W['spine'] = w_h * (1 - w_s); W['neck'] = w_s * (1 - w_n); W['head'] = w_n
    def blend(f, name):
        if f <= 0: return
        for k in W: W[k] *= (1 - f)
        W[name] = W.get(name, 0) + f
    s = 1 if p.x >= 0 else -1; Ln = 'R' if s > 0 else 'L'
    if z > 1.55: blend(ss(0.24, 0.13, (p - Vector((s * 0.40, 0.04, 1.78))).length), f'ear.{Ln}')
    blend(ss(0.15, 0.08, (p - Vector((0, 0.36, 0.42))).length), 'tail')
    return W

def arm_w(s):
    Ln = 'R' if s > 0 else 'L'
    a, m, b = SHOULDER[s], ELBOW[s], WRIST[s]
    def fn(p):
        # distance along the upper arm and along the forearm decide the elbow and wrist blends
        ue = (p - m).dot((b - m).normalized())            # signed distance past the elbow
        uw = (p - b).dot((b - m).normalized())            # signed distance past the wrist
        e = ss(-0.07, 0.07, ue); w = ss(-0.05, 0.05, uw)
        return {f'upperarm.{Ln}': 1 - e, f'forearm.{Ln}': e * (1 - w), f'hand.{Ln}': e * w}
    return fn

def leg_w(s):
    Ln = 'R' if s > 0 else 'L'
    def fn(p):
        f = ss(0.22, 0.11, p.z)
        return {f'thigh.{Ln}': 1 - f, f'foot.{Ln}': f}
    return fn

bind(body); set_weights(body, core_w); soften(body, 6)
for s in (-1, 1):
    bind(arms[s]); set_weights(arms[s], arm_w(s)); soften(arms[s], 3)
    bind(legs[s]); set_weights(legs[s], leg_w(s)); soften(legs[s], 3)

# eyes must not follow the body's soft weights; the face rides the head
for o in [muzzle, nose, sh_, mouth, mo] + brows + blush:
    skin_rigid(o, 'head')
for (e, _, _), hl, L in zip(eyes, shines, 'LR'):
    skin_rigid(e, f'eye.{L}'); skin_rigid(hl, f'eye.{L}')
for e, L in zip(ear_inner, 'LR'): skin_rigid(e, f'ear.{L}')
for pad, nm in zip(pads, ['hand.L', 'foot.L', 'hand.R', 'foot.R']): skin_rigid(pad, nm)
skin_rigid(bow, 'neck')
skin_rigid(pack, 'pack')

# ------------------------------------------------------------------ facial shape keys (morph targets)
def add_key(o, name, fn):
    if not o.data.shape_keys: o.shape_key_add(name='Basis')
    k = o.shape_key_add(name=name, from_mix=False)
    for i, v in enumerate(o.data.vertices):
        k.data[i].co = fn(Vector(v.co))
    return k

for (e, ep, en), hl in zip(eyes, shines):
    c = e.matrix_world.translation.copy() if False else (ep + en * (EYE[1] * 0.3))
    add_key(e, 'blink', lambda p, c=c: Vector((c.x + (p.x - c.x) * 1.05, p.y, c.z - 0.02 + (p.z - c.z) * 0.1)))
    add_key(e, 'wide', lambda p, c=c: c + (p - c) * Vector((1.18, 1.0, 1.25)))
    # happy: the eye becomes an upward arch ("^")
    def happy(p, c=c):
        u = (p.x - c.x) / EYE[0]
        top = c.z + 0.05 * (1 - u * u) - 0.015
        return Vector((p.x, p.y, top + (p.z - c.z) * 0.18))
    add_key(e, 'happy', happy)
    add_key(e, 'sad', lambda p, c=c: Vector((p.x, p.y, c.z + (p.z - c.z) * 0.8 - 0.012 + (0.02 if p.z > c.z else 0) * -abs((p.x - c.x) / EYE[0]))))
    add_key(hl, 'blink', lambda p, c=c: Vector((p.x, p.y, c.z - 0.02 + (p.z - c.z) * 0.02)))
    add_key(hl, 'happy', lambda p, c=c: Vector((p.x, p.y, c.z + 0.02 + (p.z - c.z) * 0.02)))
    add_key(hl, 'wide', lambda p, c=c: c + (p - c) * 1.2)

for b, s in zip(brows, (-1, 1)):
    cx = s * 0.175
    add_key(b, 'up', lambda p: p + Vector((0, 0, 0.05)))
    add_key(b, 'sad', lambda p, cx=cx, s=s: p + Vector((0, 0, 0.035 * max(0, 1 - (p.x - cx) * s / 0.055 - 0.0) / 2)))
    add_key(b, 'angry', lambda p, cx=cx, s=s: p + Vector((0, 0, -0.03 * max(0, 1 - (p.x - cx) * s / 0.055) / 2)))

# mouth: grin (deeper bowls) and frown (bowls flipped)
mc = Vector((0, 0, 1.225))
add_key(mouth, 'grin', lambda p: p + Vector((0, 0, -0.025 * math.sin(min(1, abs(p.x) / 0.11) * math.pi) if p.z < 1.24 else 0)))
def frown(p):
    if p.z >= 1.245: return p
    u = min(1, abs(p.x) / 0.11)
    zb = 1.225 - 0.045 * math.sin(u * math.pi)
    zt = 1.200 + 0.030 * math.cos(u * math.pi / 2)
    return p + Vector((0, 0, zt - zb))
add_key(mouth, 'frown', frown)
add_key(mouth, 'o', lambda p: Vector((p.x * 0.45, p.y, p.z)) if p.z < 1.24 else p)
oc = op.copy()
mo.data.shape_keys if mo.data.shape_keys else None
# base of the open mouth is collapsed to a point behind the smile; 'open' restores it
orig = [Vector(v.co) for v in mo.data.vertices]
for v in mo.data.vertices: v.co = oc + (v.co - oc) * 0.02 + Vector((0, 0.01, 0))
add_key(mo, 'open', lambda p, it=iter(orig): next(it))
add_key(mo, 'o', lambda p, it=iter(orig): oc + (next(it) - oc) * Vector((0.62, 1, 1.15)))
for b in blush:
    bc = b.matrix_world.translation
    orig_b = [Vector(v.co) for v in b.data.vertices]
    cb = sum(orig_b, Vector()) / len(orig_b)
    for v in b.data.vertices: v.co = cb + (v.co - cb) * 0.02
    add_key(b, 'blush', lambda p, it=iter(orig_b): next(it))

for o in bpy.data.objects:
    if o.type == 'MESH':
        for p in o.data.polygons: p.use_smooth = True

bpy.ops.wm.save_as_mainfile(filepath=OUT + 'mappy.blend')
tris = 0
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.data.calc_loop_triangles(); n = len(o.data.loop_triangles); tris += n
        if n > 1500: print('  ', o.name, n)
print('objects', len([o for o in bpy.data.objects if o.type == 'MESH']), 'tris', tris)
