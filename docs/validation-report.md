# NovaSteel validation report

> **Validated:** 2026-07-25  
> **Scope:** documentation, runnable local demonstration, source contracts,
> simulator, application, IaC, Fabric assets, presentation, and supply-chain
> gates.  
> **Deployment status:** deployed live to Azure Sweden Central (resource group
> `rg-novasteelv3-demo-sc`); passes 66/66 automated live API checks. Offline
> deterministic path retained as fallback. Production tenant hardening (real
> plant data, DPO sign-off, security review) is not yet complete.

## Result summary

| Check | Result | Evidence |
|---|---|---|
| Protected Python/NuGet feed enforcement | **PASS** | `pip.conf` has the protected Python index; `NuGet.Config` clears inherited sources; executable/configuration scan reports no prohibited endpoint. |
| Contracts and deterministic simulator | **PASS** | Contract, simulator, physics, scenario, checksum, and schema tests run through `Validate-Repository.ps1`. |
| BFF and integration behavior | **PASS** | Local FastAPI tests and the 66/66 real-HTTP scripted demo checks pass against `NS-DEMO-LUX-01`. |
| Knowledge workflow | **PASS** | Consent, grounded draft/review/approval, prompt-defense, and local adapter tests pass. |
| UI and portal | **PASS** | Frontend lint, component tests, build, protected Blazor restore/build, served-asset probes, and portal-origin CORS preflight pass. |
| IaC and Fabric assets | **PASS (local/static)** | Bicep/policy tests and static validation pass; Fabric asset validator parses definitions, contracts, KQL, notebooks, pipelines, semantic metadata, and lifecycle deny rules. |
| Offline fallback | **PASS** | 12/12 checks prove fixture, cached, and built-in fallback levels plus no non-loopback network activity. |
| Presentation | **PASS** | `NovaSteel-Oral-Defense.pptx` contains 28 slides with no placeholders and matches the six demo transitions. |
| Security/SBOM | **PASS** | Repository security checks, Python dependency integrity, protected-feed scan, and CycloneDX SBOM generation pass. |

The current machine-readable result and per-suite logs are under
[`artifacts\validation\final`](../artifacts/validation/final/). Run the
following command to refresh them locally without deploying any cloud resource:

```powershell
pwsh .\tools\validation\Validate-Repository.ps1 `
    -EvidencePath .\artifacts\validation\final\evidence-manifest.json
```

## Demonstration evidence

The local deterministic rehearsal uses seed `240725`, the committed
`demo-full` fixture, `DEMO_MODE=local`, and a loopback-only BFF. Its evidence is
under [`artifacts\demo-validation`](../artifacts/demo-validation/):

| Evidence | Verified result |
|---|---|
| Persona/demo driver | 66/66 checks passed across DM-1…DM-6, telemetry, tables, authorization, audit, and simulated capacity lifecycle |
| Furnace RUL | P10/P50/P90 = 18.69/19.65/20.61 days; risk 0.8995 HIGH; confidence 0.78; synthetic work order `WO-DEMO-LUX-1042` |
| Energy | 280 EUR/MWh peak; 960 = 960 tonnes; zero hard violations; 7.25% modeled cost reduction; 3.29% CO₂; 7.89% peak (56.0→51.58 MW) |
| Quality | Full genealogy and bounded prediction 88% → 95%; no operational write |
| Knowledge | Consent, transcript confidence/speaker data, draft-only agent output, human approval, approved-search result |
| Determinism | Two independent generations and BFF re-runs matched; fixture checksum/tamper protection passed |
| Fallback | 12/12 checks; local/cached/built-in data levels work with non-loopback sockets blocked |
| Defense deck | 28 slides, 799 text runs, zero placeholder/TODO findings |

These are **synthetic demonstration results**, not realized production savings,
model accuracy, OT integration, or cloud-service evidence. The 14% energy, 22%
CO₂, 21-day warning, and 8% yield figures remain pilot targets.

## Documentation reconciliation completed

- Documentation now states the implemented local application, simulator, IaC,
  Fabric asset, CI, presentation, and evidence status rather than retaining its
  former design-only wording.
- The presentation plan now references the delivered PowerPoint instead of
  instructing readers to create it.
- Local setup examples use the actual Windows paths, protected feeds, BFF
  command, fixture location, simulator CLI, and `lu` scenario route.
- Old hash-required installation examples were corrected because the committed
  requirements files are exact-version pins but do not include hash entries.
- The default portal route now aligns with the implemented `NS-DEMO-LUX-01`
  scenario rather than opening a different country label.

## Remaining cloud-only production gates

The following are intentionally open; none can be inferred from local success:

1. Provision and measure target-tenant Fabric capacity/SKU/quota in Sweden
   Central (with reviewed West Europe contingency where applicable).
2. Prove Eventstream Custom Endpoint managed-identity publishing, isolation,
   tenant switches, and allowed network route.
3. Validate Foundry model/deployment/Agent Service tool set/quota, live Speech,
   private networking, and evaluation policy in the target tenant.
4. Validate Fabric query-adapter, Entra, workspace, OneLake, Power BI, and
   item-level/RLS authorization.
5. Obtain DPO/Legal decisions for lawful basis, DPIA, retention/deletion,
   residency, recovery copies, and EU AI Act classification.
6. Obtain OT vendor/site approval for DMZ protocol, source, rate, ownership,
   and operational-boundary controls.
7. Validate market-data licensing/freshness, immutable image promotion,
   capacity/DR/performance/accessibility, and the live-cloud fallback level.

## Completion statement

The local implementation and oral-defense handoff are integrated and
reproducibly validated. They are ready for an offline/local rehearsal, while
cloud production deployment remains gated by the tenant, security, governance,
OT, and operational proof listed above.
