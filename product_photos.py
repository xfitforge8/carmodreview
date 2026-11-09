"""Product photographs, placed inside the product block they belong to.

This is deliberately separate from photos.py. That module's photographs
illustrate a component and are distributed through an article body one per
section. These are the opposite: one image, tied to one exact listing, placed
inside that listing's own block. Merging the two would mean either a body photo
could land in the middle of a buy box, or a product shot could be captioned as
if it illustrated a paragraph.

The rule this module exists to keep: the photograph next to a price is a
photograph of that product. A buying guide that recommends one specific part
and shows a stock picture of something else is the thing that makes a page look
manufactured, and it is also simply wrong -- a reader who buys off that image
gets a different part.

Images are keyed by position in the article's pick blocks: NN-<sku>.webp beside
NN-<sku>.txt, fetched by fetch_products.py. Position rather than product name,
because the names carry translated punctuation that would make an unreadable
filename, and the sidecar records the name and listing URL anyway.

Some articles write their buy links as bare paragraphs rather than pick blocks,
and one repeats the same four products across sixteen links. Position cannot key
those, so a second convention exists beside it: sku-<sku>.webp, matched to the
sku in each buy link's URL, injected once per distinct product rather than once
per link. The position pass runs first; the sku pass only fills links the first
one did not cover.
"""
import html
import os
import re

import photos

IMG_EXT = ('.jpg', '.jpeg', '.png', '.webp', '.avif')

# The pick block as the article writes it. Matched leniently on the opening
# tag, then split, so a block gains a photo without the article source having
# to mention images at all.
_BLOCK = '<div class="pick">'


def _shots(product_root, slug):
    """{position: image path} for one article."""
    d = os.path.join(product_root, slug)
    if not os.path.isdir(d):
        return {}
    out = {}
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith(IMG_EXT):
            continue
        m = re.match(r'^(\d+)-', f)
        if m:
            out[int(m.group(1))] = os.path.join(d, f)
    return out


def _alt_for(path, fallback):
    """Alt text from the sidecar's first line, which is the product name."""
    txt = os.path.splitext(path)[0] + '.txt'
    if os.path.exists(txt):
        first = open(txt, encoding='utf-8').readline().strip()
        if first:
            return first
    return fallback


def _name_in(block):
    """The product name already written in this block, for alt fallback."""
    m = re.search(r'<h3>(.+?)</h3>', block, re.S)
    if not m:
        return 'Product photograph'
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip()


def _sku_shots(product_root, slug):
    """{sku (lowercase): image path} for one article, from sku-<sku>.webp files."""
    d = os.path.join(product_root, slug)
    if not os.path.isdir(d):
        return {}
    out = {}
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith(IMG_EXT):
            continue
        m = re.match(r'^sku-(.+)\.\w+$', f, re.I)
        if m:
            out[m.group(1).lower()] = os.path.join(d, f)
    return out


def _match_sku(href, known):
    """Which of `known` a buy URL names, or None.

    Listing skus are not one shape -- s112594, z30481, 75-5138d, 31-10292,
    29532red -- so rather than encode every retailer's convention, the URL's
    last path segment is split on hyphens and its suffixes are tried longest
    first against the skus we actually hold a photograph for. A URL naming a
    part we have no photo of matches nothing and is left alone.

    Amazon carries an ASIN in /dp/ instead, which is not a part number; it is
    tried whole and against its first five characters.
    """
    m = re.search(r'/dp/([A-Za-z0-9]{10})', href)
    if m:
        asin = m.group(1).lower()
        return asin if asin in known else None

    # The sku can sit anywhere in the segment, not only at the end:
    # …-tonneau-cover-s112141-silverado1500.html names its bed length after it.
    tail = re.sub(r'\.html?$', '', href.split('?')[0].rstrip('/').rsplit('/', 1)[-1],
                  flags=re.I).lower()
    hits = [sku for sku in known
            if re.search(r'(?:^|-)' + re.escape(sku) + r'(?:-|$)', tail)]
    return max(hits, key=len) if hits else None


def _figure(img, slug, rel, fallback, cls):
    size = photos._dimensions(photos._published_path(img))
    dims = f' width="{size[0]}" height="{size[1]}"' if size else ''
    alt = _alt_for(img, fallback)
    return (
        f'<div class="{cls}">\n'
        f'    <img src="{rel}img/products/{slug}/{os.path.basename(img)}" '
        f'alt="{html.escape(alt)}" loading="lazy" decoding="async"{dims}>\n'
        f'  </div>')


def _inject_by_sku(body_html, slug, rel, product_root, used):
    """Add a photo to buy links the position pass did not cover.

    One photo per distinct product, not per link: an article that recommends
    the same tonneau cover in four sections should show it once, in the first
    place it is recommended, or the page turns into a wall of the same picture.
    """
    shots = _sku_shots(product_root, slug)
    if not shots:
        return body_html
    seen = set(used)

    def repl(m):
        whole, href, label = m.group(0), m.group(2), m.group(3)
        sku = _match_sku(href, shots)
        if not sku or sku in seen:
            return whole
        seen.add(sku)
        name = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', label)).strip()
        name = re.sub(r'\s*→$', '', name) or 'Product photograph'
        fig = _figure(shots[sku], slug, rel, name, 'pick-photo pick-photo-wide')
        return fig + '\n' + whole

    # The whole <p class="buyrow"> line, so the figure sits above the button.
    return re.sub(
        r'(<p class="buyrow">\s*)<a class="buy" href="([^"]+)"[^>]*>(.*?)</a>',
        repl, body_html, flags=re.S)


def inject_product_photos(body_html, slug, rel, product_root):
    """Add a photograph to every pick block that has one, then to stray buy links.

    Returns the html unchanged when there are no product images for this slug,
    so an article can ship before its photos are fetched.

    Only English gets them. The pick blocks on the KR and ES pages are
    translated titles over the same listings, and a photograph has no language
    -- but the alt text does, and the sidecar's is English. Emitting an English
    alt on a Spanish page is the kind of detail a screen-reader user notices.
    """
    shots = _shots(product_root, slug)

    parts = body_html.split(_BLOCK)
    used = set()
    if len(parts) > 1:
        rebuilt = [parts[0]]
        for i, block in enumerate(parts[1:], 1):
            img = shots.get(i)
            if not img:
                rebuilt.append(_BLOCK + block)
                continue
            used.add(os.path.basename(img))
            rebuilt.append(f'{_BLOCK}\n  ' + _figure(img, slug, rel,
                            _name_in(block), 'pick-photo') + '\n' + block)
        body_html = ''.join(rebuilt)

    return _inject_by_sku(body_html, slug, rel, product_root, used)


def publish(product_root, out_root):
    """Copy product images into the build. Sidecars stay out, as with photos."""
    if not os.path.isdir(product_root):
        return 0
    n = 0
    for dirpath, _, files in os.walk(product_root):
        for f in files:
            if not f.lower().endswith(IMG_EXT):
                continue
            src = os.path.join(dirpath, f)
            relp = os.path.relpath(src, product_root)
            photos.publish_image(src, os.path.join(out_root, relp))
            n += 1
    return n
