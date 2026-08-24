#!/usr/bin/env python3
"""Command-glyph sheet: wp_cmdglyphs.tga (256x64, 4 cells of 64px).

Gold vector-ish glyphs on the command-button face color, for the order
buttons (attack-move / guard / stop) that portraits don't cover. Separate
sheet from wp_cmdicons.tga so the Blender portrait pipeline stays untouched.
"""
import os
import struct
import sys

CELL, COLS = 64, 4
W, H = CELL * COLS, CELL
FACE = (34, 38, 44)
GOLD = (215, 180, 90)
DIM  = (150, 128, 70)

img = [[FACE for _ in range(W)] for _ in range(H)]

def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img[y][x] = c

def blob(cx, cy, r, c):
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                px(x, y, c)

def line(x0, y0, x1, y1, c, w=2):
    steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(steps + 1):
        t = i / steps
        blob(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, w, c)

def poly_fill(cx_off, pts, c):
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        xs = []
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            for x in range(int(xs[j]), int(xs[j + 1]) + 1):
                px(cx_off + x, y, c)

# cell 0: attack-move — chevron arrows driving right into a target dot
O = 0
line(O + 12, 20, O + 24, 32, GOLD, 3); line(O + 24, 32, O + 12, 44, GOLD, 3)
line(O + 26, 20, O + 38, 32, GOLD, 3); line(O + 38, 32, O + 26, 44, GOLD, 3)
blob(O + 49, 32, 7, DIM); blob(O + 49, 32, 4, FACE); blob(O + 49, 32, 2, GOLD)

# cell 1: guard — filled shield
O = CELL
poly_fill(O, [(32, 12), (50, 19), (48, 38), (32, 52), (16, 38), (14, 19)], DIM)
poly_fill(O, [(32, 17), (45, 22), (43, 37), (32, 46), (21, 37), (19, 22)], GOLD)
poly_fill(O, [(32, 24), (38, 27), (37, 34), (32, 39), (27, 34), (26, 27)], FACE)

# cell 2: stop — octagon
O = CELL * 2
oct_pts = [(25, 12), (39, 12), (50, 23), (50, 41), (39, 52), (25, 52), (14, 41), (14, 23)]
poly_fill(O, oct_pts, DIM)
poly_fill(O, [(x + (32 - x) * 0.18, y + (32 - y) * 0.18) for x, y in oct_pts], GOLD)
line(O + 25, 32, O + 39, 32, FACE, 3)

# cell 3: spare (blank face)

def write(path):
    hdr = bytearray(18)
    hdr[2] = 2
    struct.pack_into("<HH", hdr, 12, W, H)
    hdr[16] = 24
    hdr[17] = 0x20
    body = bytearray()
    for row in img:
        for (r, g, b) in row:
            body += bytes((b, g, r))
    with open(path, "wb") as f:
        f.write(bytes(hdr) + bytes(body))
    print(f"wrote {path}")

targets = sys.argv[1:] or [
    os.path.expanduser("~/GeneralsX/GeneralsZH/Art/Textures/wp_cmdglyphs.tga"),
    os.path.join(os.path.dirname(__file__), "..", "data", "Art", "Textures", "wp_cmdglyphs.tga"),
]
for t in targets:
    write(t)
