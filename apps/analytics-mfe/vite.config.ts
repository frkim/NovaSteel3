import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
  build: {
    emptyOutDir: true,
    // Single-entry MUI + D3 analytics library; the bundle is intentionally
    // released whole with the shell to prevent bridge skew (ADR-004).
    chunkSizeWarningLimit: 1800,
    outDir: resolve(__dirname, '../portal-shell/wwwroot/analytics-mfe'),
    lib: {
      entry: resolve(__dirname, 'src/bridge.tsx'),
      formats: ['es'],
      fileName: 'analytics-mfe',
      cssFileName: 'analytics-mfe',
    },
  },
})
