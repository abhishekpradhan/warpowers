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


def write_glow(path):
    """32x32 additive sprite: black field, warm-white radial core."""
    n = 32
    hdr = bytearray(18); hdr[2] = 2
    struct.pack_into("<HH", hdr, 12, n, n); hdr[16] = 24; hdr[17] = 0x20
    body = bytearray()
    for y in range(n):
        for x in range(n):
            dx, dy = (x - 15.5) / 14.0, (y - 15.5) / 14.0
            r = (dx * dx + dy * dy) ** 0.5
            t = max(0.0, 1.0 - r)
            v = t * t
            body += bytes((clamp(255 * v * 0.55), clamp(255 * v * 0.85), clamp(255 * v)))
    with open(path, "wb") as f:
        f.write(bytes(hdr) + bytes(body))
    print(f"wrote {path}")

def write_soft(path):
    """32x32 alpha sprite: neutral gray, radial alpha falloff (smoke/dust)."""
    n = 32
    hdr = bytearray(18); hdr[2] = 2
    struct.pack_into("<HH", hdr, 12, n, n); hdr[16] = 32; hdr[17] = 0x28
    body = bytearray()
    for y in range(n):
        for x in range(n):
            dx, dy = (x - 15.5) / 15.0, (y - 15.5) / 15.0
            r = (dx * dx + dy * dy) ** 0.5
            t = max(0.0, 1.0 - r)
            a = clamp(255 * t * t)
            body += bytes((150, 158, 168, a))
    with open(path, "wb") as f:
        f.write(bytes(hdr) + bytes(body))
    print(f"wrote {path}")

def write_rallyline(path):
    """64x8 additive line texture, tiled along rally/waypoint segmented
    lines: bright gold core dash with soft head/tail so tiling reads as a
    dotted energy path."""
    w, h = 64, 8
    hdr = bytearray(18); hdr[2] = 2
    struct.pack_into("<HH", hdr, 12, w, h); hdr[16] = 24; hdr[17] = 0x20
    body = bytearray()
    for y in range(h):
        dy = abs((y - 3.5) / 3.5)
        vy = max(0.0, 1.0 - dy * dy)
        for x in range(w):
            t = x / (w - 1.0)
            dash = max(0.0, 1.0 - abs(t - 0.5) * 2.6)
            v = vy * (dash ** 1.5)
            body += bytes((clamp(255 * v * 0.35), clamp(255 * v * 0.72), clamp(255 * v)))
    with open(path, "wb") as f:
        f.write(bytes(hdr) + bytes(body))
    print(f"wrote {path}")

def write_scorch(path):
    """256px scorch atlas (engine hardcodes EXScorch01.tga; 4x4 UV grid,
    SCORCH_PER_ROW=3 with 1.5-cell spacing -> marks at cells (0,0),(1,0),
    (2,0),(0,1), each mark spanning a quarter of the texture, alpha-blended)."""
    import random
    n = 256
    hdr = bytearray(18); hdr[2] = 2
    struct.pack_into("<HH", hdr, 12, n, n); hdr[16] = 32; hdr[17] = 0x28
    px = [[(0, 0, 0, 0)] * n for _ in range(n)]
    centers = [(32, 32, 1), (128, 32, 2), (224, 32, 3), (32, 128, 4)]
    for cx, cy, seed in centers:
        rng = random.Random(seed * 77)
        blobs = [(0.0, 0.0, 1.0)] + [
            (rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), rng.uniform(0.35, 0.6))
            for _ in range(3)]
        for y in range(cy - 31, cy + 32):
            for x in range(cx - 31, cx + 32):
                dx, dy = (x - cx) / 30.0, (y - cy) / 30.0
                a = 0.0
                for bx, by, br in blobs:
                    d = (((dx - bx) / br) ** 2 + ((dy - by) / br) ** 2) ** 0.5
                    a = max(a, 1.0 - d)
                if a <= 0.0:
                    continue
                a *= a * rng.uniform(0.75, 1.0)          # soft edge + grime
                shade = rng.uniform(0.85, 1.0)
                px[y][x] = (int(24 * shade), int(20 * shade), int(16 * shade),
                            clamp(235 * a))
    body = bytearray()
    for y in range(n):
        for x in range(n):
            r, g, b, a = px[y][x]
            body += bytes((b, g, r, a))
    with open(path, "wb") as f:
        f.write(bytes(hdr) + bytes(body))
    print(f"wrote {path}")

def write_concrete(path):
    """256x512 concrete sheet: 4x8 grid of 64px tiles. Rows 0-3 clean panels
    (seam lines, subtle stains), rows 4-7 worn (cracks, sand encroachment) for
    apron edges. Same top-left-origin 24-bit TGA as the ground sheet."""
    import random as _r
    CW, CH = 256, 256
    CBASE = (152, 149, 142)
    SAND = BASE
    cimg = [[CBASE for _ in range(CW)] for _ in range(CH)]
    for ti in range(16):
        tx, ty = ti % 4, ti // 4
        worn = ti >= 8
        rng = _r.Random(500 + ti)
        tone = rng.uniform(-6, 6)
        coarse = value_noise_grid(TILE, 4, -6, 6, 900 + ti * 3)
        fine = value_noise_grid(TILE, 16, -3, 3, 901 + ti * 3)
        for y in range(TILE):
            for x in range(TILE):
                d = tone + coarse[y][x] + fine[y][x]
                px = (clamp(CBASE[0] + d), clamp(CBASE[1] + d), clamp(CBASE[2] + d * 0.97))
                cimg[ty * TILE + y][tx * TILE + x] = px
        # panel seams: darker lines at tile borders + one mid seam
        for y in range(TILE):
            for x in range(TILE):
                on_seam = (x < 1 or y < 1 or x == 32 or y == 32)
                if on_seam:
                    pxl = cimg[ty * TILE + y][tx * TILE + x]
                    dk = 14 if (x == 32 or y == 32) else 20
                    cimg[ty * TILE + y][tx * TILE + x] = (
                        clamp(pxl[0] - dk), clamp(pxl[1] - dk), clamp(pxl[2] - dk))
        # stains
        for _ in range(rng.randint(1, 3)):
            cx, cy = rng.randrange(6, TILE - 6), rng.randrange(6, TILE - 6)
            rad = rng.uniform(3, 8)
            dk = rng.uniform(6, 14)
            for oy in range(-int(rad), int(rad) + 1):
                for ox in range(-int(rad), int(rad) + 1):
                    if ox * ox + oy * oy > rad * rad:
                        continue
                    yy, xx = ty * TILE + cy + oy, tx * TILE + cx + ox
                    if 0 <= yy < CH and 0 <= xx < CW:
                        pxl = cimg[yy][xx]
                        f = 1.0 - (ox * ox + oy * oy) / (rad * rad)
                        cimg[yy][xx] = (clamp(pxl[0] - dk * f), clamp(pxl[1] - dk * f), clamp(pxl[2] - dk * f))
        if worn:
            # cracks: dark random walks
            for _ in range(rng.randint(2, 4)):
                x, y = rng.randrange(TILE), rng.randrange(TILE)
                for _ in range(rng.randint(14, 30)):
                    yy, xx = ty * TILE + y, tx * TILE + x
                    if 0 <= yy < CH and 0 <= xx < CW:
                        pxl = cimg[yy][xx]
                        cimg[yy][xx] = (clamp(pxl[0] - 26), clamp(pxl[1] - 26), clamp(pxl[2] - 26))
                    x += rng.choice((-1, 0, 1)); y += rng.choice((-1, 0, 1))
                    x = max(0, min(TILE - 1, x)); y = max(0, min(TILE - 1, y))
            # sand encroachment: blotches lerped toward the sand base
            for _ in range(rng.randint(3, 6)):
                cx, cy = rng.randrange(TILE), rng.randrange(TILE)
                rad = rng.uniform(4, 11)
                for oy in range(-int(rad), int(rad) + 1):
                    for ox in range(-int(rad), int(rad) + 1):
                        d2 = ox * ox + oy * oy
                        if d2 > rad * rad:
                            continue
                        yy, xx = ty * TILE + cy + oy, tx * TILE + cx + ox
                        if 0 <= yy < CH and 0 <= xx < CW:
                            f = 0.75 * (1.0 - d2 / (rad * rad))
                            pxl = cimg[yy][xx]
                            cimg[yy][xx] = (
                                clamp(pxl[0] * (1 - f) + SAND[0] * f),
                                clamp(pxl[1] * (1 - f) + SAND[1] * f),
                                clamp(pxl[2] * (1 - f) + SAND[2] * f))
    hdr = bytearray(18)
    hdr[2] = 2
    struct.pack_into("<HH", hdr, 12, CW, CH)
    hdr[16] = 24
    hdr[17] = 0x20
    body = bytearray()
    for row in cimg:
        for (r, g, b) in row:
            body += bytes((b, g, r))
    with open(path, "wb") as f:
        f.write(bytes(hdr) + bytes(body))
    print(f"wrote {path}")

def write_icons(path):
    """64x32 icon sheet, 32-bit alpha: heal cross (0..31), no-power bolt (32..63)."""
    W2, H2 = 64, 32
    hdr = bytearray(18); hdr[2] = 2
    struct.pack_into("<HH", hdr, 12, W2, H2); hdr[16] = 32; hdr[17] = 0x28
    px = [[(0, 0, 0, 0)] * W2 for _ in range(H2)]
    # heal cross: green with white outline feel
    for y in range(32):
        for x in range(32):
            cx, cy = x - 15.5, y - 15.5
            in_v = abs(cx) <= 4.5 and abs(cy) <= 12.5
            in_h = abs(cy) <= 4.5 and abs(cx) <= 12.5
            if in_v or in_h:
                edge = (abs(cx) > 3.0 and in_v and not in_h) or (abs(cy) > 3.0 and in_h and not in_v)
                px[y][x] = (235, 255, 240, 255) if edge else (70, 200, 90, 255)
    # power bolt: gold zigzag on faint dark disc
    bolt = [(38+14,3),(38+10,13),(38+14,13),(38+8,27),(38+12,16),(38+8,16)]
    for y in range(32):
        for x in range(32, 64):
            cx, cy = x - 47.5, y - 15.5
            r = (cx * cx + cy * cy) ** 0.5
            if r < 14:
                px[y][x] = (30, 30, 34, 170)
    def line(x0, y0, x1, y1):
        n = max(abs(x1 - x0), abs(y1 - y0)) * 2 + 1
        for i in range(int(n) + 1):
            t = i / n
            xx, yy = int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t)
            for oy in (-1, 0, 1):
                for ox in (-1, 0, 1):
                    if 0 <= yy + oy < 32 and 32 <= xx + ox < 64:
                        px[yy + oy][xx + ox] = (255, 210, 80, 255)
    for i in range(len(bolt) - 1):
        line(*bolt[i], *bolt[i + 1])
    body = bytearray()
    for y in range(H2):
        for x in range(W2):
            r, g, b, a = px[y][x]
            body += bytes((b, g, r, a))
    with open(path, "wb") as f:
        f.write(bytes(hdr) + bytes(body))
    print(f"wrote {path}")

targets = sys.argv[1:] or [
    os.path.expanduser("~/GeneralsX/GeneralsZH/Art/Terrain/wp_ground.tga"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "data", "Art", "Terrain", "wp_ground.tga"),
]
for t in targets:
    write_tga(t)
    texdir = os.path.join(os.path.dirname(os.path.dirname(t)), "Textures")
    write_shadow(os.path.join(texdir, "shadow.tga"))
    write_glow(os.path.join(texdir, "wp_glow.tga"))
    write_soft(os.path.join(texdir, "wp_soft.tga"))
    write_scorch(os.path.join(texdir, "EXScorch01.tga"))
    write_rallyline(os.path.join(texdir, "wp_rallyline.tga"))
    write_concrete(os.path.join(os.path.dirname(t), "wp_concrete.tga"))
    write_icons(os.path.join(texdir, "wp_icons.tga"))
