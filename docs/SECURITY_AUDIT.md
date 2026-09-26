# GridLock — Frontend Security Audit Log

Last updated: 2026-09-26 (synced to commit 2d95fc0)  
Environment: Node 22.23.2, npm

> **Note:** Re-run `npm audit` at every commit. The advisory database changes daily.
> Never trust a cached audit result.

---

## Current Status: ✅ 0 critical — 1 risk-accepted dev-only vite HIGH

> This is the expected result after `npm install` on commit `2d95fc0`.
> If you see anything different, stop and file an issue before continuing.

---

## Advisory History

### GHSA-jrc7-96c5-q579 — maplibre-gl XSS (CRITICAL) — RESOLVED

| Field | Value |
|---|---|
| **Package** | `maplibre-gl` |
| **Severity** | Critical |
| **Affected** | `<=6.4.0` (all v4 and v5 releases) |
| **Patched** | `6.4.1` |
| **Production dep?** | YES — ships in `dist/` |
| **Impact** | `DOM.sanitize()` iterated a live `NamedNodeMap` while removing attributes in the same loop, allowing attribute reinsertion and XSS payload execution in map popups/tooltips |
| **Fix applied** | Upgraded `maplibre-gl` `4.7.1` → `^6.4.1` |
| **Migration** | v4→v6 breaking change. See Migration Summary below. Kiro completed in commit `2d95fc0`. |
| **Verified** | ✅ Dev server clean on Kiro's machine (2026-09-26) |

---

### GHSA-4w7w-66w2-5vf9 — Vite path-traversal (HIGH) — RISK ACCEPTED

| Field | Value |
|---|---|
| **Package** | `vite` |
| **Severity** | High |
| **Affected** | Vite dev server when `--host` or `server.host` is set |
| **Patched** | v6.4.2+ / v7+ |
| **Production dep?** | NO — devDependency only; never in `dist/` |
| **Impact** | Path-traversal allows reading arbitrary `.map` source files when dev server is network-exposed |
| **Our config** | `vite.config.js` sets `server.host: false` (localhost only). Traversal vector is NOT triggered. |
| **Decision** | Risk accepted. Dev-only dep, localhost-only config, hackathon context. Re-evaluate before cloud deployment. |
| **Residual risk** | None in current config. |

---

### GHSA-67mh-4wv8-2f99 — esbuild CORS (MODERATE) — RESOLVED

| Field | Value |
|---|---|
| **Package** | `esbuild` (transitive via `vite` and `@vitejs/plugin-react`) |
| **Severity** | Moderate |
| **Affected** | `esbuild <=0.24.2` |
| **Patched** | `>=0.25.0` |
| **Production dep?** | NO — devDependency only |
| **Fix applied** | `overrides: { "esbuild": ">=0.25.0" }` in `package.json` |
| **Verified** | ✅ |

---

## v4 → v6 MapLibre Migration Summary (completed by Kiro, commit 2d95fc0)

All changes confined to `frontend/src/App.jsx` and `frontend/vite.config.js`:

| Change | v4 pattern | v6 pattern | Reason |
|---|---|---|---|
| Import | `import maplibregl from 'maplibre-gl'` | `import * as maplibregl from 'maplibre-gl'` | v6 ESM-only; default export removed |
| Worker | Manual `?worker` import + `setWorkerUrl()` blob | **Removed entirely** | v6 + Vite bundles the worker automatically; the `maplibre-gl-csp-worker.js` file does not exist in v6 |
| CSS | Optional | `import 'maplibre-gl/dist/maplibre-gl.css'` | Bundled with package in v6 |
| esbuild target | `es2020` (default) | `es2022` | v6 ESM uses syntax esbuild cannot down-level to es2020; raised in `esbuild`, `optimizeDeps.esbuildOptions`, and `build` |
| Map init | `new maplibregl.Map(...)` | unchanged | |
| LngLatBounds/fitBounds/addSource/addLayer/setData | unchanged | unchanged | |

---

## Build Verification (action item from Kiro 2026-09-26)

Kiro verified `npm run dev` is clean. Production build (`npm run build`) must also be confirmed:

```bash
cd frontend
npm run build
# Expected:
# - Exit code 0
# - dist/ directory created
# - No esbuild destructuring errors
# - No worker/transform errors
# - Bundle includes maplibre-gl at es2022 target
```

> **TODO (Kiro):** Confirm `npm run build` succeeds and post the output summary here.

---

## Lockfile Decision (action item from Kiro 2026-09-26)

The repo currently has **no committed `package-lock.json`**. This means:
- `npm install` on a clean machine may resolve different patch versions
- `npm audit` results can diverge between machines
- CI/CD (if added) cannot guarantee identical trees

**Recommendation:** Commit `package-lock.json` so every install is reproducible and audit results are comparable.

To do this:
```bash
cd frontend
npm install          # generates/updates package-lock.json
git add package-lock.json
git commit -m "chore(frontend): commit package-lock.json for reproducible installs"
git push
```

Once committed, tag the audit result here as the canonical baseline.

> **TODO (Kiro):** Confirm and push `package-lock.json`. Security audit re-verification will follow immediately.

---

## Instructions for Kiro (updated for 2d95fc0)

```bash
git fetch && git checkout research/source-validation
# should fast-forward cleanly to 2d95fc0
cd frontend
npm install
npm audit
# Expected: 0 critical, 1 risk-accepted dev-only vite HIGH
npm run dev
# Verify: map renders at localhost:5173, no console errors
npm run build
# Verify: dist/ created, exit code 0, no esbuild errors
```

**Expected `npm audit` result (exact wording):**
```
0 critical
1 risk-accepted dev-only vite HIGH (GHSA-4w7w-66w2-5vf9, localhost-only config)
```

If you see anything else, stop and file an issue.
