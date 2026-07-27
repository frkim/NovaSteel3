# Knowledge Hub – Wave 6 Handoff

## Files created or modified

### New files
| File | Purpose |
|------|---------|
| `apps/analytics-mfe/src/api/knowledgeClient.ts` | Dedicated API client for knowledge mutations (avoids editing shared `dataClient.ts`) |
| `apps/analytics-mfe/src/i18n/knowledgeMessages.ts` | i18n catalogs (en/fr/de/nl/es) — must be spread into `CATALOGS` in `messages.ts` |
| `services/bff-api/tests/test_knowledge_workflow.py` | 19 backend tests: transitions, consent, audit, seed/reset |
| `docs/_wave6/knowledge-handoff.md` | This file |

### Modified files
| File | Changes |
|------|---------|
| `apps/analytics-mfe/src/components/screens/KnowledgeHub.tsx` | Full rewrite: real workflow UI, pipeline view, create dialog, approve/reject actions, demo seed/reset |
| `services/bff-api/src/bff_api/knowledge_adapter.py` | Added `submit_for_review`, `reject`, `get_procedure`, `seed_demo_batch`, `reset_demo` + 25-entry corpus |
| `services/bff-api/src/bff_api/routes.py` | Added 7 new routes (see below) |

## Routes added to `routes.py`

```python
@app.post("/v1/knowledge/procedures/{procedure_id}:submit", tags=["Knowledge"])
@app.post("/v1/knowledge/procedures/{procedure_id}:reject", tags=["Knowledge"])
@app.get("/v1/knowledge/procedures/{procedure_id}", tags=["Knowledge"])
@app.post("/v1/knowledge/demo/seed", tags=["Knowledge"])
@app.post("/v1/knowledge/demo/reset", tags=["Knowledge"])
@app.get("/v1/knowledge/audit", tags=["Knowledge"])
```

All routes are between the existing `:approve` route and the existing `/v1/knowledge/search` route.

## Why `knowledgeClient.ts` instead of `dataClient.ts`

Another agent is concurrently editing `dataClient.ts`. To avoid conflicts, I created a dedicated `knowledgeClient.ts` that handles all knowledge mutation API calls. The existing `DataClient.getProcedures()` and `searchKnowledge()` methods remain the read path (used via `useResource`); the new client handles mutations (create, submit, approve, reject, seed, reset, audit).

## Integration step required: i18n

In `apps/analytics-mfe/src/i18n/messages.ts`, spread the knowledge catalogs:

```typescript
import { KNOWLEDGE_CATALOGS } from './knowledgeMessages'

// In the CATALOGS construction:
export const CATALOGS = {
  en: { ...EN, ...KNOWLEDGE_CATALOGS.en },
  fr: { ...FR, ...KNOWLEDGE_CATALOGS.fr },
  // etc.
}
```

Until this is done, the Knowledge Hub imports its own catalogs directly and works standalone.

## State machine

```
DRAFT ──→ IN_REVIEW ──→ APPROVED (terminal)
  │            │
  └──→ REJECTED ←──┘    (terminal)
```

**Illegal transitions rejected (server-side, 409 Conflict):**
- APPROVED → anything
- REJECTED → anything
- DRAFT → APPROVED (must go through IN_REVIEW first)

## Procedure corpus

**27 total procedures** after seed (2 baseline + 25 seeded):
- Domains: blast furnace, refractory lining, tapping & casting, EAF, ladle metallurgy, continuous casting, hot rolling, cold rolling, cooling water, gas cleaning, crane & material handling, energy/load management, safety lockout/tagout, environmental/EU ETS, quality/SPC, coke oven, BOS vessel
- Seed status distribution: ~13 APPROVED, ~6 IN_REVIEW, ~5 DRAFT, ~1 REJECTED

## Audit

Every state transition writes to:
1. The orchestrator's hash-chained audit log (verifiable via `audit.verify()`)
2. The BFF's append-only audit store (verifiable via `services.audit.verify()`)

Both chains verified green after a full workflow run (create → submit → reject → create → submit → approve).

## Test counts

| Suite | Before | After |
|-------|--------|-------|
| Backend knowledge tests | 0 | 19 pass |
| Frontend dock test | 13 pass | 13 pass |
| Frontend `tsc -b --force` | ✅ (my files) | ✅ (my files) |

**Note:** `CopilotPanel.tsx` (owned by another agent) currently has a parse error (curly quote at line 61) that blocks `npm run build` and the dev server. This is NOT caused by any Knowledge Hub change.

## Screenshot paths

Screenshots in `artifacts/screenshots/`:
- `knowledge-01-procedures-list.png` — procedure library with New entry / Seed / Reset buttons, Approve/Reject on IN_REVIEW cards
- `knowledge-02-capture-status-pipeline.png` — capture status sub-view
- `knowledge-03-create-dialog-consent.png` — new entry form with consent checkbox
- `knowledge-04-review-detail.png` — (shows CopilotPanel vite error overlay from concurrent agent edit)
- `knowledge-05-approve-reject-actions.png` — (same CopilotPanel overlay)

The Knowledge Hub UI was visually verified working prior to the CopilotPanel corruption.

## Demo controls

- **Seed sample entries**: POST `/v1/knowledge/demo/seed` — adds 25 realistic procedures in assorted states. Idempotent (reset first if you want a clean slate).
- **Reset demo data**: POST `/v1/knowledge/demo/reset` — clears all and re-seeds only the 2 baseline procedures
- Both require `Knowledge.Publisher` role
- Labelled as demo affordances in the UI (only visible when `demoMode` is true in ShellContext)

## External blocker

`src/components/copilot/CopilotPanel.tsx` line 61 contains a curly/smart quote (`'`) in `"this morning's triage?"` that breaks the Vite OXC parser and TypeScript. This blocks the entire app from loading in dev mode and building. Fix: replace the curly `'` with `\\'` or a straight `'`.
