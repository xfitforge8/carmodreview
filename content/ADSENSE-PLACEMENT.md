# AdSense placement — where the units go, and why

Written 16 Nov 2026. **Nothing here is applied.** The standing rule is no
ads.txt and no AdSense config edits, and adding live ad slots changes the
account's review state, so the calls are the owner's. This file is the analysis
plus the exact markup, so applying it is a paste rather than a design job.

## What the site does today

Confirmed by reading `build.py`, not assumed:

- `ADSENSE_CLIENT = 'ca-pub-5923752113598101'` (`build.py:131`).
- `adsense_tag()` returns the verification `<script>` and is emitted through
  `analytics_tag()` into every page's `<head>`. That is the **site-verification
  snippet only**.
- **No `<ins class="adsbygoogle">` unit is emitted anywhere in `build.py`.**
  The file says so in a comment at line 129. So the site currently serves
  **zero ads** and earns nothing from AdSense yet.
- `docs/ads.txt` carries the correct `pub-` line for the same client.

So the question is not "where should the existing ads move." It is "where do
the first units go," and that is a much better position: the layout has not
been compromised yet.

## The layout constraint that decides everything

`.layout` (`style.css:76`) is a two-column grid: `minmax(0,1fr)` for the
article, **224px** for `.side`, with a 52px gap, max-width 1000px. Below 820px
it collapses to one column and `.side` becomes static.

The article column is therefore **about 724px wide on desktop** (1000 − 224 −
52). That single number rules out most of the standard advice:

- **A 970×250 billboard does not fit.** It is the highest-paying standard size
  and it will not render in a 724px column.
- **A 728×90 leaderboard does not fit** either, at 724px.
- **A 336×280 large rectangle does fit**, and so does **300×250** and any
  responsive unit.

This is the whole argument for responsive units: the desktop article column is
already narrower than the two best-paying fixed sizes.

## Recommended placement

Three positions, in priority order. Start with the first one only.

### 1. In-article, after the second section — the first unit to add

The strongest placement on a page like this is inside the prose, after the
reader has committed. Concretely: **after the second `<h3>` section ends**, not
immediately under the byline.

Why not under the byline: the space between `.byline` and the first `<h3>` is
the lede, and it is the one part of the page a reader has definitely read. An ad
there before the content starts reads as a toll booth and is the classic
above-the-fold policy risk. The site also already puts the hero `<figure>`
directly below the opening prose (`photos.inject_photos` places the hero above
the body, the rest at the end of sections), so a unit under the byline stacks
ad, photo and text in the first screen.

Measured on a real page: `docs/engine/ecu-tuning-explained.html` has its first
`<h3>` at byte 2,459, `<figure>` at 678, and `<h2>` only at 23,054 (the h2s are
Related/Topics blocks built by `build_related` and `build_topics`). So the
sections are `<h3>`-delimited and there are 11 of them — the second-section
boundary is a natural, low-risk break.

### 2. Sidebar, sticky — the second unit

`.side` is `position: sticky; top: 24px`, so a unit there stays with the reader
for the whole scroll. That is the highest-viewability inventory on the page
after in-article.

**Caveat that matters:** `.side` already stacks three blocks — recent posts,
categories, and "By vehicle" — and has `max-height: calc(100vh - 48px)` with its
own scrollbar. Adding a fourth block pushes the categories below the fold of the
panel itself on a laptop. If a unit goes here, put it **above** the recent-posts
block, not below everything.

### 3. End of article, before Related — the third unit

After the body, before `build_related`. Readers who finish an article are
engaged, and this is the least intrusive of the three. It is also the lowest
paying. Add it only after the first two are earning.

### Where not to put one

- **Inside a `.pick` block.** `product_photos.py` places product photographs
  inside those blocks on purpose, and the module docstring is explicit that the
  picture next to a price is a picture of that product. An ad between the
  photograph and the buy button breaks that and looks like a bait-and-switch.
- **Between the `<h1>`/dek and the first sentence.** Highest policy risk, lowest
  quality score.
- **A sticky anchor or vignette.** These are the formats that get sites
  penalised for ad density on mobile, and this site's mobile layout is a plain
  single column.

## The markup, when it is wanted

The build has one insertion point per page and `{body}` is a single HTML
string, so the clean implementation is a helper beside `adsense_tag()`:

```python
# build.py, beside adsense_tag()
ADSENSE_SLOT_ARTICLE = ''   # set to the data-ad-slot number from the AdSense UI
ADSENSE_SLOT_SIDE = ''


def adsense_unit(slot, label='Advertisement'):
    """One responsive ad slot.

    Returns '' when no slot is configured, so the build is byte-identical to
    today until a unit is deliberately enabled -- the same contract
    adsense_tag() already keeps.
    """
    if not (ADSENSE_CLIENT and slot):
        return ''
    return (
        f'<div class="ad-slot" aria-label="{label}">\n'
        f'<ins class="adsbygoogle" style="display:block" '
        f'data-ad-client="{ADSENSE_CLIENT}" data-ad-slot="{slot}" '
        f'data-ad-format="auto" data-full-width-responsive="true"></ins>\n'
        f'<script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script>\n'
        f'</div>')
```

Splitting the body at the second `<h3>` is the one non-trivial part, because
`inject_photos` has already rewritten the html by then. The insertion has to run
**after** photo injection so the section boundaries are final:

```python
# after: art_html = inject_photos(...) and the product_photos pass
art_html = insert_ad_after_section(art_html, 2, adsense_unit(ADSENSE_SLOT_ARTICLE))
```

and the helper splits on `<h3` the same way `photos.inject_photos` splits on
`(?=<h[23][\s>])`, counting to the requested section and inserting before the
next heading.

CSS, so a unit never causes layout shift — which is the thing that actually
costs Core Web Vitals and therefore ranking:

```css
.ad-slot {
  /* Reserve the box before the ad loads. A unit that appears and pushes the
     text down is a CLS hit on every page view. 280px is the large-rectangle
     height and the tallest common mobile unit. */
  min-height: 280px;
  margin: 30px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
@media (max-width: 620px) { .ad-slot { min-height: 250px; } }
```

## What has to be true before any of this earns

Three things, and the first two are not code:

1. **An ad unit has to be created in the AdSense UI.** `data-ad-slot` is a
   number Google issues per unit; it cannot be invented. This is why the helper
   above defaults both slot constants to `''`.
2. **The site has to be approved.** The verification snippet is live, which
   means the account is at least in review. Approval requires the content
   policy to pass — which the drafts-only rule already protects.
3. **There has to be traffic.** With 18 published pages and no ads, the honest
   expectation is that ads earn very little at first regardless of placement. Ad
   position multiplies revenue; it does not create it. The content queue is the
   higher-leverage work.

## The one measurement worth doing first

Rather than guessing, read the existing Analytics data for the pages that get
sessions, and place the first unit on those. `tools/cf_traffic.py` already
exists and reads Cloudflare's analytics for this site, so the data is one run
away — and it is the only way to know whether the sidebar or the in-article
unit will actually be seen.
