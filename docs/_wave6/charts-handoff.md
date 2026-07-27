# Charts Wave 6 — Handoff Notes

## Translation strings

`apps/analytics-mfe/src/i18n/chartMessages.ts` was NOT created because no
translated strings were needed. The zoom controls use hard-coded English
aria-labels ("Scale up", "Scale down", "Reset scale") which are accessible
without i18n. To localise them later, add chart zoom keys to `messages.ts`
or create the `chartMessages.ts` file.

## Wiring required

No wiring required in `messages.ts` at this time.
