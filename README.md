# GridLock

> **Sperry Hackathon 2026 — Transmission Coordination Discovery Engine**

[![Phase](https://img.shields.io/badge/phase-1%20source%20validation-yellow)](#phase-status)
[![Tests](https://img.shields.io/badge/backend%20tests-17%2F17%20passing-brightgreen)](#backend)
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
├── README.md                        ← you are here
├── .env.example                     ← copy to .env before running
├── docker-compose.yml               ← spins up PostGIS
├── backend/
│   ├── requirements.txt             ← pinned, wheels-only
│   ├── gridlock/
│   │   ├── engine.py            ← deterministic distance/tier/score
│   │   ├── api.py               ← FastAPI endpoints
│   │   └── config.py            ← thresholds + scoring weights
│   └── tests/
│       └── test_engine.py       ← 17 pytest tests (all passing)
├── frontend/
│   ├── package.json             ← pinned deps, security overrides
│   ├── vite.config.js           ← localhost-only (security note inside)
│   └── src/
│       ├── App.jsx              ← map + sidebar + evidence drawer
│       ├── main.jsx
│       └── style.css
├── db/
│   └── schema.sql               ← PostGIS tables + spatial index
├── data/
│   ├── approved_projects.csv    ← INTENTIONALLY EMPTY (awaiting Phase 1 approval)
│   ├── SOURCE_MANIFEST.md       ← verified sources + extracted projects
│   ├── VERIFICATION_LEDGER.md   ← per-source provenance audit
│   ├── REJECTED_SOURCES.md      ← rejected/pending sources log
│   └── hypotheses/              ← working hypotheses ONLY — NOT approved data
├── docs/
│   ├── SETUP.md                 ← step-by-step local setup
│   ├── ARCHITECTURE_PROPOSAL.md
│   ├── DATA_LIMITATIONS.md      ← what the dataset does/doesn’t contain
│   ├── DECISION_LOG.md          ← every architectural decision + rationale
│   ├── SECURITY_AUDIT.md        ← npm audit history + CVE decisions
│   └── WORKSTREAM_STATUS.md
└── project-docs/                    ← living documents (updated every phase)
    ├── TECH_STACK.md
    ├── DESIGN.md
    ├── WORKFLOW.md
    ├── PHASE_STATUS.md
    └── GLOSSARY.md
```

---

## Quickstart

### Prerequisites
- Python 3.11, 3.12, or 3.13
- Node 18+ (22.x recommended)
- Docker Desktop

### Backend
```bash
git clone https://github.com/Abhiramcodegit/gridlock-sperry-hackathon
cd gridlock-sperry-hackathon
python -m venv .venv && source .venv/bin/activate
pip install --prefer-binary -r backend/requirements.txt
cd backend && pytest
```

### Frontend
```bash
cd frontend
npm install
npm audit          # expect 0 high / 0 critical
npm run dev        # http://localhost:5173
```

### Database
```bash
cp .env.example .env
docker compose up -d
```

Full setup guide with troubleshooting: [`docs/SETUP.md`](docs/SETUP.md)

---

## Phase Status

| Phase | Name | Branch | Status |
|---|---|---|---|
| 0 | Scaffold | `backend/geospatial-engine` | ✅ Complete — PR #1 open |
| 1 | Source Validation | `research/source-validation` | ⏳ In progress — PR #2 DRAFT |
| 2 | Geometry + DB | TBD | ⏳ Blocked — awaiting Phase 1 approval |
| 3 | Engine Integration | TBD | ⏳ Not started |
| 4 | Demo Polish | TBD | ⏳ Not started |

Detailed tracker: [`project-docs/PHASE_STATUS.md`](project-docs/PHASE_STATUS.md)

---

## Data Rules (Non-Negotiable)

1. **No CEII data.** No confidential, access-controlled, or restricted utility information.
2. **Every project row requires a cited public URL** with publisher and date.
3. **No coordinates without a public source.** All geometries start as `UNVERIFIED`.
4. **Human approval required** before any row enters `approved_projects.csv` or the database.
5. **Hypotheses are not data.** The `data/hypotheses/` folder contains working guesses for future research — they never appear in demo output or engine results.

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

## Security

See [`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md) for the full CVE history, decisions, and residual risks.

Current status: **0 high / 0 critical** in `npm audit` (as of 2026-09-26). Re-run at every commit.

---

## Contributing / Checkpoint Rules

- All PRs targeting `main` must start as **DRAFT**.
- Phase gates require explicit approval before the next phase starts.
- No geometry or DB writes before Phase 1 approval.
- See [`project-docs/WORKFLOW.md`](project-docs/WORKFLOW.md) for branch naming and PR rules.
