# NovaSteel analytics microfrontend

This React/TypeScript/Vite library is mounted by `portal-shell` through
`src/bridge.tsx`. It receives only the typed, versioned shell context:

`themeMode`, `locale`, `activePersona`, `site`, `demoMode`, opaque `tokenRef`,
`bridgeVersion`, `navigation`, optional `bffBaseUrl`, and optional
`permittedActions`. It never stores or receives a bearer token.

## What it renders

Persona-aware, data-dense MUI + D3 surfaces for every persona area:

- **Command Center** — KPI band, live alert center (poll), next-best actions, site tiles.
- **Operations** — throughput vs target, shift board, incident table.
- **Furnace Health** — 21-day lining RUL with a P10–P90 uncertainty band, thermal
  heatmap + selected-sensor trend, maintenance Gantt and work orders.
- **Energy Optimization** — dual-axis spot-price/load overlay and a load-shift
  simulator with instant client estimate + BFF-confirmed savings.
- **Quality** — batch table with a genealogy + bounded what-if drawer, SPC control
  chart and defect Pareto.
- **Sustainability** — CO₂ ledger, ETS gauge/projection, read-only audit evidence.
- **Knowledge Hub** — search-first procedure cards, capture/review flow, coverage.
- **Executive** — cross-site comparison, targets vs actuals, optional Power BI tab.
- **Platform Ops** — read-only capacity mirror, jobs, cost/utilization.

Cross-cutting building blocks: a full `TBL-STD` `DataTable` (sorting, per-column
header search, global search, column management, density, CSV export, windowed
virtualization, states), a D3 chart catalog, KPI cards with "Why?" popovers,
confidence meters, loading/empty/error/stale boundaries, a guided demo tour with
timed runbook transitions, five-locale i18n, and light/dark theming.

## Data access

`src/api/dataClient.ts` calls the FastAPI BFF with a configurable base URL
(shell context → runtime global → `VITE_BFF_BASE_URL` → same-origin) and falls
back to deterministic synthetic fixtures (`src/api/fixtures.ts`) when the BFF is
unreachable, so demos run fully offline. Set `VITE_FIXTURES_ONLY=true` (or the
`window.NOVASTEEL_ANALYTICS_CONFIG.fixturesOnly` flag) to force the offline path.

## Commands

```powershell
npm run build   # tsc -b && vite build -> apps/portal-shell/wwwroot/analytics-mfe
npm run lint    # oxlint
npm run test    # vitest (unit + component + UI smoke)
```

The Vite library output is intentionally written to
`apps/portal-shell/wwwroot/analytics-mfe` for same-page host mounting.
