"""Shared War Powers asset pipeline: bake, composite, export.

Every painted model script funnels through this
module so the painted look stays uniform and quality upgrades land on all
assets at once.

Composite recipe (v2):
  diffuse * shaped-AO            -- painted shading baked in
  + edge-wear highlight          -- island-border texels lightened with noise
                                    breakup (smart_project splits at hard
                                    edges, so island borders ARE the mesh
                                    edges -> reads as painted edge highlights)
  + low-frequency value noise    -- breaks up flat color fields
  + fine grain
build_polish.py supplies separate HOUSECOLOR meshes after the texture bake;
these receive the owning player's color through the native W3D asset manager.
"""
import math
import os
import random
import struct
import sys
from pathlib import Path

import bpy
import bmesh


def output_dirs():
    """Consistent explicit destinations for the retained original building kits."""
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,default=Path(__file__).resolve().parents[2]/'data')
    parser.add_argument('--scratch',type=Path,help='Explicit flat review directory for models and textures')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    modeldir=args.scratch or args.data/'Art/W3D'
    texturedir=args.scratch or args.data/'Art/Textures'
    for path in (modeldir,texturedir):path.mkdir(parents=True,exist_ok=True)
    return modeldir,texturedir


class Kit:
    """Modeling kit: palette-bound primitives collected into one mesh."""

    def __init__(self, palette, roughness=0.85):
        self.pal = palette
        self.mats = {}
        self.parts = []
        self.rough = roughness

    def mat(self, name):
        if name not in self.mats:
            m = bpy.data.materials.new(name)
            m.use_nodes = True
            bsdf = m.node_tree.nodes['Principled BSDF']
            bsdf.inputs['Base Color'].default_value = self.pal[name]
            bsdf.inputs['Roughness'].default_value = self.rough
            bsdf.inputs['Metallic'].default_value = 0.0
            self.mats[name] = m
        return self.mats[name]

    def _register(self, obj, color):
        obj.data.materials.clear()
        obj.data.materials.append(self.mat(color))
        self.parts.append(obj)
        return obj

    def box(self, name, color, cx, cy, cz, sx, sy, sz, bevel=0.0, rot=None):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz))
        o = bpy.context.active_object
        o.name = name
        o.scale = (sx, sy, sz)
        # Keep the authored center: applying location before a later rotation
        # rotates a part around the world origin (treads/plates flew off models).
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if bevel > 0:
            md = o.modifiers.new('b', 'BEVEL')
            md.width = bevel
            md.segments = 1
            bpy.ops.object.modifier_apply(modifier='b')
        if rot:
            o.rotation_euler = rot
        return self._register(o, color)

    def cyl(self, name, color, cx, cy, cz, r, depth, axis='Z', verts=10, rot=None):
        base = {'Z': (0, 0, 0), 'X': (0, math.pi / 2, 0), 'Y': (math.pi / 2, 0, 0)}[axis]
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth,
                                            location=(cx, cy, cz), rotation=base)
        o = bpy.context.active_object
        o.name = name
        if rot:
            o.rotation_euler = (base[0] + rot[0], base[1] + rot[1], base[2] + rot[2])
        return self._register(o, color)

    def prism(self, name, color, profile, y0, y1):
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
        return self._register(obj, color)

    def join(self, name):
        bpy.ops.object.select_all(action='DESELECT')
        for p in self.parts:
            p.select_set(True)
        bpy.context.view_layer.objects.active = self.parts[0]
        bpy.ops.object.join()
        obj = bpy.context.active_object
        obj.name = name
        obj.data.name = name
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        print('TRIS:', tris)
        return obj


def reset_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for item in list(block):
            block.remove(item)


def smart_uv(obj, island_margin):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.0, island_margin=island_margin)
    bpy.ops.object.mode_set(mode='OBJECT')


def setup_cycles(samples=24):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    return scene


def _add_bake_target(obj, image):
    for m in obj.data.materials:
        nt = m.node_tree
        for n in [n for n in nt.nodes if n.name.startswith('BakeTarget')]:
            nt.nodes.remove(n)
        node = nt.nodes.new('ShaderNodeTexImage')
        node.name = 'BakeTarget'
        node.image = image
        nt.nodes.active = node


def bake_images(obj, atlas):
    """Bake diffuse color, AO, and the island mask. Returns pixel lists.

    NOTE: materials must be fresh datablocks created this session — imported
    FBX materials silently bake black in headless Cycles (engine-notes).
    The EMIT mask bake rewrites material emission, so it runs last.
    """
    setup_cycles()
    img_diff = bpy.data.images.new('bake_diff', atlas, atlas)
    img_ao = bpy.data.images.new('bake_ao', atlas, atlas)
    img_mask = bpy.data.images.new('bake_mask', atlas, atlas)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    _add_bake_target(obj, img_diff)
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=8)
    _add_bake_target(obj, img_ao)
    bpy.ops.object.bake(type='AO', margin=8)

    for m in obj.data.materials:
        b = m.node_tree.nodes.get('Principled BSDF')
        if b:
            b.inputs['Emission Color'].default_value = (1, 1, 1, 1)
            b.inputs['Emission Strength'].default_value = 1.0
    _add_bake_target(obj, img_mask)
    bpy.ops.object.bake(type='EMIT', margin=0)

    return list(img_diff.pixels), list(img_ao.pixels), list(img_mask.pixels)


def composite(diff, ao, mask, atlas, out_path, *, seed=5,
              shade_lo=0.52, shade_hi=0.48, grain=0.022,
              edge_strength=0.55, edge_radius=1, lowfreq=0.045):
    """Blend the bakes into a painted-style TGA."""
    rng = random.Random(seed)

    inside = [mask[i * 4] > 0.5 for i in range(atlas * atlas)]
    edge = bytearray(atlas * atlas)
    r = edge_radius
    for y in range(atlas):
        for x in range(atlas):
            p = y * atlas + x
            if not inside[p]:
                continue
            found = False
            for dy in range(-r, r + 1):
                yy = y + dy
                if yy < 0 or yy >= atlas:
                    found = True
                    break
                for dx in range(-r, r + 1):
                    xx = x + dx
                    if xx < 0 or xx >= atlas or not inside[yy * atlas + xx]:
                        found = True
                        break
                if found:
                    break
            if found:
                edge[p] = 1

    # low-frequency value noise, bilinear over an 8px-cell grid
    cell = max(4, atlas // 32)
    gw = atlas // cell + 2
    grid = [rng.uniform(-lowfreq, lowfreq) for _ in range(gw * gw)]

    def lf(x, y):
        fx, fy = x / cell, y / cell
        ix, iy = int(fx), int(fy)
        tx, ty = fx - ix, fy - iy
        a = grid[iy * gw + ix]
        b = grid[iy * gw + ix + 1]
        c = grid[(iy + 1) * gw + ix]
        d = grid[(iy + 1) * gw + ix + 1]
        return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty

    rows = []
    for y in range(atlas):
        row = bytearray()
        for x in range(atlas):
            p = y * atlas + x
            i = p * 4
            shade = shade_lo + shade_hi * (ao[i] ** 1.4)
            v = lf(x, y)
            g = rng.uniform(-grain, grain)
            px = []
            for ch in range(3):
                c = diff[i + ch] * shade
                if edge[p]:
                    w = edge_strength * rng.uniform(0.35, 1.0)
                    c = c * (1 - w) + min(1.0, c * 1.35 + 0.06) * w
                px.append(max(0.0, min(1.0, c + v + g)))
            row += bytes((int(px[2] * 255), int(px[1] * 255), int(px[0] * 255)))
        rows.append(bytes(row))

    hdr = bytearray(18)
    hdr[2] = 2
    struct.pack_into('<HH', hdr, 12, atlas, atlas)
    hdr[16] = 24
    # Blender image origin is bottom-left; TGA default is bottom-up too.
    with open(out_path, 'wb') as f:
        f.write(bytes(hdr) + b''.join(rows))


def export_w3d(obj, tga_path, w3d_path, image_name):
    """Swap to a single textured material and export via the OpenSAGE plugin."""
    final_img = bpy.data.images.load(tga_path)
    final_img.name = image_name
    export_mat = bpy.data.materials.new(image_name + '_skin')
    export_mat.use_nodes = True
    bsdf = export_mat.node_tree.nodes['Principled BSDF']
    texn = export_mat.node_tree.nodes.new('ShaderNodeTexImage')
    texn.image = final_img
    export_mat.node_tree.links.new(bsdf.inputs['Base Color'], texn.outputs['Color'])
    obj.data.materials.clear()
    obj.data.materials.append(export_mat)

    bpy.ops.export_mesh.westwood_w3d(
        filepath=w3d_path,
        file_format='W3D',
        export_mode='HM',
        force_vertex_materials=True,
    )
    from legacy_contracts import apply
    apply(w3d_path)

def render_portrait(obj, out_path, size=128):
    """Render a 3/4-view cameo of the object (flat materials, transparent bg).

    Cheap EEVEE still — call before the bake with WP_PORTRAIT_DIR set and the
    script can exit early; icon sheets get real silhouettes for free.
    """
    import mathutils
    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.film_transparent = True
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.image_settings.file_format = 'TARGA'
    scene.render.filepath = out_path

    bb = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    ctr = sum(bb, mathutils.Vector()) / 8
    radius = max((v - ctr).length for v in bb)

    cam_data = bpy.data.cameras.new('WPPortraitCam')
    cam_data.lens = 60
    cam = bpy.data.objects.new('WPPortraitCam', cam_data)
    bpy.context.collection.objects.link(cam)
    direction = mathutils.Vector((1.0, -0.9, 0.65)).normalized()
    cam.location = ctr + direction * radius * 2.35
    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam

    sun_data = bpy.data.lights.new('WPSun', 'SUN')
    sun_data.energy = 3.0
    sun = bpy.data.objects.new('WPSun', sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (0.9, 0.2, 0.6)
    world = bpy.data.worlds.new('WPPortraitWorld') if not scene.world else scene.world
    scene.world = world
    world.use_nodes = True
    bgn = world.node_tree.nodes.get('Background')
    if bgn:
        bgn.inputs[0].default_value = (0.6, 0.6, 0.65, 1.0)
        bgn.inputs[1].default_value = 0.7

    bpy.ops.render.render(write_still=True)
    print('PORTRAIT_OK', out_path)


def maybe_portrait_exit(obj, name):
    """Env-gated portrait mode: render and skip the expensive bake/export."""
    d = os.environ.get('WP_PORTRAIT_DIR')
    if not d:
        return False
    os.makedirs(d, exist_ok=True)
    render_portrait(obj, os.path.join(d, name + '.tga'))
    return True
