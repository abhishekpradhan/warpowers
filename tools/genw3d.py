#!/usr/bin/env python3
"""War Powers .w3d generator — part-composed low-poly models for the SAGE engine.

Byte layout extracted from the GPL engine's own reader (chunk framing per
WWLib/chunkio, structs per WW3D2/w3d_file.h). Each model is a list of PARTS;
every part becomes its own single-color mesh chunk, aggregated by one HLod, so
silhouettes come from composition and identity from the faction palette
(docs/creative.md). Little-endian throughout.

Primitive: a rectangular FRUSTUM — bottom rectangle (sx, sy) centered at
(cx, cy) with base at z, top rectangle scaled by (tx, ty) and shifted by
(ox, oy), height sz. tx=ty=1 is a box; tx,ty<1 gives sloped faceted sides.
All six faces stay planar. Axis-aligned only (turret pivots come later with a
real hierarchy).
"""
import os
import struct
import sys

# ---- chunk ids ----
MESH, MESH_HEADER3 = 0x00000000, 0x0000001F
VERTICES, VERTEX_NORMALS, TRIANGLES = 0x02, 0x03, 0x20
MATERIAL_INFO, SHADERS = 0x28, 0x29
VERTEX_MATERIALS, VERTEX_MATERIAL = 0x2A, 0x2B
VERTEX_MATERIAL_NAME, VERTEX_MATERIAL_INFO = 0x2C, 0x2D
MATERIAL_PASS, VERTEX_MATERIAL_IDS, SHADER_IDS = 0x38, 0x39, 0x3A
HLOD, HLOD_HEADER, HLOD_LOD_ARRAY = 0x700, 0x701, 0x702
SUB_OBJECT_ARRAY_HEADER, HLOD_SUB_OBJECT = 0x703, 0x704

TWO_SIDED = 0x00002000

# ---- palette (docs/creative.md) ----
def hexc(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

PAL = {
    "STEEL":    hexc("B8C2CC"),
    "WHITE":    hexc("E8ECF0"),
    "GOLD":     hexc("D7B45A"),
    "SAND":     hexc("C9B08A"),
    "RUST":     hexc("8A5A3C"),
    "OXIDE":    hexc("6F8F5A"),
    "GRAPHITE": hexc("4A4E55"),
    "CHARCOAL": hexc("2E3138"),
    "GUN":      hexc("5A6068"),
    "TREAD":    hexc("33363B"),
}

def chunk(cid, payload, subs=False):
    return struct.pack("<II", cid, len(payload) | (0x80000000 if subs else 0)) + payload

def name32(s):
    b = s.encode("ascii")
    assert len(b) < 32, s
    return b.ljust(32, b"\0")

def rgb(c):
    return struct.pack("<4B", c[0], c[1], c[2], 0)

def scale3(c, f):
    return tuple(min(255, int(v * f)) for v in c)

# ---- geometry ----
def frustum(cx, cy, z, sx, sy, sz, tx=1.0, ty=1.0, ox=0.0, oy=0.0):
    """8 corners -> 6 planar faces -> 24 verts / 12 tris with face normals."""
    hx, hy = sx / 2.0, sy / 2.0
    thx, thy = hx * tx, hy * ty
    b = [(cx - hx, cy - hy, z), (cx + hx, cy - hy, z),
         (cx + hx, cy + hy, z), (cx - hx, cy + hy, z)]
    t = [(cx - thx + ox, cy - thy + oy, z + sz), (cx + thx + ox, cy - thy + oy, z + sz),
         (cx + thx + ox, cy + thy + oy, z + sz), (cx - thx + ox, cy + thy + oy, z + sz)]
    faces = [
        [t[0], t[1], t[2], t[3]],              # top
        [b[0], b[3], b[2], b[1]],              # bottom
        [b[1], b[2], t[2], t[1]],              # +x
        [b[3], b[0], t[0], t[3]],              # -x
        [b[2], b[3], t[3], t[2]],              # +y
        [b[0], b[1], t[1], t[0]],              # -y
    ]
    verts, norms, tris = [], [], []
    for corners in faces:
        (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = corners[0], corners[1], corners[2]
        ux, uy, uz = x1 - x0, y1 - y0, z1 - z0
        vx, vy, vz = x2 - x0, y2 - y0, z2 - z0
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        ln = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
        n = (nx / ln, ny / ln, nz / ln)
        base = len(verts)
        verts += corners
        norms += [n] * 4
        dist = n[0] * x0 + n[1] * y0 + n[2] * z0
        for a, c in ((1, 2), (2, 3)):
            tris.append((base, base + a, base + c, n, dist))
    return verts, norms, tris

def part(name, color, cx, cy, z, sx, sy, sz, tx=1.0, ty=1.0, ox=0.0, oy=0.0):
    return (name, color, frustum(cx, cy, z, sx, sy, sz, tx, ty, ox, oy))

# ---- w3d emission ----
def mesh_chunk(model, part_name, color, geo):
    color = PAL[color] if isinstance(color, str) else color
    verts, norms, tris = geo
    xs = [v[0] for v in verts]; ys = [v[1] for v in verts]; zs = [v[2] for v in verts]
    lo = (min(xs), min(ys), min(zs)); hi = (max(xs), max(ys), max(zs))
    ctr = tuple((a + b) / 2 for a, b in zip(lo, hi))
    sph_r = max(((v[0] - ctr[0]) ** 2 + (v[1] - ctr[1]) ** 2 + (v[2] - ctr[2]) ** 2) ** 0.5
                for v in verts)

    header = struct.pack(
        "<II16s16sIIIIiIIII3f3f3ff",
        0x00040002, TWO_SIDED,
        part_name.encode(), model.encode(),
        len(tris), len(verts), 0, 0, 0, 0, 0,
        0x3, 0x1,
        lo[0], lo[1], lo[2], hi[0], hi[1], hi[2],
        ctr[0], ctr[1], ctr[2], sph_r,
    )
    assert len(header) == 116

    vert_b = b"".join(struct.pack("<3f", *v) for v in verts)
    norm_b = b"".join(struct.pack("<3f", *n) for n in norms)
    tri_b = b"".join(struct.pack("<3II3ff", a, b, c, 0, *n, d) for a, b, c, n, d in tris)

    vmat_info = (struct.pack("<I", 0) + rgb(scale3(color, 0.50)) + rgb(color)
                 + rgb((0, 0, 0)) + rgb(scale3(color, 0.07))
                 + struct.pack("<3f", 1.0, 1.0, 0.0))
    vmat = chunk(VERTEX_MATERIAL,
                 chunk(VERTEX_MATERIAL_NAME, b"Default\0")
                 + chunk(VERTEX_MATERIAL_INFO, vmat_info), subs=True)
    shader = bytes([3, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    mat_pass = chunk(MATERIAL_PASS,
                     chunk(VERTEX_MATERIAL_IDS, struct.pack("<I", 0))
                     + chunk(SHADER_IDS, struct.pack("<I", 0)), subs=True)

    return chunk(MESH,
                 chunk(MESH_HEADER3, header)
                 + chunk(VERTICES, vert_b)
                 + chunk(VERTEX_NORMALS, norm_b)
                 + chunk(TRIANGLES, tri_b)
                 + chunk(MATERIAL_INFO, struct.pack("<4I", 1, 1, 1, 0))
                 + chunk(VERTEX_MATERIALS, vmat, subs=True)
                 + chunk(SHADERS, shader)
                 + mat_pass,
                 subs=True)

def build_w3d(model, parts):
    meshes = b"".join(mesh_chunk(model, n, c, g) for n, c, g in parts)
    subs = b"".join(
        chunk(HLOD_SUB_OBJECT, struct.pack("<I32s", 0, name32(f"{model}.{n}")))
        for n, _, _ in parts)
    hlod = chunk(HLOD,
                 chunk(HLOD_HEADER, struct.pack("<II16s16s", 0x00010000, 1,
                                                model.encode(), b""))
                 + chunk(HLOD_LOD_ARRAY,
                         chunk(SUB_OBJECT_ARRAY_HEADER,
                               struct.pack("<If", len(parts), 3.4028235e38))
                         + subs, subs=True),
                 subs=True)
    return meshes + hlod

# ---- the models (docs/creative.md rosters; unit faces +X at angle 0) ----
MODELS = {
    # Placeholder-tier generator (D015): hero assets from tools/blender/
    # superseded MERCC01/MERTANK01/JAKTANK01/JAKCP01 — keep them OUT of this
    # dict or a rerun overwrites the Blender-built files in the runtime dir.
    # Tank shell tracer: bright elongated slab, oriented +X (flight dir).
    "WPSHELL01": [
        part("TRACER", (245, 216, 150), 0, 0, -0.25, 2.4, 0.5, 0.5),
    ],
    # Rally-point marker flag (ThingTemplate literally named
    # RallyPointMarker): pole + gold pennant + ground ring.
    "WPRALLY01": [
        part("POLE", (200, 204, 210), 0, 0, 0, 0.8, 0.8, 14.0),
        part("PENN", "GOLD", 2.6, 0, 11.5, 5.2, 0.4, 2.6),
        part("RING", "GOLD", 0, 0, 0.3, 7.0, 7.0, 0.3),
        part("RINGC", (30, 32, 36), 0, 0, 0.45, 4.6, 4.6, 0.3),
    ],
    # Building-placement cursor (engine-hardcoded names): corner-bracket
    # anchor ring + direction arrow, bright gold, floating just off ground.
    "LOCATER01": [
        part("BR1A", "GOLD", -9, -10, 0.4, 6, 1.2, 0.5),
        part("BR1B", "GOLD", -10, -9, 0.4, 1.2, 6, 0.5),
        part("BR2A", "GOLD", 9, -10, 0.4, 6, 1.2, 0.5),
        part("BR2B", "GOLD", 10, -9, 0.4, 1.2, 6, 0.5),
        part("BR3A", "GOLD", -9, 10, 0.4, 6, 1.2, 0.5),
        part("BR3B", "GOLD", -10, 9, 0.4, 1.2, 6, 0.5),
        part("BR4A", "GOLD", 9, 10, 0.4, 6, 1.2, 0.5),
        part("BR4B", "GOLD", 10, 9, 0.4, 1.2, 6, 0.5),
    ],
    # Move-destination hint (GameData MoveHintName): a small gold diamond
    # ring shown for ~1.3s at each move order's target point. Its absence
    # (empty name) made drawMoveHints hunt for '.w3d' every frame.
    "WPMOVE01": [
        part("N", "GOLD", 0, -6.5, 0.4, 5.0, 1.1, 0.4),
        part("S", "GOLD", 0, 6.5, 0.4, 5.0, 1.1, 0.4),
        part("W", "GOLD", -6.5, 0, 0.4, 1.1, 5.0, 0.4),
        part("E", "GOLD", 6.5, 0, 0.4, 1.1, 5.0, 0.4),
        part("C", "GOLD", 0, 0, 0.4, 1.8, 1.8, 0.5),
    ],
    # Rally/waypoint path node puck (engine-hardcoded lookup in
    # W3DWaypointBuffer, renamed to our namespace): small flat gold disc
    # drawn at line elbows and the natural rally point.
    "WPNODE01": [
        part("DISC", "GOLD", 0, 0, 0.5, 3.4, 3.4, 0.6),
        part("CORE", (30, 32, 36), 0, 0, 0.85, 1.6, 1.6, 0.5),
    ],
    # Rocket projectile (WP_Rocket object): slim body + exhaust flare + fins.
    "WPROCK01": [
        part("BODY", (200, 204, 210), 0, 0, -0.3, 2.6, 0.6, 0.6),
        part("NOSE", (198, 74, 60), 1.6, 0, -0.25, 0.7, 0.5, 0.5),
        part("FINT", (90, 96, 104), -1.2, 0, -0.45, 0.8, 0.2, 1.0),
        part("FINS", (90, 96, 104), -1.2, 0, -0.3, 0.8, 1.0, 0.2),
        part("EXH", (245, 216, 150), -1.9, 0, -0.2, 0.8, 0.4, 0.4),
    ],
    "LOCATER02": [
        part("SHAFT", "GOLD", -2, 0, 0.4, 10, 2.0, 0.5),
        part("HEADC", "GOLD", 4.6, 0, 0.4, 3.2, 5.0, 0.5, ty=0.1, ox=1.6),
    ],
}

# Construction scaffolds: steel frame boxes shown while a structure is a site
# (AWAITING/PARTIALLY/ACTIVELY_BEING_CONSTRUCTED condition states). Two sizes.
def scaffold(hx, hy, h):
    STEEL = (168, 172, 178)
    DARKS = (118, 122, 128)
    ps = []
    for i, (px, py) in enumerate([(-hx, -hy), (hx, -hy), (-hx, hy), (hx, hy)]):
        ps.append(part(f"P{i}", STEEL, px, py, 0, 1.4, 1.4, h))
    for lvl, z in enumerate([h * 0.5, h - 1.2]):
        ps += [part(f"BA{lvl}", DARKS, 0, -hy, z, hx * 2, 1.0, 1.0),
               part(f"BB{lvl}", DARKS, 0, hy, z, hx * 2, 1.0, 1.0),
               part(f"BC{lvl}", DARKS, -hx, 0, z, 1.0, hy * 2, 1.0),
               part(f"BD{lvl}", DARKS, hx, 0, z, 1.0, hy * 2, 1.0)]
    ps.append(part("PAD", DARKS, 0, 0, 0.0, hx * 2 + 2, hy * 2 + 2, 0.4))
    ps.append(part("CRT1", "GOLD", -hx * 0.4, -hy * 0.4, 0.4, 4.5, 4.5, 3.0))
    ps.append(part("CRT2", "GOLD", hx * 0.35, hy * 0.3, 0.4, 3.5, 3.5, 2.4))
    return ps

# Aircraft (VTOL hover gunships) + airpads + income structures (Phase 3).
MODELS["MERJET01"] = [                                     # Kestrel strike VTOL
    part("HULL", "WHITE", 0, 0, 2.2, 14.0, 5.0, 2.6, tx=0.55, ty=0.6),
    part("NOSE", "STEEL", 6.4, 0, 2.4, 3.2, 2.6, 1.8, tx=0.4, ty=0.5),
    part("CANO", (58, 76, 96), 2.4, 0, 4.6, 3.6, 2.2, 1.2, tx=0.6, ty=0.6),
    part("WINL", "WHITE", -1.2, -6.4, 2.8, 6.0, 7.0, 0.8, tx=0.5),
    part("WINR", "WHITE", -1.2, 6.4, 2.8, 6.0, 7.0, 0.8, tx=0.5),
    part("FANL", "GOLD", -0.8, -7.6, 3.6, 3.4, 3.4, 0.8),
    part("FANR", "GOLD", -0.8, 7.6, 3.6, 3.4, 3.4, 0.8),
    part("TAIL", "GOLD", -6.6, 0, 3.4, 2.6, 1.2, 2.6, tx=0.5),
]
MODELS["JAKJET01"] = [                                     # Buzzard rocket rig
    part("POD", "SAND", 0.6, 0, 2.0, 9.0, 5.4, 3.0, tx=0.7, ty=0.75),
    part("SNUB", "RUST", 5.2, 0, 2.4, 2.6, 3.0, 2.0),
    part("BOOML", "RUST", -4.6, -3.2, 2.8, 7.0, 1.4, 1.2),
    part("BOOMR", "RUST", -4.6, 3.2, 2.8, 7.0, 1.4, 1.2),
    part("ROTOR", "GRAPHITE", 0, 0, 5.6, 11.0, 2.2, 0.7),
    part("ROTB", "OXIDE", 0, 0, 4.9, 3.0, 3.0, 0.9),
    part("RACKL", "GUN", 1.4, -3.4, 1.2, 3.4, 1.2, 1.2),
    part("RACKR", "GUN", 1.4, 3.4, 1.2, 3.4, 1.2, 1.2),
]
MODELS["MERPAD01"] = [                                     # Launch Pad
    part("PAD", "STEEL", 0, 0, 0, 40, 34, 2.2),
    part("RING", "GOLD", 0, 0, 2.2, 24, 24, 0.5),
    part("CORE", "CHARCOAL", 0, 0, 2.7, 17, 17, 0.4),
    part("MAST", "WHITE", -16, -12, 2.2, 5, 5, 16, tx=0.7, ty=0.7),
    part("DISH", "GOLD", -16, -12, 18.2, 4.4, 4.4, 1.2),
    part("LTA", "GOLD", 16, 13, 2.2, 1.4, 1.4, 3.2),
    part("LTB", "GOLD", 16, -13, 2.2, 1.4, 1.4, 3.2),
]
MODELS["JAKPAD01"] = [                                     # Roost
    part("DECK", "RUST", 0, 0, 0, 38, 32, 3.0, tx=0.92, ty=0.92),
    part("PLNK", "SAND", 0, 0, 3.0, 26, 22, 0.6),
    part("TOWR", "GRAPHITE", -14, 11, 3.0, 6, 6, 13, tx=0.8, ty=0.8),
    part("PERCH", "RUST", -14, 11, 16.0, 10, 2.2, 1.0),
    part("BARL", "OXIDE", 14, -11, 3.0, 4.4, 4.4, 3.6),
    part("BARL2", "OXIDE", 10, -13, 3.0, 4.0, 4.0, 3.2),
]
MODELS["MEREX01"] = [                                      # Exchange (income)
    part("BASE", "STEEL", 0, 0, 0, 26, 22, 4.0),
    part("VAULT", "WHITE", 0, 0, 4.0, 20, 16, 9.0, tx=0.85, ty=0.85),
    part("BAND", "GOLD", 0, 0, 8.4, 20.6, 16.6, 1.4),
    part("CAP", "GOLD", 0, 0, 13.0, 10, 8, 1.6, tx=0.6, ty=0.6),
    part("KIOSK", "CHARCOAL", 11, 8, 4.0, 5, 4, 4.4),
]
MODELS["JAKEX01"] = [                                      # Racket (income)
    part("SHACK", "SAND", 0, 0, 0, 22, 18, 7.0, tx=0.9, ty=0.9),
    part("ROOF", "RUST", 0, 0, 7.0, 24, 20, 1.2),
    part("SIGN", "GOLD", 9, 0, 8.2, 1.2, 10, 4.2),
    part("ANT", "GRAPHITE", -8, -6, 8.2, 1.0, 1.0, 9.0),
    part("CRATE", "OXIDE", 10, -10, 0, 5, 5, 3.6),
    part("CRT2", "RUST", 5, -12, 0, 4, 4, 2.8),
]

# Phase 3 close-out: second airframes + defense/tech/power structures.
MODELS["MERJET02"] = [                                     # Shrike strafer
    part("HULL", "WHITE", 0, 0, 2.4, 11.0, 3.6, 2.0, tx=0.5, ty=0.55),
    part("NOSE", "GOLD", 5.0, 0, 2.5, 2.6, 2.0, 1.4, tx=0.35, ty=0.5),
    part("CANO", (58, 76, 96), 1.6, 0, 4.2, 3.0, 1.8, 1.0, tx=0.55),
    part("WNGL", "STEEL", -0.8, -5.2, 2.9, 4.4, 5.4, 0.6, tx=0.45),
    part("WNGR", "STEEL", -0.8, 5.2, 2.9, 4.4, 5.4, 0.6, tx=0.45),
    part("GUNL", "GUN", 2.0, -3.6, 2.3, 3.0, 0.8, 0.8),
    part("GUNR", "GUN", 2.0, 3.6, 2.3, 3.0, 0.8, 0.8),
    part("TAIL", "GOLD", -5.4, 0, 3.2, 2.0, 1.0, 2.2, tx=0.45),
]
MODELS["JAKJET02"] = [                                     # Gnat harasser
    part("POD", "SAND", 0, 0, 2.0, 6.0, 4.0, 2.6, tx=0.75, ty=0.8),
    part("SNOUT", "RUST", 3.4, 0, 2.3, 1.8, 2.2, 1.6),
    part("FAN", "GRAPHITE", -0.4, 0, 4.8, 7.4, 1.6, 0.6),
    part("FANB", "OXIDE", -0.4, 0, 4.2, 2.2, 2.2, 0.7),
    part("SKIDL", "GUN", 0, -2.0, 0.9, 4.0, 0.5, 0.5),
    part("SKIDR", "GUN", 0, 2.0, 0.9, 4.0, 0.5, 0.5),
    part("STING", "GUN", 2.6, 0, 1.4, 2.6, 0.7, 0.7),
]
MODELS["MERAA01"] = [                                      # Skyspear AA
    part("BASE", "STEEL", 0, 0, 0, 18, 18, 3.0),
    part("MAST", "WHITE", 0, 0, 3.0, 5, 5, 12, tx=0.8, ty=0.8),
    part("HEAD", "GOLD", 0, 0, 15.0, 7, 5, 2.4),
    part("RAILL", "GUN", 2.0, -2.0, 17.0, 9, 1.1, 1.1, ox=2.6),
    part("RAILR", "GUN", 2.0, 2.0, 17.0, 9, 1.1, 1.1, ox=2.6),
    part("DISH", "GOLD", -3.0, 0, 17.6, 3.2, 3.2, 1.0),
]
MODELS["JAKAA01"] = [                                      # Flakhut AA
    part("HUT", "RUST", 0, 0, 0, 16, 14, 6.0, tx=0.9, ty=0.9),
    part("BAGS", "SAND", 0, 0, 0, 20, 18, 2.2),
    part("MNT", "GRAPHITE", 0, 0, 6.0, 6, 6, 2.6),
    part("QUADA", "GUN", 1.5, -1.4, 8.6, 7, 0.9, 0.9, ox=2.0),
    part("QUADB", "GUN", 1.5, 1.4, 8.6, 7, 0.9, 0.9, ox=2.0),
    part("QUADC", "GUN", 1.5, -1.4, 9.7, 7, 0.9, 0.9, ox=2.0),
    part("QUADD", "GUN", 1.5, 1.4, 9.7, 7, 0.9, 0.9, ox=2.0),
]
MODELS["MERART01"] = [                                     # Longbow siege gun
    part("PLATE", "STEEL", 0, 0, 0, 20, 20, 2.4),
    part("TURN", "WHITE", 0, 0, 2.4, 11, 11, 2.2, tx=0.9, ty=0.9),
    part("CRDL", "GRAPHITE", -1.0, 0, 4.6, 7, 6, 3.0),
    part("BARL1", "GUN", 4.0, 0, 6.2, 9, 1.6, 1.6, ox=2.0),
    part("BARL2", "GUN", 10.5, 0, 7.6, 9, 1.3, 1.3, ox=2.4),
    part("MUZZ", "GOLD", 15.5, 0, 8.6, 2.4, 1.7, 1.7),
    part("CWT", "STEEL", -6.5, 0, 5.0, 5, 5.5, 4.2),
    part("JACKL", "GRAPHITE", -7, -8.5, 0, 3.2, 2.0, 4.5),
    part("JACKR", "GRAPHITE", -7, 8.5, 0, 3.2, 2.0, 4.5),
]
MODELS["JAKART01"] = [                                     # Lobber junk mortar
    part("BAGS", "SAND", 0, 0, 0, 19, 19, 2.4),
    part("PIT", "RUST", 0, 0, 0.4, 13, 13, 1.6),
    part("BED", "GRAPHITE", -1, 0, 2.0, 8, 8, 2.0),
    part("TUBE1", "GUN", 1.0, 0, 4.0, 4.2, 4.2, 6.5, tx=0.85, ty=0.85),
    part("TUBE2", "GUN", 2.2, 0, 10.2, 3.4, 3.4, 4.0, tx=0.85, ty=0.85),
    part("RING", "OXIDE", 2.6, 0, 13.9, 3.8, 3.8, 0.8),
    part("BRACE", "RUST", -3.5, 0, 2.4, 1.4, 1.4, 9.0),
    part("AMMO", "RUST", 6.5, -6.5, 0.4, 4.5, 3.2, 2.6),
]
MODELS["MERTECH01"] = [                                    # Directorate tech
    part("SLAB", "WHITE", 0, 0, 0, 24, 18, 14, tx=0.9, ty=0.9),
    part("BAND", "GOLD", 0, 0, 9.0, 24.6, 18.6, 1.2),
    part("ANT1", "STEEL", -7, -5, 14, 1.0, 1.0, 9),
    part("ANT2", "STEEL", 7, 4, 14, 1.0, 1.0, 7),
    part("ORB", "GOLD", -7, -5, 23.4, 2.0, 2.0, 1.6),
    part("WING", "STEEL", 14, 0, 0, 6, 12, 6),
]
MODELS["JAKTECH01"] = [                                    # Den tech
    part("DOME", "SAND", 0, 0, 0, 20, 20, 9, tx=0.55, ty=0.55),
    part("PIPE1", "RUST", 10, -5, 0, 2.2, 2.2, 12),
    part("PIPE2", "RUST", -9, 6, 0, 2.0, 2.0, 10),
    part("ELB1", "RUST", 10, -5, 11.2, 5.0, 2.0, 2.0),
    part("DISH", "OXIDE", 0, 0, 9.4, 6.0, 6.0, 2.0, tx=1.4, ty=1.4),
    part("CRT", "GRAPHITE", 12, 8, 0, 5, 5, 3.4),
]
MODELS["MERPILL01"] = [                                    # Rampart pillbox
    part("BUNK", "STEEL", 0, 0, 0, 16, 14, 6.5, tx=0.85, ty=0.85),
    part("CAP", "WHITE", 0, 0, 6.5, 12, 10, 2.0, tx=0.7, ty=0.7),
    part("SLIT", "CHARCOAL", 7.4, 0, 3.4, 1.6, 8.0, 1.6),
    part("GUNB", "GUN", 9.0, 0, 3.6, 3.6, 1.0, 1.0),
    part("TRIM", "GOLD", 0, 0, 8.5, 5, 5, 0.8),
]
MODELS["JAKPILL01"] = [                                    # Nest barricade
    part("RING", "RUST", 0, 0, 0, 17, 15, 4.5, tx=0.8, ty=0.8),
    part("PLATE", "SAND", 0, 0, 4.5, 12, 10, 1.4),
    part("GUNA", "GUN", 7.5, -2.0, 3.2, 4.2, 0.9, 0.9),
    part("GUNB2", "GUN", 7.5, 2.0, 3.2, 4.2, 0.9, 0.9),
    part("JUNK", "OXIDE", -6, 5, 4.5, 4, 4, 2.6),
]
MODELS["JAKPWR01"] = [                                     # Dynamo power
    part("GEN", "SAND", 0, 0, 0, 22, 16, 9, tx=0.9, ty=0.9),
    part("STACK", "RUST", -6, -4, 9, 4.4, 4.4, 12, tx=0.7, ty=0.7),
    part("STK2", "RUST", 2, -4, 9, 3.6, 3.6, 9, tx=0.7, ty=0.7),
    part("COIL", "GRAPHITE", 6, 4, 9, 6, 6, 4, tx=0.6, ty=0.6),
    part("BOLT", "GOLD", 6, 4, 13.2, 2.2, 2.2, 2.6),
    part("PIPE", "GUN", 11, 0, 2.0, 6, 1.6, 1.6),
]

MODELS["WPSCAF01"] = scaffold(11, 11, 12)
MODELS["WPSCAF02"] = scaffold(19, 17, 18)

# Infantry: chunky minifig troopers matching the boot-slice blocky look.
# Faces +X at angle 0 (rifle forward). ~7 world units tall.
def trooper(uniform, trim, skin=(214, 178, 148)):
    GUNC = (70, 74, 80)
    return [
        part("LEGL", trim, -0.4, -0.75, 0, 1.4, 1.1, 2.6),
        part("LEGR", trim, -0.4, 0.75, 0, 1.4, 1.1, 2.6),
        part("TORS", uniform, 0, 0, 2.6, 2.2, 3.0, 2.8),
        part("ARMR", uniform, 0.9, 1.7, 3.2, 2.6, 0.9, 1.0),
        part("ARML", uniform, 0.9, -1.7, 3.2, 2.6, 0.9, 1.0),
        part("HEAD", skin, 0, 0, 5.6, 1.6, 1.6, 1.5),
        part("HELM", trim, -0.1, 0, 6.7, 1.9, 1.9, 0.7),
        part("RIFL", GUNC, 2.2, 0.6, 3.4, 3.4, 0.5, 0.5),
    ]

MODELS["MERINF01"] = trooper((225, 229, 234), (120, 128, 138))     # Meridian Warden: white/steel
MODELS["JAKINF01"] = trooper((196, 170, 128), (138, 90, 60))       # Jackal Scrapper: sand/rust

def main():
    import argparse
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description='Generate remaining original part-language models; finished assets are protected.')
    parser.add_argument('output', nargs='?', type=Path, default=root/'data/Art/W3D')
    args = parser.parse_args()
    out_dir = args.output
    protected = {name.upper() for name in json.loads((root/'tools/blender/polish_assets.json').read_text())}
    os.makedirs(out_dir, exist_ok=True)
    for model, parts in MODELS.items():
        if model in protected:
            continue  # Approved textured replacements come from build_polish.py.
        path = os.path.join(out_dir, model.lower() + ".w3d")
        data = build_w3d(model, parts)
        with open(path, "wb") as f:
            f.write(data)
        tris = sum(len(g[2]) for _, _, g in parts)
        print(f"wrote {path} ({len(data)} bytes, {len(parts)} parts, {tris} tris)")

if __name__ == "__main__":
    main()
