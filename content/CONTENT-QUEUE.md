# Content queue — verified demand, 16 Nov 2026

Source: YouTube autocomplete (`suggestqueries.google.com/complete/search?client=youtube&ds=yt`)
pulled from a YouTube page context, plus live view counts read off `ytd-video-renderer`
`innerText` on 16 Nov 2026. Every figure below was read, not estimated.

## Why these topics and not others

The autocomplete data says the exhaust cluster is the biggest verified demand on
this site's subject matter, and that it splits into **sound** intent and **repair**
intent. Those are different articles and should not be merged.

**Sound intent** — people deciding what to do to a working truck:
`silverado 5.3 exhaust`, `muffler delete silverado 5.3`, `straight pipe`,
`borla atak`, `flowmaster 40 / super 10`, `black widow neighbor hater`,
`muffler delete vs straight pipe`, `muffler delete vs resonator delete`.

**Repair intent** — people fixing a noise they did not ask for:
`silverado exhaust flapper valve`, `exhaust rattle`, `exhaust leak sound`,
`exhaust manifold leak`, `exhaust manifold bolt broke`, `exhaust flange stud removal`.

Repair intent is worth flagging: it has less competition than "best exhaust" and
the queries are specific enough to rank for. The flapper valve cluster in
particular has three videos over 100K views about a **free** mod.

## Queue

Truck-exhaust topics (1–5) came first because that is where the deepest autocomplete
cluster was. Scope is not limited to trucks: rows 6–10 are sports cars, family sedans
and enthusiast compacts, chosen on the same evidence and each backed by prices that
were actually read.

| # | Article | Demand evidence | Status |
|---|---|---|---|
| 1 | Muffler delete vs straight pipe | `muffler delete vs straight pipe silverado` — 76K, 30K, and a 325K comparison video; 201K and 208K on adjacent terms | **written** — `25-muffler-delete-vs-straight-pipe.md` |
| 2 | Exhaust flapper valve | `exhaust flapper valve silverado` is the #1 autocomplete for that seed; videos at **214K, 172K, 115K, 58K, 20K** views — all about a $10-or-free mod | **written** — `26-exhaust-flapper-valve-rattle.md` |
| 3 | AFM/DFM disabler | 14-deep autocomplete cluster: `afm disabler silverado`, `5.3`, `6.2`, `reviews`, `sierra`, `tahoe`, `suburban`, `escalade`. Feeds the existing `24-gm-lifter-failure-which-trucks.md` | **written** — `28-afm-dfm-disabler-carb-legal.md` |
| 4 | Do tonneau covers improve MPG | One video at **624K views** (The Fast Lane Truck). Autocomplete variants: `do truck bed covers improve gas mileage`, `truck bed cover gas mileage`, `tonneau cover mpg test` | **written** — `30-tonneau-cover-mpg-test.md` |
| 5 | Cold air intake sound, before/after | `cold air intake sound` is the top autocomplete result for the whole seed; videos at **246K, 109K, 83K, 46K** | **written** — `31-cold-air-intake-sound.md` |
| 6 | Golf GTI cat-back buying guide | **"How To Modify Your Golf GTI \| THE ULTIMATE GUIDE" at 740K views** — the single highest non-truck signal found. Autocomplete: `golf gti exhaust`, `golf gti build`, `golf gti mk7`, `gti tuned mk7`, `gti burble tune`, `mk8 gti tune comparison` | **written** — `27-golf-gti-cat-back-exhaust.md`, plus `29-golf-gti-mk7-vs-mk8-tested.md` |
| 7 | Honda Accord 2.0T exhaust and tune path | `accord 2.0t exhaust`, `accord 2.0t tuned`, `accord 2.0t 0-60`. Two videos: **582K** (vs Audi A4 / Camry TRD) and **155K** (K-Tuner Stage 2) | **written** — `32-accord-2t-exhaust-tune-path.md` |
| 8 | Civic Si bolt-ons and tune | `civic si exhaust`, `civic si build`. **167K** view bolt-ons + tune review; the 17–21 Si sedan cat-back carries **209 reviews**, the most-reviewed fitment-specific exhaust found in this sweep | **written** — `33-civic-si-bolt-ons-tune-order.md` |
| 9 | WRX / STI downpipe before cat-back | Appears across the JDM seeds. The **MAP WRX catted downpipe at $749.99 has 279 reviews** — more than any cat-back in the sweep, which says the demand is power-first on this platform | **written** — `34-wrx-downpipe-before-cat-back.md` |
| 10 | Turbo Miata build order | **266K views** on a turbo Miata build; **115K** on ND2 Miata vs supercharged BRZ. The "verified-price surface is thinner" premise in this row was **wrong and is now corrected**: MAPerformance carries a deep Miata catalog, but it splits cleanly in half — every standalone ECU is NA/NB (1990–2005) and both forced-induction kits are ND (2016+), so no single model year can buy both halves from that shelf | **written** — `39-boosted-miata-build-order.md` |
| 11 | Exhaust manifold leak / broken manifold bolt | Not on the original list — repair intent, which the sweep had not searched. `exhaust manifold leak` videos at **737K, 553K, 413K, 352K, 271K, 186K, 171K**; `broken exhaust manifold bolt` at **2.5M, 2.5M, 773K, 355K, 342K, 167K, 128K**. The 355K is a product review of a single OEM Tools extractor, so the buying intent in this cluster is on the tool, not the manifold | **written** — `35-exhaust-manifold-leak-repair.md` |
| 12 | Transmission shudder: misfire, fluid or converter | The cluster the note below flagged as lower priority, promoted because the price surface turned out to be deep on Summit. `transmission shudder fix` videos at **428K, 419K, 261K, 251K, 233K, 172K, 95K**; `transmission shudder light throttle` adds **288K** (GM low-rpm shudder), **107K** (Ford Escape/Fusion 35mph); `torque converter shudder vs misfire` adds **703K** and **534K**. The diagnosis angle is the one the videos keep missing: they sell an additive before establishing whether the vibration is engine or transmission | **written** — `36-transmission-shudder-fluid-misfire.md` |
| 13 | 3.0 Duramax service: oil, fuel filter, and the diesel sound | `duramax 3.0 oil change / fuel filter change / diesel sound` — a service cluster, not a parts cluster. `diesel sound` splits it: the same traffic that wants a maintenance answer also wants a resonator or exhaust answer on the same engine | **written** — `37-duramax-3l-service-oil-fuel-filter-sound.md` |
| 14 | Bed rack with tonneau cover | 12-deep autocomplete cluster that had been parked as "accessory-fitment": `bed rack with tonneau cover`, `bed rack compatible with tonneau cover`, `rci bed rack tonneau cover adapters`, `bed rack for diamondback tonneau cover`, plus tundra/f150/tacoma/gladiator/maverick/yakima/voodoo/thule combos. Promoted because the fitment answer turned out to be one physical dimension, not a per-truck lookup | **written** — `38-bed-rack-with-tonneau-cover.md` |

### What the bed rack piece cost to source

**The deciding fact was in a `Notes` field, not in a fitment chart.** Elevate's own
listing says the rack *"Works in conjunction with tonneau covers that mount inside
bed rails without overlapping stake hole pockets"* — which is the whole article in
one sentence, because it names the surface rather than a cover brand. Rough
Country's 10204 supplies the negative case in the same field: *"Will not fit 6 ft.
7 in. bed. Will not fit tri-fold bed cover, or Rough Country's hard shell rooftop
tent."* Two exclusions of different kinds in one sentence, and only the second one
is about this topic.

**Same-brand siblings can have opposite mounting styles at a $99.96 spread.** Rough
Country 10204 is $399.99, stake holes, no drilling. 10406 is $499.95, bed rail,
**Drilling Required: Yes**. The cheaper one is the one that rules out the most
common cover type. That inversion is the piece's `fun_fact` and it came straight off
the two spec blocks.

**A populated `Notes` field is the tell for a listing worth reading.** Thule 34000
looks like a $94.95 rack in category search; its `Notes` reads *"Mounting kit for
Toyota Tacomas (without toolbox)"*, its `Part Type` is *"Bed and Ladder Rack
Accessories"* and its accessory type is *"Hardware kit."* Three correct fields, none
of which says rack.

**Unresolved: the Elevate TS Rail.** Elevate's description names it as the adapter
for covers *without* integrated T-slots, sold separately. A Summit search for it on
17 Nov 2026 returned the rack itself and nothing else. The article says the rail
exists and that it was not found in that search, and does not quote a price for it.

### Two extraction traps this cluster re-taught

**Summit part URLs still redirect to unrelated products.** `/part/backrack/30109/6613020`
resolved to a Troy Lee Designs sweatshirt (TLD-731835004). Real hrefs have to come
off the search DOM, not be assembled from a part number.

**The untrusted-content envelope contains square brackets.** A scraper that finds
its JSON payload with `text.index('[')` slices the `[UNTRUSTED_PAGE_CONTENT …]`
prefix instead of the payload and parses nothing. Strip both markers and cut at the
`Tip: this session` trailer first. This one silently returned zero rows for six
Pexels queries before it was spotted.


### What the Duramax piece cost to source, and what it could not get

**Summit's part URL can redirect to a different product.** Five of them did in one
sitting: `wix-filters/57060/1478899` resolved to a WIX 51045, `wix-filters/57060xp/5156181`
to a Rhodes Race Cars shock mount, `acdelco/13539108/7584903` to an AMS Performance
intake, `summit-racing/sum-127001/9479286` to a promo banner, `acdelco/19391402/5410236`
to a United Pacific part. Never copy an item id from a listing that was not re-searched
by keyword first.

**Fitment is checked page by page.** `?page=N` on `/applications` returns 27 rows a page
and up to ~22 pages on a big listing. The rows name Make, Model, Beginning/Ending Year,
Engine Size and Engine Family; the engine-family string (`3.0L/183`) plus a `DURAMAX`
match is the whole verification. That is what separated three real 3.0L filters from
WIX 33481 (school buses), WIX WL10255 (M22 x 1.5, Buick Enclave) and K&N HP-1017
(M22 x 1.5, Alfa Giulia).

**Vehicle-filtered listings break card extractors.** Adding
`/engine/3-0l-183-diesel` to a `/search/department/...` URL does filter correctly, but
the result cards come back empty; parse the `Part Number: ` text blocks instead.

**The dexos D list is the authority, not the bottle.** `gmdexos.com/brands/dexosd/index.html`
carries a supplier and an eleven-digit licence number per entry. Absence is provable by
substring count on the page (`SCHAEF=0 MOTUL=0 LIQUI=0 REDLINE=0`), which is what makes
the "suitable for" argument in the article defensible rather than an accusation.

### What the transmission-shudder piece cost to source, and what it could not get

Summit Racing was the working source again, and the `/search?keyword=` form was the
only one that returned usable cards. Two things are worth carrying forward:

**Fitment is a separate page and it is the one that matters.** Every fluid, filter
and gasket listing carries an `/applications` suffix that returns a "Results Found"
count and the transmission codes. That is how the LubeLocker trap was caught: the
81-review pan gasket returns eight applications naming the Turbo-Hydramatic 250 and
350, while the 6L80 version of the same gasket at the same price returns exactly
one Chevrolet application and has one review. A reader searching "6L80 pan gasket"
lands on the popular one first.

**The two products the top videos name are not on Summit at all.** Lubegard did not
return a single result, and the branded "instant shudder fix" returned one unrelated
Belltech carrier bearing across four searches. The piece names the products it can
verify, says plainly that the video-famous one is not on the retailer checked, and
publishes no price for it. Do not quote it from memory in a later revision.

One more thing worth knowing for the next repair-intent piece: Summit's fitment
counts are per listing, so a single part can legitimately show 2,176 applications
for one fluid and 450 for one gasket. Read the count as "how many vehicles this
listing claims," never as "how many vehicles this part fits."

### Verified non-truck prices (read 16 Nov 2026)

Non-domestic makes are not on AmericanTrucks or AmericanMuscle, so these come from
**maperformance.com**, which is reachable and lists fitment, price and review count on
the card. That store covers VW, Honda, Subaru and Ford, which is enough for rows 6–9.

**Golf GTI cat-back** — search "gti catback", **1,002 indexed results across 21 pages**
(16 Nov 2026). The earlier draft of this file listed 7 systems from the front page of a
different search; that was an incomplete sample and the floors below supersede it.

| Generation | Floor | Ceiling |
|---|---|---|
| MK5 (05–09) | **$386.40** Invidia Q300 | $1,129.99 Borla |
| MK6 (09–14) | **$743.75** Cobb | $1,303.95 APR |
| MK7 (15–17) | **$738.00** Ultimate Racing | $1,528.95 APR w/ front muffler |
| MK7.5 (18–21) | **$833.00** Cobb | $1,394.00 Cobb titanium |
| MK8 (22–) | **$945.00** XForce | $1,684.00 aFe Gemini XV |

Most-reviewed GTI cat-back: **Borla S-Type 140597, $1,014.99, 10 reviews** (MK7).

**Civic Si cat-back** — search "civic si exhaust", 71 results:

| System | Fitment | Price | Reviews |
|---|---|---|---|
| MAPerformance cat-back | 22+ Civic Si | from **$949.99** | 48 |
| MAP cat-back, sedan only | 17–21 Civic Si | from **$999.99** | **209** |
| MAP front pipe | 16–21 Civic X 1.5T | **$349.99** | 46 |
| PRL 3" front pipe | 16–21 Civic 1.5T | **$429.00** | 19 |
| MAP catted downpipe | 16–21 Civic 1.5T | **$599.99** | **85** |
| MAP downpipe | 22+ Civic / Si 1.5T | **$599.99** | 17 |
| Invidia catted 70mm downpipe | 16–21 EX/Touring/Si | **$861.27** | 2 |
| KTuner Flash V2 Touch | multiple Honda/Acura | **$749.00** | 248 |
| Invidia Gemini, Ti burnt tips | 17–21 Civic Si sedan | **$1,163.76** (was $1,799.28) | 56 |
| ARK Performance DT-S | 17–21 Civic Si sedan | **$1,437.84** (was $2,054.05) | 16 |

**Accord 2.0T** — search "accord 2.0t exhaust", 59 results:

| Part | Fitment | Price | Reviews |
|---|---|---|---|
| PRL front pipe hardware kit | multiple Honda/Acura 2.0T | **$31.00** | 1 |
| PRL front pipe upgrade | 18–22 Accord 2.0T | **$429.00** | — |
| PRL charge pipe upgrade | 18–22 Accord 2.0T | **$429.00** | — |
| PRL flex fuel kit | 18–22 Accord 2.0T | **$579.99** | — |
| Thermal R&D cat-back (sale) | 18–22 Accord Sport | **$1,019.99** (list $1,199.99) | 1 |
| MagnaFlow 19393 cat-back | 18–22 Accord 2.0T | **$1,231.00** | — |
| DC Sports exhaust system | 18–22 Accord 2.0T/1.5T | **$1,330.00** (was $1,399.99) | — |
| Borla S-Type cat-back | 18–22 Accord | **$1,338.99** (was $1,499.99) | 1 |
| Remark RK-C4076H-06 cat-back | 18–22 Accord 2.0T | **$1,495.00** | — |
| KTuner Flash V1.2 | multiple Honda/Acura | **$549.00** | — |
| KTuner Flash V2 Touch | multiple Honda/Acura | **$749.00** | 248 |

**WRX / STI** — search "wrx exhaust", 88 results:

| System | Fitment | Price | Reviews |
|---|---|---|---|
| MAPerformance axle-back | 22+ WRX | from **$495.00** | 16 |
| MAPerformance cat-back | 15–21 WRX/STI | from **$999.99** | 69 |
| MAPerformance cat-back | 22+ VB WRX | from **$1,149.00** | 18 |
| Tomei Expreme Ti cat-back | 08–21 WRX sedan, 11–21 STI sedan | **$1,161.00** (was $1,290.00) | — |
| Invidia R400 Gemini quad tip | 15–21 WRX/STI | from **$1,547.01** (35% off) | — |

The WRX also surfaced the highest review count found anywhere in this sweep on a
power part: the **MAP WRX catted downpipe Rev 4 at $749.99 with 279 reviews**. That
matters for article 9's shape — downpipe is the first real power step on a turbo car
and the review volume says people buy it, which is a different article from
"cat-back sound".

**The finding that reshaped article 9 (17 Nov 2026).** COBB's own product page for the
2015–2021 WRX NexGen Stage 2 package states the packages exist because of *"the removal
of Downpipes"*, and a site search for "wrx downpipe" returns **40 results with zero
named downpipe or J-pipe** — COBB still sells downpipes (67 results for the bare term,
first hit a Mitsubishi Evo X part) but not one for the WRX. Meanwhile the Accessport
carries **EO D-660-16 and D-660-43** on the 15–21 part and **seven EOs** on the 22–26
part, and every MAP/Invidia downpipe listing checked carried no CARB text at all. So
the article's thesis is that the tune is the legal first purchase and the downpipe is
the one to think hardest about — not the old "downpipe then cat-back, done" framing.

The number worth noticing across all four, and it is the opposite of what the
"trucks are expensive" instinct predicts. Reading the dollar figures visible on the
first page of each listing and taking the median of those between $200 and $4,000:

| Listing | Median | Sample |
|---|---|---|
| Silverado 1500 exhaust (AmericanTrucks) | **$674.99** | 78 prices |
| GTI exhaust (MAPerformance) | **$1,075.00** | 65 prices |

**The GTI parts are the more expensive ones, by roughly $400 at the median.** The
truck catalog has a lower floor and a lower middle; the German car's aftermarket is
priced higher across the board. Two caveats, and they matter: this is the median of
one page of each listing, not of the whole catalog (2,143 truck items and 80 GTI
results respectively), and MAPerformance is a specialist enthusiast store while
AmericanTrucks is volume retail. Treat the direction as real and the exact figures as
first-page samples.

### Scope note

Rows 6–9 exist because the owner widened scope past trucks ("dont stop digging, it
could be ohter sports car, family sedan" / "and anything"). The constraint that does
not move is the pricing rule: a piece is only writable once fitment, price and review
count have been read on a live listing. Rows 6–9 meet that bar; row 10 does not yet.

Row 11 was not on the original list and is the first repair-intent piece on the site.
It met the bar on Summit Racing, which turned out to be the working source for this
whole cluster: AmericanTrucks' `/search?q=` and `/catalogsearch/result/?q=` both
ignore the query string and return wheels, and Summit's `/search/part-type/<slug>`
endpoint returns "0 results for empty search" for any slug that is not an exact
internal name. The URL form that works is `/search?keyword=<terms>` — that one
returns product cards with part number, price and review count in the card text.


## Verification notes — traps found

**The AKM/disabler CARB split is real and the retailer hides it.** Read 16 Nov 2026
off AmericanTrucks and rangetechnology.com:

| Part | Price | Retailer says | Manufacturer says |
|---|---|---|---|
| Range RA003B | $280.95, 466 rev, 4.8 | nothing about CARB | **NOT LEGAL in California**, Emission Code 7, testing pending |
| Range RA007 | $264.95, 131 rev, 4.7 | EO D-115-32, 2021–2024 | **EO D-115-35**, 50-state, Emission Code 1, 2023–2026 trucks |
| Diablosport Sprint S1000 | $242.95, 15 rev, 4.7 | no CARB/emissions/EPA/smog text at all | not checked |
| Range Pulsar LT (15–18) | $554.95, 18 rev, 4.3 | no emissions text | Edge page makes no CARB claim either |

The EO number on the manufacturer's page and the EO on the retailer's page do not
match for the same part number (D-115-32 vs D-115-35). Always cite the
manufacturer, and tell the reader to check the EO on the box.

**Tonneau MPG — RESOLVED 16 Nov 2026. The 2007 SEMA study was found and read.**
The earlier note said not to repeat the 5.73% / 12% figures until a primary source
was reached. Both are now traceable, and one of them turns out to be much weaker
than the way it is quoted.

The primary document is `agricover.com/downloads/pdf/2007_windtunnel.pdf`,
*"How Tonneau Covers Affect The Coefficient of Drag"*, Megan McKernan, 2007. Text
extracted with the zlib `stream`/`(...)` method already noted below. What it
actually says:

- Tests run **30–31 January 2007** at the **A2 Wind Tunnel**, AeroDyne Wind
  Tunnel LLC, Mooresville, North Carolina. Dr. Richard Mark French of Purdue
  University was the academic participant.
- **Four trucks, thirteen tonneaus**: 2006 F-150 5'5" bed (1 cover), 2005 F-150
  6'5" bed (6 covers), 2006 Dodge Ram 1500 6'5" (3 covers), 2007 GMC Sierra 6'5"
  (3 covers). A dealer-provided 2007 Silverado was **dropped — as a 4-door 4WD it
  exceeded the ~5,800 lb balance limit.** Note that: the truck this site writes
  about most was excluded on weight.
- Cd was **normalised to 1** per truck. Absolute Cd values were deliberately not
  published, because the tunnel wall spacing would have inflated them. Only
  relative percentage change is meaningful here.
- Individual results at 85 mph: F-150 5'5" **5.7%**; Ram folding vinyl 5.0%,
  fiberglass **6.5%**, two-piece hard 5.0%; F-150 6'5" range **4.2% to 7.8%**
  (fiberglass 7.8% best, folding vinyl and retractable 4.2% worst); Sierra roll-up
  vinyl 5.0%, **7.4%**, **7.5%**.
- The headline **5.73% is the mean of those thirteen covers**, stated as *"on
  average, it is safe to say that a tonneau cover will reduce the coefficient of
  drag by 5.73%"*.

**The fuel-economy number is not measured, and the paper says so twice.** Direct
quotes: *"we cannot extract any information on fuel economy from the coefficient
of drag. Determining the effect on fuel efficiency would require knowing the
rolling resistance and drivetrain efficiency."* The 1.8% figure that circulates
is the author's own sketch, not a result: *"Aerodynamicists often say that a 10%
improvement in aerodynamic performance is good for a 2-3% improvement in gas
mileage, based on an EPA road speed of 48 mph. Therefore, an improvement in Cd of
5.73% could account for a 1.8% improvement in gas mileage."* That is a rule of
thumb applied to a rule of thumb. Any article repeating "1.8%" as a finding is
misreading the source. The paper's own conclusion is hedged: covers *"did reduce
drag, which would likely help to improve fuel economy."*

Two further findings from the same paper that are more useful than the headline:

- **Tailgate down is worse, not better.** F-150 5'5" went 1 → **1.001**; F-150
  6'5" improved only **0.8%**; **Sierra got 1.8% worse** (1 → 1.019). The paper
  notes this directly contradicts what owners do hoping for mileage.
- **Fiberglass tops the table but may not win** — the paper warns these *"can weigh
  much more than the soft covers and the result of adding the weight to the truck
  could decrease or even negate any improvement in Cd."* Drag is not the only term.

**The 12% figure is NOT from this study and remains unverified.** Every source
that quotes it — Peragon, covercent, tonneaucovers.me — attributes it to a 1997
Western New England College water-tunnel study. Peragon calls it *"an award-winning
paper written by the engineering students who performed it."* No primary document
was reachable: no title, no author, no archive copy, and archive.org's Western New
England College DTIC hit (`DTIC_ADA241270.pdf`) is about streamwise vorticity on
bluff bodies, not tonneaus. **Do not repeat 12% as a measurement.** The honest line
is that one secondary claim of that size exists and could not be traced.

Also worth citing, and verified only as a secondary description: the 2006
MythBusters test is the *only* one of the three that measured fuel rather than
drag, and it found fuel use *"about the same"* with a cover as without. It is
described consistently by Peragon and by the episode listing, but the episode
itself was not watched, so cite it as reported rather than as measured.

Live figures for the payback maths, all read 16 Nov 2026: AAA national average
regular **$3.8118/gal**; 2023 Silverado 4WD 5.3L **17 MPG combined / 19 highway**
(fueleconomy.gov); the Silverado bed-cover listing carries **622 covers**
(`Showing 1-30 of 622 Bed Covers & Tonneau Covers`).

**The first NHTSA TSB I downloaded was the wrong one.** `MC-10200136-9999.pdf`
is bulletin **21-NA-134**, a Camaro 3.6L squeak from a misaligned flange — not the
flapper. The flapper bulletin is **PIT5404E**, "Squeak Chirp Whistle Rattle Type
Noise From Rear Of Vehicle (Passive Exhaust Valve) Or Buffeting Vibration Drone
Exhaust Tone Change Body Pressure Booming (Afm Exhaust)", dated 11/20/2020,
covering 2014–2017 Silverado 1500, 2015–2017 Suburban and Tahoe. Read it at
`tsbsearch.com/Chevrolet/PIT5404E`. Title and summary verified on 16 Nov 2026.

TSB PDFs have no `pdftotext` on this machine. Extraction that works: inflate the
`stream...endstream` blocks with `zlib`, then pull `(...)` text-show operators.

### What the Miata piece cost to source, and the two premises it broke

**The queue's own premise was wrong.** Row 10 said the verified-price surface for a
Miata was "thinner." It is not thin — it is *split*. Every standalone ECU in the
MAPerformance catalog fits a 1990-2005 NA/NB (MegaSquirt Gen2 in 1994-1995 and
1999-2000, MS3Pro in five bands across 1990-2005, Haltech Elite 750/1500 harness
kits in 1990-1997 and 1998-2005). Both forced-induction kits fit a 2016+ ND
(HKS GT2 $5,310.00, Edelbrock E-Force $6,595.95). There is no model year where
both halves of the build can be bought from the same catalog. That split became
the article's thesis instead of a footnote.

**There is no Miata turbo kit in the catalog at all.** Ten queries turned up zero.
The trap: `Tomioka IHX475 JB Turbo Kit` is slugged
`/products/tomioka-ihx475-jb-turbo-kit-multiple-fitments-tr-tw1002` and reads
`Multiple Fitments (TR-TW1002)` in its title, which looks like it covers everything.
The body copy says it is a bolt-on for a **VW Golf R/S3**, and a scan for "Miata"
on that page returned nothing. "Multiple Fitments" is not a fitment claim for your
car; the Miata mentions have to be read out of the description.

### Three false positives that would have become false CARB claims

A naive `/(CARB|Executive Order|EO)/` scan of these product pages hits three
separate parts that have no EO at all:

- Tomioka turbo kit -> "**Carb**on Fiber Turbo Blanket"
- Haltech Elite 750 harness kit -> "**carb**ureted drag racing vehicles"
- DeatschWerks DW340 pump -> "**Carb**on Commutators and Brushes"

Every one of them would have read as "this part is CARB-legal" to a careless
pass. The article states that **no** EO was found on any part in the guide, which
is the only defensible version of the claim. Substring-match the whole word, and
print the surrounding text before concluding anything.

### The price moved between two reads of the same page

The HKS GT2 Pro Kit read **$5,900.00** in one pass and **$5,310.00** in a later
one, same URL, same day. Any figure carried over from an earlier session has to be
re-read before it goes in the file. All prices in article 39 were read on
18 Nov 2026 and every one is stamped with that date.

### Worst naming trap found so far: $1,260 for one word

`haltech-elite-750-...-adaptor-harness-1998-2005-...-ht-140621` is **$395.00** and
is the harness alone. `haltech-elite-750-...-adaptor-harness-kit-1998-2005-...-ht-150621`
is **$1,655.00** and includes the ECU. Both titles render as "Haltech Elite 750
Mazda Miata NB Plug'n'Play Adaptor Harness." Only the word **kit** separates them.
Same shape on the Elite 1500 ($2,059.00 kit vs harness-only).

## Standing rules for every article

- Drafts only. `status: draft`. Nothing publishes without the owner.
- Every number sourced and dated, read live via BrowserOS Neo. Never invented.
- Never use WebFetch — BrowserOS Neo MCP at `http://127.0.0.1:9211/mcp`.
- Draft-hold recipe before any build: move `19-*` `24-*` `25-*` (and any newer
  drafts) to `/tmp`, `python3 build.py`, move back. Then confirm the slug appears
  **zero** times in `docs/sitemap.xml`.
- Close browser tabs when done.
- ~~Disclosure line at the end of every article.~~ **Removed 18 Nov 2026** — the
  site is on AdSense, not affiliate programs, so the commission note was deleted
  site-wide (63 lines in 41 articles), along with the build-time disclosure
  block, the footer link, and `legal/affiliate-disclosure.md`. The privacy
  policy now describes Google AdSense advertising cookies instead of affiliate
  tracking cookies.

---

## Article 41 — wheel spacers (written 18 Nov 2026)

File: `41-wheel-spacers-thickness-guide.md`. EN 1,537 / KR 469 / ES 615 words,
10 `###` sections, 6 buyrows, 9 spacers verified live 18 Nov 2026.

### The finding that drove the rewrite

The first draft was built on notes saying "cheap quarter-inch spacer = lift-kit
clearance shim, expensive two-inch = stance part." Re-reading every product page
live demolished that. What is actually true:

- **Thickness does not predict price at all.** Three 0.250-inch spacers cost
  $13.99, $39.99 and $70.01 — a 5x spread at identical thickness.
- **The 2-inch bolt-on ($89.99) is $70 cheaper than the 1.25-inch ($159.99)**,
  with the same "studs included" feature set. The price ladder inverts.
- **Center bore is the spec that decides fit.** Spidertrax WHS007K is 106.17 mm
  and Trail-Gear 140019-2-KIT is 72.00 mm — same $159.99, same 1.250 inch, same
  pair quantity, 34 mm apart in the hole. No title, price or thickness field
  reveals it.
- Rough Country's 1065 copy does say *"designed to allow the use of factory
  wheels with Rough Country lift kits"* — but the 1101 at $89.99 says *"beefier
  stance"*, so the cheap/clearance framing only holds for the $39.99 part, not
  as a general rule.
- Summit SUM-75832B is **sold as Each**, every other spacer is a pair.

### Corrections caught before publish

- WHS010K is 1.5 in **5 x 5 Jeep**, not Toyota — an early note had it wrong.
- Trail-Gear 140019-2-KIT is 5 x 4.5 Jeep/Ford, not 6 x 5.5 Toyota.
- The `HUB-WORD` flag fired on pages where "hub-centric" appeared only inside a
  Rough Country bullet about *some models, application dependent* — not a claim
  about the part being viewed. Written into the article as the caution it is.

### Still to do

Bolt-pattern and center-bore columns are blank for four spacers where Summit
does not publish a bore. Filling those needs a vehicle-specific lookup, not a
guess.

---

## Article 42 — brake fluid (written 18 Nov 2026)

File: `42-brake-fluid-flush-guide.md`. EN 1,579 / KR 415 / ES 525 words,
10 `###` sections, 4 buyrows, 7 fluids verified live 18 Nov 2026.

### Queue correction

Items 2, 3, 4 and 5 in the topic queue were already written AND published
(`26-exhaust-flapper-valve-rattle`, `28-afm-dfm-disabler-carb-legal`,
`30-tonneau-cover-mpg-test`, `31-cold-air-intake-sound`) — all four in the live
sitemap. The queue was stale, so this article was chosen fresh from gap analysis
plus YouTube autocomplete instead: Brakes was the thinnest category at 2 articles.

Demand checked live: `brake fluid flush interval` returned 400K, 328K views on
the top explainers and a 13M-view how-to. `brake rotor resurfacing vs
replacement` was the runner-up (497K, 5.7M) and is still open.

### Why the spine is the wet boiling point

Summit publishes boiling points on only two of the seven fluids, so the article
quotes those two and explicitly declines to state figures for the other five
rather than lifting them from a forum table. The two that do publish happen to be
the cleanest possible comparison: **Summit SUM-943020 at $14.99/16.90 oz vs Motul
600 at $23.99/500 ml** — 16.90 US fl oz is 499.8 ml, so the bottles are the same
size, and the $9 buys 22°F dry and 16°F wet.

Legal floor verified from the primary source, not a blog: eCFR 49 CFR 571.116
gives DOT 4 as **230°C (446°F) ERBP and 155°C (311°F) wet**. The article quotes
the regulation directly.

### Numbers checked by arithmetic, not eyeballed

Per-ounce column (price / volume in US fl oz) recomputed in Python for all seven
rows before publishing; 3.38x spread between Wagner at $0.42 and Motul at $1.42.
One draft sentence claimed the Summit's 16°F dry-to-wet gap was "a third" of its
72°F margin over the legal floor — it is 22%, so it was corrected to "under a
quarter" before the build.

### Still open from this shelf

Liqui Moly ($8.99/500 ml, 42 reviews) is the value pick by price per ounce but
publishes no boiling figures. Worth a manufacturer spec-sheet lookup.

---

## Article 43 — rotor resurfacing (written 18 Nov 2026)

File: `43-brake-rotor-resurface-vs-replace.md`. EN 1,443 / KR 312 / ES 441 words,
10 `###` sections, 4 buyrows, 5 rotors verified live 18 Nov 2026.

### The spine is a subtraction

Every rotor carries a nominal and a discard thickness, and the gap is all the
metal you may ever remove. PowerStop AR85130SCR (2009 F-150) is 1.180 nominal /
1.120 discard = **0.060 in.** of usable life. Resurfacing spends part of it
permanently, which is why a previously machined rotor rarely takes a second cut.

### The counterintuitive finding, stated carefully

The drilled/slotted PowerStop AR8584XPR has **0.095 in.** between nominal and
discard — more than the 0.060 in. solid-surface rotor. Summit's drilled pair has
0.079 in. Both drilled rotors here beat both solid ones on usable range.

The article is explicit that **this is not a controlled drilling-vs-not test**:
the discs are different diameters for different applications, and usable
thickness range says nothing about crack resistance under thermal cycling. What
it does refute is assuming the margin from a product title.

### Two rotors, identical specs, $69.29 apart

PowerStop AR85130SCR ($89.99) and Frozen Rotors 2527FZR ($159.28) carry the same
12.99 in. diameter, same 1.180 nominal, same 1.120 discard. The premium buys a
60-hour cryogenic treatment, not more wearable material. That distinction is in
the article because it is what the specs actually show.

### Declined to invent

- EBC RK7042 publishes a nominal 1.011 in. but **no discard thickness**. Table
  shows a dash and the article says why, rather than filling the gap.
- No machining costs are quoted, because no listing prices the service. The
  cost comparison is qualitative and the article says so.
- Added a "What I could not verify" section covering machining cost, the
  cryogenic claim, and drilled-rotor cracking resistance.

## Article 44 — wheel alignment after a lift kit (draft)

**Queue staleness, second time.** Items 2-5 of the supplied queue were already
published: 26-exhaust-flapper-valve-rattle, 28-afm-dfm-disabler-carb-legal,
30-tonneau-cover-mpg-test, 31-cold-air-intake-sound. Picked a gap instead:
Wheels & Tires had three articles and Suspension four, against fourteen in
Engine.

**Demand verified live, 18 Nov 2026.** YouTube `ytd-video-renderer` innerText on
a search for "wheel alignment after lift kit": 1.7M views ("FREE ALIGNMENTS
FOREVER"), 876K ("Understanding the Wheel Alignment Process"), 105K ("How To
Properly Align Your Lifted Subaru"), 48K, 27K, 25K, 16K. Google autocomplete
returned empty for all three test queries, so view counts are the evidence here
rather than suggestion data.

### The spine: every kit is priced per wheel

Eight parts verified live. Five alignment kits and their published per-kit
quantity:

| Kit | Price | Covers | Front axle |
|---|---|---|---|
| Moog K80277 | $12.99 | one front wheel | $25.98 |
| Moog K6669 | $65.99 | one front wheel | $131.98 |
| SPC 82387 | $75.99 | one front wheel | $151.98 |
| SPC 86376 | $66.99 | one front wheel | $133.98 |
| SPC 86377 | $99.99 | not stated | — |

All figures read from the listing spec blocks on 18 Nov 2026, after "See More
Specifications" expansion, between the `Part Number:` and `Brand:` markers.

### The trap that is actually worth money

**"Sold as a pair" does not mean both front wheels.** SPC 82387's spec row reads
*Includes Alignment Components For: One front wheel* and *Quantity: Sold as a
pair.* The pair is two cam bolts for one strut. A $75.99 kit is $151.98 at the
counter, and the information is in a spec row, not the title or the price.

### The $14.99 part that is not an alignment kit

Search results surface SPC 6766099 at $14.99. Its Part Type is *Wheel Alignment
Kit Replacement Components* and its notes say *Replacement hardware for
SPS-67660* — a hardware bag. SPC 67660 itself is $195.99 and described as
*Control Arm, Adjustable, Alignment, Rear, Scion, Subaru, Each* — a Subaru rear
arm. Nothing in that chain is a truck front alignment kit. This is in the article
because the search results do not separate them.

### Correction ranges are what you buy

Moog K6669 ±1.00° camber and caster; SPC 86376 ±1.50° both; SPC 82387 ±2.00°
camber only, caster not rated. SPC 86377 at $99.99 — the most expensive part —
publishes no degree figures at all, only an application list (2019+ Silverado/
Sierra). The article states that rather than inferring a number.

### Declined to invent

- SPC 86377's correction range. Application list only, no degrees.
- Moog K80277's correction range. Listing says "adjustable caster/camber plates"
  with no figures.
- Fitment for any specific truck. The applications tables lazy-load and were not
  read; the article tells the reader to check by VIN.
- Labour cost. No listing prices the alignment service.

### Photos

Five Pexels photos, each page title verified before download: 3806288, 6720507,
38324578, 8986137, 37175105. Sidecars carry alt + caption naming the source.

### Operational note

`python3 build.py` takes ~29s in the foreground. The same command backgrounded
through the harness wrapper produced empty output and a hung process twice
(6:48 elapsed, 0% CPU, no sockets), and the hold/restore chain then left the
article in /tmp. Run builds in the foreground with a long timeout.

## Article 45 — wheel offset vs backspacing (draft)

**Queue stale for the third time.** Items 2-5 of the supplied queue are 26, 28,
30 and 31, all published. Picked a verified gap instead.

**Demand verified live 18 Nov 2026** from YouTube `ytd-video-renderer` on
"wheel offset explained": **921K** ("How To Choose Wheel Offset For Your Chevy
Silverado"), **735K** ("Truck Wheel Offset Explained | Ford F150"), **513K**
("What is Wheel Offset?"), **502K** ("How to measure your Wheel Offset / ET"),
**429K** ("What's the Best Stance for Your Truck?"), **411K**, 251K, 148K, 110K.

### The spine: the two specs are one spec, so listings self-check

Backspacing = (width + 1) ÷ 2 + offset ÷ 25.4

Verified against five wheels read live, worst case 0.04 in.:

| Wheel | Width | Offset | Calculated | Listed |
|---|---|---|---|---|
| Vision SW60 | 6.50 | +40 | 5.32 | **5.33** |
| Method MR305 | 8.50 | +25 | 5.73 | **5.70** |
| Black Rhino Tembo | 9.00 | +12 | 5.47 | **5.47** |
| Moto Metal MO970 | 9.00 | +18 | 5.71 | **5.71** |
| Fuel Vapor D560 | 9.00 | +20 | 5.79 | **5.75** |

I tested the naive form first (`width/2 + offset/25.4`) and it was off by a
consistent -0.5 in. on all five. That consistency is what identified the missing
inch as bead flange rather than a data error -- which is exactly the diagnostic
the article teaches.

### The counterintuitive pair

Vision SW60: 6.5 in. wide, **+40 mm** offset, backspace **5.33 in.**
Black Rhino Tembo: 9.0 in. wide, **+12 mm** offset, backspace **5.47 in.**

More than three times the positive offset and still the shallower backspace,
because 2.5 in. of extra width moves the centre line 1.25 in. before offset
counts at all. Big offset numbers do not mean the wheel sits further in.

### Other figures verified

Bolt patterns 6x135, 6x139.70, 8x165.10, 8x180. Center bore **57.10 mm**
(Vision) to **125.10 mm** (Moto Metal) -- 68 mm spread, in no title. Load rating
**1,520 lbs.** to **3,700 lbs.** per wheel. Black Rhino wheel weight **33.2
lbs.**, Vision **12.9 lbs.** (16x6.5 steel vs 18x9 aluminum, so size and
material, not quality).

### Deliberate choices

- **No prices in the article.** Read but not quoted: the piece is about
  specification, prices move, and quoting them would date the article on a page
  whose value is durable arithmetic. Stated in "What I could not verify".
- **Flange constant presented as empirical, not exact.** It matched five wheels
  to 0.04 in.; flange thickness varies by construction, and the article says a
  small gap is normal and a large one is a red flag.
- **No fitment claims.** Application tables lazy-load and were not read;
  readers are told to confirm by year/make/model/trim.
- **Load rating basis flagged as unverified** -- whether each brand accounts for
  dynamic load or a safety factor is not comparable without manufacturer docs.

### Overlap check

`04-wheels-buying-guide.md` covers offset, width and fitment across 1,944 words
and mentions **backspacing zero times**. This article is the backspacing
arithmetic 04 does not contain, so it complements rather than duplicates.

### Operational

Draft-hold now has to include 44 as well as 45: 44 is still `status: draft` but
live in `docs/`, so a build with only 45 held produced 66 URLs. Held both,
confirmed 65.

---

## Article 46 — `46-tonneau-cover-spec-row-guide.md`

`slug: tonneau-cover-spec-row-guide` | category: Tonneau & Bed | vehicle: truck
| `status: draft` | EN 1,330 words, KR 452, ES 561 | 9 `###`, 5 photos, 5 buyrows

### Why this one

Tonneau & Bed was the thinnest category at 3 articles. Demand checked on
YouTube: "hard vs soft tonneau cover" returns 714K, 571K, 345K, 187K, 125K views
on the top five results. The category earns its fourth piece.

### Overlap check

`11-tonneau-covers-explained.md` is 2,399 EN words and owns the tier/price-band
story (soft roll-up $190-275 up through hinged $1,500-2,700). It contains
**zero** occurrences of "Full Truck Bed Access" or "Toolbox Compatible". This
article is about the spec row, not the tier, so it complements rather than
duplicates. `30-tonneau-cover-mpg-test.md` owns the fuel-economy question and
this article quotes no MPG figure at all.

### The angle changed during verification

The first draft framed "Full Bed Access: No" on the $1,999.95 Rough Country as a
straight inversion — most expensive, only No, beaten by a $189.99 cover. Reading
the feature list corrected that: its **first listed feature is a removable
canister**, so "No" describes the cover as delivered, not a limit on the bed.
That turned a negative framing into the real story — the two retractables here
are two legitimate answers to the same problem (canister stays and bed stays
usable vs. canister comes out). The article now leads with that.

### Verified live 18-19 Nov 2026, all five spec blocks re-read

| Cover | Price | Full bed access | Toolbox | Location | Warranty |
|---|---|---|---|---|---|
| Summit SUM-484800 | $189.99 | Yes | No | Top of bed rails | 1-year |
| TruXedo 297701 | $349.99 | Yes | No | Top of bed rails | 5-year |
| BAK 448339 | $1,199.99 | Yes | **Yes** | **Inside bed rails** | 5-year |
| Retrax 60378 | $1,599.99 | Yes | No | Inside bed rails | **Limited lifetime** |
| Rough Country 51509550 | $1,999.95 | **No** | No | Top of bed rails | 5-year |

All five: 5 1/2 ft. bed, Drilling Required: No, Hinged: No.

### Listing contradictions found on the Rough Country (all verbatim)

1. Title says **5'7"** bed; spec row says **5 1/2 ft.**
2. Title says **"Powered"**; description says **"manually operated"**
3. Spec row says **5-year** cover and frame; feature list says **"3-Year
   Limited Warranty"**
4. Spec row says **Full Bed Access: No**; feature list says **"Removable
   canister for total bed access"**

Four disagreements on one $1,999.95 page. The article reports all four and tells
the reader to confirm by manufacturer part number — it does not pick a winner.

### Deliberate choices

- **No MPG numbers, manufacturer or otherwise.** Several listings imply
  aerodynamic benefit; none publishes a measured figure, so none is quoted.
- **No negative disclaimers.** The Rough Country section is framed as "confirm
  before ordering", not "avoid this part".
- **Canister cost stated as design reasoning, not measurement.** No listing
  publishes the bed volume a canister consumes; Retrax is the only one that
  publishes a container size (11 in. squared spiral track).
- **No fitment claims beyond bed length.** Application tables lazy-load and were
  not read.

### Photos

Five verified Pexels photos (each `/photo/<id>/` page title read individually,
not scraped from search results): 33038583, 31905602, 4895403, 9331872,
12748714. **Pexels has no tonneau cover photography** — six search terms
returned only bare truck beds. Captions say so honestly ("the bed fully open and
uncovered", "from outside, five covers at five prices look the same"), matching
the convention already used by `tonneau-cover-mpg-test`.

### Operational

Draft-hold must now hold **44, 45 and 46**. Confirmed: build with all three held
gives 65 URLs, 43 articles, and none of the three appear in `docs/sitemap.xml`
or `docs/`.

---

## Article 47 — `47-big-brake-kits-wheel-diameter.md`

`slug: big-brake-kits-wheel-diameter` | category: Brakes | vehicle: truck (+suv)
| `status: draft` | EN 1,452 words, KR 323, ES 477 | 10 `###`, 4 buyrows, 5 photos

### Why this one, and why the queue was skipped again

The supplied topic queue has now been stale five runs running — items 2 through 5
(exhaust flapper, AFM/DFM disabler, tonneau MPG, CAI sound) already exist as
published articles 26, 28, 30 and 31. Re-walking it would duplicate them.

Picked from the live gap instead. Published counts by category were: Engine 14
(30% of the site), Exhaust 7, Electrical/Tuning/Suspension 4 each, Tonneau 3,
**Brakes 2**, **Wheels & Tires 2**. Brakes was joint-thinnest.

Demand checked on YouTube 19 Nov: "big brake kit worth it" returns 2.7M, 1.1M,
231K, 156K, 151K; "brake caliper upgrade truck" returns 447K, 239K, 231K, 156K.

### Overlap check

**No brake article mentions "big brake" at all.** Grepped counts across
`08-brake-pads-rotors-guide` (2,187 EN words), `40-stuck-brake-rotor-removal`
(1,618), `42-brake-fluid-flush-guide` (1,654) and
`43-brake-rotor-resurface-vs-replace` (1,526): zero occurrences in every one.
Article 43 owns rotor discard thickness; this owns kit selection. Complementary.

### Verified live 19 Nov 2026

| Kit | Price | Rotor | Pistons | Min wheel | Bolt | Rear incl. | Reman |
|---|---|---|---|---|---|---|---|
| PowerStop KC2073-36 | $1,269.84 | 12.80 in. | 2 | **none published** | 8 x 6.50 in. | Yes | **Yes** |
| Wilwood AERO6 140-9789-D | $2,692.54 | 14.25 in. | 6 | 18 in. | 6 x 5.50 in. | No | No |
| Wilwood TX6R 140-13877 | $3,200.56 | 16.00 in. | 6 | 20 in. | 8 x 6.50 in. | No | No |
| Wilwood TX6R 140-13873 | $3,268.50 | 15.00 in. | 6 | 20 in. | 8 x 6.50 in. | No | No |

Fifth part, referenced but not in the table: PowerStop **BBK-JK-002R** (Jeep),
$1,010.99, front rotor 13.50 in., rear 14.25 in., **one piston** per front
caliper.

All four table kits: master cylinder, brake booster and front spindles **not**
included. AERO6 notes: will not fit aluminum spindles, cast iron only.

### Inversions this article is built on

1. **The rear rotor is bigger than the front** on BBK-JK-002R — 14.25 in. against
   13.50 in., on a kit sold as a front-and-rear upgrade.
2. **"Big brake" with one piston** per caliper at $1,010.99, the same count as a
   base economy car, and `Remanufactured: Yes` at a four-figure price.
3. **The cheaper PowerStop includes both axles** ($1,269.84) while every Wilwood
   is front-only at 2-2.5x the price — so per-axle the gap is far wider than the
   stickers suggest.
4. **Bolt pattern splits the market before price does**: the $2,692.54 AERO6 is
   the only 6-lug kit, the other three are 8 x 6.50 in.

### Deliberate choices

- **No stopping-distance claim of any kind.** No listing publishes a 60-0 figure
  before or after, so none is made. The article says so twice.
- **"None published" is stated, not interpreted.** The PowerStop Chevy/GMC kit has
  a blank minimum-wheel field; the article says that is a question for the
  seller, not a claim of universal fit.
- **Remanufactured framed as a difference, not a defect.** It is legitimate and
  warrantied; at four figures it belongs in the decision.
- **No fitment claims.** Spec blocks read, application tables not.

### Photos

Five verified Pexels photos, each `/photo/<id>/` title read individually:
833320, 34277926, 6870299, 36774072, 27534016. Unlike the tonneau article —
where Pexels had no cover photography at all — real brake caliper and rotor
photos are plentiful, so every caption describes an actual brake component.

### Operational

Four articles are now held from builds: **44, 45, 46, 47**. Articles 41-43 are
also `status: draft` but are already committed in `docs/`, so holding them would
delete live pages; they are left alone. Confirmed build: 65 URLs, 43 articles,
none of 44-47 in `docs/sitemap.xml` or `docs/`, no photo directory leaked.

---

## Article 48 — `48-led-headlights-street-legal-dot.md`

`slug: led-headlights-street-legal-dot` | category: Electrical | vehicle: truck
(+suv) | `status: draft` | EN 1,356 / KR 343 / ES 522 | 10 `###`, 5 photos

### Why this one

Electrical was tied thinnest at 4 published articles, and had no lighting
article at all: across 47 articles "headlight" appears seven times, all passing
mentions in suspension and intake pieces.

Demand verified on YouTube 19 Nov: "led headlight bulb upgrade truck" returns
4.3M, 3.2M, 1.3M, 922K, 589K, 369K views. This is the strongest cluster seen in
any of the last three runs.

### Verified live 19 Nov 2026

| Product | Price | Type | Colour temp | Street legal | DOT | Qty |
|---|---|---|---|---|---|---|
| PIAA LEH172E | $148.99 | bulb kit H8/H9/H11/H16 | 6600K | **Yes** | not stated | pair |
| Oracle 5769-123 | $324.79 | 7 in. sealed LED | not published | not stated | not stated | **individually** |
| J.W. Speaker 8700 Evo 2 | $464.75 | 7 in. sealed LED | not published | **DOT-approved** | **Yes** | pair |

PIAA also lists: 18.0 W low beam, controller-free, JIS S2 waterproof.
Oracle: Halo/DRL Yes (white), SwitchBack amber turn signals.
Both sealed units: CAPA Certified No, NSF Certified No.

### The finding

A $148.99 kit states **Street Legal: Yes** and publishes **no lumen field, no
candlepower field, no DOT field and no SAE field** — all four searched for on the
page and all four absent. The $464.75 pair states DOT-approved in its notes and
publishes three certification fields, answering No on two of them.

The per-unit inversion: Oracle is $324.79 for **one**, J.W. Speaker $464.75 for
**two** — $324.79 vs $232.38 per lamp, so the DOT-approved pair is **$92.41
cheaper per unit**. That vanishes if you compare stickers without reading the
quantity field.

### Deliberate choices

- **No lumen comparison at all.** None of the three publishes a figure, so any
  brightness ranking would be invented. The article says this explicitly and
  tells the reader the ranking they want cannot be honestly built.
- **6600K framed as colour, not brightness** — the single most common misreading
  of a headlight spec.
- **No assertion about FMVSS 108 self-certification.** An earlier draft claimed
  DOT approval is manufacturer self-certification under FMVSS 108; I could not
  verify that live, so the final text describes what the two certification fields
  mean and no more. Likewise a specific FMVSS/Vehicle Code citation was removed
  and replaced with a plain statement that lighting is a different rulebook from
  CARB.
- **PIAA's street-legal claim is not contradicted.** The article says it is a
  manufacturer claim worth taking seriously, and that the page simply gives you
  no standard to check it against.

### Photos

Five verified Pexels photos, each `/photo/<id>/` title read individually:
33695403, 17286224, 31140747, 28339262, 38510054. All are genuine headlight
photography. Captions tie each to a spec field rather than describing the stock
image generically.

### Operational

Only article 48 was held for this build: 44-47 are now published, 41-43 were
already live. Build gave 69 URLs unchanged, no page, no photo directory, and
`docs/` byte-identical.

---

## Article 49 — `49-load-range-ply-rating-guide.md`

`slug: load-range-ply-rating-guide` | category: Wheels & Tires | vehicle: truck
(+suv) | `status: draft` | EN 1,245 / KR 265 / ES 509 | 22 `###`, 5 photos

### Why this one

Wheels & Tires was the joint-thinnest published category at 4, and "load range"
appeared in exactly **one** of 47 articles — a passing mention in the 4x4 tire
buying guide. Genuine gap, not a re-run.

Demand verified on YouTube 19 Nov, query "load range e rated tires explained":
100K, 44K, 29K, 17K, 3.8K, 928 views. Viewers are asking a definitional question,
which is exactly what a spec-block comparison answers.

### Verified live 19 Nov 2026 — all five are 285/70-17, same day

| Tire | Price | Load range | Load index | Max load | Tread plies | Sidewall plies | Weight |
|---|---|---|---|---|---|---|---|
| Toyo Open Country A/T III | $320.99 | P-metric (no letter) | 117 | **2,833 lbs.** | not published | not published | 46.0 lbs. |
| BFGoodrich All-Terrain T/A KO3 | $320.99 | C | 116/113 | 2,755 lbs. | **6** | **6** | 57.0 lbs. |
| Falken Wildpeak A/T4W | $316.99 | E | 126/123 | **3,750 lbs.** | **10** | **3** | 65.4 lbs. |
| Mickey Thompson Baja Boss A/T | $307.99 | SL | 116 | 2,756 lbs. | not published | not published | 48.8 lbs. |
| Nitto Ridge Grappler | $300.99 | XL | 116 | 2,756 lbs. | not published | not published | 48.7 lbs. |

Also read: all five DOT-Approved Yes; 3PMSF Yes on Toyo/KO3/Falken/MT, **No**
on Nitto; UTQG 600 (Toyo), 500 (Nitto), absent on the three LT-style tires;
speed ratings T (Toyo), S (KO3, Falken), Q (Nitto), T (MT).

### The finding

**Load Range E published 10 tread plies and 3 sidewall plies.** Load Range C
published 6 and 6. Anyone converting the letter to a ply count gets both wrong,
in opposite directions. Ply rating stopped describing physical plies when
cotton gave way to other cord materials; the letters survived as load bands. The
article's core point is that tread ply and sidewall ply are separate construction
details and *neither* is the ply rating.

Second finding: the **P-metric** Toyo carries 2,833 lbs. against the **LT Load
Range C** KO3's 2,755 — 78 lbs. more, at the identical $320.99, and 11 lbs.
lighter per corner (44 lbs. across four).

Third: four tires, four different letters (SL, XL, C, none), and max load lands
within 78 lbs. of itself across all four. At this size the letter is not a price
or capacity tier. Only the Falken separates, and on the number.

### Deliberate choices

- **No conversion table.** Every load-range-to-ply table I have seen is
  unreliable, and the two products that publish plies contradict the popular
  ones. The article says plainly that it will not supply one.
- **No claim that P-metric is better than LT.** The verified fact is a price,
  weight and capacity comparison between two specific tires. LT construction
  exists for reasons this article could not source, and it says so.
- **No load-at-pressure arithmetic.** Max load is quoted at a stated inflation
  pressure that was not read on all five, so no derating is attempted.
- **Deferred to the vehicle on capacity.** Load range cannot raise a payload
  rating; that comes off the door jamb. Stated explicitly to head off the most
  common misreading.
- **Corrected an error before commit:** the article first called the KO3 the
  "Trail-Terrain" — the spec block read was the All-Terrain T/A KO3. Fixed in
  all three languages. Also fixed a ranking sentence that called the KO3
  "third-weakest" when it is in fact the lowest of the five.

### Photos

Five verified Pexels photos, each `/photo/<id>/` title read individually:
7019611 (tire with pebbles in treads), 5578887 (truck tire close-up), 9576099
(black tires), 7019607 (truck chassis and tires), 7019610 (dirty tire).
Captions tie each photo to a specific spec field rather than describing the
stock image.

### Operational

Articles 48 and 49 were **both** held for this build — 48 is still an unpushed
draft from the previous run. Build: 69 URLs unchanged, 0 hits for either slug in
sitemap, no pages, no photo directories, `docs/` byte-identical.

---

## Article 50 — `50-truck-tuner-carb-eo-guide.md`

`slug: truck-tuner-carb-eo-guide` | category: Tuning | vehicle: truck (+suv) |
`status: draft` | EN 1,220 / KR 308 / ES 497 | 23 `###`, 5 photos

The supplied topic queue was stale for the **sixth** consecutive run — items 2–5
are published articles 26, 28, 30, 31. Chose by category gap and product-class
fit instead: Tuning is tied thinnest at 4 published, and all four existing Tuning
articles are platform build-orders (Tundra, Civic Si, Miata). **There was no
truck programmer article at all**, and programmer listings publish a CARB EO
field, which is this site's core competence.

### Verified live 19 Nov 2026

| Device | Price | Rating | EO published | Writes |
|---|---|---|---|---|
| Superchips GM Flashcal 2545 | $268.95 | 4.0 · 18 | none | speedo/gears/TPMS, **no tune** |
| SCT X4 Power Flash 7015 | $377.99 | 4.25 · 79 | none | **pre-loaded** tunes |
| Bully Dog BDX 40470 | $377.99 | 3.5 · 16 | none | pre-loaded + 10 custom |
| Superchips Flashpaq F5 Pro 3874 | $448.95 | 4.5 · 8 | none | **NO pre-loaded tunes** |
| DiabloSport inTune i3 8200 | $448.95 | 4.5 · 18 | **D-770, D-802-19** | pre-loaded, 50-state |

### The finding

**Exactly one of five publishes a CARB EO number.** The i3 lists
`CARB EO Number(s): D-770 / D-802-19` and `Emissions: California EO Approved`.
The other four return nothing for CARB, Executive Order, EO#, 50-State or
emissions — all five terms searched on each page.

Both EO numbers were verified independently, not taken from the listing:
- **D-770** title read in full: *"Relating to Exemptions Under Section 27156 of
  the California Vehicle Code — DiabloSport inTune 12 CE, inTune 13 CE, inTune
  12, inTune 13, Predator 2, and Trinity 2 Programmers."* The i3 is **not named
  in that title**, which is precisely why the second number matters.
- **D-802-19** covers "GM V-8 Tunes... manufactured and marketed by Powerteq...
  and its subsidiaries DiabloSport, Edge Products, and Superchips."

Second finding: **the $448.95 "Pro" ships with zero pre-loaded tunes** and exists
to load HP Tuners dealer files, while the $377.99 SCT X4 is pre-loaded. "Pro"
means unlocked for custom files, not more in the box.

Third: the cheapest device ($268.95) is a **recalibrator, not a tuner** — 26–38
in. speedo correction, gear swaps, TPMS, no engine calibration.

### Deliberate choices

- **`CA Warning` was checked before it was written about, and kept out.** Every
  listing carries that badge; clicking it reads *"Cancer and Reproductive Harm"*
  — Proposition 65, unrelated to CARB. Conflating the two would have been a false
  emissions claim. The article says so explicitly to pre-empt the misreading.
- **Absence of an EO is reported as absence, not as prohibition.** The text says
  the listing does not let you confirm legality, and separately states the rule
  for parts with no applicable EO. It does not assert the four lack one.
- **No horsepower or torque figures for any device.** None publishes a dyno number
  for a specific application on the listing page.
- **Bully Dog's "not for use on applications with deleted emission controls"**
  framed as a restriction, not a compliance claim.
- **CARB's searchable EO database was unreachable** — ww2.arb.ca.gov restructured;
  `/applications/aftermarket-parts-database`, `/executive-orders-search`,
  `/msprog/aftermkt/...` all 404, and `ssl.arb.ca.gov/AftermarketParts/` returns
  "Request Rejected". The EO titles were verified via web search of the documents
  instead, and the failure is disclosed in the article's "could not verify".

### Photos

Five verified Pexels photos, each `/photo/<id>/` title read individually:
12271947, 4116193, 6870326, 12271949, 12271948. All OBD/diagnostic-tool
photography. Captions tie each to a spec field.

Note: a heredoc with a missing trailing newline silently swallowed three sidecars
into one file. Caught by `wc -l` (should have been 5 separate 1-line files, got
2 files with one 956 bytes long). Rewritten with Write.

### Operational

Articles 48, 49 **and** 50 were all held for this build — 48 and 49 are still
unpublished drafts from earlier runs. Build: 69 URLs unchanged, 0 hits for all
three slugs in sitemap, no pages, no photo directories, `docs/` byte-identical.

### Queue note for future runs

The supplied 5-item queue has now been stale six times running. Do not re-walk
it. Current published category counts: Engine 14, Exhaust 7, Suspension 5,
Brakes 5, Wheels & Tires 4, Tonneau & Bed 4, Electrical 4, Tuning 4 — plus
drafts 48 (Electrical), 49 (Wheels & Tires), 50 (Tuning). Once those publish,
the thinnest are Suspension and Brakes at 5 each.

---

## PUBLISHED — articles 48, 49, 50 (2026-11-19)

All three were flipped from `status: draft` to `status: published` and deployed.
Live sitemap went 69 -> 72 URLs, feed 48 -> 51 items, search index 47 -> 50.

| # | Page | Category |
|---|---|---|
| 48 | `/electrical/led-headlights-street-legal-dot.html` | Electrical |
| 49 | `/wheels-tires/load-range-ply-rating-guide.html` | Wheels & Tires |
| 50 | `/tuning/truck-tuner-carb-eo-guide.html` | Tuning |

Verified live after deploy: all three return 200, each serves its 5 `<img>`
blocks, sitemap 72 `<loc>`, feed 51 `<item>`. All three dated 2026-11-19, and
git confirms zero prior adds to `docs/` for any of them, so publish date and
first-existence agree.

### Deploy incident, and the lesson

The first Pages build for commit `0354370` errored with **duration 0** and the
API's only detail is `"Page build failed."`. Cause: I ran
`gh api -X POST repos/.../pages/builds` manually while GitHub's own automatic
build for the same push was already queued, producing two builds for one
commit; the loser errored instantly. Re-triggering cleanly built in the normal
time.

**Do not POST a Pages build after a push.** Pushing to `main` already queues
one. Only trigger manually if a deploy has genuinely stalled with no build in
flight, and check `pages/builds` for an existing entry on the same commit first.

The commit itself was sound throughout: 107 files, no non-ASCII filenames, all
15 image references resolving locally, `.nojekyll` tracked, 573 files in docs/.

### Updated category counts (published)

Engine 14, Exhaust 7, Suspension 5, Brakes 5, Wheels & Tires 5,
Tonneau & Bed 4, Electrical 5, Tuning 5.

Thinnest now: **Tonneau & Bed at 4**, then Suspension / Brakes / Wheels & Tires
/ Electrical / Tuning at 5 each. Next run should look at Tonneau & Bed, or at
Suspension and Brakes which have had no new article in this session.
