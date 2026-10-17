# Renders the economy's UI sprites to assets/ui/*.webp (transparent, 512x512): the three chests closed and open,
# a coin, a coin stack, a coin bag, a gem and a gem cluster. Same low-poly language as the game's models
# (beveled primitives, flat shading), rendered in EEVEE with a sun, a rim light and a Freestyle ink outline, so they
# read like stickers on the menu cards. Run:
#   blender --background --factory-startup --python tools/blender/ui_sprites.py [-- <dir for PNG previews>]
import bpy, math, os, random, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import reset, Part, ASSETS, euler

reset(21)
OUT = os.path.abspath(os.path.join(ASSETS, 'ui'))
os.makedirs(OUT, exist_ok=True)
INK = (0.106, 0.086, 0.25)
WOOD, WOOD_DARK = (0.55, 0.33, 0.16), (0.42, 0.24, 0.11)
GOLD, GOLD_DARK = (1.0, 0.8, 0.12), (0.82, 0.5, 0.04)
GEM, GEM_DARK = (0.22, 0.8, 1.0), (0.1, 0.5, 0.85)
METAL = { 'bronze': (0.86, 0.5, 0.2), 'silver': (0.88, 0.92, 1.0), 'gold': GOLD }
SPRITES = {}  # name -> objects


def paint(ob, rgb, rough=0.55, metal=0.0):
    m = ob.data.materials[0]
    m.diffuse_color = (*rgb, 1.0); m.roughness = rough; m.metallic = 0.0  # Workbench darkens metals; the color does the work
    return ob


def part(name, sprite):
    p = Part(name)
    SPRITES.setdefault(sprite, []).append(p)
    return p


def finish(sprite):
    """Builds every Part of a sprite into objects (keeps the color set on the Part)."""
    obs = []
    for p in SPRITES[sprite]:
        ob = p.build(); paint(ob, p.rgb, p.rough, p.metal); obs.append(ob)
    SPRITES[sprite] = obs


def colored(p, rgb, rough=0.55, metal=0.0):
    p.rgb, p.rough, p.metal = rgb, rough, metal
    return p


# ---------- chests ----------
def chest(tier, open_):
    name = f'chest_{tier}' + ('_open' if open_ else '')
    metal = METAL[tier]
    body = colored(part(name + '_wood', name), WOOD)
    body.box((0, 0, 0.36), (1.4, 0.9, 0.72), bevel=0.05)
    for i in range(4):  # planks
        body.box((-0.52 + i * 0.347, -0.455, 0.36), (0.3, 0.03, 0.66), bevel=0.01)
    bands = colored(part(name + '_metal', name), metal, rough=0.35, metal=0.6)
    for x in (-0.46, 0.46):
        bands.box((x, 0, 0.36), (0.14, 0.96, 0.76), bevel=0.02)
    for x in (-0.68, 0.68):
        for y in (-0.43, 0.43):
            bands.box((x, y, 0.08), (0.1, 0.1, 0.16), bevel=0.01)
    bands.box((0, -0.47, 0.58), (0.3, 0.06, 0.3), bevel=0.015)  # lock plate
    colored(part(name + '_hole', name), INK).box((0, -0.505, 0.58), (0.08, 0.03, 0.12), bevel=0.0)
    if tier == 'gold':
        inlay = colored(part(name + '_inlay', name), GEM, rough=0.2)
        for x in (-0.2, 0.2): inlay.ball((x, -0.46, 0.5), 0.07, subdiv=1)
    # the lid is built around its hinge (back top edge) so it can swing open
    lid = colored(part(name + '_lid', name), WOOD_DARK)
    lid.box((0, -0.45, 0.14), (1.44, 0.92, 0.28), bevel=0.05)
    lid.cyl((0, -0.45, 0.28), 0.46, 0.46, 1.44, segs=14, rot=(0, math.pi / 2, 0))
    lbands = colored(part(name + '_lidmetal', name), metal, rough=0.35, metal=0.6)
    for x in (-0.46, 0.46):
        lbands.box((x, -0.45, 0.14), (0.14, 0.98, 0.3), bevel=0.02)
        lbands.cyl((x, -0.45, 0.28), 0.49, 0.49, 0.14, segs=14, rot=(0, math.pi / 2, 0))
    lbands.box((0, -0.93, 0.16), (0.3, 0.06, 0.22), bevel=0.015)  # hasp
    if tier != 'bronze':
        trim = colored(part(name + '_trim', name), metal, rough=0.35, metal=0.6)
        trim.box((0, -0.45, 0.02), (1.5, 0.98, 0.06), bevel=0.01)
    if open_:
        glow = colored(part(name + '_glow', name), (1.0, 0.95, 0.6), rough=1.0)
        glow.box((0, 0, 0.7), (1.2, 0.7, 0.06), bevel=0.0)
        coins = colored(part(name + '_coins', name), GOLD, rough=0.3, metal=0.7)
        for i in range(14):
            x, y = random.uniform(-0.5, 0.5), random.uniform(-0.3, 0.3)
            coins.cyl((x, y, 0.72 + random.uniform(0, 0.18)), 0.14, 0.14, 0.05, segs=12, rot=(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), 0), bevel=0.01)
        if tier != 'bronze':
            gems = colored(part(name + '_gems', name), GEM, rough=0.4)
            for i in range(2 if tier == 'silver' else 4):
                gem_shape(gems, (random.uniform(-0.4, 0.4), random.uniform(-0.2, 0.2), 0.95), 0.16)
    finish(name)
    hinge = Vector((0, 0.47, 0.72))
    for ob in SPRITES[name]:
        if ob.name in (name + '_lid', name + '_lidmetal', name + '_trim', name + '_hasp'):
            ob.location = hinge
            if open_: ob.rotation_euler = (math.radians(-110), 0, 0)
    return name


# ---------- coins and gems ----------
def coin_shape(p, c, r=0.5, rot=(0, 0, 0)):
    p.cyl(c, r, r, r * 0.24, segs=24, rot=rot, bevel=r * 0.06)


def coin_inner(p, c, r=0.5, rot=(0, 0, 0)):
    p.cyl(c, r * 0.7, r * 0.7, r * 0.28, segs=24, rot=rot, bevel=0.0)


def gem_shape(p, c, r, tilt=0.0):
    """A brilliant cut from explicit faces: an octagonal table, crown facets down to the girdle, a pavilion to a point."""
    bm = p.bm; cx, cy, cz = c; m = euler((tilt, 0, 0))
    at = lambda x, y, z: bm.verts.new(Vector((cx, cy, cz)) + m @ Vector((x, y, z)))
    table = [at(0.5 * r * math.cos(a), 0.5 * r * math.sin(a), 0.42 * r) for a in (i / 8 * 2 * math.pi + math.pi / 8 for i in range(8))]
    girdle = [at(r * math.cos(a), r * math.sin(a), 0) for a in (i / 8 * 2 * math.pi + math.pi / 8 for i in range(8))]
    tip = at(0, 0, -0.95 * r)
    bm.faces.new(table)
    for i in range(8):
        bm.faces.new((table[i], girdle[i], girdle[(i + 1) % 8], table[(i + 1) % 8]))
        bm.faces.new((girdle[(i + 1) % 8], girdle[i], tip))
    p._paint(table + girdle + [tip], None)


def coin():
    p = colored(part('coin_face', 'coin'), GOLD_DARK, rough=0.35); coin_shape(p, (0, 0, 0.5), 0.5, rot=(math.radians(70), 0, math.radians(-20)))
    q = colored(part('coin_in', 'coin'), GOLD, rough=0.25); coin_inner(q, (0, 0, 0.5), 0.5, rot=(math.radians(70), 0, math.radians(-20)))
    finish('coin')


def coins():
    p = colored(part('coins_face', 'coins'), GOLD_DARK, rough=0.35)
    q = colored(part('coins_in', 'coins'), GOLD, rough=0.25)
    for i in range(7):
        c = (random.uniform(-0.04, 0.04), random.uniform(-0.04, 0.04), 0.06 + i * 0.12)
        rot = (0, 0, random.uniform(0, 1))
        coin_shape(p, c, 0.5, rot); coin_inner(q, c, 0.5, rot)
    for c, rot in (((0.75, -0.35, 0.3), (math.radians(75), 0, math.radians(30))), ((-0.7, -0.5, 0.06), (0, 0, 0.4))):
        coin_shape(p, c, 0.45, rot); coin_inner(q, c, 0.45, rot)
    finish('coins')


def bag():
    s = colored(part('bag_sack', 'bag'), (0.82, 0.58, 0.32), rough=0.9)
    s.uvsphere((0, 0, 0.56), 0.72, segs=14, rings=9, scale=(1, 0.95, 0.78))
    s.cyl((0, 0, 1.08), 0.36, 0.14, 0.4, segs=12)
    s.cyl((0.04, -0.03, 1.38), 0.14, 0.3, 0.24, segs=12, rot=(0.4, 0.25, 0))
    rope = colored(part('bag_rope', 'bag'), (0.5, 0.22, 0.12), rough=0.9)
    rope.torus((0, 0, 1.2), 0.19, 0.06, segs=14, tube=6)
    p = colored(part('bag_coins', 'bag'), GOLD_DARK, rough=0.35)
    q = colored(part('bag_coins_in', 'bag'), GOLD, rough=0.25)
    for c, rot in (((0.8, -0.3, 0.06), (0, 0, 0.3)), ((0.95, -0.1, 0.18), (0, 0, 1.2)), ((-0.75, -0.4, 0.06), (0, 0, 0.9)), ((-0.6, -0.65, 0.2), (math.radians(70), 0, 0.5))):
        coin_shape(p, c, 0.3, rot); coin_inner(q, c, 0.3, rot)
    finish('bag')


def gem():
    g = colored(part('gem_body', 'gem'), GEM, rough=0.4); gem_shape(g, (0, 0, 0.6), 0.62, tilt=-0.55)
    finish('gem')


def gems():
    g = colored(part('gems_body', 'gems'), GEM, rough=0.4)
    gem_shape(g, (0, 0, 0.55), 0.55, tilt=-0.5); gem_shape(g, (0.78, -0.3, 0.3), 0.32, tilt=-0.7); gem_shape(g, (-0.72, -0.28, 0.27), 0.28, tilt=-0.6)
    finish('gems')


for tier in ('bronze', 'silver', 'gold'):
    chest(tier, False); chest(tier, True)
coin(); coins(); bag(); gem(); gems()

# ---------- render: EEVEE, a warm sun plus a cool rim light, flat ambient, Freestyle ink outline ----------
sc = bpy.context.scene
try: sc.render.engine = 'BLENDER_EEVEE'
except TypeError: sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.eevee.taa_render_samples = 48
for m in bpy.data.materials:  # the Part colors become Principled materials
    rgb, rough = m.diffuse_color[:3], m.roughness
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = 0.0
    if 'Emission Color' in bsdf.inputs and max(rgb) > 0.6 and rgb[2] > 0.7:  # the gems glow a little
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1.0); bsdf.inputs['Emission Strength'].default_value = 0.06
world = bpy.data.worlds.new('ui'); sc.world = world; world.use_nodes = True
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
fs.crease_angle = math.radians(70)  # low enough to ink the gem facets and the chest planks
ls.linestyle.color = INK; ls.linestyle.thickness = 2.4
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 512; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'WEBP'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.quality = 92
PREVIEW = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else None
sc.view_settings.view_transform = 'Standard'
bpy.ops.object.camera_add(); cam = bpy.context.active_object; cam.data.type = 'ORTHO'; sc.camera = cam
light = Vector((-0.45, -1.0, 0.62)).normalized()  # from the front-left, above
cam.rotation_euler = light.to_track_quat('Z', 'Y').to_euler()

bpy.context.view_layer.update()
for name, obs in SPRITES.items():
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = o not in obs
    pts = [ob.matrix_world @ Vector(c) for ob in obs for c in ob.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (lo + hi) / 2
    cam.location = center + light * 10
    bpy.context.view_layer.update()
    # frame the bounding box in camera space with a small margin
    inv = cam.matrix_world.inverted()
    cs = [inv @ p for p in pts]
    w = max(p.x for p in cs) - min(p.x for p in cs); h = max(p.y for p in cs) - min(p.y for p in cs)
    cam.data.ortho_scale = max(w, h) * 1.12
    shift = Vector(((max(p.x for p in cs) + min(p.x for p in cs)) / 2, (max(p.y for p in cs) + min(p.y for p in cs)) / 2, 0))
    cam.data.shift_x = shift.x / cam.data.ortho_scale; cam.data.shift_y = shift.y / cam.data.ortho_scale
    sc.render.filepath = os.path.join(OUT, name + '.webp')
    bpy.ops.render.render(write_still=True)
    if PREVIEW:
        sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = os.path.join(PREVIEW, name + '.png'); bpy.ops.render.render(write_still=True)
        sc.render.image_settings.file_format = 'WEBP'
    print('WROTE', sc.render.filepath, len(obs), 'objects')
