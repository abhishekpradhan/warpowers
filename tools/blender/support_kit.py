"""Original aircraft and support architecture for build_polish.py.

+X is forward. Everything is authored here; no imported geometry or images.
"""
import math
import bpy


def plate(k,name,mat,points,z,thickness=.35):
    n=len(points)
    vertices=[(x,y,z+dz) for dz in (-thickness/2,thickness/2) for x,y in points]
    faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj)
    return k._register(obj,mat)


def fan(k,x,y,z,r,mat='steel'):
    # Hollow duct, dark fan cavity and a readable central hub.
    for i in range(16):
        a=i*math.tau/16;b=(i+1)*math.tau/16
        k.beam('DUCT',mat,(x+r*math.cos(a),y+r*math.sin(a),z),(x+r*math.cos(b),y+r*math.sin(b),z),.46)
    k.cyl('FAN','dark',x,y,z-.13,r*.88,.14,verts=16)
    for i in range(4):
        a=i*math.pi/4
        k.box('ROTOR','bare',x,y,z+.02,r*1.65,.19,.12,rot=(0,0,a))
    k.cyl('HUB',mat,x,y,z+.19,.42,.36,verts=8)


def aircraft(k,kind):
    jackal=kind in ('buzzard','gnat');body='sand' if jackal else 'ivory';trim='olive' if jackal else 'gold'
    if kind=='kestrel':
        # Broad ducted-fan attack craft with a long armored beak.
        k.prism('FUSELAGE',body,[(-7,2),(-7,3.5),(-3,4.5),(3,4.5),(8.5,2.6),(7,1.7)],-2.15,2.15)
        k.prism('COCKPIT','glass',[(0,4.45),(1.2,5.4),(3.2,5.3),(5.2,3.95)],-1.25,1.25)
        for s in (-1,1):
            plate(k,'WING','steel',[(-4,s*2),(-3.5,s*7.3),(1,s*8),(2,s*2)],3)
            fan(k,-1,s*7.1,3.8,2.65)
            k.cyl('MISSILE','dark',1.3,s*3.5,2,.52,5.8,axis='X',verts=10)
            k.cyl('NOSE',trim,4.25,s*3.5,2,.52,.6,axis='X',verts=10)
            k.prism('TAIL',trim,[(-7,3),(-6,6),(-4.4,5.6),(-4,3)],s*1.7-.18,s*1.7+.18)
        k.cyl('CHINGUN','dark',6.1,0,1.72,.23,5.3,axis='X',verts=8)
        mark=(-3.7,0,4.5,1.8,2.5,.08)
    elif kind=='shrike':
        # Slender swept-wing interceptor/strafer, twin rear jets, no ducts.
        k.prism('FUSELAGE',body,[(-6,2.3),(-6,3.3),(-2,4.15),(2.8,3.75),(8.1,2.3),(4,1.6)],-1.3,1.3)
        k.prism('CANOPY','glass',[(0,4.08),(1.2,4.9),(3,4.25),(4.2,3.13)],-.88,.88)
        for s in (-1,1):
            plate(k,'SWEPTWING','steel',[(1.7,s*1),(-3.4,s*8),(-6,s*7),(-4.7,s*1)],2.9)
            plate(k,'WINGTIP',trim,[(-2.5,s*6.8),(-3.4,s*8),(-6,s*7),(-5.7,s*6.1)],3.13,.14)
            k.cyl('ENGINE','dark',-4.5,s*1.65,2.55,.92,4.6,axis='X',verts=12)
            k.cyl('EXHAUST','bare',-6.85,s*1.65,2.55,.83,.28,axis='X',verts=12)
            k.cyl('NOZZLE','dark',-7,s*1.65,2.55,.57,.09,axis='X',verts=10)
            k.cyl('GUNPOD','dark',1.3,s*3,2.15,.28,5.8,axis='X',verts=8)
            k.prism('VTAIL',body,[(-6,3),(-5.7,6.4),(-3.9,5.4),(-3.8,3)],s*1.35-.13,s*1.35+.13)
        mark=(-1.8,0,4.07,1.5,1.45,.10)
    elif kind=='buzzard':
        # Heavy tandem-rotor gun rig: long transport cabin and exposed tail boom.
        k.box('BELLY','dark',0,0,1.8,12,4.9,1.3,bevel=.32)
        k.prism('CABIN',body,[(-6,2),(-6,4.2),(-3,5.1),(2.9,5.1),(5.9,3.5),(5.9,2)],-2.3,2.3)
        k.prism('WINDSCREEN','glass',[(3,5.1),(5.98,3.5),(6,3.45),(3.08,5.16)],-1.8,1.8)
        for s in (-1,1):
            for x in (-3.3,-.5):k.box('WINDOW','glass',x,s*2.34,4.1,1.8,.12,1.1,bevel=.1)
            k.cyl('ROCKETPOD','rust',2.4,s*3.4,2.7,.95,4.1,axis='X',verts=10)
            for dy,dz in [(-.35,-.35),(.35,-.35),(0,.35)]:k.cyl('ROCKET','dark',4.48,s*3.4+dy,2.7+dz,.23,.15,axis='X',verts=8)
            k.beam('SKID','dark',(-5,s*2.8,.6),(4,s*2.8,.6),.45)
            for x in (-3,3):k.beam('GEAR','dark',(x,s*2.8,.6),(x,s*1.6,2),.32)
        for x,z in [(-4.5,6.5),(3.5,6.0)]:
            k.box('GEARBOX','rust',x,0,z-.6,2.8,2.5,1.3,bevel=.3)
            k.cyl('ROTORHUB','bare',x,0,z+.3,.4,1.2,verts=10)
            for a in (.25,1.82):k.box('ROTOR','dark',x,0,z+.8,12,.62,.14,rot=(0,0,a))
        mark=(-.3,0,5.17,1.7,2.6,.1)
    else:
        # Compact four-duct drone; no cockpit and no helicopter tail.
        k.sphere('POD',body,(0,0,2.7),(2.9,1.9,1.75),2)
        k.box('BATTERY','olive',-1,0,3.8,2.5,1.7,1.05,bevel=.35)
        for x in (-2.8,2.8):
            for y in (-3.5,3.5):
                k.beam('BOOM','rust',(0,0,2.8),(x,y,3.2),.42)
                fan(k,x,y,3.3,1.55,'rust')
        k.sphere('SENSOR','dark',(2.4,0,2.3),(.85,.95,.75),2)
        k.box('LENS','lens',3.13,0,2.4,.18,1.18,.40,bevel=.06)
        k.cyl('CHINGUN','dark',2.6,0,1.5,.22,2.9,axis='X',verts=8)
        for s in (-1,1):k.beam('SKID','dark',(-1.8,s*1.7,.5),(2,s*1.7,.5),.28)
        mark=(-.9,0,4.38,1.6,1.2,.10)
    return dict(asset_role='aircraft',house=[mark])


def crate(k,x,y,z,mat='olive',s=3):
    k.box('CRATE',mat,x,y,z+s/2,s,s,s,bevel=.13)
    for dx in (-s*.28,s*.28):k.box('BAND','dark',x+dx,y,z+s+.06,.15,s+.08,.12)


def shutters(k,x,y,z,width=6,height=6):
    k.box('DOOR','dark',x,y,z,width,.3,height,bevel=.1)
    for i in range(7):k.box('SHUTTER','bare',x,y-.2,z-height*.4+i*height*.13,width-.55,.13,.19)
    k.box('DOORLIGHT','lens',x,y-.32,z+height*.58,width*.7,.16,.15)


def building(k,kind,jackal=False):
    body='sand' if jackal else 'ivory';trim='olive' if jackal else 'gold';metal='rust' if jackal else 'steel'
    if kind=='pad':
        k.box('FOUNDATION',metal,0,0,1.1,39 if not jackal else 37,33 if not jackal else 31,2.2,bevel=.7)
        if not jackal:
            k.cyl('LANDING','dark',0,0,2.4,13.8,.45,verts=24)
            for i in range(12):
                a=i*math.tau/12
                k.box('LANDINGMARK',trim,11.7*math.cos(a),11.7*math.sin(a),2.67,2.2,.45,.08,rot=(0,0,a+math.pi/2))
        else:
            for y in range(-11,12,2):k.box('DECK','bare',0,y,2.4,25,1.75,.4)
            for s in (-1,1):k.box('PADMARK',trim,s*6,0,2.68,.5,17,.08)
        k.box('MARK',trim,0,0,2.72,12,.65,.10)
        k.box('TOWER',body,-15,10,7.1,6,7,10,bevel=.55)
        k.box('CABIN','glass',-15,10,13,5.7,6.7,2.1,bevel=.4)
        k.box('CANOPY',metal,-15,10,14.35,7,8,.55,bevel=.2)
        k.cyl('BEACON','dark',-15,10,16.4,.28,3.7,verts=8)
        k.cyl('BEACONLIGHT','red',-15,10,18.3,.56,.5,verts=8)
        for x,y in [(16,12),(16,-12),(-16,-12)]:k.cyl('EDGELIGHT','lens',x,y,2.8,.4,.55,verts=8)
        for x in (10,14):k.cyl('FUEL',metal,x,-12,4.2,1.55,3.5,verts=12)
        k.beam('FUELPIPE','dark',(10,-12,5.8),(14,-12,5.8),.3)
        mark=(-15,10,14.66,3.1,3.3,.10)
    elif kind=='economy':
        k.box('APRON','concrete',0,0,.75,27,23,1.5,bevel=.6)
        k.box('WAREHOUSE',body,-2,2,5.7,19,16,10,bevel=.5)
        if jackal:
            k.prism('GABLEROOF','rust',[(-12,10.4),(-2,14),(8,10.4)],-6.6,10.7)
            for x in range(-11,9,2):k.beam('ROOFRIB','bare',(x,-6.7,14-abs(x+2)*.36),(x,10.8,14-abs(x+2)*.36),.18)
            k.box('AWNING','olive',0,-9,8.0,19,6,.25,rot=(.09,0,0))
            for x in (-8,8):k.cyl('AWNINGPOST','dark',x,-11,4,.18,8,verts=6)
        else:
            k.box('ROOFCAP',metal,-2,2,11.1,20.5,17.5,.8,bevel=.3)
            k.box('ROOFSTRIPE',trim,-2,2,11.6,2.5,14,.1)
            k.box('HVAC','steel',-6,5,12.2,5,5,1.8,bevel=.25);k.vents(-8,5,13.14,n=6,length=3)
        for x in (-6,3):shutters(k,x,-6.13,5,width=6.4,height=7.2)
        k.box('LOADINGRAMP',metal,-2,-9,.95,19,5,.8,rot=(.12,0,0))
        for y in (0,5):crate(k,10,y,.8,trim,s=3.5)
        k.box('OFFICE','dark',10,-6,4,4.3,5,6,bevel=.25)
        k.box('DISPLAY','lens',10,-8.6,5,2.4,.1,1.2)
        mark=(-2,2,14.04 if jackal else 11.7,3.8,3.3,.10)
    elif kind=='tech':
        k.box('FOUNDATION','concrete',0,0,.8,27,22,1.6,bevel=.5)
        if jackal:
            # Quonset bunker with external utility pipes and a satellite dish.
            k.cyl('VAULT','sand',-1,0,4.3,8.9,17,axis='Y',verts=16)
            k.box('BASEFILL','sand',-1,0,2.5,17.8,17,5)
            for y in (-8,-4,0,4,8):
                for i in range(8):
                    a=i*math.pi/8;b=(i+1)*math.pi/8
                    k.beam('ARCH','rust',(-1+9*math.cos(a),y,4.3+9*math.sin(a)),(-1+9*math.cos(b),y,4.3+9*math.sin(b)),.32)
            for x,y in [(10,-5),(-11,5)]:
                k.cyl('PIPE','rust',x,y,7,.65,12,verts=8)
                k.cyl('ELBOW','rust',x-1,y,13,.65,2.8,axis='X',verts=8)
            k.cyl('DISHSUPPORT','dark',1,2,14,.38,4,verts=8)
            k.sphere('DISH','olive',(1,2,16),(3.5,3.5,.72),2)
            k.beam('FEED','bare',(1,2,16),(1,2,18),.15)
            shutters(k,-1,-8.7,4.7,width=8,height=7)
            mark=(-1,0,13.27,3.7,3.5,.10)
        else:
            k.box('CONTROL',body,-3,0,8.4,17,17,15,bevel=1.0)
            k.box('WINDOWBAND','glass',-3,0,11.8,17.1,17.1,2.1,bevel=.65)
            for x in (-9,-3,3):k.box('PIER',metal,x,-8.6,11.8,.52,.24,2.5)
            k.box('ROOFCAP',trim,-3,0,16.4,18,18,.7,bevel=.3)
            k.box('LAB','steel',10,1,4.5,8,14,8,bevel=.5)
            k.vents(8,1,8.6,n=7,length=10)
            k.sphere('RADOME','ivory',(-3,0,19.2),(4.2,4.2,3.8),2)
            for x in (-10,4):k.cyl('ANTENNA','dark',x,6,20,.14,8,verts=6)
            shutters(k,-3,-8.64,4.6,width=5,height=6)
            mark=(9,1,8.66,3,5,.10)
    else:
        # Dynamo: exposed twin generating turbines, maintenance hut and stacks.
        k.box('PLINTH','concrete',0,0,1,25,20,2,bevel=.6)
        k.box('SERVICE','sand',-7,0,5.7,9,14,9,bevel=.5)
        shutters(k,-7,-7.15,5,width=5,height=6)
        k.box('ROOF','rust',-7,0,10.5,10,15,.6,bevel=.2)
        for y in (-4.5,4.5):
            k.cyl('TURBINE','olive',3,y,5.1,3.1,12,axis='X',verts=14)
            for x in (-1,4,8):k.cyl('RIB','bare',x,y,5.1,3.22,.24,axis='X',verts=14)
            k.cyl('INTAKE','dark',9.15,y,5.1,2.54,.25,axis='X',verts=14)
            for z in (4,5.1,6.2):k.box('GRILLE','rust',9.35,y,z,.13,4.3,.19)
        for x,h in [(-8,18),(-3,14)]:
            k.cyl('STACK','rust',x,5,h/2+1,1.2,h,verts=12)
            k.cyl('STACKRIM','bare',x,5,h+1,1.44,.5,verts=12)
            k.cyl('STACKDARK','dark',x,5,h+1.27,1.05,.08,verts=12)
        mark=(-7,-1,10.86,3.4,4,.10)
    return dict(asset_role='structure',house=[mark])


def sandbags(k,r=8,z=1.3):
    for row in range(2):
        for i in range(14):
            a=(i+row*.5)*math.tau/14
            k.box('SANDBAG','sand',r*math.cos(a),r*math.sin(a),z+row*1.25,3.6,1.7,1.2,bevel=.48,rot=(0,0,a+math.pi/2))


def defense(k,kind,jackal=False):
    body='sand' if jackal else 'ivory';trim='olive' if jackal else 'gold';metal='rust' if jackal else 'steel'
    if kind=='pillbox':
        if jackal:
            k.cyl('PIT','dark',0,0,.65,7.2,1.3,verts=14);sandbags(k,7.7,.9)
            k.box('BACKSHIELD','rust',-5,0,4.8,1,9,6,bevel=.15)
            k.box('CANOPY','olive',-1.3,0,6.8,8,9,.3,rot=(0,-.11,0))
            crate(k,-4,-5,2.8,'rust',2.4)
        else:
            k.prism('BUNKER','steel',[(-8,0),(-8,5.9),(-6,7.7),(5.5,7.7),(8,4.9),(8,0)],-7,7)
            k.box('ROOF','ivory',-1,0,7.9,12.5,12.5,.8,bevel=.4)
            k.box('SLIT','dark',7.95,0,4.1,.12,9.5,1.2)
            k.vents(-5,0,8.36,n=5,length=5)
        k.cyl('GUN','dark',8.6,0,4.15,.29,4.5,axis='X',verts=10)
        return dict(asset_role='structure',house=[(-1,0,6.85 if jackal else 8.36,2.4,3,.12)])
    k.box('FOUNDATION','concrete',0,0,1,20,20,2,bevel=.8)
    if jackal:sandbags(k,8.5,1.6)
    if kind=='aa':
        if jackal:
            k.box('HUT','rust',0,0,4.3,13,11,5.3,bevel=.4)
            k.box('HATCH','olive',-3,-4,7.1,3.2,3.2,.45)
            z=7
        else:
            k.cyl('PEDESTAL','steel',0,0,3.3,6.8,4.6,verts=12)
            k.prism('MAST','ivory',[(-2.4,4.7),(-1.5,15),(1.5,15),(2.4,4.7)],-2.4,2.4)
            for y in (-6,6):k.box('EQUIPMENT','dark',0,y,3.3,5,2.1,3.5,bevel=.3)
            z=15
        k.group='TURRET';k.cyl('RING','dark',0,0,z,3.3,.55,verts=12)
        k.box('HEAD',body,0,0,z+1.4,5,5,2.6,bevel=.55)
        if jackal:
            for y in (-1.2,1.2):
                k.cyl('AMMODRUM','olive',-1,y*2.1,z+1.4,1.25,1.1,axis='Y',verts=12)
                for dz in (.8,1.8):
                    k.cyl('GUN','dark',3.4,y,z+dz,.28,7.2,axis='X',verts=10)
                    k.cyl('MUZZLEBRAKE','bare',7,y,z+dz,.38,.35,axis='X',verts=10)
            muzzle=(7.3,0,z+1.2)
        else:
            for y in (-2.2,2.2):
                k.box('MISSILEPOD','steel',2.8,y,z+2.3,7.2,2.6,2.5,bevel=.4,rot=(0,-.13,0))
                for dy in (-.55,.55):k.cyl('MISSILE',trim,6.45,y+dy,z+2.77,.38,.3,axis='X',verts=8)
            k.cyl('RADAR','gold',-3.1,0,z+3.4,1.7,.4,axis='X',verts=12)
            muzzle=(6.8,0,z+2.8)
        return dict(asset_role='structure',turret=(0,0,z),muzzle=muzzle,house=[(-6,-6,2.07,2.4,2.4,.12)])
    # Artillery: a precision long gun versus a vertical improvised mortar.
    k.cyl('TURNPLATE',metal,0,0,2.5,6.2,1,verts=16)
    for s in (-1,1):
        k.box('OUTRIGGER','dark',-5,s*7.8,2.1,7,2,1.8)
        k.cyl('JACK',metal,-7,s*7.8,2.4,.8,4.5,verts=8)
    k.group='TURRET'
    k.box('CRADLE',body,-1,0,5,7.5,6.5,4,bevel=.6)
    if jackal:
        k.cyl('MORTAR','dark',.8,0,8.2,1.6,10.5,verts=14)
        k.cyl('RIM','olive',.8,0,13.4,1.9,.75,verts=14)
        k.cyl('BORE','black',.8,0,13.81,1.25,.09,verts=14)
        for y in (-2.4,2.4):k.beam('BRACE','rust',(-3,y,3),(0.8,y,11),.6)
        muzzle=(.8,0,14)
    else:
        k.box('BREECH','steel',-4,0,6.3,5,4,4,bevel=.35)
        k.cyl('GUN','dark',6.3,0,7.5,.69,20,axis='X',verts=12)
        k.cyl('SLEEVE','ivory',0,0,7.5,1.07,7,axis='X',verts=12)
        k.box('BRAKE','gold',16.4,0,7.5,1.75,1.8,1.8,bevel=.23)
        k.box('SIGHT','glass',0,-3,7.2,2,.5,1.2)
        muzzle=(17.4,0,7.5)
    k.group='HULL';crate(k,6,-6,2,metal,3)
    return dict(asset_role='structure',turret=(0,0,3.1),muzzle=muzzle,house=[(6,6,2.07,2.4,2.4,.12)])


def base_defense(k,jackal=False):
    if jackal:
        k.box('PAD','dark',0,0,.8,14,14,1.6,bevel=.4)
        for x in (-3.4,3.4):
            for y in (-3.4,3.4):k.box('LEG','rust',x,y,6.5,1.2,1.2,11)
        for y in (-3.4,3.4):
            k.beam('CROSSBRACE','dark',(-3.4,y,2),(3.4,y,10.9),.38)
            k.beam('CROSSBRACE','dark',(3.4,y,2),(-3.4,y,10.9),.38)
        k.box('DECK','sand',0,0,12.6,10.5,10.5,1.2,bevel=.2)
        for x,y,sx,sy in [(0,4.8,10.5,.7),(0,-4.8,10.5,.7),(4.8,0,.7,9),(-4.8,0,.7,9)]:
            k.box('WALL','rust',x,y,14.4,sx,sy,2.4,bevel=.1)
        k.box('TARP','olive',-2.5,2.5,16.2,4.5,3.5,.6,rot=(.05,-.06,.1))
        k.group='TURRET';k.box('MOUNT','dark',0,0,15.4,2.4,2.4,1.4,bevel=.2)
        for y in (-.7,.7):k.cyl('GUN','dark',3.2,y,15.7,.32,5,axis='X',verts=10)
        return dict(asset_role='structure',turret=(0,0,14.8),muzzle=(5.9,0,15.7),house=[(0,-5.2,14.5,3.8,.10,1.4)])
    k.box('PAD','dark',0,0,.9,16,16,1.8,bevel=.5)
    k.cyl('DRUM','ivory',0,0,4.4,6.2,5.2,verts=12)
    k.cyl('TRIM','gold',0,0,7.2,6.4,.8,verts=12)
    for y in (-5.8,5.8):k.box('VENT','dark',0,y,4.5,3,.25,1.3)
    k.group='TURRET';k.box('HEAD','steel',0,0,9.2,7.5,6.5,3.4,bevel=.5)
    k.cyl('BARREL','dark',6.4,0,9.2,.55,8,axis='X',verts=12)
    k.cyl('BRAKE','bare',10,0,9.2,.8,1.2,axis='X',verts=10)
    k.box('SENSOR','glass',2.4,2.6,11.2,1.6,1.4,.9,bevel=.1)
    k.cyl('ANTENNA','dark',-2.6,-2.4,11.8,.12,2.4,verts=6)
    return dict(asset_role='structure',turret=(0,0,7.7),muzzle=(10.7,0,9.2),house=[(-6,-6,1.87,2.5,2.5,.10)])


ASSETS={
 'merjet01':('kestrel','wp_kestrel',lambda k:aircraft(k,'kestrel'),256),
 'merjet02':('shrike','wp_shrike',lambda k:aircraft(k,'shrike'),256),
 'jakjet01':('buzzard','wp_buzzard',lambda k:aircraft(k,'buzzard'),256),
 'jakjet02':('gnat','wp_gnat',lambda k:aircraft(k,'gnat'),256),
 'jakpwr01':('dynamo','wp_dynamo',lambda k:building(k,'power',True),256),
 'merbul01':('bulwark','wp_bulwark',lambda k:base_defense(k),256),
 'jakwp01':('watchpost','wp_watchpost',lambda k:base_defense(k,True),256),
}
for kind,suffix,mer,jak in [('pad','pad01','launchpad','roost'),('economy','ex01','exchange','racket'),
                           ('tech','tech01','directorate','den')]:
    ASSETS['mer'+suffix]=(mer,'wp_'+mer,lambda k,t=kind:building(k,t),256)
    ASSETS['jak'+suffix]=(jak,'wp_'+jak,lambda k,t=kind:building(k,t,True),256)
for kind,suffix,mer,jak in [('aa','aa01','skyspear','flakhut'),('pillbox','pill01','rampart','nest'),
                           ('artillery','art01','longbow','lobber')]:
    ASSETS['mer'+suffix]=(mer,'wp_'+mer,lambda k,t=kind:defense(k,t),256)
    ASSETS['jak'+suffix]=(jak,'wp_'+jak,lambda k,t=kind:defense(k,t,True),256)
