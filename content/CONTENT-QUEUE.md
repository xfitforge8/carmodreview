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
| 10 | Turbo Miata build order | **266K views** on a turbo Miata build; **115K** on ND2 Miata vs supercharged BRZ. Lower priority: the parts costs are build-dependent and the verified-price surface is thinner | research |

Also seen but lower priority: `silverado transmission shudder / thermostat bypass /
cooler line` (13-deep cluster, repair intent), `duramax 3.0 oil change / fuel filter
change / diesel sound`, `bed rack with tonneau cover` (12-deep, accessory-fitment).

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

## Standing rules for every article

- Drafts only. `status: draft`. Nothing publishes without the owner.
- Every number sourced and dated, read live via BrowserOS Neo. Never invented.
- Never use WebFetch — BrowserOS Neo MCP at `http://127.0.0.1:9211/mcp`.
- Draft-hold recipe before any build: move `19-*` `24-*` `25-*` (and any newer
  drafts) to `/tmp`, `python3 build.py`, move back. Then confirm the slug appears
  **zero** times in `docs/sitemap.xml`.
- Close browser tabs when done.
- Disclosure line at the end of every article.
