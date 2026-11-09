# Shorts Script #1 — "The Install Time on the Listing Is Not the Install Time"

**Article:** `listing-install-time-vs-owner-reports`
**Runtime (as scripted):** 36 seconds
**Format:** 1080×1920 vertical
**Hook:** first 3 seconds

---

## The script

### 0:00 – 0:03 — HOOK (3s)

> **"Your intake listing says under an hour."**
>
> **"Here's what owners actually reported."**

On screen: real product photograph of the S&B intake (S203478).

Why this hook: it names a specific number the viewer has seen on a listing and
implies it might be wrong. No "wait for it", no "you won't believe".

---

### 0:03 – 0:09 — THE DATA (6s)

> **"We pulled 490 owner reviews across 24 listings."**
>
> **"On the parts listed at under an hour, the median was 38 minutes."**
>
> **"So the badge points the right way."**

On screen: the two-row table from the article.

---

### 0:09 – 0:17 — THE TURN (8s)

> **"But 4 of those 22 owners took two hours or more."**
>
> **"Two of them took four and a half."**

On screen: 2026 Silverado 1500 Duramax photograph.

> **"TedT, April 17th: 'I had to take out the coolant reservoir and other
> surrounding parts just to get the factory airbox out and the new unit in.'"**
>
> **"Four to five hours."**

---

### 0:17 – 0:25 — THE PRODUCT (8s)

> **"That's a $399 S&B dry intake, five stars, still recommended."**
>
> **"2,798 reviews."**
>
> **"The part isn't the problem. The engine bay is."**

On screen: S&B product photograph again, price card.

---

### 0:25 – 0:32 — THE STEP UP (7s)

> **"Same badge, same engine bay — and the aFe owners who timed it came in at
> 30, 45 and 60 minutes."**
>
> **"$435."**

On screen: aFe Momentum GT photograph.

---

### 0:32 – 0:36 — CLOSE (4s)

> **"Read the badge as the floor, not the estimate."**
>
> **"Full guide at carmodreview.com."**

---

## What the script may NOT say

Every number above comes from the article, which sources each one to a dated
review. `make_short.py` enforces this — it re-reads the article file and
refuses to render if a figure is not there.

Specifically, the script must never claim:

- **Testing.** No "we installed this" or "our truck". The site has no test
  vehicle and the article never claims one.
- **A CARB EO number.** The article states it *could not* confirm one. A short
  that implies legality would contradict the page.
- **That the long installs are bad reviews.** All of them are five stars.

---

## Renderer note — read before publishing

`make_short.py` currently lays out five fixed cards totalling **21 seconds**,
which is below the 30–45s brief. The five-card structure is hardcoded and
shared by all 10 existing Shorts, so changing it re-renders every published
video.

Two options, and this needs your decision:

1. **Publish at 21s.** It fits a Short fine, it is just short of your stated
   range.
2. **Add a sixth card to `make_short.py`** (the "4 of 21" turn above) and go to
   ~27–30s. This changes the layout for every article, so all 10 existing
   Shorts would need re-rendering to stay consistent.

The script above is written for **option 2 at 36 seconds**. I have not changed
`make_short.py`, because that is a site-wide change and your call.

---

## Generated files

Already on disk from `make_short.py`:

- `social/listing-install-time-vs-owner-reports-short.mp4` — 21s render
- `social/listing-install-time-vs-owner-reports-caption.txt` — Instagram
- `social/listing-install-time-vs-owner-reports-youtube.txt` — YouTube Short

Product photographs are real, from the retailer's own listings, with provenance
recorded in `content/products/listing-install-time-vs-owner-reports/*.txt`:
S&B S203478, aFe S114321, AIRAID S128744, K&N S114100.
