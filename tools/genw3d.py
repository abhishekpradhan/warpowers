#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""War Powers .w3d generator — part-composed low-poly utility models.

Byte layout extracted from the GPL engine's own reader (chunk framing per
WWLib/chunkio, structs per WW3D2/w3d_file.h; see wp_w3d.py). Each model is a
list of PARTS; every part becomes its own single-color mesh chunk, aggregated
by one HLod, so silhouettes come from composition and identity from the
faction palette (docs/creative.md). Little-endian throughout.

Primitive: a rectangular FRUSTUM — bottom rectangle (sx, sy) centered at
(cx, cy) with base at z, top rectangle scaled by (tx, ty) and shifted by
(ox, oy), height sz. tx=ty=1 is a box; tx,ty<1 gives sloped faceted sides.
All six faces stay planar. Axis-aligned only.

Every roster unit and structure is a painted Blender asset from
tools/blender/build_polish.py and is listed in polish_assets.json; this file
only owns the engine-facing utility models (projectiles, markers, scaffolds and
the historical boot-slice troopers). A model name present in both places is a
hard error so a rerun can never overwrite a production asset.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wp_w3d import (HLOD, HLOD_HEADER, HLOD_LOD_ARRAY, HLOD_SUB_OBJECT,  # noqa: E402
                    SUB_OBJECT_ARRAY_HEADER, chunk, mesh_chunk, name16, name32)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'tools/blender/polish_assets.json'


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
    name16(name)  # mesh names are 16-byte fields; refuse anything that would truncate
    return (name, PAL[color] if isinstance(color, str) else color,
            frustum(cx, cy, z, sx, sy, sz, tx, ty, ox, oy))


# ---- w3d emission ----
def build_w3d(model, parts):
    meshes = b"".join(mesh_chunk(model, n, c, g) for n, c, g in parts)
    subs = b"".join(
        chunk(HLOD_SUB_OBJECT, struct.pack("<I32s", 0, name32(f"{model}.{n}")))
        for n, _, _ in parts)
    hlod = chunk(HLOD,
                 chunk(HLOD_HEADER, struct.pack("<II16s16s", 0x00010000, 1,
                                                name16(model), b""))
                 + chunk(HLOD_LOD_ARRAY,
                         chunk(SUB_OBJECT_ARRAY_HEADER,
                               struct.pack("<If", len(parts), 3.4028235e38))
                         + subs, subs=True),
                 subs=True)
    return meshes + hlod


# ---- the models (docs/creative.md rosters; unit faces +X at angle 0) ----
MODELS = {
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
    # Named apart from the WPROCK01 boulder prop, which build_polish.py owns.
    "WPRKT01": [
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


MODELS["WPSCAF01"] = scaffold(11, 11, 12)
MODELS["WPSCAF02"] = scaffold(19, 17, 18)


# Infantry: chunky minifig troopers matching the boot-slice blocky look.
# Faces +X at angle 0 (rifle forward). ~7 world units tall. Historical
# boot-slice bodies; the roster infantry are painted MER/JAK*02 assets.
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


def catalog_models(catalog=CATALOG):
    """Upper-case ids of every production model build_polish.py owns."""
    return {name.upper() for name in json.loads(Path(catalog).read_text())}


def write_models(out_dir, models=MODELS, protected=frozenset()):
    """Write every model; a name shared with the production catalog is fatal."""
    clash = sorted(set(models) & {name.upper() for name in protected})
    if clash:
        raise ValueError('model name(s) owned by tools/blender/build_polish.py: ' + ', '.join(clash)
                         + ' (rename the genw3d entry; a rerun must never overwrite a painted asset)')
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for model, parts in models.items():
        path = out_dir / (model.lower() + '.w3d')
        data = build_w3d(model, parts)
        path.write_bytes(data)
        tris = sum(len(g[2]) for _, _, g in parts)
        print(f'wrote {path} ({len(data)} bytes, {len(parts)} parts, {tris} tris)')
        written.append(path)
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description='Generate the utility part-language models; '
                                     'production assets from the Blender catalog are refused, not skipped.')
    parser.add_argument('output', nargs='?', type=Path, default=ROOT / 'data/Art/W3D',
                        help='destination directory (default: the repository dataset)')
    args = parser.parse_args(argv)
    write_models(args.output, MODELS, catalog_models())


if __name__ == '__main__':
    main()
