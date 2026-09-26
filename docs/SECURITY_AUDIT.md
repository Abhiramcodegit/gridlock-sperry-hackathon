# GridLock — Frontend Security Audit Log

Last updated: 2026-09-26  
Environment: Node 22.23.2, npm

> **Note:** Re-run `npm audit` at every commit. The advisory database changes daily.
> Never trust a cached audit result.

---

## Current Status: 0 high / 0 critical expected after `npm install`

---

## Advisory History

### GHSA-jrc7-96c5-q579 — maplibre-gl XSS (CRITICAL)

| Field | Value |
|---|---|
| **Package** | `maplibre-gl` |
| **Severity** | Critical |
| **Affected** | `<=6.4.0` (includes all v4 and v5 releases) |
| **Patched** | `6.4.1` |
| **Production dep?** | YES — ships in `dist/` |
| **Impact** | `DOM.sanitize()` iterated a live `NamedNodeMap` while removing attributes in the same loop, allowing attribute reinsertion and XSS payload execution in map popups/tooltips |
| **Fix applied** | Upgraded `maplibre-gl` from `4.7.1` → `^6.4.1` |
| **Migration required** | YES — v4→v6 is a breaking change. Applied in `App.jsx`: namespace import, `setWorkerUrl()`, CSS import |
| **Verified** | Pending Kiro re-run of `npm audit` |

---

### GHSA-4w7w-66w2-5vf9 — Vite path-traversal (HIGH)

| Field | Value |
|---|---|
| **Package** | `vite` |
| **Severity** | High |
| **Affected** | Vite dev server when `--host` or `server.host` is set |
| **Patched** | v6.4.2+ / v7+ (v5 branch: dev-only risk) |
| **Production dep?** | NO — devDependency only; not in `dist/` |
| **Impact** | Path-traversal allows reading arbitrary `.map` source files from disk when dev server is network-exposed |
| **Our config** | `vite.config.js` explicitly sets `server.host: false` (localhost only). The traversal vector is NOT triggered. |
| **Fix applied** | Pinned `vite` to `^5.4.21`; `server.host: false` documented in `vite.config.js` |
| **Residual risk** | None in current config. Re-evaluate before any production or cloud deployment. |

---

### GHSA-67mh-4wv8-2f99 — esbuild CORS (MODERATE)

| Field | Value |
|---|---|
| **Package** | `esbuild` (transitive via `vite` and `@vitejs/plugin-react`) |
| **Severity** | Moderate |
| **Affected** | `esbuild <=0.24.2` |
| **Patched** | `>=0.25.0` |
| **Production dep?** | NO — devDependency only |
| **Fix applied** | `overrides: { "esbuild": ">=0.25.0" }` in `package.json` |

---

## v4 → v6 MapLibre Migration Summary

All changes confined to `frontend/src/App.jsx`:

| Change | v4 pattern | v6 pattern | Reason |
|---|---|---|---|
| Import | `import maplibregl from 'maplibre-gl'` | `import * as maplibregl from 'maplibre-gl'` | v6 ESM-only; default export removed |
| Worker | (not needed) | `import MaplibreWorker ... + setWorkerUrl()` | v6 separates tile worker; Vite needs explicit URL |
| CSS | (optional) | `import 'maplibre-gl/dist/maplibre-gl.css'` | Bundled with package in v6 |
| Map init | `new maplibregl.Map(...)` | unchanged | |
| LngLatBounds | `new maplibregl.LngLatBounds(...)` | unchanged | |
| fitBounds | `map.fitBounds(b, opts)` | unchanged | |
| addSource/addLayer | unchanged | unchanged | |
| setData | unchanged | unchanged | |

---

## Instructions for Kiro

```bash
git fetch && git checkout research/source-validation
cd frontend
npm install          # must re-resolve with new package.json
npm audit
npm run dev          # verify map renders at localhost:5173
```

Expected:
- `npm audit`: 0 high, 0 critical
- Map renders with tiles from demotiles.maplibre.org
- Sidebar shows “No approved cross-utility opportunities yet.” (expected — approved_projects.csv is empty)
- No console errors about missing worker or tile failures
