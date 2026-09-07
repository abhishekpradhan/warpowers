#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Lossless TGA storage optimization plus the camera-appropriate atlas halving.

python3 tools/optimize_art.py --data data [--check]

Every image keeps its exact dimensions and pixels except the atlases listed in
HALVED: those are baked at twice their shipped size (the source contract that
reproduces the committed bytes; see tools/blender/polish_assets.json
``bake_size``/``texture_size``) and area-reduced here. The flagship Vector and
Mongrel keep their 512px atlases. RLE and dropping fully opaque alpha preserve
decoded RGBA pixels exactly. Unused menu padding is cleared outside its
verified native crop. ``--check`` reports what would change without writing.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wp_tga import encode, read_tga  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'tools/blender/polish_assets.json'
# Texture stem -> bake size. A file found at exactly this size is halved; the
# shipped atlas is half of it. Rock/barrier surfaces have no small markings and
# occupy only a few dozen screen pixels, so their contract is 128px from a
# 256px bake; the compact roster/base atlases ship at 256px from 512px bakes.
HALVED = {'wp_' + name: 512 for name in [
    'warden', 'scrapper', 'lancer', 'sting', 'vigil', 'prowler', 'bastion', 'bruiser',
    'scrap', 'relay', 'mercc', 'jakcp', 'merpp', 'merwf', 'jakcs',
    'outrider', 'vulture', 'zenith']}
HALVED.update({'wp_rock': 256, 'wp_wall': 256})
MENU_CROP = 'Left:57 Top:0 Right:967 Bottom:512'
MENU_PAD = (19, 25, 29, 255)


def reduce_half(rows):
    h = len(rows)
    w = len(rows[0])
    return [[tuple(round(sum(rows[y + dy][x + dx][c] for dy in (0, 1) for dx in (0, 1)) / 4) for c in range(4))
             for x in range(0, w, 2)] for y in range(0, h, 2)]


def shipped_size(texture, bake_size):
    """The committed atlas size for a texture baked at ``bake_size``."""
    return bake_size // 2 if HALVED.get(texture) == bake_size else bake_size


def optimized_rows(path, data):
    """Decoded rows after the source-contract reductions for ``path``."""
    path = Path(path)
    rows = read_tga(path)
    if path.stem in HALVED and len(rows) == len(rows[0]) == HALVED[path.stem]:
        rows = reduce_half(rows)
    if path.stem == 'wp_menu' and len(rows) == 512 and len(rows[0]) == 1024:
        # The native image samples only L57..R967. This padding is never
        # visible, so a solid border saves storage with no on-screen loss.
        mapping = Path(data) / 'Data/INI/MappedImages/HandCreated/WPMenuArt.ini'
        if MENU_CROP not in mapping.read_text():
            raise ValueError('Menu crop changed; review padding optimization before writing')
        rows = [[MENU_PAD] * 57 + row[57:967] + [MENU_PAD] * 57 for row in rows]
    return rows


def optimized_bytes(path, data):
    """The committed-form bytes of ``path``: halved if contracted, RLE if smaller."""
    return encode(optimized_rows(path, data))


def check_catalog(catalog=CATALOG):
    """The catalog's bake/ship sizes and HALVED must tell the same story."""
    if not Path(catalog).exists():
        return
    for model, contract in json.loads(Path(catalog).read_text()).items():
        texture, bake, ship = contract.get('texture'), contract.get('bake_size'), contract.get('texture_size')
        if bake is None or texture is None:
            continue
        if shipped_size(texture, bake) != ship:
            raise ValueError(f'{model}: polish_assets.json says {texture} bakes at {bake} and ships at {ship}, '
                             f'but optimize_art.HALVED would ship {shipped_size(texture, bake)}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data', type=Path, default=ROOT / 'data', help='dataset root (default: the repository data/)')
    parser.add_argument('--check', action='store_true', help='report files that would change; write nothing')
    args = parser.parse_args(argv)
    check_catalog()
    before = after = changed = 0
    for path in sorted((args.data / 'Art').rglob('*.tga')):
        old = path.read_bytes()
        rows = optimized_rows(path, args.data)
        new = encode(rows)
        before += len(old)
        after += len(new)
        if new != old:
            changed += 1
            if args.check:
                print(f'would rewrite {path} ({len(old)} -> {len(new)} bytes)')
            else:
                temporary = path.with_name('.' + path.name + '.tmp')
                temporary.write_bytes(new)
                if read_tga(temporary) != rows:
                    raise RuntimeError(f'RLE pixel verification failed: {path}')
                temporary.replace(path)
    print(f'ART_OPTIMIZE {changed} files: {before / 1048576:.2f} -> {after / 1048576:.2f} MiB; saved {(before - after) / 1048576:.2f} MiB')
    return 1 if (args.check and changed) else 0


if __name__ == '__main__':
    sys.exit(main())
