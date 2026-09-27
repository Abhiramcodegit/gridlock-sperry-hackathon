# Phase 3 — Deterministic PostGIS Engine

First real engine commit on `backend/geospatial-engine`.

## What it does

- **Ingest** (`gridlock/db.ingest_csv`): loads `data/normalized/projects_proposed.csv`
  into the PostGIS `projects` table. Proposed rows only by default. A row's
  `geom` is set only when the CSV supplies GeoJSON; otherwise it stays NULL.
  The CSV confidence vocabulary (`inferred`, `unresolved`, ...) is mapped to
  the schema's CHECK vocabulary (`inferred_endpoints`, ...).
- **Candidate filter**: `candidate_pairs` view uses
  `ST_DWithin(a.geom, b.geom, 40000)` (geography → meters, geodesic) to select
  cross-utility pairs (`a.utility < b.utility`) within 40 km.
- **Distance**: `ST_Distance` on `geography`, computed **only for pairs where
  both projects are `approved` and have geometry**.
- **Temporal overlap**: overlapping days on the construction window, reported
  separately from proximity. NULL when either window is unknown — never
  silently treated as overlapping.
- **API**: `GET /opportunities` returns a ranked JSON array. Uses PostGIS when
  `GRIDLOCK_DATABASE_URL` is set, else the file-based deterministic engine.

## Current real result

No geometry has been human-approved yet (approved set is empty; all rows are
`proposed`). Therefore `GET /opportunities` returns `[]`. **This is the correct
answer, not a bug** — the candidate query only considers approved rows.

The only two rows with geometry (GPC-004, DESC-003) are ~117 km apart, so even
if approved they would be rejected by the 40 km `ST_DWithin` filter (see
`docs/PROXY_DISTANCE_RESULT.md`).

## Running the PostGIS integration tests

The unit suite runs without a database. The integration tests
(`backend/tests/test_db_integration.py`) require a real PostGIS instance and
skip automatically when `GRIDLOCK_DATABASE_URL` is unset.

```bash
# from repo root
docker compose up -d db          # postgis/postgis:16-3.4, applies db/schema.sql
export GRIDLOCK_DATABASE_URL=postgresql://postgres:$POSTGRES_PASSWORD@localhost:5432/gridlock
cd backend && pytest             # 4 previously-skipped DB tests now execute
```

The integration tests cover: ingestion of proposed rows; the empty-result case
(nothing approved); the honest-negative case (GPC-004 ↔ DESC-003 rejected by the
40 km filter); and a positive control (a synthetic <40 km approved cross-utility
pair does produce an opportunity), proving the empty result is data-driven, not
a broken query.

## Verification status (local, no DB available on this machine)

- `pytest`: 20 passed, 4 skipped (DB integration — no local Postgres/Docker).
- `GET /opportunities` via FastAPI TestClient (file mode): returns `[]`, HTTP 200.
- Schema SQL contains the required constructs (ST_DWithin 40000, ST_Distance,
  ST_ShortestLine, cross-utility join, temporal overlap, approved-only filter).
- **NOT YET RUN against a live PostGIS instance** — the 4 integration tests must
  be executed in a Docker-capable environment to complete Phase 3 verification.
