# Generates assets/ogre.glb: brute/boss ogre parts. Run:
#   blender --background --factory-startup --python tools/blender/ogre.py
# The game keeps its ogre hierarchy (hips, shoulders, head, club animate) and boss decorations; each object here
# is one part in its group's local frame, named <group>_<material> (see buildOgre in index.html):
#   leg_*: hip frame (pivot at the hip)   body_*/cape_*: root frame (feet on the ground)   head_*/horns_*/crown_*: head frame
#   arm_*: shoulder frame                  club_*: club frame (handle along +Y)
# Coordinates below are written in game space (x right, y up, z toward the camera) and converted to Blender.
import bpy, bmesh, math, os, sys, random
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import Part, reset, export, euler

reset(4)


def G(x, y, z):
    return (x, -z, y)


def GS(sx, sy, sz):
    return (sx, sz, sy)


def flesh(name, lumps, voxel, faces):
    """Organic shape: union of scaled spheres (game coords) -> voxel remesh -> decimate, smooth shaded."""
    objs = []
    for (c, r, s) in lumps:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=r, location=G(*c))
        o = bpy.context.active_object; o.scale = GS(*s)
        bpy.ops.object.transform_apply(location=False, scale=True)
        objs.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = objs[0]
    rm = o.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = voxel
    bpy.ops.object.modifier_apply(modifier='rm')
    sm = o.modifiers.new('sm', 'SMOOTH'); sm.iterations = 4; sm.factor = 0.6
    bpy.ops.object.modifier_apply(modifier='sm')
    dec = o.modifiers.new('dec', 'DECIMATE'); dec.ratio = min(1.0, faces / max(1, len(o.data.polygons)))
    bpy.ops.object.modifier_apply(modifier='dec')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o.name = o.data.name = name
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.clear(); o.data.materials.append(bpy.data.materials.get(name) or bpy.data.materials.new(name))
    return o


class GP(Part):
    """Part with game-space coordinates."""
    def gbox(self, c, size, rot=(0, 0, 0), bevel=0.02):
        return self.box(G(*c), GS(*size), rot=grot(rot), bevel=bevel)

    def gcyl(self, c, r1, r2, h, segs=12, rot=(0, 0, 0)):
        # Blender cones run along Z (= game Y); rotate them like a game cylinder
        return self.cyl(G(*c), r1, r2, h, segs=segs, rot=grot(rot))

    def gball(self, c, r, s=(1, 1, 1), segs=10, rings=7):
        return self.uvsphere(G(*c), r, segs=segs, rings=rings, scale=GS(*s))

    def gtorus(self, c, R, r, segs=20, tube=6, rot=(0, 0, 0)):
        # Part.torus lies in Blender XY = game XZ (a horizontal ring in the game)
        return self.torus(G(*c), R, r, segs=segs, tube=tube, rot=grot(rot))


def grot(r):
    """Game Euler (x, y, z) -> Blender Euler: game X stays X, game Y is Blender Z, game Z is Blender -Y."""
    return (r[0], -r[2], r[1])


def horn_chain(p, base, s, scale=1.0):
    """A curved horn: three shrinking frustums bending outward and up."""
    x, y, z = base
    r, ang = 0.065 * scale, 0.5
    for i in range(3):
        h = 0.11 * scale
        dx, dy = math.sin(ang) * s, math.cos(ang)
        p.gcyl((x + dx * h / 2, y + dy * h / 2, z), r, r * 0.7 if i < 2 else 0.0, h, segs=8, rot=(0, 0, -s * ang))
        x, y = x + dx * h * 0.9, y + dy * h * 0.9
        r *= 0.7; ang -= 0.45


# ---------------- Leg (hip frame) ----------------
flesh('leg_skin', [((0, -0.1, 0), 0.17, (1, 1.25, 1)), ((0, -0.2, 0.04), 0.12, (1, 1, 1)),
                   ((0, -0.31, 0.01), 0.14, (1, 1.25, 1))], 0.025, 900)
boot = GP('leg_dark')
boot.gball((0, -0.4, 0.06), 0.17, (1.1, 0.55, 1.45), segs=14, rings=8)
boot.gcyl((0, -0.33, 0), 0.155, 0.16, 0.1, segs=14)
for t in (-1, 0, 1): boot.gcyl((t * 0.07, -0.42, 0.29), 0.035, 0.0, 0.09, segs=5, rot=(math.pi / 2, 0, 0))
boot.build(smooth=False)

# ---------------- Body (root frame) ----------------
flesh('body_skin', [((0, 0.92, 0), 0.44, (1.05, 0.95, 0.82)), ((0, 0.72, 0.03), 0.38, (1, 0.9, 0.85)),
                    ((0.3, 1.15, -0.02), 0.2, (1, 1, 1)), ((-0.3, 1.15, -0.02), 0.2, (1, 1, 1)),
                    ((0.17, 1.0, 0.2), 0.2, (1, 0.8, 0.6)), ((-0.17, 1.0, 0.2), 0.2, (1, 0.8, 0.6)),
                    ((0, 1.22, 0), 0.17, (1, 1, 1))], 0.035, 1600)
flesh('body_belly', [((0, 0.78, 0.25), 0.3, (1, 1.05, 0.5)), ((0, 0.66, 0.22), 0.22, (1.1, 0.8, 0.5))], 0.03, 500)
cloth = GP('body_cloth')
cloth.gcyl((0, 0.5, 0), 0.44, 0.38, 0.22, segs=16)
for z in (0.41, -0.41):
    cloth.gbox((0, 0.33, z), (0.32, 0.3, 0.05), rot=(0.12 if z > 0 else -0.12, 0, 0), bevel=0.015)
for x in (-0.3, 0.3): cloth.gbox((x, 0.36, 0.3), (0.16, 0.22, 0.05), rot=(0.1, x * 0.8, 0), bevel=0.01)
cloth.build()
trim = GP('body_trim')
trim.gtorus((0, 0.6, 0), 0.405, 0.05, segs=24, tube=6)
trim.gbox((0, 0.6, 0.44), (0.15, 0.13, 0.05), bevel=0.015)
for s in (-1, 1):
    trim.gball((s * 0.43, 1.09, 0), 0.22, (1.05, 0.9, 1.05), segs=14, rings=8)
    trim.gtorus((s * 0.43, 1.06, 0), 0.215, 0.025, segs=18, tube=4)
trim.gbox((0, 0.88, 0.335), (0.08, 0.95, 0.03), rot=(0, 0, 0.62), bevel=0.0)  # chest strap
trim.gbox((0, 0.88, -0.36), (0.08, 0.95, 0.03), rot=(0, 0, -0.62), bevel=0.0)
trim.build()
bone = GP('body_bone')
for s in (-1, 1):
    for dz in (-0.09, 0.0, 0.09):
        bone.gcyl((s * 0.45, 1.29 + (0.04 if dz == 0 else 0), dz), 0.05, 0.0, 0.18 if dz == 0 else 0.14, segs=6, rot=(0, 0, -s * 0.25))
bone.build()

# ---------------- Head (head frame) ----------------
flesh('head_skin', [((0, 0, 0), 0.26, (1, 0.95, 1)), ((0, -0.13, 0.08), 0.2, (1.05, 0.6, 0.95)),
                    ((0, 0.0, 0.25), 0.065, (1.2, 0.85, 1)), ((0, 0.09, 0.18), 0.1, (2.6, 0.5, 0.75)),
                    ((0.27, 0.02, -0.02), 0.09, (0.45, 0.85, 0.7)), ((-0.27, 0.02, -0.02), 0.09, (0.45, 0.85, 0.7))], 0.02, 1100)
eyes = GP('head_white'); dark = GP('head_dark'); tusk = GP('head_bone')
for s in (-1, 1):
    eyes.gball((s * 0.09, 0.03, 0.205), 0.062, segs=10, rings=7)
    dark.gball((s * 0.09, 0.03, 0.258), 0.032, segs=8, rings=5)
    dark.gbox((s * 0.095, 0.125, 0.235), (0.13, 0.03, 0.04), rot=(0, 0, s * 0.35), bevel=0.0)
    dark.gball((s * 0.03, -0.02, 0.305), 0.018, segs=6, rings=4)
    tusk.gcyl((s * 0.11, -0.04, 0.2), 0.04, 0.0, 0.14, segs=8, rot=(0.15, 0, -s * 0.15))
    tusk.gbox((s * 0.035, -0.09, 0.255), (0.04, 0.05, 0.03), bevel=0.005)
dark.gbox((0, -0.1, 0.255), (0.2, 0.022, 0.03), bevel=0.0)
for p in (eyes, dark, tusk): p.build(smooth=True)
horns = GP('horns_bone')
for s in (-1, 1): horn_chain(horns, (s * 0.19, 0.17, 0), s)
horns.build()
crown = GP('crown_gold')
crown.gcyl((0, 0.23, 0), 0.2, 0.18, 0.14, segs=16)
crown.gtorus((0, 0.17, 0), 0.2, 0.02, segs=18, tube=4)
for i in range(7):
    a = i / 7 * math.tau
    crown.gcyl((math.cos(a) * 0.18, 0.35, math.sin(a) * 0.18), 0.045, 0.0, 0.14, segs=5)
    crown.gball((math.cos(a) * 0.18, 0.43, math.sin(a) * 0.18), 0.022, segs=6, rings=4)
crown.build()
gem = GP('crown_gem')
for i in range(0, 7, 2):
    a = i / 7 * math.tau
    gem.gball((math.cos(a) * 0.205, 0.23, math.sin(a) * 0.205), 0.042, segs=6, rings=4)
gem.build()

# ---------------- Cape (root frame, boss) ----------------
cape = GP('cape_cloth')
bm = cape.bm
NX, NY = 8, 8
rows = []
for j in range(NY + 1):
    v = j / NY
    row = []
    for i in range(NX + 1):
        u = i / NX
        w = 0.8 + v * 0.35
        x = (u - 0.5) * w
        y = 1.32 - v * 1.1
        z = -0.36 - v * 0.2 + math.sin(u * math.pi * 4) * 0.035 * v
        row.append(bm.verts.new(G(x, y, z)))
    rows.append(row)
for j in range(NY):
    for i in range(NX):
        bm.faces.new((rows[j][i], rows[j + 1][i], rows[j + 1][i + 1], rows[j][i + 1]))
cape.build(smooth=True)

# ---------------- Arm (shoulder frame) ----------------
flesh('arm_skin', [((0, -0.14, 0), 0.155, (1, 1.35, 1)), ((0, -0.15, 0.06), 0.11, (1, 1, 1)),
                   ((0, -0.4, 0.01), 0.15, (1, 1.45, 1)), ((0, -0.58, 0.03), 0.16, (1, 0.95, 1.05)),
                   ((0.07, -0.6, 0.16), 0.05, (1, 1, 1)), ((-0.07, -0.6, 0.16), 0.05, (1, 1, 1)), ((0, -0.62, 0.17), 0.05, (1, 1, 1))],
      0.022, 1000)
brace = GP('arm_trim')
brace.gcyl((0, -0.43, 0.01), 0.16, 0.17, 0.15, segs=14)
for y in (-0.37, -0.49): brace.gtorus((0, y, 0.01), 0.168, 0.018, segs=16, tube=4)
brace.build()

# ---------------- Club (club frame: handle along +Y) ----------------
wood = GP('club_wood')
wood.gcyl((0, 0.3, 0), 0.05, 0.075, 0.8, segs=8)
for y in (-0.02, 0.06, 0.14): wood.gtorus((0, y, 0), 0.055, 0.016, segs=10, tube=4)
wood.build()
flesh('club_head', [((0, 0.74, 0), 0.2, (1, 1.15, 1))] + [
    ((math.cos(a) * 0.17, 0.74 + math.sin(a * 2.3) * 0.12, math.sin(a) * 0.17), 0.08, (1, 1, 1)) for a in (0.3, 1.6, 2.9, 4.2, 5.4)], 0.03, 500)
sp = GP('club_bone')
for i in range(8):
    a = i / 8 * math.tau
    d = Vector((math.cos(a), 0.6 if i % 2 else -0.15, math.sin(a))).normalized()
    c = (d.x * 0.22, 0.74 + d.y * 0.24, d.z * 0.22)
    # orient a +Y cone along d: tilt from +Y around the axis Y x d
    tilt = math.acos(max(-1, min(1, d.y)))
    yaw = math.atan2(d.x, d.z)
    sp.gcyl(c, 0.05, 0.0, 0.17, segs=6, rot=(tilt, yaw, 0))
sp.gcyl((0, 1.0, 0), 0.05, 0.0, 0.17, segs=6)
sp.build()

export('ogre.glb')
