# GridLock — Demo Script

> Two presenter scripts: a **90-second** version and a **3-minute** version.
> Both are built on the official challenge dataset (`Projects_Overlaps.xlsx`)
> and are computed by the **offline reference engine** (`official_engine.py`),
> not the live production API. Every number below traces to
> [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md), [`METHODOLOGY.md`](METHODOLOGY.md),
> [`COST_ESTIMATE.md`](COST_ESTIMATE.md), and Agent 1's
> [`OFFICIAL_DATASET_ENGINE.md`](OFFICIAL_DATASET_ENGINE.md). Nothing is invented.

Last updated: 2026-09-27

---

## Which result track is being demonstrated

GridLock has several distinct result surfaces; keep them separate when
presenting:

1. **Official reference engine (this script).** `official_engine.py` computes
   **closest-point** distances over the 10 official challenge projects and
   produces the **6 flagged pairs** shown below. This is an offline analysis,
   not the live API.
2. **Spreadsheet answer key.** `Projects_Overlaps.xlsx` Sheet 2 lists the same 6
   qualifying pairs but with **center-to-center** miles — a different metric. We
   show those in parentheses for reference only.
3. **Conservative production API.** `GET /opportunities` returns `[]` today
   because nothing has been human-approved. That is the correct, honest answer.
4. **Frontend candidate/proxy display.** The map can render inferred candidate
   geometry (e.g. **32 of 34** proposed pipeline records carry no geometry and
   the two that do are proxy points) for display only — never as approved
   opportunities.

Distances quoted in the walkthroughs are **closest-point (track 1)**, with the
Sheet 2 center-to-center value (track 2) in parentheses.

---

## Accuracy note (use this exact wording, and always include the last sentence)

> Distances are closest-point, computed from published endpoint coordinates.
> Against a WGS 84 geodesic reference, model error within 40 km is under 0.35%
> (about 120 m at most). No tier assignment or qualifying pair changes under any
> of the models we tested.

---

## Headline framing

**25 cross-utility pairs screened, 6 flagged.** Five DESC projects × five GPC
projects = 25 possible pairs; the reference engine flags 6 and correctly stays
silent on the other **19 pairs** (three projects — DESC_4, GPC_4, GPC_5 — appear
in no overlap at all). The 6 cluster into two geographic corridors —
Savannah/Okatie and Augusta/Thurmond.

---

## 90-second version

**(0:00–0:15) The problem.** Utilities plan transmission projects
independently. When two of them build within a few kilometres of each other on
overlapping schedules, neither usually knows — so each pulls its own permits,
mobilizes its own crews, and pays for a corridor twice. **FERC Order No. 1920
(2024)** now pushes exactly the opposite: coordinated regional transmission
planning. GridLock is a hackathon-sized version of that mandate.

**(0:15–0:35) What GridLock does.** Using the offline reference engine, it
screens every cross-utility project pair by **closest-point distance** and
in-service-date gap. Under **40 km (≈ 24.85 mi)** — about a crew's morning drive
from a staging yard — it flags the pair and ranks it by how close the projects
come, mapping distance to four coordination tiers: crossing, shared land, shared
logistics, shared crews. The decision is pure geometry and calendar math; no AI
makes the call.

**(0:35–0:55) The result.** Twenty-five pairs screened, six flagged, in two
corridors. The tightest is **DESC_2 Thurmond Sub ↔ GPC_1 THURMOND DAM #5**, which
computes to **0 km — a crossing** — because both projects list the same Thurmond
endpoint coordinate; we cannot confirm from the published data whether they
physically meet, so it is flagged for coordination review. Around Savannah/Okatie,
DESC_3 ↔ GPC_2 is about **3.0 mi** apart with only a **152-day** in-service gap —
close and well-timed.

**(0:55–1:20) Cost impact.** Anchoring on a real Dominion filing — the Okatie
230–115 kV / Jasper–Yemassee fold-in at about **$11.1 million** — a conservative,
clearly-labeled illustration shows what a shared right-of-way or shared crew
mobilization could be worth. These are illustrative figures, not verified
savings.

**(1:20–1:30) Close.** These six come from the offline reference engine; the
production API returns `[]` today because nothing is human-approved. GridLock is
a **decision-support and screening tool for human review** — it surfaces where
two utilities should talk. It does not make automated construction decisions.

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

**(0:25–0:55) How GridLock screens.** Everything shown comes from the **offline
reference engine** (`official_engine.py`) running on the 10 official projects
copied verbatim from `Projects_Overlaps.xlsx` — no CEII, public filings only. It
compares every cross-utility pair on two signals:
- **Primary: closest-point distance.** Minimum distance between full project
  geometries, not center-to-center. The gate is **40 km (40 000 m ≈ 24.85 mi)** —
  the challenge docx phrases it as 25 mi (≈ 40.23 km); GridLock implements the
  40 km form. Closer ranks higher. Distance maps to four tiers: crossing → shared
  land (<1.6 km) → shared logistics (<8 km) → shared crews (<40 km).
- **Secondary: in-service date gap in days.** Reported separately, so a
  physically close pair that is years apart on the calendar is visible as such.

> Distances are closest-point, computed from published endpoint coordinates.
> Against a WGS 84 geodesic reference, model error within 40 km is under 0.35%
> (about 120 m at most). No tier assignment or qualifying pair changes under any
> of the models we tested.

**(0:55–1:00) The headline.** Twenty-five cross-utility pairs screened, six
flagged, in two corridors.

**(1:00–1:45) Savannah/Okatie corridor walkthrough — DESC_3, DESC_5 vs GPC_2,
GPC_3.** This is the dense corridor. DESC's **Jasper–Okatie 230 kV #2** (DESC_3,
in-service 2025) and **Okatie–Bluffton 115 kV rebuild** (DESC_5, in-service 2025)
sit near Georgia Power's Savannah-area work: **McIntosh–Purrysburg 230 kV
reactors** (GPC_2, 2026) and **Goshen–McIntosh 115 kV rebuild** (GPC_3, 2027).

Four of the six flagged overlaps live here (closest-point; Sheet 2
center-to-center in parentheses):
- DESC_3 ↔ GPC_2 — about **3.0 mi (4.8 km)**, in-service gap **152 days** — the
  best-timed pair (sheet center-to-center 5.65 mi).
- DESC_3 ↔ GPC_3 — about **3.4 mi (5.5 km)**, gap **517 days** (sheet 7.55 mi).
- DESC_5 ↔ GPC_2 — about **8.4 mi (13.6 km)**, gap **365 days** (sheet 14.34 mi).
- DESC_5 ↔ GPC_3 — about **8.8 mi (14.2 km)**, gap **730 days** (sheet 14.81 mi).

All four are inside 40 km with in-service dates within roughly two years — a
genuine coordination cluster around Okatie and McIntosh.

**(1:45–2:15) Augusta/Thurmond corridor walkthrough — DESC_1, DESC_2 vs GPC_1.**
Up near the Georgia–South Carolina line at Thurmond, DESC's **Stevens Creek–Hooks
rebuild** (DESC_1, 2024) and **Hooks–Thurmond 115 kV tie rebuild** (DESC_2, 2024)
sit close to Georgia Power's **Evans Primary–Thurmond Dam #5 115 kV rebuild**
(GPC_1, 2033):
- DESC_2 Thurmond Sub ↔ GPC_1 THURMOND DAM #5 — closest-point **0.0 km, crossing
  tier**: both projects list the same Thurmond endpoint coordinate. We cannot
  confirm from the published data whether the two facilities physically meet, so
  the pair is flagged for coordination review rather than asserted as a touch.
  In-service gap **3074 days** (sheet center-to-center 4.09 mi).
- DESC_1 ↔ GPC_1 — about **6.9 mi (11.1 km)**, gap **3074 days** (sheet 8.01 mi).

These two are geographically tight but about **eight years apart** on the
calendar. That is exactly why GridLock reports the day gap **separately** from
distance — a planner sees the proximity *and* the timing mismatch, and decides
accordingly. It is a screening signal, not an instruction.

**(2:15–2:35) The pairs that don't flag.** Of the 25 pairs, 6 flag and **19 do
not**. Three projects appear in no overlap at all: GPC_4 (Mitchell–North Tifton,
southwest Georgia), GPC_5 (Jesup–Ludowici, southeast Georgia), and DESC_4
(Queensboro–Ft Johnson, Charleston). Most of the dataset correctly does not
overlap — isolating the few real matches is the entire point. A caveat: DESC_1,
DESC_2, DESC_4, and GPC_2 list only one published endpoint, so they are modeled
as points and their closest-point distances are **upper bounds** — a published
route could only bring pairs closer.

**(2:35–2:55) Cost impact (illustrative).** Anchor on the real Dominion filing:
the Okatie 230–115 kV / Jasper–Yemassee fold-in at about **$11,116,933**, with
additional anchors like Queensboro–Ft Johnson (~$5.4M) and Union Pier 115 Sub Tap
(~$5.3M). Note the anchor is a nearby Okatie-area DESC filing used as a dollar
reference, not itself one of the six flagged pair projects. For one flagged
Savannah/Okatie overlap we show, in three clearly separated layers — actual
project cost, an assumed shareable share, and the resulting estimated potential
savings — a conservative illustration of what coordination could be worth. These
are **illustrative figures, not verified savings.**

**(2:55–3:00) Close.** These six overlaps come from the offline reference engine;
the production API returns `[]` today because nothing is human-approved, and the
frontend shows candidate/proxy geometry for display only. GridLock is a
**decision-support and screening tool for human review**. It flags where two
utilities should coordinate and shows the evidence; it does **not** make automated
construction decisions. Humans decide.

---

## Presenter notes

- Walkthrough distances are **closest-point** values from the offline reference
  engine (`official_engine.py`); the parenthetical miles are the
  `Projects_Overlaps.xlsx` Sheet 2 **center-to-center** answer-key values, shown
  for reference only. The two metrics differ; do not present the sheet miles as
  engine output. See [`METHODOLOGY.md`](METHODOLOGY.md) and
  [`OFFICIAL_DATASET_ENGINE.md`](OFFICIAL_DATASET_ENGINE.md).
- The gate is **40 km (40 000 m ≈ 24.85 mi)**, not 25 mi. Do not present the two
  as interchangeable.
- When quoting the accuracy figure, always include the final sentence: "No tier
  assignment or qualifying pair changes under any of the models we tested."
- Keep the cost numbers in their three layers (actual / assumed / estimated).
  Never present the illustrative savings as a verified figure. See
  [`COST_ESTIMATE.md`](COST_ESTIMATE.md).
- If asked about the *pipeline* track (DESC-001..019 / GPC-001..009), be honest:
  its approved set is empty and the engine returns `[]` by design — see
  [`DATA_LIMITATIONS.md`](DATA_LIMITATIONS.md) and [`DEMO_FLOW.md`](DEMO_FLOW.md).

---

Related: [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md) · [`METHODOLOGY.md`](METHODOLOGY.md)
· [`COST_ESTIMATE.md`](COST_ESTIMATE.md) · [`OFFICIAL_DATASET_ENGINE.md`](OFFICIAL_DATASET_ENGINE.md)
· [`DEMO_FLOW.md`](DEMO_FLOW.md)
