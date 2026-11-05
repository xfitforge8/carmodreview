#!/usr/bin/env python3
"""Read what owners actually wrote about each product, and keep the complaints.

Why this exists: the buying guides quote a review *count* off each listing --
"$368.00 - 36 reviews" -- and a count is not a review. A guide that says "the
recurring complaint is a coupler that needs trimming" because that is generally
true of cheap intakes, and not because anyone read those 36 reviews, is
inventing authority. The site's own methodology page claims the low-rated
reviews are read specifically. This is the script that makes that true.

Where the data is, which took some finding:

  The rendered widget is not the source. The listing page's `pageModel`
  attribute holds 10 reviews, and the /reviews/ page renders the same 10 from
  the same attribute, so neither pagination nor a query string moves it.

  /ajax/reviews is scoped to one SKU. For a product sold in several
  configurations that returns two or three reviews while the page above it says
  17 -- the count is for the whole product *line*, because the same part is
  listed for the Silverado, the Sierra, the F-150 and the Ranger.

  /ajax/brandreviews with ratingFilter=1|2|3 returns every low review for the
  brand, and each one carries the WebId of the listing it was written against.
  Filtering that by our product's own WebId gives the low reviews that actually
  belong to this part, at any count, without pagination guesswork.

  /ajax/reviews/summary gives the real star distribution and the installation
  time bucket. That is where "94% five stars, 6% four" comes from, and why a
  4.5-star average is worth reading rather than trusting.

What gets stored, per product, in content/reviews/<slug>/<NN>-<SKU>.json:

  listing, name, brand, sku, line_total, line_rating
  distribution   {5: 94.1, 4: 5.9, ...} -- the real percentages
  install        the time bucket owners selected
  lowest         the low reviews belonging to this WebId, verbatim
  others         low reviews in the same line, marked as another vehicle
  themes         {theme: [quotes]} pulled from this product's reviews

`lowest` is the point. A 4.5-star average hides the truck that threw codes and
the one where the MAF harness would not reach. Those are the reviews a buyer
needs and the ones a competitor listicle never quotes.

  python3 fetch_reviews.py                 # everything missing
  python3 fetch_reviews.py --all           # refresh every product
  python3 fetch_reviews.py --article cold-air-intake-guide
  python3 fetch_reviews.py --show cold-air-intake-guide   # print what we have
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

ROOT = os.path.expanduser('~/carmodreview')
PRODUCTS = os.path.join(ROOT, 'content', 'products')
OUT = os.path.join(ROOT, 'content', 'reviews')
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
SITE = 'https://www.americantrucks.com'

# A review at or below this is what a buyer needs to see. Three stars is
# "works, but"; one and two are the failures.
LOW_STARS = (1, 2, 3)


def listing_urls():
    """[(article slug, position, web id)] for every product photograph.

    Reuses urls.json, which already maps each pick block to its own listing, so
    a review can never be attached to the wrong position.
    """
    triples = json.load(open(os.path.join(PRODUCTS, 'urls.json'), encoding='utf-8'))
    out, seen = [], set()
    for slug, pos, url in triples:
        m = re.search(r'/image/([^.]+)\.[A-Za-z0-9_\-]+\.jpg', url)
        if not m or (slug, pos) in seen:
            continue
        seen.add((slug, pos))
        out.append((slug, pos, m.group(1)))
    return out


def curl(url, referer):
    r = subprocess.run(['curl', '-sS', '--max-time', '45',
                        '-H', f'Referer: {referer}',
                        '-H', f'User-Agent: {UA}',
                        '-H', 'Accept: */*', url], capture_output=True)
    return r.stdout


def page_model(web):
    """The server-rendered review state for one listing.

    The attribute is `pageModel="..."` with every internal quote HTML-escaped,
    so it is scanned to the closing quote and unescaped rather than matched
    with a lazy regex -- the JSON contains escaped quotes of its own and a lazy
    match stops at the first one.
    """
    ref = f'{SITE}/reviews/{web}'
    body = curl(ref, SITE + '/').decode('utf-8', 'replace')
    key = 'pageModel="'
    if key not in body:
        raise ValueError('no pageModel on the page')
    i = body.index(key) + len(key)
    j = i
    while body[j] != '"':
        j += 1
    return json.loads(html.unescape(body[i:j])), ref


def ajax(path, referer, **params):
    """One ajax GET, as a dict.

    The endpoint answers `null` -- a valid JSON document, four bytes -- when it
    has nothing to say, and json.loads turns that into None. Returning it as-is
    put a None where every caller expects a dict, and a 30-product run died
    three quarters of the way through on `None.get`. An empty dict is the honest
    reading of "no rows", so that is what comes back.

    One retry, because a run this long should not lose four minutes of finished
    work to a single dropped connection -- and because the failure is loud if it
    really is a refusal rather than a blip.
    """
    url = f'{SITE}/ajax/{path}?' + urllib.parse.urlencode(params)
    last = None
    for attempt in (1, 2):
        raw = curl(url, referer)
        try:
            d = json.loads(raw)
        except ValueError:
            last = ValueError(f'ajax {path} returned no json ({len(raw)}b)')
        else:
            return d if isinstance(d, dict) else {}
        if attempt == 1:
            time.sleep(2)
    raise last


def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(str(s or ''))).strip()


def slim(r):
    """One review, reduced to the fields a guide can cite."""
    return {
        'id': r.get('Id'),
        'stars': r.get('RatingScore'),
        'date': (r.get('SubmissionTime') or '')[:10],
        'author': clean(r.get('CustomerUsername') or r.get('DisplayName')),
        'title': clean(r.get('ReviewTitle')),
        'body': clean(r.get('ReviewText')),
        'sku': r.get('Sku'),
        'web_id': r.get('WebId'),
        'product': clean(r.get('ProductName')),
        'helpful': r.get('HelpfulScore'),
        'vehicle': vehicle(r.get('Vehicle')),
        'install': install_bucket(r),
    }


def vehicle(v):
    """The truck a review was written against, as the reviewer entered it.

    Not used to filter -- the WebId does that -- but stored, because a review
    written on a Sierra about a part listed for the Silverado is still the same
    part, and a guide that cites it should be able to say so.
    """
    if not isinstance(v, dict):
        return ''
    bits = [v.get('Year'), v.get('Make'), v.get('Model'), v.get('Submodel')]
    return ' '.join(str(b) for b in bits if b).strip()


def install_bucket(r):
    for a in r.get('SecondaryAnswers') or []:
        if 'nstall' in str(a.get('DisplayLabel', '')):
            return clean(a.get('AnswerValue'))
    return ''


def line_key(name):
    """A coarse identity for "the same part, listed for other trucks".

    The same intake is listed once per vehicle, so its reviews are split across
    listing ids and the useful set is the union. But matching on the brand is
    wrong in the other direction: Hawk Performance also makes Mustang pads, and
    a 1-star "these squeal on my Mustang GT" is not evidence about Silverado
    pads. So the match is on the product name with the vehicle parenthetical and
    the punctuation removed -- "S&B Cold Air Intake with Dry Extendable Filter"
    matches across trucks, "Hawk Performance LTS Brake Pads" does not match
    "Hawk Performance HPS 5.0 Brake Pads".
    """
    n = re.sub(r'\([^)]*\)', '', name or '')
    n = re.sub(r'[^a-z0-9 ]+', ' ', n.lower())
    return re.sub(r'\s+', ' ', n).strip()


def low_reviews(model, referer, web):
    """Every 1-3 star review for this brand, split three ways.

    Brand-wide with a rating filter, because the per-SKU endpoint returns two
    reviews for a part with seventeen and the per-listing model returns ten at
    any offset. Each review names the listing it belongs to, so the split is
    exact rather than inferred -- but "not this listing" is not the same as
    "this product", so that middle group is only kept when its review carries
    the product's own name. A sister SKU in the same family keeps its review; a
    different Hawk pad for a Mustang does not.
    """
    ours, family, brand = {}, {}, {}
    key = line_key(model.get('productName'))
    for star in LOW_STARS:
        frm = 0
        while True:
            d = ajax('brandreviews', referer,
                     webid=web, pgid=model.get('pgid'), vt='Silverado 1500',
                     **{'from': frm}, lrk=model.get('lineReviewKey'),
                     brk=model.get('brandReviewKey'),
                     ratingFilter=str(star), sort='Relevance')
            got = d.get('Reviews') or []
            for r in got:
                if r.get('WebId') == web:
                    ours[r['Id']] = r
                elif line_key(r.get('ProductName')) == key:
                    family[r['Id']] = r
                else:
                    brand[r['Id']] = r
            if len(got) < 10:
                break
            frm += 10
            if frm > 400:
                break
            time.sleep(0.4)
        time.sleep(0.4)
    return ours, family, brand


# Phrases that signal a real problem rather than a preference. Matching these
# is how a guide can say "owners report X" and mean it.
SIGNALS = {
    'fitment': r'\bfit\b|\bfits\b|\bfitment\b|did ?n[o\']t fit|bolt pattern',
    'harness': r'harness|wiring|pigtail|connector|plug',
    'codes': r'\bcode[sd]?\b|check engine|cel\b|trouble light|\bp0171|\bp0101',
    'install': r'install|hardware|dremel|trim|drill|bolt(ed)? on',
    'quality': r'quality|finish|cheap(ly)?|flimsy|rust|corrosion|paint',
    'noise': r'\bdrone|\bnoise|\brattle|\bwhistle|\bhowl',
    'mpg': r'\bmpg\b|gas mileage|fuel mileage|fuel economy',
    'price': r'price|expensive|worth it|value|overpriced',
    'shipping': r'ship|delivery|arrived|packaging|box',
    'service': r'warrant|support|customer service|return|refund',
}


def themes(reviews):
    """{theme: [quotes]}, split into complaints and praise.

    The split matters more than the matching. A 5-star review saying "fit and
    works amazing" matches the fitment pattern, and filed under a heading called
    "fitment" it reads to any buyer as a fitment problem -- the opposite of what
    the owner wrote. Every quote is therefore tagged, and a guide should only
    ever cite the complaints as complaints.

    Quotes, not summaries. A guide that paraphrases becomes unfalsifiable; one
    that quotes a specific owner on a specific date does not.
    """
    out = {}
    for name, pat in SIGNALS.items():
        rx = re.compile(pat, re.I)
        hits = [r for r in reviews if rx.search(f"{r['title']} {r['body']}")]
        if not hits:
            continue
        def q(r):
            return {'stars': r['stars'], 'date': r['date'],
                    'quote': (r['title'] + ': ' + r['body'])[:300]}
        complaints = sorted((r for r in hits if (r['stars'] or 5) <= 3),
                            key=lambda r: (r['stars'] or 9))
        praise = sorted((r for r in hits if (r['stars'] or 5) > 3),
                        key=lambda r: -(r['stars'] or 0))
        entry = {}
        if complaints:
            entry['complaints'] = [q(r) for r in complaints[:4]]
        if praise:
            entry['praise'] = [q(r) for r in praise[:2]]
        if entry:
            out[name] = entry
    return out


def harvest(web):
    model, referer = page_model(web)
    summ = ajax('reviews/summary', referer, webId=web,
                lrk=model.get('lineReviewKey') or '')

    # The reviews already on the page, plus whatever the SKU-scoped endpoint
    # adds. Deduped by id, because the two overlap.
    visible = {}
    for r in model.get('reviews') or []:
        visible[r['Id']] = r
    frm = 0
    while True:
        d = ajax('reviews', referer, webid=web, pgid=model.get('pgid'),
                 vt='Silverado 1500', **{'from': frm}, sort='Relevance',
                 ratingFilter='0', lrk=model.get('lineReviewKey') or '')
        got = d.get('Reviews') or []
        for r in got:
            visible[r['Id']] = r
        if len(got) < 10 or frm > 40:
            break
        frm += 10
        time.sleep(0.4)

    ours, family, brand = low_reviews(model, referer, web)

    mine = [slim(r) for r in visible.values()]
    mine.sort(key=lambda r: r['date'], reverse=True)
    low_mine = sorted((slim(r) for r in ours.values()),
                      key=lambda r: (r['stars'], r['date']))

    # The keys are spelled out -- PercentFiveStars, not Percent5Stars -- and a
    # star level nobody chose comes back as null rather than 0.0, so an absent
    # level is dropped instead of being recorded as "zero people said this".
    dist = {}
    for k, word in ((5, 'Five'), (4, 'Four'), (3, 'Three'), (2, 'Two'), (1, 'One')):
        v = summ.get(f'Percent{word}Stars')
        if v is not None:
            dist[k] = round(float(v), 1)

    return {
        'listing': f'{SITE}/{web}.html',
        'reviews_page': referer,
        'name': clean(model.get('productName')),
        'brand': clean(model.get('brandName')),
        'sku': model.get('productSku'),
        'line_total': model.get('reviewTotalCount'),
        'line_rating': model.get('reviewAverage'),
        'rating_count': summ.get('TotalRatings'),
        'rating_average': summ.get('AverageRating'),
        'distribution': dist,
        'install': clean(summ.get('InstallationTime')),
        'attributes': {a['Key']: a['Value'] for a in
                       (summ.get('SecondaryRatingsViewModel') or [])
                       if isinstance(a.get('Value'), (int, float)) and a['Value'] > 0},
        'visible': mine,
        'low': low_mine,
        'low_same_part_other_truck': [
            {k: v for k, v in slim(r).items() if k in
             ('stars', 'date', 'title', 'body', 'author', 'vehicle', 'product')}
            for r in sorted(family.values(),
                            key=lambda r: (r.get('RatingScore') or 9))[:12]],
        'themes': themes(low_mine or [slim(r) for r in visible.values()]),
        'fetched': time.strftime('%Y-%m-%d'),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--article')
    ap.add_argument('--all', action='store_true', help='refetch everything')
    ap.add_argument('--show', help='print what is stored for one article slug')
    a = ap.parse_args()

    if a.show:
        d = os.path.join(OUT, a.show)
        if not os.path.isdir(d):
            raise SystemExit(f'nothing stored under {d}')
        for f in sorted(os.listdir(d)):
            r = json.load(open(os.path.join(d, f), encoding='utf-8'))
            print(f"\n{r['brand']} {r['name'][:70]}")
            print(f"  {r['rating_average']} from {r['rating_count']} ratings "
                  f"| distribution {r['distribution']} | install {r['install'] or '-'}")
            for t, qs in (r.get('themes') or {}).items():
                if not qs.get('complaints'):
                    continue
                print(f'  {t}:')
                for q in qs['complaints'][:2]:
                    print(f"    {q['stars']}* {q['date']} {q['quote'][:150]}")
        return 0

    saved = skipped = 0
    failed = []
    for slug, pos, web in listing_urls():
        if a.article and slug != a.article:
            continue
        dest = os.path.join(OUT, slug, f'{pos:02d}-{web}.json')
        if os.path.exists(dest) and not a.all:
            skipped += 1
            continue
        try:
            rec = harvest(web)
        except (ValueError, OSError) as e:
            failed.append((slug, pos, str(e)))
            continue
        if not rec['rating_count']:
            failed.append((slug, pos, 'no ratings on the summary endpoint'))
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'w', encoding='utf-8') as f:
            json.dump(rec, f, indent=1, ensure_ascii=False)
        saved += 1
        print(f'  {slug} #{pos}: {rec["rating_average"]} from '
              f'{rec["rating_count"]} ratings, {len(rec["low"])} low on this '
              f'listing, {len(rec["low_same_part_other_truck"])} low same part elsewhere')
        time.sleep(0.8)

    print(f'\nsaved {saved}  already had {skipped}  failed {len(failed)}')
    for f in failed:
        print(f'  FAILED {f}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
