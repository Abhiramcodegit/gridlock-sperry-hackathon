# KIRO START HERE — Open-Source Map Research Handoff (v2, current-state refresh)

> **ADVISORY ONLY.** This is research, not an approved plan. Nothing here is
> implemented or approved. Verify every claim against the current repository
> before writing code. **If the repo disagrees with this file, the repo wins.**

## Purpose and base
- **Purpose:** survey open-source projects, datasets, and map UX patterns that
  could improve GridLock's map, and rank small, independent options for the
  owner to choose from.
- **Branch base:** `origin/main` at
  `1c31e2e6efc72599317de739f98ec55bcb6f6417` (Merge PR #7).
- **Full report:** [OPEN_SOURCE_MAP_RESEARCH.md](./OPEN_SOURCE_MAP_RESEARCH.md).
- **This is v2.** It supersedes the earlier
  `research/open-source-map-handoff` handoff, which was written before Agent 2's
  basemap shipped. v2 treats the basemap + its four controls as **shipped**,
  treats **county boundaries as claimed by Agent 2**, reflects **Agent 1's open
  PR #8** (closest-point engine, four endpoint-only projects), and adds
  coordination fields to every proposed task.

## Current state you are building around (authoritative)
- **Agent 2 SHIPPED** (`frontend/openfreemap-basemap`): OpenFreeMap **Liberty
  basemap** + **Navigation, Scale, Fit-to-projects, Reset** controls.
  **Do not re-propose, re-add, or restyle any of these.**
- **Agent 2 did NOT do, and these are OPEN:** county boundaries, transmission
  infrastructure rendering, geocoding, layer controls.
- **Agent 2 CLAIMED (in progress):** GA/SC **county-boundary** layer from U.S.
  Census **cartographic boundary** data. **Treat counties as claimed** — do not
  build a county-boundary task; only *consume* the layer once merged.
- **Agent 1 OPEN PR #8:** official dataset + overlap engine, **closest-point**
  distance, **four endpoint-only** projects. Authoritative distance/tier/
  opportunity math lives here — do not reimplement it in the frontend.
- **Independent debug agent** is auditing integration + rubric evidence. Keep
  every provenance / "verified" string defensible.

## Five highest-ranked findings
1. **Hover + selected states via MapLibre `feature-state`** — native, no new
   dependency, directly delivers list↔map↔drawer selection sync.
2. **Voltage-driven line *width*** adapted from OpenInfraMap's `voltage_scale`
   pattern. Color stays bound to utility.
3. **Local search** over project names + a static GA/SC Census **Gazetteer**
   subset. Do **not** use the public Nominatim API (policy forbids autocomplete).
4. **Per-layer source / freshness / confidence strip**, approved UI strings only.
5. **Versioned GA/SC OpenStreetMap power extract** (Geofabrik → osmium → static
   GeoJSON) as **evidence only** — transmission-infra rendering is open but
   unclaimed; produce facts, let the owner decide.

## Ranked first-task options (owner decides; none approved)
Each row carries the required coordination fields. "App.jsx overlap" means a
shared-**file** edit needing coordination, not a conflict with Agent 2's
shipped **features**.

| Rank | Option | (a) Agent 2 did part? | (b) Wait for Agent 2 PR? | (c) Overlap status | (d) Independent of Agent 1 engine? | (e) Data classification |
|---|---|---|---|---|---|---|
| 1 | Hover + selected feature states | No | No (coordinate `App.jsx` edits) | No feature overlap; `App.jsx` file overlap | Yes | n/a (interaction) |
| 2 | Voltage-driven line width | No | No | No feature overlap; `App.jsx` file overlap | Yes, if voltage field present | pattern community-maintained; values authoritative |
| 3 | Fit-to-**pair** on selection | Partially adjacent (shipped Fit-to-projects fits *all*) | **Prefer yes** — extend the merged Fit logic | Partial overlap; must extend not fork | Yes | n/a (camera) |
| 4 | Local search (projects + GA/SC Gazetteer) | No | No (soft: use county bbox if it lands) | No feature overlap; soft touch on claimed counties | Yes | authoritative (Census Gazetteer 2024) |
| 5 | Source/freshness/confidence strip | No | No | No feature overlap; legend `App.jsx` file overlap | Yes | n/a (displays existing labels) |
| 6 | Hand-rolled GridLock-only legend + toggles | No (layer controls are open) | **Prefer yes** — agree layer IDs, exclude basemap/county | Medium risk; scope to GridLock layer IDs only | Yes | n/a (visibility) |
| 7 | Dev-only maplibre-gl-inspect | No | No (shared map init; coordinate) | Low overlap (map init) | Yes, once dep change approved | n/a (dev tooling) |
| 8 | GA/SC OSM power extract (data only) | No (transmission infra open) | No | No overlap (data/docs only) | Yes | community-maintained (OSM, ODbL) |

**Recommended first task:** Option 1. It delivers the selection spine
(list↔map↔drawer), adds no dependency, computes no authoritative distance, and
touches none of Agent 2's shipped or claimed surfaces.

## Work already done or claimed — do NOT duplicate
- **Basemap + Nav/Scale/Fit-to-projects/Reset controls:** shipped by Agent 2
  (`frontend/openfreemap-basemap`). Off-limits as new work.
- **GA/SC county boundaries:** claimed by Agent 2 (Census cartographic boundary
  data), in progress. Do not build; only consume once merged.
- **Overlap engine + official dataset:** Agent 1, open PR #8 (closest-point,
  four endpoint-only projects). Do not reimplement client-side.
- **Frontend map wiring / candidate-review layer, tests, demo/deploy/limitations
  docs:** merged into `main` at `1c31e2e` (PRs #5/#6/#7).

## Inspect first (read only)
- `AGENT_STATUS.md` (root; read, don't edit).
- `frontend/src/App.jsx`, `candidateFixture.js`, `App.test.jsx`, `test/`.
- `frontend/package.json`, `frontend/vite.config.js` (don't change deps).
- `docs/DATA_LIMITATIONS.md`, `docs/DEMO_FLOW.md`, `docs/ENGINE_PHASE3.md`,
  `docs/WORKSTREAM_STATUS.md`.
- `backend/` (engine + API contract), `data/` (dataset + provenance).
- `.github/workflows/` (CI).

## Assumptions still requiring verification
- Frontend is **JavaScript** (`.jsx`/`.js`), not TypeScript, despite the brief.
- MapLibre version pin and any package's MapLibre-6 compatibility.
- Approved UI-copy location (`docs/specs/UI_COPY.md`, `DEMO_NARRATIVE.md`,
  `COST_MODEL.md` were not on `main` at `1c31e2e`).
- Field names for voltage, tier, and `geometry_confidence` in the API payload.
- Stable feature IDs (or `promoteId`) — required for `feature-state`.

## Constraints that must remain unchanged
- Approved-only matching; **40 km** threshold; tiers **1.6 / 8 / 40 km** are
  challenge parameters, not tunables.
- Tier intervals half-open `[lo, hi)`; touching = intersect or ≤ 0.001 km.
- Authoritative distance/tier/opportunity math stays in Agent 1's backend engine.
- `geometry_confidence` ∈ {`endpoint_pair`, `endpoint_only`}; never call either a
  surveyed route. Four projects are endpoint-only.
- No runtime Overpass/Nominatim calls.
- Modeled/inferred grids never shown as authoritative; the 116.993 km GPC-004↔
  DESC-003 figure is a diagnostic on inferred points and the pair is ineligible.
- Cost/savings estimator is disabled — quote no savings.
- No dependency/lockfile/schema/migration change without explicit approval.
- Don't edit `README.md`, `AGENT_STATUS.md`, Agent 2's basemap/controls, or the
  (claimed) county-boundary files.

## Checklist for selecting the first task
- [ ] Owner picked one option from the table (don't self-select).
- [ ] Verified the assumptions above against current `main`.
- [ ] Confirmed with Agent 2 which layer IDs/files are theirs (basemap + counties).
- [ ] Confirmed the task needs no dependency/lockfile change (or got approval).
- [ ] Located approved UI strings for any user-facing text.
- [ ] Wrote acceptance criteria from the full report, Section 9.
- [ ] Planned a branch off latest `main`; never commit to `main` directly.

## Warning
Advisory research gathered September 27, 2026; sources and repo observations may
be stale. Verify each relevant claim against the current repository and the
linked primary sources before writing code.
