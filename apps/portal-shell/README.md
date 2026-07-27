# NovaSteel portal shell

The Blazor WebAssembly host owns global chrome and identity: top bar, left-rail
persona navigation, breadcrumb, footer, theme/locale switch, site + **primary
persona** selection, demo/cloud mode, the demo sign-in identity context, routing,
and the authoritative **Fabric capacity lifecycle control surface**.

## Capacity control

The top-bar capacity pill reflects live state and opens a shell-owned control
panel (`Components/CapacityPanel.razor`). `Services/CapacityService.cs` calls only
the BFF (`GET /v1/platform/capacity` and the start/pause/SKU request routes) with
demo headers and a UUID idempotency key; it never reaches ARM directly.
`Platform.Capacity.Manage` gates the request buttons. When the BFF is
unavailable, `Services/CapacityState.cs` falls back to a deterministic simulated
lifecycle so the demo control always works. Capacity requests raised by the React
microfrontend (`capacity.request`) are routed through this same shell service, and
`capacity.panel` lets a microfrontend tile surface this dialog without owning it.

### Resizing the capacity

The panel offers the audited demo SKUs — **F2, F4 and F8** — through
`POST /v1/platform/capacity/sku-requests`. Resizing is deliberately *not* a
lifecycle transition: a running capacity stays running and a paused capacity stays
paused, so the SKU can be raised before a rehearsal without resuming the capacity.
Requests are refused while a start/pause transition is still settling, when the
selected SKU already matches, and for anyone without `Platform.Capacity.Manage`;
a server refusal is surfaced verbatim in the dialog rather than silently ignored.

The allow-list is enforced in four places that `tests/infra/test_capacity_sku_allow_list.py`
pins together — the Azure Policy definition, `main.bicep`, `bff_api.capacity.SCALABLE_SKUS`
and `CapacityState.DefaultSkuOptions` — so the dialog can never offer a SKU that
Azure Policy would deny at the ARM boundary. Fabric capacity units scale linearly,
so F4 costs roughly twice F2 per hour and F8 roughly four times; the nightly 01:00
Europe/Luxembourg pause check is what keeps a burst tier from billing overnight.

## Bridge and configuration

The shell passes a typed, versioned context to the analytics microfrontend
(`contracts/ui/shell-interop.v1.schema.json`), including the configurable
`Bff:BaseUrl` and the demo user's server-consistent `permittedActions`. Add Entra
application values only through deployment configuration; the committed
`appsettings.json` contains no identifier or secret.

Run the root `npm run build:analytics` before serving this project so the React
library exists under `wwwroot/analytics-mfe`, then `dotnet build` (packages are
restored only from the Microsoft-protected feed in `NuGet.Config`).

## Stored preferences

Three settings survive a reload, in first-party cookies written by
`Services/ShellPreferenceStore.cs` through `wwwroot/js/shellPreferences.js`:

| Cookie | Setting | Values |
|---|---|---|
| `ns.theme` | Appearance | `Light`, `Dark`, `System` |
| `ns.locale` | Display language | `en-LU`, `fr-LU`, `de-DE`, `nl-BE`, `es-ES` |
| `ns.helpBilingual` | Help Assistant: English + French | `True`, `False` |

They are functional preference cookies: no personal data, no identifier, no
tracking, `SameSite=Lax`, one-year lifetime, and `Secure` whenever the page is
served over HTTPS. `ShellState` stays a synchronous in-memory state machine —
the store subscribes to its change notification and writes through only when
one of the three values actually changes. A boot script in `index.html` reads
`ns.theme` before the WebAssembly runtime starts, so a returning dark-mode
visitor never sees a flash of the light shell.
