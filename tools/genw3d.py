#!/usr/bin/env python3
"""War Powers .w3d generator — minimal box models for the SAGE engine.

Byte layout extracted from the GPL engine's own reader (see docs/engine-notes;
chunk framing per WWLib/chunkio, structs per WW3D2/w3d_file.h). Emits an
untextured, vertex-material-colored box mesh wrapped in a single-LOD HLOD with
an implicit root bone (HierarchyName empty). Little-endian throughout.
"""
import os
import struct
import sys

# chunk ids
MESH, MESH_HEADER3 = 0x00000000, 0x0000001F
VERTICES, VERTEX_NORMALS, TRIANGLES = 0x02, 0x03, 0x20
MATERIAL_INFO, SHADERS = 0x28, 0x29
VERTEX_MATERIALS, VERTEX_MATERIAL = 0x2A, 0x2B
VERTEX_MATERIAL_NAME, VERTEX_MATERIAL_INFO = 0x2C, 0x2D
MATERIAL_PASS, VERTEX_MATERIAL_IDS, SHADER_IDS = 0x38, 0x39, 0x3A
HLOD, HLOD_HEADER, HLOD_LOD_ARRAY = 0x700, 0x701, 0x702
SUB_OBJECT_ARRAY_HEADER, HLOD_SUB_OBJECT = 0x703, 0x704

TWO_SIDED = 0x00002000  # bring-up insurance: winding can't hide the mesh

def chunk(cid, payload, subs=False):
    return struct.pack("<II", cid, len(payload) | (0x80000000 if subs else 0)) + payload

def name16(s):
    b = s.encode("ascii")
    assert len(b) < 16, s
    return b.ljust(16, b"\0")

def name32(s):
    b = s.encode("ascii")
    assert len(b) < 32, s
    return b.ljust(32, b"\0")

def rgb(r, g, b):
    return struct.pack("<4B", r, g, b, 0)

def box_geometry(hx, hy, h):
    """24 verts / 12 tris, per-face normals, CCW-from-outside winding."""
    faces = [
        ((0, 0, 1),  [(-hx, -hy, h), (hx, -hy, h), (hx, hy, h), (-hx, hy, h)]),
        ((0, 0, -1), [(-hx, -hy, 0), (-hx, hy, 0), (hx, hy, 0), (hx, -hy, 0)]),
        ((1, 0, 0),  [(hx, -hy, 0), (hx, hy, 0), (hx, hy, h), (hx, -hy, h)]),
        ((-1, 0, 0), [(-hx, hy, 0), (-hx, -hy, 0), (-hx, -hy, h), (-hx, hy, h)]),
        ((0, 1, 0),  [(hx, hy, 0), (-hx, hy, 0), (-hx, hy, h), (hx, hy, h)]),
        ((0, -1, 0), [(-hx, -hy, 0), (hx, -hy, 0), (hx, -hy, h), (-hx, -hy, h)]),
    ]
    verts, norms, tris = [], [], []
    for n, corners in faces:
        base = len(verts)
        verts += corners
        norms += [n] * 4
        dist = sum(a * b for a, b in zip(n, corners[0]))
        for a, b in ((1, 2), (2, 3)):
            tris.append((base, base + a, base + b, n, dist))
    return verts, norms, tris

def build_w3d(model, hx, hy, h, ambient, diffuse, emissive):
    mesh_name = "BOX01"
    verts, norms, tris = box_geometry(hx, hy, h)
    sph_r = (hx * hx + hy * hy + (h / 2) ** 2) ** 0.5

    header = struct.pack(
        "<II16s16sIIIIiIIII3f3f3ff",
        0x00040002, TWO_SIDED,
        mesh_name.encode(), model.encode(),
        len(tris), len(verts), 0, 0, 0, 0, 0,
        0x3, 0x1,
        -hx, -hy, 0.0, hx, hy, float(h),
        0.0, 0.0, h / 2.0, sph_r,
    )
    assert len(header) == 116, len(header)

    vert_b = b"".join(struct.pack("<3f", *v) for v in verts)
    norm_b = b"".join(struct.pack("<3f", *n) for n in norms)
    tri_b = b"".join(
        struct.pack("<3II3ff", a, b, c, 0, *n, d) for a, b, c, n, d in tris
    )

    vmat_info = struct.pack("<I", 0) + rgb(*ambient) + rgb(*diffuse) + rgb(0, 0, 0) + rgb(*emissive) + struct.pack("<3f", 1.0, 1.0, 0.0)
    assert len(vmat_info) == 32
    vmat = chunk(VERTEX_MATERIAL,
                 chunk(VERTEX_MATERIAL_NAME, b"Default\0")
                 + chunk(VERTEX_MATERIAL_INFO, vmat_info), subs=True)
    shader = bytes([3, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])  # opaque solid
    mat_pass = chunk(MATERIAL_PASS,
                     chunk(VERTEX_MATERIAL_IDS, struct.pack("<I", 0))
                     + chunk(SHADER_IDS, struct.pack("<I", 0)), subs=True)

    mesh = chunk(MESH,
                 chunk(MESH_HEADER3, header)
                 + chunk(VERTICES, vert_b)
                 + chunk(VERTEX_NORMALS, norm_b)
                 + chunk(TRIANGLES, tri_b)
                 + chunk(MATERIAL_INFO, struct.pack("<4I", 1, 1, 1, 0))
                 + chunk(VERTEX_MATERIALS, vmat, subs=True)
                 + chunk(SHADERS, shader)
                 + mat_pass,
                 subs=True)

    hlod = chunk(HLOD,
                 chunk(HLOD_HEADER, struct.pack("<II16s16s", 0x00010000, 1, model.encode(), b""))
                 + chunk(HLOD_LOD_ARRAY,
                         chunk(SUB_OBJECT_ARRAY_HEADER, struct.pack("<If", 1, 3.4028235e38))
                         + chunk(HLOD_SUB_OBJECT, struct.pack("<I32s", 0, name32(f"{model}.{mesh_name}"))),
                         subs=True),
                 subs=True)
    return mesh + hlod

MODELS = [
    # name, half-x, half-y, height, ambient, diffuse, emissive
    ("WPCC01", 20, 20, 30, (150, 155, 165), (200, 205, 215), (45, 45, 50)),
    ("WPTANK01", 11, 7, 7, (120, 130, 115), (170, 180, 160), (40, 42, 38)),
]

out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/GeneralsX/GeneralsZH/Art/W3D")
os.makedirs(out_dir, exist_ok=True)
for model, hx, hy, h, amb, dif, emi in MODELS:
    path = os.path.join(out_dir, model.lower() + ".w3d")
    data = build_w3d(model, hx, hy, h, amb, dif, emi)
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes)")
