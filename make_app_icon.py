#!/usr/bin/env python3
"""Render the 1024x1024 app icon that Meta's app submission requires.

Two constraints shaped this, both from watching earlier attempts fail:

* **No alpha channel.** Meta rejects an icon whose PNG has transparency. Pillow
  is not installed here, and `sips` upscales to colour type 6 (RGBA), so the
  file is written by hand as colour type 2 -- 8-bit RGB, no alpha -- rather than
  converted from something else.

* **Nothing exotic to rasterise.** `qlmanage` renders SVG to a blank image for
  both arc paths and stroke-dasharray, which is why the mark is drawn here as a
  signed-distance field instead. That also gives analytic antialiasing for free:
  the coverage of a pixel is how far its centre is from the edge, so there is no
  stair-stepping and no supersampling loop.

The mark is a bold open ring -- the site's rust (#b4451f, --rust in style.css)
with a white stroke. One shape, high contrast, still legible at 48px in an app
list, which is the size this actually gets seen at.
"""
import math
import struct
import zlib

W = H = 1024
RUST = (0xB4, 0x45, 0x1F)
WHITE = (0xFF, 0xFF, 0xFF)

# The ring: radius of the stroke centreline, half its thickness, and the sweep.
# Angles are in radians, y pointing down, so -pi/2 is 12 o'clock.
CX, CY = 512.0, 512.0
R = 268.0
HALF = 62.0          # stroke half-width -> 124px thick
A0, A1 = math.radians(-118.0), math.radians(118.0)


def dist_to_ring(px, py):
    """Signed distance from a point to the stroke of the open ring.

    Inside the stroke the distance is negative, which is what makes the
    antialiasing formula below a single expression rather than a special case
    for the interior.
    """
    dx, dy = px - CX, py - CY
    r = math.hypot(dx, dy)
    a = math.atan2(dy, dx)
    # Normalise the angle into [A0, A1]'s neighbourhood. The arc is centred on
    # 0 rad and spans less than 2pi, so wrapping into (-pi, pi] is enough.
    # Outside the sweep, the nearest point on the stroke is one of the caps
    # rather than the centreline annulus, so measure to the cap centre.
    if a < A0 or a > A1:
        # The cap sits on the *centreline*, so it is placed at radius R -- not
        # at this point's radius. Using r here puts the cap wherever the sample
        # happens to be, which paints a disc of radius HALF around a point that
        # drifts outwards, and leaves white blobs far outside the ring.
        ca = A0 if a < A0 else A1
        cap_x = CX + R * math.cos(ca)
        cap_y = CY + R * math.sin(ca)
        return math.hypot(px - cap_x, py - cap_y) - HALF
    return abs(r - R) - HALF


def write_png(path, rows):
    """Colour type 2, 8-bit, filter 0 on every row."""
    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw = b''.join(b'\x00' + row for row in rows)
    ihdr = struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', zlib.compress(raw, 9)))
        f.write(chunk(b'IEND', b''))


def main():
    rows = []
    for y in range(H):
        py = y + 0.5
        row = bytearray()
        for x in range(W):
            d = dist_to_ring(x + 0.5, py)
            # A pixel centre exactly on the edge is half covered; one pixel
            # away is fully in or fully out. That is the whole antialiasing
            # model, and for a shape this size it is indistinguishable from
            # supersampling.
            cov = 0.5 - d
            if cov <= 0.0:
                row += bytes(RUST)
            elif cov >= 1.0:
                row += bytes(WHITE)
            else:
                row += bytes(round(r + (w - r) * cov) for r, w in zip(RUST, WHITE))
        rows.append(bytes(row))
    write_png('app-icon-1024.png', rows)


if __name__ == '__main__':
    main()
