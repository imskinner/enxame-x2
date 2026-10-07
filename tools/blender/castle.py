# Generates assets/castle.glb: the player's wall ("home") and the enemy fort ("fort"), built from beveled
# stone blocks. Run: blender --background --factory-startup --python tools/blender/castle.py
# Each castle has two meshes, <name>_stone and <name>_roof. Per-block brightness lives in vertex colors
# (COLOR_0); the game multiplies it by its own material color, which it changes per biome and on damage.
# Blender -Y is the front (it becomes glTF +Z, toward the game camera). Origins sit at the ground.
import bpy, bmesh, math, os, random, sys
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import export

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'castle.glb')
random.seed(5)
bpy.ops.wm.read_factory_settings(use_empty=True)


class Builder:
    """Accumulates beveled boxes into one bmesh with a per-box brightness."""
    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.color.new('Col')

    def box(self, center, size, shade=None, rot_z=0.0, bevel=True, face=None):
        """face: local axis of the one visible face ((0,-1,0) for walls, (1,0,0) for tower blocks). When given,
        the opposite face is dropped and only the visible face's rim is beveled, which keeps the mesh light."""
        shade = random.uniform(0.82, 1.06) if shade is None else shade
        rot = Matrix.Rotation(rot_z, 4, 'Z')
        mat = Matrix.Translation(center) @ rot @ Matrix.Diagonal((*size, 1))
        res = bmesh.ops.create_cube(self.bm, size=1.0, matrix=mat)
        verts = res['verts']
        faces = list({f for v in verts for f in v.link_faces})
        for f in faces:
            for l in f.loops: l[self.col] = (shade, shade, shade, 1.0)
        if face is not None:
            d = (rot.to_3x3() @ Vector(face)).normalized()
            for f in faces: f.normal_update()
            front = max(faces, key=lambda f: f.normal.dot(d))
            back = min(faces, key=lambda f: f.normal.dot(d))
            bottom = min(faces, key=lambda f: f.normal.z)
            front_edges = list(front.edges)
            bmesh.ops.delete(self.bm, geom=[back] + ([bottom] if bottom is not back else []), context='FACES_ONLY')
            if bevel:
                bmesh.ops.bevel(self.bm, geom=front_edges, offset=min(0.05, min(size) * 0.22), segments=1, affect='EDGES', profile=0.5)
        elif bevel:
            edges = list({e for v in verts for e in v.link_edges})
            bmesh.ops.bevel(self.bm, geom=edges + verts, offset=min(0.045, min(size) * 0.22), segments=1, affect='EDGES', profile=0.5)

    def cylinder(self, center, r, depth, segs, shade, cap=True):
        res = bmesh.ops.create_cone(self.bm, cap_ends=cap, segments=segs, radius1=r, radius2=r, depth=depth,
                                    matrix=Matrix.Translation(center))
        for f in {f for v in res['verts'] for f in v.link_faces}:
            for l in f.loops: l[self.col] = (shade, shade, shade, 1.0)

    def cone(self, center, r0, r1, depth, segs, shade_fn):
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r0, radius2=r1, depth=depth,
                                    matrix=Matrix.Translation(center))
        for f in {f for v in res['verts'] for f in v.link_faces}:
            c = f.calc_center_median()
            s = shade_fn(c, f)
            for l in f.loops: l[self.col] = (s, s, s, 1.0)

    def to_object(self, name):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me); self.bm.free()
        ca = me.color_attributes['Col']
        me.color_attributes.active_color = ca; me.color_attributes.render_color_index = me.color_attributes.find('Col')
        for p in me.polygons: p.use_smooth = False
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        mat = bpy.data.materials.get(name.split('_')[1]) or bpy.data.materials.new(name.split('_')[1])
        me.materials.append(mat)
        return ob


def brick_wall(b, x0, x1, z0, z1, y, depth, bw=1.0, bh=0.5):
    """Running-bond blocks covering the rectangle [x0,x1]x[z0,z1] at depth center y."""
    rows = max(1, round((z1 - z0) / bh)); rh = (z1 - z0) / rows
    for r in range(rows):
        z = z0 + rh * (r + 0.5)
        x = x0 - (bw / 2 if r % 2 else 0)
        while x < x1 - 1e-3:
            a, c = max(x, x0), min(x + bw, x1)
            if c - a > 0.12:
                out = random.uniform(0.0, 0.05)
                b.box(((a + c) / 2, y - out / 2, z), (c - a - 0.05, depth + out, rh - 0.05), face=(0, -1, 0))
            x += bw


def tower(b, roof, cx, r, h, roof_r, roof_h, slits=True):
    # mortar core + rings of curved blocks
    b.cylinder((cx, 0, h / 2), r - 0.06, h, 16, 0.5)
    rows = max(1, round(h / 0.5)); rh = h / rows
    n = max(8, round(2 * math.pi * r / 1.0))
    for k in range(rows):
        z = rh * (k + 0.5)
        for i in range(n):
            a = (i + (0.5 if k % 2 else 0)) / n * 2 * math.pi
            if math.sin(a) > 0.45: continue  # back of the tower: never on camera
            out = random.uniform(0, 0.04)
            blen = 2 * math.pi * r / n - 0.05
            b.box((cx + math.cos(a) * (r + out / 2), math.sin(a) * (r + out / 2), z), (0.28 + out, blen, rh - 0.05), rot_z=a, face=(1, 0, 0), bevel=False)
    # corbel ring and crenellated top
    b.cylinder((cx, 0, h + 0.12), r + 0.22, 0.24, 20, 0.78)
    for i in range(8):
        a = i / 8 * 2 * math.pi
        b.box((cx + math.cos(a) * (r + 0.05), math.sin(a) * (r + 0.05), h + 0.55), (0.45, 0.6, 0.62), rot_z=a)
    if slits:  # dark arrow slits facing the front
        for z in (h * 0.38, h * 0.72):
            b.box((cx, -r - 0.02, z), (0.16, 0.12, 0.62), shade=0.08, bevel=False)
    # roof: cone with shingle bands (alternating brightness) and a gold-ish finial (roof material too)
    roof.cone((cx, 0, h + 0.24 + roof_h / 2), roof_r, 0.0, roof_h, 16,
              lambda c, f: (0.88 if int((c.z - h) / 0.32) % 2 else 1.0) if abs(f.normal.z) < 0.99 else 0.7)
    roof.cylinder((cx, 0, h + 0.24 + roof_h + 0.25), 0.05, 0.5, 6, 1.1)
    roof.box((cx, 0, h + 0.24 + roof_h + 0.55), (0.16, 0.16, 0.16), shade=1.2)


def castle(name, w, h, depth, tower_r, tower_h, roof_r, roof_h, fort):
    stone, roof = Builder(), Builder()
    # mortar core (dark) and block faces front and back
    stone.box((0, 0, h / 2), (w, depth - 0.1, h), shade=0.5, bevel=False)
    brick_wall(stone, -w / 2, w / 2, 0, h, -depth / 2 + 0.07, 0.16)
    # plinth course
    stone.box((0, 0, 0.18), (w + 0.25, depth + 0.3, 0.36), shade=0.7)
    # wall-walk ledge and merlons
    stone.box((0, 0, h + 0.06), (w + 0.1, depth + 0.24, 0.14), shade=0.8)
    x = -w / 2 + 0.45
    while x <= w / 2 - 0.4:
        stone.box((x, 0, h + 0.5), (0.9, depth, 0.8))
        x += 1.6
    if fort:
        # buttresses and dark slits along the front
        for bx in (-7.5, -4.2, 4.2, 7.5):
            stone.box((bx, -depth / 2 - 0.25, h * 0.35), (0.7, 0.5, h * 0.7), shade=0.78)
        for sx in (-6.0, 6.0):
            for z in (h * 0.45, h * 0.8):
                stone.box((sx, -depth / 2 - 0.02, z), (0.18, 0.1, 0.7), shade=0.08, bevel=False)
    for s in (-1, 1):
        tower(stone, roof, s * (w / 2 + 0.6), tower_r, tower_h, roof_r, roof_h, slits=True)
    stone.to_object(name + '_stone'); roof.to_object(name + '_roof')


castle('home', w=20.0, h=1.8, depth=1.6, tower_r=1.55, tower_h=4.4, roof_r=2.0, roof_h=2.6, fort=False)
fort_offset = 30.0  # placed apart only so they don't overlap in Blender; the game uses each mesh's own origin
castle('fort', w=20.0, h=6.0, depth=1.6, tower_r=1.6, tower_h=8.6, roof_r=2.1, roof_h=2.8, fort=True)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
export('castle.glb')
