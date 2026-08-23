"""Pack conversions, batch 2: three Quaternius tanks -> roster units.

- Tank2 -> WP  Outrider  (Meridian recon: small, fast)
- Tank  -> WPJ Vulture   (Jackal gun truck: the faction icon)
- Tank4 -> WP  Zenith    (Meridian artillery: big, long gun)

Same recipe as the Mongrel conversion (fresh materials, luminance->ramp
retint, shared bake pipeline). Run: blender --background --python convert_pack_units.py
"""
import os
import sys

import bpy
import mathutils

PLUGIN_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', '..', 'engine', 'references', 'OpenSAGE.BlenderPlugin')
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'refs', 'quaternius-tanks')
OUT_DIR = '/tmp/hero'

sys.path.insert(0, PLUGIN_REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import io_mesh_w3d  # noqa: E402
io_mesh_w3d.register()
import wp_pipeline  # noqa: E402

os.makedirs(OUT_DIR, exist_ok=True)

MERIDIAN_RAMP = [
    (0.200, 0.212, 0.231, 1.0),   # TREAD
    (0.353, 0.376, 0.408, 1.0),   # GUN
    (0.843, 0.706, 0.353, 1.0),   # GOLD accent (mid slot)
    (0.722, 0.761, 0.800, 1.0),   # STEEL
    (0.910, 0.925, 0.941, 1.0),   # WHITE
]
JACKAL_RAMP = [
    (0.200, 0.212, 0.231, 1.0),   # TREAD
    (0.353, 0.376, 0.408, 1.0),   # GUN
    (0.541, 0.353, 0.235, 1.0),   # RUST
    (0.420, 0.450, 0.380, 1.0),   # muted olive
    (0.788, 0.690, 0.541, 1.0),   # SAND
]

UNITS = [
    dict(fbx='Tank2.fbx', name='MEROUT01', tga='wp_outrider', length=15.0,
         ramp=MERIDIAN_RAMP, seed=31, grain=0.02, shade_lo=0.52, shade_hi=0.48,
         edge=0.55),
    dict(fbx='Tank.fbx', name='JAKVUL01', tga='wp_vulture', length=16.0,
         ramp=JACKAL_RAMP, seed=37, grain=0.03, shade_lo=0.50, shade_hi=0.50,
         edge=0.50),
    dict(fbx='Tank4.fbx', name='MERZEN01', tga='wp_zenith', length=24.0,
         ramp=MERIDIAN_RAMP, seed=41, grain=0.02, shade_lo=0.52, shade_hi=0.48,
         edge=0.55),
]


def luminance(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def convert(cfg):
    wp_pipeline.reset_scene()
    for block in (bpy.data.armatures, bpy.data.actions):
        for item in list(block):
            block.remove(item)
    bpy.ops.import_scene.fbx(filepath=os.path.join(REFS, cfg['fbx']))

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
    if len(meshes) > 1:
        bpy.ops.object.join()
    unit = bpy.context.active_object
    unit.name = cfg['name']
    unit.data.name = cfg['name']
    unit.vertex_groups.clear()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    def bounds():
        bb = [unit.matrix_world @ mathutils.Vector(c) for c in unit.bound_box]
        mn = mathutils.Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
        mx = mathutils.Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
        return mn, mx

    mn, mx = bounds()
    size = mx - mn
    if size.y > size.x:
        unit.rotation_euler = (0, 0, 3.14159265 / 2)
        bpy.ops.object.transform_apply(rotation=True)
        mn, mx = bounds()
        size = mx - mn
    scale = cfg['length'] / size.x
    unit.scale = (scale, scale, scale)
    bpy.ops.object.transform_apply(scale=True)
    mn, mx = bounds()
    ctr = (mn + mx) / 2
    unit.location = (-ctr.x, -ctr.y, -mn.z)
    bpy.ops.object.transform_apply(location=True)

    # fresh materials on the ramp (imported datablocks bake black headless)
    src = []
    for m in unit.data.materials:
        b = m.node_tree.nodes.get('Principled BSDF')
        src.append(tuple(b.inputs['Base Color'].default_value) if b else (0.5, 0.5, 0.5, 1))
    order = sorted(range(len(src)), key=lambda i: luminance(src[i]))
    n = max(1, len(order) - 1)
    ramp = cfg['ramp']
    slot = {}
    for rank, idx in enumerate(order):
        slot[idx] = ramp[min(len(ramp) - 1, round(rank / n * (len(ramp) - 1)))]
    fresh = []
    for idx in range(len(unit.data.materials)):
        m = bpy.data.materials.new(f'{cfg["name"]}_{idx}')
        m.use_nodes = True
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = slot[idx]
        b.inputs['Roughness'].default_value = 0.9
        b.inputs['Metallic'].default_value = 0.0
        fresh.append(m)
    for idx, m in enumerate(fresh):
        unit.data.materials[idx] = m

    if wp_pipeline.maybe_portrait_exit(unit, cfg['tga'].replace('wp_', '')):
        return
    wp_pipeline.smart_uv(unit, 0.002)
    diff, ao, mask = wp_pipeline.bake_images(unit, 512)
    tga = os.path.join(OUT_DIR, cfg['tga'] + '.tga')
    wp_pipeline.composite(diff, ao, mask, 512, tga, seed=cfg['seed'],
                          shade_lo=cfg['shade_lo'], shade_hi=cfg['shade_hi'],
                          grain=cfg['grain'], edge_strength=cfg['edge'],
                          edge_radius=2)
    wp_pipeline.export_w3d(unit, tga,
                           os.path.join(OUT_DIR, cfg['name'].lower() + '.w3d'),
                           cfg['tga'])
    print(cfg['name'] + '_EXPORT_OK')


for cfg in UNITS:
    convert(cfg)
print('PACK_BATCH2_OK')
