# KIRO START HERE — Open-Source Map Research Handoff

> **ADVISORY ONLY.** This is research, not an approved plan. No implementation option is assigned to any agent. Verify every claim below against the current repository before writing any code. If the repo disagrees with this file, the repo wins.

## Current state (updated September 27, 2026, from P1 decisions)

- **Nothing here is assigned.** Option assignment happens after the integration audit.
- **All frontend options are BLOCKED.** Every option touches `frontend/src/App.jsx`, which Agent 2 owns and which is currently frozen. Do not start any frontend option until P1 assigns it and Agent 2 is unfrozen.
- **Basemap branch is frozen under audit:** `frontend/openfreemap-basemap`.
- **Existing transmission-lines layer: OUT OF SCOPE (confirmed by P1).** Option 8 (GA/SC OpenStreetMap power extract) is deferred. Do not develop it; it is documented only as a future option.
- **`docs/specs/` is NOT committed to the repo.** `API_CONTRACT.md`, `GEOMETRY_MATH.md`, `EDGE_CASES.md`, `UI_COPY.md`, `DEMO_NARRATIVE.md`, and `COST_MODEL.md` exist only outside the repo. **No agent should assume approved copy strings or API field names are available in the repo.** P1 is resolving this with P2. Do not commit specs yourself.
- **PR #9 (this research) stays open and unmerged** until the integration audit clears and PR #8 and the basemap PR land.

## Purpose and base

- **Purpose:** Survey open-source projects, datasets, and map UX patterns that could improve GridLock's map, and rank small, independent options for the project owner.
- **Branch base:** `origin/main` at `1c31e2e6efc72599317de739f98ec55bcb6f6417` (Merge PR #7). `main` had not moved when this update was written.
- **Evidence note:** Repo observations come from commit messages, directory listings, and project-lead messages. File contents were not read.
- **Full report:** [OPEN_SOURCE_MAP_RESEARCH.md](./OPEN_SOURCE_MAP_RESEARCH.md). Section 14 covers provenance display for Option 5.

## Five highest-ranked findings

1. **Per-layer source, vintage, and confidence display** (Option 5): comparable tools use a short source line, a per-layer info affordance, and a per-feature accuracy field. See report section 14.
2. **Hover and selected states via MapLibre `feature-state`**: native pattern, no new dependency.
3. **Fit-to-pair on selection**, leaving room for the detail panel and honoring reduced motion.
4. **Voltage-driven line width** from OpenInfraMap's `voltage_scale` pattern, only if voltage exists for every project.
5. **Local search** over projects plus Census Gazetteer GA/SC places and counties; never the public Nominatim API.

## P1 provisional priority (not assigned; blocked on Agent 2's App.jsx)

| Priority | Option | Status | Basemap/boundary overlap | Agent 2 / App.jsx overlap |
|---|---|---|---|---|
| 1 | Option 5: per-layer source/date/confidence strip | Provisional FIRST | None | **Yes, blocked** |
| 2 | Option 1: hover and selected highlighting | Provisional SECOND | None | **Yes, blocked** |
| 3 | Option 3: zoom to selected pair, room for detail panel | Provisional THIRD | None | **Yes, blocked** |
| — | Option 2: line width by voltage | DEFERRED until voltage is confirmed for all ten projects in the official dataset | None | Yes |
| — | Option 4: local search | DEFERRED (larger surface area) | Low | Yes |
| — | Option 6: legend with layer toggles | DEFERRED (not enough layers yet) | Medium | Yes |
| — | Option 7: dev-only map inspector | REJECTED FOR NOW (adds a dependency) | Low | Yes |
| — | Option 8: GA/SC OSM power extract | GATED OUT (existing lines out of scope) | None | No |

## Work already underway — do NOT duplicate

- **Basemap and state/county boundaries:** Agent 2 / basemap work on `frontend/openfreemap-basemap` (frozen under audit). Agent 2 is also preparing a county-boundary plan.
- **Spec files:** P1 and P2 are handling `docs/specs/`. Do not create or commit spec files.
- **Merged:** PR #5 (map wiring and candidate-review layer), PR #6 (map-wiring tests), PR #7 (demo, deployment, data-limitations docs).
- **Provenance docs:** branches `docs/official-data-provenance` and `docs/agent4-official-data-provenance`.
- **QA:** branch `qa/main-review`; `docs/QA_LOG.md`.

## Inspect first

- `AGENT_STATUS.md` (root; the repo's only agent-instruction file. Read it; don't edit it.)
- `frontend/src/App.jsx`, `frontend/src/candidateFixture.js`, `frontend/src/App.test.jsx`, `frontend/src/test/` (read only while frozen)
- `frontend/package.json`, `frontend/vite.config.js` (read only)
- `docs/DEMO_FLOW.md`, `docs/DATA_LIMITATIONS.md`, `docs/ENGINE_PHASE3.md`, `docs/QA_LOG.md`, `docs/WORKSTREAM_STATUS.md`
- `backend/`, `data/`, `.github/workflows/`

## Repository assumptions still requiring verification

- The frontend is JavaScript (`.jsx`/`.js`), not TypeScript. Any spec wording that assumes TypeScript types or enums must be read as string comparisons.
- Approved UI strings are **not** in the repo. Until `docs/specs/` is committed, don't hard-code or invent user-facing copy.
- Per P1, the frontend currently shows labels such as "Proposed — inferred substation proxy". The approved UI copy (uncommitted) uses "Single published endpoint — not a route" for `endpoint_only`. Reconcile once specs are committed and App.jsx is unfrozen.
- Voltage availability for all ten official projects (gates Option 2).
- MapLibre version and plugin compatibility; backend framework (FastAPI assumed, not confirmed); stable feature IDs in the API payload.

## Constraints that must remain unchanged

- Approved-only matching and the 40 km threshold.
- Tier intervals: half-open `[lo, hi)`; touching = intersect or ≤ 0.001 km.
- Authoritative distance, tier, and opportunity computation stays in the backend.
- geometry_confidence has two values only: `endpoint_pair` and `endpoint_only`. Never call either a route.
- No runtime calls to public Overpass or Nominatim endpoints.
- Modeled or inferred grid data is never shown as authoritative infrastructure.
- No dependency, lockfile, database, schema, or migration changes without explicit owner approval.
- Don't edit the root `README.md`, `AGENT_STATUS.md`, `frontend/src/App.jsx` (frozen), or basemap/boundary files.

## Checklist for selecting the first task

- [ ] Integration audit has cleared, and PR #8 and the basemap PR have landed.
- [ ] Agent 2 is unfrozen and P1 has assigned a specific option.
- [ ] `docs/specs/` is committed, so approved strings and field names exist in the repo.
- [ ] Assumptions above verified against the current `main`.
- [ ] Layer IDs and file ownership agreed with Agent 2.
- [ ] No dependency or lockfile change needed (or explicit approval obtained).
- [ ] Acceptance criteria written from report section 10 (and section 14 for Option 5).
- [ ] Work planned on a branch from the latest `main`, never on `main`.

## Warning

This research is **advisory**. Sources, maintenance signals, and repo observations were gathered on September 27, 2026 and may be stale. Verify each relevant claim against the current repository and the linked primary sources before writing code.
