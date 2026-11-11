# Generates assets/worlds.glb: one roadside landmark for each of the march's eighteen worlds, so a world is more than a
# palette. Run: blender --background --factory-startup --python tools/blender/worlds.py
# Two objects per world: w_<id> carries its own colors in the vertices (the game draws all of them with one material),
# and w_<id>_glow (where there is one) is the part the game draws unlit in the world's color, so the bloom picks it up.
# Blender axes: Z up, -Y toward the camera (the side a landmark shows to the road). Origins on the ground.
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import Part, reset, export

reset(11)
TAU = math.pi * 2
R = random.uniform


def C(h, k=1.0):
    """A display color (0xRRGGBB, optionally brightened or darkened by k). The vertex layer is a byte (sRGB) layer and
    the glTF exporter linearizes it, so the game gets back exactly this color."""
    return tuple(min(1.0, ((h >> s & 255) / 255) * k) for s in (16, 8, 0))


def spire(p, x, y, h, r, tx=0.0, ty=0.0, segs=5, col=None, z0=0.0):
    """A cone standing on the ground at (x, y), leaning a little."""
    p.cyl((x + math.sin(ty) * h * 0.5, y - math.sin(tx) * h * 0.5, z0 + h / 2), r, 0.0, h, segs=segs, rot=(tx, ty, R(0, TAU)), shade=col)


# ---------- 1. ice: a cluster of shards on a snow mound ----------
p = Part('w_ice', shade=True)
p.cyl((0, 0, 0.12), 1.6, 1.25, 0.24, segs=9, shade=C(0xf4faff))
for i, (x, y, h, r, ty) in enumerate([(0, 0, 3.6, 0.6, 0.04), (0.8, 0.2, 2.3, 0.45, 0.28), (-0.75, -0.1, 2.8, 0.5, -0.26), (0.2, -0.65, 1.6, 0.38, 0.12), (-0.3, 0.7, 1.9, 0.4, -0.1)]):
    spire(p, x, y, h, r, 0.0, ty, segs=5, col=C([0xa8dcff, 0xc8ecff, 0x8fc8f8][i % 3]), z0=0.15)
p.build()

# ---------- 2. fire: a stone brazier ----------
p = Part('w_fire', shade=True)
p.cyl((0, 0, 0.2), 0.8, 0.62, 0.4, segs=8, shade=C(0x6a5a52))
p.cyl((0, 0, 1.1), 0.32, 0.26, 1.5, segs=8, shade=C(0x7a6a60))
p.cyl((0, 0, 2.05), 0.45, 0.98, 0.5, segs=10, shade=C(0x3a3030))
for a in range(6):
    p.ball((math.cos(a * TAU / 6) * 0.5, math.sin(a * TAU / 6) * 0.5, 2.3), 0.2, shade=C(0x2a2020))
p.build()
g = Part('w_fire_glow')
g.cyl((0, 0, 2.95), 0.6, 0.0, 1.4, segs=6)
g.cyl((0.28, 0.1, 2.7), 0.3, 0.0, 0.85, segs=5)
g.cyl((-0.26, -0.12, 2.65), 0.28, 0.0, 0.75, segs=5)
g.build()

# ---------- 3. lava: basalt columns with molten tops ----------
p, g = Part('w_lava', shade=True), Part('w_lava_glow')
for (x, y, h, r) in [(0, 0, 3.1, 0.52), (0.85, 0.2, 2.3, 0.46), (-0.8, 0.3, 2.7, 0.5), (0.3, -0.8, 1.6, 0.44), (-0.55, -0.65, 1.2, 0.42), (1.35, -0.5, 0.9, 0.4)]:
    p.cyl((x, y, h / 2), r, r * 0.92, h, segs=6, shade=C(0x3a3036, R(0.85, 1.2)))
    g.cyl((x, y, h + 0.02), r * 0.55, r * 0.55, 0.05, segs=6)
p.build(); g.build()

# ---------- 4. storm: a lightning rod ----------
p = Part('w_storm', shade=True)
p.cyl((0, 0, 0.25), 0.75, 0.52, 0.5, segs=8, shade=C(0x4a5568))
p.cyl((0, 0, 2.2), 0.17, 0.08, 3.6, segs=6, shade=C(0x5a6a80))
for z in (1.4, 2.3, 3.1):
    p.torus((0, 0, z), 0.5 - z * 0.09, 0.06, segs=10, tube=4, shade=C(0x8a9ab0))
p.cyl((0, 0, 4.45), 0.05, 0.0, 0.7, segs=5, shade=C(0xb0c0d0))
p.build()
Part('w_storm_glow').ball((0, 0, 4.1), 0.26, subdiv=1).build()

# ---------- 5. water: a tiered fountain and a shell ----------
p = Part('w_water', shade=True)
p.cyl((0, 0, 0.25), 1.55, 1.42, 0.5, segs=12, shade=C(0xd8cfb0))
p.cyl((0, 0, 1.0), 0.3, 0.24, 1.1, segs=8, shade=C(0xcfc6a8))
p.cyl((0, 0, 1.6), 0.5, 0.92, 0.3, segs=10, shade=C(0xd8cfb0))
p.cyl((0, 0, 2.2), 0.18, 0.14, 0.9, segs=6, shade=C(0xcfc6a8))
p.cyl((0, 0, 2.7), 0.3, 0.52, 0.2, segs=8, shade=C(0xd8cfb0))
p.uvsphere((2.0, 0.5, 0.25), 0.45, segs=8, rings=5, scale=(1, 1, 0.6), shade=C(0xff9ab0))
p.build()
g = Part('w_water_glow')
g.cyl((0, 0, 0.52), 1.32, 1.32, 0.04, segs=12)
g.cyl((0, 0, 1.77), 0.8, 0.8, 0.04, segs=10)
g.cyl((0, 0, 2.82), 0.42, 0.42, 0.04, segs=8)
g.cyl((0, 0, 3.12), 0.07, 0.02, 0.55, segs=5)
g.build()

# ---------- 6. poison: giant mushrooms with glowing spots ----------
p, g = Part('w_poison', shade=True), Part('w_poison_glow')
for (x, y, h, r) in [(0, 0, 2.7, 1.35), (1.15, 0.4, 1.5, 0.82), (-1.05, -0.3, 1.1, 0.66), (0.4, -1.05, 0.7, 0.46)]:
    p.cyl((x, y, h / 2), r * 0.22, r * 0.16, h, segs=7, shade=C(0xe8e0c8))
    p.uvsphere((x, y, h), r, segs=10, rings=5, scale=(1, 1, 0.55), shade=C(0x8a3ab0, R(0.9, 1.15)))
    for k in range(4):
        a = k * TAU / 4 + R(0, 1)
        g.ball((x + math.cos(a) * r * 0.5, y + math.sin(a) * r * 0.5, h + r * 0.44), r * 0.13)
p.build(); g.build()

# ---------- 7. zombie: a dead tree over three tombstones ----------
p = Part('w_zombie', shade=True)
p.cyl((0, 0, 1.3), 0.36, 0.2, 2.6, segs=7, rot=(0.06, 0.05, 0), shade=C(0x4a4038))
p.cyl((0.55, 0, 2.75), 0.14, 0.05, 1.5, segs=5, rot=(0, 0.9, 0), shade=C(0x4a4038))
p.cyl((-0.6, 0.1, 2.45), 0.13, 0.04, 1.4, segs=5, rot=(0, -1.0, 0.3), shade=C(0x403830))
p.cyl((0.1, 0.4, 3.15), 0.1, 0.03, 1.2, segs=5, rot=(-0.6, 0.1, 0), shade=C(0x403830))
for (x, y, rz, tilt) in [(1.3, -0.5, 0.2, 0.08), (-1.2, -0.6, -0.15, -0.1), (0.2, -1.1, 0.05, 0.04)]:
    p.box((x, y, 0.5), (0.72, 0.2, 1.0), rot=(tilt, 0, rz), bevel=0.08, shade=C(0x8a938c, R(0.9, 1.1)))
p.box((1.3, -0.62, 0.62), (0.4, 0.04, 0.1), rot=(0.08, 0, 0.2), bevel=0.0, shade=C(0x5a625c))
p.box((1.3, -0.62, 0.62), (0.1, 0.04, 0.44), rot=(0.08, 0, 0.2), bevel=0.0, shade=C(0x5a625c))
p.build()

# ---------- 8. void: a floating shard inside two tilted rings ----------
p = Part('w_void', shade=True)
p.cyl((0, 0, 0.2), 1.05, 0.72, 0.4, segs=7, shade=C(0x2a2040))
p.cyl((0, 0, 2.45), 0.55, 0.0, 1.9, segs=4, shade=C(0x4a3478))
p.cyl((0, 0, 1.05), 0.0, 0.55, 0.9, segs=4, shade=C(0x3a2a5e))
for (x, y, z, s) in [(1.0, 0.3, 1.9, 0.5), (-0.9, -0.2, 2.6, 0.4), (0.4, -0.9, 1.3, 0.35)]:
    p.cyl((x, y, z), s * 0.45, 0.0, s, segs=4, rot=(R(-0.5, 0.5), R(-0.5, 0.5), 0), shade=C(0x4a3478))
p.build()
g = Part('w_void_glow')
g.torus((0, 0, 1.55), 1.05, 0.05, segs=18, tube=4, rot=(0.3, 0.2, 0))
g.torus((0, 0, 1.65), 0.78, 0.04, segs=16, tube=4, rot=(-0.4, 0.5, 0))
g.ball((0, 0, 1.5), 0.2)
g.build()

# ---------- 9. sand: a small pyramid and an obelisk ----------
p = Part('w_sand', shade=True)
p.cyl((0, 0, 0.9), 2.0, 0.0, 1.8, segs=4, rot=(0, 0, math.pi / 4), shade=C(0xe0b86a))
p.box((2.2, 0.6, 0.15), (0.9, 0.9, 0.3), shade=C(0xcfa860))
p.cyl((2.2, 0.6, 1.9), 0.3, 0.2, 3.2, segs=4, rot=(0, 0, math.pi / 4), shade=C(0xd8b068))
p.cyl((2.2, 0.6, 3.7), 0.2, 0.0, 0.4, segs=4, rot=(0, 0, math.pi / 4), shade=C(0xffd24a))
p.build()

# ---------- 10. crystal: a cluster of prisms on a rock ----------
p, g = Part('w_crystal', shade=True), Part('w_crystal_glow')
p.ball((0, 0, 0.2), 0.95, scale=(1.35, 1.1, 0.4), shade=C(0x6a5a8a))
for i, (x, y, h, r, tx, ty) in enumerate([(0, 0, 3.2, 0.5, 0.0, 0.05), (0.7, 0.1, 2.2, 0.4, 0.05, 0.4), (-0.7, 0.0, 2.5, 0.42, 0.0, -0.4), (0.15, -0.6, 1.6, 0.34, 0.45, 0.1), (-0.2, 0.6, 1.7, 0.34, -0.45, -0.05)]):
    spire(p, x, y, h, r, tx, ty, segs=6, col=C([0xb07aff, 0xd8a0ff, 0x9a6af0, 0xff9ae0, 0xc890ff][i]), z0=0.2)
    g.ball((x, y, 0.45), 0.14)
p.build(); g.build()

# ---------- 11. wind: a windmill ----------
p = Part('w_wind', shade=True)
p.cyl((0, 0, 1.6), 0.95, 0.58, 3.2, segs=8, shade=C(0xe8dcc0))
p.cyl((0, 0, 3.6), 0.8, 0.0, 0.95, segs=8, shade=C(0xb04a3a))
p.cyl((0, -0.72, 2.9), 0.12, 0.12, 0.5, segs=6, rot=(math.pi / 2, 0, 0), shade=C(0x5a4030))
for k in range(4):
    a = k * TAU / 4 + 0.4
    p.box((math.cos(a) * 1.15, -0.9, 2.9 + math.sin(a) * 1.15), (2.1, 0.05, 0.44), rot=(0, -a, 0), bevel=0.0, shade=C(0xf4ecd8))
p.box((0, -0.92, 0.5), (0.5, 0.1, 1.0), bevel=0.02, shade=C(0x6a4a30))
p.build()

# ---------- 12. iron: a forge with a chimney and a gear ----------
p = Part('w_iron', shade=True)
p.box((0, 0, 0.6), (1.8, 1.4, 1.2), bevel=0.06, shade=C(0x4a4a54))
p.cyl((0.45, 0.2, 2.3), 0.36, 0.28, 2.4, segs=8, shade=C(0x3a3a44))
p.torus((0.45, 0.2, 3.4), 0.3, 0.06, segs=10, tube=4, shade=C(0x8a8a94))
p.cyl((-0.5, -0.78, 0.9), 0.55, 0.55, 0.16, segs=12, rot=(math.pi / 2, 0, 0), shade=C(0x9a9aa4))
for k in range(8):
    a = k * TAU / 8
    p.box((-0.5 + math.cos(a) * 0.62, -0.78, 0.9 + math.sin(a) * 0.62), (0.2, 0.16, 0.2), rot=(0, -a, 0), bevel=0.0, shade=C(0x9a9aa4))
p.build()
g = Part('w_iron_glow')
g.box((0.35, -0.71, 0.45), (0.7, 0.04, 0.5), bevel=0.0)
g.cyl((0.45, 0.2, 3.52), 0.24, 0.24, 0.04, segs=8)
g.build()

# ---------- 13. light: a marble arch around a halo ----------
p = Part('w_light', shade=True)
for sx in (-1, 1):
    p.box((sx * 0.9, 0, 0.12), (0.7, 0.7, 0.24), shade=C(0xf0e6cc))
    p.cyl((sx * 0.9, 0, 1.7), 0.26, 0.22, 3.0, segs=10, shade=C(0xfff8e8))
    p.box((sx * 0.9, 0, 3.3), (0.66, 0.66, 0.2), shade=C(0xf0e6cc))
p.box((0, 0, 3.6), (2.7, 0.72, 0.4), bevel=0.05, shade=C(0xfff4dc))
p.box((0, 0, 3.86), (2.3, 0.5, 0.12), bevel=0.02, shade=C(0xffd24a))
p.build()
g = Part('w_light_glow')
g.torus((0, 0, 2.3), 0.55, 0.07, segs=18, tube=5, rot=(math.pi / 2, 0, 0))
g.ball((0, 0, 2.3), 0.16)
g.build()

# ---------- 14. shadow: thorn spires with eyes ----------
p = Part('w_shadow', shade=True)
for (x, y, h, r, tx, ty) in [(0, 0, 4.1, 0.62, 0.04, -0.06), (0.85, 0.3, 2.7, 0.46, 0.08, 0.3), (-0.85, 0.1, 3.1, 0.5, -0.04, -0.3), (0.2, -0.75, 1.7, 0.4, 0.3, 0.08), (-0.4, 0.75, 2.0, 0.4, -0.3, 0.0)]:
    spire(p, x, y, h, r, tx, ty, segs=5, col=C(0x241c3a, R(0.9, 1.4)))
p.build()
g = Part('w_shadow_glow')
for (x, z) in [(0.0, 1.7), (0.95, 1.1), (-0.95, 1.3)]:
    for s in (-1, 1):
        g.ball((x + s * 0.13, -0.42 if x == 0 else -0.2, z), 0.075)
g.build()

# ---------- 15. stone: a cairn of boulders ----------
p = Part('w_stone', shade=True)
z = 0.0
for (r, sx, sy, sz, dx) in [(1.15, 1.2, 1.0, 0.6, 0.0), (0.88, 1.1, 1.0, 0.6, 0.1), (0.64, 1.0, 1.1, 0.65, -0.08), (0.44, 1.1, 1.0, 0.7, 0.05), (0.27, 1.0, 1.0, 0.8, 0.0)]:
    z += r * sz
    p.ball((dx, 0, z), r, scale=(sx, sy, sz), subdiv=1, shade=C(0x9a9088, R(0.85, 1.12)))
    z += r * sz * 0.8
p.ball((1.5, -0.4, 0.3), 0.5, scale=(1.2, 1, 0.7), subdiv=1, shade=C(0x8a8078))
p.ball((-1.4, 0.3, 0.25), 0.42, scale=(1, 1.2, 0.7), subdiv=1, shade=C(0xa39a90))
p.build()

# ---------- 16. ghost: a broken arch and a grave lantern ----------
p = Part('w_ghost', shade=True)
p.box((-0.9, 0, 1.3), (0.5, 0.5, 2.6), rot=(0, 0.04, 0), bevel=0.05, shade=C(0x7a8a88))
p.box((0.9, 0, 0.9), (0.5, 0.5, 1.8), rot=(0, -0.06, 0), bevel=0.05, shade=C(0x70807e))
p.box((-0.4, 0, 2.78), (1.5, 0.5, 0.4), rot=(0, 0.12, 0), bevel=0.05, shade=C(0x869694))
p.box((1.35, -0.5, 0.2), (0.5, 0.4, 0.4), rot=(0.2, 0.3, 0.5), bevel=0.05, shade=C(0x70807e))
p.cyl((0.2, -0.55, 1.0), 0.05, 0.05, 2.0, segs=5, shade=C(0x2a3030))
p.box((0.2, -0.55, 2.38), (0.3, 0.3, 0.06), bevel=0.0, shade=C(0x2a3030))
p.build()
g = Part('w_ghost_glow')
g.ball((0.2, -0.55, 2.15), 0.2)
g.ball((-0.9, 0.0, 3.1), 0.14)
g.ball((1.05, 0.2, 2.15), 0.1)
g.build()

# ---------- 17. gold: a heap of coins under a goblet ----------
p = Part('w_gold', shade=True)
p.cyl((0, 0, 0.35), 1.55, 0.5, 0.7, segs=10, shade=C(0xffc629))
for k in range(7):
    a, h = k * TAU / 7 + R(0, 0.4), R(0.3, 0.9)
    p.cyl((math.cos(a) * 1.25, math.sin(a) * 1.25, h / 2), 0.22, 0.22, h, segs=8, shade=C(0xffd24a, R(0.85, 1.1)))
p.cyl((0, 0, 1.0), 0.2, 0.12, 0.7, segs=8, shade=C(0xe8a818))
p.cyl((0, 0, 1.62), 0.2, 0.62, 0.62, segs=10, shade=C(0xffd24a))
p.ball((0.55, -0.65, 0.52), 0.17, shade=C(0xff3a6a))
p.ball((-0.65, -0.45, 0.44), 0.15, shade=C(0x3ad8ff))
p.build()
g = Part('w_gold_glow')
g.ball((0, 0, 2.15), 0.13)
g.ball((0.9, -0.3, 1.0), 0.07)
g.ball((-0.8, 0.4, 0.9), 0.07)
g.build()

# ---------- 18. clock: a clock tower ----------
p = Part('w_clock', shade=True)
p.box((0, 0, 1.7), (1.3, 1.3, 3.4), bevel=0.05, shade=C(0x6a7a8a))
p.box((0, 0, 3.6), (1.6, 1.6, 0.5), bevel=0.05, shade=C(0x5a6a7a))
p.cyl((0, 0, 4.45), 1.1, 0.0, 1.2, segs=4, rot=(0, 0, math.pi / 4), shade=C(0x3a4a5a))
p.cyl((0, -0.68, 2.6), 0.5, 0.5, 0.06, segs=14, rot=(math.pi / 2, 0, 0), shade=C(0xf4f0e0))
p.box((0, -0.67, 0.55), (0.5, 0.06, 1.1), bevel=0.02, shade=C(0x3a2a20))
p.build()
g = Part('w_clock_glow')
g.box((0, -0.73, 2.76), (0.06, 0.03, 0.36), bevel=0.0)
g.box((0.13, -0.73, 2.6), (0.3, 0.03, 0.05), bevel=0.0)
g.ball((0, -0.73, 2.6), 0.06)
g.build()

export('worlds.glb')
