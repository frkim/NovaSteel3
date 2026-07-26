# NovaSteel v3 — Azure IaC validation proof

> **Scope:** `azure-validate-iac` — `.azure\infra` and `.azure\scripts`.
> **Result:** **PASS** — validated 2026-07-25T10:40+02:00.
> **Safety:** no Azure resource was deployed, changed, or deleted.

## Commands and results

### Local Bicep and PowerShell checks

```powershell
Get-ChildItem .\.azure\infra -Recurse -File -Filter *.bicep |
  Sort-Object FullName | ForEach-Object {
    az bicep build --file $_.FullName --stdout
    az bicep lint --file $_.FullName
  }
az bicep build-params --file .\.azure\infra\main.bicepparam --stdout

Get-ChildItem .\.azure\scripts -Recurse -File -Filter *.ps1 |
  ForEach-Object {
    $tokens = $null; $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
      $_.FullName, [ref]$tokens, [ref]$errors)
    if ($errors.Count) { throw "$($_.FullName): $($errors.Message -join '; ')" }
  }
```

Result: Bicep 0.43.8 built and linted `main.bicep`, `apps.bicep`,
`platform.bicep`, and `budget.bicep` with no diagnostics; `main.bicepparam`
built successfully. All six deployment/image PowerShell scripts parsed cleanly.

### Explicit-subscription validate and what-if

The helper compiles the Bicep parameter file into a typed, temporary JSON
parameter document in `.azure\infra`, preserves arrays/booleans, and deletes it
in `finally`. Its defaults are reserved, non-routable immutable image digests:

```text
placeholder.invalid/novasteelv3/portal@sha256:0000000000000000000000000000000000000000000000000000000000000000
placeholder.invalid/novasteelv3/bff@sha256:1111111111111111111111111111111111111111111111111111111111111111
```

```powershell
. .\.azure\scripts\Common.ps1
$parameterFile = New-NovaSteelDemoParameterFile -Overrides @{ deployApps = $false }
try {
  az deployment sub validate `
    --subscription 3377065c-bf76-4767-a982-32bce4ffb592 `
    --name novasteelv3-iac-whatif-bootstrap-final-validate-rerun `
    --location swedencentral `
    --template-file .\.azure\infra\main.bicep `
    --parameters $parameterFile --only-show-errors
  az deployment sub what-if `
    --subscription 3377065c-bf76-4767-a982-32bce4ffb592 `
    --name novasteelv3-iac-whatif-bootstrap-final-rerun `
    --location swedencentral `
    --template-file .\.azure\infra\main.bicep `
    --parameters $parameterFile `
    --result-format FullResourcePayloads --no-pretty-print --only-show-errors
} finally { Remove-Item $parameterFile -Force -ErrorAction SilentlyContinue }
```

Bootstrap result: `validate` **PASS**; what-if **Create=22, Modify=0,
Delete=0**; all reported `location` values were `swedencentral`.

The same commands were run with `@{ deployApps = $true }` and names
`novasteelv3-iac-whatif-full-final-validate-rerun` /
`novasteelv3-iac-whatif-full-final-rerun`.

Full result: `validate` **PASS**; what-if **Create=24, Modify=0, Delete=0**;
all locations `swedencentral`. The additional creates were exactly
`Microsoft.App/containerApps/novasteelv3-portal` and
`Microsoft.App/containerApps/novasteelv3-bff`.

The packaged repeatable command was also exercised:

```powershell
pwsh .\.azure\scripts\Invoke-NovaSteelDemoWhatIf.ps1 `
  -DeploymentName novasteelv3-iac-script-bootstrap-final
pwsh .\.azure\scripts\Invoke-NovaSteelDemoWhatIf.ps1 -DeployApps `
  -DeploymentName novasteelv3-iac-script-full-final
```

Results: bootstrap **22 Create / 0 Modify / 0 Delete**; full **24 Create /
0 Modify / 0 Delete**, with both Container Apps and only Sweden Central.
Neither command deploys resources. `az group exists --subscription
3377065c-bf76-4767-a982-32bce4ffb592 --name rg-novasteelv3-demo-sc` returned
`false`, so the previews cannot alter an existing target estate.

### Subscription, policy, provider, location, and name checks

All commands used subscription `3377065c-bf76-4767-a982-32bce4ffb592`.

| Check | Exact command / result |
|---|---|
| Target context | `az account show --subscription 3377065c-bf76-4767-a982-32bce4ffb592` → enabled **Contoso Fx**, tenant `9d94eb6e-d45e-4f05-bc1b-d0bbd2421561`. |
| Providers | `az provider show --namespace <provider> --subscription 3377065c-bf76-4767-a982-32bce4ffb592 --query registrationState -o tsv` → **Registered** for all 14 referenced providers, including App, Fabric, ContainerRegistry, KeyVault, EventHub, Logic, CognitiveServices, and Consumption. |
| Subscription location | `az rest --method get --url https://management.azure.com/subscriptions/3377065c-bf76-4767-a982-32bce4ffb592/locations?api-version=2022-12-01 --query "value[?name=='swedencentral'].name \| [0]" -o tsv` → `swedencentral`. |
| Service locations | `az provider show ... --query "resourceTypes[?resourceType=='<type>'].locations[]"` confirmed Sweden Central for `Microsoft.App/managedEnvironments`, `Microsoft.App/containerApps`, `Microsoft.Fabric/capacities`, `Microsoft.CognitiveServices/accounts`, `Microsoft.EventHub/namespaces`, and `Microsoft.Logic/workflows`. |
| Enforced policy | `az policy assignment list --scope /subscriptions/3377065c-bf76-4767-a982-32bce4ffb592 --disable-scope-strict-match` → `novasteel-eu-rg-locations` and `novasteel-eu-locations`, both `enforcementMode=Default`; each allows Sweden Central, West Europe, Germany West Central, and France Central. |
| Names | `az acr check-name`, `az storage account check-name`, and `az eventhubs namespace exists` returned available for `novasteelv3acrnofkol6a`, `novasteelv3stnofkol6a`, and `novasteelv3-eh-nofkol6a`. `POST .../Microsoft.KeyVault/checkNameAvailability?api-version=2023-07-01` with `{"name":"novasteelv3-kv-nofkol6a","type":"Microsoft.KeyVault/vaults"}` returned `nameAvailable=true`. |

The Bicep root permits only `swedencentral`; every taggable resource passes that
parameter as its location. Combined with the two what-if payload scans, no
target uses a non-EU location.

### Static RBAC review

Read-only role definition lookup used:

```powershell
az role definition list --subscription 3377065c-bf76-4767-a982-32bce4ffb592 `
  --name <role-definition-guid> --query '[0].{id:name,name:roleName}' -o tsv
```

| Principal / operation | Role and smallest scope | Result |
|---|---|---|
| Portal identity registry pull | `AcrPull` on the new ACR | PASS |
| BFF identity registry pull | `AcrPull` on the new ACR | PASS |
| BFF artifacts | `Storage Blob Data Contributor` on `demo-artifacts`, not the storage account | PASS |
| BFF secrets | `Key Vault Secrets User` on the demo Key Vault | PASS |
| BFF telemetry | `Azure Event Hubs Data Sender` on the `telemetry` hub | PASS |
| Optional AI/Speech | `Cognitive Services User` / `Cognitive Services Speech User`, each on its individual account | PASS |
| Nightly Fabric pause | System-assigned Logic App identity; custom role scoped to the one Fabric capacity and granting only `Microsoft.Fabric/capacities/suspend/action` | PASS |

No `Owner`, generic `Contributor`, or generic `Reader` role assignment ID is
present. The custom Fabric role is assignable only within
`rg-novasteelv3-demo-sc`; its assignment scope is the capacity itself.

## Fixes applied during validation

1. Removed Bicep lint findings by declaring module name-input minimum lengths
   and using null-safe optional AI/Speech endpoint access.
2. Replaced mutable placeholder tags with reserved `placeholder.invalid`
   SHA-256 digest references.
3. Made deployment/what-if parameter overrides typed and reliable by compiling
   `main.bicepparam` to an ephemeral JSON parameter document; cleanup is
   guaranteed in `finally`.
4. Removed runtime platform-output references from the conditional apps module.
   It now derives deterministic resource names/IDs and explicitly depends on the
   platform module, allowing full what-if expansion to show both Container Apps.
5. Narrowed RBAC: the Fabric Logic App role is suspend-only, and BFF blob access
   is scoped to the artifacts container.

## Blockers

None. Azure deployment was intentionally not invoked.
