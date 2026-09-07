#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Pack consistent model-rendered command portraits into both existing sheets.

python3 tools/genportraitsheet.py /tmp/warpowers-portraits --data data
Preserves MappedImage names. Missing portraits fail before output is replaced.
Sheets are written in the committed storage form (RLE, top-left).
"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wp_tga import encode, read_tga  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIRST = ['Vector', 'Outrider', 'Zenith', 'Fabricator', 'Mongrel', 'Vulture', 'Rigger', 'PowerArray',
         'VehiclePlant', 'Bulwark', 'ChopShop', 'Watchpost', 'CC', 'CP', 'Warden', 'Scrapper']
SECOND = ['Lancer', 'Sting', 'Kestrel', 'Buzzard', 'LaunchPad', 'Roost', 'Exchange', 'Racket',
          'Vigil', 'Prowler', 'Bastion', 'Bruiser', 'Shrike', 'Gnat', 'Skyspear', 'Flakhut',
          'Directorate', 'Den', 'Rampart', 'Nest', 'Longbow', 'Lobber', 'Dynamo',
          'Porter', 'Scavenger', 'PrecisionStrike', 'TunnelAmbush', 'MissionRelay']
JACKAL = {'Mongrel', 'Vulture', 'Rigger', 'ChopShop', 'Watchpost', 'CP', 'Scrapper',
          'Sting', 'Buzzard', 'Roost', 'Racket', 'Prowler', 'Bruiser', 'Gnat', 'Flakhut', 'Den', 'Nest', 'Lobber', 'Dynamo',
          'Scavenger', 'TunnelAmbush'}
CELL = 128


def resized(rows):
    h = len(rows)
    w = len(rows[0])
    out = []
    for y in range(CELL):
        row = []
        for x in range(CELL):
            sample = [rows[sy][sx] for sy in range(y * h // CELL, max(y * h // CELL + 1, (y + 1) * h // CELL))
                      for sx in range(x * w // CELL, max(x * w // CELL + 1, (x + 1) * w // CELL))]
            a = sum(p[3] for p in sample)
            rgb = tuple(round(sum(p[c] * p[3] for p in sample) / a) if a else 0 for c in range(3))
            row.append((*rgb, round(a / len(sample))))
        out.append(row)
    return out


def write_sheet(data, names, cols, texture, ini_name, portraits):
    rows = (len(names) + cols - 1) // cols
    w = cols * CELL
    h = rows * CELL
    sheet = [[(19, 25, 29)] * w for _ in range(h)]
    ini = ['; Original War Powers portraits rendered from shipped W3D models.',
           '; tools/blender/render_roster.py + tools/genportraitsheet.py']
    for i, name in enumerate(names):
        bx = (i % cols) * CELL
        by = (i // cols) * CELL
        plate = (48, 43, 36) if name in JACKAL else (34, 45, 53)
        accent = (139, 158, 108) if name in JACKAL else (218, 178, 87)
        for y in range(CELL):
            for x in range(CELL):
                edge = min(x, y, CELL - 1 - x, CELL - 1 - y)
                glow = max(0, 1 - ((x - 56) ** 2 + (y - 53) ** 2) ** .5 / 100)
                base = tuple(round(v * (.75 + .35 * glow)) for v in plate)
                if edge == 0:
                    base = tuple(round(v * .40) for v in accent)
                if 3 <= x < 33 and 3 <= y < 5:
                    base = accent
                r, g, b, a = portraits[name][y][x]
                af = a / 255 if edge >= 5 else 0
                sheet[by + y][bx + x] = tuple(round(v * af + base[c] * (1 - af)) for c, v in enumerate((r, g, b)))
        ini.append(f'\nMappedImage WPIco{name}\n  Texture = {texture}\n  TextureWidth = {w}\n  TextureHeight = {h}\n'
                   f'  Coords = Left:{bx} Top:{by} Right:{bx+CELL} Bottom:{by+CELL}\n  Status = NONE\nEnd')
    target = data / 'Art/Textures' / texture
    temporary = target.with_name('.' + target.name + '.tmp')
    temporary.write_bytes(encode(sheet))
    temporary.replace(target)
    (data / 'Data/INI/MappedImages/HandCreated' / ini_name).write_text('\n'.join(ini) + '\n')
    print(f'PORTRAITS_PACKED {len(names)} -> {texture} ({w}x{h})')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('source', type=Path, help='directory of WPIco*.tga renders from tools/blender/render_roster.py')
    ap.add_argument('--data', type=Path, default=ROOT / 'data',
                    help='dataset root; writes the two sheets and their MappedImage INIs (default: the repository data/)')
    args = ap.parse_args(argv)
    portraits = {name: resized(read_tga(args.source / ('WPIco' + name + '.tga'))) for name in FIRST + SECOND}
    for path in (args.data / 'Art/Textures', args.data / 'Data/INI/MappedImages/HandCreated'):
        path.mkdir(parents=True, exist_ok=True)
    write_sheet(args.data, FIRST, 4, 'wp_cmdicons.tga', 'WPCmdIcons.ini', portraits)
    write_sheet(args.data, SECOND, 5, 'wp_cmdicons2.tga', 'WPCmdIcons2.ini', portraits)


if __name__ == '__main__':
    main()
