# azure-validate: Fabric prep gate — `.azure\fabric` / novasteelv3

Status: **PASS** (2 prep-validation issues found and fixed; see "Fixes applied")

Scope: `.azure\fabric\*.ps1` (the isolated `novasteelv3` prep scripts) plus the
parameter/manifest contract they consume under
`fabric\deployment-parameters\novasteelv3.*`. No live Fabric/Azure mutation
endpoint was called at any point — every command below is either a pure
local/offline validator, or an explicit `-DryRun` invocation that the scripts
themselves guarantee makes zero network calls (verified by code review of
`.azure\fabric\New-NovaSteelV3FabricWorkspace.ps1` and
`.azure\fabric\Deploy-NovaSteelV3FabricAssets.ps1`, which both `return` before
any `Get-NsAccessToken`/`Invoke-NsFabricRequest`/`Invoke-NsHttp` call when
`-DryRun` is set).

## 1. Local schema/isolation validator — `Test-NovaSteelV3FabricPrep.ps1`

Command:

```powershell
pwsh -NoProfile -File .\.azure\fabric\Test-NovaSteelV3FabricPrep.ps1 `
  -ParameterFile .\fabric\deployment-parameters\novasteelv3.example.json `
  -ManifestFile .\fabric\deployment-parameters\novasteelv3.items-manifest.json
```

Result: `status: PASS`, exit code `0`, 41 checks, 0 errors, 0 warnings.
Confirms (among others): JSON parse, JSON-Schema conformance (`Test-Json`,
PowerShell 7.6.4), workspace name matches `^NovaSteelV3(-[A-Za-z0-9]+)?$`, no
reserved-prefix collision, `isolation.neverModifyExistingWorkspaces=true`,
`syntheticOnly=true`/`dataClassification=SYNTHETIC`, `region=Sweden Central`,
12 unique item display names with no collision against the existing
`fabric\catalog\fabric-items.json` catalog or `dev/test/demo/prod` example
files, every manifest item's source-definition files exist on disk, every
dependency key resolves, `eventstreamTelemetry` stays excluded/manual, and
`semanticModelBindingValidated` defaults to `false`.

## 2. PowerShell parsing / dry-run workspace creation — `New-NovaSteelV3FabricWorkspace.ps1 -DryRun`

```powershell
pwsh -NoProfile -File .\.azure\fabric\New-NovaSteelV3FabricWorkspace.ps1 `
  -ParameterFile .\fabric\deployment-parameters\novasteelv3.example.json -DryRun
```

Result: `status: DRY_RUN_OK`, exit `0`. Printed the exact planned action
(find-or-create `NovaSteelV3-Demo`, capacity ARM ID, `assignCapacity`,
`createOrBindWorkspace`) with **zero network calls** — all structural guards
(project/region/synthetic/never-modify/sku/name-pattern/reserved-prefix/ARM
resource-ID shape) ran and passed before the script printed the plan and
returned.

## 3. Dry-run asset deployment — `Deploy-NovaSteelV3FabricAssets.ps1 -DryRun`

```powershell
pwsh -NoProfile -File .\.azure\fabric\Deploy-NovaSteelV3FabricAssets.ps1 `
  -ParameterFile .\fabric\deployment-parameters\novasteelv3.example.json `
  -ManifestFile .\fabric\deployment-parameters\novasteelv3.items-manifest.json -DryRun
```

Result: `status: DRY_RUN_OK`, exit `0`. Planned item order for all 12 items;
11 `willDeploy: true` and `semanticOperations` correctly `willDeploy: false`
(`reason: deploySemanticModel=false`), matching the manual Direct-Lake
binding gate that must stay closed until validated.

## 4. Verification / portal-URL generation — `Get-NovaSteelV3FabricVerification.ps1`

Tested in local (non-`-Live`) mode against a synthetic, throw-away
deployment-state fixture (fake GUIDs, deleted after the test — no real state
file exists yet under `.azure\fabric\deployment-state`, which is empty/
`.gitignore`d as expected pre-deployment):

```powershell
pwsh -NoProfile -File .\.azure\fabric\Get-NovaSteelV3FabricVerification.ps1 -StateFile <fixture>
```

Result: `status: PASS`, exit `0`, 3 Fabric portal URLs built (workspace +
2 items) purely from IDs in the state file — confirmed **no network call**
occurs unless `-Live` is passed (code path gated by `if ($Live) { ... }`,
requiring `-ParameterFile` and only ever issuing read-only `GET`s).

## 5. Negative tests (isolation / tenant / subscription / capacity)

Nine mutated copies of `novasteelv3.example.json` were generated in a scratch
folder and run against all three prep scripts, then deleted. Expected
behavior: fail closed **before** any network call.

| Variant | Mutation | `Test-NovaSteelV3FabricPrep.ps1` | `New-...Workspace.ps1 -DryRun` | `Deploy-...Assets.ps1 -DryRun` |
|---|---|---|---|---|
| `reserved-prefix` | `workspace.displayName = "NovaSteel-LegacyClone"` | FAIL (exit 1) | throw (exit 1) | throw (exit 1) |
| `bad-name-pattern` | `workspace.displayName = "NotNovaSteelV3AtAll"` | FAIL (schema, exit 1) | throw (exit 1) | throw (exit 1) |
| `wrong-region` | `region = "West Europe"` | FAIL (exit 1) | throw (exit 1) | throw (exit 1)* |
| `not-synthetic` | `syntheticOnly=false`, `dataClassification="REAL"` | FAIL (schema, exit 1) | throw (exit 1) | throw (exit 1) |
| `modify-existing-allowed` | `isolation.neverModifyExistingWorkspaces = false` | FAIL (schema, exit 1) | throw (exit 1) | throw (exit 1)* |
| `wrong-project` | `project = "novasteel-dev"` | FAIL (schema, exit 1) | throw (exit 1) | throw (exit 1) |
| `bad-sku` | `capacity.sku = "F64"` | FAIL (schema, exit 1) | throw (exit 1) | throw (exit 1)* |
| `bad-arm-resource-id` | `capacity.armResourceId` → a Storage account ID (not `Microsoft.Fabric/capacities`) | PASS (not this script's concern) | throw (exit 1) | PASS (script never uses `armResourceId`) |
| `collision-with-catalog` | an item `displayName` renamed to an existing `fabric\catalog\fabric-items.json` name (`kql-ns-operations`) | FAIL (exit 1) | PASS (workspace-level check only) | PASS (item-naming hygiene, not this script's concern) |

`*` = failure only reproduced **after the fix** in section 6 below; these
three cases initially passed through `Deploy-NovaSteelV3FabricAssets.ps1
-DryRun` (a gap), which is why they are marked as fixed.

The `bad-arm-resource-id` and `collision-with-catalog` "PASS" results in the
scripts marked are correct by design, not gaps:
- `armResourceId` is only ever dereferenced by `New-NovaSteelV3FabricWorkspace.ps1`
  (the only script that calls ARM to confirm the F2 capacity is
  Active/Succeeded); `Deploy-NovaSteelV3FabricAssets.ps1` never reads it, so
  there is nothing to validate there.
- Cross-catalog display-name collisions are a naming-hygiene concern owned by
  `Test-NovaSteelV3FabricPrep.ps1` per the documented order of operations
  (`README.md` §"Local validation" must run before any workspace/deploy
  step); it does not represent an isolation/security gap because every REST
  call in `Deploy-NovaSteelV3FabricAssets.ps1` is scoped to the one
  workspace ID resolved by `New-NovaSteelV3FabricWorkspace.ps1` (re-verified
  live via `Test-WorkspaceNameIsolated` against the actual workspace
  `displayName` before any item write).

### Existing-workspace / non-novasteelv3 protection

Confirmed by code inspection and the `reserved-prefix`/`bad-name-pattern`
tests above that **no script in `.azure\fabric` can create or modify a
workspace/item outside the isolated `novasteelv3` estate**:

- `New-NovaSteelV3FabricWorkspace.ps1` and `Deploy-NovaSteelV3FabricAssets.ps1`
  both call `Test-WorkspaceNameIsolated` against the workspace display name —
  rejecting anything not matching `^NovaSteelV3(-[A-Za-z0-9]+)?$` or starting
  with a reserved prefix (`NS-DEMO-`, `NS-dev-`, `NS-test-`, `NS-prod-`,
  `NovaSteel-`) used by the existing four-workspace estate that backs
  `rg-novasteel-dev`.
- `Deploy-NovaSteelV3FabricAssets.ps1` re-validates the **live** workspace
  `displayName` (fetched by ID) against the same isolation guard immediately
  before any item is created/updated — so even an explicit `-WorkspaceId`
  override cannot be used to target an existing NovaSteel workspace.
- All REST paths are built as `/workspaces/$WorkspaceId/...`, scoped to the
  single resolved workspace; no script enumerates, lists, deletes, or writes
  to any other workspace ID.
- `Test-NovaSteelV3FabricPrep.ps1` additionally checks item display names
  against the existing catalog (`fabric\catalog\fabric-items.json`) and the
  `dev`/`test`/`demo`/`prod` example files, so no automated item name can
  shadow an existing one even before a workspace exists.

### Manual tenant gates are explicit

`fabric\deployment-parameters\novasteelv3.items-manifest.json` →
`manualAssets` explicitly lists 5 human/tenant-bound gates with `reason` and
`completionEvidence`, including `tenantApiPermission` ("A Fabric admin must
permit the deployment identity to create workspaces and use Fabric APIs...
before any script in `.azure/fabric` can run outside `-DryRun`/
`-ValidateOnly`"), plus `rtiDashboard`, `activator`, `powerBiReports`,
`oneLakeSecurity`. `excludedItems` explicitly keeps `eventstreamTelemetry`
out of automation. Previously this was only verified by manual inspection —
**fixed** below by adding an automated regression check.

## 6. Fixes applied (Fabric prep validation issues only)

1. **`.azure\fabric\Deploy-NovaSteelV3FabricAssets.ps1`** — the script's
   always-run structural validation (executed even under `-DryRun`, before
   any network call) was missing three checks present in its sibling
   `New-NovaSteelV3FabricWorkspace.ps1`: `region == 'Sweden Central'`,
   `isolation.neverModifyExistingWorkspaces == true`, and
   `capacity.sku in ('F2','F4')`. A tampered/corrupted parameter file with an
   unapproved region, an explicit permission to modify existing workspaces,
   or an unsupported capacity SKU would previously pass `-DryRun` silently.
   Added the three checks immediately after the existing `project` check
   (mirrors `New-NovaSteelV3FabricWorkspace.ps1` wording exactly). Verified:
   happy-path `-DryRun` still returns `DRY_RUN_OK`; `wrong-region`,
   `modify-existing-allowed`, and `bad-sku` variants now throw before any
   network call (see table above).

2. **`.azure\fabric\Test-NovaSteelV3FabricPrep.ps1`** — added a new
   `manual:tenant-api-permission-gated` check asserting
   `manifest.manualAssets` contains the `tenantApiPermission` key, so a
   future edit that silently drops the required manual tenant-admin gate
   from the manifest fails local validation instead of only being caught by
   manual review. Verified: happy-path run still `PASS`/exit `0` with the new
   check reporting `PASS`; a mutated manifest with `tenantApiPermission`
   removed now fails with exit `1` and
   `manual:tenant-api-permission-gated: FAIL`.

No other files were changed. `fabric/` root assets (`catalog`, `items`,
`notebooks`, `pipelines`, `semantic-model`, `scripts/FabricDeployment.psm1`,
`environment.schema.json`, `dev/test/demo/prod` examples) were read-only
inputs and were not modified, per the isolation contract in
`.azure\fabric\README.md`.

## 7. Full regression after fixes (all commands re-run)

| # | Command | Expected | Result |
|---|---|---|---|
| 1 | `Test-NovaSteelV3FabricPrep.ps1` (happy path) | PASS / exit 0 | PASS / exit 0 |
| 2 | `New-NovaSteelV3FabricWorkspace.ps1 -DryRun` (happy path) | DRY_RUN_OK / exit 0 | DRY_RUN_OK / exit 0 |
| 3 | `Deploy-NovaSteelV3FabricAssets.ps1 -DryRun` (happy path) | DRY_RUN_OK / exit 0 | DRY_RUN_OK / exit 0 |
| 4 | `Get-NovaSteelV3FabricVerification.ps1` (local, synthetic fixture) | PASS / exit 0 | PASS / exit 0 |
| 5 | 8 negative variants × `Test-NovaSteelV3FabricPrep.ps1` | fail except `bad-arm-resource-id` (N/A to this script) | matches |
| 6 | 8 negative variants × `New-NovaSteelV3FabricWorkspace.ps1 -DryRun` | fail except `collision-with-catalog` (N/A to this script) | matches |
| 7 | 8 negative variants × `Deploy-NovaSteelV3FabricAssets.ps1 -DryRun` | fail except `bad-arm-resource-id`/`collision-with-catalog` (N/A to this script) | matches |

All scratch/negative-test parameter files and the synthetic state fixture
used above were temporary, written under `.azure\validation\_tmp*` during
this run, and deleted afterward. No file under `fabric\deployment-parameters`
or `.azure\fabric\deployment-state` was created, modified, or left behind by
this validation pass. No `az`, `fab`, or HTTP call was made at any point.

## 8. Blockers / items still requiring a human before real deployment

None block this validation gate itself (all local/dry-run checks pass), but
per `.azure\fabric\README.md` and the manifest's `manualAssets`, the
following remain explicit, required manual/tenant gates before any script may
run outside `-DryRun`/`-ValidateOnly`:

- `tenantApiPermission` — a Fabric admin must grant the deployment identity
  workspace-creation/API permission and capacity contributor/admin rights on
  the exact `novasteelv3-fabric` capacity resource ID.
- F2 capacity must exist and be confirmed `Active`/`Succeeded` before
  `New-NovaSteelV3FabricWorkspace.ps1` runs for real.
- `oneLakeSecurity`, `rtiDashboard` (Eventstream/KQL dashboard), `activator`,
  `powerBiReports` — all remain manual/portal-only per the manifest.
- `semanticModelBindingValidated` must stay `false` until the Direct Lake
  binding is manually validated (currently enforced and verified `false`).

None of these block marking the `azure-validate-fabric` prep gate itself as
done — they are downstream, execution-time gates that the prep scripts
already correctly refuse to bypass.
