#!/usr/bin/env python3
"""Generate placeholder Rafiki icons using only Python stdlib."""
import os
import struct
import zlib


def make_png(width, height, hex_color):
    """Create a minimal solid-color PNG without external dependencies."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    # Each row: filter byte (0=None) + RGB pixels
    row = b"\x00" + bytes([r, g, b] * width)
    raw = row * height
    compressed = zlib.compress(raw)

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    return png


ICONS = {
    "public/icon-light-32x32.png": (32, 32, "#2C2C2C"),
    "public/icon-dark-32x32.png": (32, 32, "#FAF8F5"),
    "public/apple-icon.png": (180, 180, "#2C2C2C"),
    "public/icon-192.png": (192, 192, "#2C2C2C"),
    "public/icon-512.png": (512, 512, "#2C2C2C"),
}

os.makedirs("public", exist_ok=True)
for path, (w, h, color) in ICONS.items():
    with open(path, "wb") as f:
        f.write(make_png(w, h, color))
    print(f"Created {path}")
print("Done.")
