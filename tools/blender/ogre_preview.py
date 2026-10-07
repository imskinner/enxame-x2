# Assembles assets/ogre.glb the way the game does (buildOgre) and renders a front and a 3/4 view.
# blender --background --factory-startup --python tools/blender/ogre_preview.py -- out.png [boss]
import bpy, sys, math
from mathutils import Matrix, Vector
args = sys.argv[sys.argv.index('--') + 1:]
out, boss = args[0], len(args) > 1
bpy.ops.wm.read_factory_settings(use_empty=True)
src = bpy.path.abspath('//') if False else None
import os
bpy.ops.import_scene.gltf(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'ogre.glb'))
G = lambda x, y, z: Vector((x, -z, y))
COL = {'skin': (0.64, 0.2, 0.42, 1), 'belly': (0.95, 0.7, 0.78, 1), 'cloth': (0.42, 0.26, 0.15, 1), 'trim': (0.67, 0.71, 0.77, 1),
       'bone': (1, 0.95, 0.84, 1), 'dark': (0.16, 0.06, 0.12, 1), 'white': (1, 1, 1, 1), 'wood': (0.48, 0.29, 0.16, 1),
       'head': (0.48, 0.29, 0.16, 1), 'gold': (1, 0.78, 0.16, 1), 'gem': (0.37, 0.95, 1, 1), 'cloth2': (0.84, 0.13, 0.27, 1)}
objs = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
for name, o in objs.items():
    key = name.split('_', 1)[1].split('.')[0]
    if name.startswith('cape'): key = 'cloth2'
    if boss and key == 'trim': key = 'gold'
    if boss and name == 'club_head': key = 'gold'
    m = bpy.data.materials.new(name + '_pv'); m.diffuse_color = COL.get(key, (0.8, 0.8, 0.8, 1)); o.data.materials.clear(); o.data.materials.append(m)


def place(name, mat):
    o = objs[name]
    o.matrix_world = mat


def dup(name, mat):
    o = objs[name].copy(); o.data = objs[name].data; bpy.context.collection.objects.link(o); o.matrix_world = mat


T = Matrix.Translation
for s, f in ((-1, dup), (1, place)):
    for part in ('leg_skin', 'leg_dark'): f(part, T(G(s * 0.2, 0.46, 0)))
    for part in ('arm_skin', 'arm_trim'): f(part, T(G(s * 0.52, 1.06, 0)))
hm = T(G(0, 1.36, 0.02))
for part in ('head_skin', 'head_white', 'head_dark', 'head_bone', 'horns_bone', 'crown_gold', 'crown_gem'):
    place(part, hm)
club = T(G(0.52, 1.06, 0)) @ T(G(0, -0.56, 0.05)) @ Matrix.Rotation(-0.35, 4, 'X')
for part in ('club_wood', 'club_head', 'club_bone'): place(part, club)
for name, o in objs.items():
    if boss and name.startswith('horns'): o.hide_render = True
    if not boss and (name.startswith('crown') or name.startswith('cape')): o.hide_render = True

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_cavity = True; sc.display.shading.show_shadows = True
sc.render.resolution_x, sc.render.resolution_y = 1200, 800
sc.render.film_transparent = False
for i, (loc, rot, lens) in enumerate((((1.0, -4.2, 1.3), (math.radians(86), 0, math.radians(13)), 55),
                                      ((3.4, -2.6, 1.6), (math.radians(80), 0, math.radians(52)), 55))):
    bpy.ops.object.camera_add(location=loc, rotation=rot)
    cam = bpy.context.active_object; cam.data.lens = lens; sc.camera = cam
    sc.render.filepath = out.replace('.png', f'_{i}.png')
    bpy.ops.render.render(write_still=True)
