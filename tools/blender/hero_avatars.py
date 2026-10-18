# Renders the heroes' portraits to assets/ui/hero_<id>.webp: the game's own soldier (characters.soldier) baked in the
# hero's color, with the halo the march draws over the hero, plus each hero's in-game signature: Muralha's shield
# dome, Arqueira's piercing bolts, Ladrão's magnet of coins. Same render as the other UI sprites (lib.render_sprites).
# Run: blender --background --factory-startup --python tools/blender/hero_avatars.py [-- <dir for PNG previews>]
import bpy, math, os, random, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import reset, Part, ASSETS, euler, render_sprites, principled
from characters import Char, soldier, lin

reset(7)
random.seed(3)
OUT = os.path.abspath(os.path.join(ASSETS, 'ui'))
HEROES = { 'muralha': 0x4a6fa8, 'arqueira': 0x3aa65a, 'ladrao': 0x6a3d9a }  # HEROES[id].color in the game
GOLD = (1.0, 0.8, 0.12)
GROUPS = {}


def vertex_colored(ob, rough=0.75):
    """The character's material reads the baked vertex colors (the game's crowd shader does the same)."""
    m = ob.data.materials[0]; m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes.get('Principled BSDF')
    attr = nt.nodes.new('ShaderNodeVertexColor'); attr.layer_name = 'Col'
    nt.links.new(attr.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough; bsdf.inputs['Metallic'].default_value = 0.0
    return ob


def prop(name, rgb, **kw):
    """A plain-colored Part; call .build() through done()."""
    p = Part(name); p._rgb, p._kw = rgb, kw
    return p


def done(p):
    ob = p.build(); principled(ob, p._rgb, **p._kw); return ob


def brighter(hexv, k=1.6):
    return tuple(min(1.0, c * k) for c in lin(hexv))


def hero(hid, hexv):
    name = 'hero_' + hid
    ch = Char(name, team=hexv); soldier(ch); body = vertex_colored(ch.build())
    obs = [body]
    # the halo the march hangs over the hero, in the hero's color brightened
    halo = prop(name + '_halo', brighter(hexv), rough=0.4, emission=0.35)
    halo.torus((0, 0, 1.72), 0.3, 0.035, segs=24, tube=6); obs.append(done(halo))
    if hid == 'muralha':  # her dome: whoever stands inside survives a blow
        dome = prop(name + '_dome', brighter(hexv, 1.3), rough=0.2, alpha=0.22, emission=0.15)
        dome.uvsphere((0, 0, 0.78), 0.98, segs=24, rings=14); obs.append(done(dome))
        rim = prop(name + '_rim', brighter(hexv, 1.5), rough=0.3, emission=0.4)
        rim.torus((0, 0, 0.78), 0.98, 0.025, segs=40, tube=5); obs.append(done(rim))
    elif hid == 'arqueira':  # her bolts: longer range, piercing two targets
        bolts = prop(name + '_bolts', (1.0, 0.94, 0.45), rough=0.3, emission=0.6)
        for (x, z, dy) in ((-0.62, 0.72, -0.1), (0.66, 1.0, 0.15), (-0.5, 1.32, 0.3), (0.58, 0.42, -0.25)):
            bolts.cyl((x, dy, z), 0.035, 0.035, 0.9, segs=8, rot=(math.pi / 2, 0, 0))
            bolts.cyl((x, dy - 0.5, z), 0.07, 0.0, 0.14, segs=8, rot=(math.pi / 2, 0, 0))  # tip toward the camera
        obs.append(done(bolts))
    elif hid == 'ladrao':  # his magnet: coins pulled from fourteen meters
        coins = prop(name + '_coins', GOLD, rough=0.3, emission=0.08)
        for i in range(8):
            a = i / 8 * 2 * math.pi + 0.4; r = 0.72 + 0.08 * (i % 2); z = 0.35 + 0.16 * i if i < 5 else 1.45 - 0.2 * (i - 5)
            coins.cyl((r * math.cos(a), r * math.sin(a) * 0.6, z), 0.13, 0.13, 0.04, segs=16, rot=(random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), 0), bevel=0.01)
        obs.append(done(coins))
        bag = prop(name + '_bag', (0.82, 0.58, 0.32), rough=0.9)
        bag.uvsphere((0.36, 0.22, 0.52), 0.17, segs=10, rings=7, scale=(1, 0.9, 1.1)); obs.append(done(bag))
    GROUPS[name] = obs


for hid, hexv in HEROES.items():
    hero(hid, hexv)

PREVIEW = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else None
render_sprites(GROUPS, OUT, PREVIEW, margin=1.08)
