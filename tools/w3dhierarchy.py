# SPDX-License-Identifier: MIT
"""Canonical W3D pivot ordering and HLOD index remapping.

The native hierarchy and Blender importer both need parents before children.
Only reorder embedded hierarchies; shared infantry rigs keep their own contract.
"""
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wp_w3d import (HIERARCHY, HLOD, HLOD_LOD_ARRAY, HLOD_SUB_OBJECT, NO_PARENT,  # noqa: E402
                    PIVOTS, PIVOT_SIZE, chunk, chunks)


def canonicalize(data):
    hierarchy = next((p for c, s, p in chunks(data) if c == HIERARCHY), None)
    if hierarchy is None:
        return data
    pivotdata = next(p for c, s, p in chunks(hierarchy) if c == PIVOTS)
    pivots = [pivotdata[i:i + PIVOT_SIZE] for i in range(0, len(pivotdata), PIVOT_SIZE)]
    parents = [struct.unpack_from('<I', p, 16)[0] for p in pivots]
    order = []
    pending = list(range(len(pivots)))
    while pending:
        ready = [i for i in pending if parents[i] == NO_PARENT or parents[i] in order]
        if not ready:
            raise ValueError('Cyclic or missing W3D pivot parent')
        order.extend(ready)
        pending = [i for i in pending if i not in ready]
    remap = {old: new for new, old in enumerate(order)}
    updated = b''.join(pivots[i][:16] + struct.pack('<I', remap.get(parents[i], NO_PARENT)) + pivots[i][20:]
                       for i in order)
    result = b''
    for c, s, p in chunks(data):
        if c == HIERARCHY:
            p = b''.join(chunk(d, updated if d == PIVOTS else q, subs=t) for d, t, q in chunks(p))
        if c == HLOD:
            inner = b''
            for d, t, q in chunks(p):
                if d == HLOD_LOD_ARRAY:
                    q = b''.join(chunk(e, struct.pack('<I', remap[struct.unpack_from('<I', r)[0]]) + r[4:]
                                       if e == HLOD_SUB_OBJECT else r, subs=u)
                                 for e, u, r in chunks(q))
                inner += chunk(d, q, subs=t)
            p = inner
        result += chunk(c, p, subs=s)
    return result
