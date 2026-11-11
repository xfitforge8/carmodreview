#!/usr/bin/env python3
"""Recount the low-review analysis behind content/articles/12-what-owners-complain-about.md.

Why this exists.

The first version of that article carried round numbers -- 30 fitment complaints,
19 of them intakes, missing hardware second at 8 -- that could not be reproduced
from the stored corpus by any counting rule. Keyword matching gave 15 fitment
complaints; a looser keyword set gave 37. Neither is 30. Numbers invented to look
precise are worse than no numbers, so the article now quotes this tool.

What the corpus is and how it is counted.

content/reviews/*/*.json holds one file per product listing. Each file carries
three buckets: `visible` (the reviews shown on the listing's first page), `low`
(one- to three-star reviews), and `low_same_part_other_truck` (low reviews from
the sibling listing of the same part for a different vehicle). The same review
appears in several files, because AmericanTrucks lists one part once per vehicle
and pools the ratings, so every count here is deduplicated by review id.

All three buckets are read, not just the two named `low`. A handful of one- to
three-star reviews -- the P0106/P0171 Silverado review among them -- were
captured in `visible` only, and an earlier version of this tool that skipped
that bucket produced an incomplete population and therefore wrong percentages.

The population is then every unique one- to three-star review, which is 117. Of
those, 23 are not truck reviews at all -- AmericanTrucks pools ratings across its
whole catalogue, so low reviews written by Mustang, Wrangler, Outlander and
Mariner owners sit in the same files. A truck buyer's guide cannot use those, so
the table below reports the 94 truck reviews and prints the excluded count rather
than quietly folding them in. The first version of the article did fold them in,
and its percentages were wrong because of it.

Classification is not a keyword guess. /tmp is no place to keep a decision this
important, so the per-review verdicts live in content/reviews/LOW_TRIAGE.json,
one entry per review id, written by reading all 109. `--audit` prints every
review with its verdict so the map can be checked line by line.

Categories, applied to what the reviewer complains about:
  FIT      the part would not physically install -- holes did not line up, wrong
           size or length, the listing claimed a vehicle it does not fit, or it
           needed cutting, welding or an adapter to go on.
  CODES    check engine light, a diagnostic code, or limp/safe mode.
  MISSING  something that should have been in the box was not.
  QUALITY  cracked, bent, leaked, stripped, fell apart, or felt cheap.
  PERF     no gain, or a loss, in power, response or fuel economy.
  SOUND    drone, resonance, too loud or too quiet.
  OTHER    price, wrong item shipped, support, install difficulty, positives.

A review counts once, under the complaint it leads with.

Usage:
    python3 tools/low_review_tally.py           # the table
    python3 tools/low_review_tally.py --audit   # every review and its verdict
"""
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIAGE = os.path.join(ROOT, 'content/reviews/LOW_TRIAGE.json')
CATEGORIES = ('FIT', 'CODES', 'MISSING', 'QUALITY', 'PERF', 'SOUND', 'OTHER')

# AmericanTrucks pools ratings across the whole catalogue, so a file for a
# Silverado part also carries reviews written by car owners. A truck guide has
# no business counting those.
TRUCKS = ('silverado', 'sierra', 'f-150', 'f150', 'f-250', 'f250', 'f-350',
          'ram', 'tundra', 'tacoma', 'colorado', 'ranger', 'canyon', 'titan',
          'gladiator', 'maverick', 'ridgeline', 'frontier')


def is_truck(r):
    hay = ((r.get('vehicle') or '') + ' ' + (r.get('product') or '')).lower()
    return any(t in hay for t in TRUCKS)


def family(product):
    """Which kind of part this is, for the per-part-type breakdown."""
    s = (product or '').lower()
    if 'intake' in s or 'air filter' in s:
        return 'intake'
    if 'exhaust' in s or 'muffler' in s or 'cat-back' in s:
        return 'exhaust'
    if 'leveling' in s or 'lift kit' in s or 'suspension' in s:
        return 'leveling'
    if 'brake' in s or 'rotor' in s or 'pad' in s:
        return 'brake'
    if 'wheel' in s or 'tire' in s or 'tyre' in s:
        return 'wheel/tire'
    if 'tuner' in s or 'pulsar' in s or 'mpvi' in s:
        return 'tuner'
    return 'other'


def reviews():
    """The unique low reviews, in a stable order, from all three buckets."""
    seen, out = {}, []
    for f in sorted(glob.glob(os.path.join(ROOT, 'content/reviews/*/*.json'))):
        d = json.load(open(f))
        for bucket in ('visible', 'low', 'low_same_part_other_truck'):
            for r in (d.get(bucket) or []):
                if str(r.get('stars')) not in ('1', '2', '3'):
                    continue
                # Some records were scraped without an id, and those records are
                # also stored *with* an id elsewhere. Keying on the id alone would
                # count such a review twice, so authorship and text come first
                # and the id is only a fallback for records with no text.
                ident = 'text:%s:%s' % (
                    re.sub(r'\W', '', (r.get('author') or '').lower()),
                    re.sub(r'\W', '', (r.get('body') or '')[:120].lower()))
                if ident == 'text::':
                    ident = 'id:%s' % r.get('id')
                if ident in seen:
                    continue
                seen[ident] = True
                out.append({
                    'id': str(ident),
                    'stars': r.get('stars'),
                    'vehicle': r.get('vehicle') or '',
                    'title': r.get('title') or '',
                    'body': re.sub(r'\s+', ' ', r.get('body') or ''),
                    'product': r.get('product') or '',
                    'family': family(r.get('product')),
                })
    return out


def main():
    audit = '--audit' in sys.argv
    rs = reviews()
    verdicts = json.load(open(TRIAGE))

    missing = [r['id'] for r in rs if r['id'] not in verdicts]
    if missing:
        print('%d review(s) have no verdict in %s:' % (len(missing), TRIAGE))
        for m in missing:
            hit = next(r for r in rs if r['id'] == m)
            print('  %s  %s*  %s :: %s' % (m, hit['stars'], hit['title'][:50],
                                           hit['body'][:90]))
        return 1
    stray = [k for k in verdicts if k not in {r['id'] for r in rs}]
    if stray:
        print('%d verdict(s) name a review that is not in the corpus: %s'
              % (len(stray), ', '.join(stray[:5])))
        return 1

    for r in rs:
        r['verdict'] = verdicts[r['id']]
        if r['verdict'] not in CATEGORIES:
            print('unknown verdict %r on %s' % (r['verdict'], r['id']))
            return 1

    if audit:
        for r in rs:
            print('%-8s %s* %-22.22s %-40.40s %s'
                  % (r['verdict'], r['stars'], r['vehicle'] or '?',
                     r['title'], r['body'][:90]))
        print()

    every = len(rs)
    rs = [r for r in rs if is_truck(r)]
    total = len(rs)
    counts = collections.Counter(r['verdict'] for r in rs)
    print('%d unique one- to three-star reviews across %d listings\n'
          % (total, len({r['product'] for r in rs})))
    print('(%d low reviews in the corpus were excluded as non-truck: Mustang, '
          'Wrangler, Outlander and similar.)\n' % (every - total))
    for cat in CATEGORIES:
        n = counts[cat]
        if n:
            print('  %-8s %3d  %4.1f%%' % (cat, n, 100.0 * n / total))
    print()

    byfam = collections.defaultdict(collections.Counter)
    for r in rs:
        byfam[r['family']][r['verdict']] += 1
    order = sorted(byfam, key=lambda f: -sum(byfam[f].values()))
    print('%-11s %4s %4s %6s %8s %5s %5s %6s'
          % ('family', 'n', 'FIT', 'CODES', 'MISSING', 'PERF', 'QUAL', 'OTHER'))
    for f in order:
        c = byfam[f]
        print('%-11s %4d %4d %6d %8d %5d %5d %6d'
              % (f, sum(c.values()), c['FIT'], c['CODES'], c['MISSING'],
                 c['PERF'], c['QUALITY'], c['OTHER']))
    print()

    fit = counts['FIT']
    print('Fitment: %d of %d, %.0f%%' % (fit, total, 100.0 * fit / total))
    print('Share of fitment complaints by part type:')
    for f in order:
        if byfam[f]['FIT']:
            print('  %-11s %2d of %d' % (f, byfam[f]['FIT'], fit))
    print()
    print('Fitment fewer than all other categories combined? %s'
          % ('no -- %d fitment against %d everything else' % (fit, total - fit)))
    rank = counts.most_common()
    print('Largest category: %s (%d). Second: %s (%d).'
          % (rank[0][0], rank[0][1], rank[1][0], rank[1][1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
