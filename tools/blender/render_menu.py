# SPDX-License-Identifier: MIT
"""Render the original War Powers checkpoint tableau used behind the shell.

blender --background --factory-startup --python tools/blender/render_menu.py -- --data data
All geometry comes from our runtime asset authorship functions. No stock art.
"""
import argparse
import math
from pathlib import Path
import random
import sys
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from _bootstrap import ROOT, script_args  # noqa: E402
from build_polish import ASSETS, Kit, pipe  # noqa: E402

def main(argv=None):
    ap=argparse.ArgumentParser(description='Render the main-menu panorama from the production model kit (run inside Blender).')
    ap.add_argument('--data',type=Path,default=ROOT/'data',help='dataset root; writes Art/Textures/wp_menu.tga and the WPMenuArt mapping')
    ap.add_argument('--review',type=Path,default=Path('/tmp/warpowers-art-review'),help='JPEG contact sheet destination')
    args=ap.parse_args(script_args(argv))
    args.data=args.data.resolve();args.review.mkdir(parents=True,exist_ok=True)
    pipe.reset_scene()
    for blocks in (bpy.data.cameras,bpy.data.lights,bpy.data.armatures):
        for b in list(blocks):blocks.remove(b)
    def place(model,x,y,rotation=0,scale=1):
        k=Kit();ASSETS[model][2](k);o=k.join(model)
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        o.location=(x,y,0);o.rotation_euler.z=rotation;o.scale=(scale,)*3
        return o
    # Original terrain material: broad wind-scour + restrained fine grain.
    mat=bpy.data.materials.new('Meridian corridor')
    nt=mat.node_tree;b=nt.nodes['Principled BSDF'];b.inputs['Roughness'].default_value=.97
    noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.14;noise.inputs['Detail'].default_value=3
    ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.115,.12,.10,1)
    ramp.color_ramp.elements[1].color=(.37,.30,.20,1)
    coord=nt.nodes.new('ShaderNodeTexCoord');nt.links.new(coord.outputs['Object'],noise.inputs['Vector'])
    nt.links.new(noise.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],b.inputs['Base Color'])
    fine=nt.nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=5
    nt.links.new(coord.outputs['Object'],fine.inputs['Vector'])
    bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.11
    nt.links.new(fine.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],b.inputs['Normal'])
    n=64;verts=[];faces=[]
    for j in range(n+1):
        y=-220+j*500/n
        for i in range(n+1):
            x=-250+i*500/n
            lane=min(1,max(0,(abs(x-(.23*y+21))-18)/22))
            z=(math.sin(x*.042)*math.sin(y*.026)+math.cos((x+y)*.037))*.9*lane
            verts.append((x,y,z))
    for j in range(n):
        for i in range(n):a=j*(n+1)+i;faces.append((a,a+1,a+n+2,a+n+1))
    mesh=bpy.data.meshes.new('Dunes');mesh.from_pydata(verts,[],faces);mesh.update()
    ground=bpy.data.objects.new('Dunes',mesh);bpy.context.collection.objects.link(ground);ground.data.materials.append(mat)
    k=Kit()
    roadmat=k.mat('earth')
    road=bpy.data.meshes.new('Supply road');road.from_pydata([(-30,-220,.05),(-4,-220,.05),(99,280,.05),(73,280,.05)],[],[(0,1,2,3)])
    ob=bpy.data.objects.new('Supply road',road);bpy.context.collection.objects.link(ob);ob.data.materials.append(roadmat)
    # The deployment column occupies the right; open terrain leaves room for UI.
    place('mertank01',33,-19,1.20,1.20)
    place('merout01',62,6,1.23,1.15)
    place('merhaul01',37,28,1.40)
    place('mertank01',48,56,1.52,.90)
    place('wprelay01',78,64,-.30,1.18)
    place('wpscrap01',92,44,.20,1.12)
    for x,y in [(54,47),(57,72),(90,73),(106,68)]:place('wpwall01',x,y,.18,.73)
    for x,y in [(69,40),(74,43),(68,72),(85,48)]:place('merinf02',x,y,1.5,1.13)
    rng=random.Random(206)
    for i in range(27):
        x=rng.choice([-1,1])*rng.uniform(100,220);y=rng.uniform(-80,245)
        place('wprock01',x,y,rng.uniform(0,6.28),rng.uniform(1.6,4.9))
    # Distant front line; these remain small enough that the command column leads.
    place('jakvul01',58,160,-1.6,.9)
    place('jaktank01',37,184,-1.8,.9)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48
    scene.cycles.use_denoising=True;scene.render.resolution_x=1024;scene.render.resolution_y=512
    scene.render.resolution_percentage=100;scene.render.film_transparent=False
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.55
    world=scene.world or bpy.data.worlds.new('Dawn');scene.world=world
    world.node_tree.nodes['Background'].inputs[0].default_value=(.30,.40,.46,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.5
    sun=bpy.data.lights.new('Low morning sun','SUN');sun.energy=2.5;sun.angle=.085;sun.color=(1,.77,.48)
    o=bpy.data.objects.new('Low morning sun',sun);bpy.context.collection.objects.link(o);o.rotation_euler=(.8,-.4,-.6)
    camera=bpy.data.cameras.new('Operations');camera.lens=44
    cam=bpy.data.objects.new('Operations',camera);bpy.context.collection.objects.link(cam)
    cam.location=(119,-199,121);target=Vector((4,55,8))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    # Real volumetric distance haze makes large neutral forms recede naturally.
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,40,25));fog=bpy.context.object;fog.scale=(560,540,150)
    fmat=bpy.data.materials.new('Distance haze');fmat.node_tree.nodes.clear()
    volume=fmat.node_tree.nodes.new('ShaderNodeVolumeScatter');volume.inputs['Density'].default_value=.0022
    volume.inputs['Color'].default_value=(.63,.65,.60,1);volume.inputs['Anisotropy'].default_value=.3
    out=fmat.node_tree.nodes.new('ShaderNodeOutputMaterial');fmat.node_tree.links.new(volume.outputs[0],out.inputs['Volume'])
    fog.data.materials.append(fmat)
    texture=args.data/'Art/Textures/wp_menu.tga'
    scene.render.image_settings.file_format='TARGA';scene.render.filepath=str(texture)
    bpy.ops.render.render(write_still=True)
    scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=91
    bpy.data.images['Render Result'].save_render(str(args.review/'menu-panorama.jpg'),scene=scene)
    (args.data/'Data/INI/MappedImages/HandCreated/WPMenuArt.ini').write_text(
        '; Original game-asset tableau, tools/blender/render_menu.py\nMappedImage WPMenuBackdrop\n'
        '  Texture = wp_menu.tga\n  TextureWidth = 1024\n  TextureHeight = 512\n'
        '  Coords = Left:57 Top:0 Right:967 Bottom:512\n  Status = NONE\nEnd\n')
    print('MENU_ART_OK',texture,flush=True)

if __name__=='__main__':main()
