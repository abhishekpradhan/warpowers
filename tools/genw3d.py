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

MODELS["WPSCAF01"] = scaffold(11, 11, 12)
MODELS["WPSCAF02"] = scaffold(19, 17, 18)

out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/GeneralsX/GeneralsZH/Art/W3D")
os.makedirs(out_dir, exist_ok=True)
for model, parts in MODELS.items():
    path = os.path.join(out_dir, model.lower() + ".w3d")
    data = build_w3d(model, parts)
    with open(path, "wb") as f:
        f.write(data)
    tris = sum(len(g[2]) for _, _, g in parts)
    print(f"wrote {path} ({len(data)} bytes, {len(parts)} parts, {tris} tris)")
