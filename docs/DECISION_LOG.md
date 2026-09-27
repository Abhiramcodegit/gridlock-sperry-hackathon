# GridLock — Architecture Decision Log

This file records every significant architectural, tooling, and process decision made during development. Add an entry whenever a non-obvious choice is made.

---

## ADR-001 — MapLibre GL JS v6 (not v4 or v5)

**Date:** 2026-09-26  
**Status:** Accepted  
**Context:** XSS advisory GHSA-jrc7-96c5-q579 affects all versions ≤6.4.0. v4 and v5 are unpatched.  
**Decision:** Upgrade to `^6.4.1`. Accept the v4→v6 breaking change costs (worker removal, ESM-only import, es2022 target).  
**Consequences:** Worker wiring removed from `App.jsx`. `vite.config.js` build target raised to es2022. See `docs/SECURITY_AUDIT.md` and commit `2d95fc0`.

---

## ADR-002 — es2022 build target

**Date:** 2026-09-26  
**Status:** Accepted  
**Context:** maplibre-gl v6 ESM bundle uses destructuring patterns that esbuild cannot down-level to es2020 (the previous default), producing ~40 transform errors.  
**Decision:** Raise `esbuild`, `optimizeDeps.esbuildOptions`, and `build` targets to `es2022` in `vite.config.js`.  
**Consequences:** Browser support floor is Chrome 94+, Firefox 93+, Safari 15+. Acceptable for hackathon demo. Re-evaluate before broader production deployment.

---

## ADR-003 — Vite dev server localhost-only

**Date:** 2026-09-26  
**Status:** Accepted  
**Context:** GHSA-4w7w-66w2-5vf9 path-traversal advisory affects Vite dev server when `--host` or `server.host` is set to a network interface.  
**Decision:** Explicitly set `server.host: false` in `vite.config.js`. Never use `--host` flag during development.  
**Consequences:** Dev server accessible at localhost:5173 only. Risk accepted for hackathon context. Must re-evaluate before any cloud or CI deployment.

---

## ADR-004 — PostGIS makes all overlap decisions

**Date:** 2026-09-26  
**Status:** Accepted  
**Context:** AI models can hallucinate geospatial results. Judges (including Sperry engineers) will scrutinize technical correctness.  
**Decision:** `ST_Distance` and `ST_DWithin` are the sole arbiters of whether two projects overlap. No model output enters the overlap calculation.  
**Consequences:** Agents may locate, extract, and normalize project data; they may explain results; they may not decide overlap. All geometries must be human-validated before entering the production dataset.

---

## ADR-005 — Commit package-lock.json for reproducible installs

**Date:** 2026-09-26  
**Status:** Accepted — CLOSED (commit bbc7888)  
**Context:** Repo was initialized without committing a lockfile. Without it, `npm install` resolves different patch versions on different machines and `npm audit` results can diverge.  
**Decision:** Committed `package-lock.json` (lockfileVersion 3) in commit bbc7888. All future installs must use `npm ci` to guarantee exact locked versions.  
**Consequences:** maplibre-gl pinned to 6.11.2, vite pinned to 5.4.21. Audit baselines are now reproducible and comparable across machines.

---

## ADR-006 — Accept maplibre bundle size warning (~1.16 MB / 324 KB gzip)

**Date:** 2026-09-26  
**Status:** Accepted  
**Context:** Vite production build emits a chunk-size warning because maplibre-gl dominates the bundle at ~1.16 MB (324 KB gzipped). This is not an error.  
**Decision:** Accept for hackathon demo. The warning is informational. maplibre is a map rendering library and this size is expected.  
**Consequences:** None for demo. Optional Phase 4 optimization: code-split maplibre via `build.rollupOptions.output.manualChunks`. Do not attempt until Phase 3 is stable.
