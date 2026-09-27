# GridLock — Deployment & Run Guide

How to run GridLock in each supported mode, what environment variables matter,
how to health-check it, how to start from a clean clone, how to build for
production, and how to recover during a live demo.

Prerequisites: Python 3.11–3.13, Node 18+ (22.x recommended), and Docker Desktop
(only for the PostGIS mode).

---

## Modes at a glance

| Mode | Command | `/opportunities` source | Needs Docker? |
|---|---|---|---|
| Frontend dev | `npm run dev` | static fixtures | no |
| API file mode | `uvicorn gridlock.api:app` | `data/approved/projects_approved.geojson` (empty → `[]`) | no |
| API + PostGIS | `docker compose up --build` | PostGIS query over ingested rows | yes |

---

## 1. Frontend development mode

```bash
cd frontend
npm install
npm audit                 # expect 0 high / 0 critical
npm run dev               # http://localhost:5173
```

Vite serves the map UI on `http://localhost:5173`. In dev the frontend reads
static fixtures under `frontend/public/static/` (candidate/fixture data for
display only — see `docs/DATA_LIMITATIONS.md`). It does not require the API to
render.

## 2. API — file mode (no database)

Uses the file-based deterministic engine. It reads
`data/approved/projects_approved.geojson`, which is empty, so `/opportunities`
correctly returns `[]`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install --prefer-binary -r backend/requirements.txt
cd backend
uvicorn gridlock.api:app --reload         # http://localhost:8000
```

Expected:
- `GET /health` → `{"ok": true, "backend": "file"}`
- `GET /opportunities` → `[]`
- `GET /projects` → the (empty) approved FeatureCollection

## 3. PostGIS / docker-compose mode

Brings up `postgis/postgis:16-3.4` (applies `db/schema.sql` on first init) plus
the API. The API ingests `data/normalized/projects_proposed.csv` **once at
startup** (FastAPI lifespan handler / `python -m gridlock.migrate`), then serves
the PostGIS-backed read-only `/opportunities` query.

```bash
cp .env.example .env      # set POSTGRES_PASSWORD
docker compose up --build
# db  -> localhost:5432
# api -> localhost:8000
```

Expected:
- `GET /health` → `{"ok": true, "backend": "postgis"}`
- `GET /opportunities` → `[]` (nothing approved yet; the query is approved-only)

To run the PostGIS integration tests directly (matches CI):

```bash
docker compose up -d db
export GRIDLOCK_DATABASE_URL=postgresql://postgres:$POSTGRES_PASSWORD@localhost:5432/gridlock
cd backend && pytest                      # 24 passed, 0 skipped (engine suite, with a live database)
```

> The "24 passed, 0 skipped" figure is the **backend engine suite** at Agent 1's
> tested SHA — not the final integrated project test count.

## 4. Environment variables

| Variable | Used by | Purpose |
|---|---|---|
| `POSTGRES_PASSWORD` | docker-compose (`db`, `api`) | PostGIS superuser password; substituted into the compose `GRIDLOCK_DATABASE_URL`. |
| `DATABASE_URL` | `.env` template | Convenience connection string for local tooling. |
| `GRIDLOCK_DATABASE_URL` | API + tests | When set, the API and the integration tests use PostGIS; when unset, the API falls back to file mode and the 4 DB tests skip. |

Copy `.env.example` to `.env` and set a local `POSTGRES_PASSWORD` before using
the PostGIS mode. Never commit a real secret; `.env` is git-ignored.

The frontend has no required environment variables for local dev. If a future
build needs to point the UI at a non-default API origin, introduce a
`VITE_`-prefixed variable (Vite only exposes `VITE_*` to client code) rather
than hardcoding a URL.

## 5. Health checks

- **API:** `curl -s localhost:8000/health` → `{"ok": true, "backend": "file"}`
  in file mode or `"postgis"` when a database is configured. The `backend`
  field tells you which path is live.
- **Database (compose):** the `db` service uses `pg_isready` as its healthcheck;
  `docker compose ps` shows it healthy before the API begins ingesting.
- **End-to-end:** `curl -s localhost:8000/opportunities` should return `[]`
  today (empty approved set). A non-`[]` response would mean approved data
  exists — verify that is intended.

## 6. Clean-clone setup

```bash
git clone https://github.com/Abhiramcodegit/gridlock-sperry-hackathon
cd gridlock-sperry-hackathon

# backend (file mode)
python -m venv .venv && source .venv/bin/activate
pip install --prefer-binary -r backend/requirements.txt
cd backend && pytest            # 20 passed, 4 skipped without a database
uvicorn gridlock.api:app        # http://localhost:8000

# frontend (separate terminal)
cd frontend && npm install && npm run dev   # http://localhost:5173
```

For the full PostGIS path from a clean clone, add `cp .env.example .env`, set
`POSTGRES_PASSWORD`, then `docker compose up --build`.

## 7. Production build

- **Frontend:** `cd frontend && npm run build` emits static assets to
  `frontend/dist/`. Preview locally with `npm run preview`. Serve `dist/` behind
  any static host / CDN.
- **API:** build the image from `backend/Dockerfile` (the compose `api` service
  does this). In a real deployment, run migrations/ingest once
  (`python -m gridlock.migrate`) against the target database, then start
  `uvicorn gridlock.api:app` behind a process manager or container orchestrator,
  with `GRIDLOCK_DATABASE_URL` pointed at managed PostgreSQL + PostGIS.
- Keep secrets in the deployment platform's secret store, not in the image.

## 8. Fallback / demo recovery

If something fails mid-demo, degrade gracefully in this order:

1. **PostGIS mode misbehaving?** Drop to **API file mode**
   (`uvicorn gridlock.api:app` with `GRIDLOCK_DATABASE_URL` unset). It returns
   the same correct `[]` for `/opportunities` without needing Docker.
2. **API unavailable entirely?** The **frontend dev server** renders from static
   fixtures under `frontend/public/static/` and does not require the API.
3. **Docker won't start?** Skip PostGIS; run the backend test suite in file mode
   (`cd backend && pytest` → 20 passed, 4 skipped) to demonstrate the engine
   logic, and cite the verified CI run for the PostGIS path (below).
4. **Need to prove the PostGIS path without running it live?** Cite the green CI
   run — see the verification caveat below.

Talking point during any fallback: the empty `/opportunities` result is the
**correct** answer, so a fallback that still returns `[]` is fully faithful to
the real system.

## 9. Actions-run verification caveat

The Phase 3 PostGIS verification was executed in GitHub Actions, not on the demo
machine (local Docker was unavailable on the original dev machine). The evidence:

- **Green run:** [Actions run 36287891004](https://github.com/Abhiramcodegit/gridlock-sperry-hackathon/actions/runs/36287891004)
- **Tested engine SHA:** `02752cb1edb4085c8e80a328deac637685af3def`
- **Result:** 24 passed, 0 skipped (four PostGIS integration tests executed)
- **Verified:** 2026-09-27 (recorded in
  [`ENGINE_PHASE3.md`](ENGINE_PHASE3.md), verification commit `2eff3d0`)

**Caveat:** the repository is private, so the Actions run page requires
authenticated GitHub access — an unauthenticated viewer cannot open the URL. The
result is attested by Agent 1 and recorded in-repo. A human with repo access
should glance at the run page to independently confirm. This count is the
**engine suite only**, not the final integrated project test count.

---

Related: [`../README.md`](../README.md) · [`DATA_LIMITATIONS.md`](DATA_LIMITATIONS.md) ·
[`DEMO_FLOW.md`](DEMO_FLOW.md) · [`ENGINE_PHASE3.md`](ENGINE_PHASE3.md) ·
[`SETUP.md`](SETUP.md)
