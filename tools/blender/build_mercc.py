"""Hero building: the Meridian Command Center, built to the D015 bar.

Keeps the placeholder's identity tokens — terraced white monolith, gold
cornice ring, corner tower with gold-tipped mast — and grows them into real
architecture: chamfered plinth, entry portal, comms dish, vents, landing pad.

Run: blender --background --python build_mercc.py
Outputs: /tmp/hero/mercc01.w3d + /tmp/hero/wp_mercc.tga
"""
import os
import sys

import bpy

PLUGIN_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', '..', 'engine', 'references', 'OpenSAGE.BlenderPlugin')
OUT_DIR = '/tmp/hero'
ATLAS = 512

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
    'GLASS': (0.18, 0.24, 0.30, 1.0),
}

wp_pipeline.reset_scene()
k = wp_pipeline.Kit(PAL)

# ---------- plinth + podium ----------
k.box('PLINTH', 'DARK', 0, 0, 1.25, 46, 46, 2.5, bevel=0.8)
k.box('PODIUM', 'STEEL', 0, 0, 5.5, 40, 40, 6, bevel=0.5)

# entry portal on the front (-y): frame, recessed door, flanking lights
k.box('PORTFRAME', 'STEEL', 0, -20.4, 5.4, 11, 2.0, 7.2, bevel=0.3)
k.box('PORTDOOR', 'GLASS', 0, -21.1, 4.8, 7.4, 1.2, 5.6)
k.box('LIGHTL', 'GOLD', -6.6, -20.9, 7.6, 1.0, 0.6, 1.0)
k.box('LIGHTR', 'GOLD', 6.6, -20.9, 7.6, 1.0, 0.6, 1.0)

# vents + landing pad on the podium roof
k.box('VENTL', 'GUN', -14, 13, 9.6, 6.5, 4.5, 2.2, bevel=0.3)
k.box('VENTR', 'GUN', -14, 5, 9.6, 6.5, 4.5, 2.2, bevel=0.3)
k.box('PAD', 'DARK', 12, 12, 9.0, 13, 14, 1.0)
k.box('PADTRIM', 'GOLD', 12, 12, 9.55, 9.5, 10.5, 0.35)

# ---------- main block with cornice ring ----------
k.box('BLOCK', 'WHITE', 0, -3, 14.5, 30, 30, 12, bevel=0.6)
for nm, x, y, sx, sy in (('CORN_N', 0, 11.6, 27.5, 1.2), ('CORN_S', 0, -17.6, 27.5, 1.2),
                         ('CORN_E', 14.6, -3, 1.2, 25.0), ('CORN_W', -14.6, -3, 1.2, 25.0)):
    k.box(nm, 'GOLD', x, y, 19.9, sx, sy, 1.4)

# glass band near the block top (command deck windows)
k.box('DECKGLASS', 'GLASS', 0, -18.7, 17.5, 22, 0.6, 2.2)

# ---------- clerestory + crown ----------
k.box('CLERE', 'STEEL', 0, -3, 22.0, 23, 23, 3.0, bevel=0.4)
k.box('CROWN', 'WHITE', -2, -5, 25.5, 15, 15, 4.0, bevel=0.5)
k.box('BEACON', 'GOLD', -2, -5, 27.9, 5.5, 5.5, 1.0, bevel=0.2)
k.cyl('ANT1', 'DARK', -6.5, -9.5, 30.0, 0.16, 5.0, verts=6)
k.cyl('ANT2', 'DARK', 2.0, -1.0, 29.4, 0.16, 3.6, verts=6)

# ---------- corner comms tower ----------
k.box('TOWER', 'STEEL', 10, 8, 26.0, 10, 10, 9.0, bevel=0.4)
k.box('TOWERTRIM', 'GOLD', 10, 8, 30.7, 8.2, 8.2, 0.8)
k.cyl('MAST', 'GUN', 10, 8, 34.5, 0.7, 7.0, verts=8)
k.box('TIP', 'GOLD', 10, 8, 38.4, 1.9, 1.9, 1.2)
# dish: tilted disc + bracket on the tower's outboard corner
k.box('BRACKET', 'GUN', 14.2, 12.2, 29.5, 1.4, 1.4, 3.4)
k.cyl('DISH', 'STEEL', 15.6, 13.6, 31.6, 3.4, 0.8, axis='Z', verts=12,
      rot=(0.9, 0.0, -0.78))
k.cyl('FEED', 'GUN', 15.6, 13.6, 32.6, 0.22, 2.6, verts=6, rot=(0.9, 0.0, -0.78))

# ---------- walkway from clerestory to tower ----------
k.box('WALK', 'STEEL', 5, 2, 21.2, 6.0, 2.6, 0.7)

structure = k.join('MERCC01')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

if wp_pipeline.maybe_portrait_exit(structure, 'mercc'):
    raise SystemExit
wp_pipeline.smart_uv(structure, 0.006)
diff, ao, mask = wp_pipeline.bake_images(structure, ATLAS)
tga = os.path.join(OUT_DIR, 'wp_mercc.tga')
wp_pipeline.composite(diff, ao, mask, ATLAS, tga, seed=11,
                      grain=0.018, edge_strength=0.45, edge_radius=2,
                      lowfreq=0.035)
print('TEXTURE_OK')
wp_pipeline.export_w3d(structure, tga, os.path.join(OUT_DIR, 'mercc01.w3d'), 'wp_mercc')
print('MERCC_EXPORT_OK')
