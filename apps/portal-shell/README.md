# NovaSteel portal shell

The Blazor WebAssembly host owns global chrome and identity: top bar, left-rail
persona navigation, breadcrumb, footer, theme/locale switch, site + **primary
persona** selection, demo/cloud mode, the demo sign-in identity context, routing,
and the authoritative **Fabric capacity lifecycle control surface**.

## Capacity control

The top-bar capacity pill reflects live state and opens a shell-owned control
panel (`Components/CapacityPanel.razor`). `Services/CapacityService.cs` calls only
the BFF (`GET /v1/platform/capacity` and the start/pause request routes) with
demo headers and an idempotency key; it never reaches ARM and never scales a SKU.
`Platform.Capacity.Manage` gates the request buttons. When the BFF is
unavailable, `Services/CapacityState.cs` falls back to a deterministic simulated
lifecycle so the demo control always works. Capacity requests raised by the React
microfrontend (`capacity.request`) are routed through this same shell service.

## Bridge and configuration

The shell passes a typed, versioned context to the analytics microfrontend
(`contracts/ui/shell-interop.v1.schema.json`), including the configurable
`Bff:BaseUrl` and the demo user's server-consistent `permittedActions`. Add Entra
application values only through deployment configuration; the committed
`appsettings.json` contains no identifier or secret.

Run the root `npm run build:analytics` before serving this project so the React
library exists under `wwwroot/analytics-mfe`, then `dotnet build` (packages are
restored only from the Microsoft-protected feed in `NuGet.Config`).
