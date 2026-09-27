# GridLock — Build Verification Log

Last updated: 2026-09-26 (synced to commit bbc7888)  
Environment: Node 22.23.2, npm, macOS Intel  
Vite: 5.4.21 | maplibre-gl: 6.11.2

---

## Why This File Exists

Tracks dev server and production build verification. Must be updated every time the build target, bundler config, or major dependencies change.

---

## ✅ Phase 0 COMPLETE — All build checks passed

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

**STATUS: ✅ PASS** — Verified by Kiro on 2026-09-26 (macOS Intel, Node 22.23.2, Vite 5.4.21, commit bbc7888)

| Check | Status | Confirmed by | Date |
|---|---|---|---|
| `npm run build` exits code 0 | ✅ | Kiro | 2026-09-26 |
| `dist/` directory created | ✅ | Kiro | 2026-09-26 |
| No esbuild destructuring errors | ✅ | Kiro | 2026-09-26 |
| No worker/transform errors in build output | ✅ | Kiro | 2026-09-26 |
| Bundle target is es2022 (not es2020) | ✅ | Kiro | 2026-09-26 |
| maplibre-gl 6.11.2 included in bundle | ✅ | Kiro | 2026-09-26 |

**Exit code:** `0`

**Build output (verbatim, commit bbc7888):**
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

### Chunk-size warning
Informational only — not an error. The ~1.16 MB (324 KB gzipped) bundle is dominated by maplibre-gl, which is expected for a map library. Acceptable for hackathon demo.

**Optional Phase 4 optimization:** code-split maplibre via `build.rollupOptions.output.manualChunks` or dynamic `import()`. Do not do this until Phase 3 is complete and the demo path is stable.

---

## Lockfile Status

| Item | Status |
|---|---|
| `package-lock.json` committed | ✅ lockfileVersion 3, commit bbc7888 |
| maplibre-gl version pinned | ✅ 6.11.2 |
| vite version pinned | ✅ 5.4.21 |
| Installs reproducible across machines | ✅ Use `npm ci` (not `npm install`) |
| Audit baselines comparable | ✅ All machines install identical tree |

**Always use `npm ci` from now on** (not `npm install`) so the exact locked versions are installed:
```bash
cd frontend
npm ci
npm audit
# Expected: 0 critical, 1 risk-accepted dev-only vite HIGH
```

---

## Build Config Reference (current)

```js
// vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    host: false,   // localhost only — ADR-003
    port: 5173
  },
  esbuild: { target: 'es2022' },           // ADR-002
  optimizeDeps: { esbuildOptions: { target: 'es2022' } },
  build: { target: 'es2022' }
})
```
