# Device Operations — Wave 6 Handoff

## Authoritative Counts (seed 240726)

| Site | Plant ID         | Devices | Signals | Profile                              |
|------|------------------|---------|---------|--------------------------------------|
| LUX  | NS-DEMO-LUX-01   | 6       | 34      | Integrated works (BF+BOF+CC+Rolling) |
| DE   | NS-DEMO-DE-01    | 4       | 22      | EAF steelmaking + ladle + billet     |
| BE   | NS-DEMO-BE-01    | 3       | 16      | Cold rolling + galvanizing           |
| ES   | NS-DEMO-ES-01    | 3       | 14      | EAF mini-mill + wire rod             |
| **Total** |              | **16**  | **86**  |                                      |

Scenarios: 6 (unchanged), Seed: 240726.

## Required Change: `AnalyticsDashboard.tsx`

The `DataClient` now reads `context.site` at **call time** (robust design), but the
`useMemo` that creates the client should still include `site` to force React to
re-fetch data when the user switches sites. Apply the following change:

```tsx
// File: apps/analytics-mfe/src/components/screens/AnalyticsDashboard.tsx
// Find the useMemo for dataClient and add context.site to the dependency array:

// BEFORE:
const dataClient = useMemo(
  () => new DataClient(context),
  [context.bffBaseUrl, context.locale, context.demoMode],
)

// AFTER:
const dataClient = useMemo(
  () => new DataClient(context),
  [context.bffBaseUrl, context.locale, context.demoMode, context.site],
)
```

Similarly for `deviceClient` if it has the same pattern.

## Site Bug Root Cause

`dataClient.ts` hard-coded `site: 'all'` in every BFF URL (furnaces, telemetry,
energy, quality, sustainability). The `DeviceClient` used the constant `DEMO_PLANT`
(`NS-DEMO-LUX-01`). Neither read the shell's selected site.

**Fix:** Both clients now store a reference to the `ShellContext` and resolve the
active plant at call time via `siteToPlant(this.context.site)`. The `demoHeaders`
function sends **all 4 plant IDs** in `X-Demo-Plants` so the BFF grants access to
every site regardless of which is currently selected.

## Fleet Filter Dropdowns (Task 3)

Added to `DeviceFleet.tsx` via the `toolbarExtras`-adjacent pattern (filter row
above the DataTable). Columns with select filters:

| Column   | Why dropdown                        |
|----------|-------------------------------------|
| Site     | 4 values (low cardinality)          |
| Type     | ~8 distinct device descriptions     |
| Status   | 3–4 values (healthy/degraded/fault) |
| Area     | 5–6 values                          |

All options populated from the loaded data. Active filters shown as removable chips
with "Clear all filters" button and `{filtered} of {total} devices` counter.

New i18n keys (all 5 locales): `device.fleet.filter.{site,type,status,area,all,clearAll,showing}`.

## DataTable Note

No changes to `DataTable.tsx` were required. The filter dropdowns are implemented
above the table in the `DeviceFleet` component using MUI `Select` controls. They
filter the `displayedDevices` array passed to `DataTable` as `rows`.
