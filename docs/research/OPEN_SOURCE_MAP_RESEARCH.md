# Open-Source Map Research for Gridlock

Prepared by P3 (Perplexity Session 3). Research and documentation only. No application code, dependencies, branches' application files, or database objects were changed.

- Research date: September 27, 2026. Maintenance signals were read from public GitHub pages on that date and will go stale.
- Handoff branch base: `origin/main` at `1c31e2e6efc72599317de739f98ec55bcb6f6417`.
- Repo evidence: commit messages on `main` (earlier at `85a7138`) and directory listings at `1c31e2e`. File contents were not read.

> Method note, stated plainly: P3 cannot choose or confirm which underlying model runs a given step. To honor the "two models" request, this report was produced as two deliberately separate passes: **Pass A (Discovery)**, which looked for the strongest projects, datasets, and UX ideas, and **Pass B (Practicality)**, which judged fit for this repo, GA/SC coverage, browser cost, maintenance, and conflicts with the basemap work. Section 2 reconciles them. Treat this as two review lenses, not proof that two distinct models were invoked.

---

## 1. Executive Summary — the 5 strongest ideas, ranked by impact vs effort

| Rank | Idea | Impact | Effort | Why it ranks here |
|---|---|---|---|---|
| 1 | **Hover and selected-feature states with MapLibre `feature-state`** for project lines, endpoints, and closest-point connectors | High | Low | Native MapLibre pattern with an official example; no new dependency; makes pairs readable immediately. |
| 2 | **Voltage-driven styling adapted from OpenInfraMap's `voltage_scale` step expression**, applied to GridLock's own project voltages | High | Low | Proven power-map convention; one data-driven expression; no data acquisition needed. |
| 3 | **Local search over project names plus Census Gazetteer places and counties for GA/SC**, with fly-to | Medium–High | Low–Medium | Census Gazetteer files are small, authoritative, and static. Avoids the public Nominatim API, whose policy forbids autocomplete. |
| 4 | **Per-layer source, freshness, and confidence indicator** (dataset snapshot date, source document, geometry_confidence, "not a surveyed route") | High for judges | Low | Directly supports GridLock's truth-labeling rules; little code. |
| 5 | **A versioned, regenerable GA/SC OpenStreetMap power extract** (Geofabrik state PBFs → osmium `tags-filter` → static GeoJSON) as *context-only* existing-grid data | Medium–High | Medium | The only practical open source of current line/substation geometry after HIFLD Open shut down. **Gated:** the current UI spec lists the existing-lines layer as out of scope; the owner must decide. |

---

## 2. Model Agreement, Disagreement, and Unique Finds

### Agreed (both passes)

- **Plain static GeoJSON is likely sufficient for a two-state scope.** A tile pipeline is not the default; measure first.
- **Use `feature-state` for hover/selection** rather than re-filtering layers.
- **OpenInfraMap is the best design reference** for power symbology, but take the pattern, not the code verbatim.
- **OpenStreetMap is the practical source for existing lines and substations**, but only through a static, versioned extract, never a live Overpass call at runtime.
- **Authoritative opportunity computation stays in the backend.** Client-side Turf.js, if used, is for display helpers only.
- **Modeled grids (PyPSA-USA, GridSFM) are inspiration only** and must never appear as authoritative infrastructure.

### Disagreed (and how it was reconciled)

| Topic | Pass A (Discovery) | Pass B (Practicality) | Reconciled position |
|---|---|---|---|
| Existing-grid delivery | PMTiles + Tippecanoe from the start (best-in-class, serverless) | Static GeoJSON first; the two-state dataset is probably small | **GeoJSON first**, with a measured trigger to move to PMTiles (Section 8). |
| Layer control | Install `maplibre-gl-layer-control` (React, TypeScript, feature-rich) | Hand-roll a small legend/toggle; the package's "Background" group manages basemap layers and could collide with the basemap agent | **Hand-rolled legend by default**; the package is "investigate further" with basemap grouping disabled. |
| deck.gl | Use it for arcs and GPU picking | Overkill for tens of features; adds a large dependency and a second rendering path | **Avoid for now.** |
| HIFLD transmission lines | Authoritative-looking federal dataset | HIFLD Open was shut down in August 2025; remaining copies are archives that won't be updated | **Investigate only as a frozen, labeled snapshot**; never a runtime dependency. |
| Geocoder control | Use `maplibre-gl-geocoder` with Nominatim, as in MapLibre's example | Nominatim's policy forbids client-side autocomplete; the package's last release was February 2025 | **Local search first**; the geocoder control is "investigate further," only with a local data provider. |

### Unique finds

- **Pass A only:** GridSFM builds US grid models from OpenStreetMap through to optimal power flow, a clear example of *modeled* topology. OSM also has a `construction:power=line` tag for lines under construction. The Awesome Electrical Grid Mapping list is CC0 and was actively updated in September 2026.
- **Pass B only:** HIFLD Open shut down on August 26, 2025. Nominatim's usage policy explicitly addresses LLM-suggested use and bans autocomplete. Census Gazetteer files give internal-point lat/long for places and counties. The frontend on `main` is JavaScript (`.jsx`/`.js` files in `frontend/src`, `vite.config.js`), not TypeScript.

---

## 3. Current Project Assumptions — what a coding agent must verify in the repo

Evidence comes from commit messages, directory listings at `1c31e2e`, and project-lead messages, not from reading file contents. Each item must be checked before work starts.

| # | Assumption | Evidence / conflict | Verify |
|---|---|---|---|
| 1 | Frontend is React + **TypeScript** | **Conflict:** `frontend/src` on `main` contains `App.jsx`, `App.test.jsx`, `candidateFixture.js`, `main.jsx`, `style.css`, and `test/`, with `vite.config.js`. That's JavaScript. | Treat it as JavaScript unless proven otherwise |
| 2 | MapLibre GL JS version | A commit pins `maplibre-gl` 6.11.2, Vite 5.4.21, and a build target of es2022 | `frontend/package.json` and lockfile (read only) |
| 3 | Backend is Python/FastAPI | Commits mention pytest and a backend; FastAPI isn't confirmed | `backend/` entry point |
| 4 | Distance method | The brief says PostGIS. The project lead's latest ruling says the display method string is "haversine, local planar segment math" and that the PostGIS reference is inaccurate | Engine code; the UI must use the approved string |
| 5 | Opportunities = approved pairs within 40 km | Binding rule; not to be changed | Engine filter and tier enums |
| 6 | Tier intervals | Half-open `[lo, hi)`; touching = intersect or ≤ 0.001 km | API contract |
| 7 | Project geometry | Only two geometry types: `endpoint_pair` (straight line between published endpoints) and `endpoint_only` (a point) | API contract and dataset |
| 8 | Map styling bindings | endpoint_pair = solid line in utility color; endpoint_only = ringed point; connector = dashed line in tier color; shared facility = filled diamond | UI spec |
| 9 | Existing-lines layer | **Declared out of scope in the current UI spec.** Any task that renders existing grid data needs the owner's explicit approval | Owner decision |
| 10 | Canonical data | `Projects_Overlaps.xlsx` (challenge starter dataset), Dominion's 2024–2028 $2M-and-above PDF, Georgia Power's 2025 IRP Volume 3 PDF | Repo `data/` |
| 11 | Basemap/boundaries | Another agent owns the basemap and state/county boundaries; branch `frontend/openfreemap-basemap` exists | Coordinate before touching style setup, map initialization, or boundary layers |
| 12 | Branches | Map wiring (PR #5), map-wiring tests (PR #6), and demo/deployment/limitations docs (PR #7) are merged into `main` at `1c31e2e` | Branch from the latest `main` |
| 13 | UI spec location | `docs/specs/UI_COPY.md`, `DEMO_NARRATIVE.md`, and `COST_MODEL.md` were **not present on `main` at `1c31e2e`** | Confirm where the approved copy lives |
| 14 | Agent conventions | Root `AGENT_STATUS.md` exists; no `AGENTS.md` or `.kiro/` steering directory was found on `main` | Read `AGENT_STATUS.md`; don't edit it |

---

## 4. Candidate Comparison Table

| Candidate | Type | Verdict | Difficulty | User value | Data nature | GA/SC coverage | Maintenance (as of Sep 2026) |
|---|---|---|---|---|---|---|---|
| OpenInfraMap | Design inspiration / adapt a pattern | Inspiration only (adapt pattern) | Low | High | Community (OSM) | Good for major lines; varies | 262 stars, BSD-3; active project |
| MapLibre `feature-state` hover example | Adapt a pattern | Adopt | Low | High | n/a | n/a | Official docs, MapLibre 6.11.2 example |
| MapLibre large-GeoJSON guide | Adapt a pattern | Adopt | Low | Medium | n/a | n/a | Official docs |
| Census Gazetteer files | Use a dataset | Adopt | Low | Medium–High | Authoritative | Complete for places/counties | 2024 files published |
| OSM power tagging + Geofabrik extracts + osmium | Use a dataset | Investigate further (gated) | Medium | Medium–High | Community | Uneven; measure | GA/SC PBFs updated daily |
| maplibre-gl-inspect | Install a package (dev only) | Adopt (dev only) | Low | Low (dev) | n/a | n/a | v1.9.0, Aug 2026; supports MapLibre 3–6 |
| maplibre-gl-layer-control | Install a package | Investigate further | Low–Medium | Medium | n/a | n/a | v0.17.4, Jun 2026; 22 stars; mostly one maintainer |
| maplibre-gl-geocoder | Install a package | Investigate further (local provider only) | Medium | Medium | n/a | n/a | v1.8.0, Feb 2025 |
| Public Nominatim API | Hosted API | Avoid | — | — | Community | — | Policy bans autocomplete |
| PMTiles | Install a package / format | Investigate further (upgrade path) | Medium | Medium | n/a | n/a | Very active; Sep 2026 commits; BSD-3 |
| Tippecanoe | Build tool | Investigate further (upgrade path) | Medium | Medium | n/a | n/a | Maintained by Felt |
| Protomaps Basemaps | Basemap | Avoid (duplicates basemap work) | — | — | Community | — | Owned by another agent's scope |
| Turf.js | Install a package | Investigate further (display helpers only) | Low | Low–Medium | n/a | n/a | v7.3.3, Jan 2026; MIT |
| deck.gl | Install a package | Avoid (for now) | High | Low for this scope | n/a | n/a | v9.4.0, Sep 2026; very active |
| HIFLD transmission lines (archives) | Use a dataset | Investigate further (frozen snapshot only) | Medium | Medium | Authoritative-origin, archived | National; frozen | HIFLD Open shut down Aug 2025 |
| EIA-860 / 860M | Use a dataset | Investigate further | Low–Medium | Medium | Authoritative (plants only) | Complete for plants ≥ 1 MW | Monthly/annual releases |
| PyPSA-USA | Modeled network | Inspiration only | High | Low for demo | Modeled | National model | v0.9.0, Aug 2026 |
| GridSFM | Modeled network | Inspiration only | High | Low for demo | Modeled / inferred | US models via OSM | Last commit May 2026; no releases |
| Awesome Electrical Grid Mapping | Catalog | Inspiration only | Low | Medium (research) | Mixed | Catalog | Updated Sep 7, 2026; CC0 |
| Martin (PostGIS vector tile server) | Tile service | Avoid for now | High | Low for this scope | n/a | n/a | Not checked by P3 |

---

## 5. Detailed Candidate Findings

### 5.1 OpenInfraMap
- **URL:** https://github.com/openinframap/openinframap · live site https://openinframap.org
- **Most useful file:** `web/src/style/style_oim_power.ts` — https://github.com/openinframap/openinframap/blob/main/web/src/style/style_oim_power.ts
- **What to take:** The file defines a `voltage_scale` table of `[voltage, color]` rows with a `null` fallback row (gray `#7A7A85`). A helper builds a MapLibre `['step', ['to-number', coalesce(get(field), 0)], …]` expression from that table. GridLock can adopt the same *pattern*: one table of voltage bands mapped to colors or line widths, compiled into a single expression, with an explicit "unknown voltage" style. P3 read only fragments of this file through code search; the full band list and widths should be read directly.
- **Architecture note:** The repository topics list PostGIS, imposm3, tegola, and maplibre-gl-js, a full planet-scale pipeline. That's far more than GridLock needs.
- **Recommendation type:** adapt a pattern / design inspiration
- **Compatibility:** Pattern is plain MapLibre style JSON; works in React (TS or JS).
- **GA/SC coverage:** Reflects whatever OSM contains for GA/SC.
- **Data nature:** community-maintained (OSM).
- **Maintenance:** 262 stars, 54 forks, 32 contributors, BSD-3.
- **Difficulty:** Low. **User value:** High.
- **Concerns:** Don't copy its full style or color set verbatim; write GridLock's own table. Also, GridLock's project colors are bound to *utility* (solid line in utility color), so voltage might drive **width**, not color, to avoid conflicting with the spec.
- **License note:** BSD-3 code; if patterns are adapted closely, credit OpenInfraMap in the README.
- **Verdict:** Inspiration only (adapt the pattern).

### 5.2 MapLibre GL JS official examples and guides
- **URLs:** hover effect https://maplibre.org/maplibre-gl-js/docs/examples/create-a-hover-effect/ · large-data guide https://maplibre.org/maplibre-gl-js/docs/guides/large-data/ · example index https://maplibre.org/maplibre-gl-js/docs/examples/ (see "Fly to a location," "Fit to the bounds of a LineString," "Display a popup on click," "Style lines with a data-driven property," "PMTiles source and protocol")
- **What to take:**
  - `setFeatureState({source, id}, {hover: true})` with a `['case', ['boolean', ['feature-state','hover'], false], …]` paint expression. The same approach gives a separate `selected` state for the open drawer pair.
  - From the large-data guide: strip unused properties, round coordinates to about 6 decimals, simplify, minify, compress, set a source `maxZoom` of about 12 for points, and set layer `minzoom` above 0.
- **Recommendation type:** adapt a pattern. **Compatibility:** native. **Difficulty:** Low. **Value:** High.
- **Concerns:** `feature-state` requires stable feature IDs (numeric `id` or `promoteId`). The project/pair IDs must be stable across API reloads.
- **License note:** MapLibre GL JS is BSD-3; examples are documentation.
- **Verdict:** Adopt.

### 5.3 U.S. Census Gazetteer files
- **URL:** https://www.census.gov/geographies/reference-files/2024/geo/gazetter-file.html · record layouts https://www.census.gov/programs-surveys/geography/technical-documentation/records-layout/gaz-record-layouts.html
- **What to take:** Places and counties with names, GEOIDs, and internal-point latitude/longitude. The national places file is about 1.2 MB, and single-state files are available. Filter to GA and SC, then ship as a tiny static JSON for search.
- **Recommendation type:** use a dataset. **Compatibility:** static JSON in any frontend; Python can pre-process it.
- **GA/SC coverage:** complete for incorporated places, CDPs, and counties.
- **Data nature:** authoritative.
- **Difficulty:** Low. **Value:** Medium–High.
- **Concerns:** Internal points aren't centroids of built-up areas; fly-to should use a zoom that shows context, or the boundary bbox if the basemap agent supplies it.
- **License note:** U.S. federal government work; cite "U.S. Census Bureau Gazetteer Files, 2024."
- **Verdict:** Adopt.

### 5.4 OpenStreetMap power tagging, Geofabrik extracts, and osmium
- **URLs:** `power=line` https://wiki.openstreetmap.org/wiki/Tag:power=line · `voltage` https://wiki.openstreetmap.org/wiki/Key:voltage · `power=substation` https://wiki.openstreetmap.org/wiki/Tag:power=substation · Geofabrik Georgia https://download.geofabrik.de/north-america/us/georgia.html · US index (includes South Carolina) https://download.geofabrik.de/north-america/us.html · osmium tags-filter https://docs.osmcode.org/osmium/latest/osmium-tags-filter.html
- **What to take:**
  - Tags: `power=line` (towers), `power=minor_line`, `power=cable`, `power=substation`, and `construction:power=line` for lines under construction.
  - `voltage` is in volts; multiple values are semicolon-separated with the highest first (e.g. `275000;132000`). Parse the first value as the max voltage, and treat anything unparseable as "unknown."
  - Build a static extract: Georgia PBF (339 MB) and South Carolina PBF (156 MB) → `osmium tags-filter` for power features → convert to GeoJSON → strip to the needed properties → version with a manifest recording the OSM timestamp.
- **Recommendation type:** use a dataset.
- **GA/SC coverage and quality:** **Unknown until measured.** Major transmission lines are commonly mapped in the US, but voltage/operator completeness varies. The first extract should report counts of lines with and without `voltage` and `operator`.
- **Data nature:** community-maintained.
- **Difficulty:** Medium. **Value:** Medium–High.
- **Concerns:** Must be labeled as OSM context, never as utility-verified. Must never be used to infer GridLock project routes. And the existing-lines layer is currently out of scope (Section 3, item 9).
- **License note:** ODbL; show "© OpenStreetMap contributors" whenever it's rendered, and keep the extract's derivation reproducible.
- **Verdict:** Investigate further (gated by owner decision).

### 5.5 maplibre-gl-inspect
- **URL:** https://github.com/maplibre/maplibre-gl-inspect · docs https://maplibre.org/maplibre-gl-inspect/
- **What to take:** A dev-only toggle that shows every source feature and its properties on hover, useful for checking that feature IDs, tier values, and geometry_confidence arrive correctly.
- **Recommendation type:** install a package (dev only). **Compatibility:** supports MapLibre GL JS v3 through v6; TypeScript; ESM.
- **Maintenance:** v1.9.0 (Aug 16, 2026), MapLibre 6 support added, dependabot activity Sep 21, 2026. BSD-3.
- **Difficulty:** Low. **Value:** Low for users, High for developers.
- **Concerns:** Must be excluded from the demo build or hidden behind a dev flag, because its popups show raw properties. Installing it changes dependencies, which requires explicit owner approval.
- **Verdict:** Adopt (dev only), subject to approval.

### 5.6 maplibre-gl-layer-control
- **URL:** https://github.com/opengeos/maplibre-gl-layer-control
- **What to take:** Visibility toggles, opacity sliders, layer symbols, React component, ARIA/keyboard support.
- **Recommendation type:** install a package, or adapt the pattern.
- **Compatibility:** TypeScript and React. **MapLibre 6 compatibility is not stated in the README; verify.**
- **Maintenance:** v0.17.4 (Jun 26, 2026), 34 releases, 22 stars, mostly one maintainer. MIT.
- **Difficulty:** Low–Medium. **Value:** Medium.
- **Concerns:** Its "Background" group and basemap-style detection manage basemap layers, which is the other agent's scope. Its style editor lets users change colors, which would undermine the legend's fixed truth semantics. If used, pass an explicit `layers` list, disable the style editor, and disable background presets.
- **Verdict:** Investigate further. The default recommendation is a small hand-rolled legend.

### 5.7 maplibre-gl-geocoder and Nominatim
- **URLs:** https://github.com/maplibre/maplibre-gl-geocoder · Nominatim policy https://operations.osmfoundation.org/policies/nominatim/
- **What to take:** The control accepts a custom `forwardGeocode` function, so it can search a **local** index (projects plus Gazetteer places and counties) with no external API.
- **Maintenance:** v1.8.0 (Feb 17, 2025); ISC. MapLibre 6 compatibility is not confirmed by P3.
- **Nominatim policy (required disclosure):** The public API allows at most 1 request per second, requires an identifying User-Agent or Referer, and **forbids autocomplete**. It also states that LLMs may only suggest it while pointing to the policy, and that it must not be built into vibe-coding platforms as a generic geocoder.
- **Verdict:** Geocoder control: investigate further (local provider only). Public Nominatim: avoid.

### 5.8 PMTiles
- **URL:** https://github.com/protomaps/PMTiles · MapLibre example "PMTiles source and protocol" in the examples index
- **What to take:** A single-file tile archive served from static storage with HTTP range requests; no tile server.
- **Maintenance:** very active (commits Sep 16, 2026; the viewer app is updated to MapLibre 6.9); spec v3; BSD-3 code; spec CC0.
- **Difficulty:** Medium (needs a build step plus range-request-capable hosting; local dev needs a server that supports range requests).
- **Concerns:** Adds a pipeline step for what may be a small dataset.
- **Verdict:** Investigate further (upgrade path, Section 8).

### 5.9 Tippecanoe
- **URL:** https://github.com/felt/tippecanoe
- **What to take:** Builds vector tiles from GeoJSON and writes `.pmtiles` directly. `-zg` guesses the max zoom; `--drop-densest-as-needed` keeps tiles under the size limit; `-y`/`-x` keep or drop attributes; `-A` embeds attribution.
- **Maintenance:** officially maintained by Felt. P3 did not verify the license text; check `LICENSE.md`.
- **Difficulty:** Medium (native binary; Homebrew on macOS, build from source on Ubuntu).
- **Verdict:** Investigate further (only if Section 8's trigger is hit).

### 5.10 Protomaps Basemaps
- **URL:** https://github.com/protomaps/basemaps
- **Assessment:** A basemap product, which is the other agent's scope.
- **Verdict:** Avoid (duplicate work).

### 5.11 Turf.js
- **URL:** https://github.com/Turfjs/turf · https://turfjs.org
- **What to take:** Client-side display helpers only: `bbox` for fit-to-pair, `midpoint` for connector label placement, `nearestPointOnLine` for *visual* hover hints.
- **Maintenance:** v7.3.3 (Jan 28, 2026), MIT, TypeScript.
- **Concerns:** Must never compute tiers or distances shown as authoritative; those come from the backend. Import individual modules (e.g. `@turf/bbox`) to keep the bundle small. Installing it changes dependencies, which requires explicit owner approval.
- **Verdict:** Investigate further (display helpers only).

### 5.12 deck.gl
- **URL:** https://github.com/visgl/deck.gl
- **Assessment:** Excellent for millions of features; a `@deck.gl/maplibre` integration for MapLibre v4–6 exists (Aug 2026). GridLock renders tens of projects and pairs, so it would add weight and a second picking/highlight model.
- **Maintenance:** v9.4.0 (Sep 5, 2026), 14.6k stars, very active; MIT.
- **Verdict:** Avoid for now; revisit only for national-scale work.

### 5.13 HIFLD transmission lines (archived copies)
- **URLs:** HIFLD status https://www.hsdl.org/hifld/ · Data Rescue Project copy https://portal.datarescueproject.org/datasets/hifld-open-transmission-lines/ · Living Atlas archive https://www.arcgis.com/home/item.html?id=d4090758322c4d32a4cd002ffaa0aa12
- **Facts:** HIFLD Open was shut down in August 2025. One public GIS portal states that the Living Atlas layer remains available but will not be updated. EIA's FAQ says EIA is not the source of transmission line data and points to HIFLD.
- **What to take:** At most, a frozen, clearly dated comparison snapshot for research.
- **Data nature:** authoritative in origin, now archived and frozen.
- **Concerns:** Frozen currency, uncertain provenance of the archive copies, and terms that must be checked in each copy.
- **Verdict:** Investigate further (frozen snapshot only; never a runtime dependency).

### 5.14 EIA-860 / EIA-860M
- **URLs:** https://www.eia.gov/electricity/data/eia860/ · https://www.eia.gov/electricity/data/eia860m/ · EIA FAQ on transmission data https://www.eia.gov/tools/faqs/faq.php?id=567&t=1
- **What to take:** Generator- and plant-level data with coordinates for plants of 1 MW or more (existing and planned). That's useful context for "why is a line here," but it isn't transmission geometry.
- **Data nature:** authoritative (plants only).
- **Verdict:** Investigate further (optional context layer; lower priority than the GridLock-owned layers).

### 5.15 PyPSA-USA
- **URL:** https://github.com/PyPSA/pypsa-usa · docs https://pypsa-usa.readthedocs.io
- **Assessment:** A capacity-expansion and power-flow model of the US bulk system. Its network is **modeled**.
- **Maintenance:** v0.9.0 (Aug 28, 2026), MIT.
- **Verdict:** Inspiration only (future network analysis; must be labeled "modeled").

### 5.16 GridSFM (Microsoft)
- **URL:** https://github.com/microsoft/GridSFM
- **Assessment:** An AC-OPF framework with a pipeline that builds US grid models from OpenStreetMap data and a browser viewer. Its topology is **modeled or inferred** from OSM.
- **Maintenance:** 46 commits, last May 22, 2026, no releases, 60 stars, MIT. Tested on Ubuntu/macOS; uses a Julia pipeline.
- **Verdict:** Inspiration only. Its viewer is a reference for network-view UX; nothing should enter GridLock's authoritative layers.

### 5.17 Awesome Electrical Grid Mapping
- **URL:** https://github.com/open-energy-transition/Awesome-Electrical-Grid-Mapping
- **Assessment:** A CC0 catalog maintained by the MapYourGrid initiative, with a Grid Data Explorer and a Global Transmission Length Index (CC BY 4.0). Updated Sep 7, 2026. Its US sub-national coverage should be checked for GA/SC-specific sources.
- **Verdict:** Inspiration only (a research index).

### 5.18 Martin (PostGIS to vector tiles)
- **URL:** https://github.com/maplibre/martin
- **Assessment:** Cited in MapLibre's large-data guide for serving tiles from a database. P3 did not check its maintenance signals.
- **Verdict:** Avoid for this scope (adds a service to operate).

---

## 6. Georgia and South Carolina Infrastructure Data Options

| Option | What it provides | Nature | Currency | Coverage confidence | Recommended use |
|---|---|---|---|---|---|
| GridLock dataset (`Projects_Overlaps.xlsx` + utility PDFs) | Proposed projects, endpoints, in-service dates, published costs | Authoritative for GridLock's scope | As delivered | Canonical | Primary layer; unchanged |
| OSM via Geofabrik GA/SC extracts | Existing lines, cables, substations, voltage/operator where tagged | Community | Daily extracts; version the snapshot | Unknown until measured | Optional context layer (owner decision) |
| HIFLD archives | National transmission lines | Authoritative origin, archived | Frozen (Aug 2025 or earlier) | National; frozen | Research comparison only |
| EIA-860 / 860M | Power plants ≥ 1 MW with coordinates | Authoritative | Annual / monthly | Complete for its scope | Optional context |
| Census Gazetteer | Places and counties with internal points | Authoritative | 2024 vintage | Complete | Search index |
| PyPSA-USA / GridSFM | Modeled network topology | Modeled | Model releases | National models | Research only; never rendered as infrastructure |

Labeling rule for every non-GridLock layer: show its source, snapshot date, and data nature in the legend and the popup. Modeled or inferred connections get a distinct style and the word "modeled."

---

## 7. Reusable Map Features — ranked

| Rank | Feature | Source pattern | Difficulty | Value | Basemap overlap |
|---|---|---|---|---|---|
| 1 | Hover + selected states for projects, endpoints, connectors | MapLibre `feature-state` example | Low | High | None |
| 2 | Voltage-driven line width (color stays bound to utility) | OpenInfraMap `voltage_scale` step pattern | Low | High | None |
| 3 | Fit-to-pair with drawer-aware padding, honoring `prefers-reduced-motion` | MapLibre "Fit to the bounds of a LineString" / "Fly to a location" | Low | Medium–High | None |
| 4 | Local search (projects + GA/SC places/counties) | Census Gazetteer + optional geocoder control with local provider | Low–Medium | Medium–High | Low (uses its own data) |
| 5 | Source, freshness, and confidence strip per layer | GridLock truth rules | Low | High for judges | None |
| 6 | Clickable popups/drawer sync (map click opens the same drawer as list click) | MapLibre "Display a popup on click" | Low | Medium | None |
| 7 | Hand-rolled legend with layer toggles for GridLock layers only | Pattern from layer-control package | Low–Medium | Medium | **Medium:** must not toggle basemap layers |
| 8 | Dev-only feature inspector | maplibre-gl-inspect | Low | Developer | None |
| 9 | Existing-grid context layer (OSM) | Geofabrik + osmium + static GeoJSON | Medium | Medium–High | Low; **gated by owner** |
| 10 | Future: network/topology analysis | PyPSA-USA, GridSFM | High | Low now | None |

---

## 8. Architecture Comparison and Recommendation

Scope: existing-grid context layers for Georgia and South Carolina only.

| Criterion | A. Hosted third-party APIs/tiles | B. Static GeoJSON | C. Self-hosted PMTiles | D. PostGIS + vector-tile service | E. Hybrid |
|---|---|---|---|---|---|
| Setup difficulty | Low–Medium (keys, terms) | **Low** | Medium (Tippecanoe + range-request hosting) | High (tile server, DB tuning) | Medium–High |
| Hosting needs | Third-party dependency | Any static host / Vite `public/` | Static host with HTTP range requests | Running service + DB | Mixed |
| Download size | Per-view tiles | Whole file up front (gzip helps) | Per-view tiles | Per-view tiles | Mixed |
| Browser performance | Good | Good at small/medium size; degrades with large line sets | Very good | Very good | Very good |
| Data updates | Provider-controlled (freshness unknown) | Regenerate the file and bump its version | Rebuild the archive | Live from DB | Mixed |
| Local development | Needs network/keys | **Trivial** | Needs a range-capable server | Needs Docker service | Complex |
| Scalability | High | Low–Medium | High | High | High |
| Truth-labeling control | Low | **High** | High | High | Medium |

**Recommendation: B, static, versioned GeoJSON.** For two states it is probably sufficient, easiest to reproduce, and gives full control over labeling. It must follow MapLibre's large-data guidance: drop unused properties, round coordinates to about 6 decimals, simplify, minify, gzip, and set layer `minzoom` so lines don't draw at state-wide zooms if they're too dense.

**Upgrade trigger to C (PMTiles), stated as a heuristic to measure, not a verified threshold:** move only if the gzipped GeoJSON is still large enough to noticeably slow first load, or if panning becomes sluggish on a mid-range laptop. The coding agent should record file size, load time, and frame behavior in the proof of concept and let the owner decide.

**Not recommended:** A (a runtime third-party dependency, and public Overpass/Nominatim endpoints are unsuitable), D (a service to operate for a small, mostly static dataset), E (complexity without a demonstrated need).

---

## 9. Practical Attribution Notes — short checklist only

- [ ] Any OSM-derived layer shown: display "© OpenStreetMap contributors" (ODbL), https://www.openstreetmap.org/copyright
- [ ] Census Gazetteer used for search: credit "U.S. Census Bureau Gazetteer Files, 2024" in the README
- [ ] EIA data shown: cite the EIA form and release date
- [ ] HIFLD archive used: cite the specific archive copy and its date; label it "archived, not updated"
- [ ] Patterns adapted from OpenInfraMap (BSD-3): credit in the README; don't copy large code blocks
- [ ] Packages installed: keep their license files through the normal npm/pip mechanisms
- [ ] Modeled data (PyPSA-USA, GridSFM): never rendered as infrastructure; cite if referenced in docs

---

## 10. Ranked Initial Implementation Choices

The owner chooses. None of these changes the approved-only rule or the 40 km threshold, and all opportunity computation stays in the backend. Every frontend option touches `frontend/src/App.jsx` or components mounted from it, which is Agent 2's UI area; coordinate before starting.

### Option 1 — Hover and selected states
- **Exact scope:** Add `hover` and `selected` feature states to the project line, endpoint point, and connector layers. Hover thickens or brightens the feature; selected persists while the drawer is open and clears on close.
- **Why users notice:** Pairs become obvious, and the map and drawer feel connected.
- **Likely files:** `frontend/src/App.jsx` (map and layer definitions); related tests in `frontend/src/App.test.jsx`.
- **Dependencies:** stable feature IDs from the API (`promoteId` or numeric `id`).
- **Difficulty / impact:** Low / High.
- **Acceptance criteria:** Hovering any GridLock feature changes only that feature. Opening a pair marks both projects and its connector as selected. Closing clears the selection. No basemap layer changes. Colors still match the UI spec's utility/tier bindings.
- **Basemap overlap:** None. **Independent:** Yes.

### Option 2 — Voltage-driven line width
- **Exact scope:** One data-driven `line-width` expression from project voltage bands, with an explicit width for "voltage not published." Color remains the utility color.
- **Why users notice:** Bigger projects read as bigger at a glance.
- **Likely files:** layer style definitions in `frontend/src/App.jsx`; legend.
- **Dependencies:** the voltage field is present in the API payload (verify its name against the P2 contract).
- **Difficulty / impact:** Low / Medium–High.
- **Acceptance criteria:** Every project renders; unknown voltage uses the documented fallback width; the legend shows the width bands; no color changes.
- **Basemap overlap:** None. **Independent:** Yes.

### Option 3 — Fit-to-pair on selection
- **Exact scope:** Selecting a pair (list or map) fits both geometries in view with padding that accounts for the drawer, and honors `prefers-reduced-motion` with an instant jump.
- **Why users notice:** No manual panning to find the pair.
- **Likely files:** map component and selection handler in `frontend/src/App.jsx`.
- **Dependencies:** pair geometry available client-side.
- **Difficulty / impact:** Low / Medium–High.
- **Acceptance criteria:** Both projects and the connector are fully visible and not hidden by the drawer; reduced-motion users get no animation; repeated clicks don't stack animations.
- **Basemap overlap:** None. **Independent:** Yes.

### Option 4 — Local search (projects plus GA/SC places and counties)
- **Exact scope:** A search box over GridLock project names plus a static GA/SC subset of Census Gazetteer places and counties. Selecting a project opens its drawer; selecting a place flies to it. No external geocoding API.
- **Why users notice:** Demo navigation by name ("Savannah," "Thurmond," a project name).
- **Likely files:** a new search component under `frontend/src/`; a static JSON in `frontend/public/`; a README credit (requires owner approval because the root README must not be overwritten).
- **Dependencies:** Gazetteer download and one-time filtering.
- **Difficulty / impact:** Low–Medium / Medium–High.
- **Acceptance criteria:** Works offline; no network calls to geocoders; results are labeled "Project," "Place," or "County"; keyboard accessible.
- **Basemap overlap:** Low (fly-to only; doesn't touch boundaries). **Independent:** Yes.

### Option 5 — Source, freshness, and confidence strip
- **Exact scope:** A compact strip or legend footer showing, per GridLock layer, the source name, dataset snapshot date, and the geometry note "Straight lines between published endpoints — not surveyed routes."
- **Why users notice:** Judges see provenance without opening the drawer.
- **Likely files:** legend area in `frontend/src/App.jsx`; strings from the approved UI copy spec.
- **Dependencies:** dataset snapshot date available from the API or bundle; location of the approved UI copy confirmed.
- **Difficulty / impact:** Low / High (for judging).
- **Acceptance criteria:** Uses only approved UI strings; is visible in the live, local, and unavailable API states; shows no source the repo doesn't hold.
- **Basemap overlap:** None. **Independent:** Yes.

### Option 6 — Hand-rolled legend with GridLock-only layer toggles
- **Exact scope:** Toggles for project lines, endpoints, connectors, and dismissed pairs. It never touches basemap or boundary layers.
- **Why users notice:** They can declutter the map during the demo.
- **Likely files:** legend and layer-visibility code in `frontend/src/App.jsx`.
- **Dependencies:** a stable list of GridLock layer IDs.
- **Difficulty / impact:** Low–Medium / Medium.
- **Acceptance criteria:** Each toggle affects only its GridLock layer; the state survives drawer open/close; the legend labels match the UI spec exactly.
- **Basemap overlap:** Medium risk. Agree on layer IDs with the basemap agent first. **Independent:** Mostly.

### Option 7 — Dev-only inspector
- **Exact scope:** Add maplibre-gl-inspect behind a development flag.
- **Why users notice:** They don't. Developers catch data bugs faster.
- **Likely files:** map initialization in `frontend/src/App.jsx`; `frontend/package.json` and lockfile (dependency change requires explicit owner approval).
- **Dependencies:** a new dev dependency.
- **Difficulty / impact:** Low / Low (users), High (developers).
- **Acceptance criteria:** Absent from the production build; toggles on in dev; no raw-property popups in the demo.
- **Basemap overlap:** Low (map initialization is shared; coordinate). **Independent:** Yes, once the dependency change is approved.

### Option 8 — GA/SC OSM power extract (data only, no rendering)
- **Exact scope:** A documented, regenerable procedure that produces a versioned GeoJSON of OSM power lines and substations for GA and SC, with a manifest of the OSM timestamp, feature counts, and the share of features with `voltage`/`operator`. Nothing is rendered.
- **Why users notice:** Not immediately. It produces the facts needed to decide whether an existing-grid layer is worth showing.
- **Likely files:** `data/` scripts and docs.
- **Dependencies:** Geofabrik downloads; osmium; GDAL/ogr2ogr (local tools, not app dependencies).
- **Difficulty / impact:** Medium / Medium (decision value).
- **Acceptance criteria:** Reproducible from documented commands; the output includes ODbL attribution and a snapshot date; no runtime Overpass calls; size and completeness numbers are reported.
- **Basemap overlap:** None. **Independent:** Yes. **Gated:** The existing-lines layer is currently out of scope; this produces evidence only.

---

## 11. Recommended Smallest Proof of Concept — describe, do not code

**"Selected pair, clearly shown."** This combines Options 1 and 3 on existing GridLock data only:

1. With the current dataset, hover any project line, endpoint, or connector; only that feature highlights.
2. Click a flagged pair in the sidebar. The map fits both projects and their connector into view, accounting for the drawer, and the pair takes a persistent "selected" style.
3. Close the drawer. The selection clears, and the view stays put.
4. Record three measurements for the owner: time-to-interactive, frame smoothness during hover, and whether any basemap layer was touched (it must not be).

Why this is the smallest proof: it uses no new dependency and no new data, involves no backend change, stays out of the basemap agent's scope, and makes the demo's lead finding easier to see.

---

## 12. Risks and Unknowns

| Risk / unknown | Impact | Mitigation |
|---|---|---|
| The frontend is JavaScript on `main`, while the brief says TypeScript | Package typing and file naming | Treat it as JavaScript unless the owner says otherwise |
| Approved UI spec files are not on `main` at `1c31e2e` | Agents could use unapproved strings | Confirm where the approved copy lives |
| The existing-lines layer is out of scope in the current spec | Options 8+ may be wasted work | Owner decision before any rendering |
| OSM GA/SC completeness is unknown | Misleading context layer | Measure with Option 8; label as community data |
| An OSM layer could be read as "the real route" of a GridLock project | Truth-rule violation | Distinct style, legend note, never snapped or joined to projects |
| HIFLD archives are frozen and their provenance varies | Stale or unclear data | Snapshot-only; dated label; not a runtime dependency |
| Layer-control package manages basemap layers | Collision with basemap agent | Hand-rolled legend by default; explicit `layers` list if the package is used |
| MapLibre 6 compatibility of layer-control and geocoder is not confirmed | Build failures | Verify before installing |
| Public Nominatim misuse | Blocked by policy; ban risk | Local search only |
| Feature IDs unstable across reloads | Hover/selected states break | Stable IDs via `promoteId` in the API contract |
| Distance-method wording conflicts across docs | Credibility with engineers | Use the approved string: "haversine, local planar segment math" |
| Maintenance signals age quickly | Stale choices | Re-check before adoption |

---

## 13. Handoff Checklist for the next coding agent

- [ ] Start with `docs/research/KIRO_START_HERE.md`.
- [ ] Locate the approved UI copy spec; use only approved strings and styles.
- [ ] Verify Section 3 assumptions 1–14 in the repo and note any mismatch.
- [ ] Read `AGENT_STATUS.md`; don't edit it.
- [ ] Confirm with the owner which Section 10 option(s) to do; don't pick one yourself.
- [ ] Confirm layer IDs and map-initialization ownership with the basemap/boundaries agent.
- [ ] Don't change the approved-only rule, the 40 km threshold, tier intervals, or backend computation.
- [ ] Don't add runtime calls to Overpass, Nominatim, or other hosted APIs.
- [ ] Don't change dependencies or lockfiles without explicit owner approval.
- [ ] If any external data is rendered, add attribution per Section 9 in the same change.
- [ ] Keep modeled or inferred grid data out of authoritative layers.
- [ ] Record measurements (size, load time, interaction smoothness) for any data-layer work.
- [ ] Re-check maintenance and compatibility signals for any package before installing it.
