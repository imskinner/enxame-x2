# Generates assets/characters.glb: the blue soldier and the red imp used by the crowd shader.
# Run: blender --background --factory-startup --python tools/blender/characters.py
# Each character is one mesh with two float color layers the game decodes per vertex:
#   COLOR_0 "Col"  : base color (linear RGB). Team parts are white * shade and get the team tint in the game.
#   COLOR_1 "Meta" : R = team tint (0/1), G = (swing + 1) / 2 (walk cycle: -1, 0, +1), B = pivot height / 2.
# Front (face) is Blender -Y = game +Z. Origin at the feet. Units match the old procedural models.
import bpy, bmesh, math, os, sys
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import reset, euler, ASSETS

reset(2)


def lin(hexv):
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (c((hexv >> 16) & 255), c((hexv >> 8) & 255), c(hexv & 255))


class Char:
    def __init__(self, name):
        self.name, self.bm = name, bmesh.new()
        self.col = self.bm.loops.layers.float_color.new('Col')
        self.meta = self.bm.loops.layers.float_color.new('Meta')

    def _tag(self, verts, hexv, tint, swing, pivot, shade):
        c = (1.0, 1.0, 1.0) if tint else lin(hexv)
        c = tuple(x * shade for x in c)
        for f in {f for v in verts for f in v.link_faces}:
            for l in f.loops:
                l[self.col] = (*c, 1.0)
                l[self.meta] = (float(tint), (swing + 1) / 2, pivot / 2, 1.0)

    def g(self, x, y, z):  # game coords -> Blender coords
        return Vector((x, -z, y))

    def ball(self, at, r, hexv, scale=(1, 1, 1), rot=(0, 0, 0), segs=10, rings=7, tint=0, swing=0, pivot=0, shade=1.0, half=False):
        sx, sy, sz = scale  # game axes
        m = Matrix.Translation(self.g(*at)) @ euler(rot) @ Matrix.Diagonal((sx, sz, sy, 1))
        v = bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=rings, radius=r, matrix=m)['verts']
        if half:
            cz = self.g(*at).z
            kill = [x for x in v if x.co.z < cz - 1e-4]
            bmesh.ops.delete(self.bm, geom=kill, context='VERTS')
            v = [x for x in v if x.is_valid]
        self._tag(v, hexv, tint, swing, pivot, shade)

    def caps(self, at, r, length, hexv, rot=(0, 0, 0), segs=8, **kw):
        """Capsule along game Y (Blender Z)."""
        self.ball(at, r, hexv, scale=(1, (r + length / 2) / r, 1), rot=rot, segs=segs, rings=8, **kw)

    def cone(self, at, r1, r2, depth, hexv, rot=(0, 0, 0), segs=8, tint=0, swing=0, pivot=0, shade=1.0):
        m = Matrix.Translation(self.g(*at)) @ euler(rot)
        v = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=depth, matrix=m)['verts']
        self._tag(v, hexv, tint, swing, pivot, shade)

    def box(self, at, size, hexv, rot=(0, 0, 0), bevel=0.0, tint=0, swing=0, pivot=0, shade=1.0):
        sx, sy, sz = size
        m = Matrix.Translation(self.g(*at)) @ euler(rot) @ Matrix.Diagonal((sx, sz, sy, 1))
        v = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)['verts']
        self._tag(v, hexv, tint, swing, pivot, shade)
        if bevel:
            edges = list({e for x in v for e in x.link_edges})
            bmesh.ops.bevel(self.bm, geom=edges + list(v), offset=bevel, segments=1, affect='EDGES')

    def torus(self, at, R, r, hexv, segs=16, tube=5, tint=0, swing=0, pivot=0, shade=1.0):
        rows = []
        c = self.g(*at)
        for i in range(segs):
            a = i / segs * 2 * math.pi
            rows.append([self.bm.verts.new(c + Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b))))
                         for b in (j / tube * 2 * math.pi for j in range(tube))])
        for i in range(segs):
            for j in range(tube):
                self.bm.faces.new((rows[i][j], rows[(i + 1) % segs][j], rows[(i + 1) % segs][(j + 1) % tube], rows[i][(j + 1) % tube]))
        self._tag([v for r_ in rows for v in r_], hexv, tint, swing, pivot, shade)

    def build(self):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me); self.bm.free()
        for p in me.polygons: p.use_smooth = True
        me.color_attributes.active_color = me.color_attributes['Col']
        me.color_attributes.render_color_index = me.color_attributes.find('Col')
        ob = bpy.data.objects.new(self.name, me); bpy.context.collection.objects.link(ob)
        me.materials.append(bpy.data.materials.new(self.name))
        return ob


TEAM, SKIN, INK, GOLD = 0xffffff, 0xffd2b0, 0x1b1640, 0xffc629

# ---------------- Soldier (runs away from the camera: back gear faces it) ----------------
s = Char('soldier')
for k in (-1, 1):
    leg = dict(swing=k, pivot=0.42)
    arm = dict(swing=-k, pivot=0.84)
    s.caps((k * 0.13, 0.22, 0), 0.1, 0.2, 0x27306e, **leg)
    s.ball((k * 0.13, 0.07, 0.03), 0.12, 0x3b2a20, scale=(1, 0.6, 1.4), **leg)
    s.box((k * 0.13, 0.15, 0.03), (0.22, 0.05, 0.26), 0x2a1d16, **leg)  # boot cuff
    s.caps((k * 0.36, 0.64, 0), 0.085, 0.24, TEAM, rot=(0, -k * 0.22, 0), tint=1, shade=0.85, **arm)
    s.ball((k * 0.39, 0.45, 0), 0.085, SKIN, **arm)
    s.ball((k * 0.31, 0.86, 0), 0.13, TEAM, scale=(1.1, 0.75, 1.1), tint=1, shade=0.7, half=True)  # shoulder pad
    s.ball((k * 0.09, 1.08, 0.23), 0.045, INK, segs=6, rings=4)
    s.ball((k * 0.25, 1.06, 0.0), 0.06, SKIN, scale=(0.6, 1, 1), segs=6, rings=4)  # ears
s.caps((0, 0.66, 0), 0.27, 0.26, TEAM, segs=12, tint=1)
s.torus((0, 0.5, 0), 0.268, 0.045, GOLD, segs=18)
s.box((0, 0.5, 0.29), (0.11, 0.09, 0.04), 0xfff0a0)
for k in (-1, 1): s.box((k * 0.2, 0.47, -0.18), (0.1, 0.12, 0.08), 0x6b4a30, rot=(0, 0, k * 0.5))  # pouches
s.ball((0, 1.1, 0), 0.25, SKIN, segs=12, rings=9)
s.ball((0, 1.04, 0.24), 0.04, 0xf2b08a, segs=6, rings=4)  # nose
s.ball((0, 1.12, -0.01), 0.285, TEAM, segs=14, rings=9, tint=1, shade=0.78, half=True)  # helmet
s.cone((0, 1.085, 0), 0.32, 0.3, 0.05, TEAM, segs=16, tint=1, shade=0.6)  # brim
for k in (-1, 1): s.box((k * 0.24, 0.98, 0.02), (0.05, 0.16, 0.14), TEAM, tint=1, shade=0.65)  # cheek guards
s.box((0, 1.44, -0.03), (0.05, 0.12, 0.32), GOLD, bevel=0.01)  # crest
s.ball((0, 1.47, -0.2), 0.07, 0xff4a5a, scale=(0.8, 1, 1.6), segs=6, rings=4)  # plume tail
s.box((0, 0.72, -0.3), (0.36, 0.38, 0.18), 0x7d5a3c, bevel=0.02)  # backpack
s.box((0, 0.84, -0.4), (0.36, 0.14, 0.04), 0x6b4a30)  # flap
s.cone((0, 0.95, -0.32), 0.085, 0.085, 0.42, 0x5b8c4a, rot=(0, math.pi / 2, 0), segs=8)  # bedroll
for k in (-1, 1): s.cone((k * 0.21, 0.95, -0.32), 0.09, 0.09, 0.02, 0x8a6a40, rot=(0, math.pi / 2, 0), segs=8)
s.build()

# ---------------- Imp (charges at the camera: face and club toward it) ----------------
RED = TEAM
i = Char('imp')
for k in (-1, 1):
    leg = dict(swing=k, pivot=0.4, tint=1)
    arm = dict(swing=-k, pivot=0.86, tint=1)
    i.caps((k * 0.14, 0.2, 0), 0.1, 0.18, RED, shade=0.7, **leg)
    i.ball((k * 0.14, 0.06, 0.05), 0.12, RED, scale=(1.1, 0.55, 1.4), shade=0.5, **leg)
    for t in (-1, 0, 1): i.cone((k * 0.14 + t * 0.06, 0.05, 0.2), 0.03, 0.0, 0.08, 0xfff1d6, rot=(-math.pi / 2, 0, 0), segs=4, swing=k, pivot=0.4)  # toe claws
    i.caps((k * 0.37, 0.66, 0), 0.085, 0.28, RED, rot=(0, -k * 0.35, 0), shade=0.85, **arm)
    i.ball((k * 0.44, 0.46, 0), 0.09, RED, shade=0.7, **arm)
    i.cone((k * 0.15, 1.36, -0.02), 0.065, 0.0, 0.26, 0xfff1d6, rot=(0.25, k * 0.45, 0), segs=6)  # horns
    i.cone((k * 0.34, 1.12, -0.02), 0.085, 0.0, 0.26, RED, rot=(0, k * 1.25, 0), segs=5, tint=1, shade=0.8)  # ears
    i.ball((k * 0.11, 1.13, 0.21), 0.09, 0xffffff, segs=8, rings=6)
    i.ball((k * 0.105, 1.12, 0.295), 0.047, 0x140f30, segs=6, rings=4)
    i.ball((k * 0.09, 1.145, 0.325), 0.015, 0xffffff, segs=4, rings=3)  # eye glint
    i.box((k * 0.11, 1.235, 0.265), (0.15, 0.04, 0.045), 0x140f30, rot=(0, k * 0.45, 0))
    i.cone((k * 0.055, 0.955, 0.28), 0.028, 0.0, 0.08, 0xffffff, rot=(math.pi / 2, 0, 0), segs=4)  # fangs
i.caps((0, 0.66, 0), 0.3, 0.3, RED, segs=12, tint=1)
i.ball((0, 0.62, 0.17), 0.22, 0xffd6b8, scale=(1, 1.1, 0.5))
i.ball((0, 1.08, 0), 0.3, RED, segs=12, rings=9, tint=1)
i.box((0, 0.975, 0.275), (0.2, 0.05, 0.03), 0x3a0d1a)
for t in range(3):  # back spikes
    i.cone((0, 1.0 - t * 0.2, -0.3 + t * 0.02), 0.06, 0.0, 0.16, RED, rot=(math.pi / 2 + 0.6, 0, 0), segs=4, tint=1, shade=0.6)
# tail: a curve of shrinking segments ending in a spade
for t in range(5):
    a = t / 5
    i.ball((0.05 * t, 0.42 - a * 0.1 + a * a * 0.5, -0.32 - t * 0.09), 0.05 - t * 0.006, RED, segs=6, rings=4, tint=1, shade=0.75)
i.cone((0.27, 0.66, -0.78), 0.08, 0.0, 0.14, RED, rot=(0.9, 0, 0), segs=4, tint=1, shade=0.6)
club = dict(swing=-1, pivot=0.86)
i.cone((0.45, 0.58, 0.14), 0.04, 0.07, 0.55, 0x7a4b2a, rot=(-0.5, 0, 0), segs=6, **club)
i.ball((0.45, 0.83, 0.28), 0.11, 0x5a3418, segs=8, rings=6, **club)
for (dx, dy, dz) in ((0.1, 0, 0), (-0.1, 0, 0), (0, 0.1, 0), (0, 0, 0.1), (0, -0.07, 0.07)):
    i.cone((0.45 + dx, 0.83 + dy, 0.28 + dz), 0.025, 0.0, 0.08, 0xd8d0c0, rot=(math.atan2(dz, dy) if dy or dz else 0, 0, -math.atan2(dx, dy) if dx else 0), segs=4, **club)
i.build()

out = os.path.abspath(os.path.join(ASSETS, 'characters.glb'))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_apply=True, export_normals=True,
                          export_vertex_color='ACTIVE', export_all_vertex_colors=True, export_yup=True)
print('WROTE', out, {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects})
