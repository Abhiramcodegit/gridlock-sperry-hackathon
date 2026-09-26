# GridLock — Local Setup Guide

## Prerequisites

- Python 3.11, 3.12, or 3.13 (any platform)
- Node 18+ (22.x recommended)
- Docker Desktop (for PostgreSQL/PostGIS)
- Git

## Backend

```bash
# 1. Clone and enter repo
git clone https://github.com/Abhiramcodegit/gridlock-sperry-hackathon
cd gridlock-sperry-hackathon

# 2. Create and activate a virtualenv (required — do not install globally)
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows

# 3. Install pinned deps — --prefer-binary prevents source builds
pip install --prefer-binary -r backend/requirements.txt

# 4. Run tests
cd backend && pytest
```

**Important:** `pyproj==3.7.0` ships PROJ 9.4.1 bundled inside the wheel.
No system PROJ installation required. Do not upgrade to 3.8.x until cp313
macOS x86_64 wheels are confirmed on PyPI.

## Frontend

```bash
cd frontend
npm install
npm run dev          # serves on http://localhost:5173
```

**Security note:** Three `npm audit` findings are present. All are
`devDependencies` (vite chain) and do not ship to production.
`vite` is pinned to `^5.4.14` which patches CVE-2026-39364 (CVSS 7.5,
file-read in dev server). The `esbuild` override resolves the remaining
moderate finding. Run `npm audit` to confirm 0 high/critical after install.

## Database (Docker)

```bash
cp .env.example .env
docker compose up -d
```

## Stopping

```bash
deactivate            # backend venv
docker compose down   # database
```
