# SPDX-License-Identifier: MIT
"""Ownership panels for the retained original base kit, applied after export."""
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genw3d import frustum  # noqa: E402
from wp_w3d import (HLOD, HLOD_LOD_ARRAY, HLOD_SUB_OBJECT, MESH, MESH_HEADER3,  # noqa: E402
                    SUB_OBJECT_ARRAY_HEADER, chunk, chunks, mesh_chunk, name32)

PANELS = {
    'mercc01': (-2, -5, 28.46, 4.2, 4.2, .10),
    'jakcp01': (-3, 0, 12.27, 4.5, 4.5, .10),
    'merpp01': (-2, 0, 14.12, 4.5, 5, .10),
    'merwf01': (21, -6, 10.36, 4.5, 5, .10),
    'jakcs01': (0, 0, 16.67, 7, 2, .10),
    'mersuv01': (-1.8, 0, 8.36, 2.1, 2.7, .10),
    'jakrig01': (5, 0, 6.76, 2.4, 2.8, .10),
}


def apply(path):
    path = Path(path)
    model = path.stem.lower()
    if model not in PANELS:
        return
    # Reruns are idempotent. Older base models bind everything to the root.
    data = path.read_bytes()
    name = 'HOUSECOLOR0'
    out = b''
    for c, s, p in chunks(data):
        if c == MESH:
            header = next(q for d, t, q in chunks(p) if d == MESH_HEADER3)
            if header[8:24].split(b'\0')[0].startswith(b'HOUSECOLOR'):
                continue
        if c == HLOD:
            out += mesh_chunk(model.upper(), name, (220, 220, 220), frustum(*PANELS[model]))
            inner = b''
            for d, t, q in chunks(p):
                if d == HLOD_LOD_ARRAY:
                    entries = [(e, u, r) for e, u, r in chunks(q) if e != HLOD_SUB_OBJECT or b'.HOUSECOLOR' not in r]
                    entries.append((HLOD_SUB_OBJECT, False, struct.pack('<I32s', 0, name32(model.upper() + '.' + name))))
                    count = sum(e == HLOD_SUB_OBJECT for e, u, r in entries)
                    q = b''.join(chunk(e, struct.pack('<I', count) + r[4:] if e == SUB_OBJECT_ARRAY_HEADER else r, subs=u)
                                 for e, u, r in entries)
                inner += chunk(d, q, subs=t)
            p = inner
        out += chunk(c, p, subs=s)
    path.write_bytes(out)
