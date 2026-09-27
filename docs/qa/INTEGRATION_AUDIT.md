# GridLock — Integration Audit (READ-ONLY)

**Auditor:** integration-debug / rubric-audit agent (Agent 5 role).
**Date:** 2026-09-27
**Scope:** Read-only cross-branch audit. No merges. No application-code changes.
No agent branch modified. No stash applied/popped/deleted.

---

## 1. Repository state audited

| Ref | SHA | Notes |
|---|---|---|
| `origin/main` | `1c31e2e6efc72599317de739f98ec55bcb6f6417` | Merge of PR #7; audit baseline |
| Agent 1 — `origin/data/agent1-official-dataset-engine` | `0a1f6da` | Official dataset builder + independent overlap engine |
| Agent 2 — `origin/frontend/openfreemap-basemap` | `87879c6` | OpenFreeMap Liberty basemap + controls |
| Agent 4 — `origin/docs/agent4-official-data-provenance` | `8c6d7c0` | Provenance / methodology / cost / demo docs |
| This audit branch — `qa/integration-rubric-audit` | branched from `1c31e2e` | docs-only |

All three feature branches share merge-base `1c31e2e` (current `origin/main`) — none is stale relative to main.

**PR state — ATTESTATION GAP:** the repository is private and no `gh` CLI or API
token is available in this environment. PR metadata (whether PR #8 is open or
merged, review state, checks) **could not be verified programmatically**. A human
repo member should confirm PR state directly on GitHub. The Agent 1 *branch*
exists on origin and was audited from that branch content.

---

## 2. Compatibility matrix (files changed vs `origin/main`)

| Branch | Files changed | Nature | Touches existing tracked files? |
|---|---|---|---|
| Agent 1 | `backend/gridlock/official_engine.py`, `backend/tests/test_official_engine.py`, `data/official/projects_official.json`, `data/official/projects_official.geojson`, `docs/OFFICIAL_DATASET_ENGINE.md`, `scripts/build_official_dataset.py` | **Additive only** (6 new files, +1160/-0) | No |
| Agent 2 | `frontend/src/App.jsx` (+319/-75), `frontend/src/style.css` (+9) | Rewrite of App.jsx + CSS | Yes (App.jsx, style.css) |
| Agent 4 | `README.md` (+46/-2), `docs/COST_ESTIMATE.md`, `docs/DATA_PROVENANCE.md`, `docs/DEMO_SCRIPT.md`, `docs/METHODOLOGY.md` | 4 new docs + README edit | Yes (README.md) |

### Conflict analysis

- **Textual merge conflicts between the three branches: NONE.** No two branches
  change the same file. The change sets are disjoint (backend/data vs frontend
  vs docs).
- **Only existing-file edits anywhere:** Agent 2 rewrites `App.jsx`/`style.css`;
  Agent 4 edits `README.md`. Neither collides with the other or with Agent 1.
- **Agent 4 README vs current main:** applies cleanly (git merge-tree reports
  "added in remote"; the edit inserts a Screenshots + Source Attribution block
  and updates the Documentation list). Small future conflict surface only if
  main's README Documentation section is edited on the same lines before merge.
- **Agent 1 core-file safety CONFIRMED:** `backend/gridlock/engine.py`,
  `backend/gridlock/api.py`, and `data/approved/projects_approved.geojson` are
  **untouched** by Agent 1 (verified by exact-path check against its diff).

### Semantic / data-contract conflicts (do not show up in a textual diff)

1. **Opportunity data-contract mismatch (Agent 1 engine ↔ Agent 2 UI).**
   Agent 2's `App.jsx` renders opportunities using fields:
   `project_a`, `project_b`, `distance_m`, `tier`, `score`, `closest_segment`,
   `timeline_status`, `timeline_overlap_fraction`, `confidence_multiplier`.
   Agent 1's `official_engine.find_opportunities()` emits a different shape:
   `desc_id`, `gpc_id`, `distance_m`, `distance_km`, `distance_mi`, `day_gap`,
   `tier`, `coordination_action`, `confidence{desc,gpc}`, `desc_name`, `gpc_name`.
   → **The UI is wired to the main/approved `/opportunities` shape, NOT to Agent
   1's official engine.** Feeding the 6 official overlaps into this UI requires
   an adapter (or an API endpoint that emits the UI's shape). This is the single
   most important integration gap.

2. **Worker-loading bug present on Agent 2 (and main).** Agent 2's `App.jsx`
   still carries the comment "no `setWorkerUrl()` wiring is needed" and contains
   **no** worker import and **no** `setWorkerUrl` call. maplibre-gl 6.11.2
   resolves its render worker from `import.meta.url`; under the Vite dev server
   that URL is not `http(s)` for the pre-bundled dep, so maplibre's internal
   resolver returns an **empty string** → `new Worker('')` → "Worker failed to
   load", and the map's `load` event never fires. Root cause confirmed by
   reading `node_modules/maplibre-gl/dist/maplibre-gl.mjs`
   (`if(!/^https?:/.test(e))return\`\``). This is a **demo-blocking risk** for the
   basemap branch and must be fixed before the map is shown. (A prepared fix
   exists — see §5 stash finding — but against a stale base.)

3. **Multiple live counts across two datasets (see §4 and §7).** Not a code
   conflict, but a presentation conflict: the UI surfaces numbers from the
   Track-B pipeline (34 / 32 / 2) next to numbers that belong to the Track-A
   official engine (25 / 6). Nothing labels which dataset each number is from.

---

## 3. Per-agent verification

### Agent 1 — VERIFIED PASS (engine + dataset)

Environment: Python 3.13, shapely 2.0.6, pyproj 3.7.0, openpyxl 3.1.5.

- **Dataset rebuild is deterministic and reproducible.** Ran
  `scripts/build_official_dataset.py` twice → byte-identical output; the rebuilt
  `projects_official.json` / `.geojson` match the committed files exactly
  (`git diff` empty). The builder reads coordinates verbatim from
  `Sperry-Tech-Challenge/Projects_Overlaps.xlsx`; it never invents coordinates.
- **Focused tests:** `pytest tests/test_official_engine.py` → **8 passed.**
- **Full backend suite (no DB):** **28 passed, 4 skipped.**
- **PostGIS integration tests (the 4 skips): NOT RUN — status UNKNOWN.** This
  machine has no Docker, no local Postgres, no Postgres.app, no Homebrew
  Postgres, so a PostGIS server cannot be started here. Per instruction, these
  are reported as **skipped / not verified**, never as passing. They are
  verifiable only in CI. NOTE: those 4 tests exercise `db.py` (the *approved*
  PostGIS engine), a **different code path** from Agent 1's `official_engine.py`,
  which is pure shapely with **no database dependency** — so Agent 1's engine is
  fully covered by its 8 passing tests without PostGIS.
- **Independent recomputation of the 6 pairs** (recomputed from the dataset
  WITHOUT importing Agent 1's engine — own shapely/pyproj UTM-17N pass):
  **25 total cross-utility pairs, exactly 6 qualifying (< 40 km).** Pair IDs and
  day gaps match Agent 1's report exactly:

  | Pair | closest-point km | closest-point mi | day gap | touching |
  |---|---|---|---|---|
  | DESC_2 × GPC_1 | 0.000 | 0.000 | 3074 | **yes** |
  | DESC_3 × GPC_2 | 4.816 | 2.992 | 152 | no |
  | DESC_3 × GPC_3 | 5.466 | 3.396 | 517 | no |
  | DESC_1 × GPC_1 | 11.083 | 6.886 | 3074 | no |
  | DESC_5 × GPC_2 | 13.574 | 8.434 | 365 | no |
  | DESC_5 × GPC_3 | 14.225 | 8.839 | 730 | no |

- **The 0 m Thurmond result — confirmed from source coordinates, with a caveat.**
  DESC_2 is `endpoint_only` and is located at Thurmond Sub
  `[-82.195931, 33.660127]`. GPC_1's LineString endpoint "THURMOND DAM #5" is at
  the **identical** coordinate `[-82.195931, 33.660127]`. The 0 m is therefore
  mathematically correct but is an **artifact of the source spreadsheet assigning
  the same coordinate to two differently-named substations** ("Thurmond Sub" vs
  "Thurmond Dam #5"), not independently verified touching infrastructure. **The
  engine is correct; the interpretation needs this caveat in any demo.**
- **Endpoint-only projects confirmed:** DESC_1, DESC_2, DESC_4, GPC_2 (the four
  the branch declares). Modeled as single Points. Their closest-point distance is
  an **upper bound** on the true line-to-line distance — the unlocated endpoint
  could extend the real geometry closer to the other project. Distances for
  these pairs should be labeled "upper bound (endpoint-only)".
- **Only the 6 declared files differ from main; core files untouched** — confirmed.

**Agent 1 verdict: PASS** for the file-mode / shapely engine and dataset. PostGIS
path unverified here (CI-only) but not exercised by this engine.

### Agent 2 — CONDITIONAL PASS (unit/build) / RENDER UNVERIFIED

- `npm run test:run` → **9 passed.** `npm run build` → **exit 0.**
- **Style lifecycle:** overlay adds are **idempotent** (`hasSource`/`hasLayer`
  guards) and re-add safe on style (re)load; overlays are added on `load` and via
  a `tryAddOverlays()` path. Controls are added once in `addControls()` inside a
  single `useEffect` with a cleanup `map.remove()`, so a normal React remount
  tears down and rebuilds cleanly (no obvious duplication under the documented
  lifecycle). Attribution is left to MapLibre's **built-in** AttributionControl
  (no `customAttribution`), so the OpenFreeMap/OpenMapTiles/OSM credit renders
  **once** — verified by code inspection, not by pixel.
- **Sidebar independence:** a 4-second fallback timer calls `loadData()` even if
  the map `load` never fires, and `loadData` is idempotent — so the ranked list
  and candidate panel still populate if the basemap fails. Good defensive design.
- **Basemap reachability:** `https://tiles.openfreemap.org/styles/liberty` →
  HTTP 200, valid style v8, 111 layers, includes `boundary_2` / `boundary_3`
  (state-level admin boundaries). So **state lines are defined in the style** and
  will appear **if tiles render**.
- **Real-GPU render: UNVERIFIED.** This environment has no real GPU browser or
  display (the same SwiftShader-class limitation Agent 2 reported). Necessary
  conditions are met (style reachable, boundary layers present, build succeeds)
  but the **sufficient** condition — tiles/roads/cities/state-lines actually
  painting on a GPU — **could not be confirmed here.** Combined with the worker
  bug (§2.2), render must be confirmed in a real browser before the demo.
- **Counties:** Agent 2 added **no** county/geocoding/transmission code (verified
  against its diff). Counties are **absent** — stated plainly, not claimed.
- **Desktop/mobile:** not verifiable without a real browser; `style.css` adds
  responsive rules but visual responsive behavior is unconfirmed here.

**Agent 2 verdict: PASS on unit tests + build; RENDER UNVERIFIED; blocked by the
worker bug for a live map demo.**

### Agent 4 — VERIFIED PASS (documentation)

- **Threshold wording CORRECT.** METHODOLOGY states 40 km ≈ 24.85 mi and that
  the docx/xlsx "25 mi" and the prompt's "40 km" are effectively the same cutoff.
  It cites `backend/gridlock/config.py` `CANDIDATE_RADIUS_M = 40000.0` and
  `TIERS` — **both confirmed to exist on `origin/main`**. It does **not** conflate
  the two numbers into two different gates.
- **Cost figures cleanly separated.** COST_ESTIMATE uses three explicit layers:
  Layer 1 actual filed cost (~$11,116,933, Okatie/Jasper–Yemassee fold-in, which
  matches the Dominion PDF), Layer 2 assumed shareable share (labeled an
  assumption), Layer 3 illustrative savings (arithmetic on the assumption), plus
  a Fact/Assumption/Illustrative summary table and repeated "illustrative, not
  verified" framing. The estimator ships **disabled**. **Minor note:** the cost
  anchor project is a *nearby* DESC project, not one of the 6-overlap projects —
  defensible as an illustration but worth stating in the demo.
- **No false API claim.** DATA_PROVENANCE explicitly separates **Track A**
  (official xlsx: 10 projects / 6 overlaps, the answer key) from **Track B** (the
  ingestion pipeline: 34 proposed / 0 approved, engine correctly returns `[]`).
  It does **not** imply the production API already returns the 6 official
  overlaps.
- **Metric conflation: none.** Closest-point vs center-to-center is kept distinct
  in METHODOLOGY (dedicated section), DEMO_SCRIPT, and DATA_PROVENANCE.
- **Endpoint-only limits disclosed:** explicit section; distances described as
  "endpoint/proxy proximity, not surveyed route proximity."
- **No-CEII rule stated and enforced** in provenance.

**Agent 4 verdict: PASS.** Documentation is accurate against the code and data as
they exist. One wording caveat to add (below).

---

## 4. Truth table across result tracks

| | (a) Conservative ingestion pipeline | (b) Agent 1 official reference engine | (c) Frontend candidate / proxy presentation | (d) Spreadsheet reference oracle |
|---|---|---|---|---|
| Input dataset | `data/normalized/projects_proposed.csv` → `data/approved/projects_approved.geojson` | `data/official/projects_official.json` (built from `Projects_Overlaps.xlsx`) | `frontend/src/candidateFixture.js` (hand-derived from 2 proposed rows) | `Sperry-Tech-Challenge/Projects_Overlaps.xlsx` Sheet 2 |
| Geometry type | endpoint/proxy points; approved set empty | LineString (2-endpoint) / Point (endpoint-only) | 2 inferred substation **proxy points** | project **center** points (midpoints) |
| Approval interpretation | approved-only gate; **0 approved** | official dataset treated as analyzable (challenge-supplied) | non-authoritative "review" candidates | reference answer key |
| Distance metric | closest-point (`ST_Distance`/tier) | **closest-point**, UTM 17N | none (no pair distance computed between proxies) | **center-to-center** haversine |
| Project count | 34 proposed (0 approved) | 10 (5 DESC + 5 GPC) | 2 plotted (of 34) | 10 |
| Candidate pair count | 0 (nothing approved to pair) | 25 (5×5) | 0 | 25 (implied) |
| Qualifying pairs | **0** (correct honest negative) | **6** | 0 | **6** |
| Intended purpose | strict provenance-gated research pipeline | primary challenge result (screen + rank) | show 2 proposed proxies for human review | validation baseline / answer key |
| Safe to show in demo? | Only as an honest "0 approved yet" story | **YES — primary demo engine** | Only as clearly-labeled non-authoritative candidates | As a validation cross-check, **not** as the engine |

**Key cross-track fact:** tracks (b) and (d) agree on **which 6 pairs qualify**,
but their **distances differ materially** because (b) is closest-point and (d) is
center-to-center (e.g. DESC_2×GPC_1 = 0.00 mi closest-point vs 4.09 mi
center-to-center; DESC_5×GPC_2 = 8.43 vs 14.34). The numbers must never be
presented interchangeably.

---

## 5. Stash inspection (read-only) — `agent1-preserve-before-branch`

Inspected with `git stash list`, `git stash show --stat`, `git stash show -p`
only. **Not applied, popped, or deleted.**

- **Identifier (current):** `stash@{1}`, message
  `On official-data-provenance: agent1-preserve-before-branch`.
  (It is at index `{1}`, not `{0}`, because the auditor pushed a separate,
  clearly-labeled stash `kiro-audit-worker-fix-WIP` on top to keep the working
  tree clean during the audit; that auditor stash is `stash@{0}`.)
- **Contents:** `frontend/src/App.jsx` (+27/-2), `frontend/src/App.test.jsx`
  (+6/-1).
- **What it is:** the **worker-loading fix** — adds
  `import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'`,
  a guarded `maplibregl.setWorkerUrl(maplibreWorkerUrl)`, and a `map.on('error')`
  handler; plus test mocks for `setWorkerUrl` and the `?worker&url` import.
- **Relationship to Agent 2's committed App.jsx:** the stash's App.jsx base blob
  is `93f3ca2` — the **pre-basemap** App.jsx. It therefore **predates** Agent 2's
  committed basemap rewrite and would **NOT apply cleanly** on top of it (both
  edit the header comment block and the `useEffect`/`on('load')` region). It
  **duplicates the intent** of the still-needed worker fix but against a stale
  base.
- **Recommendation:** **archive as a patch, then delete later.** Do not pop it
  onto Agent 2's branch. The worker fix should be **re-authored on top of Agent
  2's basemap `App.jsx`** (or on main) so it composes with the new lifecycle.
  Suggested archival (when approved, not now):
  `git stash show -p stash@{1} > docs/qa/worker-fix-legacy.patch`.

---

## 6. Blockers before any merge

1. **Worker-loading bug** must be fixed on whatever frontend branch ships
   (Agent 2 / main). Without it the map hangs on "Loading map data" under the
   Vite dev server. Re-author the fix on Agent 2's App.jsx; confirm render in a
   real browser.
2. **Opportunity data-contract adapter** — decide how the demo UI is fed. Either
   (a) demo the main/approved `/opportunities` shape, or (b) add an adapter/
   endpoint that maps Agent 1's official-engine output into the UI's field names.
   Today they do not match.
3. **Real-GPU render confirmation** for Agent 2's basemap (tiles + state lines).
   Unverifiable in this environment.
4. **UI number labeling** (see §7) before showing judges.
5. **PR-state attestation** — confirm PR #8 (and any others) on GitHub.
6. **PostGIS CI attestation** — confirm the 4 integration tests pass in CI (they
   cannot be run locally here).

---

## 7. The "32 of 34" figure and number-collision risk

The UI string is: **"32 of 34 proposed records have no geometry and are not
shown on the map."** Source: `frontend/src/candidateFixture.js` —
`PROPOSED_TOTAL = 34`, `CANDIDATE_RECORDS.length = 2`, so
`PROPOSED_WITHOUT_GEOMETRY = 32`.

- **34** = total Track-B **pipeline** proposed rows (28 sourced + 6 `H-*`
  hypotheses).
- **32** = pipeline proposed rows with **no geometry** (34 − 2 located proxies).
- **2** = located proxies actually plotted (GPC-004, DESC-003).
- **25** = cross-utility pairs **screened** by the Track-A **official engine**.
- **6** = qualifying **official overlaps**.

**Confusion risk: HIGH.** Five numbers (34, 32, 2, 25, 6) from **two different
datasets** appear in one interface, and none is labeled with its dataset. "32 of
34" belongs to the *proposed pipeline* (which yields **zero** opportunities);
"6 of 25" belongs to the *official dataset*. A judge could easily read "32 of 34"
as if it related to overlaps. **Recommendation:** label each number with its
dataset in the UI — e.g. "Official dataset: 6 of 25 cross-utility pairs qualify"
vs "Research pipeline (separate): 32 of 34 proposed records lack geometry" — and
visually separate the two panels.

---

## 8. Summary verdicts

| Branch | Verdict |
|---|---|
| Agent 1 (`0a1f6da`) | **PASS** — deterministic, reproducible, 6/25 independently confirmed; core files untouched; PostGIS path CI-only (not this engine). |
| Agent 2 (`87879c6`) | **CONDITIONAL** — tests 9/9 + build pass; **worker bug present**; **render unverified**; counties correctly absent. |
| Agent 4 (`8c6d7c0`) | **PASS** — quantitative claims trace to sources; threshold/metric/cost handled honestly; one minor cost-anchor caveat. |

Merge order and detailed recommendations: see the recommendations section in
this repository's audit output (§6 blockers) and `RUBRIC_EVIDENCE_MATRIX.md`.
Recommended order: **Agent 1 → Agent 4 → Agent 2** (backend/data first, then the
docs that describe it, then the frontend once the worker fix + data-contract are
resolved).
