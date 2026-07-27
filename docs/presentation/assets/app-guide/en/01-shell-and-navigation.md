# 01 · Shell & navigation

**Audience:** first-time NovaSteel users who need to know what every persistent control does.  
**Reading time:** ~16 minutes.  
**Related routes:** `/{site}/{section}/{subView}`, `/lu/command-center/overview`, `/lu/furnace-health/lining-forecast`, `/lu/platform-ops/capacity`.  
**Last updated:** 2026-07-27  
**Language:** 🇫🇷 [Version française](../fr/01-shell-and-navigation.md)

---

![Command Center chrome reference](../screenshots/command-center-overview.png)

Use the screenshot above as the map. The same shell surrounds every screen: logo, top bar, purple synthetic-data banner, left rail, breadcrumb, content, dock buttons, toast area, and footer. The shell is Blazor-owned; the dashboard inside it is React-owned (`apps\portal-shell\README.md:1-6`; `docs\ux\dashboard-specification.md:64-78`).

## The route grammar

Routes use `/{site}/{section}/{subView}`. The Blazor host declares `/`, `/{Site}`, `/{Site}/{Section}`, and `/{Site}/{Section}/{SubView}` (`apps\portal-shell\Pages\AnalyticsHost.razor:1-4`). Missing site redirects to `/lu/command-center` (`apps\portal-shell\Pages\AnalyticsHost.razor:30-39`). The route builder emits `/{Site}/{section}` or `/{Site}/{section}/{subView}` (`apps\portal-shell\Services\ShellState.cs:205-209`).

Examples: `/lu/command-center/overview`, `/de/energy-optimization/spot-price-schedule`, `/be/quality/batches`, `/es/device-operations/fleet`.

## Why a Blazor shell hosts a React microfrontend

The project keeps C# where the brief wanted it: sign-in, routing, chrome, theme, locale, and capacity lifecycle. It uses React/MUI where dense dashboards need KPI cards, D3-style charts, and virtualized tables (`docs\ux\dashboard-specification.md:64-88`). The architecture repeats the same boundary: Blazor shell in the browser, React/TypeScript MFE for analytics, and Python FastAPI APIs behind it (`docs\architecture\solution-architecture.md:44-50`, `docs\architecture\solution-architecture.md:109-117`).

## Shell ↔ microfrontend contract

The shell passes a typed context defined by `contracts\ui\shell-interop.v1.schema.json`: `themeMode`, `locale`, `activePersona`, `site`, `demoMode`, an opaque `tokenRef`, `bridgeVersion`, and `navigation` (`contracts\ui\shell-interop.v1.schema.json:7-16`, `contracts\ui\shell-interop.v1.schema.json:18-81`). The React app is mounted through `AnalyticsBridge`, which calls JavaScript `mount` and later `update` when context changes (`apps\portal-shell\Components\AnalyticsBridge.razor:20-39`).

Events flow back to the shell through `ReceiveEvent` (`apps\portal-shell\Components\AnalyticsBridge.razor:42-44`):

| Event | Meaning | Evidence |
|---|---|---|
| `nav.intent` | React asks Blazor to navigate to another route. | `apps\portal-shell\Pages\AnalyticsHost.razor:47-53` |
| `capacity.request` | React asks the shell to mediate a start/pause/SKU-type capacity request through the BFF. | `apps\portal-shell\Pages\AnalyticsHost.razor:54-66` |
| `capacity.panel` | React asks the shell to open the shell-owned capacity panel. | `apps\portal-shell\Pages\AnalyticsHost.razor:68-73` |
| `toast` | React asks the shell to show a status message. | `apps\portal-shell\Pages\AnalyticsHost.razor:74-79` |
| `telemetry` | React emits an accepted telemetry event notice. | `apps\portal-shell\Pages\AnalyticsHost.razor:81-83` |

## Chrome components, one by one

| Component | What it is | What you see | Why it exists | Evidence |
|---|---|---|---|---|
| Brand / home link | The NovaSteel logo link in the top-left. | Logo and “FORGING INTELLIGENCE INTO STEEL”; clicking returns to Command Center. | Gives a stable home anchor and keeps shell navigation outside the MFE. | `apps\portal-shell\Layout\MainLayout.razor:10-15`; shell ownership in `apps\portal-shell\README.md:1-6`. |
| Site selector | Plant selector for the multi-country estate. | `LU - Moselle Integrated Works`; options include LU, DE, BE, ES, and ALL. | AxelorMetal spans four countries; users must switch scope without changing app. | `apps\portal-shell\Layout\MainLayout.razor:17-25`; `apps\portal-shell\Services\ShellState.cs:23-38`; four-country use case `docs\usecase\usecase.md:7-10`. |
| Persona selector | Primary role selector. | `Marc Weber - Plant Manager` in the top bar; the list shows the named demo personas, not bare role names. | A person can hold several demo personas; the shell routes to that persona's default area **and narrows the left navigation to the sections that persona works in**. | `apps\portal-shell\Layout\MainLayout.razor:27-35`; persona labels and navigation scoping in `apps\portal-shell\Services\ShellState.cs`; personas in `docs\personas\personas-and-journeys.md:44-53`. |
| Global search | Shell-level search field. | Placeholder `Search…`. | Gives a global entry point but deliberately redirects users to scoped in-view search for accuracy. | `apps\portal-shell\Layout\MainLayout.razor:37-40`, `apps\portal-shell\Layout\MainLayout.razor:216-222`. |
| Fabric capacity pill | Top-bar status and entry to capacity control. | `Fabric: Paused` plus `Simulated`. | Makes non-production Fabric cost/lifecycle visible and shell-owned. | `apps\portal-shell\Layout\MainLayout.razor:44-53`; `apps\portal-shell\README.md:8-18`; `OBJ/ops` evidence in `docs\ux\dashboard-specification.md:34-35`. |
| Alerts bell | Shortcut to Command Center alerts. | Bell icon with red badge `3`. | Keeps critical triage one click away from every screen. | `apps\portal-shell\Layout\MainLayout.razor:55-57`, `apps\portal-shell\Layout\MainLayout.razor:225-228`; Command Center purpose `apps\analytics-mfe\src\personaRoutes.ts:18-24`. |
| Theme cycle button | Light/dark/system toggle. | Sun/system icon near the locale flag; dark screenshot changes the dashboard chrome. | Supports accessibility, presentation rooms, and user comfort without changing data. | `apps\portal-shell\Layout\MainLayout.razor:59-62`, `apps\portal-shell\Layout\MainLayout.razor:230-243`; Settings radio buttons `apps\portal-shell\Components\SettingsDialog.razor:18-40`. |
| Locale listbox | Language/locale selector. | Flag plus `en-LU`; listbox supports five locales. | Supports Luxembourg, French, German, Dutch/Belgian, and Spanish operations. | `apps\portal-shell\Layout\MainLayout.razor:64-65`; locales in `apps\portal-shell\Services\ShellState.cs:37-38`; listbox UI `apps\portal-shell\Components\LocaleListbox.razor:3-35`. |
| DEMO / CLOUD toggle | Data-source mode button. | Purple `DEMO` badge in screenshots. | Makes demo honesty visible; cloud mode still keeps data synthetic when BFF says demo data. | `apps\portal-shell\Layout\MainLayout.razor:67-69`; toggle behavior `apps\portal-shell\Services\ShellState.cs:124-180`. |
| Account / identity menu | Demo sign-in menu. | Avatar `SU`; popover shows Synthetic Demo User, roles, and Sign out (demo). | Separates shell-owned identity and permitted actions from React dashboards. | `apps\portal-shell\Layout\MainLayout.razor:71-89`; role headers in `apps\portal-shell\Services\AuthDemoContext.cs:24-34`. |
| Hamburger menu | Compact main menu. | Three-line icon; menu contains Settings, Reset workspace layout, About NovaSteel. | Keeps lower-frequency shell actions available without crowding the top bar. | `apps\portal-shell\Layout\MainLayout.razor:91-115`, `apps\portal-shell\Layout\MainLayout.razor:245-287`. |
| Settings dialog | Modal for appearance, language, data, and help preferences. | `Settings`, Appearance Light/Dark/System, Locale, Demo mode, BFF base URL, bilingual help checkbox. | Groups durable shell preferences and traps focus for accessibility. | `apps\portal-shell\Components\SettingsDialog.razor:5-75`, focus handling `apps\portal-shell\Components\SettingsDialog.razor:103-160`. |
| Synthetic-data banner | Purple honesty banner. | `Synthetic demo data — not for operational control` across the top and inside the dashboard. | Prevents confusion between demo predictions and operational measurements. | Shell banner `apps\portal-shell\Layout\MainLayout.razor:118-122`; React banner `apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:102-119`; advisory boundary `docs\architecture\solution-architecture.md:24-29`. |
| Left navigation rail | Persistent, persona-scoped section navigation. | Groups: DAILY OPERATIONS, INSIGHT & GOVERNANCE, PLATFORM & REFERENCE. The screenshots show the Plant Manager, who — as the cross-domain triage role — keeps the full 14-entry menu; an Energy Manager sees 4 entries under 2 headings. A heading whose items are all filtered out disappears with them, and the section you are currently on always stays listed so a deep link cannot strand you. | Lets beginners find their own role surfaces without reading past screens that belong to someone else, while keeping cross-role navigation for triage. | `apps\portal-shell\Layout\MainLayout.razor:125-145`; group definitions and persona scoping `apps\portal-shell\Services\ShellState.cs`. |
| Breadcrumb | Location trail above the page title. | Example: `LU / Command Center` or `LU › Executive›overview`. | Shows site and screen context after route changes or deep links. | Shell breadcrumb `apps\portal-shell\Layout\MainLayout.razor:147-154`; React breadcrumb `apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:127-139`. |
| Toast area | Temporary shell message area. | Appears above content when search, about, or bridge events publish a message. | Confirms actions without using modal dialogs. | `apps\portal-shell\Layout\MainLayout.razor:155-158`; publish method `apps\portal-shell\Services\ShellState.cs:193-197`. |
| Footer | Always-visible mode and accessibility note. | Left: `Demo mode · BFF http://localhost:8080`; right: `WCAG 2.2 AA target · synthetic evidence only`. | Reminds users of backend source, accessibility target, and synthetic evidence. | `apps\portal-shell\Layout\MainLayout.razor:163-166`; WCAG target in `docs\ux\dashboard-specification.md:14-16`. |
| Dock action buttons | Page-level controls owned by the MFE but framed by shell context. | `Reset layout`, `What's this?`, `Copilot`, `Start guided demo`, plus persona chip. | Gives every screen the same workspace, help, chat, and demo controls. | `apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:147-192`; Dock reset behavior `apps\analytics-mfe\src\components\dock\WorkspaceDock.tsx:266-277`. |

## Screenshots for menus and panels

![Account menu](../screenshots/feature-account-menu.png)

The account screenshot shows the avatar menu expanded over the Command Center. It lists demo roles such as `Operator.Read`, `MaintenanceEngineer.Read`, `EnergyPlanner.Approve`, and `Platform.Capacity.Manage`; those roles are shell-side demo identity, not proof of a real signed-in employee (`apps\portal-shell\Layout\MainLayout.razor:75-87`; `apps\portal-shell\Services\AuthDemoContext.cs:24-34`).

![Settings dialog](../screenshots/feature-settings-dialog.png)

The settings screenshot shows appearance radios, locale selector, Demo mode checked, BFF base URL `http://localhost:8080`, and the bilingual help option. These settings map to `ThemeMode`, `Locale`, `DemoMode`, and `HelpBilingual` in `ShellState` (`apps\portal-shell\Services\ShellState.cs:64-83`, `apps\portal-shell\Components\SettingsDialog.razor:18-72`).

![Fabric capacity panel](../screenshots/feature-capacity-panel.png)

The capacity screenshot is a right-side dialog with state `Paused`, capacity id, SKU `F2`, environment `demo`, region `Sweden Central`, source `Live BFF`, reason field, SKU selector, and `Request start` / `Request pause`. It explicitly says simulated transitions do not fire ARM operations (`apps\portal-shell\Components\CapacityPanel.razor:19-31`, `apps\portal-shell\Components\CapacityPanel.razor:38-73`).

![Dark theme](../screenshots/feature-dark-theme.png)

The dark-theme screenshot keeps the same layout while changing visual tokens. The shell cycles system → light → dark → system, and React receives `themeMode` through the bridge (`apps\portal-shell\Layout\MainLayout.razor:230-243`; `contracts\ui\shell-interop.v1.schema.json:18-25`; `apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:42-44`).

---

◀ Previous [00 · Getting started](00-getting-started.md) · ▲ Index ([README.md](README.md)) · Next ▶ [02 · AxelorMetal public website](02-company-website.md)
