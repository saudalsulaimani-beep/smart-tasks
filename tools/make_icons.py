#!/usr/bin/env python3
"""
Renders the app icon (the brand's ascending-bars mark on a teal ground)
to PNG at every size the manifest and iOS need.

Pure standard library — no Pillow, no numpy. Shapes are drawn by analytic
coverage with 3x3 supersampling, which is plenty for flat geometry.
"""
import math, os, struct, zlib

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icons")

TOP    = (0x2D, 0xD4, 0xBF)   # gradient start
BOTTOM = (0x0E, 0x76, 0x6B)   # gradient end
INK    = (0x06, 0x24, 0x22)   # the mark


def lerp(a, b, t):
    return a + (b - a) * t


def rounded_rect_cover(x, y, w, h, r):
    """Signed coverage test for a rounded rect spanning (0,0)-(w,h)."""
    cx = min(max(x, r), w - r)
    cy = min(max(y, r), h - r)
    dx, dy = x - cx, y - cy
    return (dx * dx + dy * dy) <= r * r


def capsule_cover(x, y, x1, y1, x2, y2, r):
    """Point-in-thick-segment (round caps)."""
    vx, vy = x2 - x1, y2 - y1
    wx, wy = x - x1, y - y1
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / L2))
    px, py = x1 + t * vx, y1 + t * vy
    dx, dy = x - px, y - py
    return (dx * dx + dy * dy) <= r * r


def render(size, maskable=False):
    """Returns RGBA bytes for one square icon."""
    S = float(size)
    radius = 0.0 if maskable else S * 0.2226          # iOS-ish squircle radius

    # The mark, expressed in the same 24-unit space as the in-app SVG,
    # then mapped into a safe box (smaller when the OS will mask it).
    box = S * (0.58 if maskable else 0.74)
    off = (S - box) / 2.0
    u = box / 24.0
    def P(vx, vy):
        return (off + vx * u, off + vy * u)

    stroke = 2.35 * u / 2.0                            # half-width
    bars = [
        (P(4, 19),  P(4, 6)),
        (P(10, 19), P(10, 10)),
        (P(16, 19), P(16, 4)),
        (P(2, 19),  P(22, 19)),
    ]
    # keep the glyph inside the safe box even with round caps
    minx = min(min(a[0], b[0]) for a, b in bars) - stroke
    maxx = max(max(a[0], b[0]) for a, b in bars) + stroke
    miny = min(min(a[1], b[1]) for a, b in bars) - stroke
    maxy = max(max(a[1], b[1]) for a, b in bars) + stroke

    SS = 3
    inv = 1.0 / (SS * SS)
    px = bytearray()
    for py_ in range(size):
        row = bytearray()
        for px_ in range(size):
            bg_hits = 0
            ink_hits = 0
            near_glyph = (px_ + 1 >= minx and px_ <= maxx and
                          py_ + 1 >= miny and py_ <= maxy)
            for sy in range(SS):
                y = py_ + (sy + 0.5) / SS
                for sx in range(SS):
                    x = px_ + (sx + 0.5) / SS
                    if maskable or rounded_rect_cover(x, y, S, S, radius):
                        bg_hits += 1
                        if near_glyph:
                            for (x1, y1), (x2, y2) in bars:
                                if capsule_cover(x, y, x1, y1, x2, y2, stroke):
                                    ink_hits += 1
                                    break
            if bg_hits == 0:
                row += b"\x00\x00\x00\x00"
                continue
            t = py_ / S
            base = (int(lerp(TOP[0], BOTTOM[0], t)),
                    int(lerp(TOP[1], BOTTOM[1], t)),
                    int(lerp(TOP[2], BOTTOM[2], t)))
            ink = ink_hits * inv
            r = int(round(lerp(base[0], INK[0], ink)))
            g = int(round(lerp(base[1], INK[1], ink)))
            b = int(round(lerp(base[2], INK[2], ink)))
            a = int(round(255 * bg_hits * inv))
            row += bytes((r, g, b, a))
        px += b"\x00" + row
    return bytes(px)


def write_png(path, size, raw):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = [
        ("icon-512.png", 512, False),
        ("icon-192.png", 192, False),
        ("apple-touch-icon.png", 180, False),
        ("icon-maskable-512.png", 512, True),
        ("favicon-32.png", 32, False),
    ]
    for name, size, maskable in jobs:
        path = os.path.join(OUT, name)
        n = write_png(path, size, render(size, maskable))
        print("%-26s %4dpx  %6d bytes" % (name, size, n))


if __name__ == "__main__":
    main()
