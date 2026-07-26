import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    css: false,
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    // jsdom + MUI + D3 renders are CPU-heavy; under full-suite parallel load
    // a userEvent interaction can exceed the 5s default and fail spuriously.
    testTimeout: 20000,
    hookTimeout: 20000,
  },
})
