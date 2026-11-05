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


def inject_product_photos(body_html, slug, rel, product_root):
    """Add a photograph to the top of every pick block that has one.

    Returns the html unchanged when there are no product images for this slug,
    so an article can ship before its photos are fetched.

    Only English gets them. The pick blocks on the KR and ES pages are
    translated titles over the same listings, and a photograph has no language
    -- but the alt text does, and the sidecar's is English. Emitting an English
    alt on a Spanish page is the kind of detail a screen-reader user notices.
    """
    shots = _shots(product_root, slug)
    if not shots:
        return body_html

    parts = body_html.split(_BLOCK)
    if len(parts) == 1:
        return body_html

    rebuilt = [parts[0]]
    for i, block in enumerate(parts[1:], 1):
        img = shots.get(i)
        if not img:
            rebuilt.append(_BLOCK + block)
            continue
        size = photos._dimensions(photos._published_path(img))
        dims = f' width="{size[0]}" height="{size[1]}"' if size else ''
        alt = _alt_for(img, _name_in(block))
        fig = (
            f'{_BLOCK}\n'
            f'  <div class="pick-photo">\n'
            f'    <img src="{rel}img/products/{slug}/{os.path.basename(img)}" '
            f'alt="{html.escape(alt)}" loading="lazy" decoding="async"{dims}>\n'
            f'  </div>'
        )
        rebuilt.append(fig + block)
    return ''.join(rebuilt)


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
