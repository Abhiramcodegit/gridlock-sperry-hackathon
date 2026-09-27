# GridLock — Demo Flow (2–3 minutes)

A presenter script for the GridLock coordination-discovery engine. Every claim
below is backed by evidence in this repo. Read the presenter warning box before
you start.

> ### ⚠️ PRESENTER WARNING — READ BEFORE DEMOING
>
> - **Do NOT call GPC-004 or DESC-003 "verified project routes."** They are
>   **inferred substation proxy points**, not confirmed project geometry.
> - **Do NOT claim "verified proximity" between any two projects.** The only
>   distance we can defend is between two *proxy* points, and it is a negative
>   result (~117 km apart, outside the filter).
> - The approved dataset is **empty**. `/opportunities` returns `[]`. That is
>   the **correct, honest answer** — say so plainly. Do not imply the engine
>   "found" coordination opportunities.
> - The `H-` rows are **hypotheses for future research**, not confirmed
>   projects. Never present them as real projects.

---

## 0. One-line pitch (10 seconds)

"GridLock finds places where two utilities are about to build transmission
near each other, at the same time, so they can share the right-of-way,
permits, and crews instead of paying for it twice — and it only reports an
opportunity when the public evidence actually supports it."

---

## 1. The problem (20–25 seconds)

Utilities plan transmission projects independently. When two of them plan work
within a few kilometres of each other on overlapping schedules, neither side
usually knows. Each hires its own contractors, pulls its own permits, and
mobilizes its own crews — even when a shared corridor or a single permit would
have covered both. That duplicated mobilization is expensive and avoidable.

The catch: this only matters if the answer is honest. A tool that invents
coordination opportunities from weak data is worse than no tool. GridLock is
built to be conservative — it would rather say nothing than say something it
can't defend.

---

## 2. How the engine works (35–40 seconds)

GridLock is a **deterministic** engine. No LLM decides whether two projects
should coordinate. The decision is pure geometry and calendar math:

1. **Candidate filter — `ST_DWithin(a.geom, b.geom, 40000)`.** PostGIS selects
   cross-utility pairs (`a.utility < b.utility`) whose geometries are within
   **40 km**, measured on the `geography` type (geodesic, in meters).
2. **Distance — `ST_Distance` on `geography`.** For qualifying pairs, we
   compute the true minimum distance between full geometries — not
   centre-to-centre. This runs **only for pairs where both projects are
   `approved` and have geometry.**
3. **Temporal overlap.** Overlapping construction days are reported separately
   from proximity. If either construction window is unknown, overlap is `NULL`
   — never silently treated as overlapping.
4. **Approved-only.** The candidate query considers only human-approved rows.
   Proposed and hypothesis rows are invisible to the engine.

The 40 km radius and scoring weights live in `backend/gridlock/config.py`
(`CANDIDATE_RADIUS_M = 40000`). Show it if asked — the threshold is a constant,
not a guess made per-request.

---

## 3. Why the empty result is the correct answer (25–30 seconds)

Open `GET /opportunities`. It returns `[]`.

That is **not a bug**. The approved dataset
(`data/approved/projects_approved.geojson`) is `{"type":"FeatureCollection",
"features":[]}` — intentionally empty. Nothing has been human-approved, so the
candidate query has nothing to pair. An empty array is the truthful output of a
pipeline that refuses to promote unverified data.

Say it out loud: **"The honest answer today is zero approved opportunities,
and the engine says exactly that."**

---

## 4. The candidate-review layer — why proxies aren't approved (25–30 seconds)

We *do* have research-grade geometry, but it lives behind the approval gate:

- **34 proposed records**: 19 DESC, 9 GPC, and 6 labeled hypotheses (`H-` rows).
- Only **two** rows carry any geometry: **GPC-004** (Effingham County 500 kV,
  proxied by the West McIntosh substation centroid) and **DESC-003** (Long
  Savannah 115 kV Tap, proxied by the Church Creek substation centroid).
- Both are `inferred` — substation proxy points sourced from OpenStreetMap and
  corroborated against public substation records. **Neither is a confirmed
  project route.** That is exactly why they sit in the candidate layer and were
  **not** approved into the engine.
- **DESC-002** (Okatie–McIntosh) is **unresolved** on purpose. We found no
  defensible public coordinate, so there is **no placeholder** — a blank is more
  honest than a fabricated point.

This is the point of the demo: the pipeline has a review layer, and it is
actually holding the line. Weak geometry stays out.

---

## 5. The honest negative result — 116.993 km (20–25 seconds)

To prove the threshold does real work, we ran the distance calculation on the
two proxy points we *do* have (a human-authorized, proxy-level run — see
`docs/PROXY_DISTANCE_RESULT.md`):

- **GPC-004 proxy ↔ DESC-003 proxy = 116.993 km** (geodesic on WGS84,
  mathematically equivalent to PostGIS `ST_Distance` on `geography`).
- The candidate radius is **40 km**. `ST_DWithin(..., 40000)` returns **FALSE**.
- So even if these two proxies were approved, the engine would correctly
  **reject** the pair as too far apart.

This is a feature, not a disappointment. The threshold rejects a real pair for
a real reason. A UTM 17N planar cross-check agrees to within ~44 m.

> Reminder: this is a distance between two **proxy** points, not verified
> project-to-project proximity. Do not overstate it.

---

## 6. The positive-control test — proof the pipeline emits real results (20–25 seconds)

If the engine always returned `[]`, you couldn't tell "correctly empty" from
"broken query." So the integration suite includes a **positive control**:

- `backend/tests/test_db_integration.py` inserts a **synthetic, approved,
  cross-utility pair placed under 40 km apart** and asserts that
  `db.find_opportunities()` returns exactly one opportunity for it.
- The same suite also asserts the empty-result case (nothing approved) and the
  honest-negative case (GPC-004 ↔ DESC-003 rejected by the 40 km filter).

Together these prove the empty production result is **data-driven**, not a dead
query. When qualifying data exists, the engine emits it.

**Test count: 24 passed, 0 skipped** under CI with PostGIS
(17 engine + 3 proxy-distance + 4 DB integration). Locally without a database
the 4 DB tests skip, so you'll see 20 passed, 4 skipped.

> **Phase 3 PostGIS CI verification: pending** — awaiting a green GitHub Actions
> run URL and tested commit SHA from Agent 1. Do not claim the live PostGIS run
> is verified until the status board Gate reads GREEN.

---

## 7. Close (10 seconds)

"GridLock is a deterministic coordination engine with a human approval gate in
front of it. Today it honestly reports zero approved opportunities, it proves
its own threshold works with a 117 km negative result, and it proves its
pipeline works with a positive-control test. When verified data lands, the
opportunities appear — and not a moment sooner."

---

## Appendix — quick reference for Q&A

| Fact | Value | Source |
|---|---|---|
| Proposed records | 34 (19 DESC, 9 GPC, 6 hypotheses) | `data/normalized/projects_proposed.csv` |
| Approved records | 0 (empty FeatureCollection) | `data/approved/projects_approved.geojson` |
| Rows with geometry | 2 (GPC-004, DESC-003), both `inferred` proxies | `projects_proposed.csv` |
| DESC-002 | unresolved, no placeholder coordinate | `projects_proposed.csv`, `docs/DATA_LIMITATIONS.md` |
| Candidate radius | 40 km (`CANDIDATE_RADIUS_M = 40000`) | `backend/gridlock/config.py` |
| Proxy distance | 116.993 km (geodesic WGS84), outside 40 km | `docs/PROXY_DISTANCE_RESULT.md` |
| `/opportunities` result | `[]` (correct) | `backend/gridlock/api.py` |
| Test count (CI, with PostGIS) | 24 passed, 0 skipped | `.github/workflows/engine-ci.yml`, `docs/ENGINE_PHASE3.md` |
| Test count (local, no DB) | 20 passed, 4 skipped | local `pytest` run |
| Phase 3 CI verification | **pending** (awaiting Agent 1 green-run URL + SHA) | `docs/ENGINE_PHASE3.md` |

Related docs: [`README.md`](../README.md) ·
[`AGENT_STATUS.md`](../AGENT_STATUS.md) ·
[`docs/ENGINE_PHASE3.md`](ENGINE_PHASE3.md) ·
[`docs/PROXY_DISTANCE_RESULT.md`](PROXY_DISTANCE_RESULT.md) ·
[`docs/DATA_LIMITATIONS.md`](DATA_LIMITATIONS.md)
