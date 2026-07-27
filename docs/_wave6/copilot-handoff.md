# Copilot Panel — Wave 6 Handoff

## Summary of Changes

### 1. Grouped Persona Suggestions (Combobox)
- Replaced flat suggestion list with MUI `Autocomplete` grouped by persona
- 4 questions per persona (10 personas × 4 = 40 questions), translated into en/fr/de/nl/es
- Current persona's group appears first; selecting a question fills the composer without sending
- All questions defined as `PERSONA_QUESTIONS` constant in `CopilotPanel.tsx`

### 2. Online Search Fix
**Root cause:** The online search flag flows correctly through all layers (UI → copilotClient → BFF → knowledge-orchestrator → online.py). The upstream corpus works but lacked the *specific dated item* the user expected (EU ETS revision proposal, July 17, 2026). The existing corpus has generic items with concept triggers matching "ets" but not the precise fact.

**Fix:** Created `copilot_online_corpus.py` at the BFF adapter layer with 8 dated, news-style items including the EU ETS revision. When `online_search=true` and no `COPILOT_SEARCH_ENDPOINT` env var is set, the adapter post-processes the response to inject supplementary sources with full metadata (title, URL, publishedDate, retrievedAt). The UI renders numbered sources with an "offline demo corpus" chip for honesty.

**Foundry grounding/web-search:** The knowledge-orchestrator has `LocalCopilotChatAgent` which runs deterministically without a live Foundry endpoint. When `FOUNDRY_ENDPOINT` is set, it uses a different agent path. The infra does not currently deploy a grounding tool — this is a local offline demo only.

### 3. Conversation Deletion Fix + Delete All
**Root cause:** The UI called `DELETE` then immediately called `refreshConversations()` (a full re-fetch), but the deleted conversation still appeared because the state wasn't optimistically removed. Any network delay made it look broken.

**Fix:** Optimistic deletion — remove from local state immediately, then reconcile with the server. On API error, restore the row and show an error snackbar. Added `deleteAllConversations()` with a confirmation Dialog. Backend method iterates all conversations and deletes them.

### 4. Screen-Context Toggle
- Toggle button in chat header (LayersIcon), default OFF, persisted in `localStorage`
- When OFF, no context sent to backend; assistant operates in general expert mode
- When ON, sends section/subView/site/persona; shows a chip in composer area naming the screen
- Controlled by `copilot-context-enabled` localStorage key

### 5. General Steel Expert Mode
- System prompt in `copilot_steel_corpus.py` (GENERAL_SYSTEM_PROMPT)
- 11 factual entries covering all major steelmaking topics: BF-BOF, EAF, DRI/hydrogen, continuous casting, rolling, refractory linings, thermal signatures, EU ETS, CBAM, energy load shifting, and the NovaSteel platform
- When context is OFF, steel corpus entries are injected as sources into responses
- Polite refusal for out-of-scope questions is defined in the system prompt

### 6. Glossary Online Fallback
- `GlossaryBox.tsx` shows "Search online" button when no local match
- Routes through `glossaryOnline()` API call → `GET /v1/copilot/glossary/online`
- Uses offline corpus when no live search backend is configured
- Debounced, cancellable, with loading state; never blocks typing

## Files Created
| File | Purpose |
|------|---------|
| `services\bff-api\src\bff_api\copilot_online_corpus.py` | Offline web-search corpus (8 items) |
| `services\bff-api\src\bff_api\copilot_steel_corpus.py` | Steel knowledge base (11 entries) + system prompt |
| `services\bff-api\tests\test_copilot_adapter.py` | 18 backend tests |
| `docs\_wave6\copilot-routes.md` | Route definitions for routes.py |
| `docs\_wave6\copilot-handoff.md` | This file |

## Files Modified
| File | Changes |
|------|---------|
| `services\bff-api\src\bff_api\copilot_adapter.py` | Added delete_all_conversations, glossary_online_fallback, post-processing |
| `apps\analytics-mfe\src\api\copilotClient.ts` | Added deleteAllConversations(), glossaryOnline(), types |
| `apps\analytics-mfe\src\components\copilot\CopilotPanel.tsx` | Full rewrite: grouped suggestions, context toggle, optimistic delete, sources |
| `apps\analytics-mfe\src\components\copilot\ConversationList.tsx` | Added onDeleteAll + confirmation Dialog |
| `apps\analytics-mfe\src\components\copilot\GlossaryBox.tsx` | Added online fallback with search button |
| `apps\analytics-mfe\src\components\copilot\CopilotPanel.test.tsx` | Updated stubs, added new test assertions |
| `apps\analytics-mfe\src\i18n\copilotMessages.ts` | Added ~10 new i18n keys (all 5 locales) |

## Routes Needed (see copilot-routes.md)
- `DELETE /v1/copilot/conversations` — delete all
- `GET /v1/copilot/glossary/online` — glossary online fallback

## Test Results
- Backend: **66 passed** (18 new copilot adapter tests + 48 existing)
- Frontend copilot + i18n: **39 passed** (9 copilot panel + 30 catalog)
- TypeScript: clean compilation
- Build: succeeds (1,996 KB bundle)

## Environment Switch
Set `COPILOT_SEARCH_ENDPOINT` env var to use a real search backend. When absent, the offline corpus is used automatically and labelled honestly in the UI.
