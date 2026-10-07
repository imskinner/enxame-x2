# Renders a lineup of every mesh in a GLB to a PNG (Workbench, flat colors by material name).
# blender --background --factory-startup --python tools/blender/preview.py -- assets/flora.glb out.png
import bpy, sys, math
args = sys.argv[sys.argv.index('--') + 1:]
src, out = args[0], args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
COL = {'bark': (0.42, 0.27, 0.17, 1), 'leaf': (0.3, 0.68, 0.32, 1), 'rock': (0.62, 0.6, 0.7, 1)}
for m in bpy.data.materials:
    for k, c in COL.items():
        if m.name.startswith(k): m.diffuse_color = c
groups = {}
for o in bpy.data.objects:
    if o.type == 'MESH': groups.setdefault(o.name.split('_')[0], []).append(o)
x = 0
for name in sorted(groups):
    w = max(max(abs(v.co.x) for v in o.data.vertices) for o in groups[name])
    x += w + 0.6
    for o in groups[name]: o.location = (x, 0, 0)
    x += w + 0.6
bpy.ops.object.camera_add(location=(x / 2, -x * 1.25, x * 0.3), rotation=(math.radians(80), 0, 0))
cam = bpy.context.active_object; cam.data.lens = 45; bpy.context.scene.camera = cam
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'VERTEX' if any(o.type == 'MESH' and o.data.color_attributes for o in bpy.data.objects) else 'MATERIAL'
sc.display.shading.show_cavity = True; sc.display.shading.show_shadows = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 600
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
