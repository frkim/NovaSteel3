# NovaSteel — final local demonstration handoff

> **Delivery status:** runnable demonstration; source, tests, Bicep IaC, Fabric definitions, CI gates, and defense assets are present.  
> **Cloud status:** **deployed** to Azure Sweden Central (`rg-novasteelv3-demo-sc`). Fabric, Foundry Agent Service, Speech, and OT/tenant integrations remain gated production work.

**Live demonstration endpoints**

| Surface | URL |
|---|---|
| Portal (front end) | <https://novasteelv3-portal.calmbeach-dbad72b1.swedencentral.azurecontainerapps.io> |
| Command centre (deep link) | <https://novasteelv3-portal.calmbeach-dbad72b1.swedencentral.azurecontainerapps.io/NS-DEMO-LUX-01/command-center/overview> |
| BFF API | <https://novasteelv3-bff.calmbeach-dbad72b1.swedencentral.azurecontainerapps.io> |

NovaSteel is an EU-oriented, Fabric-centered decision-support platform for
AxelorMetal's four-country steel estate. It uses a Blazor WebAssembly shell, a
React/MUI/D3 analytics microfrontend with Dockview workspaces, a FastAPI BFF,
Python advisory services (a PuLP/CBC
MILP energy optimiser, a physics-informed RUL regressor, and a knowledge
orchestrator with a critic loop and agent handoff), and synthetic simulator
fixtures. Every service runs fully offline against deterministic fixtures as a
demonstration fallback.

## Architecture and safety boundary

`OT gateway (outbound only) → Event Hubs → managed-identity relay → Fabric
Eventstream → Eventhouse/KQL + OneLake/Lakehouse → Python advisory services →
FastAPI BFF → Blazor shell + React dashboard`

- Fabric is the intended governed analytics core. Adapters are selected at
  runtime: Azure implementations activate when their configuration is present
  (`FOUNDRY_ENDPOINT`, `NOVASTEEL_TABLE_ENDPOINT`,
  `APPLICATIONINSIGHTS_CONNECTION_STRING`), and deterministic local fixtures are
  used otherwise, so the demonstration never depends on tenant availability.
- The platform is **decision support**, never PLC, interlock, furnace, recipe,
  setpoint, schedule-commit, or CMMS control.
- Local mode accepts only `NS-DEMO-*` scope, binds the BFF to `127.0.0.1`, and
  labels all data synthetic/non-personal.
- The browser receives an opaque token reference, not a workload bearer token.
  Cloud identities are designed for Entra managed identity/OIDC, not secrets.

## Prerequisites and protected feeds

- Windows with PowerShell 7 (`pwsh`), Python 3.13, Node/npm (rehearsed:
  Node 22.19.0 / npm 10.9.3), and .NET SDK 10.0.302 (`global.json`).
- Existing dependencies are sufficient for the normal local demo. Azure CLI and
  Fabric CLI are required only for the gated cloud steps.
- **Python and NuGet restores are mandatory through the repository feeds:**
  - Python: `https://packagefeedproxy.microsoft.io/pypi/simple`
  - NuGet: `https://packagefeedproxy.microsoft.io/nuget/v3/index.json`

Microsoft-managed devices block direct access to the public PyPI and NuGet
registries; package downloads must go through Microsoft-protected feeds backed
by Central Feed Services (CFS). The full policy, including the blocked-endpoint
list, is [`docs\tech\security_requirement.md`](docs/tech/security_requirement.md).

`pip.conf` supplies the only Python index. `NuGet.Config` clears inherited
sources and maps every package to `MicrosoftProtectedFeed`. Never add an extra
Python index or another NuGet source. If Node dependencies must be restored,
set `NPM_CONFIG_REGISTRY` to the organization-approved protected npm proxy; do
not use a public fallback. If a package is unavailable on a protected feed,
stop and request the approved CFS exception rather than falling back to a
public registry.

### First-time protected restore

Run from the repository root:

```powershell
if (-not (Test-Path .\services\bff-api\.venv\Scripts\python.exe)) {
    python -m venv .\services\bff-api\.venv
}

$env:PIP_CONFIG_FILE = "$PWD\pip.conf"
$env:PIP_INDEX_URL = "https://packagefeedproxy.microsoft.io/pypi/simple"
$env:PIP_EXTRA_INDEX_URL = ""
$env:PIP_NO_INPUT = "1"

& .\services\bff-api\.venv\Scripts\python.exe -m pip install `
    --disable-pip-version-check `
    -r .\services\bff-api\requirements.txt

dotnet restore .\apps\portal-shell\PortalShell.csproj `
    --configfile .\NuGet.Config `
    --locked-mode

# Only if node_modules is absent. Supply the approved internal registry first.
$env:NPM_CONFIG_REGISTRY = "https://<organization-approved-npm-proxy>"
npm ci --ignore-scripts
```

## One-command local validation

```powershell
pwsh .\tools\validation\Validate-Repository.ps1
```

This is the local, no-cloud validation entry point. It checks protected feeds,
contracts, simulator, BFF/integration, knowledge workflow, frontend lint/tests/
build, protected portal restore/build, IaC, Fabric assets, PowerPoint package,
security, dependency integrity, and SBOM generation. Evidence is written under
`artifacts\validation\`. The npm vulnerability audit is intentionally skipped
unless `NPM_CONFIG_REGISTRY` is an approved non-public HTTPS registry.

## Exact Windows PowerShell demo procedure

The BFF reads the committed `services\bff-api\fixtures\demo-full` fixture; no
simulator process or cloud account is required to present the web demo.

### 1. Build the portal (terminal 1)

```powershell
npm run build:analytics
dotnet restore .\apps\portal-shell\PortalShell.csproj --configfile .\NuGet.Config --locked-mode
npm run build:portal
```

### 2. Start the local BFF (terminal 2)

```powershell
npm run run:bff
```

Wait for `Application startup complete`, then verify:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health/ready
```

### 3. Start the shell (terminal 1)

```powershell
dotnet run --project .\apps\portal-shell\PortalShell.csproj `
    --launch-profile http `
    --no-restore
```

Open the default, scenario-aligned route:

```powershell
Start-Process http://localhost:5266/lu/command-center
```

The shell maps routes to the demo persona surface; its demo identity is scoped
to `NS-DEMO-LUX-01`. Useful direct routes are:

| Persona / proof point | Route |
|---|---|
| Plant Manager command center | `http://localhost:5266/lu/command-center` |
| Shift operations board | `http://localhost:5266/lu/operations/overview` |
| Energy Manager dispatch | `http://localhost:5266/lu/energy-optimization/spot-price-schedule` |
| Reliability Engineer RUL | `http://localhost:5266/lu/furnace-health/lining-forecast` |
| Quality Engineer genealogy | `http://localhost:5266/lu/quality/batches` |
| Knowledge Engineer review | `http://localhost:5266/lu/knowledge-hub/procedures` |
| Sustainability / audit | `http://localhost:5266/lu/sustainability-compliance/emissions-ledger` |
| Executive overview | `http://localhost:5266/lu/executive-overview` |
| Platform capacity simulation | `http://localhost:5266/lu/platform-ops/capacity` |
| Device Fleet (wave 3) | `http://localhost:5266/lu/device-operations/fleet` |
| Sensor Explorer (wave 3) | `http://localhost:5266/lu/device-operations/sensors` |
| Device Simulator (wave 3) | `http://localhost:5266/lu/device-operations/simulator` |
| Dashboard Collections (wave 3) | `http://localhost:5266/lu/dashboards/collections` |
| AxelorMetal corporate website (wave 4) | `http://localhost:5266/lu/company-website/home` |
| Use-case brief | `http://localhost:5266/lu/proof-of-execution/use-case` |
| Requirement register / proof of execution | `http://localhost:5266/lu/proof-of-execution/requirements` |
| Technical requirements (rating grid) | `http://localhost:5266/lu/technical-requirements/criteria` |

Every analytics route is a Dockview workspace: panels can be rearranged,
maximized, persisted per screen, and reset from the dashboard header. The
**Copilot** button opens an outer docked chat panel on any route. It answers from
the active screen's grounding material — screen profile, glossary, and an
optional curated public-context corpus — in EN/FR/DE/NL/ES, and reports the
reasoning tier and the sources it used. It has no tools and no data-plane access,
and conversations are held in the API process only. See [ADR-011, ADR-012, and
ADR-014](docs/architecture/solution-architecture.md#10-architecture-decision-records).

### 4. Run the scripted API demonstration

With the BFF running:

```powershell
& .\services\bff-api\.venv\Scripts\python.exe .\artifacts\demo-validation\drive_demo.py
```

It executes the six demo moments plus telemetry, table behavior, authorization,
audit, and simulated capacity lifecycle; refreshed response evidence is written
to `artifacts\demo-validation\http\`.

### 5. Reset, optional simulator generation, and stop

Restarting the BFF resets alert, work-order, recommendation, and interview state
to `READY` when it runs on the in-memory adapters. When `NOVASTEEL_TABLE_ENDPOINT`
is configured, the audit hash-chain and idempotency records persist in Azure
Table Storage and survive the restart. Stop its listener, then rerun
`npm run run:bff`:

```powershell
$listenerIds = @(
    Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
)
$listenerIds | ForEach-Object { Stop-Process -Id $_ }
```

The simulator is optional for the portal demo. Its generated output is isolated
and can be generated, validated, and removed safely:

```powershell
& .\services\bff-api\.venv\Scripts\python.exe -m simulator.cli demo --out .\output\demo
& .\services\bff-api\.venv\Scripts\python.exe -m simulator.cli validate --run-dir .\output\demo
& .\services\bff-api\.venv\Scripts\python.exe -m simulator.cli reset --out .\output\demo
```

The wave-3 **device simulator** runs in-process inside the BFF (no extra
Container App) and seeds the `degrading-furnace` incident automatically so the
Device Operations screens show a live fault on first load. To run it as a
standalone out-of-process service instead (e.g., for a team that wants to scale
it independently):

```powershell
# Standalone device simulator (optional, out-of-process)
& .\services\bff-api\.venv\Scripts\python.exe -m uvicorn device_simulator.app:app `
    --app-dir .\services\device-simulator\src `
    --host 127.0.0.1 --port 8081
```

Point the BFF at it by setting `DEVICE_SIMULATOR_URL=http://127.0.0.1:8081` in
the BFF environment. When the variable is absent, the BFF uses its built-in
in-process adapter (the default for the demo).

Stop both local listeners after the rehearsal:

```powershell
foreach ($port in 8080, 5266) {
    $listenerIds = @(
        Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique
    )
    $listenerIds | ForEach-Object { Stop-Process -Id $_ }
}
```

## Documentation

Start with [`docs\README.md`](docs/README.md), which routes each audience to the
right document.

If you are **new to the application or to steel making**, read the illustrated
application guide instead — a screenshot-driven, beginner-oriented walkthrough
of every screen, available in both languages:

- English — [`docs\presentation\assets\app-guide\en\README.md`](docs/presentation/assets/app-guide/en/README.md)
- Français — [`docs\presentation\assets\app-guide\fr\LISEZMOI.md`](docs/presentation/assets/app-guide/fr/LISEZMOI.md)

It explains, for every screen, what you are looking at, why the component
exists, and which use-case requirement it evidences, and closes with a
glossary, a traceability matrix, and a guided demo walkthrough.

Other frequently used entry points:

| Topic | Document |
|---|---|
| Business brief | [`docs\usecase\usecase.md`](docs/usecase/usecase.md) |
| Requirement register / proof of execution | [`docs\presentation\proof_of_execution.md`](docs/presentation/proof_of_execution.md) |
| Architecture and ADRs | [`docs\architecture\solution-architecture.md`](docs/architecture/solution-architecture.md) |
| Screen-by-screen UX specification | [`docs\ux\dashboard-specification.md`](docs/ux/dashboard-specification.md) |
| Demo runbook | [`docs\demo\demo-runbook.md`](docs/demo/demo-runbook.md) |
| Package-feed security policy | [`docs\tech\security_requirement.md`](docs/tech/security_requirement.md) |

## Oral-defense handoff — 30 + 15 + 15 minutes

1. **00:00–30:00:** architecture/value story (20 primary slides).
2. **30:00–45:00:** deterministic six-moment persona demonstration.
3. **45:00–60:00:** moderated FAQ and production-gate discussion.

Open `docs\presentation\NovaSteel-Oral-Defense.pptx` for the final 26-slide
deck (20 primary slides including the demo handoff, plus six FAQ backups). Use
`docs\presentation\oral-defense-and-slide-plan.md` for speaker notes,
`docs\demo\demo-runbook.md` for minute-by-minute cues, and
`docs\presentation\faq.md` for the last 15 minutes. Local rehearsal evidence is
in `artifacts\demo-validation\rehearsal-report.md`; final handoff is
`artifacts\final-handoff.md`.

The same deck is also maintained as Markdown in `presentation\slides.md` and
rebuilt autonomously with [Marp](https://marp.app/): the `Presentation` workflow
regenerates `NovaSteel-Oral-Defense.pdf`, the speaker-note PDF and
`NovaSteel-Oral-Defense.pptx` on every change and publishes the web deck to
GitHub Pages. See [`presentation\README.md`](presentation/README.md).

## Validated proof

- 66/66 live BFF checks passed against the deterministic scenario; 1,139
  automated tests (874 Python, 265 frontend) and all 19 repository validation
  gates pass. Three further end-to-end persona journeys run against a live
  demo instance.
- RUL: P10/P50/P90 = 18.69/19.65/20.61 days, risk 0.8995 HIGH, confidence 0.7846.
  Regressed wear slope −3.21 mm/day at r² = 0.88 — the forecast moves when the
  thermal input moves.
- Energy: 960 = 960 tonnes conserved, zero hard-constraint violations, and on a
  whole-dispatch basis 7.25% cost, 3.29% CO₂ and 7.89% peak reduction
  (56.0 → 51.58 MW) at a 280 EUR/MWh scarcity peak. The movable-reheat-load-only
  view (21.74% cost, 31.71% CO₂) is exposed separately as `rawFlexibleCostPct` /
  `rawFlexibleCo2Pct` and is deliberately not used as a headline.
- Quality: bounded synthetic what-if 88% → 95%, with no operational write.
- Fallback/no-network: 12/12 checks passed; local BFF uses loopback only.
- PowerPoint package: 26 slides, no placeholders, aligned to the demo.

These are reproducible synthetic-scenario results, **not** realized production
outcomes. The 14% energy, 22% CO₂, 21-day warning, and 8% yield figures remain
pilot targets. The measured figures above are smaller because they cover one
24-hour scenario at a single site rather than an annualised four-country pilot;
the difference is scope, not a shortfall against the model.

## Repository map

| Path | Purpose |
|---|---|
| `apps\portal-shell` | Blazor WASM host, routing, demo identity, capacity mediation |
| `apps\analytics-mfe` | React/TypeScript MUI/D3 persona dashboard with Dockview workspaces, docked Copilot chat, and the AxelorMetal corporate website |
| `services` | FastAPI BFF, optimizer, scoring, ingest relay, knowledge orchestration and Copilot grounding |
| `services\device-simulator` | Deterministic 6-device/34-sensor fleet simulator (runs in-process inside BFF; standalone FastAPI app also ships) |
| `simulator` | Deterministic synthetic scenarios, validators, CLI |
| `contracts` | OpenAPI, event, data, and UI interop contracts |
| `infra` | Bicep control-plane IaC, policy, OIDC-only deployment scripts |
| `fabric` | Fabric REST/CLI assets, KQL, Lakehouse, notebooks, pipeline, semantic model |
| `tests` | Contract, simulator, backend, integration, E2E, infra, knowledge, and presentation tests |
| `tools\validation` | Local validation, feed/security scans, SBOM, PPTX validation |
| `docs` | Architecture, operations, runbook, presentation, research, and the bilingual illustrated application guide |
| `artifacts` | Local validation, rehearsal, fallback, and final-handoff evidence |
| `presentation` | Marp deck source (`slides.md`, `theme.css`) built to HTML/PDF/PPTX by the `Presentation` workflow |

## Cloud deployment

The `demo` environment is deployed to Azure Sweden Central. Reproduce or refresh
it with:

```powershell
az login
pwsh -File .\infra\scripts\validate.ps1 -Environment demo
pwsh -File .\infra\scripts\what-if.ps1 -Environment demo -OutFile .\artifacts\validation\whatif-demo.txt
pwsh -File .\infra\scripts\deploy.ps1 -Environment demo

Copy-Item .\fabric\deployment-parameters\demo.example.json `
    .\fabric\deployment-parameters\demo.parameters.json
pwsh -File .\fabric\scripts\Deploy-FabricAssets.ps1 `
    -ParameterFile .\fabric\deployment-parameters\demo.parameters.json
pwsh -File .\fabric\scripts\Test-FabricDeployment.ps1 `
    -ParameterFile .\fabric\deployment-parameters\demo.parameters.json `
    -StateFile .\fabric\deployment-state\demo.json `
    -Deep
```

The Fabric asset steps above require a target-tenant capacity and are still
gated; see **Known limitations** below for the full production gate list. No
cloud action may introduce an OT control write.

## Known limitations

- Fabric, Speech, Eventstream, and Power BI tenant resources are **not**
  provisioned in the deployed slice, which covers Container Apps, storage,
  networking, Key Vault, Event Hubs, and monitoring. Fabric access from a guest
  account is still unresolved. The Bicep templates now also declare the Foundry
  project, AI Search, Cosmos agent-thread storage and the Agent Service
  connections, but the Agent Service **capability host** stays behind the
  `foundryAgentServiceManuallyValidated` gate (it is immutable once created) and
  has not been deployed — see `infra/README.md`.
- The knowledge agent calls the Foundry chat deployment (`gpt-5.4-mini`) only when
  the container environment sets `KNOWLEDGE_AGENT_MODE=azure` and
  `FOUNDRY_ENDPOINT`; images ship offline-safe and fall back to fixtures
  otherwise. The same applies to Copilot chat (`COPILOT_CHAT_MODE`), the AI Search
  procedure store (`AI_SEARCH_ENDPOINT`) and hosted agents
  (`FOUNDRY_PROJECT_ENDPOINT`).
- Online search is `offline` by default. Web IQ / web-search grounding leaves the
  Azure compliance boundary and needs DPO sign-off before `ONLINE_SEARCH_MODE` is
  changed.
- Capacity actions remain simulated; no OT control write exists on any path.
- Full browser click-through automation is not installed; evidence covers served
  assets, CORS, component tests, and live BFF HTTP assertions.
- The Fabric scoring notebook still derives its P10/P90 band from fixed ×0.80 /
  ×1.30 multipliers, whereas the Python service derives the band from fit
  residuals. The two paths will disagree until the notebook is aligned.
- Production gates still outstanding: target-tenant Fabric capacity/SKU and
  quota; Eventstream Custom Endpoint managed-identity/network proof; Entra and
  Fabric item-level authorization; Foundry Agent Service and Speech private
  network validation; DPO/Legal/DPIA and EU AI Act decisions; OT vendor/DMZ
  approval; market-data licensing; DR, performance, accessibility, and
  live-cloud fallback rehearsal. Production capacity is never auto-paused.
