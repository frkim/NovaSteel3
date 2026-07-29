# 14 · Cross-cutting features

**Audience:** beginners who already know the screens and now need to understand the features that appear everywhere.  
**Reading time:** ~15 minutes.  
**Related routes:** all NovaSteel portal routes; especially `/lu/command-center/overview`, `/lu/platform-ops/capacity`, `/lu/dashboards/collections`.  
**Last updated:** 2026-07-27  
**Language:** 🇫🇷 [Version française](../fr/14-cross-cutting-features.md)

---

Cross-cutting means “not tied to one business screen.” These features make every screen usable, honest, explainable, and repeatable. They do **not** change the safety boundary: data is synthetic, recommendations are advisory, and predictions are not measurements (`docs\architecture\solution-architecture.md:22-29`; `apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:102-119`).

## 1. Dockview workspace

![Dashboard collections in a Dockview workspace](../screenshots/dashboards-collections.png)

**What it is.** A draggable, resizable panel workspace around each screen. Dockview panels can be rearranged, resized, grouped, maximized, and reset (`docs\ux\dashboard-specification.md:34-35`).

**What you see.** Each panel has a tab label such as `Key metrics`, `Site status`, or `Collection cards`. Grey tab bars include maximize arrows. The toolbar has `Reset layout` when a Dockview layout is present (`apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:147-160`).

**Why implemented.** Steel operators compare related signals: a KPI, a chart, a table, and the “why” panel. Dockview lets the same screen fit a presenter wall, laptop, or tablet without making separate pages (`docs\ux\dashboard-specification.md:30-36`).

**Evidence.** The panel collector derives stable panels from screen JSX and marks KPI/structural panels non-closable unless the screen provides an `onDockClose` callback (`apps\analytics-mfe\src\components\dock\dockPanels.ts:111-139`, `apps\analytics-mfe\src\components\dock\dockPanels.ts:198-212`). Layout is stored per screen under `novasteel.dock.v1.*`, restored from localStorage, and reset by clearing the screen layout (`apps\analytics-mfe\src\components\dock\WorkspaceDock.tsx:101-128`, `apps\analytics-mfe\src\components\dock\WorkspaceDock.tsx:266-277`, `apps\analytics-mfe\src\components\dock\WorkspaceDock.tsx:336-360`). Maximize arrows are tab-bar actions (`apps\analytics-mfe\src\components\dock\WorkspaceDock.tsx:64-96`).

## 2. Copilot chat dock

![Copilot panel](../screenshots/feature-copilot-panel.png)

**What it is.** A docked chat panel that can answer questions about the current screen, steel terms, and synthetic demo data.

**What you see.** `Copilot` opens a right dock titled `Copilot`. The panel shows language selection, enterprise data protection notice, context mode, suggested questions, question box, online-search toggle, reasoning tier, glossary, and conversations.

**Why implemented.** Beginners need plain-language explanations without leaving the screen. The dock keeps the workspace visible while the answer appears beside it.

**Requirement served.** Knowledge preservation and GenAI support map to `AI-03` and `CHL-05`; AI transparency maps to `REG-02` (`docs\presentation\proof_of_execution.md:259-276`, `docs\presentation\proof_of_execution.md:362-406`).

**Evidence.** `CopilotDock` hosts the dashboard and chat in Dockview, keeps the dashboard tab non-closable, docks Copilot to the right, disables floating groups, and persists layout (`apps\analytics-mfe\src\components\copilot\CopilotDock.tsx:59-80`, `apps\analytics-mfe\src\components\copilot\CopilotDock.tsx:115-123`, `apps\analytics-mfe\src\components\copilot\CopilotDock.tsx:177-216`). `CopilotPanel` sends section/subView/site context only when context mode is enabled and displays sources, conversations, language, temporary mode, online search, and reasoning (`apps\analytics-mfe\src\components\copilot\CopilotPanel.tsx:284-313`, `apps\analytics-mfe\src\components\copilot\CopilotPanel.tsx:400-548`). It deliberately renders constrained markdown so model output cannot inject HTML (`apps\analytics-mfe\src\components\copilot\CopilotPanel.tsx:120-157`).

## 3. “What's this?” help assistant and bilingual help

![Help assistant explain mode](../screenshots/feature-help-assistant.png)

**What it is.** An explain mode. When active, the app says `Explain mode - click any element`; your next click explains the widget instead of activating it.

**What you see.** Blue banner at the top, selected element outline, and a popup with a plain explanation. If bilingual help is enabled in Settings, explanations can show English and French.

**Why implemented.** The audience includes steel newcomers. They need help attached to the exact KPI, table, button, or chart they are looking at.

**Requirement served.** EU AI Act transparency and operator knowledge support: `REG-02`, `AI-03`, `CHL-05` (`docs\presentation\proof_of_execution.md:105-152`, `docs\presentation\proof_of_execution.md:406-439`).

**Evidence.** The dashboard exposes the `What's this?` button and passes scope, locale, and `helpBilingual` into `HelpAssistant` (`apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:161-172`, `apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:240-247`). The assistant intercepts clicks, prevents the normal action, resolves the help target, draws a viewport frame, and exits on Escape (`apps\analytics-mfe\src\components\help\HelpAssistant.tsx:61-132`, `apps\analytics-mfe\src\components\help\HelpAssistant.tsx:212-320`). Settings exposes the bilingual checkbox (`apps\portal-shell\Components\SettingsDialog.razor:63-72`).

## 4. Guided demo tour

**What it is.** A presenter-friendly tour through the demo moments.

**What you see.** `Start guided demo` is always available in the dock. The tour panel has a step number, title, narrative, headline, Next/Back, and optional auto-advance.

**Why implemented.** The defense/demo needs a reliable story that does not depend on live plant data.

**Requirement served.** The tour ties the four headline outcomes and AI infusion points together; the first tour step explicitly repeats −14% energy, −22% CO₂, +8% yield, and 21-day warning (`apps\analytics-mfe\src\components\DemoTour.tsx:27-70`).

**Evidence.** The dashboard renders the button unconditionally (`apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:189-196`) and mounts `DemoTour` on every screen (`apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:241`). `DemoTour` navigates by emitting `nav.intent` and uses deterministic steps (`apps\analytics-mfe\src\components\DemoTour.tsx:82-108`, `apps\analytics-mfe\src\components\DemoTour.tsx:116-168`).

## 5. Fabric capacity control panel

![Fabric capacity control](../screenshots/feature-capacity-panel.png)

**What it is.** Shell-owned control for non-production Microsoft Fabric capacity lifecycle and SKU.

**What you see.** Right-side `Fabric capacity` dialog with state, capacity id, SKU, environment, region, source, reason, SKU dropdown, `Apply SKU`, `Request start`, `Request pause`, and recent transitions.

**Why implemented.** Fabric costs money when running. The platform makes start/pause visible, role-gated, audited, and separate from dashboards.

**Requirement served.** Platform cost awareness and governance; it supports the UX goal for cost-aware platform control (`docs\ux\dashboard-specification.md:34-35`).

**Evidence.** The top-bar pill opens the dialog (`apps\portal-shell\Layout\MainLayout.razor:44-53`). The panel says simulated transitions fire no ARM operation and gates controls by role/busy state (`apps\portal-shell\Components\CapacityPanel.razor:19-22`, `apps\portal-shell\Components\CapacityPanel.razor:62-82`, `apps\portal-shell\Components\CapacityPanel.razor:135-155`). The shell README says requests raised by React are routed through the same shell service and BFF, never directly to ARM (`apps\portal-shell\README.md:8-18`).

## 6. Settings dialog

![Settings dialog](../screenshots/feature-settings-dialog.png)

**What it is.** Modal for appearance, language, data mode, BFF URL display, and bilingual help.

**What you see.** `Light`, `Dark`, `System`; a locale listbox; the read-only BFF base URL; bilingual help checkbox.

**Why implemented.** Preferences belong to the shell because they affect every page and must be accessible before the React MFE even renders.

**Requirement served.** Accessibility and multilingual operations support WCAG and cross-country operation (`docs\ux\dashboard-specification.md:14-16`, `docs\usecase\usecase.md:7-10`).

**Evidence.** `SettingsDialog` defines those sections and controls (`apps\portal-shell\Components\SettingsDialog.razor:17-72`). It focuses the dialog, supports Escape, and activates a focus trap (`apps\portal-shell\Components\SettingsDialog.razor:103-160`). State maps to `ThemeMode`, `Locale`, and `HelpBilingual` (`apps\portal-shell\Services\ShellState.cs`).

## 7. Theme and dark mode

![Dark theme](../screenshots/feature-dark-theme.png)

**What it is.** Light, dark, or system theme for shell and dashboards.

**What you see.** The same Command Center structure with darker surfaces and adjusted contrast.

**Why implemented.** Control rooms and presentations vary in lighting. Theme support also helps meet accessibility goals.

**Evidence.** Shell cycles the mode and changes the icon/title (`apps\portal-shell\Services\ShellState.cs:182-190`; `apps\portal-shell\Layout\MainLayout.razor:230-243`). The shell contract carries `themeMode` (`contracts\ui\shell-interop.v1.schema.json:18-25`). React builds a NovaSteel theme from that value and updates document tokens (`apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:42-44`, `apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:89-92`).

## 8. Account menu

![Account menu](../screenshots/feature-account-menu.png)

**What it is.** Demo identity and role visibility menu.

**What you see.** `Synthetic Demo User`, `Signed in (demo identity)`, roles, and `Sign out (demo)`.

**Why implemented.** The app demonstrates role-gated UI without exposing real credentials. The browser receives an opaque token reference, not a bearer token (`contracts\ui\shell-interop.v1.schema.json:41-45`; `README.md:35-39`).

**Evidence.** MainLayout renders current user, role list, and sign-in toggle (`apps\portal-shell\Layout\MainLayout.razor:71-89`). Auth demo context defines role-to-action mappings and demo plant scope (`apps\portal-shell\Services\AuthDemoContext.cs:24-34`, `apps\portal-shell\Services\AuthDemoContext.cs:70-77`).

## 9. Localization and unit formatting

**What it is.** Shared language and locale behavior across shell and microfrontend.

**What you see.** Locale flag/listbox in the shell, `en-LU` in screenshots, and translated UI keys when another locale is selected.

**Why implemented.** The use case spans Luxembourg, Germany, Belgium, and Spain, so users need local language and formatting without changing the data model (`docs\usecase\usecase.md:7-10`).

**Evidence.** Shell locales are `en-LU`, `fr-LU`, `de-DE`, `nl-BE`, `es-ES` (`apps\portal-shell\Services\ShellState.cs:37-38`). The React message catalog covers English, French, German, Dutch, and Spanish and falls back gracefully (`apps\analytics-mfe\src\i18n\messages.ts:15-20`, `apps\analytics-mfe\src\i18n\messages.ts:21-123`). React context fixes `unitSystem: 'metric'` for the app (`apps\analytics-mfe\src\components\AnalyticsDashboard.tsx:70-83`).

## 10. Shared UI primitives

| Primitive | What it is | Why implemented | Evidence |
|---|---|---|---|
| KPI card with why-popover | A status-colored metric tile with value, trend, target, freshness, and optional “Why?” drivers. | AI-derived values need confidence, freshness, and explanation for trust and EU AI Act alignment. | `apps\analytics-mfe\src\components\primitives\KpiCard.tsx:79-219`; `WhyPopover` model version, scored time, drivers `apps\analytics-mfe\src\components\primitives\WhyPopover.tsx:15-82`; UX trust goal `docs\ux\dashboard-specification.md:30-33`. |
| Data table | Searchable, sortable, hideable-column, exportable table with density and refresh controls. | Operators must inspect evidence rows, not just charts. | `apps\analytics-mfe\src\components\primitives\DataTable.tsx:76-183`; toolbar/search/export `apps\analytics-mfe\src\components\primitives\DataTable.tsx:248-313`; table semantics `apps\analytics-mfe\src\components\primitives\DataTable.tsx:340-428`. |
| Freshness badge | Small age/source indicator. | Separates live BFF data from cached/offline fixture data and flags staleness. | `apps\analytics-mfe\src\components\primitives\FreshnessBadge.tsx:14-38`. |
| Confidence meter | P10/P50/P90 uncertainty bar. | Predictions must show uncertainty, not pretend exactness. | `apps\analytics-mfe\src\components\primitives\ConfidenceMeter.tsx:13-64`; lining uncertainty target `docs\presentation\proof_of_execution.md:340-352`. |
| Severity pill | Text+glyph+color status pill. | Accessibility: state must not rely on color alone. | `apps\analytics-mfe\src\components\primitives\SeverityPill.tsx:10-33`; WCAG target `docs\ux\dashboard-specification.md:14-16`. |
| Proof badge | Clickable requirement ID badge. | Lets any screen trace back to the use-case line it proves. | `apps\analytics-mfe\src\components\primitives\ProofBadge.tsx:13-19`, `apps\analytics-mfe\src\components\primitives\ProofBadge.tsx:28-50`; proof IDs overview `docs\presentation\proof_of_execution.md:16-28`. |
| State boundary | Loading, empty, and error wrapper. | Keeps every data panel understandable during loading, empty filters, and failures. | `apps\analytics-mfe\src\components\primitives\StateBoundary.tsx:41-99`. |

---

◀ Previous [13 · Platform Ops](13-platform-ops.md) · ▲ Index ([README.md](README.md)) · Next ▶ [15 · Glossary](15-glossary.md)
