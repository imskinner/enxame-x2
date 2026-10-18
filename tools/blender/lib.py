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


# ---------------- sprite renders (UI icons, hero portraits) ----------------
INK = (0.106, 0.086, 0.25)


def render_sprites(groups, out_dir, preview_dir=None, size=512, ink=INK, light=(-0.45, -1.0, 0.62), margin=1.12):
    """Renders each group of objects to <out_dir>/<name>.webp with a transparent background (and a PNG preview
    when preview_dir is given): EEVEE, a warm key sun and a cool rim light, flat ambient, Freestyle ink outline,
    orthographic camera from the front-left-above framed on the group's bounds. Materials are left as they are."""
    os.makedirs(out_dir, exist_ok=True)
    sc = bpy.context.scene
    try: sc.render.engine = 'BLENDER_EEVEE'
    except TypeError: sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.eevee.taa_render_samples = 48
    world = bpy.data.worlds.new('sprites'); sc.world = world; world.use_nodes = True
    bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.85, 0.9, 1.0, 1.0); bg.inputs[1].default_value = 0.45

    def sun(name, direction, energy, color):
        d = bpy.data.lights.new(name, 'SUN'); d.energy = energy; d.color = color; d.angle = math.radians(12)
        o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o)
        o.rotation_euler = Vector(direction).normalized().to_track_quat('Z', 'Y').to_euler()
        return o
    sun('key', (-0.5, -0.8, 1.0), 3.2, (1.0, 0.96, 0.88))
    sun('rim', (0.8, 0.7, 0.5), 1.6, (0.75, 0.88, 1.0))
    sc.render.use_freestyle = True; sc.render.line_thickness_mode = 'ABSOLUTE'; sc.render.line_thickness = 2.4
    fs = bpy.context.view_layer.freestyle_settings
    ls = fs.linesets.new('ink') if not len(fs.linesets) else fs.linesets[0]
    if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new('ink')
    ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True; ls.select_edge_mark = False
    fs.crease_angle = math.radians(70)
    ls.linestyle.color = ink; ls.linestyle.thickness = 2.4
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = size; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'WEBP'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.quality = 92
    sc.view_settings.view_transform = 'Standard'
    bpy.ops.object.camera_add(); cam = bpy.context.active_object; cam.data.type = 'ORTHO'; sc.camera = cam
    view = Vector(light).normalized()
    cam.rotation_euler = view.to_track_quat('Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    for name, obs in groups.items():
        for o in bpy.data.objects:
            if o.type == 'MESH': o.hide_render = o not in obs
        pts = [ob.matrix_world @ Vector(c) for ob in obs for c in ob.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        center = (lo + hi) / 2
        cam.location = center + view * 10
        bpy.context.view_layer.update()
        inv = cam.matrix_world.inverted()
        cs = [inv @ p for p in pts]
        w = max(p.x for p in cs) - min(p.x for p in cs); h = max(p.y for p in cs) - min(p.y for p in cs)
        cam.data.ortho_scale = max(w, h) * margin
        shift = Vector(((max(p.x for p in cs) + min(p.x for p in cs)) / 2, (max(p.y for p in cs) + min(p.y for p in cs)) / 2, 0))
        cam.data.shift_x = shift.x / cam.data.ortho_scale; cam.data.shift_y = shift.y / cam.data.ortho_scale
        sc.render.filepath = os.path.join(out_dir, name + '.webp')
        bpy.ops.render.render(write_still=True)
        print('WROTE', sc.render.filepath, len(obs), 'objects')
        if preview_dir:
            os.makedirs(preview_dir, exist_ok=True)
            sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = os.path.join(preview_dir, name + '.png'); bpy.ops.render.render(write_still=True)
            sc.render.image_settings.file_format = 'WEBP'


def principled(ob, rgb, rough=0.5, alpha=1.0, emission=0.0):
    """Gives an object's first material a Principled BSDF with a plain color (for sprite renders)."""
    m = ob.data.materials[0]; m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1.0); bsdf.inputs['Roughness'].default_value = rough; bsdf.inputs['Metallic'].default_value = 0.0
    if emission > 0 and 'Emission Color' in bsdf.inputs:
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1.0); bsdf.inputs['Emission Strength'].default_value = emission
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        for attr, val in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
            try: setattr(m, attr, val)
            except Exception: pass
        m.use_backface_culling = True
    return ob
