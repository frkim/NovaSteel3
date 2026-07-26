# NovaSteel — final local demonstration handoff

> **Delivery status:** runnable, deterministic local demonstration; source, tests, Bicep IaC, Fabric definitions, CI gates, and defense assets are present.  
> **Cloud status:** **not deployed**. Azure, Fabric, Foundry, Speech, and tenant integrations remain gated production work.

NovaSteel is an EU-oriented, Fabric-centered decision-support platform for a
four-country steel estate. The implemented local slice uses a Blazor WebAssembly
shell, React/MUI/D3 analytics microfrontend, FastAPI BFF, deterministic Python
scoring/optimization/knowledge workflows, and synthetic simulator fixtures.

## Architecture and safety boundary

`OT gateway (outbound only) → Event Hubs → managed-identity relay → Fabric
Eventstream → Eventhouse/KQL + OneLake/Lakehouse → Python advisory services →
FastAPI BFF → Blazor shell + React dashboard`

- Fabric is the intended governed analytics core; local mode replaces cloud
  adapters with deterministic fixtures only.
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

`pip.conf` supplies the only Python index. `NuGet.Config` clears inherited
sources and maps every package to `MicrosoftProtectedFeed`. Never add an extra
Python index or another NuGet source. If Node dependencies must be restored,
set `NPM_CONFIG_REGISTRY` to the organization-approved protected npm proxy; do
not use a public fallback.

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
| Energy Manager dispatch | `http://localhost:5266/lu/energy-optimization/spot-price-schedule` |
| Reliability Engineer RUL | `http://localhost:5266/lu/furnace-health/lining-forecast` |
| Quality Engineer genealogy | `http://localhost:5266/lu/quality/batches` |
| Knowledge Engineer review | `http://localhost:5266/lu/knowledge-hub/procedures` |
| Sustainability / audit | `http://localhost:5266/lu/sustainability-compliance/emissions-ledger` |
| Executive overview | `http://localhost:5266/lu/executive-overview` |
| Platform capacity simulation | `http://localhost:5266/lu/platform-ops/capacity` |

### 4. Run the scripted API demonstration

With the BFF running:

```powershell
& .\services\bff-api\.venv\Scripts\python.exe .\artifacts\demo-validation\drive_demo.py
```

It executes the six demo moments plus telemetry, table behavior, authorization,
audit, and simulated capacity lifecycle; refreshed response evidence is written
to `artifacts\demo-validation\http\`.

### 5. Reset, optional simulator generation, and stop

Restarting the BFF resets in-memory alert, work-order, recommendation, and
interview state to `READY`. Stop its listener, then rerun `npm run run:bff`:

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

## Validated local proof

- 66/66 live BFF checks passed against the local deterministic scenario.
- RUL: P10/P50/P90 = 16.8/21.0/27.5 days, risk 0.87 HIGH.
- Energy: 960 = 960 tonnes, zero hard-constraint violations, 9.94% modeled
  cost reduction at a 280 EUR/MWh peak.
- Quality: bounded synthetic what-if 88% → 95%, with no operational write.
- Fallback/no-network: 12/12 checks passed; local BFF uses loopback only.
- PowerPoint package: 26 slides, no placeholders, aligned to the demo.

These are reproducible synthetic-scenario results, **not** realized production
outcomes. The 14% energy, 22% CO₂, 21-day warning, and 8% yield figures remain
pilot targets.

## Repository map

| Path | Purpose |
|---|---|
| `apps\portal-shell` | Blazor WASM host, routing, demo identity, capacity mediation |
| `apps\analytics-mfe` | React/TypeScript MUI/D3 persona dashboard |
| `services` | FastAPI BFF, optimizer, scoring, ingest relay, knowledge orchestration |
| `simulator` | Deterministic synthetic scenarios, validators, CLI |
| `contracts` | OpenAPI, event, data, and UI interop contracts |
| `infra` | Bicep control-plane IaC, policy, OIDC-only deployment scripts |
| `fabric` | Fabric REST/CLI assets, KQL, Lakehouse, notebooks, pipeline, semantic model |
| `tests` | Contract, simulator, backend, integration, E2E, infra, and knowledge tests |
| `tools\validation` | Local validation, feed/security scans, SBOM, PPTX validation |
| `docs` | Architecture, operations, runbook, presentation, and research |
| `artifacts` | Local validation, rehearsal, fallback, and final-handoff evidence |

## Gated cloud deployment (not performed)

Do not treat local validation as a cloud deployment. After tenant, security, and
governance approval, use a dedicated `demo` environment:

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

Before production, clear all of these gates: target-tenant Fabric capacity/SKU
and quota; Eventstream Custom Endpoint managed-identity/network proof; Entra and
Fabric item-level authorization; Foundry Agent Service/model/Speech/private
network validation; container images promoted by OIDC pipeline; DPO/Legal/DPIA
and EU AI Act decisions; OT vendor/DMZ approval; market-data licensing; DR,
performance, accessibility, and live-cloud fallback rehearsal. Production
capacity is never auto-paused and no cloud action may introduce an OT control
write.

## Known limitations

- No Azure, Fabric, Foundry, Speech, Eventstream, or Power BI tenant resource
  has been deployed from this repository.
- Local adapter responses and capacity actions are deterministic/simulated.
- Full browser click-through automation is not installed; local evidence covers
  served assets, CORS, component tests, and live BFF HTTP assertions.
- The target cloud IaC uses placeholder Container Apps images until approved
  immutable service images are promoted through `cd-services.yml`.
