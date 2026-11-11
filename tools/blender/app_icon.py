# Renders the app icon (assets/icon-512.png, icon-192.png, icon-180.png): three of the game's own soldiers under a gold
# "×2", over the game's ink purple. The render is the same as the UI sprites (lib.render_sprites); the background is
# composited here, and the soldiers stay inside the middle two thirds so the icon also works as a maskable one.
# Run: blender --background --factory-startup --python tools/blender/app_icon.py
import bpy, math, os, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import reset, ASSETS, render_sprites, principled
from characters import Char, soldier

reset(5)
obs = []
for i, (x, y) in enumerate(((0, -0.55), (-0.72, 0.3), (0.72, 0.3))):
    ch = Char('icon_soldier%d' % i, team=0x2f7bff); soldier(ch); ob = ch.build()
    m = ob.data.materials[0]; m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes.get('Principled BSDF')
    attr = nt.nodes.new('ShaderNodeVertexColor'); attr.layer_name = 'Col'
    nt.links.new(attr.outputs['Color'], bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value = 0.75
    ob.location = (x, y, 0); obs.append(ob)

bpy.ops.object.text_add(location=(0.0, 0.35, 1.62), rotation=(math.pi / 2, 0, 0))
txt = bpy.context.active_object; txt.data.body = '×2'; txt.data.align_x = 'CENTER'; txt.data.size = 1.25; txt.data.extrude = 0.09; txt.data.bevel_depth = 0.012
bpy.ops.object.convert(target='MESH')
txt.data.materials.append(bpy.data.materials.new('icon_gold')); principled(txt, (1.0, 0.78, 0.16), rough=0.35, emission=0.25)
obs.append(txt)
bpy.context.view_layer.update()

tmp = tempfile.mkdtemp()
render_sprites({'icon': obs}, tmp, tmp, size=512, light=(-0.25, -1.0, 0.42), margin=1.5)

src = bpy.data.images.load(os.path.join(tmp, 'icon.png'))
fg = np.array(src.pixels[:], dtype=np.float32).reshape(512, 512, 4)
yy, xx = np.mgrid[0:512, 0:512].astype(np.float32) / 511.0
d = np.clip(np.sqrt((xx - 0.5) ** 2 + (yy - 0.45) ** 2) / 0.72, 0, 1)[..., None]
hexc = lambda h: np.array([(h >> s & 255) / 255 for s in (16, 8, 0)], dtype=np.float32)
bg = hexc(0x4a3a9a) * (1 - d) + hexc(0x1b1640) * d  # a soft glow behind the troop, the game's ink at the corners
a = fg[..., 3:4]
out = np.concatenate([fg[..., :3] * a + bg * (1 - a), np.ones((512, 512, 1), dtype=np.float32)], axis=2)
for size in (512, 192, 180):
    img = bpy.data.images.new('icon%d' % size, 512, 512, alpha=False)
    img.pixels = out.ravel().tolist()
    if size != 512: img.scale(size, size)
    img.filepath_raw = os.path.abspath(os.path.join(ASSETS, 'icon-%d.png' % size)); img.file_format = 'PNG'; img.save()
    print('WROTE', img.filepath_raw)
