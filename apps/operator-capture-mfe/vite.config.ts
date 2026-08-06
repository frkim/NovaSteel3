import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Standalone, installable PWA for shop-floor operators. Unlike analytics-mfe
// (a `lib` bridge bundle released with the shell), this app ships its own
// `index.html`, service worker and web manifest and is served on its own.
export default defineConfig({
  plugins: [react()],
  build: {
    emptyOutDir: true,
    outDir: 'dist',
  },
})
