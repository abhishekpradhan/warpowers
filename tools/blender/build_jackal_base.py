# SPDX-License-Identifier: MIT
"""Jackal base-loop set.

- JAKRIG01: the Rigger — welded half-truck builder (canon: docs/creative.md)
- JAKCS01: the Chop Shop — open-sided vehicle garage

The Bulwark (MERBUL01) and Watchpost (JAKWP01) that this kit once carried are
articulated production assets owned by build_polish.py / support_kit.py.

Run: blender --background --factory-startup --python tools/blender/build_jackal_base.py -- [--data DIR | --scratch DIR]
Outputs: data/Art/W3D and data/Art/Textures. The Rigger bakes at 256px; the
Chop Shop bakes at 512px and tools/optimize_art.py halves it to the shipped
256px atlas.
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _bootstrap import KIT_PALETTE  # noqa: E402
import wp_pipeline  # noqa: E402


def build(name, atlas, tga_name, fn, model_dir, texture_dir, **comp):
    wp_pipeline.reset_scene()
    k = wp_pipeline.Kit(KIT_PALETTE, roughness=0.92)
    fn(k)
    obj = k.join(name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    wp_pipeline.smart_uv(obj, 0.006)
    diff, ao, mask = wp_pipeline.bake_images(obj, atlas)
    tga = os.path.join(texture_dir, tga_name + '.tga')
    wp_pipeline.composite(diff, ao, mask, atlas, tga, **comp)
    wp_pipeline.export_w3d(obj, tga, os.path.join(model_dir, name.lower() + '.w3d'), tga_name)
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


def main():
    model_dir, texture_dir = wp_pipeline.output_dirs()
    build('JAKRIG01', 256, 'wp_rigger', rigger, model_dir, texture_dir,
          seed=51, shade_lo=0.50, shade_hi=0.50, grain=0.03, edge_strength=0.5, edge_radius=1)
    build('JAKCS01', 512, 'wp_jakcs', chopshop, model_dir, texture_dir,
          seed=52, shade_lo=0.50, shade_hi=0.50, grain=0.028, edge_strength=0.5,
          edge_radius=2, lowfreq=0.05)
    print('JACKAL_BASE_SET_OK')


if __name__ == '__main__':
    main()
