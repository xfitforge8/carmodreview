#!/usr/bin/env python3
"""Render a vertical short (1080x1920) from an article's own text.

Why this exists instead of a template video: every claim in a short has to be a
claim the article already makes and can source. So the script reads the real
article file, pulls the headline numbers straight out of it, and refuses to run
if it cannot find them. Nothing is retyped from memory into a caption, which is
the way a number drifts between the page and the video.

What it does not do: it does not animate a cover or show a product. There is no
b-roll of these parts because we have not photographed any, so the cards carry
the figures and the page carries the detail.

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

# Kicker line and hashtags, keyed by the article's own category. These used to
# name one specific truck, which both narrowed reach and told every owner of a
# different vehicle that the guide was not for them. The topic is what the
# video is about; the vehicle is not.
CAT_KICKER = {
    'Engine': 'ENGINE & INTAKE',
    'Exhaust': 'EXHAUST',
    'Suspension': 'SUSPENSION',
    'Brakes': 'BRAKES',
    'Wheels & Tires': 'WHEELS & TIRES',
    'Tonneau & Bed': 'TRUCK BED',
    'Tuning': 'TUNING',
}
CAT_TAGS = {
    'Engine': '#engine #airintake #carmods #diyrepair',
    'Exhaust': '#exhaust #carmods #diyrepair #truckmods',
    'Suspension': '#suspension #liftkit #carmods #truckmods',
    'Brakes': '#brakes #carmods #diyrepair #carrepair',
    'Wheels & Tires': '#wheels #tires #fitment #carmods',
    'Tonneau & Bed': '#truckbed #truckmods #carmods #diyrepair',
    'Tuning': '#tuning #carmods #turbo #diyrepair',
}


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
    """Category slug and category name for an article.

    Returns (slug, name) -- the slug builds the URL, the name picks the kicker
    line and hashtags, so a video never names a vehicle it is not about.

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
                key = cat.group(1).strip()
                return m.CATEGORIES.get(key, ('engine',))[0], key
    return 'engine', 'Engine'


def cover(slug, cards, outdir):
    """Render the first card as a 1080x1350 still for the Instagram feed.

    Instagram's feed is 4:5, not 9:16. Posting the vertical short as a still
    would letterbox it, so the cover gets its own render at the feed ratio with
    the same type. The video reels still use the 9:16 file.
    """
    W2, H2 = 1080, 1350
    c = cards[0]
    out = os.path.join(outdir, f'{slug}-cover.jpg')
    vf = []
    y = 520
    if c['kicker']:
        vf.append(f"drawtext=fontfile={FONT_BOLD}:text='{esc(c['kicker'])}':"
                  f"fontcolor={MUTED}:fontsize=42:x=(w-text_w)/2:y={y - 150}")
    for ln in wrap(c['main'], 16):
        vf.append(f"drawtext=fontfile={FONT_BOLD}:text='{esc(ln)}':"
                  f"fontcolor={PAPER}:fontsize=82:x=(w-text_w)/2:y={y}")
        y += 100
    if c['sub']:
        y += 40
        for ln in wrap(c['sub'], 30):
            vf.append(f"drawtext=fontfile={FONT_REG}:text='{esc(ln)}':"
                      f"fontcolor={MUTED}:fontsize=44:x=(w-text_w)/2:y={y}")
            y += 62
    vf.append(f"drawbox=x=(iw-140)/2:y={520 - 70}:w=140:h=4:color={ACCENT}:t=fill")
    vf.append('format=yuv420p')
    subprocess.run(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
         '-f', 'lavfi', '-i', f'color=c={INK}:s={W2}x{H2}:d=1',
         '-vf', ','.join(vf), '-frames:v', '1', '-q:v', '2', out],
        check=True)
    return out


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
    # The whole first paragraph, not its first line. `(.+?)$` with re.M stops at
    # the newline, so a paragraph wrapped across four lines came back as one
    # truncated line and the hook in the description ended mid-sentence:
    # "they are really five different". Match through to the blank line.
    lede = must(r'^## EN\s*\n+([\s\S]*?)(?:\n\s*\n)', 'the opening paragraph')
    lede = re.sub(r'\s+', ' ', lede).strip()

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
    # the part after the colon -- but only when the prefix is a noun-phrase
    # label, not the start of a question or a statement. "Cold Air Intake: What
    # It Does..." splits cleanly on the colon but the tail is a sentence
    # fragment, and "What a Leveling Kit Does -- and What It Costs You" splits
    # on an em dash that is part of the sentence. Both are better whole. A
    # prefix starting with What/How/Why/When/Where/Which is the giveaway that
    # it is prose, not a label.
    headline = title
    m = re.match(r'^(?!(?:what|how|why|when|where|which)\b)([\w &/\-]{6,}):\s*(.+)$',
                 title, re.I)
    if m:
        headline = m.group(2).strip()

    # Resolved before the cards, not after: the first card's kicker comes from
    # here. It used to be the literal 'SILVERADO 1500', which narrowed every
    # short to one truck and told every other owner the guide was not for them.
    cat_slug, topic = cat_path(slug)
    kicker = CAT_KICKER.get(topic, topic.upper())

    cards = [
        card(headline, kicker=kicker, seconds=3.5),
        card(money(lo), sub='the bottom of the range on this guide',
             kicker='THE CHEAP END', seconds=4.0),
        card(money(hi), sub='the top of the range on this guide',
             kicker='THE EXPENSIVE END', seconds=4.0),
        card(lead_line, kicker='THE SHORT VERSION', seconds=4.5, accent=True),
        card('Full guide at carmodreview.com',
             sub='every price dated to the listing it came from',
             kicker='READ THE REST', seconds=4.0, accent=True),
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
    url = f'https://carmodreview.com/{cat_slug}/{slug}.html'

    # Sourcing is stated as fact, not as a disclaimer. "Prices read off the
    # listing, dated 5 Nov 2026" is a credibility signal; "we have not tested
    # these" is a hedge that makes a reader trust the page less. The site still
    # never claims first-hand testing -- it simply does not narrate what it
    # didn't do. The article itself keeps its "what we could not verify"
    # section, where that belongs.
    has_listings = bool(re.search(r'listing|list price|reviews\b', body, re.I))
    if has_listings:
        source_line = 'Prices and review counts from live listings, dated in the guide.'
    else:
        source_line = 'Sources named for every claim in the guide.'

    tags = (CAT_TAGS.get(topic, '#truckmods #carmods #diyrepair')
            + (' #tonneaucover' if 'tonneau' in slug else ''))
    plain_lede = re.sub(r'\s+', ' ', lede)[:220].rstrip()

    # A teaser reads better than a summary: state the hook, then name what the
    # guide actually answers. The bullets come from the article's own h3
    # headings, so the description cannot promise a section the page does not
    # have. "What we could not verify" is filtered out -- it is the right thing
    # to have on the page and the wrong thing to lead a short with.
    en_body = body.split('## EN', 1)[-1]
    heads = [h.strip() for h in re.findall(r'^###\s+(.+)$', en_body, re.M)]
    heads = [h for h in heads if not re.search(r'could not verify|cannot verify|'
                                               r'확인하지 못한|no pudimos', h, re.I)]
    # Headings like "1. The $65-97 drop-in filter" are already an ordered list
    # on the page; rendering them as "- 1. ..." in a description shows two
    # numbering schemes at once. Drop the article's own number, keep the bullet.
    heads = [re.sub(r'^\d+[.)]\s*', '', h) for h in heads]
    bullets = '\n'.join(f'- {h}' for h in heads[:4])

    # Two whole sentences, not a character count. Slicing the lede at 220 chars
    # cut "Intakes are sold as one product category but they are really five
    # different" off mid-sentence, which reads like a bug rather than a hook.
    raw_lede = re.sub(r'\s+', ' ', lede).strip()
    sentences = re.split(r'(?<=[.!?])\s+', raw_lede)
    hook = ' '.join(sentences[:2]).strip()
    if len(hook) > 260:
        hook = sentences[0].strip()

    # No .title() on the headline: it capitalises "to", "and" and "of", which is
    # not title case and looks machine-touched. The article title is already
    # cased correctly.
    #
    # The description leads with the full title, not the card headline. The card
    # is allowed to drop a label prefix -- "Leveling Kits: What They Change..."
    # fits a card better as "What They Change..." because the kicker above it
    # already says LEVELING KITS. A YouTube title has no kicker above it, so
    # dropping the prefix there leaves a first line with no subject at all.
    desc = (f'{re.sub(r"\s+", " ", title).strip()}\n\n'
            f'{hook}\n\n'
            + (f'In the full guide:\n{bullets}\n\n' if bullets else '')
            + f'{url}\n\n{source_line}')
    caption = (f'{re.sub(r"\s+", " ", title)}\n\n'
               f'{plain_lede}\n\n'
               f'{source_line}\n\n'
               f'Full guide: {url}\n\n{tags}')
    open(os.path.join(outdir, f'{slug}-caption.txt'), 'w',
         encoding='utf-8').write(caption + '\n')
    open(os.path.join(outdir, f'{slug}-youtube.txt'), 'w',
         encoding='utf-8').write(desc + '\n')
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y']
    for p in parts:
        cmd += ['-f', 'lavfi', '-i', p]
    cmd += ['-filter_complex', graph, '-map', '[outv]',
            '-t', str(total), '-r', str(FPS),
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    print(f'wrote {out}  ({total:.0f}s, {W}x{H})')
    cover(slug, cards, outdir)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--out', default=os.path.join(ROOT, 'social'))
    a = ap.parse_args()
    render(a.slug, os.path.expanduser(a.out))


if __name__ == '__main__':
    main()
