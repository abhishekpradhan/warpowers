#!/usr/bin/env python3
"""Diff two WP_FRAME_DUMP TGAs (18-byte header, 32-bit BGRA, top-left origin).
Reports count of significantly-changed pixels and their bounding box, plus a
brightness histogram summary of the second image."""
import sys, struct

def load(path):
    with open(path, "rb") as f:
        data = f.read()
    w, h = struct.unpack_from("<HH", data, 12)
    bpp = data[16]
    assert bpp == 32, f"expected 32bpp, got {bpp}"
    return w, h, data[18:18 + w * h * 4]

def main(a_path, b_path, thresh=30):
    wa, ha, a = load(a_path)
    wb, hb, b = load(b_path)
    assert (wa, ha) == (wb, hb), "size mismatch"
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

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 30)
