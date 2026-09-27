# Open-Source Map Research for GridLock (v2 — current-state refresh)

**Research and documentation only. No application code, dependencies, database
objects, or existing documentation were changed by this report.**

- **Research date:** September 27, 2026. Maintenance signals (stars, release
  dates, project status) were read from public pages on that date and will go
  stale. Re-verify before acting.
- **Handoff branch base:** `origin/main` at
  `1c31e2e6efc72599317de739f98ec55bcb6f6417` (Merge PR #7).
- **This is v2.** A prior handoff (`research/open-source-map-handoff`) surveyed
  the same ground while Agent 2's basemap was still only a branch and while
  PRs #5/#6/#7 were the newest work. This version supersedes it on two points:
  it treats Agent 2's basemap + controls as **shipped**, treats county
  boundaries as **claimed by Agent 2**, and it adds the required
  coordination-status fields to every proposed task (Section 9). Where the two
  documents disagree, this one is newer; where the **repository** disagrees with
  either, the repository wins.

> **Advisory only.** Nothing here is approved or implemented. Every claim about
> the repo must be re-verified against the current tree before code is written.

---

## 0. Current state as of this report (authoritative inputs)

These facts were provided by the project lead and are the frame for every
recommendation below. Treat them as the coordination baseline.

- **Agent 2 — SHIPPED (branch `frontend/openfreemap-basemap`):** OpenFreeMap
  Liberty basemap, plus **Navigation, Scale, Fit-to-projects, and Reset**
  controls. **Do not propose any of these as new work.** Do not re-add,
  restyle, or re-wire the basemap or those four controls.
- **Agent 2 — explicitly NOT done, and OPEN:** county boundaries, transmission
  infrastructure rendering, geocoding, and layer controls.
- **Agent 2 — CLAIMED (in progress):** a Georgia / South Carolina
  **county-boundary** layer from U.S. Census **cartographic boundary** data.
  **Treat counties as claimed** — do not propose a county-boundary task as
  independent work; at most, propose things that *consume* the county layer once
  it lands, clearly marked as dependent on Agent 2.
- **Agent 1 — OPEN PR #8:** official dataset + overlap engine using
  **closest-point** distance, with **four endpoint-only** projects in the set.
  Distance/tier/opportunity computation is Agent 1's engine and must not be
  reimplemented in the frontend.
- **Independent debug agent:** auditing integration and rubric evidence.
  Expect scrutiny of any truth claim, provenance label, or "verified" wording.

**Net effect on scope:** the still-open map surfaces are (a) selection/hover
interaction, (b) voltage-driven styling, (c) local search / geocoding, (d)
provenance & confidence display, (e) a GridLock-only legend / layer control that
never touches Agent 2's basemap or county layers, and (f) evidence-only data
extracts. The basemap, its four controls, and county boundaries are off the
table as new work.

---

## 1. Executive summary — five strongest ideas, ranked by impact vs effort

| Rank | Idea | Impact | Effort | Data classification | Why it ranks here |
|---|---|---|---|---|---|
| 1 | **Hover + selected-feature states** via MapLibre `feature-state` for project lines, endpoints, and closest-point connectors | High | Low | n/a (interaction) | Native MapLibre pattern, official example, no new dependency; makes the selected pair readable instantly and syncs list ↔ map ↔ drawer. |
| 2 | **Voltage-driven line *width*** adapted from OpenInfraMap's `voltage_scale` step-expression pattern (color stays bound to utility) | High | Low | community-maintained (pattern only) | One data-driven expression, no data acquisition, proven power-map convention; width avoids colliding with the utility-color rule. |
| 3 | **Local search** over project names + a static GA/SC subset of Census Gazetteer places & counties, with fly-to | Medium–High | Low–Medium | authoritative (Census Gazetteer) | Small, static, authoritative; enables demo navigation by name without the public Nominatim API (whose policy forbids autocomplete). |
| 4 | **Per-layer source / freshness / confidence strip** (snapshot date, source doc, `geometry_confidence`, "not a surveyed route") | High for judges | Low | n/a (display of existing provenance) | Directly serves GridLock's truth-labeling rules and the debug agent's evidence audit; little code. |
| 5 | **Versioned GA/SC OpenStreetMap power extract** (Geofabrik → osmium → static GeoJSON) as **evidence only, not rendered** | Medium–High | Medium | community-maintained (OSM) | The only practical open source of existing line/substation geometry after HIFLD Open shut down. **Gated:** transmission-infra rendering is open scope but unclaimed; produce the evidence, let the owner decide on rendering. |

---

## 2. What changed since the v1 handoff

| Topic | v1 handoff assumed | Current state (this report) | Consequence |
|---|---|---|---|
| Basemap | branch `frontend/openfreemap-basemap` *exists*; owned by another agent | **Shipped**: Liberty basemap + Nav/Scale/Fit/Reset controls | Never propose basemap or those controls as new work. |
| County/state boundaries | "owned by another agent" (unspecified) | **Claimed by Agent 2**, using Census cartographic boundary data, in progress | Counties are off-limits as independent work; only *consume* them once merged. |
| Distance engine | PostGIS reference; "closest points … haversine, local planar segment math" | **Agent 1 PR #8 open**: official dataset + closest-point engine, **four endpoint-only projects** | Frontend must render engine output, not compute authoritative distance; endpoint-only count is now four, not two-by-inference. |
| Review posture | general QA branch | **Independent debug agent auditing** integration + rubric evidence | Every provenance/"verified" string must be defensible. |
| Layer controls / geocoding / transmission infra | listed as future options | **Confirmed open and unclaimed** by Agent 2 | These are the cleanest independent targets, subject to the shared-file caveat on `App.jsx`. |

---

## 3. Repository assumptions a coding agent must verify first

Evidence is from directory listings at `1c31e2e`, `docs/DATA_LIMITATIONS.md`,
the `AGENT_STATUS.md` board, and project-lead messages. Verify each before
writing code.

| # | Assumption | Evidence / conflict | Verify against |
|---|---|---|---|
| 1 | Frontend is React + **JavaScript**, not TypeScript | `frontend/src` holds `App.jsx`, `App.test.jsx`, `candidateFixture.js`, `main.jsx`, `style.css`, `test/`; `vite.config.js` | The tree; treat as JS unless proven otherwise |
| 2 | MapLibre GL JS version | Agent 2 section cites `maplibre-gl` pin; verify MapLibre 6 vs any package's stated support | `frontend/package.json` + lockfile (read only) |
| 3 | Distance is **closest-point**, computed in the backend engine | Agent 1 PR #8; challenge brief | Engine code; the UI uses the approved display string |
| 4 | Opportunities = approved pairs within 40 km | `CANDIDATE_RADIUS_M=40000`; binding challenge rule | Engine filter + tier enums; **do not change** |
| 5 | Tier intervals half-open `[lo, hi)`; touching = intersect or ≤ 0.001 km; tiers 1.6 / 8 / 40 km | Challenge parameters, not GridLock-derived | API contract |
| 6 | `geometry_confidence` has exactly two values: `endpoint_pair`, `endpoint_only` | `DATA_LIMITATIONS.md`; four endpoint-only projects per PR #8 | API contract + dataset |
| 7 | Approved set is **empty**; `/opportunities` returns `[]` by design | `data/approved/projects_approved.geojson` = empty FeatureCollection | The file + engine |
| 8 | Proposed data = 34 records (19 DESC, 9 GPC, 6 `H-` hypotheses); proxies GPC-004 & DESC-003 are **inferred single points**, 116.993 km apart = **ineligible** | `DATA_LIMITATIONS.md`, `candidateFixture.js` | Dataset + fixture |
| 9 | Cost / savings estimator is **disabled** in this build | `DATA_LIMITATIONS.md` | Do not surface any savings figure |
| 10 | Agent 2 owns basemap + Nav/Scale/Fit/Reset (**shipped**) and county boundaries (**claimed**) | Current-state update | `frontend/openfreemap-basemap`; coordinate before any style/init/boundary touch |
| 11 | Approved UI copy location (`docs/specs/UI_COPY.md`, `DEMO_NARRATIVE.md`, `COST_MODEL.md`) | **Not present** on `main` at `1c31e2e` in v1 review | Confirm where approved strings live before using any user-facing text |
| 12 | `feature-state` needs stable numeric feature IDs or `promoteId` | MapLibre requirement | Confirm stable IDs in the API/fixture payload |

---

## 4. Candidate comparison table

| Candidate | Type | Verdict | Difficulty | User value | Data classification | GA/SC coverage | Maintenance (Sep 2026) |
|---|---|---|---|---|---|---|---|
| MapLibre `feature-state` hover/select example | adapt a pattern | **Adopt** | Low | High | n/a | n/a | Official docs |
| OpenInfraMap `voltage_scale` pattern | adapt a pattern | **Adopt pattern only** | Low | High | community-maintained (OSM) | reflects OSM | active; BSD-3 |
| Census Gazetteer files (places/counties) | use a dataset | **Adopt** | Low | Medium–High | authoritative | complete | 2024 files published |
| Census **cartographic boundary** files (counties) | use a dataset | **Do NOT** (Agent 2 claimed) | — | — | authoritative | complete | 2024 published |
| MapLibre large-GeoJSON guide | adapt a pattern | **Adopt** | Low | Medium | n/a | n/a | official docs |
| OSM power tags + Geofabrik + osmium extract | use a dataset | **Investigate (evidence only)** | Medium | Medium–High | community-maintained | uneven; measure | GA/SC PBFs updated daily |
| maplibre-gl-inspect | dev-only package | **Adopt (dev only, needs dep approval)** | Low | Low (users) / High (devs) | n/a | n/a | v1.9.0 Aug 2026; BSD-3 |
| maplibre-gl-layer-control | package | **Investigate / prefer hand-roll** | Low–Medium | Medium | n/a | n/a | v0.17.x 2026; ~1 maintainer; MIT |
| maplibre-gl-geocoder | package | **Investigate (local provider only)** | Medium | Medium | n/a | n/a | v1.8.0 Feb 2025; ISC |
| Public Nominatim API | hosted API | **Avoid** | — | — | community-maintained | — | policy forbids autocomplete |
| Turf.js (`@turf/bbox`, `@turf/midpoint`) | package | **Investigate (display helpers only)** | Low | Low–Medium | n/a | n/a | v7.x 2026; MIT |
| PMTiles + Tippecanoe | format + build tool | **Investigate (upgrade path only)** | Medium | Medium | n/a | n/a | very active; BSD-3 |
| deck.gl | package | **Avoid for now** | High | Low at this scale | n/a | n/a | v9.4 Sep 2026; MIT |
| HIFLD transmission lines (archives) | dataset | **Investigate (frozen snapshot only)** | Medium | Medium | authoritative-origin, archived | national, frozen | HIFLD Open shut down Aug 2025 |
| EIA-860 / 860M | dataset | **Investigate** | Low–Medium | Medium | authoritative (plants only) | complete for ≥1 MW plants | monthly/annual |
| PyPSA-USA / GridSFM | modeled network | **Inspiration only** | High | Low for demo | modeled / inferred | national model | active/2026 |
| Protomaps / OpenFreeMap basemaps | basemap | **Avoid (Agent 2 shipped)** | — | — | community-maintained | — | out of scope |

---

## 5. Detailed findings (deltas and specifics)

### 5.1 MapLibre `feature-state` for hover + selection (Adopt)
- **URLs:** hover example `https://maplibre.org/maplibre-gl-js/docs/examples/create-a-hover-effect/`;
  fit-to-bounds and fly-to examples in `https://maplibre.org/maplibre-gl-js/docs/examples/`.
- **Take:** `setFeatureState({source, id}, {hover:true})` plus a separate
  `selected` state for the open drawer pair, read via
  `['case', ['boolean', ['feature-state','selected'], false], …]` in paint.
- **Why it fits now:** the acceptance bar for the opportunity experience is
  "selection syncs list, map, and drawer." `feature-state` is the idiomatic way
  to do that without re-filtering layers, and it does **not** touch Agent 2's
  basemap or controls.
- **Concern:** needs stable feature IDs across reloads (Section 3, item 12).
- **Classification:** interaction pattern (n/a). **License:** BSD-3 docs.

### 5.2 OpenInfraMap voltage pattern → line **width** (Adopt pattern only)
- **URL:** `https://github.com/openinframap/openinframap` (see the power style
  file for the `[voltage, color]` step table and `null` fallback).
- **Take:** the *pattern* — one table of voltage bands compiled into a single
  `['step', ['to-number', …], …]` expression with an explicit "unknown voltage"
  style. Bind it to **line width**, not color, because GridLock color is bound
  to utility.
- **Classification:** community-maintained (OSM-derived reference). Write
  GridLock's own table; credit OpenInfraMap (BSD-3) if adapted closely.

### 5.3 Census Gazetteer files for local search (Adopt)
- **URL:** `https://www.census.gov/geographies/reference-files/2024/geo/gazetter-file.html`.
- **Take:** place/county names + GEOIDs + internal-point lat/long. Filter to GA
  and SC, ship a tiny static JSON, search locally, fly-to on select.
- **Distinct from counties:** Gazetteer = point search index (open target).
  Cartographic **boundary polygons** = Agent 2's claimed county layer. Keep them
  separate; do not draw boundaries from Gazetteer data.
- **Classification:** authoritative. **Cite:** "U.S. Census Bureau Gazetteer
  Files, 2024" (U.S. federal government work, public domain).

### 5.4 GA/SC OSM power extract (Investigate — evidence only)
- **URLs:** Geofabrik Georgia `https://download.geofabrik.de/north-america/us/georgia.html`;
  US index (incl. South Carolina) `https://download.geofabrik.de/north-america/us.html`;
  osmium tags-filter `https://docs.osmcode.org/osmium/latest/osmium-tags-filter.html`.
- **Take:** `power=line|minor_line|cable|substation` and
  `construction:power=line`; `voltage` is volts, semicolon-separated highest
  first — parse the first, treat unparseable as unknown. Build a versioned
  GeoJSON with a manifest recording OSM timestamp and the share of features with
  `voltage`/`operator`. **Do not render** in this task.
- **Why gated now:** transmission-infra rendering is *open* scope but *unclaimed*
  and not yet specced. Produce the facts; the owner decides on rendering.
- **Classification:** community-maintained. **License:** ODbL — "© OpenStreetMap
  contributors" wherever rendered; keep derivation reproducible.

### 5.5 Packages: geocoder, layer control, inspector, Turf (Investigate)
- **maplibre-gl-geocoder** accepts a custom `forwardGeocode`, so it can search a
  **local** index with no external API. Public **Nominatim** is **Avoid**: its
  policy caps 1 req/s, requires identifying headers, and **forbids autocomplete**.
- **maplibre-gl-layer-control** manages a "Background" group that could collide
  with Agent 2's basemap; prefer a **hand-rolled** GridLock-only legend, or if
  used, pass an explicit `layers` list and disable background/style editing.
- **maplibre-gl-inspect** is a dev-only property inspector; exclude from the
  demo build. Any of these change dependencies → **explicit owner approval**.
- **Turf.js**: display helpers only (`bbox` for fit-to-pair, `midpoint` for
  connector labels). Never compute authoritative distance/tier client-side.
- **Classification:** n/a (tooling).

---

## 6. Constraints that must remain unchanged

- Approved-only matching and the **40 km** threshold; tiers **1.6 / 8 / 40 km**
  are challenge parameters, not tunables.
- Tier intervals half-open `[lo, hi)`; touching = intersect or ≤ 0.001 km.
- Authoritative distance / tier / opportunity computation stays in **Agent 1's
  backend engine**. Client math is display-only.
- `geometry_confidence` is exactly `endpoint_pair` or `endpoint_only`; never call
  either a surveyed route. Four projects are endpoint-only.
- No runtime calls to public **Overpass** or **Nominatim**.
- Modeled/inferred grids (PyPSA-USA, GridSFM) never shown as authoritative.
- The **116.993 km** GPC-004 ↔ DESC-003 figure is a diagnostic on two inferred
  points, **not** a project-to-project distance; the pair is **ineligible**.
- The **cost/savings estimator is disabled**; quote no savings figure.
- No dependency, lockfile, schema, or migration change without explicit approval.
- **Do not** edit `README.md`, `AGENT_STATUS.md`, Agent 2's basemap/controls, or
  the (claimed) county-boundary files.

---

## 7. Data classification key (applied throughout)

- **observed** — directly measured/recorded from the physical world.
- **authoritative** — from an official primary source (Census, EIA, utility IRP filings).
- **community-maintained** — crowd-sourced (OpenStreetMap and derivatives).
- **modeled** — computed by a model/simulation (PyPSA-USA, GridSFM).
- **inferred** — GridLock-side guess/proxy (e.g. the GPC-004 / DESC-003 substation proxy points; `H-` hypothesis rows).

---

## 8. Upgrade path (only if triggered)

Default delivery is **static GeoJSON**. Move to **PMTiles + Tippecanoe** only if
a measured extract exceeds comfortable in-browser size (rule of thumb: the
combined GA/SC power GeoJSON is heavy enough to hurt first paint, or the feature
count makes `feature-state` sluggish). Measure before adding a tile pipeline.

---

## 9. Ranked first-task options — each with the required coordination fields

Every option below carries the five required fields:
**(a) Agent 2 already implemented any part?** · **(b) Must wait for Agent 2's PR
to merge?** · **(c) Overlap / no-overlap status** · **(d) Buildable independently
of Agent 1's engine?** · **(e) Data classification.**

Shared-file note: most UI options touch `frontend/src/App.jsx`, which Agent 2
also edits. That is a *file* overlap requiring coordination, distinct from a
*feature* overlap with shipped work.

### Option 1 — Hover + selected feature states  ★ recommended first
- **Scope:** `feature-state` hover + a `selected` state that highlights the
  chosen pair's two projects and their connector; selection syncs list ↔ map ↔
  drawer; closing clears it. No basemap or control changes.
- **(a) Agent 2 already did part?** No — Agent 2 shipped basemap + Nav/Scale/Fit/
  Reset, not per-feature selection styling.
- **(b) Wait for Agent 2's PR?** No functional dependency. Coordinate on
  `App.jsx` edits to avoid a merge conflict; not a blocker.
- **(c) Overlap status:** **No feature overlap.** File-level overlap on `App.jsx` only.
- **(d) Independent of Agent 1's engine?** Yes — reads whatever pair objects the
  UI already has; adds no distance/tier math.
- **(e) Data classification:** n/a (interaction over existing data).

### Option 2 — Voltage-driven line width
- **Scope:** one data-driven `line-width` step expression from project voltage
  bands with an explicit "voltage not published" width; color stays utility-bound.
- **(a) Agent 2 already did part?** No.
- **(b) Wait for Agent 2's PR?** No.
- **(c) Overlap status:** **No feature overlap.** `App.jsx` layer-style file overlap only.
- **(d) Independent of Agent 1's engine?** Yes, **if** the voltage field is in the
  payload; verify the field name. No engine change needed.
- **(e) Data classification:** styling pattern is community-maintained (OpenInfraMap);
  the voltage values themselves are authoritative (from IRP/SCRTP filings) where present.

### Option 3 — Fit-to-**pair** on selection
- **Scope:** selecting a pair fits *both* geometries with drawer-aware padding;
  honors `prefers-reduced-motion` with an instant jump.
- **(a) Agent 2 already did part?** **Partially adjacent.** Agent 2 shipped
  **Fit-to-projects** (fit *all*). This is fit-to-*selected-pair* — a different
  behavior — but it must reuse, not duplicate or fight, Agent 2's camera logic.
- **(b) Wait for Agent 2's PR?** **Prefer yes.** Build on the merged Fit control
  so there is one camera/padding convention; otherwise risk two competing
  fit behaviors.
- **(c) Overlap status:** **Partial overlap** with shipped Fit-to-projects; must
  extend it, not replace it.
- **(d) Independent of Agent 1's engine?** Yes — needs only client-side pair geometry.
- **(e) Data classification:** n/a (camera behavior).

### Option 4 — Local search (projects + GA/SC Gazetteer places & counties)
- **Scope:** search box over project names + a static GA/SC Gazetteer subset;
  select a project → open drawer, select a place/county → fly to it. No external
  geocoder.
- **(a) Agent 2 already did part?** No — geocoding is explicitly open/unclaimed.
- **(b) Wait for Agent 2's PR?** No hard dependency. If it flies to a **county**,
  it can optionally use Agent 2's county bbox once that merges — a soft, additive
  dependency, not a blocker.
- **(c) Overlap status:** **No feature overlap** with shipped work; **soft
  touch-point** with Agent 2's claimed county layer (consume its bbox if present).
- **(d) Independent of Agent 1's engine?** Yes.
- **(e) Data classification:** **authoritative** (Census Gazetteer 2024); project
  names are authoritative from filings.

### Option 5 — Source / freshness / confidence strip
- **Scope:** compact per-layer strip: source name, snapshot date, and the
  geometry note "straight lines between published endpoints — not surveyed
  routes"; visible in live / local / API-unavailable states.
- **(a) Agent 2 already did part?** No.
- **(b) Wait for Agent 2's PR?** No.
- **(c) Overlap status:** **No feature overlap.** Legend-area `App.jsx` file overlap only.
- **(d) Independent of Agent 1's engine?** Yes — displays existing provenance
  fields; strong support for the debug agent's evidence audit.
- **(e) Data classification:** n/a (displays existing labels: authoritative /
  community-maintained / inferred as already tagged per record).

### Option 6 — Hand-rolled GridLock-only legend + layer toggles
- **Scope:** toggles for GridLock layers only (project lines, endpoints,
  connectors, dismissed pairs). **Never** toggles basemap or county layers.
- **(a) Agent 2 already did part?** No — layer controls are explicitly open. But
  the basemap and county layers it would sit beside are Agent 2's.
- **(b) Wait for Agent 2's PR?** **Prefer yes**, to agree on layer IDs and ensure
  the toggle list excludes Agent 2's basemap/county layer IDs.
- **(c) Overlap status:** **Medium risk** — must be scoped to GridLock layer IDs
  only; coordinate IDs with Agent 2 first.
- **(d) Independent of Agent 1's engine?** Yes.
- **(e) Data classification:** n/a (visibility control).

### Option 7 — Dev-only inspector (maplibre-gl-inspect)
- **Scope:** property inspector behind a dev flag; absent from the demo build.
- **(a) Agent 2 already did part?** No.
- **(b) Wait for Agent 2's PR?** No, but it touches shared map init — coordinate.
- **(c) Overlap status:** **Low overlap** (map initialization is shared).
- **(d) Independent of Agent 1's engine?** Yes, once the **dependency change is
  approved** (owner sign-off required).
- **(e) Data classification:** n/a (dev tooling).

### Option 8 — GA/SC OSM power extract (data only, not rendered)
- **Scope:** reproducible Geofabrik → osmium → GeoJSON procedure + manifest
  (OSM timestamp, feature counts, `voltage`/`operator` completeness). Nothing rendered.
- **(a) Agent 2 already did part?** No — transmission infra is open and unclaimed.
- **(b) Wait for Agent 2's PR?** No.
- **(c) Overlap status:** **No overlap** (data/docs only). If a rendering task
  follows, that would need its own owner decision.
- **(d) Independent of Agent 1's engine?** Yes — context data, never an engine input.
- **(e) Data classification:** **community-maintained** (OSM, ODbL).

---

## 10. Recommended smallest proof of concept (describe, do not code)

**"Selected pair, clearly shown."** Combine Option 1 (selection states) with the
pair-aware half of Option 3, layered strictly on top of Agent 2's shipped
basemap and camera controls:

1. Selecting an opportunity in the list sets a `selected` feature-state on both
   its projects and the connector; the map highlights them and the drawer opens.
2. The camera fits the selected pair using Agent 2's existing padding convention
   (extend, don't fork), honoring reduced-motion.
3. Deselect clears state and the drawer.

**Acceptance:** selection stays in sync across list, map, and drawer; no basemap
or control change; no new authoritative distance computed client-side; no
savings claim; works on mobile widths. This proves the interaction spine without
touching any claimed or shipped surface, and gives the debug agent a clean,
low-risk artifact to audit.

---

## 11. Sources

- U.S. Census Bureau — Cartographic Boundary Files (2024):
  `https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html`
  (public domain). *For reference only — counties are Agent 2's claimed scope.*
- U.S. Census Bureau — Gazetteer Files (2024):
  `https://www.census.gov/geographies/reference-files/2024/geo/gazetter-file.html` (public domain).
- MapLibre GL JS docs & examples: `https://maplibre.org/maplibre-gl-js/docs/` (BSD-3).
- OpenInfraMap: `https://github.com/openinframap/openinframap` (BSD-3; OSM data).
- Geofabrik downloads: `https://download.geofabrik.de/north-america/us.html` (OSM/ODbL).
- osmium tags-filter: `https://docs.osmcode.org/osmium/latest/osmium-tags-filter.html`.
- Nominatim usage policy: `https://operations.osmfoundation.org/policies/nominatim/`.

*Maintenance signals and repository observations were gathered on
September 27, 2026 and will go stale. Content from third-party sources was
summarized and paraphrased for licensing compliance; verify against the primary
sources before acting.*
