# Shared helpers for the asset scripts: build meshes from beveled primitives with bmesh, one object per
# game material, origins at the ground, flat shading, and a GLB export. Blender Z-up / -Y front becomes
# glTF Y-up / +Z front (toward the game camera).
import bpy, bmesh, math, os, random
from mathutils import Matrix, Vector

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets')


def reset(seed=1):
    random.seed(seed)
    bpy.ops.wm.read_factory_settings(use_empty=True)


class Part:
    """One output object (= one game material). Shapes are added in Blender units, Z up."""
    def __init__(self, name, shade=False):
        self.name, self.bm = name, bmesh.new()
        self.col = self.bm.loops.layers.color.new('Col') if shade else None

    def _paint(self, verts, shade):
        if self.col is None: return
        s = shade if shade is not None else random.uniform(0.85, 1.05)
        for f in {f for v in verts for f in v.link_faces}:
            for l in f.loops: l[self.col] = (s, s, s, 1.0)

    def _bevel(self, verts, amount):
        if amount > 0:
            edges = list({e for v in verts for e in v.link_edges})
            bmesh.ops.bevel(self.bm, geom=edges + list(verts), offset=amount, segments=1, affect='EDGES', profile=0.5)

    def box(self, c, size, rot=(0, 0, 0), bevel=0.03, shade=None):
        m = Matrix.Translation(c) @ euler(rot) @ Matrix.Diagonal((*size, 1))
        v = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)['verts']
        self._paint(v, shade); self._bevel(v, min(bevel, min(size) * 0.3))
        return self

    def cyl(self, c, r1, r2, depth, segs=10, rot=(0, 0, 0), bevel=0.0, shade=None, caps=True):
        m = Matrix.Translation(c) @ euler(rot)
        v = bmesh.ops.create_cone(self.bm, cap_ends=caps, segments=segs, radius1=r1, radius2=r2, depth=depth, matrix=m)['verts']
        self._paint(v, shade); self._bevel(v, bevel)
        return self

    def ball(self, c, r, scale=(1, 1, 1), subdiv=1, shade=None):
        m = Matrix.Translation(c) @ Matrix.Diagonal((*scale, 1))
        v = bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv, radius=r, matrix=m)['verts']
        self._paint(v, shade)
        return self

    def uvsphere(self, c, r, segs=12, rings=8, scale=(1, 1, 1), rot=(0, 0, 0), shade=None):
        m = Matrix.Translation(c) @ euler(rot) @ Matrix.Diagonal((*scale, 1))
        v = bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=rings, radius=r, matrix=m)['verts']
        self._paint(v, shade)
        return self

    def torus(self, c, R, r, segs=16, tube=6, rot=(0, 0, 0), shade=None):
        """Torus in the XY plane (axis Z) before rotation."""
        verts = []
        ring = []
        for i in range(segs):
            a = i / segs * 2 * math.pi
            row = []
            for j in range(tube):
                b = j / tube * 2 * math.pi
                p = Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
                row.append(self.bm.verts.new(p))
            ring.append(row)
        for i in range(segs):
            for j in range(tube):
                a, b = ring[i][j], ring[(i + 1) % segs][j]
                c2, d = ring[(i + 1) % segs][(j + 1) % tube], ring[i][(j + 1) % tube]
                self.bm.faces.new((a, b, c2, d))
            verts += ring[i]
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(c) @ euler(rot), verts=verts)
        self._paint(verts, shade)
        return self

    def build(self, smooth=False):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me); self.bm.free()
        for p in me.polygons: p.use_smooth = smooth
        if self.col is not None:
            ca = me.color_attributes['Col']; me.color_attributes.active_color = ca
            me.color_attributes.render_color_index = me.color_attributes.find('Col')
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.collection.objects.link(ob)
        mat = bpy.data.materials.get(self.name) or bpy.data.materials.new(self.name)
        me.materials.append(mat)
        return ob


def euler(rot):
    return (Matrix.Rotation(rot[2], 4, 'Z') @ Matrix.Rotation(rot[1], 4, 'Y') @ Matrix.Rotation(rot[0], 4, 'X'))


# Draco settings shared by every asset script. Position precision: 14 bits over the mesh bounds (~1 mm on the 20 m
# castle); colors get 10 bits, plenty for block shades and the crowd meta channel (tint, swing, pivot).
DRACO = dict(export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7,
             export_draco_position_quantization=14, export_draco_normal_quantization=10,
             export_draco_texcoord_quantization=12, export_draco_color_quantization=10,
             export_draco_generic_quantization=12)


def export(filename, **extra):
    out = os.path.abspath(os.path.join(ASSETS, filename))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_apply=True,
                              export_normals=True, export_vertex_color='ACTIVE', export_yup=True, **DRACO, **extra)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    print('WROTE', out, sorted(o.name for o in bpy.data.objects), 'tris:', tris)
