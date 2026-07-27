# Wave 6 — Personas Handoff

## Summary

This wave introduced named personas, moved site status to the top of Command Center, made all KPI tiles clickable, and added icons to dashboard collection cards.

## Files created

| File | Purpose |
|------|---------|
| `apps/analytics-mfe/src/personas.ts` | Single source of truth for all 10 persona records |
| `apps/analytics-mfe/src/i18n/personaMessages.ts` | Translated persona labels (en/fr/de/nl/es) |
| `apps/analytics-mfe/src/components/screens/CommandCenter.test.tsx` | Tests for KPI clickability, site card navigation, site status presence |
| `apps/analytics-mfe/src/components/screens/DashboardCollections.test.tsx` | Tests for collection icon rendering |
| `docs/_wave6/personas-handoff.md` | This file |

## Files modified

| File | Change |
|------|--------|
| `apps/analytics-mfe/src/personaRoutes.ts` | Added `personaIds: string[]` to `PersonaSection`; updated `persona` display string to include names |
| `apps/analytics-mfe/src/components/screens/CommandCenter.tsx` | Moved site status to first child of `SectionStack`; made site cards clickable with `CardActionArea`; added `dockId`/`dockTitle` to KPI StateBoundary |
| `apps/analytics-mfe/src/components/screens/DashboardCollections.tsx` | Added MUI icon per collection card |

## Integration required (not done — outside scope)

### `apps/analytics-mfe/src/i18n/messages.ts`

The new `PERSONA_CATALOGS` from `./personaMessages` must be spread into the main `CATALOGS` object:

```ts
import { PERSONA_CATALOGS } from './personaMessages'

// Inside CATALOGS construction, spread each locale:
// en: { ...EN, ...PERSONA_CATALOGS.en },
// fr: { ...FR, ...PERSONA_CATALOGS.fr },
// ... etc.
```

Until wired, persona keys resolve to themselves (the raw key string) — they are not currently used in any `t()` call, only as static display strings in `personaRoutes.ts`.

### `apps/analytics-mfe/src/i18n/catalogs.test.ts`

Once `PERSONA_CATALOGS` is spread into the main catalogs, add it to the parity loop:

```ts
import { PERSONA_CATALOGS } from './personaMessages'
// ...
for (const catalogs of [COPILOT_CATALOGS, DEVICE_CATALOGS, WEBSITE_CATALOGS, PERSONA_CATALOGS]) {
```

## Persona table

| ID | Name | Role | Initials |
|----|------|------|----------|
| `plant-manager` | Marc Weber | Plant Manager | MW |
| `furnace-operator` | Elena Duarte | Furnace Operator | ED |
| `maintenance-engineer` | Tomás Rossi | Maintenance & Reliability Engineer | TR |
| `energy-manager` | Sofia Lindqvist | Energy Manager | SL |
| `quality-engineer` | Jens Bakker | Quality Engineer | JB |
| `sustainability-officer` | Amina Haddad | Sustainability Officer | AH |
| `knowledge-engineer` | Pieter Claes | Knowledge Engineer | PC |
| `executive` | Isabelle Moreau | Executive | IM |
| `ot-systems-engineer` | Rui Almeida | OT Systems Engineer | RA |
| `platform-ops` | Nils Andersen | Platform Ops | NA |

## Persona display string changes

The `persona` field on each `PersonaSection` was updated to include the name:

- `'Plant Manager'` → `'Marc Weber - Plant Manager'`
- `'Furnace Operator & Maintenance/Reliability Engineer'` → `'Elena Duarte & Tomás Rossi - Furnace / Maintenance'`
- `'Energy Manager'` → `'Sofia Lindqvist - Energy Manager'`
- `'Quality Engineer'` → `'Jens Bakker - Quality Engineer'`
- `'Sustainability Officer'` → `'Amina Haddad - Sustainability Officer'`
- `'Knowledge Engineer/Admin'` → `'Pieter Claes - Knowledge Engineer'`
- `'Executive'` → `'Isabelle Moreau - Executive'`
- `'OT Systems Engineer'` → `'Rui Almeida - OT Systems Engineer'`
- `'All personas'` → kept as `'All personas'`
- `'Platform Ops'` → `'Nils Andersen - Platform Ops'`
- `'Public site'` → kept as `'Public site'`

No existing tests asserted these display strings.

## KPI tile → destination mapping (Command Center)

| Tile | Destination | actionHint |
|------|-------------|------------|
| Energy consumption | `/{site}/energy-optimization/spot-price-schedule` | "the spot-price schedule" |
| CO₂ (Scope 2) | `/{site}/sustainability-compliance/emissions-ledger` | "the emissions ledger" |
| Furnace lining RUL | `/{site}/furnace-health/lining-forecast` | "the lining forecast" |
| High-grade yield (pred.) | `/{site}/quality/batches` | "quality batches" |
| Open alerts | Reveals `cc-alerts` panel in dock | "the active alerts table" |

All tiles are clickable — none were left non-clickable.

## Collection icons

| Collection | Icon | Colour |
|------------|------|--------|
| Morning shift handover | `WbTwilightOutlined` | `#E69F00` (amber — morning) |
| Furnace risk investigation | `WhatshotOutlined` | `#D55E00` (red-orange — heat) |
| Energy and cost review | `BoltOutlined` | `#0072B2` (blue — energy) |
| Quality escape review | `ScienceOutlined` | `#009E73` (green — quality) |
| Compliance evidence pack | `VerifiedUserOutlined` | `#CC79A7` (pink — compliance) |
| Platform health and spend | `StorageOutlined` | `#56B4E9` (cyan — infrastructure) |

Colours are taken from the chart palette in `design-tokens.v1.json`.

## Test results

- **Before**: 177 tests, 17 files, all passing
- **After**: 184 tests, 19 files, all passing (+7 new tests in 2 new files)
- `tsc -b --force`: ✅ no errors
- `npm run build`: ✅ success (2,031 kB gzip 511 kB)

## Screenshots

- `artifacts/screenshots/command-center-site-status-top.png` — Site status first dock tab
- `artifacts/screenshots/dashboard-collections-icons.png` — Icons on collection cards
- `artifacts/screenshots/command-center-after-site-click.png` — Navigation after site card click
