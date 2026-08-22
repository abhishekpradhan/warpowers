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
    # Meridian Vector MBT: sloped steel hull on dark treads, gold canopy.
    "MERTANK01": [
        part("TREADL", "TREAD", 0, -5.5, 0, 22, 3.6, 3.2),
        part("TREADR", "TREAD", 0, +5.5, 0, 22, 3.6, 3.2),
        part("HULL",  "STEEL", 0.5, 0, 2.6, 20, 11, 4.2, tx=0.78, ty=0.72, ox=1.2),
        part("TURRET", "WHITE", -1.0, 0, 6.8, 9.5, 8, 3.4, tx=0.7, ty=0.7),
        part("BARREL", "GUN", 7.5, 0, 8.0, 11, 1.3, 1.3),
        part("CANOPY", "GOLD", -3.2, 0, 10.0, 3.2, 3.2, 1.1, tx=0.7, ty=0.7),
    ],
    # Meridian Command Center: terraced white block, steel tower, gold cornice
    # ring (four thin strips along the roof edge, not a solid gold roof).
    "MERCC01": [
        part("PODIUM", "STEEL", 0, 0, 0, 40, 40, 7, tx=0.92, ty=0.92),
        part("BLOCK", "WHITE", 0, 0, 7, 32, 32, 13, tx=0.85, ty=0.85),
        part("CORN_N", "GOLD", 0, 13.0, 19.6, 28.6, 1.3, 1.5),
        part("CORN_S", "GOLD", 0, -13.0, 19.6, 28.6, 1.3, 1.5),
        part("CORN_E", "GOLD", 13.0, 0, 19.6, 1.3, 26.0, 1.5),
        part("CORN_W", "GOLD", -13.0, 0, 19.6, 1.3, 26.0, 1.5),
        part("TOWER", "STEEL", 5, 5, 20, 11, 11, 9, tx=0.85, ty=0.85),
        part("MAST",  "GRAPHITE", 5, 5, 29, 1.6, 1.6, 8),
        part("TIP",   "GOLD", 5, 5, 37, 2.4, 2.4, 1.4),
        part("PAD",   "GRAPHITE", -11, -10, 7, 14, 16, 1.8),
    ],
    # Jackal Mongrel tank: rusty mismatched hull, off-center sand turret,
    # uneven treads, one salvaged oxide plate.
    "JAKTANK01": [
        part("TREADL", "TREAD", -0.8, -5.2, 0, 21, 3.4, 3.0),
        part("TREADR", "TREAD", 0.8, +5.2, 0, 19, 3.4, 3.0),
        part("HULL",  "RUST", 0, 0, 2.4, 19, 10.4, 4.0, tx=0.85, ty=0.9, ox=0.8),
        part("PLATE", "OXIDE", 2.0, -5.0, 3.0, 7, 1.0, 3.2),
        part("TURRET", "SAND", -1.5, 1.2, 6.2, 8.5, 7.5, 3.2, tx=0.8, ty=0.75),
        part("BARREL", "GUN", 6.0, 1.2, 7.2, 9, 1.6, 1.6),
        part("STACK", "CHARCOAL", -6.5, -3.0, 5.5, 1.8, 1.8, 4.5),
    ],
    # Jackal Command Post: offset slab, shack, tarp, watchtower — asymmetric.
    "JAKCP01": [
        part("SLAB",  "RUST", 1, -1, 0, 38, 34, 6, tx=0.95, ty=0.95),
        part("SHACK", "SAND", -4, 3, 6, 21, 16, 8, tx=0.9, ty=0.92),
        part("TARP",  "OXIDE", -1, 6, 14, 15, 11, 1.2, ox=1.5),
        part("POLE",  "RUST", 12, -9, 6, 2.6, 2.6, 17),
        part("NEST",  "SAND", 12, -9, 23, 8.5, 8.5, 5, tx=0.85, ty=0.85),
        part("SCRAP", "CHARCOAL", -13, -11, 6, 9, 7, 3, tx=0.7, ty=0.6, ox=1.0),
        part("DISH",  "GUN", 6, 10, 14.5, 4.5, 4.5, 2.2, tx=0.3, ty=0.3),
    ],
}

out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/GeneralsX/GeneralsZH/Art/W3D")
os.makedirs(out_dir, exist_ok=True)
for model, parts in MODELS.items():
    path = os.path.join(out_dir, model.lower() + ".w3d")
    data = build_w3d(model, parts)
    with open(path, "wb") as f:
        f.write(data)
    tris = sum(len(g[2]) for _, _, g in parts)
    print(f"wrote {path} ({len(data)} bytes, {len(parts)} parts, {tris} tris)")
