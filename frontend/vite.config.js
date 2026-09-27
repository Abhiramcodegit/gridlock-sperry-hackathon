import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// NOTE: --host is intentionally NOT set here.
// GHSA-4w7w-66w2-5vf9 (path-traversal in optimised deps .map handling)
// only triggers when the dev server is exposed on a network interface
// via --host or server.host. This config binds to localhost only.
// Risk assessment: dev-only, not triggered by our config. Acceptable
// for hackathon. Re-evaluate before any production deployment.
export default defineConfig({
  plugins: [react()],
  server: {
    host: false,        // localhost only — explicitly disables network exposure
    port: 5173
  },
  // maplibre-gl v6's ESM bundle uses syntax (e.g. destructuring in
  // certain positions) that esbuild cannot down-level to the old default
  // target (es2020). Raise the target so both dev (esbuild deps optimizer)
  // and the production build transform maplibre v6 correctly.
  esbuild: { target: 'es2022' },
  optimizeDeps: { esbuildOptions: { target: 'es2022' } },
  build: { target: 'es2022' }
})
