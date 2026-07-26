<#
.SYNOPSIS
    Offline validation of the isolated novasteelv3 Fabric parameter file and
    item manifest. Makes no az/fab/HTTP call and requires no credentials.

.DESCRIPTION
    Validates JSON syntax and (when Test-Json is available) schema conformance,
    confirms the workspace/item naming isolation guarantees, confirms every
    manifest item's source definition files exist on disk, confirms dependency
    keys resolve, and confirms the excluded Eventstream item and manual assets
    remain out of the automated deployment path.

.PARAMETER ParameterFile
    Path to the novasteelv3 parameter file (defaults to the checked-in example).

.PARAMETER ManifestFile
    Path to the novasteelv3 items manifest (defaults to the checked-in file).
#>
[CmdletBinding()]
param(
    [string]$ParameterFile = '',
    [string]$ManifestFile = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$azureFabricRoot = $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $azureFabricRoot)
$fabricRoot = Join-Path $repoRoot 'fabric'
$deploymentParametersRoot = Join-Path $fabricRoot 'deployment-parameters'

if (-not $ParameterFile) {
    $ParameterFile = Join-Path $deploymentParametersRoot 'novasteelv3.example.json'
}
if (-not $ManifestFile) {
    $ManifestFile = Join-Path $deploymentParametersRoot 'novasteelv3.items-manifest.json'
}
foreach ($pathVariable in @('ParameterFile', 'ManifestFile')) {
    $value = Get-Variable -Name $pathVariable -ValueOnly
    if (-not [IO.Path]::IsPathRooted($value)) {
        Set-Variable -Name $pathVariable -Value (Join-Path (Get-Location) $value)
    }
}

$errors = [System.Collections.Generic.List[string]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()
$checks = [System.Collections.Generic.List[object]]::new()

function Add-Result {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][bool]$Passed,
        [Parameter(Mandatory)][string]$Detail,
        [switch]$Warning
    )
    $status = if ($Passed) { 'PASS' } elseif ($Warning) { 'WARN' } else { 'FAIL' }
    $checks.Add([pscustomobject]@{ name = $Name; status = $status; detail = $Detail })
    if (-not $Passed) {
        if ($Warning) { $warnings.Add("$Name - $Detail") }
        else { $errors.Add("$Name - $Detail") }
    }
}

function Read-JsonFile {
    param([Parameter(Mandatory)][string]$Path)
    try {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100
    }
    catch {
        Add-Result -Name "json-parse:$Path" -Passed $false -Detail $_.Exception.Message
        return $null
    }
}

if (-not (Test-Path -LiteralPath $ParameterFile -PathType Leaf)) {
    throw "Parameter file not found: $ParameterFile"
}
if (-not (Test-Path -LiteralPath $ManifestFile -PathType Leaf)) {
    throw "Manifest file not found: $ManifestFile"
}

Add-Result -Name 'json-parse:parameters' -Passed $true -Detail $ParameterFile
$parameters = Read-JsonFile -Path $ParameterFile
Add-Result -Name 'json-parse:manifest' -Passed $true -Detail $ManifestFile
$manifest = Read-JsonFile -Path $ManifestFile

if ($null -eq $parameters -or $null -eq $manifest) {
    $result = [pscustomobject]@{
        status = 'FAIL'
        checks = $checks.ToArray()
        errors = $errors.ToArray()
    }
    $result | ConvertTo-Json -Depth 20
    throw "novasteelv3 local validation failed with $($errors.Count) error(s)."
}

if (Get-Command Test-Json -ErrorAction SilentlyContinue) {
    $parameterSchema = Join-Path $deploymentParametersRoot 'novasteelv3.schema.json'
    $manifestSchema = Join-Path $deploymentParametersRoot 'novasteelv3.items-manifest.schema.json'
    $parametersValid = Get-Content -LiteralPath $ParameterFile -Raw -Encoding UTF8 |
        Test-Json -SchemaFile $parameterSchema -ErrorAction SilentlyContinue
    Add-Result -Name 'json-schema:parameters' -Passed $parametersValid -Detail "Schema: $parameterSchema"
    $manifestValid = Get-Content -LiteralPath $ManifestFile -Raw -Encoding UTF8 |
        Test-Json -SchemaFile $manifestSchema -ErrorAction SilentlyContinue
    Add-Result -Name 'json-schema:manifest' -Passed $manifestValid -Detail "Schema: $manifestSchema"
}
else {
    Add-Result -Name 'json-schema' -Passed $false -Warning `
        -Detail 'Test-Json cmdlet unavailable in this PowerShell edition; schema conformance was not checked.'
}

# --- Isolation guarantees ------------------------------------------------------------------
$workspaceDisplayName = [string]$parameters.workspace.displayName
$pattern = [string]$parameters.isolation.workspaceNamePattern
Add-Result -Name 'isolation:workspace-name-pattern' `
    -Passed ($workspaceDisplayName -match $pattern) `
    -Detail "'$workspaceDisplayName' against pattern '$pattern'"

$reservedHit = $null
foreach ($reserved in @($parameters.isolation.reservedNamePrefixes)) {
    if ($workspaceDisplayName.StartsWith([string]$reserved, [StringComparison]::OrdinalIgnoreCase)) {
        $reservedHit = $reserved
        break
    }
}
Add-Result -Name 'isolation:workspace-name-not-reserved' `
    -Passed ($null -eq $reservedHit) `
    -Detail $(if ($reservedHit) { "Starts with reserved prefix '$reservedHit'" } else { 'No reserved prefix collision.' })

Add-Result -Name 'isolation:never-modify-existing' `
    -Passed ([bool]$parameters.isolation.neverModifyExistingWorkspaces) `
    -Detail 'isolation.neverModifyExistingWorkspaces must be true.'

Add-Result -Name 'isolation:synthetic-only' `
    -Passed ([bool]$parameters.syntheticOnly -and [string]$parameters.dataClassification -eq 'SYNTHETIC') `
    -Detail "syntheticOnly=$($parameters.syntheticOnly), dataClassification=$($parameters.dataClassification)"

Add-Result -Name 'isolation:region' `
    -Passed ([string]$parameters.region -eq 'Sweden Central') `
    -Detail "region=$($parameters.region)"

# --- Item display-name uniqueness, including cross-catalog collisions ---------------------
$configuredDisplayNames = @()
foreach ($itemProperty in $parameters.items.PSObject.Properties) {
    $configuredDisplayNames += [string]$itemProperty.Value.displayName
}
$duplicates = @($configuredDisplayNames | Group-Object | Where-Object { $_.Count -gt 1 } | ForEach-Object { $_.Name })
Add-Result -Name 'items:unique-within-parameters' `
    -Passed ($duplicates.Count -eq 0) `
    -Detail $(if ($duplicates.Count -gt 0) { "Duplicates: $($duplicates -join ', ')" } else { "$($configuredDisplayNames.Count) item display names are unique." })

$mainCatalogPath = Join-Path $fabricRoot 'catalog\fabric-items.json'
$mainCatalogDisplayNames = @()
if (Test-Path -LiteralPath $mainCatalogPath -PathType Leaf) {
    $mainCatalog = Read-JsonFile -Path $mainCatalogPath
    if ($mainCatalog) {
        $mainCatalogDisplayNames = @($mainCatalog.items | ForEach-Object { [string]$_.displayName })
    }
}
$exampleDisplayNames = @()
foreach ($exampleFile in @('dev.example.json', 'test.example.json', 'demo.example.json', 'prod.example.json')) {
    $examplePath = Join-Path $deploymentParametersRoot $exampleFile
    if (Test-Path -LiteralPath $examplePath -PathType Leaf) {
        $example = Read-JsonFile -Path $examplePath
        if ($example) {
            foreach ($workspaceProperty in $example.workspaces.PSObject.Properties) {
                $exampleDisplayNames += [string]$workspaceProperty.Value.displayName
            }
            foreach ($itemProperty in $example.items.PSObject.Properties) {
                $exampleDisplayNames += [string]$itemProperty.Value.displayName
            }
        }
    }
}
$reservedNames = @($mainCatalogDisplayNames + $exampleDisplayNames) | Select-Object -Unique
$collisions = @($configuredDisplayNames + @($workspaceDisplayName) | Where-Object { $reservedNames -icontains $_ })
Add-Result -Name 'items:no-collision-with-existing-estate' `
    -Passed ($collisions.Count -eq 0) `
    -Detail $(if ($collisions.Count -gt 0) { "Colliding names: $($collisions -join ', ')" } else { 'No overlap with the existing NovaSteel catalog/example display names.' })

# --- Manifest source-file and dependency integrity -----------------------------------------
$manifestKeys = @($manifest.supportedItems | ForEach-Object { [string]$_.key })
foreach ($itemSpec in $manifest.supportedItems) {
    if (-not [bool]$itemSpec.createWithoutDefinition) {
        $sourceDirectory = Join-Path $fabricRoot ([string]$itemSpec.sourceDirectory)
        $missingParts = @()
        foreach ($part in @($itemSpec.definitionParts)) {
            $partPath = Join-Path $sourceDirectory ([string]$part)
            if (-not (Test-Path -LiteralPath $partPath -PathType Leaf)) {
                $missingParts += $part
            }
        }
        Add-Result -Name "source:$($itemSpec.key)" `
            -Passed ($missingParts.Count -eq 0) `
            -Detail $(if ($missingParts.Count -gt 0) { "Missing: $($missingParts -join ', ') under $sourceDirectory" } else { "$($itemSpec.definitionParts.Count) part(s) found under $sourceDirectory" })
    }
    else {
        $sourceDirectory = Join-Path $fabricRoot ([string]$itemSpec.sourceDirectory)
        Add-Result -Name "source:$($itemSpec.key)" `
            -Passed (Test-Path -LiteralPath $sourceDirectory -PathType Container) `
            -Detail "Source directory: $sourceDirectory"
    }

    foreach ($dependency in @($itemSpec.dependencies)) {
        Add-Result -Name "dependency:$($itemSpec.key)->$dependency" `
            -Passed ($manifestKeys -contains [string]$dependency) `
            -Detail "Dependency '$dependency' must be a supportedItems key."
    }

    if (-not $parameters.items.PSObject.Properties.Name -contains [string]$itemSpec.key) {
        Add-Result -Name "parameters:has-item:$($itemSpec.key)" -Passed $false `
            -Detail "parameters.items is missing key '$($itemSpec.key)'."
    }
}

# --- Excluded/manual assets stay out of automation ------------------------------------------
$excludedKeys = @($manifest.excludedItems | ForEach-Object { [string]$_.key })
Add-Result -Name 'excluded:eventstream-not-automated' `
    -Passed ($excludedKeys -contains 'eventstreamTelemetry') `
    -Detail "excludedItems must list eventstreamTelemetry as a manual gate for novasteelv3; found: $($excludedKeys -join ', ')"
Add-Result -Name 'excluded:not-in-supported-items' `
    -Passed (-not ($manifestKeys -contains 'eventstreamTelemetry')) `
    -Detail 'eventstreamTelemetry must not appear in supportedItems.'

Add-Result -Name 'gate:semantic-model-binding-default-false' `
    -Passed (-not [bool]$parameters.deploymentOptions.semanticModelBindingValidated) `
    -Detail 'semanticModelBindingValidated must default to false until the Direct Lake tenant binding is validated.'

$manualAssetKeys = @($manifest.manualAssets | ForEach-Object { [string]$_.key })
Add-Result -Name 'manual:tenant-api-permission-gated' `
    -Passed ($manualAssetKeys -contains 'tenantApiPermission') `
    -Detail "manualAssets must list tenantApiPermission as an explicit human/tenant-admin gate before any .azure/fabric script may run outside -DryRun/-ValidateOnly; found: $($manualAssetKeys -join ', ')"

$result = [pscustomobject]@{
    status    = if ($errors.Count -eq 0) { 'PASS' } else { 'FAIL' }
    checkedAt = [DateTimeOffset]::UtcNow.ToString('o')
    checks    = $checks.ToArray()
    warnings  = $warnings.ToArray()
    errors    = $errors.ToArray()
}
$result | ConvertTo-Json -Depth 30
if ($errors.Count -gt 0) {
    throw "novasteelv3 local validation failed with $($errors.Count) error(s)."
}
