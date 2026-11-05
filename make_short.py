#!/usr/bin/env python3
"""Render a vertical short (1080x1920) from an article's own text.

Why this exists instead of a template video: every claim in a short has to be a
claim the article already makes and can source. So the script reads the real
article file, pulls the headline numbers straight out of it, and refuses to run
if it cannot find them. Nothing is retyped from memory into a caption, which is
the way a number drifts between the page and the video.

What it does not do: it does not animate a cover, show a product, or imply we
handled one. There is no b-roll of these covers because we have not photographed
any, and the short says so on screen.

  python3 make_short.py tonneau-covers-explained
  python3 make_short.py tonneau-covers-explained --out ~/Desktop
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.expanduser('~/carmodreview')
OUT = os.path.join(ROOT, 'docs')

W, H = 1080, 1920
FPS = 30

# Palette lifted from style.css so the video matches the site rather than
# looking like a different brand in the feed.
INK = '0x14161A'
PAPER = '0xF7F5F1'
MUTED = '0x9AA0A6'
ACCENT = '0xB4402F'
RULE = '0x2C3038'

FONT_BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
FONT_REG = '/System/Library/Fonts/Supplemental/Arial.ttf'


def esc(text):
    """Escape text for drawtext's filtergraph parser.

    The colon and backslash are the two characters that break a drawtext
    argument; commas and single quotes need escaping too because the whole
    graph is one comma-separated string. Article titles contain em dashes and
    question marks, which are safe, but prices contain no specials and years
    are digits, so most slides go through untouched.
    """
    for a, b in (('\\', '\\\\\\\\'), (':', '\\:'), ("'", "’"),
                 ('%', '\\%'), (',', '\\,')):
        text = text.replace(a, b)
    return text


def wrap(text, width):
    """Greedy wrap, because drawtext has no wrapping of its own."""
    words, lines, cur = text.split(), [], ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if len(trial) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def probe_duration(path):
    out = subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height',
         '-of', 'json', path])
    s = json.loads(out)['streams'][0]
    return int(s['width']), int(s['height'])


def card(main, sub=None, kicker=None, seconds=4.0, accent=False):
    """One full-frame text card as a filtergraph segment plus a video clip.

    Returns a single-clip lavfi input string and its drawtext filters. Caller
    concatenates the clips.
    """
    return dict(main=main, sub=sub, kicker=kicker, seconds=seconds, accent=accent)


def build_filtergraph(cards, audio=False):
    """Turn cards into a filter_complex string over N lavfi color sources."""
    parts, chains = [], []
    for c in cards:
        parts.append(f'color=c={INK}:s={W}x{H}:r={FPS}:d={c["seconds"]}')
    for i, c in enumerate(cards):
        vf = []
        y = 760
        if c['kicker']:
            vf.append(
                f"drawtext=fontfile={FONT_BOLD}:text='{esc(c['kicker'])}':"
                f"fontcolor={ACCENT if c['accent'] else MUTED}:fontsize=42:"
                f"x=(w-text_w)/2:y={y - 150}")
        main_lines = wrap(c['main'], 16)
        for ln in main_lines:
            vf.append(
                f"drawtext=fontfile={FONT_BOLD}:text='{esc(ln)}':"
                f"fontcolor={PAPER}:fontsize=82:x=(w-text_w)/2:y={y}")
            y += 100
        if c['sub']:
            y += 40
            for ln in wrap(c['sub'], 30):
                vf.append(
                    f"drawtext=fontfile={FONT_REG}:text='{esc(ln)}':"
                    f"fontcolor={MUTED}:fontsize=44:x=(w-text_w)/2:y={y}")
                y += 62
        # A short accent rule under the kicker, matching the site's 1px rules.
        vf.append(
            f"drawbox=x=(iw-140)/2:y=690:w=140:h=4:color={ACCENT}:t=fill")
        vf.append(f"format=yuv420p[v{i}]")
        chains.append(f'[{i}:v]' + ','.join(vf))
    concat_in = ''.join(f'[v{i}]' for i in range(len(cards)))
    chains.append(f'{concat_in}concat=n={len(cards)}:v=1:a=0[outv]')
    return parts, ';'.join(chains)


def cat_path(slug):
    """Category slug for an article, read from the same mapping the site uses.

    Imported lazily rather than at module top: build.py does real work at import
    time, and this script only needs the one dict.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_build', os.path.join(ROOT, 'build.py'))
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except SystemExit:
        pass
    src = os.path.join(ROOT, 'content', 'articles')
    for f in os.listdir(src):
        p = os.path.join(src, f)
        body = open(p, encoding='utf-8').read()
        if re.search(r'^slug:\s*' + re.escape(slug) + r'\s*$', body, re.M):
            cat = re.search(r'^category:\s*(.+?)\s*$', body, re.M)
            if cat:
                return m.CATEGORIES.get(cat.group(1), ('engine',))[0]
    return 'engine'


def render(slug, outdir):
    src = None
    for f in os.listdir(os.path.join(ROOT, 'content', 'articles')):
        p = os.path.join(ROOT, 'content', 'articles', f)
        if re.search(r'^slug:\s*' + re.escape(slug) + r'\s*$',
                     open(p, encoding='utf-8').read(), re.M):
            src = p
            break
    if not src:
        sys.exit(f'no article with slug {slug}')

    body = open(src, encoding='utf-8').read()

    def must(pattern, label):
        m = re.search(pattern, body, re.M)
        if not m:
            sys.exit(f'refusing to build: could not find {label} in {slug}')
        return m.group(1)

    title = must(r'^\s+en:\s*"(.+?)"\s*$', 'the English title')
    seo = re.search(r'^\s+en:\s*"(.+?)"\s*$', body, re.M)
    lede = must(r'^## EN\s*\n\s*\n(.+?)$', 'the opening line')

    # Every figure on screen is scraped from the article, never retyped. If an
    # article is re-priced and the scrape finds nothing, the build stops instead
    # of publishing a short with a stale number -- the two must not drift.
    amounts = sorted({m.replace(',', '') for m in
                      re.findall(r'\$([\d,]+\.\d{2}|\d[\d,]*)', body)},
                     key=lambda s: float(s))
    if len(amounts) < 2:
        sys.exit(f'refusing to build: {slug} has no price range to quote')
    lo, hi = amounts[0], amounts[-1]

    def money(s):
        v = float(s)
        return f'${v:,.0f}' if v == int(v) else f'${v:,.2f}'

    # First sentence of the lede, trimmed to a headline that fits a card.
    lead_line = re.split(r'(?<=[.!?])\s', re.sub(r'\s+', ' ', lede))[0]
    lead_line = lead_line[:110].rstrip(' ,;:')

    # Titles that are themselves "Topic: subtitle" read badly as a card, so keep
    # the part after the colon when there is one -- but only when the prefix is
    # long enough to be a real label. "What $190 Buys and What $1,500 Buys" has
    # no colon and passes through untouched; stripping on any colon cut the
    # first two words off titles that merely contained one.
    headline = title
    if re.search(r'^\w[\w &/\-]{6,}:', title):
        headline = title.split(':', 1)[1].strip()

    cards = [
        card(headline, kicker='SILVERADO 1500', seconds=3.5),
        card(money(lo), sub='the bottom of the range on this guide',
             kicker='THE CHEAP END', seconds=4.0),
        card(money(hi), sub='the top of the range on this guide',
             kicker='THE EXPENSIVE END', seconds=4.0),
        card(lead_line, kicker='THE SHORT VERSION', seconds=4.5, accent=True),
        card('We have not tested these.', sub='Every number is read off the '
             'listing. Full guide at carmodreview.com', kicker='WHAT THIS IS',
             seconds=4.5, accent=True),
    ]

    parts, graph = build_filtergraph(cards)
    total = sum(c['seconds'] for c in cards)

    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f'{slug}-short.mp4')

    # Caption and title are written next to the video, because the text that
    # gets pasted into Instagram and the text that gets pasted into a YouTube
    # Short are not the same file. Hashtags stay generic: the niche ones get
    # spammed to death and a generic set is what the platforms' own discovery
    # actually reads.
    url = f'https://carmodreview.com/{cat_path(slug)}/{slug}.html'

    # The sourcing line has to match the article it sits under. A guide built on
    # live retailer listings can say so; one built on manufacturer specs and
    # published figures cannot, and claiming otherwise on a guide that quotes no
    # listings is exactly the kind of small inaccuracy the site is meant to
    # avoid. So the sentence is chosen from what the article actually contains.
    has_listings = bool(re.search(r'listing|list price|reviews\b', body, re.I))
    if has_listings:
        source_line = ('Prices and review counts are read off live retailer '
                       'listings and dated in the guide.')
    else:
        source_line = 'Every claim is sourced in the guide, with the source named.'

    tags = ('#silverado #silverado1500 #chevy #truckmods #tonneaucover'
            if slug.startswith('tonneau')
            else '#silverado #silverado1500 #chevy #truckmods #carmods')
    plain_lede = re.sub(r'\s+', ' ', lede)[:220].rstrip()
    caption = (f'{re.sub(r"\s+", " ", title)}\n\n'
               f'{plain_lede}\n\n'
               f'No first-hand testing is claimed. {source_line}\n\n'
               f'Full guide: {url}\n\n{tags}')
    open(os.path.join(outdir, f'{slug}-caption.txt'), 'w',
         encoding='utf-8').write(caption + '\n')
    open(os.path.join(outdir, f'{slug}-youtube.txt'), 'w', encoding='utf-8').write(
        headline.title().replace('?', '') + '\n\n'
        + re.sub(r'\s+', ' ', lede)[:300].rstrip() + '\n\n'
        + f'Full guide: {url}\n\n'
        + f'No first-hand testing is claimed. {source_line}\n')
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y']
    for p in parts:
        cmd += ['-f', 'lavfi', '-i', p]
    cmd += ['-filter_complex', graph, '-map', '[outv]',
            '-t', str(total), '-r', str(FPS),
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    print(f'wrote {out}  ({total:.0f}s, {W}x{H})')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--out', default=os.path.join(ROOT, 'social'))
    a = ap.parse_args()
    render(a.slug, os.path.expanduser(a.out))


if __name__ == '__main__':
    main()
