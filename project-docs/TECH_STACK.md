# GridLock — Tech Stack

> Living document. Updated every phase. Last updated: 2026-09-26 (Phase 1)

---

## Frontend

### MapLibre GL JS `6.4.1`
- **Role:** WebGL map rendering, vector tile display, GeoJSON layer management
- **Why:** Open-source (no Mapbox token), full GeoJSON/layer API, active maintenance, ships prebuilt WebGL workers
- **Alternatives considered:** Mapbox GL JS (proprietary token required), Leaflet (no WebGL, no vector tiles), deck.gl (overkill for our use case)
- **Security note:** Upgraded from 4.7.1 to 6.4.1 to patch GHSA-jrc7-96c5-q579 (XSS in DOM.sanitize). Production dep.
- **v4→v6 breaking changes applied:** namespace import, `setWorkerUrl()`, CSS import

### React `18.3.1`
- **Role:** Component tree, state management for opportunity list + evidence drawer
- **Why:** Widely understood, hooks-based, no build complexity beyond Vite
- **Alternatives considered:** Vanilla JS (simpler but no component reuse), Svelte (smaller but less familiar)

### Vite `5.4.21`
- **Role:** Dev server + production bundler
- **Why:** Fast HMR, native ESM, works cleanly with React and MapLibre v6 ESM-only build
- **Security note:** `server.host: false` in vite.config.js neutralises GHSA-4w7w-66w2-5vf9 path-traversal. Dev-only dep.

---

## Backend

### FastAPI `0.115.5` + Uvicorn `0.32.0`
- **Role:** REST API serving `/health`, `/projects`, `/opportunities`
- **Why:** Async, auto-docs (OpenAPI), minimal boilerplate, Python-native
- **Alternatives considered:** Flask (no async), Django REST (too heavy)

### Shapely `2.0.6`
- **Role:** In-memory geometry operations (distance, buffer, intersection) for unit tests and pre-DB validation
- **Why:** Standard Python geospatial library, GEOS-backed, integrates with pyproj for CRS-aware ops
- **Note:** Production distance calculations use PostGIS `ST_Distance`, not Shapely, for correctness on large datasets

### pyproj `3.7.0`
- **Role:** Coordinate reference system transformations (WGS84 ↔ UTM)
- **Why:** 3.7.0 ships PROJ 9.4.1 bundled in the wheel — no system PROJ install needed
- **Critical pin:** Do NOT upgrade to 3.8.x until cp313-macosx_10_9_x86_64 wheel is confirmed on PyPI. 3.8.0 has no Intel macOS cp313 wheel and fails on source build.

### psycopg `3.2.3` (binary)
- **Role:** PostgreSQL driver (async-capable, binary protocol)
- **Why:** psycopg3 is the current standard; binary variant avoids libpq system dependency
- **Alternatives considered:** psycopg2 (older, more system deps), asyncpg (async-only, less flexible)

### pytest `8.3.3`
- **Role:** Backend test runner
- **Tests:** 17 unit tests covering distance calculation, tier assignment, timeline logic, scoring, edge cases
- **All passing on Python 3.11, 3.12, 3.13**

---

## Database

### PostgreSQL 16 + PostGIS 3.4
- **Role:** Authoritative geometry store; spatial distance calculations
- **Why:** PostGIS `ST_Distance` (geography type) returns spheroidal distance in metres on full geometries — not centre-to-centre approximations. `ST_DWithin` uses spatial indexes for efficient 40 km pre-filtering.
- **Alternatives considered:** SQLite + SpatiaLite (no full spheroidal distance), DuckDB spatial (no production-grade spatial index)

---

## Infrastructure

### Docker + docker-compose
- **Role:** Local PostGIS container
- **Why:** One command setup, no system Postgres install required, matches production config

---

## Planned Additions (Phase 2+)

| Tool | Phase | Role |
|---|---|---|
| EIA-860 dataset | 2 | Public substation coordinates for geocoding |
| OpenStreetMap Nominatim | 2 | Substation name → coordinate lookup |
| LangGraph (optional) | 3 | Multi-agent orchestration if ingestion pipeline needs it |
| Playwright | 3 | Fallback web scraping for filing portals |
