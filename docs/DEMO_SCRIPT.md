# GridLock — Demo Script

> Two presenter scripts: a **90-second** version and a **3-minute** version.
> Both are built on the official challenge dataset (`Projects_Overlaps.xlsx`)
> and its answer key. Every number below traces to
> [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md), [`METHODOLOGY.md`](METHODOLOGY.md),
> and [`COST_ESTIMATE.md`](COST_ESTIMATE.md). Nothing is invented.

Last updated: 2026-09-27

---

## Headline framing

**25 cross-utility pairs screened, 6 flagged.** Five DESC projects × five GPC
projects = 25 possible pairs; the screen flags 6 real coordination candidates
and correctly stays silent on the other 19. The 6 cluster into two geographic
corridors — Savannah/Okatie and Augusta/Thurmond.

---

## 90-second version

**(0:00–0:15) The problem.** Utilities plan transmission projects
independently. When two of them build within a few kilometres of each other on
overlapping schedules, neither usually knows — so each pulls its own permits,
mobilizes its own crews, and pays for a corridor twice. **FERC Order No. 1920
(2024)** now pushes exactly the opposite: coordinated regional transmission
planning. GridLock is a hackathon-sized version of that mandate.

**(0:15–0:35) What GridLock does.** It screens every cross-utility project pair
by closest-point distance and in-service-date gap. Under 40 km — about a crew's
morning drive from a staging yard — it flags the pair and ranks it by how close
the projects come, mapping distance to four coordination tiers: crossing, shared
land, shared logistics, shared crews. The decision is pure geometry and calendar
math; no AI makes the call.

**(0:35–0:55) The result.** Twenty-five pairs screened, six flagged. They fall
into two corridors. In the **Savannah/Okatie** corridor, DESC's Jasper–Okatie
line sits about 5.6 miles from Georgia Power's McIntosh–Purrysburg work — inside
the shared-crew tier. In the **Augusta/Thurmond** corridor, DESC's Hooks–Thurmond
rebuild is about 4 miles from GPC's Evans Primary–Thurmond Dam rebuild.

**(0:55–1:20) Cost impact.** Anchoring on a real Dominion filing — the Okatie
230–115 kV / Jasper–Yemassee fold-in at about **$11.1 million** — a conservative,
clearly-labeled illustration shows what a shared right-of-way or shared crew
mobilization could be worth. These are illustrative figures, not verified
savings.

**(1:20–1:30) Close.** GridLock is a **decision-support and screening tool for
human review** — it surfaces where two utilities should talk. It does not make
automated construction decisions.

---

## 3-minute version

**(0:00–0:25) The coordination problem + FERC Order 1920.** Electric utilities
file long-term transmission plans independently. Historically they planned in
isolation, which produced duplicated, inefficient work where their footprints
meet. **FERC Order No. 1920 (2024)** now requires more coordinated regional
transmission planning. The practical question underneath the rule is simple: are
two neighboring utilities about to build near each other, at the same time,
without knowing it? DESC (Dominion Energy South Carolina) and Georgia Power share
the Savannah River border and sit in the same regional planning forum, so the
overlap is real, not hypothetical.

**(0:25–0:55) How GridLock screens.** GridLock ingests publicly filed
future-construction projects from both utilities — no CEII, public filings only —
and compares every cross-utility pair on two signals:
- **Primary: closest-point distance.** Minimum distance between full project
  geometries, not center-to-center. Under 40 km (≈ 25 mi) flags the pair; closer
  ranks higher. Distance maps to four tiers: crossing → shared land (<1.6 km) →
  shared logistics (<8 km) → shared crews (<40 km).
- **Secondary: in-service date gap in days.** Reported separately, so a
  physically close pair that is years apart on the calendar is visible as such.

**(0:55–1:00) The headline.** Twenty-five cross-utility pairs screened, six
flagged, in two corridors.

**(1:00–1:45) Savannah/Okatie corridor walkthrough — DESC_3, DESC_5 vs GPC_2,
GPC_3.** This is the dense corridor. DESC's **Jasper–Okatie 230 kV #2** (DESC_3,
in-service 2025) and **Okatie–Bluffton 115 kV rebuild** (DESC_5, in-service 2025)
sit right next to Georgia Power's Savannah-area work: **McIntosh–Purrysburg 230 kV
reactors** (GPC_2, 2026) and **Goshen–McIntosh 115 kV rebuild** (GPC_3, 2027).

Four of the six flagged overlaps live here:
- DESC_3 ↔ GPC_2 — about **5.65 mi**, in-service gap **152 days**. The closest
  and best-timed pair in the whole dataset.
- DESC_3 ↔ GPC_3 — about **7.55 mi**, gap **517 days**.
- DESC_5 ↔ GPC_2 — about **14.34 mi**, gap **365 days**.
- DESC_5 ↔ GPC_3 — about **14.81 mi**, gap **730 days**.

All four are inside 40 km with in-service dates within roughly two years — a
genuine coordination cluster around Okatie and McIntosh.

**(1:45–2:15) Augusta/Thurmond corridor walkthrough — DESC_1, DESC_2 vs GPC_1.**
Up near the Georgia–South Carolina line at Thurmond, DESC's **Stevens Creek–Hooks
rebuild** (DESC_1, 2024) and **Hooks–Thurmond 115 kV tie rebuild** (DESC_2, 2024)
sit close to Georgia Power's **Evans Primary–Thurmond Dam #5 115 kV rebuild**
(GPC_1, 2033):
- DESC_2 ↔ GPC_1 — about **4.09 mi**, gap **3074 days**.
- DESC_1 ↔ GPC_1 — about **8.01 mi**, gap **3074 days**.

These two are geographically tight but about **eight years apart** on the
calendar. That is exactly why GridLock reports the day gap **separately** from
distance — a planner sees the proximity *and* the timing mismatch, and decides
accordingly. It is a screening signal, not an instruction.

**(2:15–2:35) The 19 that don't flag.** GPC_4 (Mitchell–North Tifton, southwest
Georgia), GPC_5 (Jesup–Ludowici, southeast Georgia), and DESC_4 (Queensboro–Ft
Johnson, Charleston) produce no overlaps. Most of the dataset correctly does not
overlap — isolating the few real matches is the entire point.

**(2:35–2:55) Cost impact (illustrative).** Anchor on the real Dominion filing:
the Okatie 230–115 kV / Jasper–Yemassee fold-in at about **$11,116,933**, with
additional anchors like Queensboro–Ft Johnson (~$5.4M) and Union Pier 115 Sub Tap
(~$5.3M). For one flagged Savannah/Okatie overlap we show, in three clearly
separated layers — actual project cost, an assumed shareable share, and the
resulting estimated potential savings — a conservative illustration of what
coordination could be worth. These are **illustrative figures, not verified
savings.**

**(2:55–3:00) Close.** GridLock is a **decision-support and screening tool for
human review**. It flags where two utilities should coordinate and shows the
evidence; it does **not** make automated construction decisions. Humans decide.

---

## Presenter notes

- Distances and day gaps above are the official answer-key values from
  `Projects_Overlaps.xlsx` Sheet 2 (center-to-center miles). GridLock's engine
  reports closest-point distance, which ranks the same corridors but is a more
  faithful measure — see [`METHODOLOGY.md`](METHODOLOGY.md).
- Keep the cost numbers in their three layers (actual / assumed / estimated).
  Never present the illustrative savings as a verified figure. See
  [`COST_ESTIMATE.md`](COST_ESTIMATE.md).
- If asked about the *pipeline* track (DESC-001..019 / GPC-001..009), be honest:
  its approved set is empty and the engine returns `[]` by design — see
  [`DATA_LIMITATIONS.md`](DATA_LIMITATIONS.md) and [`DEMO_FLOW.md`](DEMO_FLOW.md).

---

Related: [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md) · [`METHODOLOGY.md`](METHODOLOGY.md)
· [`COST_ESTIMATE.md`](COST_ESTIMATE.md) · [`DEMO_FLOW.md`](DEMO_FLOW.md)
