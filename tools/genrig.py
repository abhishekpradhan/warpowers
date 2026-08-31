#!/usr/bin/env python3
"""War Powers rigged-infantry generator — hierarchy + animations + bone-bound
models, in the engine's own W3D chunk dialect (structs per w3d_file.h, loader
behavior per htree/hrawanim/hlod.cpp).

Design: ONE shared skeleton (WPINF1) for every infantry body; per-model files
carry only meshes (bone-LOCAL coordinates) + an HLOD whose HierarchyName binds
them. Animation = rigid part motion (no skinning): the engine composes
base pose x anim DELTA per pivot (HTreeClass::Anim_Update), so channels
author swings around zero.

File layout follows the engine's load-on-demand rules exactly:
  wpinf1.w3d        HIERARCHY WPINF1        (Get_HTree loads "<hier>.w3d")
  wpinf1wlk.w3d     ANIMATION WPINF1WLK     (Get_HAnim "A.B" loads "<B>.w3d")
  wpinf1idl.w3d     ANIMATION WPINF1IDL
  wpinf1fir.w3d     ANIMATION WPINF1FIR
  merinf02.w3d ...  meshes + HLOD(hier=WPINF1), one per infantry body
"""
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from genw3d import chunk, frustum, mesh_chunk, name32

# ---- chunk ids (hierarchy/animation family) ----
HIERARCHY, HIERARCHY_HEADER, PIVOTS = 0x100, 0x101, 0x102
ANIMATION, ANIMATION_HEADER, ANIMATION_CHANNEL = 0x200, 0x201, 0x202
HLOD, HLOD_HEADER, HLOD_LOD_ARRAY = 0x700, 0x701, 0x702
SUB_OBJECT_ARRAY_HEADER, HLOD_SUB_OBJECT = 0x703, 0x704

VERSION41 = 0x00040001
CH_X, CH_Y, CH_Z, CH_Q = 0, 1, 2, 6

# ---- the shared infantry skeleton ----
# (name, parent index, WORLD position); loader wants parent -1 on pivot 0.
# Proportions mirror genw3d.trooper() so the rigged bodies read as the same
# species as the old static minifigs.
SKEL_NAME = "WPINF1"
PIVOTS_DEF = [
    ("ROOTTRANSFORM", -1, (0.0, 0.0, 0.0)),
    ("TORSO",          0, (0.0, 0.0, 2.6)),
    ("HEAD",           1, (0.0, 0.0, 5.6)),
    ("ARML",           1, (-0.2, -1.7, 3.9)),
    ("ARMR",           1, (-0.2,  1.7, 3.9)),
    ("LEGL",           0, (-0.4, -0.75, 2.6)),
    ("LEGR",           0, (-0.4,  0.75, 2.6)),
    ("GUN",            1, (1.2, 0.6, 3.65)),
]
PIV = {name: i for i, (name, _, _) in enumerate(PIVOTS_DEF)}
WORLD = {name: pos for name, _, pos in PIVOTS_DEF}

def hierarchy_w3d():
    head = struct.pack("<I16sI3f", VERSION41, SKEL_NAME.encode(), len(PIVOTS_DEF),
                       0.0, 0.0, 0.0)
    pivs = b""
    for name, parent, pos in PIVOTS_DEF:
        pw = WORLD[PIVOTS_DEF[parent][0]] if parent >= 0 else (0.0, 0.0, 0.0)
        local = tuple(a - b for a, b in zip(pos, pw))
        pivs += struct.pack("<16sI3f3f4f", name.encode(),
                            parent & 0xFFFFFFFF,
                            *local, 0.0, 0.0, 0.0,       # euler unused by loader
                            0.0, 0.0, 0.0, 1.0)          # identity quat (x,y,z,w)
    return chunk(HIERARCHY,
                 chunk(HIERARCHY_HEADER, head) + chunk(PIVOTS, pivs), subs=True)

# ---- animation authoring ----
def qy(a):
    """quaternion for rotation about +Y (leg/arm swing axis), (x,y,z,w)"""
    return (0.0, math.sin(a / 2.0), 0.0, math.cos(a / 2.0))

def channel(pivot, ctype, frames):
    """frames: list of float (X/Y/Z) or 4-tuple (Q)"""
    veclen = 4 if ctype == CH_Q else 1
    data = b""
    for f in frames:
        vals = f if isinstance(f, tuple) else (f,)
        assert len(vals) == veclen
        data += struct.pack(f"<{veclen}f", *vals)
    head = struct.pack("<6H", 0, len(frames) - 1, veclen, ctype, pivot, 0)
    return chunk(ANIMATION_CHANNEL, head + data)

def animation_w3d(anim_name, nframes, fps, channels):
    head = struct.pack("<I16s16sII", VERSION41, anim_name.encode(),
                       SKEL_NAME.encode(), nframes, fps)
    return chunk(ANIMATION,
                 chunk(ANIMATION_HEADER, head) + b"".join(channels), subs=True)

def sine(nframes, amp, cycles=1.0, phase=0.0):
    return [amp * math.sin(2 * math.pi * (cycles * i / nframes) + phase)
            for i in range(nframes)]

def walk_anim():
    N, FPS = 16, 24                       # ~0.66s stride cycle
    swing = 0.55                          # leg amplitude (rad)
    legL = [qy(a) for a in sine(N, swing)]
    legR = [qy(a) for a in sine(N, swing, phase=math.pi)]
    armL = [qy(a) for a in sine(N, -0.28, phase=math.pi)]
    armR = [qy(a) for a in sine(N, -0.28)]
    bob = [abs(v) for v in sine(N, 0.14, cycles=1.0)]   # two touchdowns/cycle
    return animation_w3d("WPINF1WLK", N, FPS, [
        channel(PIV["LEGL"], CH_Q, legL),
        channel(PIV["LEGR"], CH_Q, legR),
        channel(PIV["ARML"], CH_Q, armL),
        channel(PIV["ARMR"], CH_Q, armR),
        channel(PIV["TORSO"], CH_Z, bob),
    ])

# stride length for INI DistanceCovered: 2 * legLen * sin(swing) per half step
STRIDE = 2 * 2.6 * math.sin(0.55) * 2

def idle_anim():
    N, FPS = 32, 10                       # slow breathing
    return animation_w3d("WPINF1IDL", N, FPS, [
        channel(PIV["TORSO"], CH_Z, sine(N, 0.06)),
        channel(PIV["ARML"], CH_Q, [qy(a) for a in sine(N, 0.04)]),
        channel(PIV["ARMR"], CH_Q, [qy(a) for a in sine(N, 0.04)]),
    ])

def fire_anim():
    N, FPS = 8, 24                        # brace + recoil kick, loops per shot
    kick = [-0.5, -0.30, -0.16, -0.08, -0.04, -0.02, -0.01, 0.0]
    brace = [qy(-0.10)] * N
    return animation_w3d("WPINF1FIR", N, FPS, [
        channel(PIV["GUN"], CH_X, kick),
        channel(PIV["ARML"], CH_Q, brace),
        channel(PIV["ARMR"], CH_Q, brace),
    ])

# ---- rigged bodies ----
def rpart(bone, name, color, cx, cy, z, sx, sy, sz, **kw):
    """part authored in WORLD coords, stored bone-local."""
    px, py, pz = WORLD[bone]
    return (PIV[bone], name, color,
            frustum(cx - px, cy - py, z - pz, sx, sy, sz, **kw))

def rifle_body(uniform, trim, skin=(214, 178, 148)):
    GUNC = (70, 74, 80)
    return [
        rpart("LEGL", "LEGL", trim, -0.4, -0.75, 0, 1.4, 1.1, 2.6),
        rpart("LEGR", "LEGR", trim, -0.4, 0.75, 0, 1.4, 1.1, 2.6),
        rpart("TORSO", "TORS", uniform, 0, 0, 2.6, 2.2, 3.0, 2.8),
        rpart("ARML", "ARML", uniform, 0.9, -1.7, 3.2, 2.6, 0.9, 1.0),
        rpart("ARMR", "ARMR", uniform, 0.9, 1.7, 3.2, 2.6, 0.9, 1.0),
        rpart("HEAD", "HEAD", skin, 0, 0, 5.6, 1.6, 1.6, 1.5),
        rpart("HEAD", "HELM", trim, -0.1, 0, 6.7, 1.9, 1.9, 0.7),
        rpart("GUN", "RIFL", GUNC, 2.2, 0.6, 3.4, 3.4, 0.5, 0.5),
    ]

def rocket_body(uniform, trim, skin=(214, 178, 148)):
    """anti-armor/anti-air: shoulder launcher tube instead of a rifle,
    heavier pauldrons for the silhouette."""
    GUNC = (70, 74, 80)
    DARK = (46, 49, 56)
    return [
        rpart("LEGL", "LEGL", trim, -0.4, -0.75, 0, 1.4, 1.1, 2.6),
        rpart("LEGR", "LEGR", trim, -0.4, 0.75, 0, 1.4, 1.1, 2.6),
        rpart("TORSO", "TORS", uniform, 0, 0, 2.6, 2.2, 3.0, 2.8),
        rpart("TORSO", "PAKL", trim, -0.4, -1.6, 4.6, 1.4, 1.4, 1.0),
        rpart("TORSO", "PAKR", trim, -0.4, 1.6, 4.6, 1.4, 1.4, 1.0),
        rpart("ARML", "ARML", uniform, 0.9, -1.7, 3.2, 2.6, 0.9, 1.0),
        rpart("ARMR", "ARMR", uniform, 0.9, 1.7, 3.2, 2.6, 0.9, 1.0),
        rpart("HEAD", "HEAD", skin, 0, 0, 5.6, 1.6, 1.6, 1.5),
        rpart("HEAD", "HELM", trim, -0.1, 0, 6.7, 1.9, 1.9, 0.7),
        rpart("GUN", "TUBE", GUNC, 0.8, 1.1, 6.0, 4.6, 1.0, 1.0),
        rpart("GUN", "TIP", DARK, 3.0, 1.1, 6.1, 0.6, 0.8, 0.8),
    ]

def scout_body(uniform, trim, visor=(80, 140, 170)):
    """recon: slim frame, wide sensor visor instead of a helmet brim,
    sidearm only - reads fast and fragile."""
    GUNC = (70, 74, 80)
    return [
        rpart("LEGL", "LEGL", trim, -0.4, -0.75, 0, 1.1, 0.9, 2.6),
        rpart("LEGR", "LEGR", trim, -0.4, 0.75, 0, 1.1, 0.9, 2.6),
        rpart("TORSO", "TORS", uniform, 0, 0, 2.6, 1.8, 2.4, 2.8),
        rpart("ARML", "ARML", uniform, 0.7, -1.4, 3.3, 2.0, 0.8, 0.9),
        rpart("ARMR", "ARMR", uniform, 0.7, 1.4, 3.3, 2.0, 0.8, 0.9),
        rpart("HEAD", "HEAD", (214, 178, 148), 0, 0, 5.6, 1.5, 1.5, 1.4),
        rpart("HEAD", "VISR", visor, 0.7, 0, 6.2, 0.6, 1.9, 0.7),
        rpart("HEAD", "ANTN", trim, -0.7, 0.6, 6.9, 0.3, 0.3, 1.8),
        rpart("GUN", "PSTL", GUNC, 1.6, 0.6, 3.5, 1.6, 0.4, 0.6),
    ]

def heavy_body(uniform, trim, skin=(214, 178, 148)):
    """heavy gunner: wide pauldrons, braced two-hand cannon, thick legs."""
    GUNC = (58, 62, 68)
    return [
        rpart("LEGL", "LEGL", trim, -0.4, -0.85, 0, 1.7, 1.3, 2.6),
        rpart("LEGR", "LEGR", trim, -0.4, 0.85, 0, 1.7, 1.3, 2.6),
        rpart("TORSO", "TORS", uniform, 0, 0, 2.6, 2.6, 3.4, 2.9),
        rpart("TORSO", "PDL", trim, -0.2, -2.0, 4.9, 1.9, 1.7, 1.2),
        rpart("TORSO", "PDR", trim, -0.2, 2.0, 4.9, 1.9, 1.7, 1.2),
        rpart("ARML", "ARML", uniform, 0.9, -1.8, 3.1, 2.7, 1.0, 1.1),
        rpart("ARMR", "ARMR", uniform, 0.9, 1.8, 3.1, 2.7, 1.0, 1.1),
        rpart("HEAD", "HEAD", skin, 0, 0, 5.7, 1.6, 1.6, 1.4),
        rpart("HEAD", "HELM", trim, -0.1, 0, 6.8, 2.1, 2.1, 0.8),
        rpart("GUN", "CANN", GUNC, 2.3, 0.3, 3.3, 3.8, 0.9, 0.9),
        rpart("GUN", "MAG", trim, 1.2, 0.3, 2.7, 1.2, 0.7, 0.7),
    ]

RIGGED = {
    "MERINF02": rifle_body((225, 229, 234), (120, 128, 138)),   # Meridian Warden
    "JAKINF02": rifle_body((196, 170, 128), (138, 90, 60)),     # Jackal Scrapper
    "MERROC01": rocket_body((225, 229, 234), (215, 180, 90)),   # Meridian Lancer
    "JAKROC01": rocket_body((196, 170, 128), (111, 143, 90)),   # Jackal Sting
    "MERSCT01": scout_body((225, 229, 234), (120, 128, 138)),   # Meridian Vigil
    "JAKSCT01": scout_body((196, 170, 128), (138, 90, 60), visor=(170, 120, 60)),  # Jackal Prowler
    "MERHVY01": heavy_body((225, 229, 234), (215, 180, 90)),    # Meridian Bastion
    "JAKHVY01": heavy_body((196, 170, 128), (111, 143, 90)),    # Jackal Bruiser
}

def rigged_w3d(model, parts):
    meshes = b"".join(mesh_chunk(model, n, c, g) for _, n, c, g in parts)
    subs = b"".join(
        chunk(HLOD_SUB_OBJECT, struct.pack("<I32s", bone, name32(f"{model}.{n}")))
        for bone, n, _, _ in parts)
    hlod = chunk(HLOD,
                 chunk(HLOD_HEADER, struct.pack("<II16s16s", 0x00010000, 1,
                                                model.encode(), SKEL_NAME.encode()))
                 + chunk(HLOD_LOD_ARRAY,
                         chunk(SUB_OBJECT_ARRAY_HEADER,
                               struct.pack("<If", len(parts), 3.4028235e38))
                         + subs, subs=True),
                 subs=True)
    return meshes + hlod

def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/GeneralsX/GeneralsZH/Art/W3D")
    os.makedirs(out_dir, exist_ok=True)
    files = {
        "wpinf1.w3d": hierarchy_w3d(),
        "wpinf1wlk.w3d": walk_anim(),
        "wpinf1idl.w3d": idle_anim(),
        "wpinf1fir.w3d": fire_anim(),
    }
    for model, parts in RIGGED.items():
        files[model.lower() + ".w3d"] = rigged_w3d(model, parts)
    for fname, data in files.items():
        path = os.path.join(out_dir, fname)
        with open(path, "wb") as f:
            f.write(data)
        print(f"wrote {path} ({len(data)} bytes)")
    print(f"walk stride for INI DistanceCovered: {STRIDE:.1f}")

if __name__ == "__main__":
    main()
