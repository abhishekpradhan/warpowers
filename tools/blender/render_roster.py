"""Render the actual shipped W3D roster with one portrait art direction.

blender --background --python tools/blender/render_roster.py --
    --data data --out /tmp/warpowers-portraits [--only WPIcoOutrider]
Then: python3 tools/genportraitsheet.py /tmp/warpowers-portraits --data data
"""
import argparse
from pathlib import Path
import re
import struct
import sys
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_polish import ROOT, portrait, pipe, Kit, chunks, chunk

def power_portrait(name,path):
    pipe.reset_scene()
    k=Kit()
    if name=='WPIcoPrecisionStrike':
        k.cyl('TARGET','gold',0,0,.15,5.9,.3,verts=32)
        k.cyl('INNER','dark',0,0,.33,5.2,.10,verts=32)
        k.cyl('RETICLE','gold',0,0,.46,2.7,.11,verts=24)
        k.cyl('INNER2','dark',0,0,.55,2.2,.10,verts=24)
        for x,y,z in [(-2,-1,6),(2,2,9)]:
            k.cyl('BOMB','ivory',x,y,z,.62,4,verts=10)
            k.sphere('NOSE','gold',(x,y,z-2),(.64,.64,.8),1)
            k.box('FIN','steel',x,y,z+1.7,2.5,.3,1.1)
            k.box('FIN2','steel',x,y,z+1.7,.3,2.5,1.1)
    else:
        k.cyl('HATCH','olive',0,0,.4,6.2,.8,verts=12)
        k.cyl('DARK','rubber',0,0,.86,5.3,.16,verts=12)
        k.cyl('LID','rust',-4,2,4.8,5,.65,axis='X',verts=12)
        for x,y,z in [(-1.5,-1.2,2.6),(2,1,3.1)]:
            k.box('VEST','sand',x,y,z,2,2.8,2.6,bevel=.4)
            k.sphere('HEAD','bare',(x,y,z+2.1),(.84,.84,1),2)
            k.sphere('HELMET','olive',(x,y,z+2.65),(1,1,.65),2)
            k.box('RIFLE','dark',x+2,y,z+.3,3.8,.6,.6,bevel=.1)
    obj=k.join('POWER');bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    portrait(obj,path)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',type=Path,default=ROOT/'data')
    ap.add_argument('--out',type=Path,default=Path('/tmp/warpowers-portraits'))
    ap.add_argument('--only',default='')
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    args.data=args.data.resolve();args.out=args.out.resolve();args.out.mkdir(parents=True,exist_ok=True)
    roster={}
    for name,body in re.findall(r'Object (\S+)\n(.*?)\nEnd',(args.data/'Data/INI/Default/Object.ini').read_text(),re.S):
        icon=re.search(r'SelectPortrait = (\S+)',body)
        model=re.search(r'\bModel = (\S+)',body)
        if icon and model:
            # Mission/decorative objects may reuse a roster portrait. They must
            # never replace the canonical unit's render because they occur later.
            if icon[1] not in roster or name=='WP_'+icon[1].removeprefix('WPIco'):
                roster[icon[1]]=model[1]
    roster.update(WPIcoPorter='MERHAUL01',WPIcoScavenger='JAKHAUL01',WPIcoMissionRelay='WPRELAY01')
    for icon,model in roster.items():
        if args.only and icon not in args.only.split(','):continue
        pipe.reset_scene()
        for blocks in (bpy.data.cameras,bpy.data.lights,bpy.data.armatures):
            for b in list(blocks):blocks.remove(b)
        # Resolve textures from the actual asset directory, never a fallback grid.
        for path in (args.data/'Art/Textures').glob('*.tga'):
            img=bpy.data.images.load(str(path));img.name=path.name
        modelpath=args.data/'Art/W3D'/(model.lower()+'.w3d')
        raw=modelpath.read_bytes();top=list(chunks(raw))
        hname=None
        for cid,sub,payload in top:
            if cid==0x700:
                for c,s,p in chunks(payload):
                    if c==0x701:hname=p[24:40].split(b'\0')[0]
        if hname==b'':
            # The engine accepts hierarchy-free utility/older models; the Blender
            # importer requires a root. Supply one in the review cache only.
            hierarchy=chunk(0x100,chunk(0x101,struct.pack('<I16sI3f',0x40001,model.encode(),1,0,0,0))+
                chunk(0x102,struct.pack('<16sI3f3f4f',b'ROOTTRANSFORM',0xffffffff,0,0,0,0,0,0,0,0,0,1)),subs=True)
            rebuilt=hierarchy
            for cid,sub,payload in top:
                if cid==0x700:
                    payload=b''.join(chunk(c,p[:24]+model.encode().ljust(16,b'\0') if c==0x701 else p,subs=s) for c,s,p in chunks(payload))
                rebuilt+=chunk(cid,payload,subs=sub)
            cachedir=args.out/'_imports';cachedir.mkdir(exist_ok=True)
            modelpath=cachedir/(model.lower()+'.w3d');modelpath.write_bytes(rebuilt)
        bpy.ops.import_mesh.westwood_w3d(filepath=str(modelpath))
        meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
        if not meshes:raise RuntimeError(f'{model}: no imported geometry')
        for o in meshes:
            bpy.context.view_layer.objects.active=o
            for md in list(o.modifiers):
                if md.type=='ARMATURE':bpy.ops.object.modifier_apply(modifier=md.name)
            matrix=o.matrix_world.copy();o.parent=None;o.matrix_world=matrix
            for mat in o.data.materials:
                if not mat or not mat.use_nodes:continue
                b=mat.node_tree.nodes.get('Principled BSDF')
                if b:
                    b.inputs['Roughness'].default_value=.85
                    b.inputs['Metallic'].default_value=0
                    b.inputs['Emission Strength'].default_value=0
        bpy.ops.object.select_all(action='DESELECT')
        for o in meshes:o.select_set(True)
        bpy.context.view_layer.objects.active=meshes[0]
        bpy.ops.object.join()
        obj=bpy.context.object
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        if max(obj.dimensions)==0:raise RuntimeError(f'{model}: empty bounds')
        portrait(obj,args.out/(icon+'.tga'))
        print('PORTRAIT_OK',icon,model,flush=True)
    for name in ['WPIcoPrecisionStrike','WPIcoTunnelAmbush']:
        if not args.only or name in args.only.split(','):
            power_portrait(name,args.out/(name+'.tga'))

if __name__=='__main__':main()
