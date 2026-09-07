# SPDX-License-Identifier: MIT
"""W3D chunk framing shared by the model generators, the Blender post-passes
and the content validator.

Chunk ids follow the GPL engine's WW3D2/w3d_file.h; framing follows
WWLib/chunkio: an 8-byte little-endian header (id, size) where the size's top
bit marks a chunk that contains sub-chunks.  Standard library only.
"""
import struct

MESH, MESH_HEADER3 = 0x00000000, 0x0000001F
VERTICES, VERTEX_NORMALS, TRIANGLES = 0x02, 0x03, 0x20
MATERIAL_INFO, SHADERS = 0x28, 0x29
VERTEX_MATERIALS, VERTEX_MATERIAL = 0x2A, 0x2B
VERTEX_MATERIAL_NAME, VERTEX_MATERIAL_INFO = 0x2C, 0x2D
TEXTURES, TEXTURE, TEXTURE_NAME = 0x30, 0x31, 0x32
MATERIAL_PASS, VERTEX_MATERIAL_IDS, SHADER_IDS = 0x38, 0x39, 0x3A
HIERARCHY, HIERARCHY_HEADER, PIVOTS = 0x100, 0x101, 0x102
ANIMATION, ANIMATION_HEADER, ANIMATION_CHANNEL = 0x200, 0x201, 0x202
HLOD, HLOD_HEADER, HLOD_LOD_ARRAY = 0x700, 0x701, 0x702
SUB_OBJECT_ARRAY_HEADER, HLOD_SUB_OBJECT = 0x703, 0x704

HAS_SUBCHUNKS = 0x80000000
MESH_TWO_SIDED = 0x00002000
PIVOT_SIZE = 60          # W3dPivotStruct: name[16], parent, translation, euler, rotation
NO_PARENT = 0xFFFFFFFF
HEADER_SIZE = 8


def chunk(kind, payload, subs=False):
    """Frame ``payload`` as one chunk; ``subs`` marks a container of chunks."""
    return struct.pack('<II', kind, len(payload) | (HAS_SUBCHUNKS if subs else 0)) + payload


def chunks(data):
    """Iterate one level: yields (kind, has_subchunks, payload)."""
    pos = 0
    end = len(data)
    while pos < end:
        if pos + HEADER_SIZE > end:
            raise ValueError(f'truncated W3D chunk header at {pos}')
        kind, encoded = struct.unpack_from('<II', data, pos)
        boundary = pos + HEADER_SIZE + (encoded & ~HAS_SUBCHUNKS)
        if boundary > end:
            raise ValueError(f'W3D chunk {kind:#x} extends beyond its parent')
        yield kind, bool(encoded & HAS_SUBCHUNKS), data[pos + HEADER_SIZE:boundary]
        pos = boundary


def walk(data, start=0, end=None):
    """Iterate every chunk at every depth: yields (kind, payload)."""
    end = len(data) if end is None else end
    offset = start
    while offset < end:
        if offset + HEADER_SIZE > end:
            raise ValueError(f'truncated W3D chunk header at {offset}')
        kind, encoded = struct.unpack_from('<II', data, offset)
        boundary = offset + HEADER_SIZE + (encoded & ~HAS_SUBCHUNKS)
        if boundary > end:
            raise ValueError(f'W3D chunk {kind:#x} extends beyond its parent')
        yield kind, data[offset + HEADER_SIZE:boundary]
        if encoded & HAS_SUBCHUNKS:
            yield from walk(data, offset + HEADER_SIZE, boundary)
        offset = boundary


def fixed_name(text, size):
    """ASCII name in a NUL-terminated fixed field; overflow is an error, never
    a silent truncation (the engine matches meshes and pivots by these names)."""
    encoded = text.encode('ascii')
    if len(encoded) >= size:
        raise ValueError(f'W3D name {text!r} needs {len(encoded) + 1} bytes; the field holds {size}')
    return encoded.ljust(size, b'\0')


def name16(text):
    return fixed_name(text, 16)


def name32(text):
    return fixed_name(text, 32)


def _rgb(colour):
    return struct.pack('<4B', colour[0], colour[1], colour[2], 0)


def _scale(colour, factor):
    return tuple(min(255, int(v * factor)) for v in colour)


def mesh_chunk(model, part_name, colour, geometry):
    """One single-colour, unlit, two-sided mesh chunk named ``model.part_name``.

    ``geometry`` is (vertices, normals, triangles) where each triangle is
    (a, b, c, normal, plane_distance); ``colour`` is an (r, g, b) tuple.
    """
    verts, norms, tris = geometry
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    lo = (min(xs), min(ys), min(zs))
    hi = (max(xs), max(ys), max(zs))
    ctr = tuple((a + b) / 2 for a, b in zip(lo, hi))
    sph_r = max(((v[0] - ctr[0]) ** 2 + (v[1] - ctr[1]) ** 2 + (v[2] - ctr[2]) ** 2) ** 0.5
                for v in verts)
    header = struct.pack(
        '<II16s16sIIIIiIIII3f3f3ff',
        0x00040002, MESH_TWO_SIDED,
        name16(part_name), name16(model),
        len(tris), len(verts), 0, 0, 0, 0, 0,
        0x3, 0x1,
        lo[0], lo[1], lo[2], hi[0], hi[1], hi[2],
        ctr[0], ctr[1], ctr[2], sph_r,
    )
    vert_b = b''.join(struct.pack('<3f', *v) for v in verts)
    norm_b = b''.join(struct.pack('<3f', *n) for n in norms)
    tri_b = b''.join(struct.pack('<3II3ff', a, b, c, 0, *n, d) for a, b, c, n, d in tris)
    vmat_info = (struct.pack('<I', 0) + _rgb(_scale(colour, 0.50)) + _rgb(colour)
                 + _rgb((0, 0, 0)) + _rgb(_scale(colour, 0.07))
                 + struct.pack('<3f', 1.0, 1.0, 0.0))
    vmat = chunk(VERTEX_MATERIAL,
                 chunk(VERTEX_MATERIAL_NAME, b'Default\0')
                 + chunk(VERTEX_MATERIAL_INFO, vmat_info), subs=True)
    shader = bytes([3, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    mat_pass = chunk(MATERIAL_PASS,
                     chunk(VERTEX_MATERIAL_IDS, struct.pack('<I', 0))
                     + chunk(SHADER_IDS, struct.pack('<I', 0)), subs=True)
    return chunk(MESH,
                 chunk(MESH_HEADER3, header)
                 + chunk(VERTICES, vert_b)
                 + chunk(VERTEX_NORMALS, norm_b)
                 + chunk(TRIANGLES, tri_b)
                 + chunk(MATERIAL_INFO, struct.pack('<4I', 1, 1, 1, 0))
                 + chunk(VERTEX_MATERIALS, vmat, subs=True)
                 + chunk(SHADERS, shader)
                 + mat_pass,
                 subs=True)
