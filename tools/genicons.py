#!/usr/bin/env python3
"""Command-button icon sheet: wp_cmdicons.tga, 4x4 grid of 64px icons.

Programmatic silhouette icons on faction-tinted plates — readable at 40px,
consistent language: vehicles as side profiles, structures as front
elevations, build-actions framed by the gold construct bracket.
Slots (row-major): 0 vector, 1 outrider, 2 zenith, 3 fabricator,
4 mongrel, 5 vulture, 6 rigger, 7 powerarray, 8 vehicleplant, 9 bulwark,
10 chopshop, 11 watchpost, 12 generic.
"""
import os
import struct

S = 64
GRID = 4
W = H = S * GRID

MER_BG = (46, 52, 60)
JAK_BG = (56, 46, 38)
WHITE = (232, 236, 240)
STEEL = (184, 194, 204)
GOLD = (215, 180, 90)
SAND = (201, 176, 138)
RUST = (138, 90, 60)
GUN = (90, 96, 104)

img = [[(20, 22, 26) for _ in range(W)] for _ in range(H)]


def plate(ix, bg):
    x0, y0 = (ix % GRID) * S, (ix // GRID) * S
    for y in range(4, S - 4):
        for x in range(4, S - 4):
            edge = x < 6 or x > S - 7 or y < 6 or y > S - 7
            c = tuple(int(v * (1.25 if edge else 1.0)) for v in bg)
            img[y0 + y][x0 + x] = c
    return x0, y0


def rect(x0, y0, x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if 0 <= yy < S and 0 <= xx < S:
                img[y0 + yy][x0 + xx] = c


def tank(ix, bg, hull, turret):
    x0, y0 = plate(ix, bg)
    rect(x0, y0, 10, 38, 44, 10, hull)          # hull
    rect(x0, y0, 8, 46, 48, 6, (30, 32, 36))    # tracks
    rect(x0, y0, 22, 28, 18, 10, turret)        # turret
    rect(x0, y0, 40, 30, 16, 4, GUN)            # barrel


def scout(ix, bg, hull):
    x0, y0 = plate(ix, bg)
    rect(x0, y0, 14, 40, 36, 8, hull)
    rect(x0, y0, 12, 46, 40, 5, (30, 32, 36))
    rect(x0, y0, 24, 32, 12, 8, hull)
    rect(x0, y0, 36, 34, 10, 3, GUN)


def artillery(ix, bg, hull):
    x0, y0 = plate(ix, bg)
    rect(x0, y0, 10, 40, 40, 9, hull)
    rect(x0, y0, 8, 47, 44, 5, (30, 32, 36))
    for i in range(22):                          # long raised barrel
        rect(x0, y0, 22 + i, 36 - i // 2, 3, 3, GUN)


def dozer(ix, bg, body, blade):
    x0, y0 = plate(ix, bg)
    rect(x0, y0, 16, 36, 26, 12, body)
    rect(x0, y0, 14, 46, 34, 5, (30, 32, 36))
    rect(x0, y0, 30, 28, 12, 8, body)
    rect(x0, y0, 44, 32, 6, 16, blade)          # blade


def structure(ix, bg, wall, roof, tall=False):
    x0, y0 = plate(ix, bg)
    h = 26 if tall else 18
    rect(x0, y0, 14, 48 - h, 36, h, wall)
    rect(x0, y0, 12, 46 - h - 4, 40, 6, roof)
    rect(x0, y0, 28, 40, 8, 8, (30, 32, 36))    # door


def turret_icon(ix, bg, base, head):
    x0, y0 = plate(ix, bg)
    rect(x0, y0, 22, 40, 20, 8, base)
    rect(x0, y0, 24, 30, 16, 10, head)
    rect(x0, y0, 38, 32, 14, 4, GUN)


def tower(ix, bg, legs, deck):
    x0, y0 = plate(ix, bg)
    rect(x0, y0, 22, 30, 4, 18, legs)
    rect(x0, y0, 38, 30, 4, 18, legs)
    rect(x0, y0, 18, 22, 28, 8, deck)
    rect(x0, y0, 40, 24, 12, 3, GUN)


def power(ix, bg):
    x0, y0 = plate(ix, bg)
    rect(x0, y0, 14, 34, 26, 14, WHITE)
    rect(x0, y0, 40, 20, 6, 28, STEEL)          # stack
    rect(x0, y0, 39, 26, 8, 3, GOLD)            # ring
    rect(x0, y0, 47, 20, 6, 28, STEEL)
    rect(x0, y0, 46, 26, 8, 3, GOLD)


def generic(ix, bg):
    x0, y0 = plate(ix, bg)
    rect(x0, y0, 28, 24, 8, 20, GOLD)
    rect(x0, y0, 22, 30, 20, 8, GOLD)


tank(0, MER_BG, STEEL, WHITE)
scout(1, MER_BG, STEEL)
artillery(2, MER_BG, STEEL)
dozer(3, MER_BG, WHITE, GOLD)
tank(4, JAK_BG, SAND, RUST)
scout(5, JAK_BG, SAND)
dozer(6, JAK_BG, SAND, RUST)
power(7, MER_BG)
structure(8, MER_BG, WHITE, GOLD, tall=True)
turret_icon(9, MER_BG, WHITE, STEEL)
structure(10, JAK_BG, SAND, RUST, tall=True)
tower(11, JAK_BG, GUN, SAND)
generic(12, MER_BG)

targets = [os.path.expanduser("~/GeneralsX/GeneralsZH/Art/Textures/wp_cmdicons.tga"),
           os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "Art", "Textures", "wp_cmdicons.tga")]
hdr = bytearray(18)
hdr[2] = 2
struct.pack_into("<HH", hdr, 12, W, H)
hdr[16] = 24
hdr[17] = 0x20
body = bytearray()
for row in img:
    for (r, g, b) in row:
        body += bytes((b, g, r))
for t in targets:
    os.makedirs(os.path.dirname(t), exist_ok=True)
    with open(t, "wb") as f:
        f.write(bytes(hdr) + bytes(body))
    print("wrote", t)
