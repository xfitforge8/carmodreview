"""Vehicle-type taxonomy.

The site files every guide under a category -- Engine, Exhaust, Suspension --
which answers "what part" and not "what car". That was fine while every guide
was about a Silverado, but the catalog now reaches a Golf GTI, an Audi cabin
and a Bentley screen, and a reader arriving at /exhaust/ has no way to ask for
the half of it that applies to their vehicle.

This module adds the second axis. Each guide gets one primary vehicle type and
any number of secondary ones, and the build emits a page per type that
cross-cuts the categories.

Two sources, in this order:

  1. `vehicle:` in the article's front matter. Explicit, reviewable, and the
     only source a new guide needs to be filed correctly.
  2. Scoring the body text, when no field is set. This exists so a guide can
     never ship unfiled, not so that it can be filed accurately -- it cannot
     tell a Tundra teardown that mentions a Lexus from a luxury-car guide.

A guide the scorer is not confident about lands in `general`, which is a real
page and not a dumping ground: some guides genuinely apply to anything with
four wheels, and saying so is more honest than guessing.

## Why the thresholds are asymmetric

`CONFIDENT` gates the automatic path only. A type declared in front matter goes
live with a single guide, because an author saying "this is a truck guide" is a
claim about the guide rather than a guess about it. A type reached by scoring
needs `MIN_AUTO` guides before it gets a page, because a scorer that is wrong
once should not be able to mint a URL on its own.
"""

# slug -> (label, blurb). The blurb is what the page says under its H1; it is
# deliberately about the *vehicle* and not about the guides, matching the hub
# intros in build.py.
VEHICLES = {
    'truck': (
        'Pickup Trucks',
        'Half-ton and up, plus the mid-size trucks that share their parts.',
    ),
    'suv': (
        'SUVs',
        'Body-on-frame and crossover, including the full-size SUVs that are a '
        'truck underneath.',
    ),
    'sports-car': (
        'Sports Cars',
        'Hot hatches, coupes and anything bought for the drive rather than the bed.',
    ),
    'sedan': (
        'Sedans',
        'Family four-doors and the sport compacts built on the same platforms.',
    ),
    'luxury': (
        'Luxury Vehicles',
        'Cars whose infotainment, cabin and service costs are the subject.',
    ),
    'general': (
        'Any Vehicle',
        'Guides that apply regardless of what you drive.',
    ),
}

# Order matters: it is the order the vehicle strip renders in, and the order
# the sitemap lists the pages. Trucks first because that is the bulk of the
# catalog and the reader most likely to be here.
ORDER = ['truck', 'suv', 'sports-car', 'sedan', 'luxury', 'general']

# Words that identify a vehicle class when they appear in a guide's body. Only
# used when front matter is silent. Multi-word entries are matched as
# substrings, so 'F-150' and 'F150' are listed separately rather than being
# normalised -- cheaper to read and it cannot silently miss a spelling.
SIGNALS = {
    'truck': [
        'Silverado', 'Sierra', 'F-150', 'F150', 'F-250', 'F250', 'Ram 1500',
        'RAM 1500', 'Tundra', 'Tacoma', 'Colorado', 'Canyon', 'Ranger',
        'Wrangler', 'Gladiator', 'pickup', 'half-ton', 'bed length',
        'tonneau', 'tailgate', 'bed cover',
    ],
    'suv': [
        'Tahoe', 'Suburban', 'Escalade', 'Yukon', '4Runner', 'Bronco',
        'Explorer', 'Durango', 'Wagoneer', 'Expedition', 'Sequoia', 'SUV',
    ],
    'sports-car': [
        'GTI', 'Golf R', 'WRX', 'STI', 'Miata', 'Mustang', 'Camaro',
        'Corvette', 'Porsche', 'Cayman', 'Boxster', 'BRZ', 'GR86',
        'hot hatch', 'sports car', 'cat-back',
    ],
    'sedan': [
        'Accord', 'Civic', 'Camry', 'Corolla', 'Altima', 'Sonata', 'Elantra',
        'Jetta', 'sedan', 'sport compact',
    ],
    'luxury': [
        'Audi', 'Bentley', 'BMW', 'Mercedes', 'Lexus', 'Porsche', 'Genesis',
        'Cadillac', 'Land Rover', 'Jaguar', 'infotainment',
    ],
}

# How many scored mentions a type needs to be confidently the primary one, and
# how far ahead of the runner-up. Both have to hold. A guide that mentions a
# truck twice and a sedan twice is not confidently either.
CONFIDENT = 3
MARGIN = 2

# Guides a type needs before it earns a page of its own.
#
# Two, not one. A vehicle page with a single guide is a worse copy of that
# guide: the reader who searched for it wanted the article, and the page that
# ranks for the vehicle term has nothing on it the article does not. Two is
# enough that the page does a job -- it puts two guides next to each other and
# says what they have in common -- and it is the same bar the site already
# applies to category hubs, one of which ships with a single guide.
#
# It is not three. Three was the first instinct and it hid every type but
# trucks on a 28-article site, which makes the whole axis invisible to a reader
# and pointless to build. Hiding an empty page is the goal; hiding a page that
# would help because the catalog is young is not.
MIN_PAGES = 2


def score(text):
    """Raw mention count per vehicle type across a guide's body."""
    out = {}
    for vtype, words in SIGNALS.items():
        n = 0
        for w in words:
            n += text.count(w)
        if n:
            out[vtype] = n
    return out


def classify(meta, body_text):
    """Return (primary, [secondary...]) for one guide.

    `meta` is the article front matter. `body_text` is the English body, used
    only when the front matter says nothing.
    """
    declared = (meta.get('vehicle') or '').strip()
    also = meta.get('vehicle_also') or []
    if isinstance(also, str):
        also = [also]
    also = [str(x).strip() for x in also if str(x).strip()]

    if declared in VEHICLES:
        # A declared type is authoritative; `also` adds cross-listings.
        return declared, [x for x in also if x in VEHICLES and x != declared]

    counts = score(body_text)
    if not counts:
        return 'general', []
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], ORDER.index(kv[0])
                                                    if kv[0] in ORDER else 99))
    top, n = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0
    if n >= CONFIDENT and n - second >= MARGIN:
        # Anything else that scored at all becomes a secondary entry, so a
        # truck guide that spends a section on SUVs is findable from both.
        extra = [v for v, c in ranked[1:] if c >= CONFIDENT]
        return top, extra
    return 'general', []


def group(arts):
    """Map vehicle slug -> list of articles, newest first.

    `arts` is the list build.py assembles, each entry a dict with 'meta'.
    Every article lands in exactly one primary bucket and optionally more.
    """
    buckets = {v: [] for v in VEHICLES}
    for a in arts:
        meta = a['meta']
        primary, also = a.get('vehicle_primary'), a.get('vehicle_also') or []
        if primary not in VEHICLES:
            continue
        for v in [primary] + [x for x in also if x in VEHICLES]:
            buckets[v].append(a)
    for v in buckets:
        buckets[v].sort(
            key=lambda a: (str(a['meta'].get('published') or ''),
                           a['meta'].get('slug') or ''),
            reverse=True)
    return buckets


def live(buckets):
    """The vehicle slugs that have earned a page at MIN_PAGES or more."""
    return [v for v in ORDER if len(buckets.get(v, [])) >= MIN_PAGES]
