#!/usr/bin/env python3
"""Render a vertical short (1080x1920) from an article's own text.

Why this exists instead of a template video: every claim in a short has to be a
claim the article already makes and can source. So the script reads the real
article file, pulls the headline numbers straight out of it, and refuses to run
if it cannot find them. Nothing is retyped from memory into a caption, which is
the way a number drifts between the page and the video.

Each card carries a real photograph of the product it names, fetched from that
product's own listing by fetch_products.py. Nothing here is generated: a short
that shows a part has to show that part, or it is the same stock-photo filler it
was meant to replace.

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
# Product photographs, one directory per article, keyed by pick position.
# Fetched from the retailer's own listing by fetch_products.py.
PRODUCT_ROOT = os.path.join(ROOT, 'content', 'products')

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
    """Greedy wrap, because drawtext has no wrapping of its own.

    A single word longer than `width` is hard-split rather than left to run off
    the frame. drawtext does not wrap and does not clip, so 'carmodreview.com'
    at 82px simply continued past the right edge and out of the video -- the
    card looked like a deliberate crop rather than a bug.
    """
    lines, cur = [], ''
    for chunk in text.split('\n'):
        if cur:
            lines.append(cur)
            cur = ''
        for w in chunk.split():
            trial = (cur + ' ' + w).strip()
            if len(trial) <= width:
                cur = trial
                continue
            if cur:
                lines.append(cur)
            while len(w) > width:
                lines.append(w[:width])
                w = w[width:]
            cur = w
        if cur:
            lines.append(cur)
            cur = ''
    return [l for l in lines if l]


# Words that cannot end a sentence. A card whose sub-line stops on one of
# these reads as text that was cut, not text that finished: "...is removed
# rather", "...in the range we". Shared by both the word-boundary and the
# punctuation-boundary cut, because a comma cut can land on one just as easily.
_DANGLE = {
    'a', 'an', 'the', 'and', 'or', 'but', 'of', 'to', 'in', 'on', 'at',
    'for', 'from', 'with', 'by', 'as', 'is', 'are', 'was', 'were', 'be',
    'that', 'which', 'than', 'then', 'so', 'if', 'when', 'while', 'into',
    'over', 'under', 'about', 'its', 'this', 'these', 'those', 'any',
    'all', 'more', 'most', 'not', 'no', 'you', 'your', 'it',
    'rather', 'we', 'they', 'our', 'their', 'also', 'very',
    'just', 'even', 'still', 'only', 'both', 'each', 'same', 'other',
}
# Finds the final word of a string, ignoring trailing punctuation. Two things
# went wrong here before it worked. The pattern anchored with \b, which fails
# once a full stop has been appended -- "rather." has no word boundary after
# the dot, so every cut passed. And it was applied with .match(), which only
# anchors at the start of the string, so even a correct pattern would have
# found nothing. It must be .search().
_DANGLING_TAIL = re.compile(
    r'(?:^|\s)(' + '|'.join(sorted(_DANGLE)) + r')[.,;:]?$', re.I)


def fit_words(text, width, max_lines):
    """Trim `text` to at most `max_lines` wrapped lines, always ending cleanly.

    Three bugs lived in the naive version of this, and each showed up on
    screen. Character-count truncation put the cut wherever the count landed,
    so a sub-line ended "rather than an open cone with..." -- one orphaned word,
    reading as broken rather than cut. Counting the lines before the ellipsis
    was appended meant the "..." itself pushed the result one line past the
    budget, and the layout silently clipped it. And a plain word-boundary cut
    leaves dangling connectives: "the money over...", "puts it ahead of..."
    are not truncated sentences, they are sentences that stopped.

    So the cut is taken at the last real clause boundary that fits -- a comma,
    colon, semicolon or full stop the article itself wrote -- and closed with a
    full stop. Every candidate is collected rather than stopping at the first
    separator type, because the best break is often the last comma and not the
    first colon. Only when no punctuation fits at all does it fall back to a
    word cut that avoids ending on a connective.
    """
    text = re.sub(r'\s+', ' ', text).strip()

    def closed(cand):
        cand = cand.rstrip(' ,;:-')
        return cand if cand.endswith(('.', '!', '?')) else cand + '.'

    def fits(cand):
        return len(wrap(cand, width)) <= max_lines

    if fits(text):
        return closed(text)

    # A cut at a comma can manufacture a fragment that reads as a claim:
    # "If the goal is sound and the budget is tight." is a subordinate clause
    # with a full stop bolted on, and on a card it looks like the video's
    # conclusion. Any candidate opening with a subordinator is rejected, and
    # the cut falls further back to a word boundary with an ellipsis.
    SUBORD = re.compile(r'^(?:if|when|while|since|although|though|unless|'
                        r'because|after|before|once|as|until)\b', re.I)
    best = ''
    for m in re.finditer(r'[,;:.]\s', text):
        cand = closed(text[:m.start()])
        if SUBORD.match(cand):
            continue
        # A punctuation cut is no safer than a word cut: "...is removed rather
        # than managed" cut at an earlier comma gives "...is removed rather.",
        # and "in the range we checked" gives "...in the range we." Both are
        # the same defect -- a line ending on a word that needs what follows.
        if _DANGLING_TAIL.search(cand):
            continue
        if len(cand) > len(best) and fits(cand):
            best = cand
    if best:
        return best

    # No punctuation break fits inside the budget. Drop whole words, skipping
    # any cut that would end the line on a word that cannot end a sentence.
    words = text.split()
    for end in range(len(words), 3, -1):
        cand = closed(' '.join(words[:end]))
        if _DANGLING_TAIL.search(cand):
            continue
        if fits(cand):
            return cand
    return closed(' '.join(words[:4]))


def probe_duration(path):
    out = subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height',
         '-of', 'json', path])
    s = json.loads(out)['streams'][0]
    return int(s['width']), int(s['height'])


def product_image(product_root, slug, pos):
    """Path to the photograph for one pick, or None.

    Accepts any image extension because fetch_products.py decides the extension
    from the file's magic bytes -- the retailer's image service names every file
    .jpg and serves WebP. Returns None rather than raising: a short without a
    photo is still publishable, a short that crashes because one image is
    missing is not.
    """
    d = os.path.join(product_root, slug)
    if not os.path.isdir(d):
        return None
    for f in sorted(os.listdir(d)):
        if f.startswith(f'{pos:02d}-') and f.lower().endswith(
                ('.webp', '.jpg', '.jpeg', '.png')):
            return os.path.join(d, f)
    return None


# Every HTML entity the article files actually use. A named table rather than
# html.unescape(), because the article bodies contain things like "&amp;lt;"
# written literally in code examples, and unescaping those twice would corrupt
# them. These seven cover every entity in content/articles/.
_ENT = {'&ndash;': '-', '&mdash;': '-', '&minus;': '-', '&middot;': '-',
        '&amp;': '&', '&nbsp;': ' ', '&rsquo;': "'", '&times;': 'x',
        '&quot;': '"', '&#39;': "'", '&lt;': '<', '&gt;': '>'}


def unent(text):
    """Decode the entities the article files use."""
    for k, v in _ENT.items():
        text = text.replace(k, v)
    return text


# A short is watched on its own, with no page around it. The buy blocks were
# written to sit inside a long article, so their first sentence is often about
# the article -- "the pick from the section above", "the distinction this
# article keeps returning to", "the two things the rest of this article says
# matter". On a phone that reads as a video that started in the middle.
# read_picks() keeps the whole reason; this picks the sentence that stands
# alone, and only falls back to a structural one when every sentence has it.
_STRUCT = re.compile(
    r'\bsection above\b|\bthe section\b|\bsections?\b|\bthis article\b'
    r'|\bthis page\b|\babove\b|\bbelow\b|\bthe rest of\b|\bearlier\b'
    r'|\bwe(?: have)? (?:said|covered|mentioned|explained)\b', re.I)


# A sentence opening on one of these is a subordinate clause, not a claim:
# "If the goal is sound and the budget is tight." on a card looks like the
# video's conclusion while actually being half a sentence.
_SUBORD = re.compile(r'^(?:if|when|while|since|although|though|unless|because|'
                     r'after|before|once|as|until)\b', re.I)


def _STRUCT_SUB(t):
    """Strip a reference to the article, keeping the sentence readable.

    "This is the piggyback option from the section above" is true on the page
    and meaningless in a video with no page around it. The reference goes and
    the sentence stays; "this article" becomes "the guide" rather than being
    deleted, because deleting the subject of a sentence leaves "This is the
    option would point you to". Longer phrases first, so "from the section
    above" is not left behind as a dangling "from the".
    """
    t = re.sub(
        r'\s*(?:,?\s*from the section above|,?\s*from the section below)'
        r'|\s*,?\s*which is (?:exactly )?the (?:discipline|distinction|point)'
        r' this article [^,.]*'
        r'|\s*,?\s*the rest of this article says matter'
        r'|\s*,?\s*at the price the section implies'
        r'|\s*,?\s*(?:the )?section above'
        r'|\s*,?\s*the earlier section',
        '', t)
    t = re.sub(r'\bthis article\b', 'the guide', t)
    t = re.sub(r'\s+([,.;:])', r'\1', t)
    return re.sub(r'\s{2,}', ' ', t).strip()


def pick_reason(why, width=32, max_lines=4):
    """One self-contained sentence from a buy block's explanation.

    Two attempts got this wrong in opposite directions, both visible on screen.
    Truncating a long sentence to fit produced "the money over...", "in the
    range we.", "damages." -- grammatical wreckage. Splitting on commas to
    avoid truncating then produced lowercase clause tails: "which puts it
    ahead of several pricier options", "and the arms are what bring the
    alignment back". Those are not sentences; they are the second half of one,
    and a card that opens on "which" reads as broken.

    A clause only counts if it stands as a sentence on its own: it starts with
    a capital, contains a verb of its own, and names something. Within the ones
    that qualify, the sentence carrying a claim -- a figure, a because, a
    comparison -- wins over one that just describes. Failing all that, the
    whole sentence is trimmed with fit_words, which ends cleanly.
    """
    why = re.sub(r'\s+', ' ', unent(why or '')).strip()
    if not why:
        return ''

    def fits(t):
        return len(wrap(t, width)) <= max_lines

    sents = [x.strip() for x in re.split(r'(?<=[.!?])\s+', why) if x.strip()]
    good = [x for x in sents
            if not _STRUCT.search(x) and not _SUBORD.match(x)
            and len(x.split()) >= 6]

    # A sentence that starts lowercase came from a mid-sentence split in the
    # article itself ("...trouble. dry media, which means..."), which makes it
    # a fragment no matter how long it is.
    good = [x for x in good if x[:1].isupper() or x[:1].isdigit()]
    if not good:
        # Every sentence mentions the article. Scrub the reference rather than
        # falling back to publishing it -- "the pick from the section above" is
        # not something a viewer can act on, and scrubbing leaves "the pick",
        # which is true and readable.
        good = [_STRUCT_SUB(x) for x in sents
                if not _SUBORD.match(_STRUCT_SUB(x))]
        good = [x for x in good if x and not _STRUCT.search(x)] or sents

    fits_whole = [x for x in good if fits(x)]
    if fits_whole:
        # Prefer a sentence with a because, a price, or a comparison: that is
        # the part of the block a viewer can act on.
        def weight(t):
            score = 0
            score += 2 if re.search(r'\bbecause\b|\bwhy\b|\bso\b', t, re.I) else 0
            score += 2 if re.search(r'\$\d|\d+\s*reviews?\b', t, re.I) else 0
            score += 1 if re.search(r'\bthan\b|\brather than\b|\bcheapest\b'
                                    r'|\bmost\b|\bonly\b', t, re.I) else 0
            return (-score, -len(t.split()))
        return sorted(fits_whole, key=weight)[0]

    return fit_words(min(good, key=lambda t: len(wrap(t, width))), width, max_lines)


def read_picks(body, lang='en'):
    """The article's buy blocks as data: name, price, review count, why.

    Read from the English section only. The buy blocks are literally the same
    product in all three languages with translated titles, so reading the whole
    file would return each pick three times and put a Spanish name on an
    English card.

    Parsed rather than retyped for the same reason the prices are scraped: if
    the article is re-priced and this reads a stale figure from memory, the
    video and the page disagree and only one of them is right.
    """
    # Anchored to a real top-level heading, not a bare '## '. Markdown '###'
    # subheadings are three hashes, so splitting on '## ' cuts the section at
    # the first '###' in the article -- which is before most buy blocks, and
    # yields zero picks. build.py's split_langs() uses this same pattern.
    marks = list(re.finditer(r'^##[ \t]+(EN|KR|ES)\b[^\n]*$', body, re.M))
    section = ''
    for i, mk in enumerate(marks):
        if mk.group(1) == lang.upper():
            end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
            section = body[mk.end():end]
            break
    if not section:
        return []

    out = []
    for block in re.split(r'<div class="pick">', section)[1:]:
        block = block.split('</div>\n</div>')[0]
        name = re.search(r'<h3>(.+?)</h3>', block, re.S)
        if not name:
            continue
        name = unent(re.sub(r'<[^>]+>', '', name.group(1)))

        # The block's own editorial label -- "Best value", "Best all-round".
        # It is what the article already says about why this part is here, and
        # unlike the fitment parenthetical it names no vehicle.
        label = re.search(r'class="pick-label">\s*(.+?)\s*</div>', block)
        # The article writes &minus; and &mdash; for the true typographic
        # characters. drawtext renders text literally, so an undecoded entity
        # paints "&minus;6mm Offset" across a card. Decoding here rather than
        # where the card is built covers the name, the label and the reason
        # in one place.
        price = re.search(r'class="pick-price">\s*\$([\d,]+(?:\.\d{2})?)',
                          block)
        reviews = re.search(r'(\d[\d,]*)\s*(?:owner\s+)?reviews?', block, re.I)
        # The first <p> after the price is the block's own justification --
        # the sentence that says why this part is the pick. That is the whole
        # editorial value of the block, so it is what the card quotes.
        why = ''
        for p in re.findall(r'<p>(.+?)</p>', block, re.S):
            p = unent(re.sub(r'<[^>]+>', '', p))
            p = re.sub(r'\s+', ' ', p).strip()
            if len(p) > 40:
                why = p
                break

        out.append(dict(
            name=re.sub(r'\s+', ' ', name).strip(),
            label=(unent(re.sub(r'<[^>]+>', '', label.group(1)))
                   .strip().capitalize() if label else ''),
            price=price.group(1).replace(',', '') if price else None,
            reviews=reviews.group(1).replace(',', '') if reviews else '',
            why=why,
        ))
    return out


def card(main, sub=None, kicker=None, seconds=4.0, accent=False, image=None):
    """One full-frame text card as a filtergraph segment plus a video clip.

    Returns a single-clip lavfi input string and its drawtext filters. Caller
    concatenates the clips.

    `image` is a product photograph to show on the card. It is drawn on a white
    plate, because these are retailer cut-outs on white rather than cropped
    scenes, and a cut-out laid straight onto the dark card reads as a product
    floating in a hole.
    """
    return dict(main=main, sub=sub, kicker=kicker, seconds=seconds,
                accent=accent, image=image)


def layout(c, w, h, top):
    """drawtext filters for one card, sized to fit the space below `top`.

    Autosizing has to be driven by the number of lines, not only their width.
    The first version picked a size from the longest line alone, so a headline
    that wrapped to five short lines rendered at full 82px and ran straight
    through the accent rule and off the bottom of the frame. Fitting the tallest
    constraint -- widest line AND total block height together -- is what makes a
    long article title and a two-word price both look deliberate.
    """
    rule_y = top - 100
    y = top
    vf = [f'drawbox=x=(iw-140)/2:y={rule_y}:w=140:h=4:color={ACCENT}:t=fill']
    if c['kicker']:
        vf.append(f"drawtext=fontfile={FONT_BOLD}:text='{esc(c['kicker'])}':"
                  f"fontcolor={ACCENT if c['accent'] else MUTED}:fontsize=38:"
                  f"x=(w-text_w)/2:y={top - 80}")
        y = top + 60

    main_lines = wrap(c['main'], 14)
    # Hard cap on the sub-line. Without it a long reason pushed the block past
    # the bottom of the frame and the autosize loop answered by shrinking the
    # headline to try to save it -- so one wordy sub-line made every other
    # card's headline inconsistent. The card is a glance, not a paragraph.
    sub_lines = wrap(c['sub'], 32)[:4] if c['sub'] else []
    bottom = h - 150

    # Shrink until the whole block fits: the tallest line at this size, the
    # block's total height, and a hard floor so it never becomes unreadable.
    # The sub-line has a fixed size of its own, so it must not drive the
    # headline down. Folding both into one width test rendered "$368" at 52px
    # because the sentence underneath it was longer than the price -- the
    # number a viewer came for came out smaller than the reason for it.
    widest = max((len(l) for l in main_lines), default=0)
    size = 88
    while size > 40:
        block = len(main_lines) * size * 1.2
        if sub_lines:
            block += 40 + len(sub_lines) * 56
        if y + block <= bottom and widest * 0.56 * size <= w - 110:
            break
        size -= 4

    for ln in main_lines:
        vf.append(f"drawtext=fontfile={FONT_BOLD}:text='{esc(ln)}':"
                  f"fontcolor={PAPER}:fontsize={size}:x=(w-text_w)/2:y={y}")
        y += int(size * 1.2)
    if sub_lines:
        y += 40
        for ln in sub_lines:
            vf.append(f"drawtext=fontfile={FONT_REG}:text='{esc(ln)}':"
                      f"fontcolor={MUTED}:fontsize=42:x=(w-text_w)/2:y={y}")
            y += 56
    return vf


def card_png(c, out_png):
    """Render one card to a single still PNG.

    This replaced a single filter_complex that drew all five cards and
    concatenated them in one pass. That graph was fragile in a way that failed
    silently: a card's white plate and product photograph would simply be
    absent from the output while every individual chain rendered correctly in
    isolation, and ffmpeg reported success. Rendering each card separately is a
    few seconds slower and can be inspected frame by frame, which is what
    caught the bug -- and the concat demuxer below needs every input in the same
    pixel format, which was the second half of it.
    """
    has_img = bool(c.get('image'))
    # With a photograph the white plate occupies the upper third and the type
    # starts below it; without one the type is centred higher, because a card
    # that is nothing but a short line at the very bottom looks like a caption
    # someone forgot to finish.
    top = 1180 if has_img else 800
    vf = layout(c, W, H, top)

    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
           '-f', 'lavfi', '-i', f'color=c={INK}:s={W}x{H}:d=1']
    if has_img:
        cmd += ['-i', c['image']]
        # Two inputs: [0:v] is the background, [1:v] the cut-out. The overlay
        # must name a scaled stream, so the scale runs first as its own chain.
        plate = 'drawbox=x=70:y=260:w=940:h=800:color=0xFFFFFF:t=fill,'
        graph = (
            f'[0:v]{plate}' + ','.join(vf) + '[base];'
            f'[1:v]scale=880:740:force_original_aspect_ratio=decrease[sc];'
            f'[base][sc]overlay=x=100:y=290:format=auto[out]')
        cmd += ['-filter_complex', graph, '-map', '[out]']
    else:
        cmd += ['-vf', ','.join(vf)]
    # rgb24, always, even though there is no transparency to lose. The concat
    # demuxer requires its inputs to agree on pixel format, and an overlay on a
    # card with no photograph left the PNG as rgb24 while a card with one left
    # it rgba. The mismatched stream did not error -- it silently dropped the
    # overlay on the cards that had it, which is exactly the bug this rewrite
    # was supposed to end.
    cmd += ['-frames:v', '1', '-pix_fmt', 'rgb24', out_png]
    return cmd


def build_video(cards, out_mp4, total):
    """One ffmpeg call that turns N card stills into a video.

    concat demuxer with an explicit duration per still. Each PNG is held for
    its card's seconds and the whole thing is encoded once, which keeps the
    file small and the frame rate exact.
    """
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False,
                                     encoding='utf-8') as fh:
        listing = fh.name
        for c, png in cards:
            fh.write(f"file '{png}'\nduration {c['seconds']}\n")
        # The demuxer needs the final image repeated or the last card is cut
        # to a single frame.
        fh.write(f"file '{cards[-1][1]}'\n")
    try:
        subprocess.run(
            ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
             '-f', 'concat', '-safe', '0', '-i', listing,
             '-t', str(total), '-r', str(FPS), '-vsync', 'cfr',
             '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
             '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out_mp4],
            check=True)
    finally:
        os.unlink(listing)


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
    vf = layout(c, W2, H2, 800 if not c.get('image') else 900)
    vf.append('format=yuv420p')
    subprocess.run(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
         '-f', 'lavfi', '-i', f'color=c={INK}:s={W2}x{H2}:d=1',
         '-vf', ','.join(vf), '-frames:v', '1', '-q:v', '2', out],
        check=True)
    return out


def owner_quote(slug, limit=210):
    """The shortest sharpest owner quote for this article's picks.

    The caption used to be the article's own lede, which is accurate but is the
    site talking about itself. A real owner's sentence is the one thing on the
    post that a reader cannot get from the product page, and it is the reason
    the guides exist: every quote on the article is verified against the
    harvested review corpus, so a quote pulled from the same place cannot
    contradict the page it points at.

    Low-star reviews win, because a four-or-five-star "great product" is not
    worth reading and a specific complaint is. Ties go to the shorter text --
    a caption is not the place for a 300-word account. If nothing at three stars
    or below survives the filters, there is no quote: a caption hook that reads
    as an advert is worse than a caption with no hook.

    Returns None rather than a placeholder when an article has no corpus. A
    generic "real owner reviews" line would be worse than not having one.
    """
    d = os.path.join(ROOT, 'content', 'reviews', slug)
    if not os.path.isdir(d):
        return None
    # Quotes from other vehicles' listings are real, but leading a caption with
    # "does not fit the 2020 Ford F250" on a page about a Silverado reads as a
    # mistake. Those are ranked last rather than dropped: for an article whose
    # only complaints are cross-vehicle, a cross-vehicle quote still beats no
    # quote.
    OFF_TRUCK = re.compile(r'\b(F-?150|F-?250|F-?350|Ram|Dodge|Jeep|Gladiator|'
                           r'Wrangler|Tundra|Tacoma|Colorado|Canyon|Ranger|'
                           r'Sierra\s*2500|Duramax|Powerstroke|EcoBoost)\b', re.I)
    # Words that describe a part actually going wrong. A quote with none of
    # these is not a failure report, whatever star rating it carries.
    COMPLAINT = re.compile(
        r'\b(fit|fits|fitting|line[sd]? up|leak|leaking|broke|broken|break|'
        r'fail|failed|came apart|noise|noisy|squeak\w*|rattle\w*|dron\w*|'
        r'loud|loose|fell|falling|falls|crack\w*|wrong|missing|bent|'
        r'rust\w*|warp\w*|did not work|doesn.t work|didn.t work|won.t|'
        r'safe mode|check engine|throw\w*)\b', re.I)
    cands = []
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json'):
            continue
        try:
            j = json.load(open(os.path.join(d, f), encoding='utf-8'))
        except (ValueError, OSError):
            continue
        for key in ('low', 'low_same_part_other_truck', 'visible'):
            for r in (j.get(key) or []):
                body = (r.get('body') or '').strip()
                # Truncated corpus entries end in "[...]"; a quote with its
                # last clause missing reads as a mistake in the caption, so
                # those are skipped rather than tidied.
                if '[...]' in body or '...' in body[-6:]:
                    continue
                # A quote that opens or closes mid-sentence reads as a broken
                # paste in a caption, however genuine the words are.
                if body.startswith(('...', '…')) or body.endswith(('...', '…')):
                    continue
                if not (60 <= len(body) <= limit):
                    continue
                stars = r.get('stars') or 5
                # Spelling is left exactly as the owner wrote it, but a quote
                # the caption leads with should not be the one with the most
                # typos in it -- "witch" for "which" is honest and also the
                # first thing a reader would see. Count misspellings as a
                # ranking signal, never as a reason to exclude or correct.
                typos = len(re.findall(r'\b(?:witch|dont|doesnt|cant|wont|'
                                       r'havent|thats|teh|thier)\b', body, re.I))
                off = 1 if OFF_TRUCK.search(body) else 0
                # Weighted so an off-truck quote always ranks below an on-truck
                # one: adding it to typos let a clean F-150 quote beat a typo'd
                # Silverado complaint, which is the wrong order.
                cands.append((stars, len(body), body, off, typos))
    if not cands:
        return None
    # Order: on-truck before off-truck, then stars, then fewest typos, then
    # shortest. Off-truck leads the key rather than following the star count
    # because a 1-star about a different truck is less relevant to this page
    # than a 2-star about this one, and star-first ranking picked the F-150.
    cands.sort(key=lambda c: (c[3], c[0], c[4], c[1]))
    best = cands[0]
    # Require an actual failure. Star count alone is not enough: this corpus
    # contains a two-star that reads "Leveled my 2021 RST perfectly... no change
    # in the ride that I can tell", and a caption leading with that would
    # undercut the guide it is advertising. Applied to every candidate, not just
    # the three-star ones, because the mismatch was at two stars.
    if not COMPLAINT.search(best[2]):
        return None
    return re.sub(r'\s+', ' ', best[2]).strip()


def render(slug, outdir, text_only=False):
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

    # ── The product story ────────────────────────────────────────────────
    # The first version of this short was: title, the lowest price in the
    # article, the highest price, one sentence from the introduction, a URL.
    # On screen that reads as two unexplained dollar figures a few percent
    # apart and no subject -- nothing to watch and nothing to learn, which is
    # why the renders were deleted rather than published.
    #
    # What a parts short can actually say is what the article's own buy block
    # says: one real product, what it costs, and the specific reason it is the
    # pick. Those three facts exist in the article, they are checkable, and
    # they are the thing a viewer came for. Prices are still scraped, never
    # retyped.
    picks = read_picks(body)
    if not picks:
        sys.exit(f'refusing to build: {slug} has no buy block to tell a story about')
    hero = picks[0]
    if not hero['price']:
        sys.exit(f'refusing to build: {slug} pick 1 has no price')

    # The reason is the pick block's own explanation, cut to its first
    # sentence so it fits a card without reflowing into a paragraph.
    reason = pick_reason(hero['why'])

    # Listing names carry a fitment parenthetical: "AIRAID SynthaMax Dry
    # Filter (19-26 2.7L Silverado 1500)" reads as one long unbroken string on
    # a card. It used to move to the sub-line, which put a specific truck on
    # screen and told every other owner the video was not for them -- the guide
    # is about intakes, not about one vehicle. The parenthetical is dropped
    # entirely and the sub-line carries the article's own pick label instead:
    # "Best value - 36 owner reviews" is about the part and applies to anyone.
    short_name = re.sub(r'\s*\([^)]*\)\s*$', '', hero['name']).strip()
    review_line = f"{hero['reviews']} owner reviews" if hero['reviews'] else ''
    price_sub = ' - '.join(x for x in (hero['label'], review_line) if x)

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

    # One product photograph, for the pick the short is actually about. The
    # body photos are not used: those illustrate a component in general, and a
    # short that names a specific part at a specific price has to show that
    # part or it has taught the viewer nothing they can act on.
    hero_img = product_image(PRODUCT_ROOT, slug, 1)
    # The step-up is a different product, so the second product card shows
    # something new rather than repeating the opening shot. Repeating a still
    # on two cards is what made the first cut feel like a slideshow of one
    # image; a viewer reads a repeated frame as "nothing changed".
    upgrade = picks[1] if len(picks) > 1 else None
    upgrade_img = product_image(PRODUCT_ROOT, slug, 2) if upgrade else None

    cards = [
        # Card 1: the subject, with the product itself on screen. A parts video
        # that opens on a title card is asking the viewer to take it on faith.
        card(headline, kicker=kicker, seconds=3.5, image=hero_img),
        # Card 2: the specific pick and what it costs. The fact the viewer
        # came for, and the reason behind it.
        card(short_name, sub=price_sub, kicker='THE PICK', seconds=4.0),
        card(money(hero['price']),
             sub=reason or 'the reason it is the pick is in the guide',
             kicker='WHAT IT COSTS', seconds=5.0),
    ]
    if upgrade:
        up_name = re.sub(r'\s*\([^)]*\)\s*$', '', upgrade['name']).strip()
        # The step-up card is the fourth thing on screen and the viewer already
        # has the hero's full reason behind them. One clause is enough here; a
        # second paragraph at this point reads as the video refusing to end.
        # It also has to survive the sub-line's own width, so the cut is on a
        # word boundary rather than mid-word.
        up_why = pick_reason(upgrade['why'], max_lines=2)
        cards.append(
            card(up_name,
                 # money(), not the raw scraped string: the block writes
                 # "$435.00" and a card that shows cents next to a hero card
                 # showing "$368" looks like two different sources.
                 # Trimmed once, with the price already in the string. Cutting
                 # the reason first and the price-plus-reason second counted the
                 # same words against the line budget twice, which is how an
                 # orphan "open" ended up alone on the last line.
                 sub=fit_words(((money(upgrade['price']) + ' - ')
                                if upgrade['price'] else '') + (up_why or 'the step up'),
                               32, 3),
                 kicker='IF YOU WANT MORE', seconds=4.5, image=upgrade_img))
    cards += [
        # Two lines, because 'carmodreview.com' is one unbreakable word that
        # will not fit at a legible size on one line with the rest of it.
        card('Full guide at\ncarmodreview.com',
             sub=f"all {len(picks)} picks, each priced off its own listing",
             kicker='READ THE REST', seconds=4.0, accent=True),
    ]

    total = sum(c['seconds'] for c in cards)

    # --text-only prints exactly what will appear on screen and stops. Every
    # review of a short before this had to render 21 seconds of video and
    # sample frames to read five lines of text, which is why a card saying the
    # wrong thing was easy to ship and hard to spot.
    if text_only:
        print(f'\n{slug}  ({total:.1f}s)')
        for i, c in enumerate(cards, 1):
            pic = f"  [photo: {os.path.basename(c['image'])}]" if c.get('image') else ''
            print(f'  {i}. [{c["seconds"]:.1f}s] {c["kicker"] or "":<18}{pic}')
            for ln in c['main'].split('\n'):
                print(f'        {ln}')
            if c['sub']:
                for ln in wrap(c['sub'], 32):
                    print(f'        - {ln}')
        return None

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
    # Whole sentences, not a character count. Slicing the lede at 220 chars
    # cut "walks the whole range in" off mid-sentence, and that is the first
    # thing anyone reads in the caption -- it read as a truncated post, not a
    # hook. Two sentences is the right length for a caption anyway.
    _sents = re.split(r'(?<=[.!?])\s+', re.sub(r'\s+', ' ', lede).strip())
    plain_lede = ' '.join(_sents[:2]).strip()
    if len(plain_lede) > 300:
        plain_lede = _sents[0].strip()

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
    # An owner's own sentence, attributed rather than presented as ours. The
    # caption is the only place a reader sees this without clicking through, so
    # it is worth the space; the quote is checked against the same corpus
    # verify_quotes.py uses, so it cannot say something the page does not.
    q = owner_quote(slug)
    quote_block = f'"{q}"\n\n' if q else ''
    caption = (f'{re.sub(r"\s+", " ", title)}\n\n'
               f'{plain_lede}\n\n'
               + (quote_block)
               + f'{source_line}\n\n'
               f'Full guide: {url}\n\n{tags}')
    open(os.path.join(outdir, f'{slug}-caption.txt'), 'w',
         encoding='utf-8').write(caption + '\n')
    open(os.path.join(outdir, f'{slug}-youtube.txt'), 'w',
         encoding='utf-8').write(desc + '\n')
    # Each card is rendered to its own still, then the stills are assembled.
    # See card_png() for why this is not one big filter_complex.
    frames = []
    for i, c in enumerate(cards, 1):
        png = os.path.join(outdir, f'.card-{slug}-{i}.png')
        subprocess.run(card_png(c, png), check=True)
        if not os.path.exists(png) or os.path.getsize(png) < 5000:
            sys.exit(f'refusing to build: card {i} rendered empty')
        frames.append((c, png))
    try:
        build_video(frames, out, total)
    finally:
        for _, png in frames:
            if os.path.exists(png):
                os.unlink(png)
    print(f'wrote {out}  ({total:.0f}s, {W}x{H})')
    cover(slug, cards, outdir)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug', nargs='?',
                    help='one article slug, or omit with --all')
    ap.add_argument('--out', default=os.path.join(ROOT, 'social'))
    ap.add_argument('--all', action='store_true',
                    help='re-render every article that has a buy block')
    ap.add_argument('--text-only', action='store_true',
                    help='print the cards and exit; no ffmpeg, no files')
    a = ap.parse_args()
    if not a.slug and not a.all:
        ap.error('give a slug or --all')

    if a.all:
        # Every article with a buy block, which is every article that should
        # have a short. tonneau-covers-explained has no picks and is skipped
        # with a reason rather than crashing the batch.
        slugs = []
        for f in sorted(os.listdir(os.path.join(ROOT, 'content', 'articles'))):
            if not f.endswith('.md'):
                continue
            body = open(os.path.join(ROOT, 'content', 'articles', f),
                        encoding='utf-8').read()
            slug = re.search(r'^slug:\s*(.+?)\s*$', body, re.M).group(1)
            slugs.append(slug)
    else:
        slugs = [a.slug]

    failed = []
    for slug in slugs:
        try:
            render(slug, os.path.expanduser(a.out), text_only=a.text_only)
        except SystemExit as e:
            failed.append((slug, str(e)))
    if failed:
        print()
        for slug, why in failed:
            print(f'skipped {slug}: {why}')


if __name__ == '__main__':
    main()
