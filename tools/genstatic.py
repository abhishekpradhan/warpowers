#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Raster icons for the browser shell, reproduced from web/static/favicon.svg.

favicon-32.png, apple-touch-icon.png (180 px), icon-192.png, icon-512.png and favicon.ico
are the favicon's gold "W" on its dark square. No SVG rasterizer is needed:
the script reads the favicon's <path> elements (move, line, horizontal,
vertical and close commands only), fills each with an even-odd scanline
rasterizer (4 sub-scanlines per pixel row, exact horizontal span coverage),
writes the 512 px master through zlib, and box-filters the smaller sizes from
that master. Every icon is therefore a pure function of the SVG and this
script; rerunning it is byte-identical on the same zlib.

python3 tools/genstatic.py [--out web/static] [--svg web/static/favicon.svg] [--check]

--check reports icons that differ from a fresh render without writing.
The social card (social-card.jpg) is not produced here: it is a JPEG crop of
docs/media/warpowers-panorama.jpg (see docs/web-bridge.md).
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ElementTree
import zlib

ROOT = Path(__file__).resolve().parents[1]
SVG_NS = '{http://www.w3.org/2000/svg}'
MASTER = 512
SAMPLES = 4
ICONS = {'icon-512.png': 512, 'icon-192.png': 192, 'apple-touch-icon.png': 180, 'favicon-32.png': 32}
NUMBER = re.compile(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')
TOKEN = re.compile(r'[MmLlHhVvZz]|' + NUMBER.pattern + r'|[^\s,]')

Point = tuple[float, float]
Color = tuple[float, float, float]


def parse_path(data: str) -> list[list[Point]]:
    """Return the closed subpaths of an SVG path made of M/L/H/V/Z commands."""
    tokens = TOKEN.findall(data)
    subpaths: list[list[Point]] = []
    current: list[Point] = []
    command = None
    x = y = start_x = start_y = 0.0
    index = 0

    def number() -> float:
        nonlocal index
        if index >= len(tokens) or not NUMBER.fullmatch(tokens[index]):
            raise ValueError(f'Path command {command!r} is missing a number: {data!r}')
        index += 1
        return float(tokens[index - 1])

    def close() -> None:
        nonlocal current
        if len(current) >= 3:
            subpaths.append(current)
        elif current:
            raise ValueError(f'Subpath with fewer than three points: {data!r}')
        current = []

    while index < len(tokens):
        token = tokens[index]
        if token.isalpha():
            if token not in 'MmLlHhVvZz':
                raise ValueError(f'Unsupported path command {token!r} (only M, L, H, V and Z are rasterized): {data!r}')
            command = token
            index += 1
        elif command is None or NUMBER.fullmatch(token) is None:
            raise ValueError(f'Unexpected token {token!r} in path: {data!r}')
        if command in 'Zz':
            close()
            x, y = start_x, start_y
            command = None
            continue
        relative = command.islower()
        if command in 'Mm':
            close()
            dx, dy = number(), number()
            x, y = (x + dx, y + dy) if relative else (dx, dy)
            start_x, start_y = x, y
            command = 'l' if relative else 'L'  # further pairs are implicit line-tos
        elif command in 'Ll':
            dx, dy = number(), number()
            x, y = (x + dx, y + dy) if relative else (dx, dy)
        elif command in 'Hh':
            dx = number()
            x = x + dx if relative else dx
        else:
            dy = number()
            y = y + dy if relative else dy
        current.append((x, y))
    close()
    return subpaths


def parse_color(value: str) -> Color:
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', value or ''):
        raise ValueError(f'Fill must be a six-digit hex color: {value!r}')
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def read_svg(path: Path) -> tuple[float, list[tuple[Color, list[list[Point]]]]]:
    """Return the square viewBox size and the (fill, subpaths) of every <path>."""
    root = ElementTree.parse(path).getroot()
    if root.tag != SVG_NS + 'svg':
        raise ValueError(f'{path} is not an SVG document.')
    box = [float(part) for part in root.get('viewBox', '').replace(',', ' ').split()]
    if len(box) != 4 or box[0] != 0 or box[1] != 0 or box[2] <= 0 or box[2] != box[3]:
        raise ValueError(f'{path} needs a square viewBox anchored at the origin.')
    layers = []
    for element in root:
        if element.tag != SVG_NS + 'path':
            raise ValueError(f'{path}: only <path> elements are rasterized, found {element.tag!r}.')
        layers.append((parse_color(element.get('fill')), parse_path(element.get('d', ''))))
    if not layers:
        raise ValueError(f'{path} contains no paths.')
    return box[2], layers


def coverage(subpaths: list[list[Point]], size: int, scale: float, samples: int = SAMPLES) -> list[list[float]]:
    """Even-odd fill coverage of the subpaths on a size x size grid, in 0..1 per pixel."""
    edges = []
    for points in subpaths:
        for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
            if y0 != y1:
                edges.append((x0 * scale, y0 * scale, x1 * scale, y1 * scale))
    grid = [[0.0] * size for _ in range(size)]
    weight = 1.0 / samples
    for py, row in enumerate(grid):
        for sample in range(samples):
            y = py + (sample + 0.5) * weight
            crossings = sorted(x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                               for x0, y0, x1, y1 in edges if (y0 <= y < y1) or (y1 <= y < y0))
            for left, right in zip(crossings[0::2], crossings[1::2]):
                left, right = max(left, 0.0), min(right, float(size))
                for px in range(int(left), min(math.ceil(right), size)):
                    overlap = min(right, px + 1) - max(left, px)
                    if overlap > 0:
                        row[px] += overlap * weight
    return grid


def render(layers: list[tuple[Color, list[list[Point]]]], box: float, size: int) -> list[list[Color]]:
    """Composite the layers in document order over black (the first layer is the square)."""
    image = [[(0.0, 0.0, 0.0)] * size for _ in range(size)]
    scale = size / box
    for fill, subpaths in layers:
        for row, alpha in zip(image, coverage(subpaths, size, scale)):
            for px, a in enumerate(alpha):
                if a > 0:
                    a = min(a, 1.0)
                    row[px] = tuple(row[px][c] * (1 - a) + fill[c] * a for c in range(3))
    return image


def quantize(image: list[list[Color]]) -> list[bytes]:
    return [bytes(max(0, min(255, int(channel + 0.5))) for pixel in row for channel in pixel) for row in image]


def box_weights(source: int, target: int) -> list[list[tuple[int, float]]]:
    """Area-average weights of the source samples covering each target sample."""
    ratio = source / target
    table = []
    for index in range(target):
        start, end = index * ratio, (index + 1) * ratio
        pairs = []
        for i in range(int(start), min(math.ceil(end), source)):
            overlap = min(end, i + 1) - max(start, i)
            if overlap > 0:
                pairs.append((i, overlap / ratio))
        table.append(pairs)
    return table


def downsample(rows: list[bytes], target: int) -> list[bytes]:
    """Box-filter square 8-bit RGB rows to target x target (separable area average)."""
    source = len(rows)
    if target > source:
        raise ValueError('Icons are only ever downsampled from the master.')
    weights = box_weights(source, target)
    horizontal = [[tuple(sum(row[3 * i + c] * w for i, w in pairs) for c in range(3)) for pairs in weights]
                  for row in rows]
    return quantize([[tuple(sum(horizontal[i][x][c] * w for i, w in pairs) for c in range(3)) for x in range(target)]
                     for pairs in weights])


def png(rows: list[bytes]) -> bytes:
    """Encode 8-bit RGB rows (each 3 * width bytes) as a filter-0 PNG."""
    height = len(rows)
    width = len(rows[0]) // 3
    if any(len(row) != width * 3 for row in rows):
        raise ValueError('Every row needs the same width.')

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return struct.pack('>I', len(payload)) + tag + payload + struct.pack('>I', zlib.crc32(tag + payload))

    raw = b''.join(b'\0' + row for row in rows)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def generate(svg: Path, master: int = MASTER, icons: dict[str, int] = ICONS) -> dict[str, bytes]:
    """PNG bytes per icon name: the master is rendered once, every other size is box-filtered from it."""
    box, layers = read_svg(svg)
    master_rows = quantize(render(layers, box, master))
    return {name: png(master_rows if size == master else downsample(master_rows, size))
            for name, size in icons.items()}


def ico_from_png(png: bytes, size: int) -> bytes:
    """One-image ICO whose payload is the PNG itself (valid for every current browser and OS)."""
    import struct
    entry = struct.pack('<BBBBHHII', size % 256, size % 256, 0, 0, 1, 32, len(png), 6 + 16)
    return struct.pack('<HHH', 0, 1, 1) + entry + png


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', type=Path, default=ROOT / 'web/static', help='directory for the PNG icons')
    parser.add_argument('--svg', type=Path, default=ROOT / 'web/static/favicon.svg', help='vector favicon to rasterize')
    parser.add_argument('--check', action='store_true', help='report stale icons without writing (exit 1 if any differ)')
    args = parser.parse_args()
    icons = generate(args.svg)
    icons['favicon.ico'] = ico_from_png(icons['favicon-32.png'], 32)  # legacy /favicon.ico probes
    stale = [name for name, data in icons.items()
             if not (args.out / name).is_file() or (args.out / name).read_bytes() != data]
    if args.check:
        for name in stale:
            print(f'stale: {args.out / name}')
        print(f'{len(icons) - len(stale)} of {len(icons)} icons match {args.svg}')
        return 1 if stale else 0
    args.out.mkdir(parents=True, exist_ok=True)
    for name, data in icons.items():
        (args.out / name).write_bytes(data)
        print(f'{args.out / name}: {len(data):,} bytes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
