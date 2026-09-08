# SPDX-License-Identifier: MIT
"""Original War Powers production assets, with reproducible repository outputs.

Run: blender --background --factory-startup --python tools/blender/build_polish.py -- --data data
     --review /tmp/warpowers-art-review [--only merout01,jakvul01,wprock01] [--check]

No imported meshes. All geometry, markings and surface detail are authored here.
The existing shared Cycles bake and W3D exporter remain the production format.

Every ASSETS entry records its BAKE size. Atlases listed in optimize_art.HALVED
are baked at twice their shipped size and area-halved by tools/optimize_art.py;
that two-step is what reproduces the committed bytes (a direct half-size bake
yields different pixels). ``--check`` rebuilds the selection into a temporary
tree, applies the optimize step and compares W3D/TGA bytes with ``--data``.

Geometry lives here and in two kit modules: support_kit.py (aircraft, support
and defense structures) and base_kit.py (the seven established base buildings
and builders). A builder's contract may set ``uv_margin`` and ``composite``
to keep a model's own smart-UV margin and painted-composite recipe instead of
the house defaults below; base_kit.py uses that to preserve its look.
"""
import argparse
import json
import math
from pathlib import Path
import random
import struct
import sys
import tempfile

import bpy
from mathutils import Vector, Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import ROOT, register_w3d_plugin, script_args  # noqa: E402
import wp_pipeline as pipe  # noqa: E402
from genw3d import frustum  # noqa: E402
from wp_w3d import (HIERARCHY, HIERARCHY_HEADER, HLOD, HLOD_HEADER, HLOD_LOD_ARRAY,  # noqa: E402
                    HLOD_SUB_OBJECT, MESH, MESH_HEADER3, PIVOT_SIZE, PIVOTS,
                    SUB_OBJECT_ARRAY_HEADER, chunk, chunks, mesh_chunk, name32)
import genrig  # noqa: E402
import optimize_art  # noqa: E402
import base_kit  # noqa: E402
import support_kit  # noqa: E402
from w3dhierarchy import canonicalize  # noqa: E402
register_w3d_plugin()

def color(hexcode):
    return tuple(int(hexcode[i:i+2], 16) / 255 for i in (0, 2, 4)) + (1,)

# Large contrasting surfaces carry recognition at the RTS camera distance.
PAL = {k: color(v) for k, v in dict(
    steel='708995', ivory='c8d1cf', gold='d5a94e', dark='28383f',
    rubber='171e22', glass='1d4753', lens='73bfbe', sand='a58b64',
    rust='744936', olive='5b7052', bare='77817d', concrete='74776d',
    rock='777064', rocklight='908779', earth='59584d', black='252b28',
    red='9a493c', white='d8d9cc').items()}

class Kit(pipe.Kit):
    def __init__(self):
        # Materials are created on first use, so the base-kit colours cost
        # nothing for models that never name them.
        super().__init__({**PAL, **base_kit.PALETTE})
        self.group = 'HULL'
    def _register(self, obj, material):
        super()._register(obj, material)
        vg = obj.vertex_groups.new(name=self.group)
        vg.add(range(len(obj.data.vertices)), 1.0, 'REPLACE')
        return obj
    def beam(self, name, mat, a, b, width=0.45):
        mid = (Vector(a) + Vector(b)) / 2
        v = Vector(b) - Vector(a)
        o = self.cyl(name, mat, *mid, width / 2, v.length, verts=6)
        o.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
        return o
    def sphere(self,name,mat,center,scale,subdivisions=1):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions,radius=1,location=center)
        o=bpy.context.object;o.name=name;o.scale=scale
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        return self._register(o,mat)
    def wheel(self, x, y, z, r=2, width=1.7, hub='bare'):
        previous=self.group
        side='L' if y>0 else 'R'
        axle='F' if x>3 else ('R' if x<-3 else 'M')
        self.group='WH'+side+'_'+axle
        if not hasattr(self,'wheel_bones'):self.wheel_bones={}
        self.wheel_bones[self.group]=(x,y,z)
        self.cyl('TIRE', 'rubber', x, y, z, r, width, axis='Y', verts=14)
        self.cyl('HUB', hub, x, y + math.copysign(width / 2 + .04, y), z,
                 r * .56, .13, axis='Y', verts=10)
        self.cyl('AXLE', 'dark', x, y + math.copysign(width / 2 + .13, y), z,
                 r * .20, .19, axis='Y', verts=8)
        for i in range(12):
            a = i * math.tau / 12
            self.box('TREAD', 'dark', x + math.sin(a) * r, y,
                     z + math.cos(a) * r, .42, width + .10, .20,
                     rot=(0, a, 0))
        self.group=previous
    def vents(self, x, y, z, n=5, axis='Y', length=2.5):
        for i in range(n):
            if axis == 'Y':
                self.box('VENT', 'dark', x+i*.55, y, z, .24, length, .08)
            else:
                self.box('VENT', 'dark', x, y+i*.55, z, length, .24, .08)

def outrider(k):
    # A small, long-wheelbase reconnaissance car; the roof sensor is its token.
    k.box('CHASSIS', 'dark', 0, 0, 2.3, 13.8, 5.5, 1.1, bevel=.25)
    k.prism('BODY', 'steel', [(-7,2.9),(-6.7,4.4),(-3.5,5), (2.3,5),
                            (6.8,4.1),(7.1,3.1)], -2.8,2.8)
    for y in (-3.15,3.15):
        for x in (-4.6,4.6): k.wheel(x,y,1.85,1.85,1.6)
        k.box('SIDE', 'ivory', -.8,y*.91,4.2,6.4,.32,1.25,bevel=.10)
        k.box('STEP', 'dark', -.4,y,2.5,3.7,.8,.25)
    k.prism('CAB', 'ivory', [(-3,4.8),(-2.7,6.5),(.7,6.5),(2.2,4.8)],-2.35,2.35)
    k.prism('WINDSCREEN', 'glass',[(.78,6.46),(2.22,4.84),(2.27,4.84),(.83,6.46)],-1.98,1.98)
    for y in (-2.4,2.4):
        k.box('WINDOW', 'glass',-1.2,y,5.7,2.65,.10,.96,bevel=.08)
        k.box('HANDLE','dark',-1,y*1.03,4.6,.8,.12,.12)
    k.box('HOOD', 'gold',4.5,0,4.52,2.9,1.45,.12,rot=(0,.18,0))
    k.box('BUMPER','dark',7.2,0,2.95,.55,6.2,.48)
    k.box('GRILLE','rubber',7.05,0,3.65,.16,2.7,.64)
    for y in (-2,2): k.box('LIGHT','lens',6.95,y,3.8,.19,.9,.42)
    k.vents(-6,0,4.51,n=4,axis='Y',length=2.6)
    k.cyl('AERIAL','dark',-3.5,1.8,7,.09,3.9,verts=6)
    k.box('STOWAGE','dark',-5.5,-1.5,5,1.9,1.9,.9,bevel=.16)
    k.group='TURRET'
    k.cyl('RING','dark',-.5,0,6.7,1.05,.3,verts=12)
    k.box('SENSOR','dark',-.5,0,7.4,1.8,1.8,1.05,bevel=.22)
    k.box('OPTIC','lens',.46,0,7.55,.14,1.32,.43)
    k.group='BARREL'
    k.cyl('GUN','dark',1.7,-.62,7.05,.18,3.5,axis='X',verts=8)
    return dict(turret=(-.5,0,6.8), muzzle=(3.6,-.62,7.05),
                barrel=(.2,-.62,7.05),
                house=[(-4.7,0,4.9,1.2,2.2,.08)])

def vulture(k):
    # Improvised pickup, an exposed gun bed and offset shield distinguish it.
    k.box('FRAME','dark',0,0,2.4,17,6.4,.8)
    for y in (-3.5,3.5):
        for x in (-5.6,5.7): k.wheel(x,y,2,2,1.7,hub='rust')
    k.box('BED','rust',-3.9,0,3.5,8.6,6.6,1,bevel=.17)
    for y in (-3.1,3.1):
        k.box('BEDRAIL','sand',-4,y,4.2,8.5,.42,1.2)
        for x in (-7.5,-4,0): k.box('BEDPOST','dark',x,y,4.3,.25,.57,1.4)
    k.box('TAILGATE','sand',-8.15,0,4.15,.3,6.7,1.5)
    k.prism('CAB','sand',[(.4,3.4),(.4,7),(3.8,7),(5.4,5.25),(8.2,4.7),(8.2,3.4)],-2.9,2.9)
    k.prism('WINDSCREEN','glass',[(3.85,6.95),(5.44,5.27),(5.48,5.32),(3.91,6.99)],-2.44,2.44)
    for y in (-2.96,2.96):
        k.box('SIDEWINDOW','glass',2.1,y,6,2.7,.10,1.18)
        k.box('DOOR','olive' if y<0 else 'rust',2.8,y,4.45,3.9,.15,1.65,bevel=.06)
        k.box('HANDLE','bare',1,y*1.02,5.05,.72,.15,.12)
    k.box('HOOD','rust',6.8,0,4.92,2.6,5.8,.20,rot=(0,.13,0))
    k.box('GRILLE','dark',8.4,0,4.0,.35,4.9,1.05)
    for y in (-2.05,2.05): k.cyl('HEADLIGHT','white',8.6,y,4.2,.4,.14,axis='X',verts=8)
    k.box('BUMPER','bare',8.7,0,2.95,.55,7.15,.5)
    k.cyl('EXHAUST','dark',.1,-3.05,6,.23,5,verts=8)
    k.cyl('FUEL','olive',-6.8,1.6,4.8,.76,1.9,verts=10)
    k.box('AMMO','dark',-6.3,-1.3,4.35,2.4,1.6,.9,bevel=.08)
    k.group='TURRET'
    k.cyl('MOUNT','dark',-3.1,0,4.6,.6,1.4,verts=10)
    k.box('RECEIVER','dark',-2.6,0,6,2.6,1.3,1.2,bevel=.10)
    k.box('SHIELD','olive',-.85,0,6.25,.26,3.4,2.5,rot=(0,-.1,0))
    k.box('PATCH','rust',-.65,-.95,6.7,.13,1.35,.8)
    k.group='BARREL'
    for y in (-.42,.42):
        k.cyl('BARREL','dark',1.35,y,6, .18,4.2,axis='X',verts=8)
        k.cyl('MUZZLE','bare',3.45,y,6,.24,.4,axis='X',verts=8)
    k.group='TURRET'
    k.box('BELTBOX','rust',-2.4,-1.1,5.6,1.8,1.0,1.1)
    return dict(turret=(-3.1,0,5.15),barrel=(-.85,0,6),muzzle=(3.7,0,6),house=[(1.7,0,7.06,1.5,2.1,.10)])

def mongrel(k):
    k.prism('HULL','sand',[(-10,2),(-10,5),(-7,6.3),(5.7,6.3),(10,3.7),(10,2)],-4.8,4.8)
    for y in (-5.4,5.4):
        k.box('TRACK','rubber',-.4,y,1.8,20,2.6,3,bevel=.55)
        for x in (-7,-3.5,0,3.5,7): k.cyl('ROADWHEEL','dark',x,y+math.copysign(1.35,y),1.7,1.35,.2,axis='Y',verts=10)
        for x in (-6,-2,2,6):
            k.box('ARMOR','rust' if x in (-6,2) else 'olive',x,y,4.7,3.55,2.65,1.55,bevel=.12)
        k.box('TREADTOP','rubber',0,y,3.4,19,2.3,.18)
    k.vents(-8,-1.5,6.4,n=6,length=2.8)
    k.cyl('DRUM','rust',-10.1,0,5.5,1.35,5.8,axis='Y',verts=12)
    k.group='TURRET'
    k.cyl('RING','dark',-1,0,6.4,3.6,.5,verts=12)
    k.box('TURRETHEAD','sand',-1.5,0,8,8,6.5,2.6,bevel=.8)
    k.box('ARMOR','olive',-1.6,-3.4,8.2,6.4,.48,2.4,rot=(.06,0,0))
    k.box('PATCH','rust',1.1,3.35,8.25,2.5,.4,1.8)
    k.cyl('MANTLET','dark',3,0,8,.85,2.8,axis='X',verts=10)
    k.group='BARREL'
    k.cyl('BARREL','dark',8.5,0,8,.43,10.7,axis='X',verts=10)
    k.box('BRAKE','bare',13.5,0,8,1.45,1.15,1.0,bevel=.13)
    k.group='TURRET'
    k.cyl('HATCH','rust',-2.5,1.1,9.55,1.2,.38,verts=12)
    k.cyl('ANTENNA','dark',-4.2,-2.2,11.3,.10,3.7,verts=6)
    return dict(turret=(-1,0,6.5),barrel=(3,0,8),muzzle=(14.3,0,8),house=[(7,-2.6,5.06,2.3,1.5,.12)])

def vector(k):
    k.prism('HULL','steel',[(-10,2.5),(-10.3,5.1),(-7,6.7),(3.6,6.7),(10.5,3.9),(10.2,2.5)],-4.8,4.8)
    for y in (-5.5,5.5):
        k.box('TRACK','rubber',0,y,1.9,20.4,2.7,3,bevel=.55)
        for x in (-7.2,-3.6,0,3.6,7.2):k.cyl('ROADWHEEL','steel',x,y+math.copysign(1.43,y),1.8,1.34,.16,axis='Y',verts=12)
        for x in (-6.5,-2.1,2.3,6.7):
            k.box('SKIRT','ivory',x,y,4.75,3.9,2.65,1.60,bevel=.14)
            k.box('INSET','dark',x,y+math.copysign(1.4,y),4.68,2.6,.10,.63)
    k.vents(-8,-1.5,6.77,n=6,length=3)
    for y in (-3.3,3.3):
        k.box('HEADLIGHT','lens',9.1,y,4.61,.34,1.07,.45)
        k.cyl('EXHAUST','dark',-10.2,y,5.2,.48,1.15,axis='X',verts=8)
    k.box('GLACIS','gold',5.7,0,5.58,3.4,2,.13,rot=(0,.38,0))
    k.group='TURRET'
    k.cyl('RING','dark',-1.0,0,6.9,3.5,.55,verts=12)
    k.box('TURRET','ivory',-1.2,0,8.2,8.8,7,2.45,bevel=.73)
    k.box('CHEEK','steel',1.75,-3.15,8.4,3.7,.62,1.6,bevel=.18)
    k.box('CHEEK','steel',1.75,3.15,8.4,3.7,.62,1.6,bevel=.18)
    k.box('MANTLET','steel',3.4,0,8.2,1.8,2.55,1.9,bevel=.32)
    k.group='BARREL'
    k.cyl('BARREL','dark',9.0,0,8.2,.41,10.6,axis='X',verts=12)
    k.cyl('SLEEVE','steel',5.45,0,8.2,.62,3.2,axis='X',verts=12)
    k.box('BRAKE','dark',14.1,0,8.2,1.4,1.18,.98,bevel=.12)
    k.group='TURRET'
    k.box('OPTICS','gold',-2.7,-1.6,9.7,2.5,1.85,.73,bevel=.14)
    k.box('LENS','lens',-1.4,-1.6,9.8,.13,1.4,.33)
    k.cyl('HATCH','steel',-2.3,1.5,9.62,1.17,.31,verts=12)
    k.cyl('AERIAL','dark',-4.8,2.5,11.3,.09,3.7,verts=6)
    return dict(turret=(-1,0,6.9),barrel=(3.4,0,8.2),muzzle=(14.9,0,8.2),house=[(6.8,-3.1,5.03,2.1,1.5,.14)])

def zenith(k):
    k.box('FRAME','dark',0,0,2.1,21,7.5,1.2)
    for y in (-4.1,4.1):
        for x in (-7,-1,7): k.wheel(x,y,2.1,2.1,1.9)
    k.box('DECK','steel',-1,0,4,19,7.7,1.5,bevel=.25)
    k.prism('CAB','ivory',[(4.5,4.6),(4.5,7.9),(7.8,7.9),(10.4,5.1),(10.4,4.6)],-3.2,3.2)
    k.prism('GLASS','glass',[(7.9,7.9),(10.5,5.2),(10.6,5.2),(8,7.9)],-2.6,2.6)
    for y in (-3.26,3.26): k.box('WINDOW','glass',6,y,6.8,2.1,.12,1.2)
    k.box('BUMPER','dark',10.5,0,3.1,.65,8.5,.6)
    k.box('AMMORACK','gold',-7.4,0,5.6,3.5,6.4,1.8,bevel=.16)
    for y in (-4.3,4.3):
        k.box('STABILIZER','dark',-6.5,y,3.7,2.8,1.1,1.1)
        k.box('JACK','steel',-6.5,y,2.7,.8,.8,2.3)
    k.group='TURRET'
    k.cyl('RING','dark',-1.8,0,5.1,2.8,.45,verts=12)
    k.box('CRADLE','ivory',-1.8,0,6.35,5.5,4.8,2.4,bevel=.5)
    k.group='BARREL'
    k.box('BREECH','dark',-4,0,7.6,4,2,1.65,bevel=.22)
    k.cyl('BARREL','dark',5.5,0,7.7,.5,16,axis='X',verts=10)
    k.cyl('SLEEVE','steel',1,0,7.7,.76,5.2,axis='X',verts=10)
    k.box('BRAKE','dark',13.3,0,7.7,1.7,1.5,1.2,bevel=.13)
    k.group='TURRET'
    k.box('SIGHT','glass',-.3,-2,8.0,1.7,.65,.7)
    return dict(turret=(-1.8,0,5.3),barrel=(-4,0,7.7),muzzle=(14.3,0,7.7),house=[(6.15,0,7.96,1.5,2.9,.10)])

def rock(k):
    rng=random.Random(47)
    for i,(x,y,sx,sy,sz) in enumerate([(0,0,22,17,15),(-9,3,11,11,8),(8,-5,13,10,6)]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,sz*.36))
        o=bpy.context.object
        for v in o.data.vertices:
            v.co.x*=sx*.53*rng.uniform(.85,1.15)
            v.co.y*=sy*.53*rng.uniform(.85,1.15)
            v.co.z=max(-sz*.35,v.co.z*sz*.66)
        k._register(o,'rocklight' if i==1 else 'rock')
    for i in range(5):
        k.box('STRATA','earth',-5+i*2.6,-7.1,3+i*.36,3.8,.6,.45,rot=(0,.1,.10))
    return {}

def scrap(k):
    k.box('PALLET','earth',0,0,.5,22,17,1,bevel=.4)
    k.box('CONTAINER','rust',-2,1,4,14,8,6,bevel=.35,rot=(0,-.045,.09))
    for x in range(-8,5,2): k.box('CORRUGATION','dark',x,-3.2,3.8,.22,.25,5.4)
    k.box('OPENEND','dark',5.2,1.7,3.6,.18,6.7,4.7,rot=(0,0,.09))
    for i in range(4):
        k.box('SHEET','bare' if i%2 else 'olive',-3+i*1.9,4.4,7.2+i*.2,7,4,.22,rot=(.12,-.07,.24*i))
    for x,y in [(7,-5.5),(8,-1),(-7,-6.2)]:
        k.cyl('DRUM','rust',x,y,2.3,1.7,3.8,verts=10)
        for z in (1,3.6): k.cyl('RIB','dark',x,y,z,1.78,.14,verts=10)
    k.cyl('TIRE','rubber',7,5,1.2,2.9,1.8,verts=14)
    k.cyl('TIREHOLE','earth',7,5,2.15,1.5,.10,verts=12)
    return {}

def relay(k):
    k.box('FOUNDATION','concrete',0,0,.65,20,18,1.3,bevel=.5)
    k.box('EQUIPMENT','steel',-4,1,4.2,7.5,10,7,bevel=.3)
    k.box('DOOR','dark',-.15,1,4,.12,6,5.4)
    k.box('CONTROL','gold',-.05,-1.6,4.7,.16,1.15,1.8)
    for i in range(4):k.box('COOLING','dark',-4,-4.1,3+i*.85,5,.13,.35)
    # Open triangular lattice mast keeps it recognizable through fog.
    feet=[(3,-5),(8,3),(0,4)]
    for x,y in feet:
        k.beam('LEG','bare',(x,y,1),(4,0,32),.7)
    for z in (6,13,20,27):
        t=z/32
        ring=[(x*(1-t)+4*t,y*(1-t),z) for x,y in feet]
        for i in range(3): k.beam('CROSS','dark',ring[i],ring[(i+1)%3],.42)
        if z<27:
            for i in range(3):k.beam('BRACE','dark',ring[i],(4,0,z+6),.32)
    k.cyl('DISHBACK','dark',4,-.8,27,4.5,.75,axis='Y',verts=16)
    k.cyl('DISH','ivory',4,-1.25,27,4.1,.20,axis='Y',verts=16)
    k.cyl('FEED','gold',4,-2.3,27,.35,1.7,axis='Y',verts=8)
    k.cyl('AERIAL','bare',4,0,34.6,.16,6,verts=8)
    k.cyl('BEACON','red',4,0,37.6,.38,.65,verts=8)
    return {}

def wall(k):
    k.prism('JERSEY','concrete',[(-18,0),(18,0),(18,7),(-18,7)],-2.5,2.5)
    k.box('CAP','rocklight',0,0,7.5,36,5.4,1,bevel=.4)
    for x in (-16.5,16.5): k.box('BUTTRESS','dark',x,0,4,2.2,6.4,8,bevel=.12)
    for x in (-11,-3,5):
        k.box('PANEL','earth',x,-2.54,3.2,7,.12,4.7)
        k.box('MARKING','gold',x,-2.63,4.1,3.8,.10,.55,rot=(0,.40,0))
    k.box('CHIP','dark',8,-2.6,1.8,1.3,.15,.4,rot=(0,.4,0))
    return {}

def hauler(k,jackal=False):
    body='sand' if jackal else 'ivory';trim='olive' if jackal else 'gold'
    k.box('FRAME','dark',0,0,2.3,23,7.8,1.1)
    for y in (-4.25,4.25):
        for x in (-8,-2,8):k.wheel(x,y,2.15,2.15,1.8,hub='rust' if jackal else 'steel')
    k.box('FLATBED','rust' if jackal else 'steel',-3.4,0,3.9,16,8.2,1.3,bevel=.25)
    k.prism('CAB',body,[(5.2,3.7),(5.2,8.5),(8.4,8.5),(11.2,6.1),(11.2,3.7)],-3.35,3.35)
    k.prism('GLASS','glass',[(8.5,8.4),(11.25,6.1),(11.3,6.15),(8.55,8.45)],-2.9,2.9)
    for y in (-3.42,3.42):
        k.box('WINDOW','glass',6.7,y,7,2.35,.13,1.65)
        k.box('DOORSTRIPE',trim,7.7,y,5.2,4.7,.18,.72)
        k.box('MIRROR','dark',10.2,y*1.15,7.1,.7,.35,1.1)
    k.box('BUMPER','dark',11.5,0,3.2,.6,8.7,.65)
    k.box('GRILLE','dark',11.3,0,4.8,.17,4.8,1.4)
    for y in (-2.85,2.85):k.box('LIGHT','white',11.5,y,4.75,.16,.8,.55)
    # Visible standardized loads make the unit's economic purpose unambiguous.
    k.group='CARGO'
    for x in (-8.3,-3.4,1.4):
        for y in (-2.05,2.05):
            k.box('CARGO',trim if x==-3.4 else 'bare',x,y,5.9,4.4,3.6,2.7,bevel=.20)
            for dx in (-1.35,1.35):k.box('STRAP','dark',x+dx,y,7.32,.20,3.72,.12)
    k.group='HULL'
    for y in (-3.8,3.8):k.box('BEDRAIL','dark',-3.4,y,5.4,16,.30,.42)
    k.cyl('STACK','dark',4.4,-3.5,6.3,.32,6.1,verts=8)
    return dict(bones={'HULL':(0,0,0),'CARGO':(0,0,0)},house=[(6.8,0,8.55,1.5,2.9,.12)])

def infantry(k,role='rifle',jackal=False):
    uniform='olive' if jackal else 'steel';armor='sand' if jackal else 'ivory'
    trim='rust' if jackal else 'gold'
    heavy=role=='heavy';scout=role=='scout'
    width=1.24 if heavy else (.88 if scout else 1.05)
    for bone,y in [('LEGL',-.73),('LEGR',.73)]:
        k.group=bone
        k.box('BOOT','rubber',.23,y,.38,1.42,.98,.76,bevel=.17)
        k.box('SHIN',uniform,-.10,y,1.24,1.02,.87,1.2,bevel=.19)
        k.box('THIGH',uniform,-.12,y,2.16,1.07,.94,1.05,bevel=.23)
        k.box('KNEEPAD','dark',.49,y,1.64,.23,.67,.64,bevel=.07)
    k.group='TORSO'
    k.box('PELVIS','dark',-.05,0,2.84,1.68,2.4,.73,bevel=.18)
    k.box('JACKET',uniform,0,0,4.07,1.90,width*2.4,2.15,bevel=.30)
    k.box('VEST',armor,.93,0,4.22,.26,width*1.91,1.78,bevel=.13)
    for y in (-.62,.12,.62):k.box('POUCH','dark',1.12,y,3.64,.36,.47,.59,bevel=.07)
    k.box('PACK',uniform,-1.2,0,4.38,.69,1.65,1.69,bevel=.17)
    if heavy:
        k.box('AMMOPACK','dark',-1.51,0,4.30,.61,2.16,2.17,bevel=.16)
        k.box('GORGET',armor,.20,0,5.30,1.58,2.65,.41,bevel=.12)
    if scout:k.cyl('RADIO','dark',-.9,.7,6.1,.07,2.6,verts=6)
    for bone,y in [('ARML',-1.55),('ARMR',1.55)]:
        k.group=bone
        k.box('SLEEVE',uniform,.36,y,4.17,1.67,.82,.93,bevel=.23)
        k.box('SHOULDER',armor,-.07,y,4.75,.90,1.04,.51,bevel=.15)
        k.box('FOREARM',uniform,1.45,y*.85,3.88,1.20,.66,.69,bevel=.17)
        k.box('GLOVE','dark',2.04,y*.69,3.83,.56,.59,.52,bevel=.12)
    k.group='HEAD'
    k.sphere('HEAD','sand' if jackal else 'bare',(0,0,6.05),(.77,.77,.86),2)
    if scout:
        k.box('HOOD',uniform,-.22,0,6.30,1.38,1.64,1.35,bevel=.32)
        k.box('VISOR','lens',.73,0,6.18,.13,1.44,.49,bevel=.08)
    else:
        k.sphere('HELMET',trim if jackal else 'dark',(-.10,0,6.71),(.94,.94,.64),2)
        k.box('BRIM',armor,.35,0,6.71,1.38,1.96,.16,bevel=.07)
        k.box('EYEPIECE','dark',.74,0,6.24,.13,1.28,.25,bevel=.05)
    k.group='GUN'
    if role=='rocket':
        k.cyl('LAUNCHER','dark',.65,1.0,6.03,.48,4.4,axis='X',verts=10)
        k.cyl('WARHEAD',trim,2.85,1.0,6.03,.43,.65,axis='X',verts=10)
        k.cyl('BACKBLAST','bare',-1.65,1.0,6.03,.61,.35,axis='X',verts=10)
        k.box('SIGHT','glass',1.0,.44,6.47,.55,.23,.43)
    elif role=='heavy':
        k.box('RECEIVER','dark',2.1,.51,3.87,2.1,.96,.76,bevel=.09)
        k.cyl('BARREL','dark',4.0,.51,3.98,.32,2.7,axis='X',verts=10)
        k.cyl('DRUM',trim,2.5,.51,3.24,.55,1.1,axis='Y',verts=10)
    else:
        length=1.65 if scout else 3.2
        k.box('RIFLE','dark',2.1,.51,3.88,length,.43,.46,bevel=.06)
        k.cyl('BARREL','dark',2.1+length*.5,.51,3.98,.10,.72,axis='X',verts=8)
        k.box('MAGAZINE',trim,2,.51,3.42,.34,.34,.52,rot=(0,.17,0))
    return dict(bones=genrig.WORLD,bone_indices=genrig.PIV,hierarchy='WPINF1',
                housebone=genrig.PIV['TORSO'],houseorigin=genrig.WORLD['TORSO'],
                house=[(.96,-.84,4.74,.08,.45,.43)])

def damaged(k,fn):
    contract=fn(k)
    for name,mat in k.mats.items():
        b=mat.node_tree.nodes['Principled BSDF'];c=b.inputs['Base Color'].default_value
        l=c[0]*.3+c[1]*.5+c[2]*.2
        if name not in ('gold','olive','lens'):
            b.inputs['Base Color'].default_value=(l*.61+.016,l*.55+.012,l*.47+.008,1)
    contract['lifecycle']='damaged'
    return contract

def wreck(k,fn):
    fn(k)
    for o in k.parts:
        for v in o.data.vertices:
            p=o.matrix_world@v.co
            p.z=max(.05,p.z*.34+.15*math.sin(p.x*.62));p.y+=.045*p.x
            v.co=p
        o.matrix_world=Matrix.Identity(4)
        o.vertex_groups.clear();g=o.vertex_groups.new(name='HULL');g.add(range(len(o.data.vertices)),1,'REPLACE')
    for mat in k.mats.values():
        b=mat.node_tree.nodes['Principled BSDF'];l=sum(b.inputs['Base Color'].default_value[:3])/3
        b.inputs['Base Color'].default_value=(l*.30+.028,l*.27+.024,l*.23+.02,1)
    return dict(lifecycle='wreck')

def rubble(k,small=False):
    size=1 if small else 1.6
    k.box('FOUNDATION','dark',0,0,.35,25*size,21*size,.7,bevel=.2)
    profile=[(-12,0),(12,0),(12,3),(8,3),(7,7),(2,6),(0,10),(-5,7),(-7,10),(-12,8)]
    k.prism('BROKENWALL','concrete',[(x*size,z*size) for x,z in profile],8*size,10*size)
    k.box('SIDESTUMP','concrete',-11*size,0,3*size,2*size,17*size,6*size,bevel=.3)
    rng=random.Random(212 if small else 214)
    for i in range(10):
        x=rng.uniform(-8,10)*size;y=rng.uniform(-8,6)*size
        k.box('RUBBLE','earth' if i%3 else 'bare',x,y,rng.uniform(.7,2)*size,
              rng.uniform(2,5)*size,rng.uniform(1.5,4)*size,rng.uniform(.7,2)*size,
              bevel=.15,rot=(rng.uniform(-.25,.25),rng.uniform(-.2,.2),rng.uniform(0,3)))
    for x,z in [(-8,10),(1,9),(6,8)]:
        k.beam('REBAR','dark',(x*size,8.8*size,z*size),((x+.8)*size,9*size,(z+2.5)*size),.22*size)
    k.box('FALLENROOF','dark',1,-2,3*size,13*size,8*size,.45,rot=(.14,.08,.25))
    return dict(lifecycle='rubble')

# (portrait label, texture stem, authoring function, BAKE size). The shipped
# atlas size is optimize_art.shipped_size(texture, bake): the compact combat
# vehicles, infantry, scrap, relay and the five base-kit buildings ship at
# half a 512px bake, rock/wall at half a 256px bake; the flagship tanks ship
# their 512px bake and everything else (haulers, damaged/wreck/ruin variants,
# the support kit, the two builders) its 256px bake.
ASSETS={
    'merout01': ('outrider','wp_outrider',outrider,512),
    'mertank01': ('vector','wp_vector',vector,512),
    'jakvul01': ('vulture','wp_vulture',vulture,512),
    'jaktank01': ('mongrel','wp_mongrel',mongrel,512),
    'merzen01': ('zenith','wp_zenith',zenith,512),
    'wprock01': ('rock','wp_rock',rock,256),
    'wpscrap01': ('scrap','wp_scrap',scrap,512),
    'wprelay01': ('relay','wp_relay',relay,512),
    'wpwall01': ('wall','wp_wall',wall,256),
    'merhaul01': ('porter','wp_porter',lambda k:hauler(k),256),
    'jakhaul01': ('scavenger','wp_scavenger',lambda k:hauler(k,True),256),
}
for role,suffix,mer,jak in [('rifle','inf02','warden','scrapper'),('rocket','roc01','lancer','sting'),
                           ('scout','sct01','vigil','prowler'),('heavy','hvy01','bastion','bruiser')]:
    ASSETS['mer'+suffix]=(mer,'wp_'+mer,lambda k,r=role:infantry(k,r),512)
    ASSETS['jak'+suffix]=(jak,'wp_'+jak,lambda k,r=role:infantry(k,r,True),512)
for original in ['mertank01','jaktank01','merout01','jakvul01','merzen01']:
    label,texture,fn,res=ASSETS[original]
    ASSETS[original+'d']=(label+'-damaged',texture+'_d',lambda k,f=fn:damaged(k,f),256)
ASSETS.update({
    'wpwreck01':('meridian-wreck','wp_merwreck',lambda k:wreck(k,vector),256),
    'wpwreck02':('jackal-wreck','wp_jakwreck',lambda k:wreck(k,mongrel),256),
    'wpruin01':('structure-ruin','wp_ruinlarge',lambda k:rubble(k),256),
    'wpruin02':('structure-ruin-small','wp_ruinsmall',lambda k:rubble(k,True),256),
})
ASSETS.update(support_kit.ASSETS)
ASSETS.update(base_kit.ASSETS)
GEOMETRY_SOURCES=[('tools/blender/support_kit.py',support_kit.ASSETS),('tools/blender/base_kit.py',base_kit.ASSETS)]

def final_w3d(path, model, contract):
    """Append original player-color geometry and a turret-relative muzzle bone."""
    content=list(chunks(path.read_bytes()))
    meshes=[]
    for i,p in enumerate(contract.get('house',[])):
        name='HOUSECOLOR'+str(i)
        x,y,z,sx,sy,sz=p
        origin=contract.get('houseorigin',(0,0,0));x-=origin[0];y-=origin[1];z-=origin[2]
        meshes.append((name,mesh_chunk(model,name,(220,220,220),frustum(x,y,z,sx,sy,sz))))
    output=b''
    for cid,sub,payload in content:
        if cid==HIERARCHY and contract.get('hierarchy'):continue
        if cid==HIERARCHY and contract.get('muzzle'):
            parts=list(chunks(payload))
            pivotdata=next(p for c,s,p in parts if c==PIVOTS)
            pivots=[pivotdata[i:i+PIVOT_SIZE] for i in range(0,len(pivotdata),PIVOT_SIZE)]
            names={p[:16].split(b'\0')[0].decode():i for i,p in enumerate(pivots)}
            if 'TURRET' not in names:raise ValueError('TURRET pivot missing')
            parent='BARREL' if contract.get('barrel') else 'TURRET'
            if contract.get('barrel'):
                i=names['BARREL'];v=tuple(a-b for a,b in zip(contract['barrel'],contract['turret']))
                pivots[i]=struct.pack('<16sI3f3f4f',b'BARREL',names['TURRET'],*v,0,0,0,0,0,0,1)
            v=tuple(a-b for a,b in zip(contract['muzzle'],contract.get('barrel',contract['turret'])))
            pivots.append(struct.pack('<16sI3f3f4f',b'MUZZLE',names[parent],*v,0,0,0,0,0,0,1))
            payload=b''
            for c,s,p in parts:
                if c==HIERARCHY_HEADER:
                    p=p[:20]+struct.pack('<I',len(pivots))+p[24:]
                if c==PIVOTS:p=b''.join(pivots)
                payload+=chunk(c,p,subs=s)
        if cid==HLOD:
            output+=b''.join(m for _,m in meshes)
            rebuilt=b''
            for c,s,p in chunks(payload):
                if c==HLOD_HEADER and contract.get('hierarchy'):
                    p=p[:24]+contract['hierarchy'].encode().ljust(16,b'\0')
                if c==HLOD_LOD_ARRAY:
                    q=b''
                    for cc,ss,pp in chunks(p):
                        if cc==SUB_OBJECT_ARRAY_HEADER:pp=struct.pack('<I',struct.unpack_from('<I',pp)[0]+len(meshes))+pp[4:]
                        if cc==HLOD_SUB_OBJECT and contract.get('bone_indices'):
                            name=pp[4:].split(b'\0')[0].decode().split('.')[-1]
                            pp=struct.pack('<I',contract['bone_indices'][name])+pp[4:]
                        q+=chunk(cc,pp,subs=ss)
                    for name,_ in meshes:q+=chunk(HLOD_SUB_OBJECT,struct.pack('<I32s',contract.get('housebone',0),name32(model+'.'+name)))
                    p=q
                rebuilt+=chunk(c,p,subs=s)
            payload=rebuilt
        output+=chunk(cid,payload,subs=sub)
    path.write_bytes(canonicalize(output))

def portrait(obj,path):
    """One camera and neutral studio lighting for every unit and structure."""
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.samples=24
    scene.render.film_transparent=True
    scene.render.resolution_x=scene.render.resolution_y=256
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='TARGA'
    scene.render.filepath=str(path)
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    world=scene.world or bpy.data.worlds.new('Studio')
    scene.world=world
    world.node_tree.nodes['Background'].inputs[0].default_value=(.45,.50,.56,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.35
    pts=[obj.matrix_world@Vector(v) for v in obj.bound_box]
    ctr=sum(pts,Vector())/8
    radius=max((p-ctr).length for p in pts)
    camdata=bpy.data.cameras.new('PortraitCamera');camdata.type='ORTHO'
    camdata.ortho_scale=radius*1.82
    cam=bpy.data.objects.new('PortraitCamera',camdata);scene.collection.objects.link(cam)
    cam.location=ctr+Vector((1,-1.3,1.1)).normalized()*radius*4
    cam.rotation_euler=(ctr-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    for name,offset,energy,size in [('Key',(1,-2,3),800,2),('Rim',(-2,1,2),1000,1.5)]:
        ld=bpy.data.lights.new(name,'AREA');ld.energy=energy*(radius/10)**2;ld.shape='DISK';ld.size=radius*size
        light=bpy.data.objects.new(name,ld);scene.collection.objects.link(light)
        light.location=ctr+Vector(offset)*radius
        light.rotation_euler=(ctr-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.render.render(write_still=True)

def build(model,entry,args):
    label,texture,fn,res=entry
    pipe.reset_scene()
    for blocks in (bpy.data.cameras,bpy.data.lights,bpy.data.armatures):
        for b in list(blocks):blocks.remove(b)
    k=Kit();contract=fn(k)
    if contract.get('barrel') or getattr(k,'wheel_bones',None):
        bones=dict(contract.get('bones',{'HULL':(0,0,0)}))
        if contract.get('turret'):bones['TURRET']=contract['turret']
        if contract.get('barrel'):bones['BARREL']=contract['barrel']
        bones.update(getattr(k,'wheel_bones',{}))
        contract['bones']=bones
        if getattr(k,'wheel_bones',None):contract['wheels']=list(k.wheel_bones)
    obj=k.join('HULL');bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    bounds=[obj.matrix_world@Vector(v) for v in obj.bound_box]
    bbox=[tuple(min(v[i] for v in bounds) for i in range(3)),tuple(max(v[i] for v in bounds) for i in range(3))]
    tris=sum(len(p.vertices)-2 for p in obj.data.polygons)
    portrait(obj,args.review/(label+'.tga'))
    pipe.smart_uv(obj,contract.get('uv_margin',.009))
    diff,ao,mask=pipe.bake_images(obj,res)
    tga=args.data/'Art/Textures'/(texture+'.tga')
    recipe=dict(seed=sum(map(ord,model)),shade_lo=.52,shade_hi=.48,grain=.012,edge_strength=.32,edge_radius=1,lowfreq=.024)
    recipe.update(contract.get('composite',{}))
    pipe.composite(diff,ao,mask,res,str(tga),**recipe)
    # Clear mask-bake emission; the final W3D uses one painted atlas.
    image=bpy.data.images.load(str(tga));image.name=texture
    mat=bpy.data.materials.new(texture+'_skin')
    bsdf=mat.node_tree.nodes['Principled BSDF'];bsdf.inputs['Roughness'].default_value=.87
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
    mat.node_tree.links.new(bsdf.inputs['Base Color'],tex.outputs['Color'])
    obj.data.materials.clear();obj.data.materials.append(mat)
    groups=contract.get('bones') or ({'HULL':(0,0,0),'TURRET':contract['turret']} if contract.get('turret') else {})
    names=[g for g in groups if obj.vertex_groups.get(g)]
    for ix,name in enumerate(names):
        vg=obj.vertex_groups.get(name)
        if vg is None:raise ValueError('Missing vertex group '+name)
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
        for v in obj.data.vertices:v.select=any(g.group==vg.index for g in v.groups)
        if ix<len(names)-1:
            bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
            piece=next(o for o in bpy.context.selected_objects if o!=obj)
        else:piece=obj
        # Free HULL before assigning that name to a separated piece.
        if piece!=obj and name==obj.name:obj.name='REMAINDER'
        piece.name=name;piece.data.name=name
        bpy.ops.object.select_all(action='DESELECT');piece.select_set(True);bpy.context.view_layer.objects.active=piece
        bpy.context.scene.cursor.location=groups[name];bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    for o in bpy.context.scene.objects:
        if o.type=='MESH':o.vertex_groups.clear()
    # Exporter derives model container from the filename and pivots from mesh origins.
    w3d=args.data/'Art/W3D'/(model+'.w3d')
    bpy.ops.export_mesh.westwood_w3d(filepath=str(w3d),file_format='W3D',export_mode='HM',force_vertex_materials=True)
    final_w3d(w3d,model.upper(),contract)
    role=contract.get('asset_role') or ('infantry' if contract.get('hierarchy') else ('vehicle' if contract.get('turret') or model.endswith('haul01') else 'environment'))
    contract.update(model=model.upper(),portrait=label,texture=texture,triangles=tris+12*len(contract.get('house',[])),bounds=bbox,
                    source='tools/blender/build_polish.py',role=role,origin='original',
                    required_states=['idle','move','attack'] if role=='infantry' else (['turret','muzzle','player-color'] if contract.get('turret') else ['default']),
                    texture_size=optimize_art.shipped_size(texture,res),bake_size=res)
    print('ASSET_OK',json.dumps(contract),flush=True)
    return contract

def check(selected,reference):
    """Rebuild ``selected`` into a temporary tree, run the optimize step and
    compare every W3D/TGA with the copy under ``reference``. Returns failures."""
    failures=[]
    with tempfile.TemporaryDirectory(prefix='warpowers-polish-check-') as temp:
        scratch=argparse.Namespace(data=Path(temp)/'data',review=Path(temp)/'review')
        for p in (scratch.data/'Art/W3D',scratch.data/'Art/Textures',scratch.review):p.mkdir(parents=True)
        for model in selected:
            contract=build(model,ASSETS[model],scratch)
            texture=contract['texture']
            produced={f'Art/W3D/{model}.w3d':(scratch.data/'Art/W3D'/f'{model}.w3d').read_bytes(),
                      f'Art/Textures/{texture}.tga':optimize_art.optimized_bytes(scratch.data/'Art/Textures'/f'{texture}.tga',scratch.data)}
            for relative,data in produced.items():
                committed=reference/relative
                if not committed.exists():failures.append(f'{model}: {relative} is not in {reference}')
                elif committed.read_bytes()!=data:failures.append(f'{model}: {relative} differs from {committed}')
                else:print('CHECK_OK',relative,flush=True)
    for failure in failures:print('CHECK_DIFF',failure,flush=True)
    return failures

def main(argv=None):
    ap=argparse.ArgumentParser(description='Build the painted War Powers production assets (run inside Blender).')
    ap.add_argument('--data',type=Path,default=ROOT/'data',help='dataset root to write, or the reference for --check')
    ap.add_argument('--review',type=Path,default=Path('/tmp/warpowers-art-review'),help='portrait renders and the build manifest')
    ap.add_argument('--only',default='',help='comma-separated model ids (default: every catalog model)')
    ap.add_argument('--catalog-only',action='store_true',help='Refresh catalog metadata from existing exports without rebuilding')
    ap.add_argument('--check',action='store_true',help='rebuild into a temporary directory, optimize, and diff against --data; writes nothing')
    args=ap.parse_args(script_args(argv))
    args.data=args.data.resolve();args.review=args.review.resolve()
    selected=[m.strip().lower() for m in args.only.split(',')] if args.only else list(ASSETS)
    if args.catalog_only:selected=[]
    unknown=set(selected)-set(ASSETS)
    if unknown:ap.error('Unknown model(s): '+', '.join(sorted(unknown)))
    if args.check:
        failures=check(selected,args.data)
        print(f'CHECK_DONE {len(selected)-len(failures)} of {len(selected)} models reproduce {args.data}',flush=True)
        if failures:raise SystemExit(1)
        return
    for p in [args.data/'Art/W3D',args.data/'Art/Textures',args.review]:p.mkdir(parents=True,exist_ok=True)
    manifest={}
    manifestpath=args.review/'asset-contracts.json'
    catalogpath=ROOT/'tools/blender/polish_assets.json'
    # The committed catalog is authoritative; a stale scratch render must not
    # remove production entries or restore superseded texture resolutions.
    if catalogpath.exists():manifest=json.loads(catalogpath.read_text())
    for model in selected:
        manifest[model]=build(model,ASSETS[model],args)
        manifestpath.write_text(json.dumps(manifest,indent=2)+'\n')
    # This tracked build manifest feeds the content registry and documents the
    # engine-facing contract without guessing from filenames or historical prose.
    for model,contract in manifest.items():
        if model not in ASSETS:continue
        label,texture,_,res=ASSETS[model]
        role=contract.get('asset_role') or ('infantry' if contract.get('hierarchy') else ('vehicle' if contract.get('turret') or model.endswith('haul01') else 'environment'))
        states=['idle','move','attack','death'] if role=='infantry' else (['turret','muzzle','player-color'] if contract.get('turret') else ['default'])
        if model.endswith('haul01'):states=['default','cargo','player-color']
        if contract.get('barrel'):states+=['recoil']
        if contract.get('wheels'):states+=['wheel-motion']
        contract.update(source='tools/blender/build_polish.py',origin='original',
                        portrait=label,texture=texture,texture_size=optimize_art.shipped_size(texture,res),bake_size=res,
                        role=role,required_states=states)
        for source,kit in GEOMETRY_SOURCES:
            if model in kit:contract['geometry_source']=source
        w3d=args.data/'Art/W3D'/(model+'.w3d')
        if w3d.exists():
            contract['triangles']=sum(struct.unpack_from('<I',q,40)[0]
                for c,s,p in chunks(w3d.read_bytes()) if c==MESH
                for d,t,q in chunks(p) if d==MESH_HEADER3)
    manifestpath.write_text(json.dumps(manifest,indent=2)+'\n')
    # Scratch exports carry a scratch catalog. Only production exports update
    # the tracked metadata used by the release validator.
    if args.data==(ROOT/'data').resolve():
        catalogpath.write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()
