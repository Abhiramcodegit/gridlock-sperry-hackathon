# GridLock — Build Verification Log

Last updated: 2026-09-26  
Branch: `research/source-validation`  
Baseline commit: `2d95fc0` (Kiro — fix(frontend): repair maplibre-gl v6 migration build)

---

## Why This File Exists

Kiro confirmed `npm run dev` is clean after the maplibre-gl v6 migration. Production build (`npm run build`) has not yet been confirmed. This file tracks both verification steps and must be updated every time the build target, bundler config, or major dependencies change.

---

## Dev Server Verification

| Check | Status | Confirmed by | Date |
|---|---|---|---|
| `npm run dev` exits without worker/transform errors | ✅ | Kiro | 2026-09-26 |
| App loads HTTP 200 at localhost:5173 | ✅ | Kiro | 2026-09-26 |
| maplibre-gl dep bundle loads HTTP 200 | ✅ | Kiro | 2026-09-26 |
| No `?worker` import errors in console | ✅ | Kiro | 2026-09-26 |
| maplibre XSS GHSA-jrc7-96c5-q579 resolved | ✅ | Kiro | 2026-09-26 |

---

## Production Build Verification

> **STATUS: PASS** — Verified by Kiro on 2026-09-26 (macOS Intel, Node 22.23.2, Vite 5.4.21).

| Check | Status | Confirmed by | Date |
|---|---|---|---|
| `npm run build` exits code 0 | ✅ | Kiro | 2026-09-26 |
| `dist/` directory created | ✅ | Kiro | 2026-09-26 |
| No esbuild destructuring errors | ✅ | Kiro | 2026-09-26 |
| No worker/transform errors in build output | ✅ | Kiro | 2026-09-26 |
| Bundle target is es2022 (not es2020) | ✅ | Kiro | 2026-09-26 |
| maplibre-gl included in bundle at correct version | ✅ (6.11.2) | Kiro | 2026-09-26 |

**Exit code:** `0`

**Build output (verbatim):**
```
> build
> vite build
vite v5.4.21 building for production...
transforming...
✓ 34 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                     0.34 kB │ gzip:   0.25 kB
dist/assets/index-DeUcOmFd.css     83.75 kB │ gzip:  10.77 kB
dist/assets/index-D6XzBjoj.js   1,162.50 kB │ gzip: 324.33 kB
(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking
- Adjust chunk size limit via build.chunkSizeWarningLimit.
✓ built in 9.42s
```

**Note on the chunk-size warning:** informational only, not an error. The ~1.16 MB
(324 KB gzipped) bundle is dominated by maplibre-gl, which is expected for a map
library. Acceptable for the hackathon demo. Optional future optimization:
code-split maplibre via dynamic import or `manualChunks`.

---

## Build Config Reference (commit 2d95fc0)

```js
// vite.config.js — current state
export default defineConfig({
  plugins: [react()],
  server: {
    host: false,   // localhost only
    port: 5173
  },
  esbuild: { target: 'es2022' },
  optimizeDeps: { esbuildOptions: { target: 'es2022' } },
  build: { target: 'es2022' }
})
```

**Why es2022:** maplibre-gl v6's ESM bundle uses destructuring syntax patterns that esbuild cannot down-level to the previous default target (es2020). Raising to es2022 eliminates ~40 esbuild transform errors. See commit `2d95fc0` message for full details.

**Browser support:** es2022 is supported by all Chrome/Edge 94+, Firefox 93+, Safari 15+. Safe for hackathon demo context. Re-evaluate for broader production deployment.

---

## Lockfile Status

| Item | Status |
|---|---|
| `package-lock.json` committed | ❌ Not yet committed |
| Installs reproducible across machines | ❌ Not until lockfile committed |
| Audit baselines comparable | ❌ Not until lockfile committed |

Action: Kiro to run `npm install && git add package-lock.json && git commit`.
