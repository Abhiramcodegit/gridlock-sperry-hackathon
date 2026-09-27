# KIRO START HERE — Open-Source Map Research Handoff

> **ADVISORY ONLY.** This is research, not an approved plan. Nothing here has been implemented or approved. Verify every claim below against the current repository before writing any code. If the repo disagrees with this file, the repo wins.

## Purpose and base

- **Purpose:** Survey open-source projects, datasets, and map UX patterns that could improve GridLock's map, and rank small, independent implementation options for the project owner to choose from.
- **Branch base:** `origin/main` at `1c31e2e6efc72599317de739f98ec55bcb6f6417` (Merge PR #7).
- **Research evidence note:** Parts of the research were gathered earlier from commit messages on `main` at `85a7138` and from project-lead messages. File contents were not read. Directory listings were re-checked at `1c31e2e`.
- **Full report:** [OPEN_SOURCE_MAP_RESEARCH.md](./OPEN_SOURCE_MAP_RESEARCH.md)

## Five highest-ranked findings

1. **Hover and selected states via MapLibre `feature-state`** — native pattern, no new dependency, high value.
2. **Voltage-driven line width** adapted from OpenInfraMap's `voltage_scale` step-expression pattern. Color stays bound to utility.
3. **Local search** over project names plus U.S. Census Gazetteer places/counties for GA/SC. Do not use the public Nominatim API; its policy forbids autocomplete.
4. **Per-layer source, freshness, and confidence indicator**, using approved UI strings only.
5. **Versioned GA/SC OpenStreetMap power extract** (Geofabrik → osmium → static GeoJSON) as evidence only. **Gated:** the existing-lines layer is currently out of scope in the UI spec.

## Ranked implementation choices (owner decides; none approved)

| Rank | Option | Basemap/boundary overlap | Shared-file / Agent 2 overlap flag |
|---|---|---|---|
| 1 | Hover + selected feature states | None | **Yes:** touches `frontend/src/App.jsx` (Agent 2 UI area); coordinate |
| 2 | Voltage-driven line width | None | **Yes:** layer styles in `App.jsx`; coordinate |
| 3 | Fit-to-pair on selection (reduced-motion aware) | None | **Yes:** map/selection code in `App.jsx`; coordinate |
| 4 | Local search (projects + GA/SC Gazetteer) | Low (fly-to only) | **Yes:** new component mounted in the UI; coordinate |
| 5 | Source/freshness/confidence strip | None | **Yes:** legend area; coordinate |
| 6 | Hand-rolled legend with GridLock-only toggles | **Medium:** must never toggle basemap/boundary layers | **Yes:** legend + layer IDs; agree on IDs with Agent 2 first |
| 7 | Dev-only maplibre-gl-inspect | Low (map init is shared) | **Yes:** map initialization; would change dependencies (needs explicit approval) |
| 8 | GA/SC OSM power extract (data only, no rendering) | None | No (data/docs only); gated by owner |

## Work already underway — do NOT duplicate

- **Basemap and state/county boundaries:** owned by another agent. See branch `frontend/openfreemap-basemap`. Do not add or change basemap styles, boundary layers, or Protomaps/OpenFreeMap setup.
- **Frontend map wiring and candidate-review layer:** merged via PR #5 (`frontend/map-wiring`).
- **Frontend map-wiring tests:** merged via PR #6.
- **Demo, deployment, and data-limitations docs:** merged via PR #7.
- **Official data provenance docs:** branch `docs/official-data-provenance` and `docs/agent4-official-data-provenance`.
- **QA review:** branch `qa/main-review`; `docs/QA_LOG.md`.

## Inspect first

- `AGENT_STATUS.md` (root; the repo's agent-status convention. Read it, don't edit it.)
- `frontend/src/App.jsx`, `frontend/src/candidateFixture.js`, `frontend/src/App.test.jsx`, `frontend/src/test/`
- `frontend/package.json`, `frontend/vite.config.js` (read only; don't change dependencies)
- `docs/DEMO_FLOW.md`, `docs/DATA_LIMITATIONS.md`, `docs/ENGINE_PHASE3.md`, `docs/QA_LOG.md`, `docs/WORKSTREAM_STATUS.md`
- `backend/` (engine and API contract), `data/` (dataset and provenance)
- `.github/workflows/` (CI)

## Repository assumptions still requiring verification

- The brief says React + **TypeScript**, but `frontend/src` on `main` contains `.jsx`/`.js` files only. Treat the frontend as JavaScript unless proven otherwise.
- The approved UI spec files (`docs/specs/UI_COPY.md`, `DEMO_NARRATIVE.md`, `COST_MODEL.md`) were **not present on `main` at `1c31e2e`**. Confirm where the approved copy lives before using any string.
- The MapLibre version (a commit pinned 6.11.2) and the MapLibre 6 compatibility of any proposed package.
- The backend framework (FastAPI is assumed, not confirmed).
- Distance method wording: the approved display string is "Closest points between project geometries (haversine, local planar segment math)". Verify against the engine.
- Stable feature IDs in the API payload (required for `feature-state`).
- Field names for voltage, tier, and geometry_confidence in the P2 API contract.

## Constraints that must remain unchanged

- Approved-only matching and the 40 km threshold.
- Tier intervals: half-open `[lo, hi)`; touching = intersect or ≤ 0.001 km.
- Authoritative distance/tier/opportunity computation stays in the backend.
- geometry_confidence has two values only: `endpoint_pair` and `endpoint_only`. Never call either a route.
- No runtime calls to public Overpass or Nominatim endpoints.
- Modeled or inferred grid data (PyPSA-USA, GridSFM) is never shown as authoritative infrastructure.
- Any rendered third-party data carries attribution (e.g. "© OpenStreetMap contributors").
- No dependency, lockfile, database, schema, or migration changes without explicit owner approval.
- Don't edit the root `README.md`, `AGENT_STATUS.md`, or the basemap/boundary files.

## Checklist for selecting the first task

- [ ] Owner has chosen one option from the table above (don't choose it yourself).
- [ ] Verified the assumptions above against the current `main`.
- [ ] Confirmed with Agent 2 / the basemap agent which layer IDs and files are theirs.
- [ ] Confirmed the task needs no dependency or lockfile change (or got explicit approval).
- [ ] Located the approved UI strings for any user-facing text.
- [ ] Written acceptance criteria from the full report, section 10.
- [ ] Planned a branch off the latest `main`, never committing to `main` directly.

## Warning

This research is **advisory**. Sources, maintenance signals, and repo observations were gathered on September 27, 2026 and may be stale. Before writing code, verify each relevant claim against the current repository and the linked primary sources.
