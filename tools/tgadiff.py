#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Diff two WP_FRAME_DUMP TGAs (18-byte header, 32-bit BGRA, top-left origin).

Reports the count of significantly changed pixels and their bounding box, plus
a brightness summary of the second image. A native-renderer debugging aid.

python3 tools/tgadiff.py BEFORE.tga AFTER.tga [--threshold 30]
"""
import argparse
from pathlib import Path
import struct


def load(path):
    data = Path(path).read_bytes()
    w, h = struct.unpack_from("<HH", data, 12)
    bpp = data[16]
    if bpp != 32:
        raise ValueError(f"{path}: expected a 32bpp frame dump, got {bpp}bpp")
    return w, h, data[18:18 + w * h * 4]


def compare(a_path, b_path, thresh=30):
    wa, ha, a = load(a_path)
    wb, hb, b = load(b_path)
    if (wa, ha) != (wb, hb):
        raise ValueError(f"size mismatch: {wa}x{ha} vs {wb}x{hb}")
    changed = 0
    minx = miny = 1 << 30
    maxx = maxy = -1
    bright = 0
    for y in range(ha):
        row = y * wa * 4
        for x in range(wa):
            i = row + x * 4
            da = abs(a[i] - b[i]) + abs(a[i+1] - b[i+1]) + abs(a[i+2] - b[i+2])
            if da > thresh:
                changed += 1
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
            if b[i] + b[i+1] + b[i+2] > 450:
                bright += 1
    print(f"size={wa}x{ha} changed={changed} bbox=({minx},{miny})-({maxx},{maxy})" if maxx >= 0
          else f"size={wa}x{ha} changed=0")
    print(f"bright(>150avg) pixels in B: {bright}")
    return changed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--threshold", type=int, default=30, help="summed RGB delta that counts as a change (default 30)")
    args = parser.parse_args(argv)
    compare(args.before, args.after, args.threshold)


if __name__ == "__main__":
    main()
