# SPDX-License-Identifier: MIT
"""Hero building: the Jackal Command Post, built to the D015 bar.

Keeps the placeholder's identity tokens — shack + tarp + watchtower + dish —
and grows them into a scavenger compound: bermed perimeter, roofed blockhouse
with rust reinforcement, crate stacks under an oxide tarp, water tank,
lattice watchtower with a crow's nest.

Run: blender --background --factory-startup --python tools/blender/build_jakcp.py -- [--data DIR | --scratch DIR]
Outputs: data/Art/W3D/jakcp01.w3d and data/Art/Textures/wp_jakcp.tga (a 512px
bake; tools/optimize_art.py halves it to the shipped 256px atlas).
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _bootstrap import KIT_PALETTE  # noqa: E402
import wp_pipeline  # noqa: E402

ATLAS = 512


def command_post(k):
    # ---------- ground slab + berm walls (entry gap on -y) ----------
    k.box('SLAB', 'GRAPHITE', 0, 0, 1.1, 40, 36, 2.2, bevel=0.6)
    wall = [(-19, 2.2), (19, 2.2), (16.5, 5.6), (-16.5, 5.6)]
    k.prism('BERM_N', 'SAND', wall, 15.4, 18.0)
    k.prism('BERM_S1', 'SAND', [(-19, 2.2), (-6, 2.2), (-5, 5.4), (-16.5, 5.4)], -18.0, -15.4)
    k.prism('BERM_S2', 'SAND', [(7, 2.2), (19, 2.2), (16.5, 5.4), (8, 5.4)], -18.0, -15.4)
    k.box('BERM_E', 'SAND', 18.2, 0, 3.8, 2.8, 31, 3.2, bevel=0.5)
    k.box('BERM_W', 'SAND', -18.2, 0, 3.8, 2.8, 31, 3.2, bevel=0.5)

    # sandbags at the entry gap
    for i, (bx, by) in enumerate(((-2.5, -16.6), (0.5, -16.9), (3.5, -16.5))):
        k.box(f'BAG{i}', 'SAND', bx, by, 2.9, 2.6, 1.6, 1.3, bevel=0.35)

    # ---------- blockhouse with roof overhang + rust reinforcement ----------
    k.box('HOUSE', 'SAND', -4, 3, 6.7, 22, 16, 9, bevel=0.4)
    k.box('ROOF', 'GRAPHITE', -3.2, 3, 11.6, 25, 19, 1.2, rot=(0, 0, 0.04))
    k.box('RIB1', 'RUST', -14.7, 3, 6.7, 0.9, 15.5, 8.5)
    k.box('RIB2', 'RUST', -4, 10.7, 6.7, 21.5, 0.9, 8.5)
    k.box('DOOR', 'CHARCOAL', -4, -5.2, 4.9, 5.5, 0.8, 5.5)
    k.box('WINDOW', 'CHARCOAL', 3.5, -5.1, 8.0, 4.0, 0.6, 2.0)
    # rooftop clutter: cooler + pipe
    k.box('COOLER', 'GUN', -9, 6, 12.8, 4.0, 3.2, 1.6, bevel=0.25)
    k.cyl('STACK', 'CHARCOAL', 2, 8.5, 13.8, 0.9, 5.0, verts=8)
    k.cyl('STACKBAND', 'RUST', 2, 8.5, 15.2, 1.05, 0.8, verts=8)

    # ---------- crates + oxide tarp ----------
    k.box('CRATE1', 'CHARCOAL', -12, -9, 3.6, 4.6, 3.8, 2.8)
    k.box('CRATE2', 'RUST', -8.5, -10, 3.3, 3.4, 3.0, 2.2, rot=(0, 0, 0.25))
    k.box('CRATE3', 'CHARCOAL', -11, -6.5, 5.6, 3.2, 2.8, 1.6, rot=(0, 0, -0.15))
    k.box('TARP', 'OXIDE', -10.5, -8, 6.9, 9.5, 8.0, 0.9, bevel=0.4, rot=(0.06, -0.08, 0.12))

    # ---------- water tank on legs ----------
    k.cyl('TANK', 'RUST', 12, 10, 6.8, 3.6, 6.0, verts=12)
    k.cyl('TANKCAP', 'CHARCOAL', 12, 10, 10.0, 3.7, 0.5, verts=12)
    for i, (lx, ly) in enumerate(((9.5, 7.6), (14.5, 7.6), (9.5, 12.4), (14.5, 12.4))):
        k.box(f'LEG{i}', 'CHARCOAL', lx, ly, 2.9, 0.8, 0.8, 1.6)

    # ---------- watchtower: legs, platform, nest, roof, mast ----------
    TX, TY = 13, -8
    for i, (lx, ly) in enumerate(((TX - 2.6, TY - 2.6), (TX + 2.6, TY - 2.6),
                                  (TX - 2.6, TY + 2.6), (TX + 2.6, TY + 2.6))):
        k.box(f'TLEG{i}', 'GRAPHITE', lx, ly, 7.7, 1.0, 1.0, 13)
    k.box('TBRACE1', 'GRAPHITE', TX, TY - 2.7, 7.5, 5.6, 0.5, 0.7)
    k.box('TBRACE2', 'GRAPHITE', TX - 2.7, TY, 10.5, 0.5, 5.6, 0.7)
    k.box('TDECK', 'SAND', TX, TY, 14.6, 8.8, 8.8, 1.0)
    for nm, dx, dy, sx, sy in (('NW_N', 0, 4.1, 8.8, 0.6), ('NW_S', 0, -4.1, 8.8, 0.6),
                               ('NW_E', 4.1, 0, 0.6, 7.6), ('NW_W', -4.1, 0, 0.6, 7.6)):
        k.box(f'NEST{nm}', 'SAND', TX + dx, TY + dy, 16.2, sx, sy, 2.2)
    k.box('TROOF', 'RUST', TX + 0.4, TY, 19.3, 10, 10, 0.8, rot=(0, 0.05, 0))
    k.cyl('TPOLE', 'GRAPHITE', TX - 3.5, TY - 3.5, 17.8, 0.35, 4.5, verts=6)
    k.cyl('TMAST', 'GRAPHITE', TX + 3.8, TY + 3.8, 21.8, 0.35, 6.0, verts=6)
    k.box('PENNANT', 'OXIDE', TX + 3.8, TY + 4.9, 24.2, 0.25, 2.0, 1.1)

    # ---------- salvaged dish, propped on the roof ----------
    k.box('DBRACK', 'GUN', 4, 9.5, 12.8, 1.2, 1.2, 1.8)
    k.cyl('DISH', 'GUN', 4.6, 10.1, 14.0, 3.0, 0.7, axis='Z', verts=10,
          rot=(1.05, 0.0, 0.6))


def main():
    model_dir, texture_dir = wp_pipeline.output_dirs()
    wp_pipeline.reset_scene()
    k = wp_pipeline.Kit(KIT_PALETTE, roughness=0.95)
    command_post(k)
    structure = k.join('JAKCP01')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    wp_pipeline.smart_uv(structure, 0.006)
    diff, ao, mask = wp_pipeline.bake_images(structure, ATLAS)
    tga = os.path.join(texture_dir, 'wp_jakcp.tga')
    wp_pipeline.composite(diff, ao, mask, ATLAS, tga, seed=17,
                          shade_lo=0.50, shade_hi=0.50,
                          grain=0.028, edge_strength=0.5, edge_radius=2,
                          lowfreq=0.05)
    print('TEXTURE_OK')
    wp_pipeline.export_w3d(structure, tga, os.path.join(model_dir, 'jakcp01.w3d'), 'wp_jakcp')
    print('JAKCP_EXPORT_OK')


if __name__ == '__main__':
    main()
