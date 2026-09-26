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
  }
})
