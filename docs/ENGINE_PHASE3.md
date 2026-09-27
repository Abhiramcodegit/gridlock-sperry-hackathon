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
  Ingestion runs ONCE at app startup (FastAPI lifespan handler) and via the
  `python -m gridlock.migrate` CLI — NOT on every request. The endpoint itself
  is a read-only query. (Addresses the review note about per-request ingest.)

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

## Verification via GitHub Actions CI

Local Docker is unavailable on the dev machine (macOS 12, unsupported by current
Docker Desktop and Homebrew), so the live PostGIS run is executed by the GitHub
Actions workflow `.github/workflows/engine-ci.yml`: it spins up
`postgis/postgis:16-3.4` as a service, applies `db/schema.sql` manually (service
containers do not honor the docker-compose init-script mount), sets
`GRIDLOCK_DATABASE_URL`, and runs `pytest -v`. A green run is the verification
record.

Expected on a green run: **24 passed, 0 skipped** (20 unit/proxy-distance
+ 4 DB integration).

CI runs `pytest` only. The DB integration tests call `db.find_opportunities()`
directly against live PostGIS; CI does NOT hit the `/opportunities` HTTP endpoint
against the database.

## Verification status

- `pytest` (local, no DB): 20 passed, 4 skipped (20 = 17 engine + 3
  proxy-distance; the 4 DB integration tests skip without a database).
- `GET /opportunities` via FastAPI TestClient (file mode): returns `[]`, HTTP 200.
- Schema SQL contains the required constructs (ST_DWithin 40000, ST_Distance,
  ST_ShortestLine, cross-utility join, temporal overlap, approved-only filter).
- Live PostGIS run: **verified green** — see confirmed record below.

Phase 3 PostGIS integration verified via GitHub Actions: pytest 24 passed,
0 skipped (20 unit/proxy-distance + 4 DB integration against
postgis/postgis:16-3.4).

db.find_opportunities() -> [] against live PostGIS (correct — no approved
geometry pair qualifies).

Tested commit: 02752cb1edb4085c8e80a328deac637685af3def

CI run: https://github.com/Abhiramcodegit/gridlock-sperry-hackathon/actions/runs/36287891004

Verified: 2026-09-27
