# NovaSteel Microsoft Fabric assets

This folder contains the source-controlled Microsoft Fabric data-plane assets for
NovaSteel. The default configuration is synthetic-only and follows the
architecture in `docs/architecture/solution-architecture.md`.

For a mapping of these assets to Fabric-Brain agents and a three-phase
deployment sequence, see
[`docs/architecture/fabric-brain-mapping.md`](../docs/architecture/fabric-brain-mapping.md).

## Supported deployment boundary

| Asset | Automation in this repository | Required tenant/manual gate |
|---|---|---|
| Workspaces and capacity assignment | Idempotent Fabric REST deployment | Fabric admin must permit the deployment identity to create workspaces and use Fabric APIs; the identity must be a capacity contributor/admin. |
| Eventhouse, read/write KQL database, Lakehouses | Fabric REST create/update; KQL database definition contains tables, mappings, functions, policies, and materialized views | Capacity must be running and the target region/SKU must support the item. |
| Eventstream Custom Endpoint and destinations | Fabric REST definition deployment | Validate tenant settings, obtain the generated Custom Endpoint connection details, and prove the managed-identity publisher path. The publisher receives Contributor only on the isolated RTI-Ingress workspace. |
| Notebooks and Data Pipelines | Fabric REST definition deployment; Fabric CLI import is available after workspace bootstrap | Attach/authorize the Lakehouses, bind tenant connection IDs, and test notebook/pipeline job identities. |
| Direct Lake semantic model | TMDL metadata and DAX measures are source controlled; REST/CLI deployment is disabled until the environment gate is set | Create/validate the tenant-specific Direct Lake binding, RLS identity mapping, labels, and refresh/query behavior before enabling deployment. |
| RTI dashboard, Activator, Power BI reports | Query packs, rule specifications, theme, and report metadata are source controlled | Build or import a tenant-exported definition in the portal, bind notification/report identities, validate DLP/licensing, and check accessibility/RLS. |
| OneLake security roles and sensitivity labels | Desired state is catalogued and tenant validation reports omissions | A data/platform administrator applies and verifies current tenant-supported role/label APIs or the portal Secure tab. |

**Bicep boundary:** Bicep can deploy the Azure
`Microsoft.Fabric/capacities` resource and other Azure control-plane
dependencies. It does **not** deploy Fabric SaaS workspaces, Eventstreams,
Eventhouses/KQL databases, Lakehouses, notebooks, pipelines, semantic models,
RTI dashboards, Activator rules, or Power BI reports. Those items use Fabric
REST, Fabric CLI/Git integration, or an explicit portal gate.

## Layout

- `catalog/` — item inventory, dependencies, automation tier, and manual gates.
- `deployment-parameters/` — no-secret environment templates.
- `items/` — Eventhouse, KQL database, Lakehouse, and Eventstream definitions.
- `kql/` — operational query and smoke-test packs.
- `lakehouse/` — medallion table contracts, Spark SQL DDL, and data-quality rules.
- `notebooks/` — Fabric Git source notebooks for initialization, transforms,
  validation, and deterministic synthetic scoring.
- `pipelines/` — Fabric Data Pipeline definitions and connection templates.
- `semantic-model/` — TMDL metadata plus authoritative DAX KPI measures.
- `rti/` and `powerbi/` — portal/import-ready setup specifications.
- `capacity/` — lifecycle and Logic App contracts.
- `scripts/` — secretless REST/CLI deployment and validation.

## Local validation (no tenant access)

```powershell
pwsh -File .\fabric\scripts\Test-FabricAssetsLocal.ps1
```

The validator parses JSON, PowerShell, Python notebook source, item catalogs,
KQL required objects, medallion contracts, pipeline dependencies, KPI coverage,
and the production lifecycle hard deny. It does not contact Azure or Fabric.

## Tenant deployment

1. Copy an environment example and replace placeholder identifiers. Never add a
   password, client secret, SAS token, connection string, or access key.

   ```powershell
   Copy-Item .\fabric\deployment-parameters\demo.example.json `
     .\fabric\deployment-parameters\demo.parameters.json
   ```
2. Authenticate the Azure CLI as a user or managed identity:

   ```powershell
   az login
   # On a supported Azure host instead:
   az login --identity
   ```

3. Validate the plan, then deploy the REST-supported items:

   ```powershell
   pwsh -File .\fabric\scripts\Deploy-FabricAssets.ps1 `
     -ParameterFile .\fabric\deployment-parameters\demo.parameters.json
   ```

4. Optionally update definition-capable items through Fabric CLI after the REST
   bootstrap has produced a deployment-state file:

   ```powershell
   fab auth login --identity
   pwsh -File .\fabric\scripts\Deploy-FabricDefinitionsWithCli.ps1 `
     -ParameterFile .\fabric\deployment-parameters\demo.parameters.json `
     -StateFile .\fabric\deployment-state\demo.json
   ```

5. Run tenant validation and complete every reported manual gate:

   ```powershell
   pwsh -File .\fabric\scripts\Test-FabricDeployment.ps1 `
     -ParameterFile .\fabric\deployment-parameters\demo.parameters.json `
     -StateFile .\fabric\deployment-state\demo.json -Deep
   ```

The scripts acquire tokens from the current Azure CLI context. Managed-identity
login is opt-in and no script accepts a client secret.

## Safety and operating rules

- `demo` accepts only `SYNTHETIC` / `DEMO-NONPERSONAL` data and `NS-DEMO-*`
  namespaces.
- Quarantined records remain queryable; transforms never silently repair or
  delete them.
- Fabric alerts and Activator actions are notifications/enrichment only, never
  PLC, safety, setpoint, schedule-commit, or capacity-control actions.
- Capacity automation is allow-listed to `dev`, `test`, and `demo`. `prod` is a
  hard deny in both the parameter contract and lifecycle script.
- A `202 Accepted` Fabric or ARM response is never treated as completion; the
  scripts poll the documented long-running operation.

## Current official interfaces used

- Fabric Core/item REST API: `https://api.fabric.microsoft.com/v1`
- Fabric CLI (`fab`): managed identity is supported by
  `fab auth login --identity`.
- Capacity ARM API: `2023-11-01` for read/resume/suspend.

Recheck item-specific identity support and definition formats immediately before
a major release because Fabric item support evolves independently of ARM/Bicep.
