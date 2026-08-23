"""Pipeline spike: headless Blender -> OpenSAGE plugin -> .w3d for the engine.

Builds a deliberately non-trivial test mesh (beveled cube = shapes genw3d
cannot make), UV-unwraps it, assigns an image texture, and exports it as a
Generals-format W3D named MERTANK01 (temporarily replacing the Vector model
so no INI changes are needed to see it in-game).

Run: blender --background --python spike_export.py
"""
import os
import sys

import bpy

PLUGIN_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', '..', 'engine', 'references', 'OpenSAGE.BlenderPlugin')
OUT_W3D = '/tmp/mertank01.w3d'
TEX_NAME = 'wp_spike'

sys.path.insert(0, PLUGIN_REPO)
import io_mesh_w3d  # noqa: E402
io_mesh_w3d.register()

# clean scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# a beveled, stretched cube: proves real modeling ops survive the pipeline
bpy.ops.mesh.primitive_cube_add(size=1)
obj = bpy.context.active_object
obj.name = 'HULL'
obj.scale = (11.0, 6.0, 3.0)
bpy.ops.object.transform_apply(scale=True)
obj.location = (0, 0, 4.0)
bpy.ops.object.transform_apply(location=True)
mod = obj.modifiers.new('bevel', 'BEVEL')
mod.width = 0.8
mod.segments = 2
bpy.ops.object.modifier_apply(modifier='bevel')

# UV unwrap
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')

# checker-ish test texture, saved as TGA for the engine
img = bpy.data.images.new(TEX_NAME, width=64, height=64)
px = []
for y in range(64):
    for x in range(64):
        c = 0.75 if ((x // 8) + (y // 8)) % 2 == 0 else 0.35
        px += [c, c * 0.9, c * 0.7, 1.0]
img.pixels = px
img.filepath_raw = f'/tmp/{TEX_NAME}.tga'
img.file_format = 'TARGA_RAW'
img.save()

mat = bpy.data.materials.new('SpikeMat')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
tex.image = img
mat.node_tree.links.new(bsdf.inputs['Base Color'], tex.outputs['Color'])
obj.data.materials.append(mat)

bpy.ops.export_mesh.westwood_w3d(
    filepath=OUT_W3D,
    file_format='W3D',
    export_mode='HM',
    force_vertex_materials=True,
)
print('SPIKE_EXPORT_OK', OUT_W3D)
