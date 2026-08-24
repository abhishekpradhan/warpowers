#!/usr/bin/env python3
"""Pack Blender-rendered unit portraits into the command-icon sheet.

Reads 128px TGA portraits (WP_PORTRAIT_DIR renders, default /tmp/portraits),
composites each over a faction plate, packs a 4x4 512px sheet ->
wp_cmdicons.tga (same file the MappedImages already reference; coordinates
regenerated to the 128px grid).
"""
import os
import struct
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else '/tmp/portraits'
CELL = 128
GRID = 4
SIZE = CELL * GRID

MER = (46, 52, 60)
JAK = (56, 46, 38)

# icon name -> (portrait file, plate)
SLOTS = [
    ('WPIcoVector', 'vector', MER), ('WPIcoOutrider', 'outrider', MER),
    ('WPIcoZenith', 'zenith', MER), ('WPIcoFabricator', 'surveyor', MER),
    ('WPIcoMongrel', 'mongrel', JAK), ('WPIcoVulture', 'vulture', JAK),
    ('WPIcoRigger', 'rigger', JAK), ('WPIcoPowerArray', 'merpp', MER),
    ('WPIcoVehiclePlant', 'merwf', MER), ('WPIcoBulwark', 'bulwark', MER),
    ('WPIcoChopShop', 'jakcs', JAK), ('WPIcoWatchpost', 'watchpost', JAK),
    ('WPIcoCC', 'mercc', MER), ('WPIcoCP', 'jakcp', JAK),
    ('WPIcoWarden', 'warden', MER), ('WPIcoScrapper', 'scrapper', JAK),
]


def read_tga(path):
    d = open(path, 'rb').read()
    idlen = d[0]
    typ = d[2]
    w, h = struct.unpack('<HH', d[12:16])
    bpp = d[16]
    desc = d[17]
    off = 18 + idlen
    n = w * h
    px = []
    if typ == 2:
        step = bpp // 8
        for i in range(n):
            b = d[off + i * step:off + i * step + step]
            px.append((b[2], b[1], b[0], b[3] if step == 4 else 255))
    elif typ == 10:  # RLE
        i = off
        while len(px) < n:
            hdrb = d[i]; i += 1
            count = (hdrb & 0x7F) + 1
            if hdrb & 0x80:
                b = d[i:i + bpp // 8]; i += bpp // 8
                px.extend([(b[2], b[1], b[0], b[3] if bpp == 32 else 255)] * count)
            else:
                for _ in range(count):
                    b = d[i:i + bpp // 8]; i += bpp // 8
                    px.append((b[2], b[1], b[0], b[3] if bpp == 32 else 255))
    else:
        raise ValueError(f'tga type {typ}')
    rows = [px[y * w:(y + 1) * w] for y in range(h)]
    if not (desc & 0x20):     # bottom-up -> flip to top-down
        rows = rows[::-1]
    return rows, w, h


sheet = [[(16, 17, 20) for _ in range(SIZE)] for _ in range(SIZE)]
ini = ['; War Powers original data — command button icons',
       '; (model-rendered portraits packed by tools/genportraitsheet.py)']

for ix, (name, fname, plate) in enumerate(SLOTS):
    cx, cy = (ix % GRID) * CELL, (ix // GRID) * CELL
    # plate with soft edge
    for y in range(CELL):
        for x in range(CELL):
            e = min(x, y, CELL - 1 - x, CELL - 1 - y)
            f = 1.18 if e < 3 else (1.0 + 0.06 * (1.0 - min(1.0, e / 40.0)))
            sheet[cy + y][cx + x] = tuple(min(255, int(c * f)) for c in plate)
    path = os.path.join(SRC, fname + '.tga')
    rows, w, h = read_tga(path)
    ox, oy = (CELL - w) // 2, (CELL - h) // 2
    for y in range(h):
        for x in range(w):
            r, g, b, a = rows[y][x]
            if a == 0:
                continue
            base = sheet[cy + oy + y][cx + ox + x]
            af = a / 255.0
            sheet[cy + oy + y][cx + ox + x] = (
                int(r * af + base[0] * (1 - af)),
                int(g * af + base[1] * (1 - af)),
                int(b * af + base[2] * (1 - af)))
    ini.append(f'''
MappedImage {name}
  Texture = wp_cmdicons.tga
  TextureWidth = {SIZE}
  TextureHeight = {SIZE}
  Coords = Left:{cx} Top:{cy} Right:{cx + CELL} Bottom:{cy + CELL}
End''')

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
targets = [os.path.expanduser('~/GeneralsX/GeneralsZH/Art/Textures/wp_cmdicons.tga'),
           os.path.join(root, 'data', 'Art', 'Textures', 'wp_cmdicons.tga')]
hdr = bytearray(18)
hdr[2] = 2
struct.pack_into('<HH', hdr, 12, SIZE, SIZE)
hdr[16] = 24
hdr[17] = 0x20
body = bytearray()
for row in sheet:
    for (r, g, b) in row:
        body += bytes((b, g, r))
for t in targets:
    with open(t, 'wb') as f:
        f.write(bytes(hdr) + bytes(body))
    print('wrote', t)

ini_targets = [os.path.join(root, 'data', 'Data', 'INI', 'MappedImages', 'HandCreated', 'WPCmdIcons.ini'),
               os.path.expanduser('~/GeneralsX/GeneralsZH/Data/INI/MappedImages/HandCreated/WPCmdIcons.ini')]
for t in ini_targets:
    with open(t, 'w') as f:
        f.write('\n'.join(ini) + '\n')
    print('wrote', t)
