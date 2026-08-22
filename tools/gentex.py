#!/usr/bin/env python3
"""War Powers terrain texture generator.

Paints wp_ground.tga: a 256x256 desert sheet the engine reads as a 4x4 grid
of 64x64 tiles (16 variants; genmap indexes them per-cell to kill repetition).
Stylized-clean per the creative bible: desaturated sand base, low-contrast
grain, sparse pebble speckle, occasional streak tiles. Deterministic (seeded).
Raw 24-bit TGA, top-left origin, no deps.
"""
import os
import random
import struct
import sys

SIZE, TILE = 256, 64
BASE = (171, 158, 136)   # desaturated warm sand (RGB)

rng = random.Random(1917)

def value_noise_grid(n, cells, lo, hi, seed):
    """n x n bilinear-interpolated value noise in [lo, hi]."""
    r = random.Random(seed)
    g = [[r.uniform(lo, hi) for _ in range(cells + 1)] for _ in range(cells + 1)]
    out = [[0.0] * n for _ in range(n)]
    step = n / cells
    for y in range(n):
        gy = y / step
        y0 = int(gy); fy = gy - y0
        fy = fy * fy * (3 - 2 * fy)
        for x in range(n):
            gx = x / step
            x0 = int(gx); fx = gx - x0
            fx = fx * fx * (3 - 2 * fx)
            a = g[y0][x0] * (1 - fx) + g[y0][x0 + 1] * fx
            b = g[y0 + 1][x0] * (1 - fx) + g[y0 + 1][x0 + 1] * fx
            out[y][x] = a * (1 - fy) + b * fy
    return out

def clamp(v):
    return 0 if v < 0 else 255 if v > 255 else int(v)

# per-pixel luminance offset buffer for the whole sheet
img = [[BASE for _ in range(SIZE)] for _ in range(SIZE)]

for ty in range(SIZE // TILE):
    for tx in range(SIZE // TILE):
        tile_i = ty * 4 + tx
        seed = 100 + tile_i
        # tile-level tone shift keeps variants distinguishable but subtle
        tone = random.Random(seed).uniform(-7, 7)
        coarse = value_noise_grid(TILE, 4, -9, 9, seed * 3 + 1)
        fine = value_noise_grid(TILE, 16, -5, 5, seed * 3 + 2)
        for y in range(TILE):
            for x in range(TILE):
                d = tone + coarse[y][x] + fine[y][x]
                px = (clamp(BASE[0] + d), clamp(BASE[1] + d * 0.96), clamp(BASE[2] + d * 0.88))
                img[ty * TILE + y][tx * TILE + x] = px
        # sparse pebbles: small darker clusters
        r = random.Random(seed * 7)
        for _ in range(r.randint(4, 9)):
            cx, cy = r.randrange(2, TILE - 2), r.randrange(2, TILE - 2)
            dk = r.uniform(14, 26)
            for oy in range(-1, 2):
                for ox in range(-1, 2):
                    if abs(ox) + abs(oy) > 1 and r.random() < 0.5:
                        continue
                    yy, xx = ty * TILE + cy + oy, tx * TILE + cx + ox
                    p = img[yy][xx]
                    img[yy][xx] = (clamp(p[0] - dk), clamp(p[1] - dk), clamp(p[2] - dk * 0.9))
        # streak tiles: a few variants carry faint wind-scour lines
        if tile_i in (3, 6, 9, 12):
            r2 = random.Random(seed * 11)
            for _ in range(r2.randint(2, 3)):
                yline = r2.randrange(6, TILE - 6)
                amp = r2.uniform(5, 9)
                for x in range(TILE):
                    yy = ty * TILE + yline + int(2.2 * (value_noise_grid(1, 1, -1, 1, x)[0][0]))
                    yy = max(ty * TILE, min(ty * TILE + TILE - 1, yy))
                    p = img[yy][tx * TILE + x]
                    img[yy][tx * TILE + x] = (clamp(p[0] - amp), clamp(p[1] - amp), clamp(p[2] - amp))

def write_tga(path):
    hdr = bytearray(18)
    hdr[2] = 2
    struct.pack_into("<HH", hdr, 12, SIZE, SIZE)
    hdr[16] = 24
    hdr[17] = 0x20  # top-left origin
    body = bytearray()
    for row in img:
        for (r, g, b) in row:
            body += bytes((b, g, r))
    with open(path, "wb") as f:
        f.write(bytes(hdr) + bytes(body))
    print(f"wrote {path} ({len(hdr) + len(body)} bytes)")

def write_shadow(path):
    """64x64 multiplicative blob: white field, soft dark ellipse."""
    n = 64
    hdr = bytearray(18)
    hdr[2] = 2
    struct.pack_into("<HH", hdr, 12, n, n)
    hdr[16] = 24
    hdr[17] = 0x20
    body = bytearray()
    for y in range(n):
        for x in range(n):
            dx, dy = (x - 31.5) / 27.0, (y - 31.5) / 27.0
            r = (dx * dx + dy * dy) ** 0.5
            t = max(0.0, min(1.0, (r - 0.55) / 0.45))
            t = t * t * (3 - 2 * t)                 # 0 center -> 1 edge
            v = clamp(110 + 145 * t)                # 110 core, 255 rim
            body += bytes((v, v, v))
    with open(path, "wb") as f:
        f.write(bytes(hdr) + bytes(body))
    print(f"wrote {path} ({len(hdr) + len(body)} bytes)")

targets = sys.argv[1:] or [
    os.path.expanduser("~/GeneralsX/GeneralsZH/Art/Terrain/wp_ground.tga"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "data", "Art", "Terrain", "wp_ground.tga"),
]
for t in targets:
    write_tga(t)
    shadow = os.path.join(os.path.dirname(os.path.dirname(t)), "Textures", "shadow.tga")
    write_shadow(shadow)
