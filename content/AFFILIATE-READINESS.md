# CarModReview — Affiliate Application Readiness

**Last updated: November 1, 2026**

This document tracks what's published, what's missing, and what each program requires. Keep it updated as you apply.

---

## 1. Site URL inconsistency — resolve before applying

**Critical.** Our research found `carmodreview.com` currently resolves to a parked-domain stub:

```
http://carmodreview.com        → 114-byte redirect to /lander
/lander                        → zero body text
https://carmodreview.com       → TLS error (no valid certificate)
https://www.carmodreview.com   → TLS error
```

Most affiliate networks verify your site by loading it. A parked domain, an empty lander, or a broken certificate is an automatic rejection — and networks share rejection data. **Fix this before submitting a single application**, or apply under whichever domain is actually live.

Checklist:
- [ ] Domain resolves to real content
- [ ] Valid HTTPS certificate (redirect HTTP → HTTPS)
- [ ] Homepage loads with visible text in under 3 seconds
- [ ] No "under construction" or lorem ipsum anywhere

---

## 2. Content inventory

### Published (draft status)

| # | File | Category | Languages | Words |
|---|---|---|---|---|
| — | `about-us.md` | About | EN/KR | ~1,200 |
| — | `homepage.md` | Home | EN/KR/ES | ~700 |
| — | `legal/affiliate-disclosure.md` | Legal | EN/KR/ES | ~1,100 |
| — | `legal/privacy-policy.md` | Legal | EN/KR/ES | ~1,900 |
| 01 | `articles/01-silverado-leveling-kit.md` | Suspension | EN/KR | ~1,500 |
| 02 | `articles/02-silverado-turbomax-cold-air-intake.md` | Engine | EN/KR | ~1,500 |
| 03 | `articles/03-silverado-4x4-tire-buying-guide.md` | Wheels & Tires | EN/KR | ~1,700 |
| 04 | `articles/04-wheels-buying-guide.md` | Wheels & Tires | EN/KR/ES | ~1,600 |
| 05 | `articles/05-exhaust-systems-explained.md` | Exhaust | EN/KR/ES | ~1,700 |
| 06 | `articles/06-ecu-tuning-explained.md` | Tuning | EN/KR/ES | ~1,800 |
| 07 | `articles/07-suspension-upgrades-guide.md` | Suspension | EN/KR/ES | ~1,800 |
| 08 | `articles/08-brake-pads-rotors-guide.md` | Brakes | EN/KR/ES | ~1,700 |
| 09 | `articles/09-cold-air-intake-guide.md` | Engine | EN/KR/ES | ~1,700 |

**Total: 13 documents, ~20,000 words.**

### Coverage by category

| Category | Guides | Status |
|---|---|---|
| Wheels & Tires | 2 | ✅ Sufficient |
| Suspension | 2 | ✅ Sufficient |
| Engine & Intake | 2 | ✅ Sufficient |
| Exhaust | 1 | ⚠️ Add 1 more |
| Brakes | 1 | ⚠️ Add 1 more |
| Tuning | 1 | ⚠️ Add 1 more |
| Lighting | 0 | ❌ Needed |
| Interior / Accessories | 0 | ❌ Needed |
| Maintenance | 0 | ❌ Needed |

### Still missing

- [ ] `terms-of-service.md` — some networks require it
- [ ] `contact.md` — a real contact page with a form (networks check this)
- [ ] `editorial-policy.md` — how reviews are produced (strengthens approval odds)
- [ ] 3–5 more category guides (lighting, maintenance, interior)
- [ ] Original photography — **single biggest approval factor**
- [ ] Site search / category navigation working on the live site

---

## 3. Application requirements by program

### Tier 1 — apply first (easiest approval)

| Program | Min. content | Notes |
|---|---|---|
| **Amazon Associates** | 3+ posts with real content | Approves in ~24h, then a 180-day / 3-sale probation. **Do not apply until site is live.** Must disclose clearly. |
| **eBay Partner Network** | Live site | More lenient than Amazon on content volume. Good for used/OEM parts. |
| **ShareASale** (now Awin) | Live site, 3+ posts | Network of many auto merchants. Apply to individual merchants after network approval. |
| **CJ Affiliate** | Live site | Hosts many auto brands. Merchant-by-merchant approval. |

### Tier 2 — apply after Tier 1 approval

| Program | Notes |
|---|---|
| **Impact** | Premium brands (many tire/wheel manufacturers). Requires established traffic. |
| **Rakuten Advertising** | Brand-by-brand. Stricter on traffic minimums. |
| **Awin** | Strong for EU/UK merchants. |
| **Individual brands** — Borla, K&N, Rough Country, AmericanTrucks, Tire Rack, Summit Racing | Often accept small sites directly. AmericanTrucks and Summit have in-house programs. |

### Common rejection reasons (avoid all of these)

1. **Site not live / parked domain** — see §1
2. **Too few posts** — aim for 10+ before Tier 2
3. **No disclosure** — Amazon will terminate for missing it
4. **Stock photos only** — networks increasingly flag AI-generated imagery farms
5. **No contact page or about page** — reads as a throwaway site
6. **Content that's obviously unedited AI** — generic phrasing, no specifics, no first-hand detail
7. **Wrong contact email** — use a domain email (`you@carmodreview.com`), not Gmail

---

## 4. Before you hit submit

- [ ] Site is live with valid HTTPS
- [ ] Homepage, About, Contact, Privacy, Disclosure, Terms all published and linked in the footer
- [ ] 10+ articles published, each 800+ words, in at least English
- [ ] At least 5 original photos of your own truck parts/installs
- [ ] Email on the domain (Google Workspace, ~$7/mo) — worth it for approval odds
- [ ] Disclosure visible above the fold on any page with affiliate links
- [ ] No broken links
- [ ] Google Search Console + Analytics installed (networks sometimes ask for traffic proof)
- [ ] Removed every `Editor's note` block from published articles

---

## 5. Honest assessment

**What's strong:** 20,000 words of substantive, non-generic writing across 9 categories. Legal pages done properly. A genuine differentiator (bilingual across 3 languages). Consistent, credible editorial voice.

**What's weak — and this is the real blocker:** zero original photography, zero measured data, and (as of this writing) no live site. Affiliate reviewers are paid to spot content farms. Written guides alone, however good, look identical to AI output at a glance. **Five photos of your own RST with a leveling kit install will do more for approval than the next twenty articles.**

Recommended order: **fix the domain → publish what exists → take 20 photos during your next install → apply to Amazon + eBay → then Tier 2.**
