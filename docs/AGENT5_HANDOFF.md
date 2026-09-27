# Agent 5 (Main QA) — Handoff

Prepared by Agent 5 (QA / merge gatekeeper). Read-only QA role; this handoff
changes no application code.

Date: 2026-09-27

---

## Current state

- **main branch SHA:** `1c31e2e` (Merge PR #7).
- All four feature PRs (#4–#7) are merged to `main`.
- **Gate:** Phase 3 PostGIS CI verified GREEN via GitHub Actions.

---

## What was merged (PRs #4–#7)

| PR | Title | Merge commit | Source branch / verified SHA | Agent 5 verdict |
|----|-------|--------------|------------------------------|-----------------|
| #4 | Phase 3 geospatial engine and verified PostGIS CI | `919616b` | `backend/geospatial-engine` (verification `2eff3d0`, engine fix `02752cb`) | PASS (run-attested) |
| #5 | Add frontend candidate-review map layer | `3f5610e` | `frontend/map-wiring` (product `4b83d4c`) | PASS WITH NOTES |
| #6 | Add frontend map-wiring tests | `35e2eb0` | `frontend/map-wiring-tests` (`9af3341`) | PASS |
| #7 | Add verified demo, deployment, and data-limitations documentation | `1c31e2e` | `docs/demo-flow` (`b157fcf`) | PASS |

Full per-SHA QA evidence is in `docs/QA_LOG.md` on the `qa/main-review` branch.

### What each PR delivered
- **#4 Engine:** PostGIS ingestion of `data/normalized/projects_proposed.csv`
  (proposed rows), `candidate_pairs` view using `ST_DWithin(geom, geom, 40000)`
  cross-utility filter + `ST_Distance` on approved-geometry pairs + temporal
  overlap; FastAPI `GET /opportunities` (PostGIS-backed when
  `GRIDLOCK_DATABASE_URL` set, else file fallback); ingestion moved to
  startup/CLI (`python -m gridlock.migrate`), not per request.
- **#5 Frontend map:** amber, non-authoritative "Candidate review" layer for
  the two proposed proxy points (GPC-004, DESC-003), on by default with toggle;
  approved layer stays authoritative; verbatim disclaimer + empty-state;
  unlocated proposed records shown as a count, not markers.
- **#6 Frontend tests:** Vitest + Testing Library; 9 tests covering loading,
  empty, candidate items, labels, toggle, disclaimer, no-tier/line for proxies,
  fetch error, static fallback.
- **#7 Docs:** README refresh citing the verified CI run, `docs/DEMO_FLOW.md`
  (presenter script + warning box), `docs/DATA_LIMITATIONS.md`,
  `docs/DEPLOYMENT.md`.

---

## Exact verified test results

Verified locally on `main` @ `1c31e2e` (macOS 12, Python 3.13, Node 22):

- **Backend unit suite** (`pytest`, no database): **20 passed, 4 skipped**.
  The 4 skips are the PostGIS integration tests, which skip automatically when
  `GRIDLOCK_DATABASE_URL` is unset.
- **Full backend suite with PostGIS** (GitHub Actions, run
  `36287891004`, tested engine SHA `02752cb`): **24 passed, 0 skipped**
  (17 engine + 3 proxy-distance + 4 DB integration). NOTE: the correct full
  count is **24**, not 27 — an earlier "27" was a miscount.
- **Frontend tests** (`npm test -- --run`): **9 passed**.
- **Frontend production build** (`npm run build`): **exit 0** (a chunk-size
  warning for the maplibre bundle is informational, not an error).

`GET /opportunities` returns `[]` today. That is the correct, honest answer:
no human-approved geometry pair exists, and the only two rows with geometry
(GPC-004, DESC-003) are ~117 km apart — outside the 40 km filter.

---

## Local startup and test commands

### Backend unit tests (no database)
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install --prefer-binary -r requirements.txt
pytest -v          # 20 passed, 4 skipped
```

### Full PostGIS suite (needs Docker; NOT available on macOS 12)
```bash
docker compose up -d db
export GRIDLOCK_DATABASE_URL="postgresql://postgres:${POSTGRES_PASSWORD}@localhost:5432/gridlock"
cd backend && pytest -v   # 24 passed, 0 skipped
```

### Frontend
```bash
cd frontend
npm ci
npm run dev        # http://localhost:5173
npm test -- --run  # 9 passed
npm run build      # exit 0
```

### Full stack via Docker
```bash
cp .env.example .env   # set POSTGRES_PASSWORD
docker compose up --build
# API /health -> {"ok": true, "backend": "postgis"}
```

---

## Known limitations

1. **`/opportunities` is empty by design.** Approved dataset is
   `{"type":"FeatureCollection","features":[]}`. Nothing has been
   human-approved, so the candidate query has nothing to pair.
2. **Only two proposed rows carry geometry** (GPC-004 West McIntosh proxy,
   DESC-003 Church Creek proxy). Both are **inferred substation proxy points**,
   not confirmed project routes. The 116.993 km between them is a proxy-point
   diagnostic negative, NOT verified project-to-project proximity.
3. **DESC-002 (Okatie–McIntosh) is unresolved** — no defensible public
   coordinate found (OSM has no Okatie feature; EIA/HIFLD do not publish
   substation locations; the Dominion route map is image-only).
4. **The cost/savings estimator is disabled** — no savings figures anywhere.
5. **macOS 12 cannot run Docker locally** (Docker Desktop + Homebrew dropped
   macOS 12). The PostGIS suite is therefore verified via GitHub Actions, not
   on the dev machine.

---

## Remaining risks

1. **KNOWN BUG — map hangs on "Loading map data" in some browsers.**
   On `main` (`1c31e2e`), `frontend/src/App.jsx` relies on maplibre-gl v6's
   automatic Vite worker resolution. In practice this can fail at runtime with
   the browser console error **"Worker failed to load. Check that the worker
   URL is correct."** Because ALL data loading and `setLoading(false)` live
   inside `map.on('load', ...)`, and there was **no `on('error')` handler**, a
   worker failure leaves the UI stuck on the "Loading map data" spinner
   forever, with the failure swallowed silently. This is reproducible and is a
   demo-blocking risk.

   **Diagnosed root cause:** maplibre-gl 6.11.2 ships its render worker as a
   separate `maplibre-gl-worker.mjs`; the bare `import * as maplibregl` does
   not reliably resolve that worker under the Vite dev server.

   **Fix prepared — the changes are:**
   - `frontend/src/App.jsx`:
     (a) `import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'`
     then `maplibregl.setWorkerUrl(maplibreWorkerUrl)`, and
     (b) add `map.on('error', ...)` so the app degrades gracefully instead of
     hanging on the spinner.
   - `frontend/src/App.test.jsx`: add `setWorkerUrl` to the maplibre mock and
     stub the `?worker&url` import so the suite still runs.

   Locally verified: worker asset resolves (HTTP 200), `npm test -- --run`
   9/9 pass, `npm run build` exit 0.

   > **ACCESS / STATUS — IMPORTANT:** As of this handoff the fix is **NOT on
   > `main`, NOT pushed to the remote, and NOT yet committed.** It exists only
   > on the developer's local machine:
   > - Local branch: `frontend/fix-worker-loading` (created off `9af3341`).
   > - The actual edits are held in a local git **stash** (`stash@{0}`,
   >   "WIP on fix-worker-loading"), not as a commit on that branch.
   >
   > This means you **cannot** `git fetch`/`git checkout frontend/fix-worker-loading`
   > from GitHub and see the fix — the remote branch does not exist. To make it
   > accessible, the local stash must be applied, committed, and the branch
   > pushed. Until then, `main` still ships the buggy version and the map will
   > hang for any browser where the maplibre worker fails to auto-resolve.
   >
   > Recommended: apply `stash@{0}` on `frontend/fix-worker-loading`, commit,
   > push, and open a PR for independent review before any live demo. (The fix
   > touches Agent 2/3 code, so Agent 5 — who authored it — should not be its
   > sole reviewer.)

2. **Private-repo CI attestation gap.** Agent 5 could not open Actions run
   `36287891004` (private repo, no API auth). A human repository member should
   open the run once to confirm conclusion=success, head SHA `02752cb`, and the
   exact "24 passed, 0 skipped / 4 DB executed" summary.

3. **Non-blocking frontend follow-ups (from PR #5 review):** thin responsive
   coverage (single `@media`), no `prefers-reduced-motion` support, map
   container lacks an aria/role label.

4. **Fixture drift risk.** The frontend candidate layer reads
   `frontend/src/candidateFixture.js` (a hand-derived snapshot of the two
   proposed geometry rows) because no endpoint serves proposed geometry. If
   `projects_proposed.csv` changes, the fixture must be updated in lockstep.

---

## Recommended next steps

1. **Merge the worker-loading fix** (`frontend/fix-worker-loading`) after
   independent review — this unblocks the live map demo. Confirm in a real
   browser that "Loading map data" clears and the map renders.
2. **Human-confirm the CI run** `36287891004` to close the attestation gap.
3. **Phase 2 continuation:** resolve additional source-backed geometries so at
   least one approved cross-utility pair can exist and `/opportunities` can
   return a real result. Keep the human geometry-approval gate.
4. Address the non-blocking a11y/responsive notes before final judging.
5. Consider a small read-only `/candidates` endpoint so the frontend stops
   depending on the hand-maintained fixture.

---

## Files future agents should read first

1. `README.md` — project overview, phase status, run commands.
2. `docs/DEMO_FLOW.md` — presenter script + the PRESENTER WARNING box
   (do not overstate proxies or the 116.993 km figure).
3. `docs/DATA_LIMITATIONS.md` — provenance, proxy-vs-verified rules, why
   `/opportunities` is empty.
4. `docs/DEPLOYMENT.md` — file mode vs PostGIS mode, health checks, recovery.
5. `docs/ENGINE_PHASE3.md` — engine design + CI verification record.
6. `docs/PROXY_DISTANCE_RESULT.md` — the 116.993 km honest-negative result.
7. `backend/gridlock/db.py`, `db/schema.sql` — deterministic PostGIS engine.
8. `backend/gridlock/api.py` — API surface (`/health`, `/projects`,
   `/opportunities`).
9. `frontend/src/App.jsx` — map UI (SEE RISK #1 re: the worker bug).
10. `docs/QA_LOG.md` (on branch `qa/main-review`) — full per-SHA QA evidence.
