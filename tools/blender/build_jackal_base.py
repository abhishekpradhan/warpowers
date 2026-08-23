"""Jackal base-loop set + both faction defenses.

- JAKRIG01: the Rigger — welded half-truck builder (canon: docs/creative.md)
- JAKCS01: the Chop Shop — open-sided vehicle garage
- MERBUL01: the Bulwark — Meridian turret (white drum, steel gun)
- JAKWP01: the Watchpost — Jackal gun tower

Run: blender --background --python build_jackal_base.py
"""
import os
import sys

import bpy

PLUGIN_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', '..', 'engine', 'references', 'OpenSAGE.BlenderPlugin')
OUT_DIR = '/tmp/hero'

sys.path.insert(0, PLUGIN_REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import io_mesh_w3d  # noqa: E402
io_mesh_w3d.register()
import wp_pipeline  # noqa: E402

os.makedirs(OUT_DIR, exist_ok=True)

PAL = {
    'STEEL': (0.722, 0.761, 0.800, 1.0),
    'WHITE': (0.910, 0.925, 0.941, 1.0),
    'GOLD': (0.843, 0.706, 0.353, 1.0),
    'GUN': (0.353, 0.376, 0.408, 1.0),
    'DARK': (0.290, 0.306, 0.333, 1.0),
    'TREAD': (0.200, 0.212, 0.231, 1.0),
    'GLASS': (0.18, 0.24, 0.30, 1.0),
    'SAND': (0.788, 0.690, 0.541, 1.0),
    'RUST': (0.541, 0.353, 0.235, 1.0),
    'OXIDE': (0.435, 0.561, 0.353, 1.0),
    'GRAPHITE': (0.290, 0.306, 0.333, 1.0),
    'CHARCOAL': (0.180, 0.192, 0.220, 1.0),
}


def build(name, atlas, tga_name, fn, **comp):
    wp_pipeline.reset_scene()
    k = wp_pipeline.Kit(PAL, roughness=0.92)
    fn(k)
    obj = k.join(name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    wp_pipeline.smart_uv(obj, 0.006)
    diff, ao, mask = wp_pipeline.bake_images(obj, atlas)
    tga = os.path.join(OUT_DIR, tga_name + '.tga')
    wp_pipeline.composite(diff, ao, mask, atlas, tga, **comp)
    wp_pipeline.export_w3d(obj, tga, os.path.join(OUT_DIR, name.lower() + '.w3d'), tga_name)
    print(name + '_EXPORT_OK')


# ---------- Rigger: welded half-truck with crane ----------
def rigger(k):
    k.box('BED', 'RUST', -2.0, 0, 3.4, 9.0, 7.0, 1.6)
    k.box('CAB', 'SAND', 5.0, 0, 4.6, 5.0, 6.2, 4.2, bevel=0.4)
    k.box('GLASS', 'GLASS', 7.2, 0, 5.4, 0.8, 4.8, 1.6)
    k.box('GRILLE', 'CHARCOAL', 7.8, 0, 3.2, 0.6, 4.6, 1.4)
    for side, yc in (('L', -3.2), ('R', 3.2)):
        k.box(f'TRACK{side}', 'TREAD', -2.2, yc, 1.6, 9.4, 1.8, 2.4)
        k.cyl(f'WHEELF{side}', 'CHARCOAL', 5.4, yc, 1.7, 1.7, 1.8, axis='Y', verts=10)
    # crane arm + welding rig on the bed
    k.box('CRANEBASE', 'GRAPHITE', -4.5, 1.6, 4.8, 2.2, 2.2, 1.6)
    k.box('CRANEARM', 'GUN', -2.0, 1.6, 6.6, 7.0, 0.9, 0.9, rot=(0, -0.18, 0))
    k.box('HOOK', 'GOLD', 1.4, 1.6, 5.6, 0.6, 0.6, 1.2)
    k.box('TANKS', 'OXIDE', -4.6, -2.0, 4.6, 2.4, 2.2, 1.8, bevel=0.3)
    k.cyl('STACK', 'CHARCOAL', 2.6, -2.8, 6.2, 0.5, 2.6, verts=8)


# ---------- Chop Shop: open-sided garage with hoist ----------
def chopshop(k):
    k.box('SLAB', 'GRAPHITE', 0, 0, 1.0, 44, 36, 2.0, bevel=0.6)
    # four corner posts + big roof
    for i, (px, py) in enumerate(((-16, -12), (16, -12), (-16, 12), (16, 12))):
        k.box(f'POST{i}', 'RUST', px, py, 8.0, 2.2, 2.2, 12)
    k.box('ROOF', 'SAND', 0, 0, 15.0, 40, 30, 1.6, rot=(0, 0.03, 0))
    k.box('ROOFRIDGE', 'RUST', 0, 0, 16.2, 40, 3.0, 0.8)
    # back wall + side wall (open front and one side)
    k.box('BACK', 'SAND', 0, 14.2, 8.0, 38, 1.6, 11)
    k.box('SIDE', 'SAND', -18.4, 0, 8.0, 1.6, 28, 11)
    k.box('SIDERIB', 'RUST', -18.5, 0, 8.0, 0.8, 26, 9)
    # hoist gantry inside
    k.box('GANTRY', 'GUN', 0, 2, 12.6, 26, 1.6, 1.2)
    k.box('TROLLEY', 'GOLD', -4, 2, 11.4, 2.6, 2.2, 1.2)
    k.cyl('CHAIN', 'CHARCOAL', -4, 2, 9.9, 0.18, 2.2, verts=6)
    # clutter: engine block, tire stack, barrels
    k.box('BLOCK', 'CHARCOAL', 8, -6, 3.6, 4.5, 3.5, 3.2, bevel=0.3)
    for i in range(3):
        k.cyl(f'TIRE{i}', 'TREAD', -10, -8, 2.6 + i * 1.1, 2.2, 1.0, verts=12)
    k.cyl('BARREL1', 'OXIDE', 13, 8, 3.7, 1.3, 3.4, verts=10)
    k.cyl('BARREL2', 'RUST', 15.5, 6.5, 3.7, 1.3, 3.4, verts=10)
    k.box('SIGN', 'OXIDE', 0, -14.5, 13.0, 10, 0.5, 3.0, rot=(0, 0, 0.04))


# ---------- Bulwark: Meridian turret ----------
def bulwark(k):
    k.box('PAD', 'DARK', 0, 0, 0.9, 16, 16, 1.8, bevel=0.5)
    k.cyl('DRUM', 'WHITE', 0, 0, 4.4, 6.2, 5.2, verts=12)
    k.cyl('TRIM', 'GOLD', 0, 0, 7.2, 6.4, 0.8, verts=12)
    k.box('HEAD', 'STEEL', 0, 0, 9.2, 7.5, 6.5, 3.4, bevel=0.5)
    k.cyl('BARREL', 'GUN', 6.4, 0, 9.2, 0.55, 8.0, axis='X', verts=10)
    k.cyl('BRAKE', 'GUN', 10.0, 0, 9.2, 0.8, 1.2, axis='X', verts=10)
    k.box('SENSOR', 'GLASS', 2.4, 2.6, 11.2, 1.6, 1.4, 0.9)
    k.cyl('ANT', 'DARK', -2.6, -2.4, 11.8, 0.12, 2.4, verts=6)


# ---------- Watchpost: Jackal gun tower ----------
def watchpost(k):
    k.box('PAD', 'CHARCOAL', 0, 0, 0.8, 14, 14, 1.6, bevel=0.4)
    for i, (lx, ly) in enumerate(((-3.4, -3.4), (3.4, -3.4), (-3.4, 3.4), (3.4, 3.4))):
        k.box(f'LEG{i}', 'GRAPHITE', lx, ly, 6.5, 1.2, 1.2, 11)
    k.box('BRACE1', 'GRAPHITE', 0, -3.5, 5.5, 6.8, 0.5, 0.8)
    k.box('BRACE2', 'GRAPHITE', -3.5, 0, 8.5, 0.5, 6.8, 0.8)
    k.box('DECK', 'SAND', 0, 0, 12.6, 10.5, 10.5, 1.2)
    for nm, dx, dy, sx, sy in (('N', 0, 4.8, 10.5, 0.7), ('S', 0, -4.8, 10.5, 0.7),
                               ('E', 4.8, 0, 0.7, 9.0), ('W', -4.8, 0, 0.7, 9.0)):
        k.box(f'WALL{nm}', 'RUST', dx, dy, 14.4, sx, sy, 2.4)
    k.box('GUNMOUNT', 'GUN', 0, 0, 15.4, 2.4, 2.4, 1.4)
    k.cyl('GUN1', 'CHARCOAL', 3.2, 0.7, 15.7, 0.32, 5.0, axis='X', verts=8)
    k.cyl('GUN2', 'CHARCOAL', 3.2, -0.7, 15.7, 0.32, 5.0, axis='X', verts=8)
    k.box('TARP', 'OXIDE', -2.5, 2.5, 16.2, 4.5, 3.5, 0.6, rot=(0.05, -0.06, 0.1))


build('JAKRIG01', 256, 'wp_rigger', rigger,
      seed=51, shade_lo=0.50, shade_hi=0.50, grain=0.03, edge_strength=0.5, edge_radius=1)
build('JAKCS01', 512, 'wp_jakcs', chopshop,
      seed=52, shade_lo=0.50, shade_hi=0.50, grain=0.028, edge_strength=0.5,
      edge_radius=2, lowfreq=0.05)
build('MERBUL01', 256, 'wp_bulwark', bulwark,
      seed=53, grain=0.018, edge_strength=0.5, edge_radius=1)
build('JAKWP01', 256, 'wp_watchpost', watchpost,
      seed=54, shade_lo=0.50, shade_hi=0.50, grain=0.028, edge_strength=0.5, edge_radius=1)
print('JACKAL_BASE_SET_OK')
