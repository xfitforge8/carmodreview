#!/usr/bin/env python3
"""Install-time statistics for the listing-badge article.

Every number the article prints comes from here. The decisions are written out
one review at a time rather than inferred by regex, because a regex version kept
getting them wrong in ways that would have printed false numbers:

  - it read "4 1/2 hrs" as 2 hours;
  - it read "less than 5 minutes to program" as an install time;
  - it counted a tyre shop's mount-and-balance time as an owner's install;
  - it counted a hypothetical ("could bang it out in 4 hours") as a real one;
  - it matched on author name alone, so one reviewer's second review was
    counted twice.

Each decision below therefore names the author AND a phrase from the review, so
a second review by the same person cannot inherit the first one's number. Every
review that states a time in any form is listed -- either with the minutes it
contributes or with the reason it does not.

Run: python3 install_time_stats.py
"""

import collections
import glob
import json
import re
import statistics

# (product-name prefix, author, phrase in body) -> (minutes, note)
# minutes of None means: read, states a time, deliberately not counted.
DECISIONS = [
    # ---- listings badged "Afternoon" -------------------------------------
    ('Mammoth 3-Inch', 'OrangePekoe', '6 hours a day',
     (None, 'a weekend at 6 hrs/day -- no single stated total')),
    ('Mammoth 3-Inch', 'CCAuthor', '30 minutes or less',
     (None, 'rear blocks only, a partial job')),
    ('Mammoth 3-Inch', 'VincentMarch', 'could definitely bang it out',
     (None, 'hypothetical, not a reported install')),
    ('Mammoth 3-Inch', 'Rusch', 'The 1st shock took me 2.5 hrs',
     (None, 'three partial times, no whole-job figure')),
    ('Mammoth 3-Inch', 'Aaronmatas75', '2 1/2 hours for the front',
     (202.5, '45-60 min rear + 2.5 hrs front = about 3.4 hrs')),
    ('Mammoth 3-Inch', 'Colt53', 'Took about 2 hours',
     (120, 'about 2 hours by himself')),
    ('Mammoth 3-Inch', 'Alyssa', 'about 3-4 hours',
     (210, '3-4 hours, midpoint')),
    ('Mammoth 3-Inch', 'jdj1911', '2 to 2.5 hours',
     (135, '2 to 2.5 hours, midpoint')),

    ('ReadyLIFT 1.75', 'David', 'little over 4 hours',
     (240, 'a little over 4 hours, with his son')),
    ('ReadyLIFT 1.75', 'RobertH67', 'about 3.5 hours',
     (210, 'about 3.5 hours without power or air tools')),
    ('ReadyLIFT 1.75', 'LoganR', 'Took 2-3 hours',
     (150, '2-3 hours, midpoint')),
    ('ReadyLIFT 1.75', 'DavidAllenS', 'about 4 hours',
     (240, 'about 4 hours with friends')),
    ('ReadyLIFT 1.75', '(anon)', 'Installed everything in about 2.5 hours',
     (150, 'about 2.5 hours')),
    ('ReadyLIFT 1.75', '(anon)', 'only on the rack 15-20 minutes',
     (None, 'that is the alignment, not the install')),

    ('Supreme Suspensions', 'Grouch', 'about 4 hours',
     (240, 'about 4 hours on jack stands')),
    ('Supreme Suspensions', 'JesseKell', 'about an hour',
     (60, 'about an hour, by himself')),
    ('Supreme Suspensions', 'Steves2022', 'One hour install both sides',
     (60, 'one hour, both sides')),
    ('Supreme Suspensions', 'BrittN', 'maybe 90 minutes total',
     (90, '90 minutes total')),
    ('Supreme Suspensions', 'levelingIT', 'about 45min in total',
     (45, 'about 45 min in total')),
    ('Supreme Suspensions', 'QDMAX', '(2hrs)',
     (120, '2 hrs')),
    ('Supreme Suspensions', 'Slegs', 'only took me 40 minutes',
     (40, '40 minutes')),

    # ---- listings badged "Less than 1 Hour" ------------------------------
    ('S&B Cold Air Intake with Dry Extendable Filter (19-26 2.7L', 'Bobknight',
     'in under an hour', (60, 'under an hour, stated as a bound')),
    ('S&B Cold Air Intake with Dry Extendable Filter (19-26 2.7L', 'Los505',
     '4 1/2 hrs', (270, '4.5 hrs, watched the video first')),
    ('S&B Cold Air Intake with Dry Extendable Filter (19-26 2.7L', 'JuanR',
     'about an hour', (60, 'about an hour')),
    ('S&B Cold Air Intake with Dry Extendable Filter (20-26 3.0L', 'TedT',
     'about 4', (270, '4-5 hours, midpoint, 3.0L Duramax')),
    ('S&B Cold Air Intake with Dry Extendable Filter (20-26 3.0L', 'AlecFairchild',
     'much longer than an hour', (60, "not much longer than an hour")),

    ('AFE Momentum GT', 'Branden', 'less than an hour',
     (60, 'less than an hour, stated as a bound')),
    ('AFE Momentum GT', 'Dbennett1188', 'About 45 minutes',
     (45, 'about 45 minutes all together')),
    ('AFE Momentum GT', 'CurtsTurbo', 'It took me 2hrs',
     (120, 'his own install took 2 hrs')),
    ('AFE Momentum GT', 'Tbush', 'only took me 30min',
     (30, '30 min')),
    ('AFE Momentum GT', 'Adamaleski', 'a few hrs',
     (None, 'vague: "only took a few hrs"')),

    ('Airaid', 'Whitehorse', 'less than an hour',
     (60, 'less than an hour, stated as a bound')),
    ('Airaid', 'RobertD', '2.5 hours to install',
     (150, '2.5 hours on a Saturday')),

    ('Corsa', 'Kolby', 'could be done in 1 hr',
     (None, 'hypothetical: "if this is the only item"')),
    ('Corsa', 'Joshua', 'about 30 mins',
     (30, 'about 30 mins')),
    ('Corsa', 'quietguy47', 'maybe 20 minutes',
     (20, 'maybe 20 minutes')),

    ('Edge Pulsar', 'Onehandyman', 'less than 5 minutes',
     (None, 'programming time, not install time')),
    ('Edge Pulsar', '(anon)', 'in roughly 10min',
     (10, 'roughly 10 min install and setup')),
    ('Edge Pulsar', 'GeorgeLC', '10 minutes tops',
     (20, '10 min install + 10 min programming')),
    ('Edge Pulsar', 'CowboyMike', 'It took me 25 minutes',
     (25, '25 minutes')),
    ('Edge Pulsar', 'EJA', 'under 30 min',
     (30, 'under 30 min')),
    ('Edge Pulsar', 'Johnr', 'about 20 minutes',
     (20, 'about 20 minutes')),
    ('Edge Pulsar', 'Bigbronx', '30 minutes to install',
     (30, '30 minutes')),

    ('K&N Drop-In', 'SamV', 'no more than 30 min',
     (30, 'no more than 30 min')),

    ('Mammoth Vex', 'Cameron Drake', '20 minutes to mount and balance',
     (None, 'a tyre shop mounted and balanced them, not the owner')),

    ('RedRock', 'BentleyKyle', 'a couple of hours',
     (None, 'vague: "a couple of hours"')),
    ('RedRock', 'Crcboom', '1hr or less',
     (60, '1 hr or less')),

    ('Single Exhaust', 'Kas', 'half an hour to install after removing',
     (None, 'excludes removing the old system, done with a sawzall')),
    ('Single Exhaust', 'Slippery', '30 minutes to disassemble',
     (30, '30 min to remove the old and fit the new')),

    # ---- badged "Shop Install": a mechanic did it ------------------------
    ('ReadyLIFT 1.50', 'Jake369', 'installed by a mechanic',
     (None, 'a mechanic installed it, so not an owner time')),
]


def load_listings():
    """One record per unique listing, deduplicated by listing URL.

    Some listings were fetched twice under different guide folders. The copy
    with more visible reviews is kept, so the review sets never overlap.
    """
    by_listing = collections.defaultdict(list)
    for path in glob.glob('content/reviews/*/*.json'):
        with open(path) as fh:
            by_listing[json.load(fh)['listing']].append(json.load(open(path)))

    listings = []
    for url, copies in by_listing.items():
        data = max(copies, key=lambda d: len(d.get('visible') or []))
        listings.append({
            'name': data['name'],
            'install': data.get('install') or '',
            'rating_count': data.get('rating_count'),
            'reviews': [(re.sub(r'\s+', ' ', r.get('body') or ''),
                         r.get('author') or '(anon)')
                        for r in (data.get('visible') or [])],
        })
    listings.sort(key=lambda d: d['name'])
    return listings


def decide(product, author, body):
    """(minutes, note) for one review. minutes is None if not counted."""
    for name, who, phrase, (minutes, note) in DECISIONS:
        if product.startswith(name) and who == author and phrase in body:
            return minutes, note
    return None, None   # states no time at all


def main():
    listings = load_listings()
    total = sum(len(l['reviews']) for l in listings)
    buckets = collections.Counter(l['install'] or '(none)' for l in listings)

    counted, excluded, unmatched = [], [], []
    used = set()
    for listing in listings:
        for body, author in listing['reviews']:
            minutes, note = decide(listing['name'], author, body)
            if minutes is not None:
                counted.append((listing['install'], minutes, author, note))
                used.add((listing['name'], author, note))
            elif note is not None:
                excluded.append((listing['install'], author, listing['name'], note))
                used.add((listing['name'], author, note))
            elif re.search(r'\d+\s*(hours?|hrs?|minutes?|mins?)|an hour|half an hour',
                           body, re.I):
                unmatched.append((author, listing['name'], body))

    print(f'listings: {len(listings)}')
    print(f'visible reviews: {total}')
    print(f'install-time buckets: {dict(buckets)}')
    print(f'stated a time in any form: {len(counted) + len(excluded)}')
    print(f'  counted: {len(counted)}')
    print(f'  read and not countable: {len(excluded)}')
    print(f'  duration-like text with no decision: {len(unmatched)}')
    for author, name, body in unmatched:
        print(f'    !! {author:<14} {name[:40]:<40} {body[:90]}')
    print()

    for bucket in ('Less than 1 Hour', 'Afternoon', 'Shop Install'):
        rows = sorted(r for r in counted if r[0] == bucket)
        if not rows:
            continue
        values = [r[1] for r in rows]
        print(f'== {bucket}: n={len(values)} median={statistics.median(values):g} '
              f'range={min(values):g}-{max(values):g}')
        for _, minutes, author, note in rows:
            print(f'   {minutes:>6.1f}  {author:<14} {note}')
        print()

    lt = sorted(r[1] for r in counted if r[0] == 'Less than 1 Hour')
    af = sorted(r[1] for r in counted if r[0] == 'Afternoon')
    print(f'Less than 1 Hour, >= 120 min: {sum(1 for v in lt if v >= 120)} of {len(lt)}')
    print(f'Afternoon, <= 90 min: {sum(1 for v in af if v <= 90)} of {len(af)}')

    print()
    print('Read and not counted:')
    for bucket, author, name, note in sorted(excluded):
        print(f'   {author:<14} {name[:44]:<44} {note}')


if __name__ == '__main__':
    main()
