#!/usr/bin/env python3
"""Extract only the reviews that were written against a listing's OWN product.

AmericanTrucks review pages are shared across a wheel/part family: the Silverado
1500 page for a wheel also serves reviews written about the Ram 1500 and F-150
versions of the same wheel, the 2.7L intake page serves the 5.3L and 6.2L ones,
and so on. Each review blob carries a `ProductName`, which is the listing the
reviewer actually bought. Bedded reviews are useless as evidence about a given
truck, so this tool keeps only the ones whose ProductName matches the listing's
own product name (from content/reviews/*/*.json) and drops the rest.

Usage:  python3 tools/onlist_reviews.py <listing-slug> [...]
"""
import glob
import html as htmllib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = '/tmp/cmr-revcache'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')


def key(s):
    """Product names differ only in punctuation and case across the two sources."""
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def listing_names():
    """listing slug -> product name, from the scraped product records."""
    out = {}
    for f in glob.glob(os.path.join(ROOT, 'content/reviews/*/*.json')):
        d = json.load(open(f))
        slug = os.path.basename(f)[3:-5]
        out[slug] = d.get('name', '')
    return out


def fetch(slug):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, slug + '.html')
    if not os.path.exists(path):
        subprocess.run(['curl', '-sL', '-m', '45', '-A', UA,
                        f'https://www.americantrucks.com/reviews/{slug}',
                        '-o', path], check=False)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    return open(path, encoding='utf-8', errors='ignore').read()


def parse(raw):
    """[(author, title, product, body, stars)] in page order.

    Product names contain escaped quotes -- 'Tire (33\\" - 285/70R17)' -- so the
    obvious "(.*?)" stops at the backslash, every name comes back a stub, and
    every review then looks like it belongs to some other fitment. The captures
    below skip over escaped characters instead of stopping at them.
    """
    dec = htmllib.unescape(raw)
    STR = r'"((?:[^"\\]|\\.)*)"'          # a JSON string, escapes respected
    rec = re.compile(r'"ReviewText":' + STR + r',"(?:Rejection|Helpful|ReviewerName)', re.S)
    field = {k: re.compile('"' + k + r'":' + STR)
             for k in ('ReviewerName', 'ReviewTitle', 'ProductName')}
    field['RatingScore'] = re.compile(r'"RatingScore":(\d)')
    out = []
    for m in rec.finditer(dec):
        blob = dec[max(0, m.start() - 3000):m.start()]
        vals = {k: (rx.findall(blob) or [''])[-1] for k, rx in field.items()}
        out.append((vals['ReviewerName'], vals['ReviewTitle'],
                    vals['ProductName'], m.group(1), vals['RatingScore']))
    if out:
        return out
    for m in re.finditer(r'"author": "([^"]*)",\s*"name": "([^"]*)",\s*"description": "(.*?)",'
                         r'\s*"reviewRating": \{\s*"@type": "Rating",\s*"bestRating": "5",'
                         r'\s*"worstRating": "1",\s*"ratingValue": "(\d)"', dec, re.S):
        out.append((m.group(1), m.group(2), '', m.group(3), m.group(4)))
    return out


def clean(s):
    return (s.replace('\\"', '"').replace('\\u0027', "'")
             .replace('\\n', ' ').replace('\\r', ' ').strip())


def main():
    names = listing_names()
    for slug in sys.argv[1:]:
        raw = fetch(slug)
        print('#' * 76)
        print(slug)
        if raw is None:
            print('  FETCH FAILED')
            continue
        want = key(names.get(slug, ''))
        revs = parse(raw)
        own = [r for r in revs if want and key(r[2]) == want]
        other = [r for r in revs if not (want and key(r[2]) == want)]
        print(f'  {len(revs)} on page, {len(own)} written against this product, '
              f'{len(other)} about other fitments\n')
        for a, t, p, b, s in own:
            print(f'  {s}* {clean(t)[:52]}')
            print(f'     {clean(b)[:230]}\n')


if __name__ == '__main__':
    main()
