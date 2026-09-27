# GridLock — Data Limitations

Last updated: 2026-09-27 (Phase 3 verified; demo-readiness update)

> The Checkpoint 1 provenance notes are retained below for history. Where they
> conflict with the 2026-09-27 update section, the update section wins.

## What the proposed dataset contains

- 19 unique DESC projects from the **Current DESC Transmission Expansion Plans** section of the SCRTP March 5, 2025 presentation.
- 9 Georgia Power projects from the public Transmission Expansion & Upgrades page.
- Record-level source URL, source title/date, source page or web marker, excerpt, review state, CEII check flag, and last-verification date.
- 6 explicitly labeled hypothesis rows retained separately from source-backed proposals.

## What it does not contain

- Approved production records: every source-backed row remains `review_status=proposed` pending human approval.
- Construction windows: the reviewed sources do not provide both construction start and end dates.
- Per-project Georgia Power in-service dates: the listing provides project names, counties/regions, and types, but not record-specific dates.
- Verified distance results: no approved cross-utility pair with geometry exists, so `ST_DWithin` / `ST_Distance` produce no verified opportunity.

## Source correction

The earlier source manifest mixed Santee Cooper committed facilities from PDF pages/slides 24/50 with the DESC project section on pages/slides 30-48. The normalized `DESC-*` records now use only the DESC section. The Santee Cooper records may be added later under a separate utility code after a dedicated extraction and review.

The DESC section yields 19 unique records, not 18: six detailed project pages and fourteen list entries, with Long Savannah appearing in both places and deduplicated once.

## Candidate-pair caution

`GPC-004 Effingham County 500 kV` and DESC projects containing Bluffton, Okatie, or Long Savannah are geographic research leads only. County/name proximity does not prove that two project geometries are within 40 km. The product must not display such a pair as verified until source-backed geometries are approved and the deterministic engine computes the minimum geometry distance.

## Remaining gate

1. Human review of all 28 source-backed proposed records.
2. Decide whether to add the live-page `Tomochichi - Towaliga River 230 kV` record after a matching raw source capture is stored.
3. Locate and verify public geometry sources.
4. Resolve the schema mismatch: proposed records intentionally permit blank geometry, while `db/schema.sql` currently defines production `geom geography NOT NULL`.
5. Promote only approved records into `data/approved/projects_approved.geojson` and the production database.

---

## Update - 2026-09-27 (Phase 3 verified; demo-readiness limitations)

This section supersedes the earlier notes where they conflict.

### The approved project set is empty

`data/approved/projects_approved.geojson` is `{"type":"FeatureCollection","features":[]}`. Nothing has been human-approved. The deterministic engine evaluates approved rows only, so `GET /opportunities` returns `[]` - the correct, honest answer, not a bug.

### Proposed records are not approved opportunities

`data/normalized/projects_proposed.csv` holds **34 proposed records** (19 DESC, 9 GPC, 6 labeled `H-` hypotheses). "Proposed" means captured with provenance and awaiting human review. A proposed record is not an approved project and not a coordination opportunity. The `H-` hypothesis rows are research guesses and are never presented as confirmed projects.

### Candidate geometry is temporary frontend fixture data

Any geometry rendered by the frontend static files (`frontend/public/static/`) is candidate / fixture data **for display only**. It is not promoted, not approved, and not an engine input.

### Proxies are points, not routes or verified substations

Two proposed rows carry geometry: **GPC-004** (West McIntosh substation centroid) and **DESC-003** (Church Creek substation centroid). Both are `inferred` **single points** derived from public OpenStreetMap data. They are **not** confirmed project routes, **not** verified project endpoints, and **not** confirmed as the substations a project will use. Never call them verified routes, verified substations, or verified proximity.

### 116.993 km is a proxy-point diagnostic negative

The distance between the GPC-004 and DESC-003 proxy points is **116.993 km** (geodesic WGS84; see [PROXY_DISTANCE_RESULT.md](PROXY_DISTANCE_RESULT.md)). This is a diagnostic figure on two inferred points - not a verified project-to-project distance, and not proof about whether the real facilities can coordinate.

### 40 km is the eligibility cutoff

The candidate radius is **40 km** (`CANDIDATE_RADIUS_M = 40000` in `backend/gridlock/config.py`; `ST_DWithin(..., 40000)` in `db/schema.sql`). The 40 km cutoff and the 1.6 km / 8 km / 40 km coordination tiers are **parameters defined by the challenge**, not values GridLock derived or tuned.

### GPC-004 <-> DESC-003 is not eligible

At 116.993 km the pair is far beyond 40 km, so `ST_DWithin(..., 40000)` returns FALSE. The pair is **not eligible** as a coordination candidate - the intended behavior of the filter, shown against the only geometry we have.

### No real proxy receives a tier, opportunity line, or savings claim

Because nothing is approved and the only geometry pair is ineligible, **no real proposed record is assigned a coordination tier, drawn as an opportunity / closest-point line, or given any cost-savings figure**. Tiers, opportunity segments, and savings appear only for the synthetic positive-control fixture in the test suite - never for real GridLock data.

### Unknown source dates remain unknown

Where a source publishes no date (`date_basis=not_published`), the field stays unknown. We do not invent, estimate, or backfill dates. An unknown construction window is reported as unknown and never silently treated as a schedule overlap.

### No CEII or non-public grid information is used

GridLock uses only publicly available information (public utility filings, SCRTP/DESC/Georgia Power published material, OpenStreetMap). No CEII, no access-controlled, and no otherwise non-public grid data is ingested, stored, or displayed.

### The cost estimator is unavailable

The cost/savings estimator is **not available** in this build. It remains disabled pending the P2 correction and P1 acceptance. No provisional or synthetic savings figures are quoted here or should be quoted from GridLock output until the estimator is corrected and accepted.

### Research-brief validation vocabulary

A research-brief validation target is recorded as exactly one of: **reproduced** (independently confirmed against the cited public source), **blocked** (could not be checked - access or tooling unavailable), **unresolved** (checked, but no defensible public evidence found - e.g. DESC-002 Okatie-McIntosh, which has **no** placeholder coordinate by design), or **existing** (already present and accepted from prior work, not re-derived). A target is **never** falsely marked `reproduced`.

### Engine verification (context, does not change the above)

The deterministic engine is verified: Phase 3 PostGIS CI is green - 24 passed, 0 skipped at engine SHA `02752cb`, [Actions run 36287891004](https://github.com/Abhiramcodegit/gridlock-sperry-hackathon/actions/runs/36287891004), 2026-09-27 (see [ENGINE_PHASE3.md](ENGINE_PHASE3.md), verification commit `2eff3d0`). That count covers the **engine suite only** and is not the final integrated project test count. A verified engine does not change any data limitation above - the approved set is still empty.

---

Related: [../README.md](../README.md) - [DEMO_FLOW.md](DEMO_FLOW.md) - [DEPLOYMENT.md](DEPLOYMENT.md) - [PROXY_DISTANCE_RESULT.md](PROXY_DISTANCE_RESULT.md) - [ENGINE_PHASE3.md](ENGINE_PHASE3.md)
