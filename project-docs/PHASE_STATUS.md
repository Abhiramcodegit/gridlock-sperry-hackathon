# GridLock — Phase Status Tracker

> Living document. Updated every PR. Last updated: 2026-09-26 (Phase 1 in progress)

---

## Current Phase: 1 — Source Validation

**Branch:** `research/source-validation`  
**PR:** [#2 (DRAFT)](https://github.com/Abhiramcodegit/gridlock-sperry-hackathon/pull/2)  
**Status:** ⏳ Awaiting Checkpoint 1 approval

### Checkpoint 1 Blockers

- [ ] Kiro re-confirms `npm audit` 0 high/0 critical after maplibre-gl v6.4.1 upgrade
- [ ] Kiro confirms map renders with v6 (tiles load, layers display, fitBounds works)
- [ ] Abhiram reviews 18 DESC projects in `data/SOURCE_MANIFEST.md` against SCRTP PDF
- [ ] Abhiram confirms `data/approved_projects.csv` is genuinely empty
- [ ] Abhiram confirms hypotheses folder is flagged non-approved
- [ ] Georgia Power source (SRC-003) resolved: approved or rejected
- [ ] Abhiram gives explicit Phase 1 approval

---

## Phase History

### Phase 0 — Scaffold ✅

**Branch:** `backend/geospatial-engine`  
**PR:** [#1 (open)](https://github.com/Abhiramcodegit/gridlock-sperry-hackathon/pull/1)  
**Completed:** 2026-09-26

Deliverables:
- [x] Deterministic engine (`engine.py`) — distance, tier, timeline, scoring
- [x] FastAPI + Uvicorn (`api.py`)
- [x] Config (`config.py`) — tier thresholds, scoring weights
- [x] 17 pytest tests — all passing
- [x] PostGIS schema (`db/schema.sql`)
- [x] Docker Compose
- [x] React + MapLibre GL JS frontend (map, ranked list, evidence drawer, offline fallback)
- [x] Reproducibility fix: pyproj pinned to 3.7.0 (prebuilt cp313 wheel)
- [x] Security fix: maplibre-gl 4.7.1 → 6.4.1 (GHSA-jrc7-96c5-q579)
- [x] Security fix: Vite pinned + server.host: false (GHSA-4w7w-66w2-5vf9)

---

## Upcoming Phases

### Phase 2 — Geometry + DB (BLOCKED)

**Blocked by:** Checkpoint 1 approval

Planned deliverables:
- [ ] Geocoding agent: EIA-860 + OSM lookup → WGS84 coords per project
- [ ] Coordinate CSV with provenance + geometry_status
- [ ] DB loader script (INSERT approved rows into PostGIS)
- [ ] ST_Distance verification test for at least 1 real project pair

### Phase 3 — Engine Integration

**Blocked by:** Phase 2 completion

Planned deliverables:
- [ ] Engine reads from PostGIS, not test fixtures
- [ ] `/opportunities` returns real ranked results
- [ ] Map renders real project layers
- [ ] Evidence drawer shows real distance + timeline numbers

### Phase 4 — Demo Polish

**Blocked by:** Phase 3 completion

Planned deliverables:
- [ ] Fully cached demo path (no live API calls required)
- [ ] Cost/impact estimator in evidence drawer
- [ ] "Import New Utility" demo mode (agent-assisted ingestion)
- [ ] Final npm audit + pytest run
- [ ] README final pass
