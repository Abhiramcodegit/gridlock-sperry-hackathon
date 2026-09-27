# GridLock — Rubric Evidence Matrix (READ-ONLY audit)

**Date:** 2026-09-27 · **Auditor:** integration/rubric-audit agent.
No criterion is marked met without evidence. Where evidence is partial or
unverifiable in this environment, it is stated plainly rather than assumed.

The rubric is the Sperry "Gridlock" challenge brief (there is no separate rubric
file in the repo). Its graded items are the two **Required** deliverables and
the **Bonus**, plus the implicit correctness rules (40 km gate, closest-point,
timeline as secondary, "most pairs should NOT overlap", public-data-only/CEII).

---

## Required / Bonus deliverables

| # | Rubric requirement | Satisfying feature / file | Current proof | Gap or ambiguity | Recommended demo evidence |
|---|---|---|---|---|---|
| R1 | Interactive UI showing **both utilities' planned projects**, overlaps highlighted; pan/zoom/click | `frontend/src/App.jsx` (Agent 2 basemap branch): OpenFreeMap Liberty basemap, utility-colored project layers, dashed closest-point segment overlay, Navigation/Scale/Fit/Reset controls | Unit tests 9/9; `npm run build` exit 0; basemap style HTTP 200 with 111 layers incl. state boundaries | **Actual GPU render UNVERIFIED here**; **worker bug present on the branch** (map may hang); overlaps are highlighted only when opportunity records are present in the UI's expected shape | Confirm in a **real GPU browser**: projects for both DESC + GPC render, a flagged overlap's closest-point segment draws, pan/zoom/click works. Fix worker bug first. |
| R2 | **Ranked list** of top coordination opportunities | Sidebar ranked `<ol data-testid="opportunity-list">` in `App.jsx`; ranking + tiers from `official_engine.find_opportunities()` (Agent 1) / `engine.py` (main) | Agent 1 independently reproduced: **6 opportunities, ranked closest-first**, with 4-tier labels; day gap shown separately | UI reads a **different field shape** than Agent 1's engine emits (data-contract mismatch — see INTEGRATION_AUDIT §2.1). Need an adapter or use the API shape. | Show the 6 ranked pairs closest-first with tier + separate day-gap; state metric is **closest-point**. |
| B1 | **Bonus:** rough cost/impact estimate for ≥1 flagged overlap | `docs/COST_ESTIMATE.md` (Agent 4) | 3-layer estimate anchored on a real filed Dominion cost (~$11,116,933), labeled Fact/Assumption/Illustrative; estimator ships disabled | Cost anchor is a **nearby** DESC project, not strictly one of the 6-overlap projects; estimate is illustrative (correctly labeled) | Walk the Savannah/Okatie corridor; show the actual filed cost, the stated assumption, and the "up to" illustrative savings — clearly not a promised number. |

---

## Implicit correctness rules (the challenge's "getting it right")

| # | Rule | Evidence | Status |
|---|---|---|---|
| C1 | Geographic overlap gate is **< 40 km / 25 mi** | `config.py CANDIDATE_RADIUS_M = 40000.0`; Agent 1 `official_engine.GATE_M = 40_000.0`; independent recompute used 40 km | **MET** — one gate, correctly ≈ 25 mi (docs state 40 km ≈ 24.85 mi; no double-gate). |
| C2 | Distance is **closest-point between geometries**, not center-to-center | `official_engine.closest_point_distance_m()` uses shapely `.distance()` in UTM 17N; METHODOLOGY documents the distinction | **MET** — and kept explicitly distinct from the xlsx center-to-center oracle. |
| C3 | **Ranked by distance**, closer = higher value; 4 tiers | `official_engine` sorts ascending by distance; `TIERS` = crossing/<1.6km/<8km/<40km with coordination actions | **MET** — verified in output and code. |
| C4 | **Timeline** is a **secondary** signal, reported alongside distance, not blended | `day_gap` field reported separately; METHODOLOGY states unknown windows → NULL, never silently "overlapping" | **MET** — day gaps 3074/152/517/3074/365/730 reproduced. |
| C5 | **Most pairs should NOT overlap** | 25 pairs → only 6 qualify; 19 correctly rejected; DATA_PROVENANCE explains far-apart GPC_4/GPC_5/DESC_4 | **MET** — the healthy-negative outcome the brief expects. |
| C6 | **Public data only, no CEII** | DATA_PROVENANCE no-CEII section; sources are the challenge PDFs, xlsx, SCRTP/GPC public pages, OSM | **MET** by documentation; sources are public filings. |
| C7 | At least **two overlapping utilities** (DESC + GPC) | 5 DESC + 5 GPC in the official dataset; cross-utility pairing only (DESC_* × GPC_*) | **MET.** |

---

## Honest caveats a judge should hear (not rubric failures, but integrity points)

1. **Two datasets, one story.** The demo-grade 6 overlaps come from the
   challenge-supplied official dataset (Track A). The team's own strict
   ingestion pipeline (Track B) currently approves 0 rows and correctly returns
   no opportunities. Both are real; do not let the UI blur them (see the
   "32 of 34" number-collision note in INTEGRATION_AUDIT §7).
2. **DESC_2 × GPC_1 = 0 m is a shared-coordinate artifact**, not verified
   touching infrastructure — two differently-named substations were given the
   same coordinate in the source spreadsheet. Present it as "coincident source
   coordinate," not "the lines physically cross."
3. **Endpoint-only projects (DESC_1, DESC_2, DESC_4, GPC_2)** are single points;
   their distances are **upper bounds** on true line-to-line proximity.
4. **PostGIS engine** is CI-attested, not verified on the dev machine
   (no local Postgres/Docker available). Confirm the CI run for the 4 integration
   tests before claiming "24 passed, 0 skipped".
5. **Map render** is unverified in this environment; confirm on a real GPU.

---

## What is genuinely strong (evidence-backed advantages)

- **Independent reproducibility:** the official dataset rebuilds deterministically
  and byte-identically from the source spreadsheet, and the 6 qualifying pairs
  were reproduced by an independent recomputation that did not use the team's own
  engine.
- **Auditability:** every quantitative doc claim traces to a repository source or
  a public filing; distance metric and geometry limits are disclosed rather than
  hidden.
- **Honest negatives:** the tool reports 0 where 0 is correct (Track B) and 6
  where 6 is correct (Track A), and separates the primary (distance) from the
  secondary (timeline) signal instead of a single blended score.

These advantages come from the **produced evidence, tests, provenance, and
independent verification** — not from the fact that multiple agents were used.
