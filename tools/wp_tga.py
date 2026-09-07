# SPDX-License-Identifier: MIT
"""Targa (TGA) reading and writing shared by every image generator.

Only the subset the SAGE engine reads is implemented: uncompressed (type 2)
and run-length encoded (type 10) true-colour images, 24-bit BGR or 32-bit
BGRA, stored top-left or bottom-left.  Pixels cross this module as rows of
(r, g, b, a) tuples; ``write`` picks the smallest faithful encoding (RLE only
when it saves bytes, alpha only when some pixel is not fully opaque), which is
also the storage contract ``optimize_art.py`` enforces on committed files.
Standard library only.
"""
from pathlib import Path
import struct

HEADER_SIZE = 18
UNCOMPRESSED, RLE = 2, 10
TOP_LEFT = 0x20


def header(width, height, *, alpha=False, rle=False, top_left=True):
    """The 18-byte true-colour header (no image id, no colour map)."""
    data = bytearray(HEADER_SIZE)
    data[2] = RLE if rle else UNCOMPRESSED
    struct.pack_into('<HH', data, 12, width, height)
    data[16] = 32 if alpha else 24
    data[17] = (TOP_LEFT if top_left else 0) | (8 if alpha else 0)
    return bytes(data)


def pack(rows, alpha=False):
    """Serialize rows of (r, g, b[, a]) tuples as raw BGR(A) pixel bytes."""
    if alpha:
        return b''.join(bytes((p[2], p[1], p[0], p[3] if len(p) > 3 else 255)) for row in rows for p in row)
    return b''.join(bytes((p[2], p[1], p[0])) for row in rows for p in row)


def write_raw(path, rows, *, alpha=False, top_left=True):
    """Uncompressed image; returns the byte count written."""
    body = header(len(rows[0]), len(rows), alpha=alpha, top_left=top_left) + pack(rows, alpha)
    Path(path).write_bytes(body)
    return len(body)


def encode(rows):
    """Smallest faithful file: RLE only when shorter, alpha only when used."""
    h = len(rows)
    w = len(rows[0])
    alpha = any(len(p) > 3 and p[3] != 255 for row in rows for p in row)
    step = 4 if alpha else 3
    pixels = [bytes((p[2], p[1], p[0], p[3]) if alpha else (p[2], p[1], p[0])) for row in rows for p in row]
    raw = b''.join(pixels)
    rle = bytearray()
    for y in range(h):
        i = y * w
        end = i + w
        while i < end:
            run = 1
            while run < 128 and i + run < end and pixels[i + run] == pixels[i]:
                run += 1
            if run >= 2:
                rle.append(128 + run - 1)
                rle.extend(pixels[i])
                i += run
            else:
                start = i
                i += 1
                while i < end and i - start < 128:
                    if i + 1 < end and pixels[i] == pixels[i + 1]:
                        break
                    i += 1
                rle.append(i - start - 1)
                rle.extend(b''.join(pixels[start:i]))
    use_rle = len(rle) < len(raw)
    return header(w, h, alpha=alpha, rle=use_rle) + (bytes(rle) if use_rle else raw)


def write(path, rows):
    """Write ``encode(rows)``; returns the byte count written."""
    data = encode(rows)
    Path(path).write_bytes(data)
    return len(data)


def decode(data):
    """Rows of (r, g, b, a) tuples in top-left order, for type 2/10 images."""
    kind = data[2]
    w, h = struct.unpack_from('<HH', data, 12)
    step = data[16] // 8
    if kind not in (UNCOMPRESSED, RLE) or step not in (3, 4):
        raise ValueError('Unsupported TGA image (only 24/32-bit type 2 or 10)')
    pos = HEADER_SIZE + data[0]
    px = []

    def pixel(at):
        b = data[at:at + step]
        if len(b) < step:
            raise ValueError('Truncated TGA pixel data')
        return (b[2], b[1], b[0], b[3] if step == 4 else 255)

    if kind == UNCOMPRESSED:
        px = [pixel(pos + i * step) for i in range(w * h)]
    else:
        while len(px) < w * h:
            if pos >= len(data):
                raise ValueError('Truncated TGA run-length data')
            packet = data[pos]
            pos += 1
            n = (packet & 127) + 1
            if packet & 128:
                px.extend([pixel(pos)] * n)
                pos += step
            else:
                px.extend(pixel(pos + i * step) for i in range(n))
                pos += step * n
    rows = [px[y * w:(y + 1) * w] for y in range(h)]
    return rows if data[17] & TOP_LEFT else rows[::-1]


def read_tga(path):
    return decode(Path(path).read_bytes())
