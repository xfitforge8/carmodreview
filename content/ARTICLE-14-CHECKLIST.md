# Verification checklist — Article 14

`content/articles/14-listing-install-time-vs-owner-reports.md`

Kept outside `content/articles/` on purpose: `build.py` publishes every `.md` in
that directory regardless of `status: draft`, so this would otherwise render as a
live public page.

**Every statistic in the article is produced by `install_time_stats.py`.** Run it
and compare. The decisions live in that file one review at a time, because an
earlier regex version got four things wrong and the first draft printed its
output before I checked it.

---

## Verified

- 24 unique product listings, 490 visible reviews, all fetched 5 Nov 2026 from
  AmericanTrucks review pages, deduplicated by listing URL. Four listings were
  fetched twice under different guide folders; the copy with more visible reviews
  is kept so no review is counted twice.
- Install-time buckets read off each listing: **16** "Less than 1 Hour", **6**
  "Afternoon", **1** "Shop Install", **1** blank.
- 51 of 490 reviews (10.4%) state a time in some form. 38 give one clear
  whole-job figure and are counted; 13 were read and excluded, each with the
  reason recorded in `install_time_stats.py`.
- "Less than 1 Hour": **n=22, median 37.5 min, range 10–270 min**. 4 of 22
  reported 120 min or more.
- "Afternoon": **n=16, median 142.5 min (2 hrs 22 min), range 40–240 min**. 5 of
  16 reported 90 min or less.
- Every quoted review: author, date and star rating as printed on the listing.
- Every price: list price read 4 Nov 2026 and already published on this site, not
  re-read today.

## Unverified

- **CARB Executive Order numbers for every intake in this set.** No listing stated
  one. The article says so plainly rather than guessing either way.
- **Live prices as of 7 Nov 2026.** BrowserOS Neo returned HTTP 503 on every call,
  so no product page was opened. All prices carry their original 4 Nov 2026
  check date.
- **Whether these 38 time reports represent each listing's full review corpus.**
  Listing pages show 10–60 reviews at a time; total review counts run from 6 to
  2,798. The 2,798-review S&B listing is represented by 3 timed reviews here.
  Treat the medians as directional, not as a survey. The article's "38 that gave
  one clear whole-job figure" says this without overclaiming.
- Any fitment claim beyond the listing's own vehicle title.

## Needs owner decision

- **Product overlap with articles 2, 9, 10 and 12.** Those already link the aFe
  Momentum GT, AIRAID, S&B and K&N. Your rule says do not repeat a product in two
  articles in the same week. This article uses them because they are the only
  listings with install-time evidence on disk. Options: move the publish date, or
  accept the overlap for this one piece.
- All buy links use `rel="nofollow"`, not `rel="sponsored"`, because every
  affiliate program in `content/affiliate.json` is still `enabled: false` with an
  empty ID.
- The commission disclosure line is in this article only. The other 13 published
  articles do not contain it. Site-wide change, your call.
- Whether to re-check all four prices before this goes live.

## Corrections made after the first draft

The first draft of this article printed numbers that its own source data does not
support. Recorded here so the same mistakes are not repeated:

| Claim in first draft | Actual |
|---|---|
| "Less than 1 Hour" n=21, median 30 min, range 5 min–5 hrs | n=22, median 37.5 min, range 10 min–4.5 hrs |
| "Afternoon" median 2 hrs 45 min, range 20 min–6 hrs | median 2 hrs 22 min, range 40 min–4 hrs |
| 4 of 21 owners took 2 hrs+ on "under an hour" parts | 4 of 22 |
| 4 of 16 "Afternoon" owners beat 90 min; "one in four" in the bottom line | 5 of 16 |
| aFe "the tightest spread of any full intake here" | false — Corsa's spread is 10 min, aFe's is 90 |
| "The five-hour intake" | the longest counted report is 4.5 hrs (two of them) |

The first five came from a regex parser that read "4 1/2 hrs" as 2 hours, read
"less than 5 minutes to program" as an install time, counted a tyre shop's
mount-and-balance as the owner's install, counted a hypothetical ("could bang it
out in 4 hours"), and matched reviews on author name alone — which counted one
reviewer's second review twice. It is replaced by explicit per-review decisions.
