# Render previews of mappy.blend.  python3 render.py <out_prefix> <view,...> [expr] [pose]
import bpy, sys, math
from mathutils import Vector, Euler

args = sys.argv[1:]
prefix = args[0] if args else 'prev'
views = (args[1] if len(args) > 1 else 'front,q34,side,back').split(',')
expr = args[2] if len(args) > 2 else 'neutral'
pose = args[3] if len(args) > 3 else 'rest'
RES = int(__import__('os').environ.get('RES', 640))
SAMPLES = int(__import__('os').environ.get('SPP', 40))

bpy.ops.wm.open_mainfile(filepath='/home/claude/mappy3d/mappy.blend')
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4
sc.render.resolution_x = RES; sc.render.resolution_y = RES
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = -0.55

w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.93, 0.95, 0.92, 1); bg.inputs[1].default_value = 0.9

# floor that catches a soft shadow
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0)); fl = bpy.context.active_object
fm = bpy.data.materials.new('floor'); fm.use_nodes = True
fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.93, 0.95, 0.92, 1)
fm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
fl.data.materials.append(fm)

def area(name, loc, energy, size, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = color
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    d = Vector((0, 0, 1.0)) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o
area('key', (-2.6, -3.2, 3.6), 650, 3.0, (1.0, 0.97, 0.92))
area('fill', (3.2, -2.4, 1.6), 180, 4.0, (0.9, 0.96, 1.0))
area('rim', (1.5, 3.2, 3.2), 500, 2.0, (0.92, 1.0, 0.94))

cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 70
cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam

# expressions: shape key values by key name
EX = {
    'neutral': {},
    'happy': {'happy': 1, 'grin': 1, 'open': 1, 'blush': 1},
    'surprised': {'wide': 1, 'up': 1, 'o': 1},
    'sad': {'sad': 1, 'frown': 1},
    'sleepy': {'blink': 1, 'sad': 0.4},
    'angry': {'angry': 1, 'frown': 0.6},
    'laugh': {'happy': 1, 'open': 1, 'grin': 1, 'up': 0.6, 'blush': 1},
}[expr]
for o in bpy.data.objects:
    if o.type == 'MESH' and o.data.shape_keys:
        for kb in o.data.shape_keys.key_blocks[1:]:
            kb.value = EX.get(kb.name, 0)

rig = bpy.data.objects['Mappy_Rig']
P = rig.pose.bones
def rot(b, x=0, y=0, z=0):
    P[b].rotation_mode = 'XYZ'; P[b].rotation_euler = Euler((math.radians(x), math.radians(y), math.radians(z)))
from mathutils import Quaternion
def wrot(b, axis, deg):
    """rotate bone about an armature-space axis (relative to its rest frame)"""
    pb = P[b]; pb.rotation_mode = 'QUATERNION'
    R = pb.bone.matrix_local.to_quaternion()
    q = R.inverted() @ Quaternion(Vector(axis), math.radians(deg)) @ R
    pb.rotation_quaternion = q @ pb.rotation_quaternion
if pose == 'wave':
    wrot('upperarm.R', (0, 1, 0), -105); wrot('forearm.R', (0, 1, 0), -35); wrot('head', (0, 1, 0), 6)
elif pose == 'cheer':
    wrot('upperarm.R', (0, 1, 0), -120); wrot('upperarm.L', (0, 1, 0), 120); wrot('head', (1, 0, 0), -8)
elif pose == 'walk':
    wrot('thigh.L', (1, 0, 0), -30); wrot('thigh.R', (1, 0, 0), 30); wrot('upperarm.L', (1, 0, 0), 35); wrot('upperarm.R', (1, 0, 0), -35)
    wrot('upperarm.L', (0, 1, 0), -30); wrot('upperarm.R', (0, 1, 0), 30)
elif pose == 'hug':
    wrot('upperarm.L', (0, 0, 1), -70); wrot('upperarm.R', (0, 0, 1), 70); wrot('forearm.L', (0, 0, 1), -60); wrot('forearm.R', (0, 0, 1), 60)
bpy.context.view_layer.update()

VIEWS = {'front': (0, -1, 0.10), 'q34': (0.62, -0.78, 0.12), 'side': (1, 0, 0.08), 'back': (-0.4, 1, 0.15), 'face': (0.15, -1, 0.05)}
for v in views:
    d = Vector(VIEWS[v]).normalized()
    tgt = Vector((0, 0, 1.4 if v == 'face' else 1.0))
    dist = 3.0 if v == 'face' else 6.2
    cam.location = tgt + d * dist
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'/home/claude/mappy3d/out/{prefix}_{v}.png'
    bpy.ops.render.render(write_still=True)
    print('wrote', sc.render.filepath)
