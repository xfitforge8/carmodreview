#!/usr/bin/env python3
"""Generate original technical diagrams for the CarModReview guides.

These are drawn from published specifications and are explicitly labelled as
diagrams, not photographs or measurement data. Each one illustrates a concept
already explained in the article text — offset, backspacing, tire diameter
matching, load range. No invented numbers appear on any of them.

Output: docs/img/diagrams/*.svg
"""
import os
import math

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs', 'img', 'diagrams')

INK = '#14161a'
INK2 = '#3d434d'
INK3 = '#6b7280'
RULE = '#ddd8cd'
RUST = '#b4451f'
TEAL = '#1d5d5d'
PAPER = '#fbfaf7'

HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        'width="{w}" height="{h}" role="img" aria-labelledby="t d">'
        '<title id="t">{title}</title><desc id="d">{desc}</desc>'
        f'<rect width="{{w}}" height="{{h}}" fill="{PAPER}"/>')


def svg(w, h, title, desc, body):
    head = HEAD.format(w=w, h=h, title=title, desc=desc)
    return head + body + '</svg>\n'


def txt(x, y, s, size=13, fill=INK2, weight='400', anchor='start', family='sans-serif'):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{s}</text>')


def caption(w, h, s, size=11.5):
    """Caption text, centred and wrapped so it can never run off the canvas.

    Line width is estimated at 0.52 em per character for the sans-serif stack;
    that is close enough to keep a long caption inside the viewBox.
    """
    max_chars = max(20, int((w - 80) / (size * 0.52)))
    words, lines, cur = s.split(), [], ''
    for word in words:
        trial = f'{cur} {word}'.strip()
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)

    out = []
    lh = size * 1.35
    y = h - 14 - (len(lines) - 1) * lh
    for line in lines:
        out.append(txt(w / 2, round(y, 1), line, size=size, fill=INK3, anchor='middle'))
        y += lh
    return ''.join(out)


# ── 1. Wheel offset ──────────────────────────────────────────────────────
def wheel_offset():
    w, h = 680, 320
    cy = 150
    b = []
    hub_x = 300
    b.append(f'<line x1="{hub_x}" y1="66" x2="{hub_x}" y2="286" stroke="{INK}" stroke-width="2.5"/>')
    b.append(txt(hub_x, 54, 'Hub mounting face', size=12, fill=INK, weight='600', anchor='middle'))

    rows = [('Positive offset', 'factory typical', 112, 62, TEAL),
            ('Zero offset', 'face on centreline', 176, 0, INK3),
            ('Negative offset', 'pushed outward', 240, -70, RUST)]
    for label, sub, y, off, col in rows:
        cx = hub_x + off
        b.append(f'<rect x="{cx-70}" y="{y-20}" width="140" height="40" rx="6" '
                 f'fill="none" stroke="{col}" stroke-width="2.5"/>')
        b.append(f'<line x1="{cx-70}" y1="{y}" x2="{cx-46}" y2="{y}" stroke="{col}" stroke-width="5"/>')
        b.append(f'<line x1="{cx+46}" y1="{y}" x2="{cx+70}" y2="{y}" stroke="{col}" stroke-width="5"/>')
        b.append(txt(cx, y + 4, 'rim', size=10.5, fill=INK3, anchor='middle'))
        # row label to the left, kept clear of the rim band
        b.append(txt(28, y - 2, label, size=11.5, fill=col, weight='600'))
        b.append(txt(28, y + 13, sub, size=10, fill=INK3))

    b.append(f'<line x1="{hub_x}" y1="112" x2="{hub_x+62}" y2="112" stroke="{TEAL}" '
             f'stroke-width="1.5" stroke-dasharray="4 3"/>')
    b.append(txt(hub_x + 70, 107, 'offset', size=11, fill=TEAL))
    b.append(f'<line x1="{hub_x}" y1="240" x2="{hub_x-70}" y2="240" stroke="{RUST}" '
             f'stroke-width="1.5" stroke-dasharray="4 3"/>')
    b.append(txt(hub_x - 78, 235, 'offset', size=11, fill=RUST, anchor='end'))

    b.append(txt(w / 2, 26, 'Wheel offset: where the mounting face sits relative to the rim centreline',
                 size=14, fill=INK, weight='700', anchor='middle'))
    b.append(caption(w, h, 'Schematic, not to scale. Offset is measured in millimetres from the rim centreline.'))
    return svg(w, h, 'Wheel offset diagram',
               'Three wheel cross-sections showing positive, zero and negative offset relative to the hub mounting face.',
               ''.join(b))


# ── 2. Backspacing vs offset ─────────────────────────────────────────────
def backspacing():
    w, h = 680, 280
    b = []
    y = 140
    bx, bw = 150, 380
    b.append(f'<rect x="{bx}" y="{y-52}" width="{bw}" height="104" rx="8" fill="none" stroke="{INK}" stroke-width="2.5"/>')
    mid = bx + bw / 2
    b.append(f'<line x1="{mid}" y1="{y-70}" x2="{mid}" y2="{y+70}" stroke="{INK3}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    b.append(txt(mid, y + 86, 'rim centreline', size=11, fill=INK3, anchor='middle'))

    face = bx + bw / 2 - 46
    b.append(f'<line x1="{face}" y1="{y-72}" x2="{face}" y2="{y+72}" stroke="{RUST}" stroke-width="3"/>')
    b.append(txt(face, y - 80, 'mounting face', size=11.5, fill=RUST, weight='600', anchor='middle'))

    # backspacing: from inner lip to face
    b.append(f'<line x1="{bx}" y1="{y+58}" x2="{face}" y2="{y+58}" stroke="{RUST}" stroke-width="1.5"/>')
    b.append(f'<line x1="{bx}" y1="{y+52}" x2="{bx}" y2="{y+64}" stroke="{RUST}" stroke-width="1.5"/>')
    b.append(f'<line x1="{face}" y1="{y+52}" x2="{face}" y2="{y+64}" stroke="{RUST}" stroke-width="1.5"/>')
    b.append(txt((bx + face) / 2, y + 78, 'backspacing (mm)', size=11, fill=RUST, anchor='middle'))

    # offset
    b.append(f'<line x1="{mid}" y1="{y-58}" x2="{face}" y2="{y-58}" stroke="{TEAL}" stroke-width="1.5"/>')
    b.append(txt((mid + face) / 2, y - 66, 'offset (mm)', size=11, fill=TEAL, anchor='middle'))

    b.append(txt(w / 2, 28, 'Backspacing measures to the inner lip; offset measures from the centreline',
                 size=14, fill=INK, weight='700', anchor='middle'))
    b.append(caption(w, h, 'Both describe the same wheel. Backspacing is measured from the inner edge, offset from the centreline.'))
    return svg(w, h, 'Backspacing versus offset',
               'A wheel cross-section showing backspacing measured from the inner lip and offset measured from the rim centreline.',
               ''.join(b))


# ── 3. Plus sizing / overall diameter ────────────────────────────────────
def plus_sizing():
    w, h = 680, 400
    b = []
    base_y = 200
    cx = 130
    rows = [('17"', 100, 62, TEAL, '225/65R17'),
            ('18"', 118, 50, INK3, '235/60R18'),
            ('20"', 140, 34, RUST, '245/50R20')]
    for i, (rim, r_out, r_in, col, spec) in enumerate(rows):
        x = cx + i * 185
        b.append(f'<circle cx="{x}" cy="{base_y}" r="{r_out}" fill="none" stroke="{col}" stroke-width="2.5"/>')
        b.append(f'<circle cx="{x}" cy="{base_y}" r="{r_in}" fill="none" stroke="{col}" stroke-width="2"/>')
        b.append(txt(x, base_y + 4, rim, size=12, fill=col, weight='700', anchor='middle'))
        b.append(txt(x, base_y + 150, spec, size=11, fill=INK3, anchor='middle'))
        b.append(f'<line x1="{x-r_out}" y1="{base_y+160}" x2="{x+r_out}" y2="{base_y+160}" stroke="{col}" stroke-width="1" stroke-dasharray="3 3"/>')
        b.append(txt(x, base_y + 174, 'same overall diameter', size=9.5, fill=col, anchor='middle'))

    b.append(txt(w / 2, 30, 'Plus sizing: a larger wheel with a shorter sidewall keeps overall diameter constant',
                 size=14, fill=INK, weight='700', anchor='middle'))
    b.append(caption(w, h, 'Illustrative sidewall ratios. A shorter sidewall means less compliance, so tyre choice changes ride quality.'))
    return svg(w, h, 'Plus sizing diagram',
               'Three wheel and tyre assemblies of increasing rim diameter but equal overall diameter.',
               ''.join(b))


# ── 4. Suspension geometry / leveling ────────────────────────────────────
def leveling_geometry():
    w, h = 680, 300
    b = []
    # front
    fx, fy = 180, 200
    # rear axle
    rx, ry = 470, 200
    # frame line
    b.append(f'<line x1="100" y1="200" x2="560" y2="200" stroke="{INK}" stroke-width="3"/>')
    # rake: rear higher
    b.append(f'<line x1="100" y1="205" x2="100" y2="196" stroke="{INK3}" stroke-width="2"/>')
    b.append(txt(fx, fy + 48, 'front', size=12, fill=INK3, anchor='middle'))
    b.append(txt(rx, ry + 48, 'rear', size=12, fill=INK3, anchor='middle'))

    # factory rake wedge
    b.append(f'<line x1="{fx}" y1="{fy}" x2="{rx}" y2="{ry-26}" stroke="{RULE}" stroke-width="2" stroke-dasharray="6 4"/>')
    b.append(txt((fx+rx)/2, ry - 40, 'factory rake', size=11, fill=INK3, anchor='middle'))

    # leveled line
    b.append(f'<line x1="{fx}" y1="{fy}" x2="{rx}" y2="{ry}" stroke="{TEAL}" stroke-width="2" stroke-dasharray="6 4"/>')
    b.append(txt((fx+rx)/2, ry + 62, 'after a leveling kit, the front is raised to match the rear', size=11, fill=TEAL, anchor='middle'))

    # wheels
    for x, y, col in [(fx, fy, INK), (rx, ry, INK)]:
        b.append(f'<circle cx="{x}" cy="{y}" r="30" fill="none" stroke="{col}" stroke-width="2.5"/>')

    # arrow showing lift
    b.append(f'<line x1="{fx+46}" y1="{fy-6}" x2="{fx+46}" y2="{fy-40}" stroke="{RUST}" stroke-width="2"/>')
    b.append(f'<polygon points="{fx+46},{fy-46} {fx+42},{fy-36} {fx+50},{fy-36}" fill="{RUST}"/>')
    b.append(txt(fx + 56, fy - 26, 'lift', size=11, fill=RUST))

    b.append(txt(w / 2, 30, 'Leveling removes the factory rake by raising the front only',
                 size=14, fill=INK, weight='700', anchor='middle'))
    b.append(caption(w, h, 'Side view, exaggerated for clarity. Raising the front changes caster and camber slightly — an alignment follows.'))
    return svg(w, h, 'Leveling kit geometry',
               'Side view of a truck frame showing the factory rake before and the leveled stance after raising the front.',
               ''.join(b))


# ── 5. Brake pad bedding / rotor wear ────────────────────────────────────
def brake_bedding():
    w, h = 680, 280
    b = []
    x0, y0, pw, ph = 90, 120, 500, 110
    b.append(f'<rect x="{x0}" y="{y0}" width="{pw}" height="{ph}" fill="none" stroke="{RULE}" stroke-width="1.5"/>')
    # steps
    steps = [(0.0, 0.22, 'clean rotor'), (0.22, 0.42, 'light stops'), (0.42, 0.70, 'medium'),
             (0.70, 0.88, 'hard stops'), (0.88, 1.0, 'cool')]
    cols = [INK3, TEAL, TEAL, RUST, INK3]
    for (a, c, label), col in zip(steps, cols):
        xa, xc = x0 + a * pw, x0 + c * pw
        b.append(f'<rect x="{xa}" y="{y0}" width="{xc-xa}" height="{ph}" fill="{col}" opacity="0.10"/>')
        b.append(f'<line x1="{xa}" y1="{y0}" x2="{xa}" y2="{y0+ph}" stroke="{RULE}" stroke-width="1"/>')
        b.append(txt((xa+xc)/2, y0 + ph + 20, label, size=10.5, fill=col, anchor='middle'))

    b.append(txt(w / 2, 28, 'Bedding sequence: progressive heat cycles, then a full cool-down',
                 size=14, fill=INK, weight='700', anchor='middle'))
    b.append(caption(w, h, 'General sequence, not a substitute for the pad manufacturer\'s own bedding procedure.'))
    return svg(w, h, 'Brake pad bedding sequence',
               'A timeline of bedding stages from a clean rotor through progressively harder stops to a cool-down period.',
               ''.join(b))


# ── 6. Exhaust systems: cat-back vs axle-back ────────────────────────────
def exhaust_layout():
    w, h = 680, 240
    b = []
    y = 120
    # engine -> cats -> muffler -> tailpipe
    labels = [(90, 110, 'engine'), (230, 90, 'catalytic'), (390, 80, 'muffler'), (560, 90, 'tailpipe')]
    x = 90
    for cx, ww, lab in labels:
        b.append(f'<rect x="{cx}" y="{y-18}" width="{ww}" height="36" rx="6" fill="none" stroke="{INK2}" stroke-width="2"/>')
        b.append(txt(cx + ww/2, y + 5, lab, size=10.5, fill=INK2, anchor='middle'))
    # connecting pipe
    b.append(f'<line x1="200" y1="{y}" x2="230" y2="{y}" stroke="{INK2}" stroke-width="4"/>')
    b.append(f'<line x1="320" y1="{y}" x2="390" y2="{y}" stroke="{INK2}" stroke-width="4"/>')
    b.append(f'<line x1="470" y1="{y}" x2="560" y2="{y}" stroke="{INK2}" stroke-width="4"/>')

    # cat-back bracket
    b.append(f'<path d="M 330 60 L 640 60 L 640 84" fill="none" stroke="{TEAL}" stroke-width="2"/>')
    b.append(txt(485, 52, 'cat-back: replaces everything from the catalyst rearward', size=11, fill=TEAL, anchor='middle'))

    # axle-back bracket
    b.append(f'<path d="M 480 180 L 640 180 L 640 150" fill="none" stroke="{RUST}" stroke-width="2"/>')
    b.append(txt(560, 198, 'axle-back: muffler and tailpipe only', size=11, fill=RUST, anchor='middle'))

    b.append(txt(w / 2, 26, 'What each exhaust system actually replaces',
                 size=14, fill=INK, weight='700', anchor='middle'))
    return svg(w, h, 'Cat-back versus axle-back exhaust',
               'A simplified exhaust layout showing the extent of a cat-back system versus an axle-back system.',
               ''.join(b))


# ── 7. Intake path ───────────────────────────────────────────────────────
def intake_path():
    w, h = 680, 260
    b = []
    y = 130
    boxes = [(80, 'throttle body', 120), (215, 'intake manifold', 150), (380, 'air filter', 120), (515, 'outside air', 110)]
    for x, lab, bw in boxes:
        b.append(f'<rect x="{x}" y="{y-20}" width="{bw}" height="40" rx="6" fill="none" stroke="{INK2}" stroke-width="2"/>')
        b.append(txt(x + bw/2, y + 5, lab, size=10.5, fill=INK2, anchor='middle'))
    for x1, x2 in [(200, 215), (365, 380), (500, 515)]:
        b.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{INK2}" stroke-width="4"/>')
    b.append(txt(w/2, y + 62, 'airflow →', size=11, fill=INK3, anchor='middle'))
    b.append(txt(w / 2, 30, 'The intake path: restriction anywhere upstream limits the whole system',
                 size=14, fill=INK, weight='700', anchor='middle'))
    b.append(caption(w, h, 'The filter is one restriction among several. A larger filter downstream of a restrictive MAF housing does little.'))
    return svg(w, h, 'Intake airflow path',
               'A diagram of the intake path from outside air through the filter, manifold and throttle body.',
               ''.join(b))


# ── 8. Load range / tyre construction ────────────────────────────────────
def load_range():
    w, h = 680, 280
    b = []
    tiers = [('P-metric', 'Passenger car construction', INK3, 1.0),
             ('LT (C / D / E)', 'Light truck, heavier sidewall', TEAL, 1.25),
             ('E rated', 'Highest common load range', RUST, 1.5)]
    base_y = 230
    for i, (name, desc, col, scale) in enumerate(tiers):
        x = 130 + i * 200
        bw = 110 * scale
        bh = 44 * scale
        b.append(f'<rect x="{x-bw/2}" y="{base_y-bh}" width="{bw}" height="{bh}" rx="5" '
                 f'fill="none" stroke="{col}" stroke-width="2.5"/>')
        b.append(txt(x, base_y + 22, name, size=12, fill=col, weight='700', anchor='middle'))
        b.append(txt(x, base_y + 40, desc, size=10, fill=INK3, anchor='middle'))
    b.append(txt(w / 2, 28, 'Load range describes sidewall construction and load capacity, not tyre size',
                 size=14, fill=INK, weight='700', anchor='middle'))
    b.append(caption(w, h, 'Schematic. Going up a load range stiffens the ride — a common complaint when a truck is fitted with E-rated tyres for looks.'))
    return svg(w, h, 'Tyre load range',
               'Three tyre sidewall sections of increasing thickness representing P-metric, LT and E load ranges.',
               ''.join(b))


# ── 9. Tuning: flash vs piggyback ────────────────────────────────────────
def tuning_compare():
    w, h = 680, 280
    b = []
    # left: flash
    b.append(f'<rect x="70" y="90" width="240" height="120" rx="8" fill="none" stroke="{TEAL}" stroke-width="2.5"/>')
    b.append(txt(190, 78, 'Flash tune', size=13, fill=TEAL, weight='700', anchor='middle'))
    b.append(txt(190, 130, 'reprograms the factory ECU', size=11, fill=INK2, anchor='middle'))
    b.append(txt(190, 152, 'full control of maps', size=11, fill=INK2, anchor='middle'))
    b.append(txt(190, 174, 'visible to dealer diagnostics', size=11, fill=RUST, anchor='middle'))

    # right: piggyback
    b.append(f'<rect x="370" y="90" width="240" height="120" rx="8" fill="none" stroke="{RUST}" stroke-width="2.5"/>')
    b.append(txt(490, 78, 'Piggyback', size=13, fill=RUST, weight='700', anchor='middle'))
    b.append(txt(490, 130, 'intercepts sensor signals', size=11, fill=INK2, anchor='middle'))
    b.append(txt(490, 152, 'limited to what it can spoof', size=11, fill=INK2, anchor='middle'))
    b.append(txt(490, 174, 'removable, but traceable', size=11, fill=INK3, anchor='middle'))

    b.append(txt(w / 2, 236, 'Neither approach makes a warranty claim safe — the failure has to be caused by the modification,',
                 size=11, fill=INK3, anchor='middle'))
    b.append(txt(w / 2, 252, 'but dealerships can and do look for evidence of either.',
                 size=11, fill=INK3, anchor='middle'))
    return svg(w, h, 'Flash tune versus piggyback',
               'Side-by-side comparison of flash tuning and piggyback tuning approaches.',
               ''.join(b))


def arrow(x1, y1, x2, y2, col, wdt=2):
    """A plain arrow: shaft plus a filled head at (x2, y2)."""
    ang = math.atan2(y2 - y1, x2 - x1)
    L = 8
    a1, a2 = ang + math.radians(150), ang - math.radians(150)
    p1 = (x2 + L * math.cos(a1), y2 + L * math.sin(a1))
    p2 = (x2 + L * math.cos(a2), y2 + L * math.sin(a2))
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{wdt}"/>'
            f'<polygon points="{x2},{y2} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{col}"/>')


def spring(cx, y0, y1, col, half=22, turns=6):
    """A coil spring drawn as a zigzag between two heights."""
    pts, n = [], turns * 2
    for i in range(n + 1):
        y = y0 + (y1 - y0) * i / n
        x = cx - half if i % 2 == 0 else cx + half
        pts.append(f'{x:.1f},{y:.1f}')
    return (f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" '
            f'stroke-width="2.2" stroke-linejoin="round"/>')


# ── 10. Tyre sidewall size code ──────────────────────────────────────────
def sidewall_decode():
    w, h = 680, 280
    b = []
    b.append(txt(w / 2, 30, 'Reading a tyre size: each part of the code is a separate specification',
                 size=14, fill=INK, weight='700', anchor='middle'))
    cy, bh = 150, 46
    segs = [
        ('275', 140, 76, TEAL, 'section width', '275 mm', 'above'),
        ('60', 236, 64, INK2, 'aspect ratio', '60% of width', 'below'),
        ('R', 320, 44, INK3, 'construction', 'radial', 'above'),
        ('20', 384, 64, INK2, 'rim diameter', '20 inches', 'below'),
        ('115', 500, 76, RUST, 'load index', '1,215 kg per tyre', 'above'),
        ('T', 596, 40, RUST, 'speed rating', 'up to 190 km/h', 'below'),
    ]
    for label, x, bw, col, name, meaning, side in segs:
        b.append(f'<rect x="{x}" y="{cy-bh/2}" width="{bw}" height="{bh}" rx="4" '
                 f'fill="none" stroke="{col}" stroke-width="2"/>')
        b.append(txt(x + bw / 2, cy + 8, label, size=21, fill=col, weight='700', anchor='middle'))
        mx = x + bw / 2
        if side == 'above':
            b.append(f'<line x1="{mx}" y1="{cy-bh/2}" x2="{mx}" y2="108" stroke="{col}" '
                     f'stroke-width="1.2" stroke-dasharray="3 3"/>')
            b.append(txt(mx, 100, name, size=10.5, fill=col, weight='600', anchor='middle'))
            b.append(txt(mx, 86, meaning, size=9.5, fill=INK3, anchor='middle'))
        else:
            b.append(f'<line x1="{mx}" y1="{cy+bh/2}" x2="{mx}" y2="196" stroke="{col}" '
                     f'stroke-width="1.2" stroke-dasharray="3 3"/>')
            b.append(txt(mx, 210, name, size=10.5, fill=col, weight='600', anchor='middle'))
            b.append(txt(mx, 224, meaning, size=9.5, fill=INK3, anchor='middle'))
    b.append(txt(224, cy + 8, '/', size=21, fill=INK3, anchor='middle'))
    b.append(caption(w, h, 'Load index and speed rating follow the size on the sidewall. Both must meet or exceed the vehicle placard.'))
    return svg(w, h, 'Tyre sidewall size code',
               'The sidewall size code broken into its parts: section width, aspect ratio, construction, rim diameter, load index and speed rating.',
               ''.join(b))


# ── 11. The three alignment angles ───────────────────────────────────────
def alignment_angles():
    w, h = 680, 350
    b = []
    b.append(txt(w / 2, 30, 'The three alignment angles', size=14, fill=INK, weight='700', anchor='middle'))
    for cx, name, view in [(128, 'camber', 'front view'), (340, 'toe', 'top view'),
                           (552, 'caster', 'side view')]:
        b.append(txt(cx, 74, name, size=12.5, fill=INK, weight='700', anchor='middle'))
        b.append(txt(cx, 90, view, size=10, fill=INK3, anchor='middle'))

    # camber: vertical tilt of the wheel, seen head-on
    cx = 128
    b.append(f'<line x1="{cx}" y1="104" x2="{cx}" y2="262" stroke="{RULE}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    b.append(f'<rect x="{cx-20}" y="112" width="40" height="146" rx="6" fill="none" '
             f'stroke="{TEAL}" stroke-width="2.5" transform="rotate(7 {cx} 185)"/>')
    b.append(f'<line x1="78" y1="270" x2="178" y2="270" stroke="{INK3}" stroke-width="1.5"/>')
    b.append(txt(cx + 32, 150, 'tilt', size=10, fill=TEAL))
    b.append(txt(cx, 246, 'vertical', size=9.5, fill=INK3, anchor='middle'))

    # toe: the angle between the two wheel planes, seen from above
    cx = 340
    b.append(f'<line x1="240" y1="185" x2="440" y2="185" stroke="{RULE}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    for ox in (250, 406):
        b.append(f'<rect x="{ox}" y="150" width="30" height="70" rx="5" fill="none" '
                 f'stroke="{INK2}" stroke-width="2.5" transform="rotate(-5 {ox+15} 185)"/>')
    b.append(txt(cx, 250, 'front of vehicle', size=10, fill=INK3, anchor='middle'))
    b.append(txt(cx, 264, 'angle between wheel planes', size=10, fill=TEAL, anchor='middle'))

    # caster: tilt of the steering axis, seen from the side
    cx = 552
    b.append(f'<line x1="{cx}" y1="104" x2="{cx}" y2="262" stroke="{RULE}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    b.append(f'<line x1="{cx+14}" y1="112" x2="{cx-10}" y2="256" stroke="{RUST}" stroke-width="2.5"/>')
    b.append(f'<circle cx="{cx+14}" cy="112" r="6" fill="none" stroke="{RUST}" stroke-width="2"/>')
    b.append(f'<circle cx="{cx-10}" cy="256" r="6" fill="none" stroke="{RUST}" stroke-width="2"/>')
    b.append(txt(cx + 24, 150, 'steering axis', size=9.5, fill={RUST}))
    b.append(txt(cx, 246, 'vertical', size=9.5, fill=INK3, anchor='middle'))

    b.append(txt(w / 2, 306, 'Changing ride height moves all three. An alignment is not optional after a lift.',
                 size=10.5, fill=INK2, anchor='middle'))
    b.append(caption(w, h, 'Camber is vertical wheel tilt, toe the angle between the wheel planes, caster the steering axis tilt.'))
    return svg(w, h, 'Camber, toe and caster',
               'Three panels showing camber from the front, toe from above and caster from the side.',
               ''.join(b))


# ── 12. What each lift method changes ────────────────────────────────────
def lift_methods():
    w, h = 680, 400
    b = []
    b.append(txt(w / 2, 30, 'What each lift method actually changes',
                 size=14, fill=INK, weight='700', anchor='middle'))

    cols = [
        (140, 'Spacer kit', RUST, 'Ride height only', 'stock travel, stock damping'),
        (340, 'Taller spring', TEAL, 'Height and travel', 'damping still fixed'),
        (540, 'Coilover', TEAL, 'Height, travel, damping', 'serviceable, costs most'),
    ]
    for cx, name, col, cap1, cap2 in cols:
        b.append(txt(cx, 74, name, size=12.5, fill=col, weight='700', anchor='middle'))
        # top mount
        b.append(f'<rect x="{cx-24}" y="116" width="48" height="12" rx="3" fill="none" stroke="{INK2}" stroke-width="2"/>')
        # damper body
        b.append(f'<rect x="{cx-14}" y="128" width="28" height="140" rx="4" fill="none" stroke="{INK2}" stroke-width="2"/>')
        if name == 'Spacer kit':
            b.append(f'<rect x="{cx-26}" y="98" width="52" height="16" rx="3" fill="{RUST}" opacity="0.18" stroke="{RUST}" stroke-width="2"/>')
            b.append(txt(cx, 168, 'spacer', size=9.5, fill=INK3, anchor='middle'))
            b.append(spring(cx, 182, 262, INK3))
        elif name == 'Taller spring':
            b.append(f'<line x1="{cx}" y1="136" x2="{cx}" y2="150" stroke="{INK3}" stroke-width="1.2" stroke-dasharray="3 3"/>')
            b.append(spring(cx, 136, 268, TEAL))
            b.append(txt(cx, 170, 'taller', size=9.5, fill=TEAL, anchor='middle'))
        else:
            b.append(spring(cx, 136, 268, TEAL))
            b.append(f'<rect x="{cx-22}" y="196" width="44" height="11" rx="2" fill="{TEAL}" opacity="0.18" stroke="{TEAL}" stroke-width="2"/>')
            b.append(txt(cx, 170, 'adjuster', size=9.5, fill=TEAL, anchor='middle'))
        b.append(txt(cx, 302, cap1, size=10.5, fill=col, weight='600', anchor='middle'))
        b.append(txt(cx, 318, cap2, size=9.5, fill=INK3, anchor='middle'))

    b.append(txt(w / 2, 352, 'All three change alignment geometry, so all three want an alignment afterwards.',
                 size=11, fill=INK2, anchor='middle'))
    b.append(caption(w, h, 'Simplified side sections. Area covered, warranty and serviceability differ by product.'))
    return svg(w, h, 'Lift methods compared',
               'Three lift approaches side by side showing which parameters each one changes.',
               ''.join(b))


# ── 13. Exhaust drone ────────────────────────────────────────────────────
def drone_resonance():
    w, h = 680, 340
    x0, x1, ybase, ytop = 100, 640, 250, 96
    b = []
    b.append(txt(w / 2, 30, 'Where an exhaust drones', size=14, fill=INK, weight='700', anchor='middle'))
    b.append(f'<rect x="300" y="{ytop}" width="160" height="{ybase-ytop}" fill="{RUST}" opacity="0.07"/>')
    b.append(f'<line x1="{x0}" y1="{ybase}" x2="{x1}" y2="{ybase}" stroke="{INK3}" stroke-width="1.5"/>')
    b.append(f'<line x1="{x0}" y1="{ybase}" x2="{x0}" y2="{ytop}" stroke="{INK3}" stroke-width="1.5"/>')

    stock = [(100, 238), (160, 232), (220, 226), (280, 224), (340, 228),
             (400, 236), (460, 242), (520, 246), (580, 248), (640, 249)]
    after = [(100, 236), (160, 224), (220, 206), (280, 180), (310, 158), (340, 146),
             (370, 148), (400, 158), (430, 178), (460, 200), (500, 220), (560, 236), (640, 243)]
    for pts, col in ((stock, INK3), (after, RUST)):
        d = ' '.join(f'{x},{y}' for x, y in pts)
        b.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="2.5" stroke-linejoin="round"/>')

    b.append(txt(380, 112, 'drone band', size=10, fill=RUST, weight='700', anchor='middle'))
    b.append(txt(470, 196, 'aftermarket', size=10, fill=RUST))
    b.append(txt(520, 236, 'stock', size=10, fill=INK3, anchor='middle'))
    for x, lab in ((118, 'idle'), (380, 'cruise'), (580, 'highway')):
        b.append(txt(x, 268, lab, size=10, fill=INK3, anchor='middle'))
    b.append(f'<text x="76" y="173" font-family="sans-serif" font-size="10" fill="{INK3}" '
             f'text-anchor="middle" transform="rotate(-90 76 173)">cabin sound level</text>')
    b.append(caption(w, h, 'Illustrative. Drone depends on engine speed, pipe diameter and cabin resonance — not on brand.'))
    return svg(w, h, 'Exhaust drone band',
               'Two curves of cabin sound level against engine speed, showing a resonance hump in the aftermarket system.',
               ''.join(b))


# ── 14. Brake pad temperature windows ────────────────────────────────────
def pad_temp_window():
    w, h = 680, 340
    x0, x1, ybase, ytop = 100, 640, 250, 96
    b = []
    b.append(txt(w / 2, 30, 'Pad compounds work over different temperature windows',
                 size=14, fill=INK, weight='700', anchor='middle'))
    b.append(f'<line x1="{x0}" y1="{ybase}" x2="{x1}" y2="{ybase}" stroke="{INK3}" stroke-width="1.5"/>')
    b.append(f'<line x1="{x0}" y1="{ybase}" x2="{x0}" y2="{ytop}" stroke="{INK3}" stroke-width="1.5"/>')

    curves = [
        ([(100, 236), (140, 206), (180, 178), (220, 190), (260, 220), (300, 240), (340, 248)], TEAL, 'street'),
        ([(100, 246), (180, 232), (240, 198), (300, 168), (340, 158), (380, 168),
          (420, 196), (460, 222), (520, 242)], INK2, 'performance'),
        ([(100, 248), (220, 246), (300, 232), (360, 206), (420, 176), (480, 156),
          (520, 152), (560, 164), (600, 196), (640, 226)], RUST, 'track'),
    ]
    labels = {'street': (176, 166), 'performance': (340, 146), 'track': (516, 140)}
    for pts, col, name in curves:
        d = ' '.join(f'{x},{y}' for x, y in pts)
        b.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="2.5" stroke-linejoin="round"/>')
        lx, ly = labels[name]
        b.append(txt(lx, ly, name, size=10, fill=col, weight='600', anchor='middle'))

    b.append(txt(370, 274, 'brake temperature', size=10, fill=INK3, anchor='middle'))
    b.append(txt(112, 292, 'cold', size=9.5, fill=INK3, anchor='middle'))
    b.append(txt(628, 292, 'hot', size=9.5, fill=INK3, anchor='middle'))
    b.append(f'<text x="76" y="173" font-family="sans-serif" font-size="10" fill="{INK3}" '
             f'text-anchor="middle" transform="rotate(-90 76 173)">friction</text>')
    b.append(caption(w, h, 'Illustrative shapes. A track pad used only on the street never reaches its window.'))
    return svg(w, h, 'Brake pad temperature windows',
               'Friction against temperature for street, performance and track pad compounds, each peaking in a different range.',
               ''.join(b))


# ── 15. Where the filter draws its air ───────────────────────────────────
def filter_types():
    w, h = 680, 360
    b = []
    b.append(txt(w / 2, 30, 'Two intakes, two different sources of air',
                 size=14, fill=INK, weight='700', anchor='middle'))

    # left: open cone sitting in the engine bay
    b.append(txt(180, 78, 'open cone in the engine bay', size=11.5, fill=INK2, weight='600', anchor='middle'))
    b.append(f'<rect x="50" y="100" width="260" height="180" rx="10" fill="none" stroke="{RULE}" '
             f'stroke-width="1.5" stroke-dasharray="6 4"/>')
    b.append(f'<rect x="80" y="180" width="80" height="70" rx="4" fill="none" stroke="{INK3}" stroke-width="2"/>')
    b.append(txt(120, 220, 'engine', size=9.5, fill=INK3, anchor='middle'))
    b.append('<polygon points="190,140 240,150 240,210 190,220" fill="none" '
             f'stroke="{RUST}" stroke-width="2.5"/>')
    b.append(txt(215, 230, 'filter', size=9.5, fill=RUST, anchor='middle'))
    for a in [(112, 120, 178, 148), (250, 118, 232, 142), (120, 250, 180, 208)]:
        b.append(arrow(*a, RUST, wdt=1.6))
    b.append(txt(180, 306, 'filter draws engine-bay air', size=10.5, fill=RUST, anchor='middle'))

    # right: sealed box ducted to the fender
    b.append(txt(500, 78, 'sealed box ducted to the fender', size=11.5, fill=INK2, weight='600', anchor='middle'))
    b.append(f'<rect x="370" y="100" width="260" height="180" rx="10" fill="none" stroke="{RULE}" '
             f'stroke-width="1.5" stroke-dasharray="6 4"/>')
    b.append(f'<rect x="400" y="180" width="80" height="70" rx="4" fill="none" stroke="{INK3}" stroke-width="2"/>')
    b.append(txt(440, 220, 'engine', size=9.5, fill=INK3, anchor='middle'))
    b.append(f'<rect x="500" y="150" width="90" height="70" rx="4" fill="none" stroke="{TEAL}" stroke-width="2.5"/>')
    b.append(txt(545, 190, 'sealed box', size=9.5, fill=TEAL, anchor='middle'))
    b.append(f'<polyline points="512,158 430,158 430,104 356,104" fill="none" stroke="{TEAL}" '
             f'stroke-width="4" stroke-linejoin="round"/>')
    b.append(arrow(380, 104, 350, 104, TEAL, wdt=3))
    b.append(txt(408, 96, 'outside air', size=9.5, fill=TEAL, anchor='middle'))
    b.append(txt(500, 306, 'filter draws from outside the bay', size=10.5, fill=TEAL, anchor='middle'))

    b.append(caption(w, h, 'A sealed box fed from the fender sees cooler air than an open element in the bay.'))
    return svg(w, h, 'Open cone versus sealed airbox',
               'Two engine bays: an open cone drawing hot bay air, and a sealed airbox ducted to the fender.',
               ''.join(b))


DIAGRAMS = {
    'wheel-offset.svg': wheel_offset,
    'backspacing-vs-offset.svg': backspacing,
    'plus-sizing.svg': plus_sizing,
    'leveling-geometry.svg': leveling_geometry,
    'brake-bedding.svg': brake_bedding,
    'exhaust-layout.svg': exhaust_layout,
    'intake-path.svg': intake_path,
    'load-range.svg': load_range,
    'tuning-compare.svg': tuning_compare,
    'sidewall-decode.svg': sidewall_decode,
    'alignment-angles.svg': alignment_angles,
    'lift-methods.svg': lift_methods,
    'drone-resonance.svg': drone_resonance,
    'pad-temp-window.svg': pad_temp_window,
    'filter-types.svg': filter_types,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in DIAGRAMS.items():
        path = os.path.join(OUT, name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(fn())
        print(f'  {name}  ({os.path.getsize(path):,} bytes)')
    print(f'wrote {len(DIAGRAMS)} diagrams -> {OUT}')


if __name__ == '__main__':
    main()
