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

# cell 3 region: power-meter pixels for the engine's W3DPowerDraw
# (hardcoded image names). Tick cells are 6x10 (5px color + 1px trough
# separator - the sheet has no alpha, so the separator IS the trough
# color); the needle is 4x10, bright core with trough edges.
TROUGH = (16, 20, 27)
PGREEN = (96, 168, 104)
PAMBER = GOLD
PRED   = (198, 74, 60)
NEEDLE = (242, 232, 202)
def tick_cell(x0, color):
    for y in range(10):
        for x in range(6):
            px(x0 + x, y, TROUGH if x == 5 else color)
def needle_cell(x0):
    for y in range(10):
        for x in range(4):
            px(x0 + x, y, TROUGH if x in (0, 3) else NEEDLE)
tick_cell(192, PGREEN)    # PowerPointG
tick_cell(200, PAMBER)    # PowerPointY
tick_cell(208, PRED)      # PowerPointR
needle_cell(216)          # PowerBarSlider

# cell 3 lower area: the idle-worker button glyph (hard hat + wrench)
O3 = CELL * 3
blob(O3 + 26, 34, 9, DIM)                      # head
blob(O3 + 26, 34, 6, (214, 178, 148))
poly_fill(O3, [(14, 28), (38, 28), (36, 22), (16, 22)], GOLD)   # hat brim
poly_fill(O3, [(18, 22), (34, 22), (32, 15), (20, 15)], GOLD)   # hat crown
line(O3 + 40, 44, O3 + 52, 32, GOLD, 2)        # wrench shaft
blob(O3 + 53, 30, 4, GOLD); blob(O3 + 55, 28, 2, FACE)          # wrench jaw

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

def main():
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('targets',nargs='*',type=Path)
    parser.add_argument('--data',type=Path,default=Path(__file__).resolve().parents[1]/'data')
    args=parser.parse_args()
    targets=args.targets or [args.data/'Art/Textures/wp_cmdglyphs.tga']
    for t in targets:
        Path(t).parent.mkdir(parents=True,exist_ok=True)
        write(t)

if __name__=='__main__':main()
