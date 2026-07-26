# NovaSteel final handoff

> **Status:** **GO for the local deterministic oral-defense rehearsal.**  
> **Cloud status:** no Azure/Fabric/Foundry/Speech tenant resource has been
> deployed; cloud production remains gated.

## Delivered implementation

- Blazor WebAssembly shell and React/MUI/D3 persona dashboard, with the
  scenario-aligned default route `http://localhost:5266/lu/command-center`.
- FastAPI BFF with local-only `NS-DEMO-LUX-01` scope, role/plant checks,
  telemetry, RUL, energy, quality, sustainability, knowledge, audit, SSE/poll,
  and simulated non-production capacity lifecycle.
- Deterministic Python simulator, committed checksummed `demo-full` fixture,
  scoring/optimizer, consent-bound knowledge draft/review/approval workflow,
  and local offline fallback.
- Source-controlled Bicep/policy/OIDC deployment assets and Fabric catalog,
  KQL, Lakehouse, notebook, pipeline, semantic-model, RTI, and capacity assets.
- GitHub Actions supply-chain/security/CI/CD workflows, locally executable
  validation, CycloneDX SBOM, and the 26-slide defense deck.

## Final local evidence

| Proof | Result |
|---|---|
| Repository validation | `Validate-Repository.ps1` passes protected feeds, contracts, simulator, backend/integration, knowledge, frontend, portal, IaC, Fabric, presentation, security, and SBOM suites. |
| Protected Python/NuGet sources | 345 executable/configuration files scanned; 0 prohibited endpoint violations. `NuGet.Config` clears inherited sources; `pip.conf` supplies the sole Python index. |
| Windows script safety | All 11 checked PowerShell scripts parse successfully; local validation uses PowerShell 7. |
| Portal/BFF smoke | BFF `/health/ready`, portal `/lu/command-center`, and portal-origin CORS preflight all passed; listeners were stopped and ports 8080/5266 confirmed free afterward. |
| Six-moment HTTP demo | **66/66** checks passed in **0.31 s** aggregate handler time. |
| Furnace evidence | P10/P50/P90 **16.8/21.0/27.5 days**, risk **0.87 HIGH**, synthetic work order `WO-DEMO-LUX-1042`. |
| Energy evidence | **280 EUR/MWh** peak, **960 = 960 tonnes**, **0** hard violations, **9.94%** modeled cost reduction. |
| Quality evidence | Full genealogy; bounded synthetic what-if **88% → 95%** with no operational write. |
| Knowledge/audit evidence | Consent, transcript, DRAFT-only agent result, human approval/search, and append-only decision evidence passed. |
| Offline fallback | **12/12** checks pass with non-loopback connections blocked. |
| Presentation | `docs\presentation\NovaSteel-Oral-Defense.pptx`: **26 slides**, no placeholders, aligned to all demo transitions. |
| Fabric/IaC local checks | Fabric validator: **325** checks, 0 errors/warnings. Bicep: **14** modules build cleanly; ARM tenant validation remains intentionally unrun. |

The current machine-readable evidence and logs are in
`artifacts\validation\final\`; the live demo trace is
`artifacts\demo-validation\logs\final-integration-demo.log`.

## Exact defense assets

| Asset | Location |
|---|---|
| Definitive quick start / commands | `README.md` |
| Slide deck | `docs\presentation\NovaSteel-Oral-Defense.pptx` |
| 30-minute speaker plan | `docs\presentation\oral-defense-and-slide-plan.md` |
| 15-minute persona runbook | `docs\demo\demo-runbook.md` |
| 15-minute FAQ | `docs\presentation\faq.md` |
| Rehearsal report | `artifacts\demo-validation\rehearsal-report.md` |
| Scripted API driver | `artifacts\demo-validation\drive_demo.py` |
| Fallback validator | `artifacts\demo-validation\verify_fallback.py` |
| Final validation manifest | `artifacts\validation\final\evidence-manifest.json` |

The clock is fixed: **30 minutes slides + 15 minutes deterministic demo + 15
minutes FAQ**. Every live value must be described as synthetic evidence; the
14% energy, 22% CO₂, 21-day warning, and 8% yield figures are pilot targets,
not realized production results.

## Operating and security boundary

- Use only the protected Python and NuGet feeds; no public fallback or extra
  Python index is permitted.
- The demo binds locally, accepts only `NS-DEMO-*` scope, and never exposes a
  workload token to the microfrontend.
- No component writes to PLCs, interlocks, furnaces, recipes, setpoints, real
  schedules, CMMS, or production capacity.
- The local capacity panel and BFF mutations are simulated; a BFF restart resets
  rehearsal state. Do not treat a successful local action as a cloud action.

## Cloud production gates

1. Confirm target-tenant Sweden Central Fabric capacity/SKU/quota and measured
   F2/F4 sizing.
2. Prove Eventstream Custom Endpoint managed-identity publishing, isolated
   Contributor scope, tenant settings, and permitted network route.
3. Validate Foundry Agent Service/model/deployment/quota, live Speech, safety
   evaluation, and private-network behavior.
4. Prove Entra/Fabric workspace/OneLake/item-level/Power BI authorization and
   RLS with the target tenant.
5. Obtain DPO/Legal/DPIA, retention/deletion, residency, recovery-copy, and EU
   AI Act decisions before non-synthetic data.
6. Obtain OT vendor/site and market-data licensing approval; complete immutable
   image promotion, DR/performance/accessibility, and live-cloud fallback tests.

## Known non-cloud blockers/limitations

- Npm vulnerability audit requires the organization-approved protected npm
  registry and is skipped when that registry is not configured; it has no public
  fallback.
- Full browser click-through automation is not installed. The handoff instead
  includes component tests, served-asset/CORS checks, and live BFF HTTP proof.
- IaC contains placeholder Container Apps images until approved immutable service
  images are promoted through `cd-services.yml`.
