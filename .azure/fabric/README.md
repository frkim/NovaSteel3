# Isolated novasteelv3 Fabric workspace/item binding

This folder is owned by the `azure-fabric-prep` workstream. It prepares — but does
**not execute** — the Fabric REST/CLI automation that binds a single, synthetic-only
`NovaSteelV3-Demo` workspace to the `novasteelv3-fabric` F2 capacity and deploys the
supported Eventhouse/KQL/Lakehouse/notebook/pipeline/semantic-model subset into it.

No Fabric or Azure resource is created by anything in this folder yet. Every script
defaults to a safe, non-mutating mode and requires an explicit switch plus
`-WhatIf`/`ShouldProcess` confirmation before it will call a write API.

## Relationship to `fabric/`

The `fabric/` folder at the repository root owns the pre-existing, four-workspace
(`rtiIngress`, `dataCore`, `ml`, `analytics`) NovaSteel dev/test/demo/prod estate and
its shared `fabric/scripts/FabricDeployment.psm1` HTTP helpers, `fabric/catalog/fabric-items.json`
catalog, and `fabric/deployment-parameters/environment.schema.json` contract. This
folder never edits any of those files. It only:

- imports `fabric/scripts/FabricDeployment.psm1` for the token/HTTP/definition
  helper functions (`Get-NsAccessToken`, `Invoke-NsFabricRequest`, `Find-NsWorkspace`,
  `Find-NsItem`, `ConvertTo-NsFabricDefinition`, `Assert-NsParameterFileHasNoSecrets`), so
  the long-running-operation, retry, and pagination behavior stays identical;
- reads (never writes) the existing source-controlled item definitions under
  `fabric/items/`, `fabric/notebooks/`, `fabric/pipelines/`, `fabric/semantic-model/`;
- reads its own additive parameter/manifest files added under
  `fabric/deployment-parameters/`:
  - `novasteelv3.schema.json` / `novasteelv3.example.json` — single-workspace
    parameter contract (tenant/subscription/capacity/workspace/item ids, retention,
    bindings, deployment options). Distinct file names; nothing in
    `environment.schema.json`, `environment.template.json`, or the `dev`/`test`/`demo`/`prod`
    example files is modified.
  - `novasteelv3.items-manifest.json` / `.schema.json` — the supported item subset
    with unique `novasteelv3`-prefixed display names, plus the excluded items and
    manual/portal gates for this isolated estate.

## Isolation guarantees

- The workspace display name is validated against `^NovaSteelV3(-[A-Za-z0-9]+)?$`
  and rejected if it starts with any reserved prefix used by the existing estate
  (`NS-DEMO-`, `NS-dev-`, `NS-test-`, `NS-prod-`, `NovaSteel-`).
- Every item display name is unique to `novasteelv3` (`evh-novasteelv3-operations`,
  `kql-novasteelv3-operations`, `lh_novasteelv3_landing`, `lh_novasteelv3_core`,
  `v3-initialize-lakehouses`, `v3-bronze-to-silver`, `v3-silver-to-gold`,
  `v3-deterministic-demo-scoring`, `v3-validate-data-quality`,
  `pl-novasteelv3-medallion`, `pl-novasteelv3-demo-scoring`,
  `sm-novasteelv3-operations`) and is checked against the existing catalog's
  default display names by `Test-NovaSteelV3FabricPrep.ps1`.
- Every REST/CLI call is scoped to the single workspace ID resolved for
  `NovaSteelV3-Demo` (or the `-WorkspaceId` supplied explicitly). No script in this
  folder enumerates, deletes, or writes to any other workspace.
- Capacity/workspace/tenant/subscription IDs are always parameters (CLI flags or
  the parameter file) — nothing is hard-coded, and every script fails closed on a
  placeholder GUID (`00000000-0000-0000-0000-000000000000`) or a `<...>` token
  outside of `-DryRun`/`-ValidateOnly`.
- Eventstream, RTI dashboard, Activator, Power BI reports, and OneLake security
  roles are **not** automated for `novasteelv3`; they are recorded as manual gates
  (see `novasteelv3.items-manifest.json` → `excludedItems` / `manualAssets`).

## Local validation (no tenant/Azure access, safe to run anytime)

```powershell
pwsh -File .\.azure\fabric\Test-NovaSteelV3FabricPrep.ps1 `
  -ParameterFile .\fabric\deployment-parameters\novasteelv3.example.json `
  -ManifestFile .\fabric\deployment-parameters\novasteelv3.items-manifest.json
```

This performs schema/name/uniqueness/dependency/source-file checks only. It never
calls `az`, `fab`, or any HTTP endpoint.

## Order of operations once the F2 capacity exists (not run yet)

1. Copy the example parameter file and fill in the real tenant/subscription/capacity
   IDs (never a secret):

   ```powershell
   Copy-Item .\fabric\deployment-parameters\novasteelv3.example.json `
     .\fabric\deployment-parameters\novasteelv3.parameters.json
   ```

2. Dry-run the workspace binding (no network calls, prints intended actions only):

   ```powershell
   pwsh -File .\.azure\fabric\New-NovaSteelV3FabricWorkspace.ps1 `
     -ParameterFile .\fabric\deployment-parameters\novasteelv3.parameters.json `
     -DryRun
   ```

3. After the F2 capacity is confirmed `Active`/`Succeeded` and the tenant gate in
   `novasteelv3.items-manifest.json` → `manualAssets.tenantApiPermission` is
   granted, bind/create the workspace for real:

   ```powershell
   az login
   pwsh -File .\.azure\fabric\New-NovaSteelV3FabricWorkspace.ps1 `
     -ParameterFile .\fabric\deployment-parameters\novasteelv3.parameters.json `
     -WhatIf   # remove -WhatIf only after review
   ```

4. Deploy the supported item subset into the bound workspace:

   ```powershell
   pwsh -File .\.azure\fabric\Deploy-NovaSteelV3FabricAssets.ps1 `
     -ParameterFile .\fabric\deployment-parameters\novasteelv3.parameters.json `
     -ManifestFile .\fabric\deployment-parameters\novasteelv3.items-manifest.json `
     -WhatIf   # remove -WhatIf only after review
   ```

5. Verify and print portal URLs without mutating anything:

   ```powershell
   pwsh -File .\.azure\fabric\Get-NovaSteelV3FabricVerification.ps1 `
     -StateFile .\.azure\fabric\deployment-state\novasteelv3.json
   ```

   Add `-Live` to re-check existence/capacity assignment through read-only Fabric
   GET calls before trusting the state file.

Capacity `Resume`/`Suspend`/`Status` lifecycle actions remain owned exclusively by
`fabric/scripts/Invoke-FabricCapacityLifecycle.ps1`; nothing in this folder starts,
pauses, or resizes any capacity.

## Manual/portal-only gates

See `fabric/deployment-parameters/novasteelv3.items-manifest.json` →
`excludedItems` and `manualAssets` for the authoritative, structured list. In
summary, a human must still:

- grant the deployment identity Fabric API/workspace-creation permission and
  capacity contributor/admin rights on the exact `novasteelv3-fabric`
  resource ID;
- confirm the F2 capacity is created and running before step 3 above runs outside
  `-DryRun`;
- retrieve the Eventstream Custom Endpoint connection details and prove the
  managed-identity publisher path (out of scope for automation here);
- validate the Direct Lake semantic model binding and RLS before flipping
  `deploySemanticModel`/`semanticModelBindingValidated` to `true`;
- apply/verify OneLake security roles and sensitivity labels;
- import a tenant-exported KQL dashboard, Activator rules, and Power BI reports
  once their tenant-bound definitions are proven.
