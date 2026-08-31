#!/usr/bin/env python3
"""Second command-icon sheet (wp_cmdicons2.tga): drawn portraits for units
added after the Blender portrait sheet filled up (rocket troopers, aircraft).
Stylized silhouette on the faction plate, same plate colors as sheet one.
Writes the TGA (both targets) and the MappedImages INI."""
import os
import struct

CELL, GRID = 128, 5
SIZE = CELL * GRID
MER = (46, 52, 60)
JAK = (56, 46, 38)
STEEL = (184, 194, 204)
SAND = (201, 176, 138)
GOLD = (215, 180, 90)
DARK = (26, 28, 33)

sheet = [[(16, 17, 20) for _ in range(SIZE)] for _ in range(SIZE)]

def px(x, y, c):
    if 0 <= x < SIZE and 0 <= y < SIZE:
        sheet[y][x] = c

def rect(x0, y0, x1, y1, c):
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            px(x, y, c)

def disc(cx, cy, r, c):
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                px(x, y, c)

def tri(p0, p1, p2, c):
    pts = [p0, p1, p2]
    miny = int(min(p[1] for p in pts)); maxy = int(max(p[1] for p in pts))
    for y in range(miny, maxy + 1):
        xs = []
        for i in range(3):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % 3]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        if len(xs) >= 2:
            for x in range(int(xs[0]), int(xs[-1]) + 1):
                px(x, y, c)

def plate(ix, color):
    cx, cy = (ix % GRID) * CELL, (ix // GRID) * CELL
    for y in range(CELL):
        for x in range(CELL):
            edge = min(x, y, CELL - 1 - x, CELL - 1 - y)
            f = min(1.0, edge / 7.0)
            px(cx + x, cy + y, tuple(int(v * (0.35 + 0.65 * f)) for v in color))
    return cx, cy

def rocket_trooper(ix, plate_c, uni, trim):
    cx, cy = plate(ix, plate_c)
    ox, oy = cx + 64, cy + 74
    rect(ox - 22, oy - 6, ox + 22, oy + 42, uni)          # torso block
    disc(ox, oy - 24, 15, (214, 178, 148))                # face
    rect(ox - 19, oy - 44, ox + 19, oy - 30, trim)        # helmet
    rect(ox - 24, oy - 34, ox + 24, oy - 28, trim)        # brim
    rect(ox - 6, oy - 62, ox + 52, oy - 48, (70, 74, 80)) # launcher tube
    disc(ox + 52, oy - 55, 8, DARK)                       # muzzle
    rect(ox - 30, oy - 2, ox - 22, oy + 30, uni)          # arm
    rect(ox + 22, oy - 2, ox + 30, oy + 30, uni)
    tri((ox - 4, oy - 48), (ox + 8, oy - 48), (ox + 2, oy - 34), trim)  # strap

def jet(ix, plate_c, body, trim):
    cx, cy = plate(ix, plate_c)
    ox, oy = cx + 64, cy + 64
    tri((ox, oy - 46), (ox - 40, oy + 34), (ox + 40, oy + 34), body)   # delta
    tri((ox, oy - 20), (ox - 14, oy + 30), (ox + 14, oy + 30), trim)   # canopy spine
    rect(ox - 5, oy + 26, ox + 5, oy + 44, (70, 74, 80))               # exhaust
    disc(ox, oy + 46, 6, GOLD)                                          # burner
    rect(ox - 46, oy + 18, ox - 34, oy + 26, trim)                      # wing pods
    rect(ox + 34, oy + 18, ox + 46, oy + 26, trim)

def pad_icon(ix, plate_c, deck, trim):
    cx, cy = plate(ix, plate_c)
    ox, oy = cx + 64, cy + 66
    rect(ox - 44, oy + 6, ox + 44, oy + 34, deck)           # platform slab
    rect(ox - 30, oy + 10, ox + 30, oy + 30, DARK)          # pad core
    disc(ox, oy + 20, 12, trim)                             # landing ring
    disc(ox, oy + 20, 7, DARK)
    rect(ox - 44, oy - 26, ox - 32, oy + 6, deck)           # tower
    rect(ox - 48, oy - 34, ox - 28, oy - 26, trim)          # tower cap

def bank_icon(ix, plate_c, body, trim):
    cx, cy = plate(ix, plate_c)
    ox, oy = cx + 64, cy + 64
    rect(ox - 34, oy + 12, ox + 34, oy + 38, body)          # base
    rect(ox - 26, oy - 22, ox + 26, oy + 12, body)          # vault
    rect(ox - 28, oy - 4, ox + 28, oy + 4, trim)            # band
    rect(ox - 12, oy - 32, ox + 12, oy - 22, trim)          # cap
    disc(ox, oy + 24, 8, trim)                              # coin
    rect(ox - 2, oy + 18, ox + 2, oy + 30, DARK)

def trooper_icon(ix, plate_c, uni, trim, heavy=False, scout=False):
    cx, cy = plate(ix, plate_c)
    ox, oy = cx + 64, cy + 74
    w = 26 if heavy else (16 if scout else 22)
    rect(ox - w, oy - 6, ox + w, oy + 42, uni)
    disc(ox, oy - 24, 14 if scout else 15, (214, 178, 148))
    if scout:
        rect(ox - 16, oy - 30, ox + 16, oy - 20, (80, 140, 170))   # visor band
        rect(ox + 12, oy - 52, ox + 15, oy - 30, trim)             # antenna
    else:
        rect(ox - 19, oy - 44, ox + 19, oy - 30, trim)
        rect(ox - 24, oy - 34, ox + 24, oy - 28, trim)
    if heavy:
        rect(ox - 34, oy - 12, ox - w, oy + 2, trim)               # pauldrons
        rect(ox + w, oy - 12, ox + 34, oy + 2, trim)
        rect(ox - 8, oy + 6, ox + 46, oy + 18, (58, 62, 68))       # cannon
        disc(ox + 46, oy + 12, 7, DARK)
    else:
        rect(ox - (w+8), oy - 2, ox - w, oy + 30, uni)
        rect(ox + w, oy - 2, ox + (w+8), oy + 30, uni)

def aa_icon(ix, plate_c, body, trim):
    cx, cy = plate(ix, plate_c)
    ox, oy = cx + 64, cy + 64
    rect(ox - 30, oy + 24, ox + 30, oy + 42, body)                  # base
    rect(ox - 7, oy - 14, ox + 7, oy + 24, body)                    # mast
    for k, dx in ((0, -12), (1, 2)):
        tri((ox + dx, oy - 16), (ox + dx + 26, oy - 44), (ox + dx + 12, oy - 8), (58, 62, 68))
    disc(ox - 14, oy - 20, 7, trim)                                 # sensor
    tri((ox - 40, oy - 34), (ox - 30, oy - 44), (ox - 30, oy - 24), trim)  # sky chevron

def tech_icon(ix, plate_c, body, trim):
    cx, cy = plate(ix, plate_c)
    ox, oy = cx + 64, cy + 64
    rect(ox - 28, oy - 18, ox + 28, oy + 38, body)                  # slab
    rect(ox - 30, oy + 2, ox + 30, oy + 10, trim)                   # band
    rect(ox - 18, oy - 44, ox - 14, oy - 18, (120, 128, 138))       # antennas
    rect(ox + 10, oy - 36, ox + 14, oy - 18, (120, 128, 138))
    disc(ox - 16, oy - 48, 5, trim)
    disc(ox, oy + 24, 9, DARK)                                      # emblem
    disc(ox, oy + 24, 5, trim)

def pill_icon(ix, plate_c, body, trim):
    cx, cy = plate(ix, plate_c)
    ox, oy = cx + 64, cy + 70
    rect(ox - 36, oy + 8, ox + 36, oy + 30, body)                   # low bunker
    tri((ox - 36, oy + 8), (ox + 36, oy + 8), (ox, oy - 18), body)  # slope
    rect(ox - 20, oy + 2, ox + 20, oy + 8, DARK)                    # slit
    rect(ox + 20, oy - 2, ox + 44, oy + 6, (58, 62, 68))            # barrel
    rect(ox - 30, oy + 30, ox + 30, oy + 36, trim)

def power_icon(ix, plate_c, body, trim):
    cx, cy = plate(ix, plate_c)
    ox, oy = cx + 64, cy + 64
    rect(ox - 30, oy, ox + 30, oy + 36, body)                        # generator
    rect(ox - 22, oy - 34, ox - 10, oy, (138, 90, 60))               # stacks
    rect(ox + 2, oy - 24, ox + 12, oy, (138, 90, 60))
    tri((ox + 18, oy - 34), (ox + 30, oy - 10), (ox + 20, oy - 10), trim)   # bolt
    tri((ox + 28, oy - 14), (ox + 16, oy + 10), (ox + 24, oy - 12), trim)

def arty_icon(ix, plate_c, body, trim):
    cx, cy = plate(ix, plate_c)
    ox, oy = cx + 64, cy + 64
    rect(ox - 34, oy + 26, ox + 34, oy + 42, body)                  # platform
    rect(ox - 14, oy + 10, ox + 14, oy + 26, body)                  # cradle
    # long barrel raked up-right
    for k in range(5):
        rect(ox - 4 + k * 10, oy + 2 - k * 8, ox + 14 + k * 10, oy + 12 - k * 8, (58, 62, 68))
    disc(ox + 50, oy - 32, 8, trim)                                 # muzzle bloom
    rect(ox - 30, oy - 2, ox - 16, oy + 26, trim)                   # counterweight
    for fx in (-26, 22):
        rect(ox + fx, oy + 42, ox + fx + 8, oy + 50, (40, 42, 46))  # jacks

SLOTS = [
    ("WPIcoLancer", lambda i: rocket_trooper(i, MER, (225, 229, 234), GOLD)),
    ("WPIcoSting", lambda i: rocket_trooper(i, JAK, (196, 170, 128), (111, 143, 90))),
    ("WPIcoKestrel", lambda i: jet(i, MER, STEEL, GOLD)),
    ("WPIcoBuzzard", lambda i: jet(i, JAK, SAND, (138, 90, 60))),
    ("WPIcoLaunchPad", lambda i: pad_icon(i, MER, STEEL, GOLD)),
    ("WPIcoRoost", lambda i: pad_icon(i, JAK, SAND, (138, 90, 60))),
    ("WPIcoExchange", lambda i: bank_icon(i, MER, STEEL, GOLD)),
    ("WPIcoRacket", lambda i: bank_icon(i, JAK, SAND, (111, 143, 90))),
    ("WPIcoVigil", lambda i: trooper_icon(i, MER, (225, 229, 234), (120, 128, 138), scout=True)),
    ("WPIcoProwler", lambda i: trooper_icon(i, JAK, (196, 170, 128), (138, 90, 60), scout=True)),
    ("WPIcoBastion", lambda i: trooper_icon(i, MER, (225, 229, 234), GOLD, heavy=True)),
    ("WPIcoBruiser", lambda i: trooper_icon(i, JAK, (196, 170, 128), (111, 143, 90), heavy=True)),
    ("WPIcoShrike", lambda i: jet(i, MER, (225, 229, 234), (120, 128, 138))),
    ("WPIcoGnat", lambda i: jet(i, JAK, (170, 150, 110), (111, 143, 90))),
    ("WPIcoSkyspear", lambda i: aa_icon(i, MER, STEEL, GOLD)),
    ("WPIcoFlakhut", lambda i: aa_icon(i, JAK, SAND, (138, 90, 60))),
    ("WPIcoDirectorate", lambda i: tech_icon(i, MER, STEEL, GOLD)),
    ("WPIcoDen", lambda i: tech_icon(i, JAK, SAND, (111, 143, 90))),
    ("WPIcoRampart", lambda i: pill_icon(i, MER, STEEL, GOLD)),
    ("WPIcoNest", lambda i: pill_icon(i, JAK, SAND, (138, 90, 60))),
    ("WPIcoLongbow", lambda i: arty_icon(i, MER, STEEL, GOLD)),
    ("WPIcoLobber", lambda i: arty_icon(i, JAK, SAND, (138, 90, 60))),
    ("WPIcoDynamo", lambda i: power_icon(i, JAK, SAND, GOLD)),
]

for i, (_, draw) in enumerate(SLOTS):
    draw(i)

def write_tga(path):
    hdr = bytearray(18)
    hdr[2] = 2
    struct.pack_into("<HH", hdr, 12, SIZE, SIZE)
    hdr[16] = 24
    hdr[17] = 0x20
    body = bytearray()
    for row in sheet:
        for (r, g, b) in row:
            body += bytes((b, g, r))
    with open(path, "wb") as f:
        f.write(bytes(hdr) + bytes(body))
    print(f"wrote {path}")

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for t in (os.path.expanduser("~/GeneralsX/GeneralsZH/Art/Textures/wp_cmdicons2.tga"),
          os.path.join(root, "data", "Art", "Textures", "wp_cmdicons2.tga")):
    os.makedirs(os.path.dirname(t), exist_ok=True)
    write_tga(t)

ini = ["; War Powers original data - second icon sheet (post-Blender additions)",
       "; generated by tools/genicons2.py"]
for i, (name, _) in enumerate(SLOTS):
    x, y = (i % GRID) * CELL, (i // GRID) * CELL
    ini.append(f"""
MappedImage {name}
  Texture = wp_cmdicons2.tga
  TextureWidth = {SIZE}
  TextureHeight = {SIZE}
  Coords = Left:{x} Top:{y} Right:{x + CELL} Bottom:{y + CELL}
  Status = NONE
End""")
for t in (os.path.expanduser("~/GeneralsX/GeneralsZH/Data/INI/MappedImages/HandCreated/WPCmdIcons2.ini"),
          os.path.join(root, "data", "Data", "INI", "MappedImages", "HandCreated", "WPCmdIcons2.ini")):
    os.makedirs(os.path.dirname(t), exist_ok=True)
    with open(t, "w") as f:
        f.write("\n".join(ini) + "\n")
    print(f"wrote {t}")
