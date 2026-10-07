# Generates assets/flora.glb: stylized low-poly trees, pines, bushes and rocks for the arena.
# Run headless:  blender --background --factory-startup --python tools/blender/flora.py
# Every object has its origin at the ground (Y-up after export) and uses one of three
# material names the game recognizes: "bark", "leaf", "rock". Colors are set in the game.
import bpy, bmesh, math, os, random, sys
from mathutils import Vector, noise
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import export

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'flora.glb')
random.seed(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
MATS = {}
for name, rgb in (('bark', (0.45, 0.3, 0.2)), ('leaf', (0.3, 0.7, 0.35)), ('rock', (0.7, 0.68, 0.78))):
    m = bpy.data.materials.new(name); m.diffuse_color = (*rgb, 1); MATS[name] = m


def finish(obj, mat, name):
    obj.name = name; obj.data.name = name
    obj.data.materials.clear(); obj.data.materials.append(MATS[mat])
    for p in obj.data.polygons: p.use_smooth = False
    return obj


def apply_mods(obj):
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)


def join(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return objs[0]


def jitter(obj, amount, scale=1.6, seed=0):
    """Organic lumps: push vertices along their normals by 3D noise."""
    me = obj.data
    off = Vector((seed * 13.1, seed * 7.7, seed * 3.3))
    for v in me.vertices:
        n = noise.noise((v.co * scale) + off)
        v.co += v.normal * n * amount


def blob(parts, voxel, faces, lump, seed):
    """Union of spheres -> voxel remesh -> noise -> decimate to a chunky low-poly shape."""
    objs = []
    for (x, y, z, r, sy) in parts:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=(x, y, z))
        o = bpy.context.active_object; o.scale.z = sy
        bpy.ops.object.transform_apply(scale=True)
        objs.append(o)
    o = join(objs)
    rm = o.modifiers.new('remesh', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = voxel
    apply_mods(o)
    jitter(o, lump, seed=seed)
    dec = o.modifiers.new('dec', 'DECIMATE'); dec.ratio = min(1.0, faces / max(1, len(o.data.polygons)))
    apply_mods(o)
    return o


def trunk(h, r0, r1, lean=0.0, branches=()):
    bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=r0, radius2=r1, depth=h, location=(0, 0, h / 2))
    t = bpy.context.active_object
    for v in t.data.vertices:  # gentle bend
        k = v.co.z / h
        v.co.x += lean * k * k
    parts = [t]
    for (ang, z, length, tilt) in branches:
        bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=r1 * 0.75, radius2=r1 * 0.35, depth=length,
                                        location=(0, 0, 0))
        b = bpy.context.active_object
        b.rotation_euler = (0, tilt, ang)
        b.location = (math.cos(ang) * math.sin(tilt) * length / 2 + lean * (z / h) ** 2,
                      math.sin(ang) * math.sin(tilt) * length / 2, z + math.cos(tilt) * length / 2)
        bpy.ops.object.transform_apply(location=True, rotation=True)
        parts.append(b)
    # roots flare
    bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=r0 * 1.6, radius2=r0 * 0.9, depth=0.35, location=(0, 0, 0.17))
    parts.append(bpy.context.active_object)
    return join(parts)


def oak(name, seed, height, spread):
    random.seed(seed)
    h = height * 0.42
    t = trunk(h + 0.5, 0.28, 0.17, lean=random.uniform(-0.2, 0.2),
              branches=[(random.uniform(0, 6.28), h * 0.75, 0.9, 0.8), (random.uniform(0, 6.28), h * 0.85, 0.8, 0.9)])
    finish(t, 'bark', name + '_bark')
    cz = h + spread * 0.45
    parts = [(0, 0, cz, spread, 0.85)]
    for i in range(random.randint(4, 6)):
        a = random.uniform(0, 6.28); d = spread * random.uniform(0.5, 0.85)
        parts.append((math.cos(a) * d, math.sin(a) * d, cz + random.uniform(-0.35, 0.55) * spread, spread * random.uniform(0.55, 0.75), 0.8))
    parts.append((0, 0, cz + spread * 0.75, spread * 0.6, 0.9))
    c = blob(parts, 0.16, 260, 0.22, seed)
    finish(c, 'leaf', name + '_leaf')


def poplar(name, seed, height):
    random.seed(seed)
    t = trunk(height * 0.35, 0.22, 0.14)
    finish(t, 'bark', name + '_bark')
    parts = []
    for i in range(5):
        z = height * 0.35 + i * height * 0.13
        r = 0.95 * math.sin(math.pi * (i + 0.8) / 5.6) + 0.35
        parts.append((random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), z + 0.4, r, 1.2))
    c = blob(parts, 0.14, 220, 0.16, seed)
    finish(c, 'leaf', name + '_leaf')


def pine(name, seed, height, tiers):
    random.seed(seed)
    t = trunk(height * 0.3, 0.2, 0.12)
    finish(t, 'bark', name + '_bark')
    cones = []
    base = height * 0.22
    for i in range(tiers):
        k = i / tiers
        r = 1.5 * (1 - k * 0.72)
        depth = height * 0.36 * (1 - k * 0.35)
        z = base + i * height * 0.19 + depth / 2
        bpy.ops.mesh.primitive_cone_add(vertices=9, radius1=r, radius2=0.0, depth=depth, location=(0, 0, z))
        cn = bpy.context.active_object
        cn.rotation_euler.z = random.uniform(0, 6.28)
        bpy.ops.object.transform_apply(rotation=True)
        # jagged skirt: alternate rim vertices up/down and in/out
        for j, v in enumerate(cn.data.vertices):
            if abs(v.co.z - (z - depth / 2)) < 1e-3:
                v.co.z += (0.18 if j % 2 else -0.08)
                v.co.x *= 1.1 if j % 2 else 0.92
                v.co.y *= 1.1 if j % 2 else 0.92
        cones.append(cn)
    c = join(cones)
    finish(c, 'leaf', name + '_leaf')


def bush(name, seed, size):
    random.seed(seed)
    parts = [(0, 0, size * 0.45, size * 0.7, 0.75)]
    for i in range(3):
        a = random.uniform(0, 6.28)
        parts.append((math.cos(a) * size * 0.55, math.sin(a) * size * 0.55, size * 0.35, size * random.uniform(0.45, 0.6), 0.75))
    c = blob(parts, 0.1, 120, 0.12, seed)
    # flatten the bottom to sit on the ground
    for v in c.data.vertices:
        if v.co.z < 0.05: v.co.z = 0.0
    finish(c, 'leaf', name + '_leaf')


def rock(name, seed, sx, sy, sz):
    random.seed(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=(0, 0, 0))
    r = bpy.context.active_object
    for v in r.data.vertices:
        v.co *= 1 + random.uniform(-0.12, 0.12)
    r.scale = (sx, sy, sz); bpy.ops.object.transform_apply(scale=True)
    jitter(r, 0.18, scale=1.2, seed=seed)
    dec = r.modifiers.new('dec', 'DECIMATE'); dec.decimate_type = 'DISSOLVE'; dec.angle_limit = math.radians(14)
    apply_mods(r)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
    # sink so it sits on the ground with a buried base
    minz = min(v.co.z for v in r.data.vertices)
    for v in r.data.vertices: v.co.z -= minz + sz * 0.25
    finish(r, 'rock', name)


oak('oak1', 1, 5.0, 1.45)
oak('oak2', 2, 4.4, 1.3)
oak('oak3', 3, 5.6, 1.6)
poplar('poplar1', 4, 5.8)
pine('pine1', 5, 6.0, 4)
pine('pine2', 6, 4.8, 3)
bush('bush1', 7, 1.0)
bush('bush2', 8, 0.85)
rock('rock1', 9, 1.0, 0.85, 0.7)
rock('rock2', 10, 1.3, 0.7, 0.55)
rock('rock3', 11, 0.7, 0.7, 0.9)

# Lay them out in a row only for previewing in Blender; the game reads each mesh at its own origin.
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)  # every origin back to the ground point
export('flora.glb')
