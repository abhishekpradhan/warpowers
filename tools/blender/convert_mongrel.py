"""Pack conversion: Quaternius Tank3 (CC0) -> the Jackal Mongrel.

Import FBX, strip rig/animation, normalize scale+orientation to game units,
retint the flat materials to the Jackal palette, then run the same bake
pipeline as the hero Vector (Smart UV -> diffuse+AO bake -> painted-style
composite) so adopted assets and self-produced assets share one look.

Run: blender --background --python convert_mongrel.py
Outputs: /tmp/hero/jaktank01.w3d + /tmp/hero/wp_mongrel.tga
"""
import os
import sys

import bpy

PLUGIN_REPO = '/Users/abhishekpradhan/Projects/cnc-project/engine/references/OpenSAGE.BlenderPlugin'
SRC_FBX = '/Users/abhishekpradhan/Projects/cnc-project/refs/quaternius-tanks/Tank3.fbx'
OUT_DIR = '/tmp/hero'
ATLAS = 512            # imported meshes carry many more UV islands than the hero builds
TARGET_LENGTH = 21.0   # world units along X (Vector is ~25 with barrel)

sys.path.insert(0, PLUGIN_REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import io_mesh_w3d  # noqa: E402
io_mesh_w3d.register()
import wp_pipeline  # noqa: E402

os.makedirs(OUT_DIR, exist_ok=True)

# Jackal palette (docs/creative.md), ordered dark -> light for luminance mapping
JACKAL_RAMP = [
    (0.200, 0.212, 0.231, 1.0),   # TREAD
    (0.353, 0.376, 0.408, 1.0),   # GUN
    (0.541, 0.353, 0.235, 1.0),   # RUST
    (0.420, 0.450, 0.380, 1.0),   # muted olive (full OXIDE reads neon on thin parts)
    (0.788, 0.690, 0.541, 1.0),   # SAND
]

# ---------- reset & import ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.armatures, bpy.data.actions):
    for item in list(block):
        block.remove(item)

bpy.ops.import_scene.fbx(filepath=SRC_FBX)

# strip animation; keep only mesh objects, freed from any armature
meshes = []
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        o.animation_data_clear()
        for mod in list(o.modifiers):
            if mod.type == 'ARMATURE':
                o.modifiers.remove(mod)
        if o.parent and o.parent.type == 'ARMATURE':
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
        meshes.append(o)
    else:
        bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.object.select_all(action='DESELECT')
for m in meshes:
    m.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
tank = bpy.context.active_object
tank.name = 'MONGREL'
tank.data.name = 'MONGREL'
tank.vertex_groups.clear()   # leftover rig weights would read as skinned
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# ---------- normalize: length along X, grounded at z=0, centered ----------
import mathutils  # noqa: E402
bb = [tank.matrix_world @ mathutils.Vector(c) for c in tank.bound_box]
minv = mathutils.Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
maxv = mathutils.Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
size = maxv - minv
# FBX packs often face -Y or +Y; rotate so the LONG axis is X
if size.y > size.x:
    tank.rotation_euler = (0, 0, 3.14159265 / 2)
    bpy.ops.object.transform_apply(rotation=True)
    bb = [tank.matrix_world @ mathutils.Vector(c) for c in tank.bound_box]
    minv = mathutils.Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    maxv = mathutils.Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    size = maxv - minv
scale = TARGET_LENGTH / size.x
tank.scale = (scale, scale, scale)
bpy.ops.object.transform_apply(scale=True)
bb = [tank.matrix_world @ mathutils.Vector(c) for c in tank.bound_box]
minv = mathutils.Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
maxv = mathutils.Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
ctr = (minv + maxv) / 2
tank.location = (-ctr.x, -ctr.y, -minv.z)
bpy.ops.object.transform_apply(location=True)
print('SIZE:', (maxv - minv))

# ---------- retint: REPLACE imported materials with fresh ones on the ramp ----------
# (imported FBX material datablocks bake black in headless Cycles; fresh
#  materials with the same slot order behave — divergence isolated empirically)
def luminance(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

src_colors = []
for m in tank.data.materials:
    b = m.node_tree.nodes.get('Principled BSDF')
    src_colors.append(tuple(b.inputs['Base Color'].default_value) if b else (0.5, 0.5, 0.5, 1))
order = sorted(range(len(src_colors)), key=lambda i: luminance(src_colors[i]))
slot_color = {}
n = max(1, len(order) - 1)
for rank, idx in enumerate(order):
    ramp_i = min(len(JACKAL_RAMP) - 1, round(rank / n * (len(JACKAL_RAMP) - 1)))
    slot_color[idx] = JACKAL_RAMP[ramp_i]

fresh = []
for idx in range(len(tank.data.materials)):
    m = bpy.data.materials.new(f'JK{idx}')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = slot_color[idx]
    b.inputs['Roughness'].default_value = 0.9
    b.inputs['Metallic'].default_value = 0.0
    fresh.append(m)
for idx, m in enumerate(fresh):
    tank.data.materials[idx] = m
print('MATERIALS:', len(fresh))

# ---------- UV + bake (same recipe as the hero Vector) ----------
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.0, island_margin=0.002)
bpy.ops.object.mode_set(mode='OBJECT')

diff, ao, mask = wp_pipeline.bake_images(tank, ATLAS)
tga = os.path.join(OUT_DIR, 'wp_mongrel.tga')
wp_pipeline.composite(diff, ao, mask, ATLAS, tga, seed=9,
                      shade_lo=0.50, shade_hi=0.50,
                      grain=0.03,   # slightly grubbier than Meridian
                      edge_strength=0.50, edge_radius=2)
print('TEXTURE_OK')

tris = sum(len(p.vertices) - 2 for p in tank.data.polygons)
print('TRIS:', tris)

wp_pipeline.export_w3d(tank, tga, os.path.join(OUT_DIR, 'jaktank01.w3d'), 'wp_mongrel')
print('MONGREL_EXPORT_OK')
