"""Meridian base-loop set: Surveyor (dozer), Power Station, Vehicle Works.

Three models through the shared pipeline in one headless run.
Run: blender --background --python build_meridian_base.py
Outputs: /tmp/hero/{mersuv01,merpp01,merwf01}.w3d + wp_{surveyor,merpp,merwf}.tga
"""
import os
import sys

import bpy

PLUGIN_REPO = '/Users/abhishekpradhan/Projects/cnc-project/engine/references/OpenSAGE.BlenderPlugin'
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
}


def build(name, atlas, tga_name, w3d_name, fn, **comp):
    wp_pipeline.reset_scene()
    k = wp_pipeline.Kit(PAL)
    fn(k)
    obj = k.join(name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    wp_pipeline.smart_uv(obj, 0.006)
    diff, ao, mask = wp_pipeline.bake_images(obj, atlas)
    tga = os.path.join(OUT_DIR, tga_name + '.tga')
    wp_pipeline.composite(diff, ao, mask, atlas, tga, **comp)
    wp_pipeline.export_w3d(obj, tga, os.path.join(OUT_DIR, w3d_name + '.w3d'), tga_name)
    print(name + '_EXPORT_OK')


# ---------- Surveyor: tracked construction vehicle with dozer blade ----------
def surveyor(k):
    k.box('CHASSIS', 'STEEL', 0, 0, 3.4, 12.0, 8.0, 3.2, bevel=0.4)
    for side, yc in (('L', -4.6), ('R', 4.6)):
        k.box(f'TRACK{side}', 'TREAD', 0, yc, 1.8, 13.5, 2.2, 2.8)
    # angled dozer blade up front
    k.prism('BLADE', 'GOLD', [(7.0, 0.6), (8.6, 0.6), (8.2, 4.6), (6.6, 4.2)], -5.2, 5.2)
    k.box('BLADEARM_L', 'GUN', 5.2, -3.4, 2.8, 3.4, 0.7, 0.7)
    k.box('BLADEARM_R', 'GUN', 5.2, 3.4, 2.8, 3.4, 0.7, 0.7)
    # cab with glass strip
    k.box('CAB', 'WHITE', -1.8, 0, 6.6, 6.0, 6.4, 3.4, bevel=0.4)
    k.box('GLASS', 'GLASS', 0.6, 0, 7.0, 1.4, 5.2, 1.8)
    k.box('STRIPE', 'GOLD', -4.6, 0, 6.4, 0.5, 6.0, 0.9)
    # rear equipment: crane arm stub + light
    k.box('RIG', 'GUN', -5.4, 1.8, 6.2, 2.6, 2.0, 1.6, bevel=0.25)
    k.cyl('MAST', 'DARK', -5.0, -2.4, 8.4, 0.14, 3.2, verts=6)
    k.box('LIGHT', 'GOLD', -5.0, -2.4, 10.1, 0.7, 0.7, 0.5)


# ---------- Power Station: hall + twin gold-ringed stacks + yard ----------
def power(k):
    k.box('PLINTH', 'DARK', 0, 0, 1.0, 40, 34, 2.0, bevel=0.6)
    k.box('HALL', 'WHITE', -4, 0, 8.0, 24, 24, 12, bevel=0.5)
    k.box('HALLTRIM', 'GOLD', -4, 0, 13.6, 21, 21, 0.9)
    k.box('CTRL', 'STEEL', -4, -13.6, 4.6, 12, 3.6, 7.0, bevel=0.4)
    k.box('CTRLGLASS', 'GLASS', -4, -15.3, 6.2, 9.0, 0.5, 2.0)
    for i, sx in enumerate((10.5, 15.5)):
        k.cyl(f'STACK{i}', 'STEEL', sx, 5.5, 13.0, 2.6, 18.0, verts=12)
        k.cyl(f'RING{i}', 'GOLD', sx, 5.5, 19.0, 2.85, 1.1, verts=12)
        k.cyl(f'CAP{i}', 'DARK', sx, 5.5, 22.2, 2.2, 0.8, verts=12)
    # transformer yard
    for i, (bx, by) in enumerate(((12, -8), (16, -8), (12, -12.5))):
        k.box(f'XFMR{i}', 'GUN', bx, by, 3.2, 3.0, 3.0, 2.4, bevel=0.3)
        k.cyl(f'COIL{i}', 'DARK', bx, by, 5.3, 0.8, 1.8, verts=8)
    k.box('VENT1', 'GUN', -10, 8, 14.6, 5.0, 4.0, 1.4, bevel=0.3)
    k.box('VENT2', 'GUN', -10, 1, 14.6, 5.0, 4.0, 1.4, bevel=0.3)


# ---------- Vehicle Works: assembly hall, gate, gantry crane ----------
def factory(k):
    k.box('PLINTH', 'DARK', 0, 0, 1.0, 48, 40, 2.0, bevel=0.6)
    k.box('HALL', 'WHITE', 0, 3, 9.5, 34, 28, 15, bevel=0.6)
    k.box('CORNICE', 'GOLD', 0, 3, 16.6, 31, 25, 1.0)
    # gate: recessed dark opening with gold hazard frame, facing -y
    k.box('GATEFRAME', 'GOLD', 0, -11.6, 6.2, 15, 1.4, 10.4)
    k.box('GATE', 'TREAD', 0, -12.0, 5.6, 12.5, 1.2, 9.2)
    # roof: gantry crane rails + trolley + skylight band
    k.box('RAIL_L', 'GUN', -12, 3, 17.8, 1.0, 26, 1.4)
    k.box('RAIL_R', 'GUN', 12, 3, 17.8, 1.0, 26, 1.4)
    k.box('BRIDGE', 'STEEL', 0, 8, 18.4, 25, 2.4, 1.2)
    k.box('TROLLEY', 'GOLD', 4, 8, 19.3, 3.0, 2.8, 0.9)
    k.box('SKYLIGHT', 'GLASS', 0, -1, 17.2, 20, 6, 0.5)
    # side office
    k.box('OFFICE', 'STEEL', 21, -6, 5.4, 8.0, 12.0, 8.8, bevel=0.4)
    k.box('OFFGLASS', 'GLASS', 24.8, -6, 6.4, 0.5, 9.0, 2.0)
    k.box('OFFTRIM', 'GOLD', 21, -6, 10.0, 7.0, 11.0, 0.6)
    # stacks + vents
    k.cyl('STACK', 'GUN', -14, 12, 18.5, 1.3, 6.0, verts=10)
    k.box('VENT', 'GUN', 8, 13, 17.6, 6.0, 3.0, 1.2, bevel=0.3)


build('MERSUV01', 256, 'wp_surveyor', 'mersuv01', surveyor,
      seed=21, grain=0.02, edge_strength=0.5, edge_radius=1)
build('MERPP01', 512, 'wp_merpp', 'merpp01', power,
      seed=22, grain=0.018, edge_strength=0.45, edge_radius=2, lowfreq=0.035)
build('MERWF01', 512, 'wp_merwf', 'merwf01', factory,
      seed=23, grain=0.018, edge_strength=0.45, edge_radius=2, lowfreq=0.035)
print('MERIDIAN_BASE_SET_OK')
