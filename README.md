# GridLock

> **Sperry Hackathon 2026 — Transmission Coordination Discovery Engine**

[![Phase](https://img.shields.io/badge/phase-3%20deterministic%20engine-brightgreen)](#phase-status)
[![Engine tests](https://img.shields.io/badge/engine%20tests-24%20passed%2C%200%20skipped-brightgreen)](https://github.com/Abhiramcodegit/gridlock-sperry-hackathon/actions/runs/36287891004)
[![Phase 3 CI](https://img.shields.io/badge/Phase%203%20PostGIS%20CI-verified-brightgreen)](https://github.com/Abhiramcodegit/gridlock-sperry-hackathon/actions/runs/36287891004)
[![Security](https://img.shields.io/badge/npm%20audit-0%20high%2F0%20critical-brightgreen)](#security)

GridLock finds opportunities for electric utilities to coordinate transmission construction projects — so they can share trenches, access roads, environmental permits, and contractor mobilization instead of paying for them twice.

---

## The Problem

When two utilities plan transmission lines within kilometres of each other, on overlapping schedules, neither usually knows. Each utility hires its own contractors, pulls its own permits, and mobilizes its own crews — even when a shared right-of-way or a single permit would cover both. Industry estimates put wasted coordination costs in the tens of millions of dollars per avoided duplication. No public tool surfaces these opportunities automatically.

## What GridLock Does

1. **Ingests** publicly available transmission planning documents from utilities and regional planning authorities (SCRTP, DESC, Georgia Power).
2. **Extracts** future projects — substation names, voltages, in-service dates, text descriptions — through a verified, human-approved pipeline. No CEII data. No private sources.
3. **Geocodes** project endpoints from public sources (EIA-860, OpenStreetMap, public filings), recording every coordinate's provenance and confidence level.
4. **Computes** minimum geometry distance between every cross-utility project pair using PostGIS `ST_Distance` on full geometries — not centre-to-centre approximations.
5. **Scores** each pair on distance (40 km threshold), schedule overlap, voltage match, and confidence, using a fully deterministic engine. No AI makes the scoring decision.
6. **Presents** ranked coordination opportunities on an interactive map with a closest-point segment overlay, evidence drawer, and cost-impact estimate.

---

## Architecture

```
Public utility filing (SCRTP PDF, DESC IRP, GPC portal)
         │
         ▼
  Source Scout Agent          ←─ finds URLs, dates, publisher
         │
         ▼
  Restriction Guard           ←─ rejects CEII / access-gated / unknown provenance
         │
         ▼
  Document Extractor          ←─ project name, voltage, dates, description → CSV
         │
         ▼
  Geolocation Agent           ←─ EIA-860, OSM, public filings → WGS84 coords
         │
         ▼
  Verification Agent          ←─ cross-checks claims against source page
         │
         ▼
  ╔══ Human Approval Gate ══╗  ←─ REQUIRED before any DB write
  ║  approved_projects.csv  ║
  ╚═══════════════════╝
         │
         ▼
  PostgreSQL + PostGIS
         │
         ▼
  Deterministic Engine        ←─ ST_Distance, interval logic, scoring
         │
         ▼
  FastAPI  /opportunities
         │
         ▼
  React + MapLibre GL JS      ←─ ranked list, map, evidence drawer
```

**Rule:** Agents research and extract. PostGIS calculates. Humans approve data before it enters the DB.

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Map UI | MapLibre GL JS | 6.4.1 |
| Frontend framework | React | 18.3.1 |
| Frontend bundler | Vite | 5.4.21 |
| API | FastAPI + Uvicorn | 0.115.5 / 0.32.0 |
| Geospatial engine | Shapely + pyproj | 2.0.6 / 3.7.0 |
| Database | PostgreSQL 16 + PostGIS 3.4 | — |
| DB driver | psycopg (v3, binary) | 3.2.3 |
| Container | Docker + docker-compose | — |
| Test runner | pytest | 8.3.3 |

Full rationale for every choice: [`project-docs/TECH_STACK.md`](project-docs/TECH_STACK.md)

---

## Folder Structure

```
gridlock-sperry-hackathon/
├── README.md                            ← you are here
├── AGENT_STATUS.md                      ← multi-agent status board
├── .env.example                         ← copy to .env before running
├── docker-compose.yml                   ← PostGIS + API
├── backend/
│   ├── requirements.txt                 ← pinned, wheels-only
│   ├── Dockerfile
│   ├── gridlock/
│   │   ├── engine.py                    ← deterministic distance/tier/score (file mode)
│   │   ├── db.py                        ← PostGIS candidate query + ST_Distance
│   │   ├── migrate.py                   ← one-time ingest CLI
│   │   ├── api.py                       ← FastAPI endpoints
│   │   └── config.py                    ← 40 km threshold + scoring weights
│   └── tests/
│       ├── test_engine.py               ← engine unit tests
│       ├── test_proxy_distance_gpc004_desc003.py  ← 116.993 km negative result
│       └── test_db_integration.py       ← PostGIS integration (skips without DB)
├── frontend/
│   ├── package.json                     ← pinned deps, security overrides
│   ├── index.html
│   ├── public/static/                   ← projects_approved.geojson, opportunities.json
│   └── src/                             ← React + MapLibre app
├── db/
│   └── schema.sql                       ← PostGIS tables, ST_DWithin/ST_Distance, spatial index
├── data/
│   ├── approved/
│   │   └── projects_approved.geojson    ← INTENTIONALLY EMPTY (nothing promoted)
│   ├── normalized/
│   │   └── projects_proposed.csv        ← 34 proposed rows (19 DESC, 9 GPC, 6 hypotheses)
│   ├── raw/                             ← captured source material (desc/, gpc/, osm/)
│   ├── manifests/sources.json
│   ├── provenance/verification_ledger.csv
│   ├── SOURCE_MANIFEST.md               ← verified sources + extracted projects
│   ├── VERIFICATION_LEDGER.md           ← per-source provenance audit
│   └── REJECTED_SOURCES.md              ← rejected/pending sources log
├── docs/
│   ├── SETUP.md                         ← step-by-step local setup
│   ├── DEMO_FLOW.md                     ← 2–3 minute demo script
│   ├── ENGINE_PHASE3.md                 ← deterministic PostGIS engine + CI verification
│   ├── PROXY_DISTANCE_RESULT.md         ← GPC-004 ↔ DESC-003 = 116.993 km (honest negative)
│   ├── DATA_LIMITATIONS.md              ← what the dataset does/doesn’t contain
│   ├── DECISION_LOG.md                  ← architectural decisions + rationale
│   ├── SECURITY_AUDIT.md                ← npm audit history + CVE decisions
│   └── ...                              ← additional audit/status docs
└── .github/workflows/engine-ci.yml      ← PostGIS integration tests on GitHub Actions
```

---

## Quickstart

### Prerequisites
- Python 3.11, 3.12, or 3.13
- Node 18+ (22.x recommended)
- Docker Desktop (only for the PostGIS mode)

```bash
git clone https://github.com/Abhiramcodegit/gridlock-sperry-hackathon
cd gridlock-sperry-hackathon
```

### 1. Frontend dev server
```bash
cd frontend
npm install
npm audit                # expect 0 high / 0 critical
npm run dev              # http://localhost:5173
```

### 2. API — file mode (no database)
Uses the file-based deterministic engine. Reads
`data/approved/projects_approved.geojson`, which is empty, so `/opportunities`
returns `[]` — the correct answer until data is approved.
```bash
python -m venv .venv && source .venv/bin/activate
pip install --prefer-binary -r backend/requirements.txt
cd backend
pytest                                   # 20 passed, 4 skipped (DB tests skip without a database)
uvicorn gridlock.api:app --reload        # http://localhost:8000
# GET /health        -> {"ok": true, "backend": "file"}
# GET /opportunities -> []
```

### 3. API + PostGIS via docker compose
Brings up `postgis/postgis:16-3.4` (applies `db/schema.sql`) and the API. The
API ingests `data/normalized/projects_proposed.csv` once at startup, then serves
the PostGIS-backed `/opportunities` query.
```bash
cp .env.example .env      # set POSTGRES_PASSWORD
docker compose up --build
# db  -> localhost:5432
# api -> localhost:8000  (GET /health -> {"ok": true, "backend": "postgis"})
```

To run the PostGIS integration tests directly (matches CI):
```bash
docker compose up -d db
export GRIDLOCK_DATABASE_URL=postgresql://postgres:$POSTGRES_PASSWORD@localhost:5432/gridlock
cd backend && pytest                     # 24 passed, 0 skipped (with a live database)
```

Full setup guide with troubleshooting: [`docs/SETUP.md`](docs/SETUP.md)

---

## Phase Status

| Phase | Name | Status |
|---|---|---|
| 0 | Scaffold | ✅ Complete |
| 1 | Source validation | ✅ 34 proposed rows captured with provenance |
| 2 | Candidate geometry | ✅ GPC-004 + DESC-003 inferred proxies; honest 116.993 km negative |
| 3 | Deterministic PostGIS engine | ✅ Verified — Phase 3 PostGIS CI green (24 passed, 0 skipped) at engine SHA `02752cb`, [run 36287891004](https://github.com/Abhiramcodegit/gridlock-sperry-hackathon/actions/runs/36287891004), 2026-09-27 |
| 4 | Demo & documentation | ✅ This branch |

Live multi-agent tracker: [`AGENT_STATUS.md`](AGENT_STATUS.md) ·
engine details: [`docs/ENGINE_PHASE3.md`](docs/ENGINE_PHASE3.md)

## Tests

Deterministic engine + integration suite:

- **CI (with PostGIS):** **24 passed, 0 skipped** — 17 engine + 3 proxy-distance
  + 4 DB integration, run by
  [`.github/workflows/engine-ci.yml`](.github/workflows/engine-ci.yml) against
  `postgis/postgis:16-3.4`.
- **Local (no database):** 20 passed, 4 skipped — the 4 PostGIS integration
  tests skip automatically when `GRIDLOCK_DATABASE_URL` is unset.

The integration suite includes a **positive control** (a synthetic approved
cross-utility pair under 40 km that must produce an opportunity), proving the
empty production result is data-driven rather than a broken query.

> **Scope of this count:** "24 passed, 0 skipped" is the result for **Agent 1's
> tested engine SHA `02752cb`** — the backend deterministic engine + PostGIS
> integration suite only. It is **not** the final post-integration project test
> count (frontend and other workstreams are counted separately).

> **Phase 3 PostGIS CI: verified.**
> [Actions run 36287891004](https://github.com/Abhiramcodegit/gridlock-sperry-hackathon/actions/runs/36287891004)
> · tested engine SHA `02752cb1edb4085c8e80a328deac637685af3def`
> · verified 2026-09-27 · four PostGIS integration tests executed · result:
> 24 passed, 0 skipped.
> Note: the repository is private, so the Actions run page requires
> authenticated access; this evidence is attested by Agent 1 and recorded in
> [`docs/ENGINE_PHASE3.md`](docs/ENGINE_PHASE3.md) (verification commit
> `2eff3d0`).

---

## Data & Provenance (current state)

- **34 proposed records** in `data/normalized/projects_proposed.csv`: 19 DESC,
  9 GPC, and 6 labeled hypotheses (`H-` rows). Every non-hypothesis row cites a
  public source URL, title, date, and page.
- **Approved dataset is empty.** `data/approved/projects_approved.geojson` is
  `{"features":[]}`. Nothing has been promoted, so `/opportunities` returns `[]`.
- **Only two rows carry geometry:** GPC-004 (West McIntosh substation proxy) and
  DESC-003 (Church Creek substation proxy), both `inferred`. They are
  **substation proxy points, not confirmed project routes**, which is why they
  remain in the candidate layer and were not approved.
- **DESC-002 (Okatie–McIntosh) is unresolved** — no defensible public coordinate
  was found, so **no placeholder exists**, by design.
- The two proxies are **116.993 km apart** (geodesic), outside the 40 km filter —
  an honest negative result. See
  [`docs/PROXY_DISTANCE_RESULT.md`](docs/PROXY_DISTANCE_RESULT.md).

### Data rules (non-negotiable)

1. **No CEII data.** No confidential, access-controlled, or restricted utility information.
2. **Every project row requires a cited public URL** with publisher and date.
3. **No coordinates without a public source.** Inferred geometry is labeled `inferred`; unknowns stay `unresolved` with no placeholder.
4. **Human approval required** before any row enters the approved set or the database.
5. **Hypotheses are not data.** The `H-` rows are working guesses for future research — they are never presented as confirmed projects and never appear in engine results.

---

## AI Build Workflow

This project uses two AI systems with a strict division of labour:

| System | Role |
|---|---|
| **Perplexity** | Builds and edits code/docs directly in the GitHub repo via MCP |
| **Kiro** | Runs code locally, executes tests, reports failures back |
| **You (Abhiram)** | Reviews data decisions, approves checkpoints, makes final merge calls |

Neither AI makes data approval decisions. You do.

Full workflow spec: [`project-docs/WORKFLOW.md`](project-docs/WORKFLOW.md)

---

## Documentation

- **[`docs/DEMO_FLOW.md`](docs/DEMO_FLOW.md)** — 2–3 minute demo script, including
  the presenter warning against calling the proxies verified routes.
- **[`AGENT_STATUS.md`](AGENT_STATUS.md)** — live multi-agent status board.
- [`docs/ENGINE_PHASE3.md`](docs/ENGINE_PHASE3.md) — deterministic PostGIS engine + CI verification.
- [`docs/PROXY_DISTANCE_RESULT.md`](docs/PROXY_DISTANCE_RESULT.md) — the 116.993 km honest negative.
- [`docs/DATA_LIMITATIONS.md`](docs/DATA_LIMITATIONS.md) — what the dataset does and doesn’t contain.
- [`docs/SETUP.md`](docs/SETUP.md) — step-by-step local setup.

## Security

See [`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md) for the full CVE history, decisions, and residual risks.

Current status: **0 high / 0 critical** in `npm audit` (as of 2026-09-26). Re-run at every commit.

---

## Contributing / Checkpoint Rules

- All PRs targeting `main` must start as **DRAFT**.
- Phase gates require explicit approval before the next phase starts.
- No geometry or DB writes before Phase 1 approval.
- See [`project-docs/WORKFLOW.md`](project-docs/WORKFLOW.md) for branch naming and PR rules.
