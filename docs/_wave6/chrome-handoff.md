# Chrome Shell — Handoff Notes

## Notes for analytics-mfe agent

The portal shell now sends a new `helpBilingual` boolean in the `ShellContext` object
passed to the micro-frontend. The TypeScript side should read `context.helpBilingual`
and, when `true`, render Help Assistant explanations in both English and French.

No changes to `apps\analytics-mfe\src\**` were made by this agent. The MFE team owns
that integration.

## Notes for services agent

No services changes were needed. The `helpBilingual` field is shell-local state only
(not persisted to BFF).

## Persona selector trade-off

To keep the top bar at ≤ 52 px without overflow, the **Persona `<select>`** was moved
from the top bar into the **Settings dialog** (under "Persona" section). This frees
space for the logo, theme icon, globe locale, hamburger, and keeps controls clickable
at 1280 px. The persona can still be changed at any time via Settings → Persona.
