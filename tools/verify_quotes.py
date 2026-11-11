#!/usr/bin/env python3
"""Check that every owner quote in an article was written against the product its card sells.

Why this exists, and why the obvious test is wrong.

AmericanTrucks does not host one review set per SKU. The review page for a
Silverado 1500 wheel also serves reviews that F-150 and Ram owners wrote about
the same casting, the 2.7L intake page serves 5.3L and 6.2L reviews, and so on.
Each review blob does carry a `ProductName` -- the exact listing its author
bought -- which is the only reliable provenance in the scraped data. `web_id` is
not: it records where a review was *first* seen, not every page that carries it.

So "does this quote appear on the page the card links to?" is satisfied by a
quote written about a completely different truck. Checking presence is not
enough; checking provenance is the point. This tool matches each `<em>` quote to
its record in content/reviews/*/*.json and requires that record's `product` to
equal the listing name of the card's own product, fitment parenthetical
included -- `... (19-26 Silverado 1500)` and `... (19-26 RAM 1500)` are not the
same part for this purpose.

It also prints the reviewing owner's `vehicle`, because a quote can be about the
right product and still be presented as evidence about the wrong truck. That is
a prose question this tool cannot settle, so it surfaces it for review rather
than guessing.

Usage:
    python3 tools/verify_quotes.py            # all articles, offline
    python3 tools/verify_quotes.py --strict   # also fail on wrong-vehicle attribution
Exit 1 when a quote is misattributed.
"""
import glob
import html as htmllib
import json
import os
import re
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def key(s):
    """Product names differ only in punctuation/case between the two sources."""
    if '&' in s:
        s = htmllib.unescape(s)
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def families(review):
    """Words that identify whose truck/part a review is really about.

    A quote is fairly attributed when the card's own prose names the thing that
    differs -- the owner's truck ('Ram 1500', 'Tundra') or the other fitment
    ('5.3L', '14-18'). This pulls those words out of the record so the check is
    mechanical rather than a matter of trusting the writer's wording.

    The `vehicle` field is blank on a fair share of records, so the review text
    itself is scanned as well: an owner who writes "my ZR2" has declared his
    truck even when the scraper did not capture it.
    """
    out = set()
    hay = ((review.get('vehicle') or '') + ' ' + (review.get('body') or '') + ' '
           + (review.get('title') or '')).lower()
    for word in ('sierra', 'ram', 'f-150', 'f150', 'tundra', 'tacoma', 'colorado',
                 'ranger', 'silverado', 'f-250', 'f-350', 'jeep', 'gladiator',
                 'bronco', 'expedition', 'zr2', 'trail boss', 'high country',
                 'wrangler', 'mustang', 'challenger', 'canyon', 'titan',
                 'frontier', 'ridgeline', 'maverick', 'outlander', 'mariner'):
        if word in hay:
            out.add(word.replace('-', ''))
    for lit in re.findall(r'\d\.\d\s*l', (review.get('product') or '').lower()):
        out.add(re.sub(r'\s+', '', lit))
    for yrs in re.findall(r'\d{2}-\d{2}', (review.get('product') or '')):
        out.add(yrs)
    return out


def discloses(prose, words):
    """True when the card's own text names at least one of these identifiers."""
    flat = re.sub(r'\s+', '', htmllib.unescape(prose).lower())
    return any(w.replace('-', '') in flat.replace('-', '') for w in words)


def norm(s):
    return htmllib.unescape(s).lower().replace('\\u0027', "'")


def corpus():
    """(listing slug -> card name, [review records]) from the scraped product files."""
    by_slug, records = {}, []
    for f in glob.glob(os.path.join(ROOT, 'content/reviews/*/*.json')):
        d = json.load(open(f))
        slug = os.path.basename(f)[3:-5]
        by_slug[slug] = d.get('name', '')
        for bucket in ('visible', 'low', 'low_same_part_other_truck'):
            for r in (d.get(bucket) or []):
                records.append(r)
    return by_slug, records


def verified_listings():
    """Listings checked live but never scraped: slug -> registry entry.

    These have no review records, so any quote on their cards will still fail as
    not-found -- which is correct. The entry only stops the card being reported
    as unbacked, and only because someone opened the page and read the number.
    """
    path = os.path.join(ROOT, 'content/reviews/VERIFIED_LISTINGS.json')
    if not os.path.exists(path):
        return {}
    d = json.load(open(path))
    return {k: v for k, v in d.items() if not k.startswith('_')}


def find(records, nq):
    """The review record containing this quote, or None."""
    for r in records:
        if nq and nq in key(r.get('body')):
            return r
    return None


def main():
    strict = '--strict' in sys.argv
    by_slug, records = corpus()
    known_live = verified_listings()
    checked = 0
    wrong_product, undisclosed, not_found, unknown_listing = [], [], [], []
    essay_checked, essay_unlabelled = 0, []
    live_checked = 0

    for af in sorted(glob.glob(os.path.join(ROOT, 'content/articles/*.md'))):
        txt = open(af).read()
        for block in re.findall(r'<div class="pick">(.*?)\n</div>', txt, re.S):
            link = re.search(r'class="buy" href="([^"]+)"', block)
            if not link:
                continue
            slug = os.path.basename(urlparse(link.group(1)).path)
            slug = slug[:-5] if slug.endswith('.html') else slug
            card = key(by_slug.get(slug, ''))
            if not card and slug in known_live:
                # Checked live, never scraped: nothing to match quotes against,
                # so the card passes the "does this listing exist" question and
                # any quote on it is still caught below by the not-found test.
                card = key(known_live[slug].get('name', ''))
                live_checked += 1
            if not card:
                unknown_listing.append((os.path.basename(af), slug))
                continue
            prose = re.sub(r'<[^>]+>', ' ', block)
            for q in re.findall(r'<em>(?:&ldquo;|")?(.+?)(?:&rdquo;|")?</em>', block, re.S):
                nq = key(q)
                if len(nq) < 12:
                    continue
                checked += 1
                hit = find(records, nq)
                row = (os.path.basename(af), slug, nq[:66])
                if hit is None:
                    not_found.append(row)
                    continue
                veh = (hit.get('vehicle') or '').lower()
                if key(hit.get('product')) != card:
                    # Wrong fitment is fine only when the card says whose truck
                    # or which other fitment it is. Undisclosed, it is a false
                    # attribution: the quote reads as evidence about this part.
                    if not (discloses(prose, families(hit))):
                        wrong_product.append(
                            row + (hit.get('product', ''), hit.get('vehicle') or '?'))
                elif 'silverado' not in veh and not discloses(prose, families(hit)):
                    undisclosed.append(row + (hit.get('vehicle') or 'not stated',))

        # Essay quotes: <em> blocks that sit outside any product card. These have
        # no card to check fitment against, so the only question is the one that
        # matters for an essay -- does the text say whose truck the quote is
        # about? A quote from a Ram owner presented without saying so reads as
        # evidence about a Silverado, which is exactly the error this tool
        # exists to catch.
        outside = re.sub(r'<div class="pick">.*?\n</div>', '', txt, flags=re.S)
        for m in re.finditer(r'<em>(?:&ldquo;|")?(.+?)(?:&rdquo;|")?</em>', outside, re.S):
            nq = key(m.group(1))
            if len(nq) < 12:
                continue
            hit = find(records, nq)
            if hit is None:
                continue
            essay_checked += 1
            # A quote is fairly presented when the text around it names the
            # truck. Attribution is often written after the quote ("the first of
            # those is an F-250 owner"), so the window runs both ways.
            before = outside[max(0, m.start() - 600):m.start()]
            after = outside[m.end():m.end() + 400]
            said = (' '.join([re.sub(r'<[^>]+>', ' ', before), m.group(1),
                              re.sub(r'<[^>]+>', ' ', after)]))
            if not discloses(said, families(hit)):
                essay_unlabelled.append(
                    (os.path.basename(af), nq[:60], hit.get('vehicle') or 'not stated',
                     re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', before))[-140:]))

    print(f'{checked} quotes checked against the product each card sells\n')
    if essay_checked:
        print(f'{essay_checked} essay quotes checked for a stated vehicle\n')

    if wrong_product:
        print(f'{len(wrong_product)} quote(s) are from another fitment and the card '
              f'does not say so:\n')
        for f, slug, q, prod, veh in wrong_product:
            print(f'  {f}')
            print(f'    card sells : {slug}')
            print(f'    quote      : "{q}"')
            print(f'    written on : {prod}  [{veh}]\n')

    if undisclosed:
        print(f'{len(undisclosed)} quote(s) are from a non-Silverado owner and the card '
              f'does not say so:\n')
        for f, slug, q, veh in undisclosed:
            print(f'  {f}\n    "{q}"\n    owner vehicle: {veh}\n')

    if not_found:
        print(f'{len(not_found)} quote(s) could not be matched to any review record:\n')
        for f, slug, q in not_found:
            print(f'  {f}  "{q}"\n')

    if unknown_listing:
        print(f'{len(unknown_listing)} card(s) link to a listing with no scraped record:')
        for f, slug in unknown_listing:
            print(f'  {f}  {slug}')
        print()

    if essay_unlabelled:
        print(f'{len(essay_unlabelled)} essay quote(s) do not say whose truck they '
              f'came from:\n')
        for f, q, veh, lead in essay_unlabelled:
            print(f'  {f}')
            print(f'    "{q}"')
            print(f'    owner vehicle : {veh}')
            print(f'    introducing   : ...{lead}\n')

    clean = not (wrong_product or not_found or unknown_listing or essay_unlabelled)
    if strict:
        clean = clean and not undisclosed
    if clean:
        print('OK: every quote is either written about the card\'s own product or '
              'labelled with the truck/fitment it came from.')
    return 0 if clean else 1


if __name__ == '__main__':
    sys.exit(main())
