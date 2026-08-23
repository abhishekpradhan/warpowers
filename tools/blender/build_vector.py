"""Hero asset: the Meridian Vector MBT, built to the D015 bar.

Fully scripted Blender pipeline (run: blender --background --python build_vector.py):
1. Model real forms — hull from an extruded side profile (sloped glacis,
   stepped rear deck), track units with road wheels, beveled turret with
   mantlet, barrel with muzzle brake, hatch, antenna, exhausts.
2. Smart-UV the joined mesh onto one 256px atlas.
3. Cycles-bake flat palette diffuse + ambient occlusion, composite them
   (plus fine grain) into a painted-style TGA.
4. Export Generals-format W3D via the OpenSAGE plugin.

Outputs: /tmp/hero/mertank01.w3d + /tmp/hero/wp_vector.tga
"""
import math
import os
import sys

import bpy
import bmesh

PLUGIN_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', '..', 'engine', 'references', 'OpenSAGE.BlenderPlugin')
OUT_DIR = '/tmp/hero'
ATLAS = 256

sys.path.insert(0, PLUGIN_REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import io_mesh_w3d  # noqa: E402
io_mesh_w3d.register()
import wp_pipeline  # noqa: E402

os.makedirs(OUT_DIR, exist_ok=True)

# palette (docs/creative.md)
PAL = {
    'STEEL': (0.722, 0.761, 0.800, 1.0),
    'WHITE': (0.910, 0.925, 0.941, 1.0),
    'GOLD': (0.843, 0.706, 0.353, 1.0),
    'GUN': (0.353, 0.376, 0.408, 1.0),
    'TREAD': (0.200, 0.212, 0.231, 1.0),
    'DARK': (0.290, 0.306, 0.333, 1.0),
}

# ---------- scene reset ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
    for item in list(block):
        block.remove(item)

mats = {}
def mat(name):
    if name not in mats:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Base Color'].default_value = PAL[name]
        bsdf.inputs['Roughness'].default_value = 0.85
        mats[name] = m
    return mats[name]

parts = []

def register_part(obj, color):
    obj.data.materials.clear()
    obj.data.materials.append(mat(color))
    parts.append(obj)
    return obj

def profile_prism(name, profile, y0, y1, color):
    """Extrude a closed (x,z) side profile across [y0, y1]."""
    m = bpy.data.meshes.new(name)
    bm = bmesh.new()
    front = [bm.verts.new((x, y0, z)) for x, z in profile]
    back = [bm.verts.new((x, y1, z)) for x, z in profile]
    bm.faces.new(reversed(front))
    bm.faces.new(back)
    n = len(profile)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([front[i], front[j], back[j], back[i]])
    bm.normal_update()
    bm.to_mesh(m)
    bm.free()
    obj = bpy.data.objects.new(name, m)
    bpy.context.collection.objects.link(obj)
    return register_part(obj, color)

def box(name, color, cx, cy, cz, sx, sy, sz, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz))
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        md = o.modifiers.new('b', 'BEVEL')
        md.width = bevel
        md.segments = 1
        bpy.ops.object.modifier_apply(modifier='b')
    return register_part(o, color)

def cyl(name, color, cx, cy, cz, r, depth, axis='Z', verts=10):
    rot = {'Z': (0, 0, 0), 'X': (0, math.pi / 2, 0), 'Y': (math.pi / 2, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth,
                                        location=(cx, cy, cz), rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return register_part(o, color)

# ---------- hull: side profile with sloped glacis and stepped rear deck ----------
hull_profile = [
    (-10.0, 2.2), (-10.4, 4.6), (-9.2, 6.1),   # rear plate + rear deck edge
    (-3.4, 6.6), (2.6, 6.6),                    # flat top deck
    (7.6, 5.9), (10.6, 3.7),                    # glacis slope down to nose
    (10.2, 2.2),                                # nose bottom
]
profile_prism('HULLCORE', hull_profile, -5.0, 5.0, 'STEEL')

# side skirts (thin prisms outboard, shorter)
skirt = [(-9.0, 3.0), (-9.0, 5.2), (8.6, 5.2), (9.6, 3.6), (9.4, 3.0)]
profile_prism('SKIRTL', skirt, -6.1, -4.9, 'DARK')
profile_prism('SKIRTR', skirt, 4.9, 6.1, 'DARK')

# ---------- tracks: runs + road wheels ----------
for side, yc in (('L', -5.6), ('R', 5.6)):
    box(f'TRACK{side}', 'TREAD', -0.2, yc, 1.7, 20.4, 2.6, 2.6)
    for i in range(5):
        cyl(f'WHEEL{side}{i}', 'DARK', -7.2 + i * 3.6, yc, 1.5, 1.35, 2.9, axis='Y', verts=10)

# ---------- turret ----------
box('TURRET', 'WHITE', -1.2, 0, 7.9, 8.6, 7.0, 2.6, bevel=0.55)
box('MANTLET', 'STEEL', 3.4, 0, 7.9, 1.6, 3.0, 2.0, bevel=0.3)
cyl('BARREL', 'GUN', 9.6, 0, 7.9, 0.55, 11.0, axis='X', verts=10)
cyl('BRAKE', 'GUN', 14.4, 0, 7.9, 0.85, 1.6, axis='X', verts=10)
cyl('HATCH', 'STEEL', -2.8, -1.6, 9.35, 1.15, 0.5, axis='Z', verts=12)
box('CANOPY', 'GOLD', -2.4, 1.5, 9.3, 2.4, 2.2, 0.55, bevel=0.18)
cyl('ANTENNA', 'DARK', -4.6, -2.6, 10.6, 0.10, 2.8, axis='Z', verts=6)

# ---------- rear details ----------
cyl('EXH1', 'DARK', -10.2, -2.6, 5.2, 0.5, 1.6, axis='X', verts=8)
cyl('EXH2', 'DARK', -10.2, 2.6, 5.2, 0.5, 1.6, axis='X', verts=8)
box('LIGHTL', 'GOLD', 10.1, -3.4, 4.6, 0.5, 1.0, 0.6)
box('LIGHTR', 'GOLD', 10.1, 3.4, 4.6, 0.5, 1.0, 0.6)

# ---------- join ----------
bpy.ops.object.select_all(action='DESELECT')
for p in parts:
    p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
tank = bpy.context.active_object
tank.name = 'VECTOR'
tank.data.name = 'VECTOR'
tris = sum(len(p.vertices) - 2 for p in tank.data.polygons)
print('TRIS:', tris)

# ---------- UV ----------
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.0, island_margin=0.012)
bpy.ops.object.mode_set(mode='OBJECT')

# ---------- bake + composite + export (shared pipeline) ----------
diff, ao, mask = wp_pipeline.bake_images(tank, ATLAS)
tga = os.path.join(OUT_DIR, 'wp_vector.tga')
wp_pipeline.composite(diff, ao, mask, ATLAS, tga, seed=5,
                      grain=0.022, edge_strength=0.55, edge_radius=1)
print('TEXTURE_OK')
wp_pipeline.export_w3d(tank, tga, os.path.join(OUT_DIR, 'mertank01.w3d'), 'wp_vector')
print('HERO_EXPORT_OK')
