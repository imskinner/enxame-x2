# Generates assets/props.glb: lanterns, trackside props (fence, barrel, crate, banner), gate pillars and the
# player's cannon. Run: blender --background --factory-startup --python tools/blender/props.py
# One object per game material; the game maps object names to its own materials (see index.html, dressProps).
# Blender axes: Z up, -Y toward the camera, +Y toward the enemy fort (the cannon fires along +Y).
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import Part, reset, export

reset(3)
TAU = math.pi * 2

# ---------- Lantern post (glow center at z 2.75, where the game puts the halo) ----------
iron = Part('lantern_iron')
iron.box((0, 0, 0.1), (0.38, 0.38, 0.2), bevel=0.04)
iron.cyl((0, 0, 0.32), 0.14, 0.09, 0.24, segs=8)
iron.cyl((0, 0, 1.4), 0.075, 0.06, 2.0, segs=8)
iron.cyl((0, 0, 0.95), 0.1, 0.1, 0.08, segs=8)
iron.cyl((0, 0, 2.42), 0.1, 0.16, 0.12, segs=8)
iron.box((0, 0, 2.5), (0.42, 0.42, 0.05), bevel=0.015)
for sx in (-1, 1):
    for sy in (-1, 1):
        iron.box((sx * 0.17, sy * 0.17, 2.77), (0.045, 0.045, 0.5), bevel=0.0)
iron.box((0, 0, 3.03), (0.44, 0.44, 0.05), bevel=0.015)
iron.cyl((0, 0, 3.17), 0.33, 0.04, 0.24, segs=4, rot=(0, 0, math.pi / 4))
iron.ball((0, 0, 3.34), 0.07)
iron.torus((0, 0, 3.42), 0.07, 0.018, segs=10, tube=4, rot=(math.pi / 2, 0, 0))
iron.build()
Part('lantern_glow').box((0, 0, 2.77), (0.28, 0.28, 0.46), bevel=0.0).build()

# ---------- Fence segment: 3 units long along Y ----------
fence = Part('fence_wood', shade=True)
for y in (-1.45, 1.45):
    fence.box((0, y, 0.55), (0.17, 0.17, 1.1), bevel=0.025)
    fence.cyl((0, y, 1.17), 0.12, 0.0, 0.16, segs=4, rot=(0, 0, math.pi / 4))
for z, tilt in ((0.45, 0.015), (0.86, -0.02)):
    fence.box((0.0, 0, z), (0.07, 3.05, 0.15), rot=(tilt, 0, 0), bevel=0.02)
fence.build()

# ---------- Barrel ----------
wood = Part('keg_wood', shade=True)
prof = [(0.0, 0.34), (0.2, 0.41), (0.45, 0.45), (0.7, 0.41), (0.9, 0.34)]
for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
    wood.cyl((0, 0, (z0 + z1) / 2), r0, r1, z1 - z0, segs=12, caps=(z0 == 0 or z1 == 0.9))
wood.cyl((0, 0, 0.9), 0.31, 0.31, 0.02, segs=12)
wood.build()
band = Part('keg_iron')
for z, R in ((0.12, 0.385), (0.78, 0.385), (0.4, 0.45), (0.5, 0.45)):
    band.torus((0, 0, z), R, 0.022, segs=14, tube=4)
band.build()

# ---------- Crate ----------
crate = Part('crate_wood', shade=True)
crate.box((0, 0, 0.4), (0.76, 0.76, 0.76), bevel=0.02, shade=0.95)
for ax in range(3):  # frame boards on every edge
    for a in (-1, 1):
        for b in (-1, 1):
            c = [0, 0, 0.4]; size = [0.12, 0.12, 0.12]
            idx = [i for i in range(3) if i != ax]
            c[idx[0]] += a * 0.36; c[idx[1]] += b * 0.36; size[ax] = 0.82
            crate.box(tuple(c), tuple(size), bevel=0.02, shade=0.8)
crate.box((0, -0.385, 0.4), (0.1, 0.03, 0.95), rot=(0, math.pi / 4, 0), bevel=0.0, shade=0.82)
crate.build()

# ---------- Banner: pole + crossbar (wood) and cloth with a swallowtail (tinted by the game) ----------
pole = Part('banner_pole')
pole.cyl((0, 0, 2.1), 0.07, 0.05, 4.2, segs=8)
pole.box((0, 0, 3.95), (1.25, 0.07, 0.07), bevel=0.01)
pole.ball((0, 0, 4.28), 0.11, subdiv=1)
for s in (-1, 1): pole.ball((s * 0.64, 0, 3.95), 0.06)
pole.build()
cloth = Part('banner_cloth', shade=True)
W, H, NX, NZ = 1.0, 1.9, 6, 10
bm = cloth.bm
grid = []
for j in range(NZ + 1):
    row = []
    for i in range(NX + 1):
        u, v = i / NX, j / NZ
        x = (u - 0.5) * W
        z = 3.9 - v * H
        if v > 0.82:  # swallowtail notch
            z += (1 - abs(u - 0.5) * 2) * (v - 0.82) / 0.18 * 0.38
        y = math.sin(u * 3.1 + v * 2.0) * 0.06 - 0.06
        row.append(bm.verts.new((x, y, z)))
    grid.append(row)
for j in range(NZ):
    for i in range(NX):
        f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
        v = j / NZ
        s = 0.62 if (v < 0.08 or i in (0, NX - 1)) else (1.0 if abs(v - 0.42) > 0.12 else 0.75)  # trim + middle stripe
        for l in f.loops: l[cloth.col] = (s, s, s, 1.0)
cloth.build()

# ---------- Gate pillar (white shaft) and plinth (dark) ----------
col = Part('gate_pillar')
fl = 14
ring_r = [0.24 if i % 2 else 0.2 for i in range(fl)]
col.cyl((0, 0, 1.75), 0.24, 0.22, 2.6, segs=fl)
for v in col.bm.verts:  # fluting: pull every other column of vertices inward
    a = math.atan2(v.co.y, v.co.x)
    k = round(a / TAU * fl) % fl
    if k % 2: v.co.x *= 0.86; v.co.y *= 0.86
col.cyl((0, 0, 0.5), 0.32, 0.27, 0.1, segs=16)
col.torus((0, 0, 0.56), 0.26, 0.04, segs=16, tube=5)
col.torus((0, 0, 2.98), 0.24, 0.035, segs=16, tube=5)
col.cyl((0, 0, 3.15), 0.24, 0.36, 0.2, segs=16)
col.box((0, 0, 3.3), (0.74, 0.74, 0.1), bevel=0.02)
col.build()
base = Part('gate_base')
base.box((0, 0, 0.13), (0.86, 0.86, 0.26), bevel=0.04)
base.box((0, 0, 0.35), (0.66, 0.66, 0.2), bevel=0.03)
base.build()

# ---------- Player cannon: turret base, wheel (axis Y), barrel (fires along +Y, origin at the pivot) ----------
dark, gold, steel, blue, core = Part('cannon_dark'), Part('cannon_gold'), Part('cannon_steel'), Part('cannon_blue'), Part('cannon_core')
dark.cyl((0, 0, 0.28), 1.8, 1.55, 0.55, segs=8, bevel=0.05)
for i in range(8):  # armor skirts between the rivets
    a = (i + 0.5) / 8 * TAU
    dark.box((math.cos(a) * 1.72, math.sin(a) * 1.72, 0.26), (0.18, 0.9, 0.42), rot=(0, 0, a), bevel=0.03)
gold.torus((0, 0, 0.57), 1.6, 0.07, segs=8, tube=5, rot=(0, 0, math.pi / 8))
for i in range(12):
    a = i / 12 * TAU
    steel.ball((math.cos(a) * 1.36, math.sin(a) * 1.36, 0.6), 0.075)
steel.cyl((0, 0, 0.66), 1.2, 1.24, 0.2, segs=24, bevel=0.03)
for s in (-1, 1):  # exhaust stacks at the back
    steel.cyl((s * 0.55, -0.85, 1.12), 0.17, 0.13, 0.72, segs=10, rot=(-0.45, 0, 0))
    steel.torus((s * 0.55, -1.0, 1.42), 0.15, 0.03, segs=10, tube=4, rot=(-0.45, 0, 0))
steel.cyl((-1.05, -0.75, 1.55), 0.035, 0.035, 1.9, segs=6)
steel.ball((-1.05, -0.75, 2.52), 0.07)
# dome: upper hemisphere with armor ribs
b = blue.bm
blue.uvsphere((0, 0, 0.72), 1.08, segs=24, rings=12)
import bmesh
bmesh.ops.delete(b, geom=[v for v in b.verts if v.co.z < 0.71], context='VERTS')
for i in range(8):
    a = i / 8 * TAU
    gold.box((math.cos(a) * 0.78, math.sin(a) * 0.78, 1.18), (0.5, 0.08, 0.06), rot=(0, -0.75, a), bevel=0.0)
core.torus((0, 0, 0.77), 1.1, 0.075, segs=36, tube=5)
for p in (dark, gold, steel, blue, core): p.build()

wd, wg, ws = Part('wheel_dark'), Part('wheel_gold'), Part('wheel_steel')
wd.torus((0, 0, 0), 0.46, 0.15, segs=22, tube=8, rot=(math.pi / 2, 0, 0))
for i in range(12):  # tread lugs
    a = i / 12 * TAU
    wd.box((math.cos(a) * 0.6, 0, math.sin(a) * 0.6), (0.08, 0.26, 0.12), rot=(0, -a, 0), bevel=0.0)
wg.cyl((0, 0, 0), 0.17, 0.17, 0.34, segs=12, rot=(math.pi / 2, 0, 0), bevel=0.02)
wg.cyl((0, 0, 0), 0.1, 0.06, 0.46, segs=8, rot=(math.pi / 2, 0, 0))
for i in range(5):
    ws.box((0, 0, 0), (0.07, 0.07, 0.8), rot=(0, i / 5 * math.pi, 0), bevel=0.0)
for p in (wd, wg, ws): p.build()

bb, bd, bgold, bc, bk = Part('barrel_blue'), Part('barrel_dark'), Part('barrel_gold'), Part('barrel_core'), Part('barrel_black')
R = (-math.pi / 2, 0, 0)  # cone axis Z -> +Y; radius1 sits at the back
bb.uvsphere((0, -0.15, 0), 0.62, segs=18, rings=10)
bb.cyl((0, 1.05, 0), 0.56, 0.46, 2.5, segs=20, rot=R)
bgold.ball((0, -0.82, 0), 0.16, subdiv=2)
bgold.cyl((0, -0.7, 0), 0.08, 0.12, 0.2, segs=8, rot=R)
for y in (0.45, 1.35):
    bgold.torus((0, y, 0), 0.5, 0.075, segs=22, tube=6, rot=(math.pi / 2, 0, 0))
bgold.torus((0, 2.55, 0), 0.62, 0.095, segs=24, tube=6, rot=(math.pi / 2, 0, 0))
bgold.torus((0, 2.05, 0), 0.5, 0.05, segs=22, tube=5, rot=(math.pi / 2, 0, 0))
bd.cyl((0, 2.3, 0), 0.48, 0.66, 0.5, segs=20, rot=R, bevel=0.02)
for s in (-1, 1):
    bd.box((s * 0.5, 0.9, 0), (0.12, 1.3, 0.34), bevel=0.03)
    bc.box((s * 0.575, 0.9, 0), (0.04, 0.9, 0.12), bevel=0.0)
    bd.cyl((s * 0.62, -0.1, 0), 0.16, 0.16, 0.2, segs=10, rot=(0, math.pi / 2, 0))  # trunnions
bk.cyl((0, 2.56, 0), 0.47, 0.47, 0.02, segs=20, rot=R)
for p in (bb, bd, bgold, bc, bk): p.build()

export('props.glb')
