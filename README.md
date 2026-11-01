# Car Mod Review

Affiliate content site for truck parts. English, US audience.

## Status

Working draft — **not published**. No domain yet.

## Structure

```
docs/                    static HTML, no build step
  index.html
  methodology.html
  style.css
  cold-air-intakes/
    best-cold-air-intake-f150-50l.html
content/
  site.json              config: editorial rules, categories
tools/                   research scripts
```

## Editorial rules (non-negotiable)

1. **No fabricated experience.** Never write "I installed this for six months"
   unless it happened. Attribute claims to their actual source.
2. **No backdated posts.** Dates are real publish dates.
3. **No unsourced performance numbers.** If no dyno data exists, say so.
4. **Every post states what it could not verify.**
5. **Affiliate disclosure** at the top of every post and sitewide in the footer.
6. Affiliate links carry `rel="sponsored nofollow noopener"`.

## Why the rules

Google's spam policies treat scaled content abuse and date manipulation as
grounds for removal from the index, not just a ranking hit. FTC rules cover
fabricated testimonials. Both risks are larger than the benefit.

## Research notes

Data for the F-150 post came from live AmericanTrucks listings scraped
2026-10-30 (prices, star ratings, review counts, fitment ranges) plus YouTube
search results. Reddit's JSON API returned 403 during research; Yelp returned
403. No dyno data was found for these SKUs, which the post says explicitly.

## Next steps

See `content/PLAN.md`.
