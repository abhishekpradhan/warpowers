#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
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
  wpinf1die.w3d     ANIMATION WPINF1DIE
The infantry bodies that bind to this skeleton (MER/JAK INF02, ROC01, SCT01,
HVY01: meshes + HLOD with HierarchyName WPINF1) are painted Blender assets
from tools/blender/build_polish.py, which imports PIV/WORLD from here.

python3 tools/genrig.py [OUTPUT_DIR]   (default: the repository data/Art/W3D)
"""
import argparse
import math
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wp_w3d import (ANIMATION, ANIMATION_CHANNEL, ANIMATION_HEADER, HIERARCHY,  # noqa: E402
                    HIERARCHY_HEADER, PIVOTS, chunk)

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
        if len(vals) != veclen:
            raise ValueError(f'channel type {ctype} needs {veclen} value(s) per frame, got {vals!r}')
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

def death_anim():
    """A brief backward fall with a settled pose; played once before sinking."""
    n=28
    fall=[-1.48*(1-(1-min(1,i/19))**2) for i in range(n)]
    # Small final impact avoids a hard discontinuity without looping the body.
    fall[19:24]=[-1.48,-1.42,-1.47,-1.49,-1.48]
    return animation_w3d('WPINF1DIE',n,24,[
        channel(PIV['ROOTTRANSFORM'],CH_Q,[qy(a) for a in fall]),
        channel(PIV['ROOTTRANSFORM'],CH_Z,[max(0,.40*math.sin(math.pi*min(1,i/19))) for i in range(n)]),
        channel(PIV['ARML'],CH_Q,[qy(.30*min(1,i/12)) for i in range(n)]),
        channel(PIV['ARMR'],CH_Q,[qy(-.20*min(1,i/12)) for i in range(n)]),
    ])

def main(argv=None):
    parser = argparse.ArgumentParser(description='Generate the shared WPINF1 skeleton and animations without replacing infantry bodies.')
    parser.add_argument('output', nargs='?', type=Path, default=Path(__file__).resolve().parents[1] / 'data/Art/W3D',
                        help='destination directory (default: the repository dataset)')
    out_dir = parser.parse_args(argv).output
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "wpinf1.w3d": hierarchy_w3d(),
        "wpinf1wlk.w3d": walk_anim(),
        "wpinf1idl.w3d": idle_anim(),
        "wpinf1fir.w3d": fire_anim(),
        "wpinf1die.w3d": death_anim(),
    }
    # The animated bodies now come from the painted Blender production pipeline.
    # This generator owns the shared skeleton/animations; rerunning it must never
    # silently replace finished infantry with the original block placeholders.
    for fname, data in files.items():
        path = out_dir / fname
        path.write_bytes(data)
        print(f"wrote {path} ({len(data)} bytes)")
    print(f"walk stride for INI DistanceCovered: {STRIDE:.1f}")

if __name__ == "__main__":
    main()
