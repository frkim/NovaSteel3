<#
.SYNOPSIS
    Deploys the supported Eventhouse/KQL/Lakehouse/notebook/pipeline/semantic
    item subset into the single, already-bound isolated novasteelv3 Fabric
    workspace.

.DESCRIPTION
    Reuses fabric/scripts/FabricDeployment.psm1 for token acquisition, HTTP
    retries, long-running-operation polling, and definition rendering — it does
    not duplicate that logic. Item source definitions are read (never written)
    from fabric/items, fabric/notebooks, fabric/pipelines, and
    fabric/semantic-model. Every created/updated item uses the unique
    novasteelv3-prefixed display name from the manifest/parameter file, and
    every write is scoped to exactly one workspace ID: the one bound by
    New-NovaSteelV3FabricWorkspace.ps1 (or supplied via -WorkspaceId).

    Eventstream and all manual/portal-only assets listed in the manifest's
    excludedItems/manualAssets are intentionally never created here.

.PARAMETER ParameterFile
    Path to a novasteelv3 parameter file matching
    fabric/deployment-parameters/novasteelv3.schema.json.

.PARAMETER ManifestFile
    Path to fabric/deployment-parameters/novasteelv3.items-manifest.json (or an
    equivalent file matching its schema).

.PARAMETER WorkspaceStateFile
    Path to the workspace binding state produced by
    New-NovaSteelV3FabricWorkspace.ps1. Ignored if -WorkspaceId is supplied.

.PARAMETER WorkspaceId
    Optional override of the target workspace ID, bypassing the state file.

.PARAMETER DryRun
    Validate the manifest/parameters and print the planned item deployment
    order without making any network call.
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$ParameterFile,

    [string]$ManifestFile = '',

    [string]$WorkspaceStateFile = '',

    [string]$WorkspaceId = '',

    [switch]$DryRun,

    [string]$StateOutputPath = '',

    [int]$OperationTimeoutSeconds = 1800
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$azureFabricRoot = $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $azureFabricRoot)
$fabricRoot = Join-Path $repoRoot 'fabric'
$fabricScriptsPath = Join-Path $fabricRoot 'scripts\FabricDeployment.psm1'
if (-not (Test-Path -LiteralPath $fabricScriptsPath -PathType Leaf)) {
    throw "Shared Fabric deployment helpers not found at '$fabricScriptsPath'."
}

if (-not $ManifestFile) {
    $ManifestFile = Join-Path $fabricRoot 'deployment-parameters\novasteelv3.items-manifest.json'
}
if (-not $WorkspaceStateFile) {
    $WorkspaceStateFile = Join-Path $azureFabricRoot 'deployment-state\novasteelv3.workspace.json'
}
foreach ($pathVariable in @('ParameterFile', 'ManifestFile')) {
    $value = Get-Variable -Name $pathVariable -ValueOnly
    if (-not [IO.Path]::IsPathRooted($value)) {
        Set-Variable -Name $pathVariable -Value (Join-Path (Get-Location) $value)
    }
}
if ($WorkspaceStateFile -and -not [IO.Path]::IsPathRooted($WorkspaceStateFile)) {
    $WorkspaceStateFile = Join-Path (Get-Location) $WorkspaceStateFile
}

Import-Module $fabricScriptsPath -Force
Assert-NsParameterFileHasNoSecrets -Path $ParameterFile

$parameters = Get-Content -LiteralPath $ParameterFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100
$manifest = Get-Content -LiteralPath $ManifestFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100

function Get-DynamicProperty {
    param([Parameter(Mandatory)]$Object, [Parameter(Mandatory)][string]$Name, $Default = $null)
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Test-WorkspaceNameIsolated {
    param([string]$DisplayName)
    $pattern = [string]$parameters.isolation.workspaceNamePattern
    if ($DisplayName -notmatch $pattern) {
        throw "Workspace display name '$DisplayName' does not match the required isolation pattern '$pattern'."
    }
    foreach ($reserved in @($parameters.isolation.reservedNamePrefixes)) {
        if ($DisplayName.StartsWith([string]$reserved, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Workspace display name '$DisplayName' starts with the reserved prefix '$reserved'. Refusing to proceed."
        }
    }
}

if ([string]$parameters.project -ne 'novasteelv3') {
    throw "Unsupported project '$($parameters.project)'."
}
if ([string]$parameters.region -ne 'Sweden Central') {
    throw 'novasteelv3 Fabric assets are approved for Sweden Central only.'
}
if (-not [bool]$parameters.syntheticOnly -or [string]$parameters.dataClassification -ne 'SYNTHETIC') {
    throw 'The isolated novasteelv3 workspace must remain synthetic-only and classified SYNTHETIC.'
}
if (-not [bool]$parameters.isolation.neverModifyExistingWorkspaces) {
    throw 'isolation.neverModifyExistingWorkspaces must be true.'
}
if ($parameters.capacity.sku -notin @('F2', 'F4')) {
    throw "Unsupported capacity SKU '$($parameters.capacity.sku)'."
}
Test-WorkspaceNameIsolated -DisplayName ([string]$parameters.workspace.displayName)

# Uniqueness guard: every configured item display name must be unique within the parameter file.
$configuredDisplayNames = @()
foreach ($itemProperty in $parameters.items.PSObject.Properties) {
    $configuredDisplayNames += [string]$itemProperty.Value.displayName
}
$duplicateNames = @($configuredDisplayNames | Group-Object | Where-Object { $_.Count -gt 1 } | ForEach-Object { $_.Name })
if ($duplicateNames.Count -gt 0) {
    throw "Duplicate item display names configured: $($duplicateNames -join ', ')"
}

if (-not $StateOutputPath) {
    $StateOutputPath = Join-Path $azureFabricRoot 'deployment-state\novasteelv3.json'
}
if (-not [IO.Path]::IsPathRooted($StateOutputPath)) {
    $StateOutputPath = Join-Path (Get-Location) $StateOutputPath
}

if ($DryRun) {
    Write-Host 'DRY RUN: no network call will be made. Planned item deployment order:' -ForegroundColor Cyan
    $plan = foreach ($itemSpec in $manifest.supportedItems) {
        $optionName = [string]$itemSpec.deploymentOption
        $enabled = [bool](Get-DynamicProperty -Object $parameters.deploymentOptions -Name $optionName -Default $true)
        $gateOpen = $true
        if ($itemSpec.bindingGate) {
            $gateOpen = [bool](Get-DynamicProperty -Object $parameters.deploymentOptions -Name ([string]$itemSpec.bindingGate) -Default $false)
        }
        $parameterItem = Get-DynamicProperty -Object $parameters.items -Name ([string]$itemSpec.key)
        $displayName = if ($parameterItem -and $parameterItem.displayName) { [string]$parameterItem.displayName } else { [string]$itemSpec.displayName }
        [pscustomobject]@{
            key         = [string]$itemSpec.key
            type        = [string]$itemSpec.type
            displayName = $displayName
            willDeploy  = ($enabled -and $gateOpen)
            reason      = if (-not $enabled) { "$optionName=false" } elseif (-not $gateOpen) { "$($itemSpec.bindingGate)=false" } else { 'enabled' }
        }
    }
    $plan | Format-Table -AutoSize | Out-String | Write-Host
    [pscustomobject]@{
        status = 'DRY_RUN_OK'
        items  = $plan
    } | ConvertTo-Json -Depth 10
    return
}

if (-not $WorkspaceId) {
    if (-not (Test-Path -LiteralPath $WorkspaceStateFile -PathType Leaf)) {
        throw "Workspace state file not found at '$WorkspaceStateFile'. Run New-NovaSteelV3FabricWorkspace.ps1 first, or pass -WorkspaceId explicitly."
    }
    $workspaceState = Get-Content -LiteralPath $WorkspaceStateFile -Raw -Encoding UTF8 |
        ConvertFrom-Json -Depth 20
    $WorkspaceId = [string]$workspaceState.workspace.id
    Test-WorkspaceNameIsolated -DisplayName ([string]$workspaceState.workspace.displayName)
}
if (-not $WorkspaceId) {
    throw 'No workspace ID resolved. Run New-NovaSteelV3FabricWorkspace.ps1 first, or pass -WorkspaceId explicitly.'
}

$authMode = [string]$parameters.authentication.mode
$managedIdentityClientId = [string]$parameters.authentication.managedIdentityClientId
$token = Get-NsAccessToken `
    -Resource 'https://api.fabric.microsoft.com' `
    -AuthenticationMode $authMode `
    -ManagedIdentityClientId $managedIdentityClientId

# Defensive re-check: confirm the resolved workspace ID's live display name still passes the guard.
$liveWorkspace = Invoke-NsFabricRequest -Method GET -Path "/workspaces/$WorkspaceId" -Token $token
if ($null -eq $liveWorkspace) {
    throw "Workspace ID '$WorkspaceId' was not found."
}
Test-WorkspaceNameIsolated -DisplayName ([string]$liveWorkspace.displayName)

$state = [ordered]@{
    schemaVersion = 1
    project       = 'novasteelv3'
    generatedAt   = [DateTimeOffset]::UtcNow.ToString('o')
    workspace     = [ordered]@{
        id          = $WorkspaceId
        displayName = [string]$liveWorkspace.displayName
    }
    items         = [ordered]@{}
}

function New-ReplacementMap {
    $map = @{}
    $map['{{environment}}'] = [string]$parameters.environment
    $map['{{workspace.id}}'] = $WorkspaceId
    $map['{{workspace.displayName}}'] = [string]$state.workspace.displayName
    $map['{{workspace.rtiIngress.id}}'] = $WorkspaceId
    $map['{{workspace.dataCore.id}}'] = $WorkspaceId
    $map['{{workspace.ml.id}}'] = $WorkspaceId
    foreach ($itemEntry in $state.items.GetEnumerator()) {
        $map["{{item.$($itemEntry.Key).id}}"] = [string]$itemEntry.Value.id
        $map["{{item.$($itemEntry.Key).displayName}}"] = [string]$itemEntry.Value.displayName
    }
    foreach ($retentionProperty in $parameters.retention.PSObject.Properties) {
        $map["{{retention.$($retentionProperty.Name)}}"] = [string]$retentionProperty.Value
    }
    $landingUri = [string]$parameters.onelake.landingTablesUri
    if ($landingUri.Contains('<') -and $state.items.Contains('landingLakehouse')) {
        $landingUri = "abfss://$WorkspaceId@onelake.dfs.fabric.microsoft.com/$($state.items.landingLakehouse.id)/Tables"
    }
    $coreUri = [string]$parameters.onelake.coreTablesUri
    if ($coreUri.Contains('<') -and $state.items.Contains('coreLakehouse')) {
        $coreUri = "abfss://$WorkspaceId@onelake.dfs.fabric.microsoft.com/$($state.items.coreLakehouse.id)/Tables"
    }
    $map['{{onelake.landingTablesUri}}'] = $landingUri
    $map['{{onelake.coreTablesUri}}'] = $coreUri
    return $map
}

foreach ($itemSpec in $manifest.supportedItems) {
    $optionName = [string]$itemSpec.deploymentOption
    $enabled = [bool](Get-DynamicProperty -Object $parameters.deploymentOptions -Name $optionName -Default $true)
    if (-not $enabled) {
        Write-Host "SKIP $($itemSpec.key): $optionName=false"
        continue
    }
    if ($itemSpec.bindingGate) {
        $gatePassed = [bool](Get-DynamicProperty -Object $parameters.deploymentOptions -Name ([string]$itemSpec.bindingGate) -Default $false)
        if (-not $gatePassed) {
            Write-Host "GATE $($itemSpec.key): $($itemSpec.bindingGate)=false"
            continue
        }
    }
    foreach ($dependency in @($itemSpec.dependencies)) {
        if (-not $state.items.Contains([string]$dependency)) {
            throw "Item '$($itemSpec.key)' depends on '$dependency', which has not been deployed. Check manifest ordering."
        }
    }

    $parameterItem = Get-DynamicProperty -Object $parameters.items -Name ([string]$itemSpec.key)
    $displayName = if ($parameterItem -and $parameterItem.displayName) { [string]$parameterItem.displayName } else { [string]$itemSpec.displayName }

    $existing = Find-NsItem `
        -WorkspaceId $WorkspaceId `
        -DisplayName $displayName `
        -Type ([string]$itemSpec.type) `
        -Token $token

    $definition = $null
    if (-not [bool]$itemSpec.createWithoutDefinition) {
        $sourceDirectory = Join-Path $fabricRoot ([string]$itemSpec.sourceDirectory)
        $definition = ConvertTo-NsFabricDefinition `
            -SourceDirectory $sourceDirectory `
            -DefinitionParts @($itemSpec.definitionParts) `
            -Replacements (New-ReplacementMap) `
            -Format ([string]$itemSpec.definitionFormat)
    }

    if ($null -eq $existing) {
        $body = [ordered]@{
            displayName = $displayName
            description = [string]$itemSpec.description
        }
        if ($null -ne $definition) {
            $body.definition = $definition
        }
        $labelId = [string]$parameters.bindings.sensitivityLabelId
        $labelGuid = [Guid]::Empty
        if ([Guid]::TryParse($labelId, [ref]$labelGuid) -and $labelGuid -ne [Guid]::Empty) {
            $body.sensitivityLabelSettings = @{
                labelId                       = $labelId
                sensitivityLabelApplyStrategy = 'ApplyOrFail'
            }
        }
        if ($PSCmdlet.ShouldProcess("$($state.workspace.displayName)/$displayName", "Create $($itemSpec.type)")) {
            Invoke-NsFabricRequest `
                -Method POST `
                -Path "/workspaces/$WorkspaceId$($itemSpec.restCollection)" `
                -Token $token `
                -Body $body `
                -TimeoutSeconds $OperationTimeoutSeconds | Out-Null
        }
    }
    elseif ($null -ne $definition) {
        if ($PSCmdlet.ShouldProcess("$($state.workspace.displayName)/$displayName", "Update $($itemSpec.type) definition")) {
            Invoke-NsFabricRequest `
                -Method POST `
                -Path "/workspaces/$WorkspaceId/items/$($existing.id)/updateDefinition?updateMetadata=true" `
                -Token $token `
                -Body @{ definition = $definition } `
                -TimeoutSeconds $OperationTimeoutSeconds | Out-Null
        }
    }

    $resolved = Find-NsItem `
        -WorkspaceId $WorkspaceId `
        -DisplayName $displayName `
        -Type ([string]$itemSpec.type) `
        -Token $token
    if ($null -eq $resolved) {
        throw "Item '$displayName' ($($itemSpec.type)) was not found after deployment."
    }
    $state.items[[string]$itemSpec.key] = [ordered]@{
        id          = [string]$resolved.id
        displayName = $displayName
        type        = [string]$itemSpec.type
    }
}

$stateDirectory = Split-Path -Parent $StateOutputPath
New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
$state.generatedAt = [DateTimeOffset]::UtcNow.ToString('o')
$state | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $StateOutputPath -Encoding UTF8

$manualGates = [System.Collections.Generic.List[object]]::new()
foreach ($excluded in $manifest.excludedItems) {
    $manualGates.Add([pscustomobject]@{ key = [string]$excluded.key; reason = [string]$excluded.reason })
}
foreach ($manualAsset in $manifest.manualAssets) {
    $manualGates.Add([pscustomobject]@{ key = [string]$manualAsset.key; reason = [string]$manualAsset.reason })
}

[pscustomobject]@{
    status      = 'DEPLOYED'
    workspaceId = $WorkspaceId
    stateFile   = $StateOutputPath
    items       = $state.items.Count
    manualGates = $manualGates.ToArray()
} | ConvertTo-Json -Depth 20
