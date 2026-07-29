<#
.SYNOPSIS
    Deploy (create or update) the es-ns-telemetry-v1 Eventstream into the
    single-workspace NovaSteelV3 demo, reusing the shared FabricDeployment
    helper module.

.DESCRIPTION
    The greenfield Deploy-FabricAssets.ps1 orchestrator assumes a four-workspace
    topology (rtiIngress/dataCore/ml/analytics) and an environment name in
    {dev,test,demo,prod}. The live NovaSteelV3-Demo tenant deployment instead
    uses a *single* workspace that already holds all 14 items, described by
    deployment-parameters/novasteelv3.parameters.json (singular `workspace` plus
    a resolved `items` map). This focused deployer bridges that gap for the one
    item that was never deployed - the Eventstream - without re-touching the
    other 13 already-deployed items.

    It does NOT reimplement token replacement or REST plumbing: it renders and
    validates the definition with ConvertTo-NsFabricDefinition and calls the
    Fabric REST API through Invoke-NsFabricRequest / Find-NsItem, exactly like
    Deploy-FabricAssets.ps1. Placeholders in the definition
    ({{workspace.rtiIngress.id}}, {{item.landingLakehouse.id}},
    {{item.kqlOperations.id}}, {{item.kqlOperations.displayName}},
    {{retention.*}}) are resolved from the parameters file.

    No secret is read or written. The generated Custom Endpoint connection
    string is retrieved separately by Get-FabricEventstreamEndpoint.ps1.
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$ParameterFile = '',

    [string]$CatalogFile = '',

    [string]$StateOutputPath = '',

    [string]$ItemKey = 'eventstreamTelemetry',

    [ValidateSet('AzureCli', 'ManagedIdentity')]
    [string]$AuthenticationMode = 'AzureCli',

    [int]$OperationTimeoutSeconds = 1800
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$fabricRoot = Split-Path -Parent $PSScriptRoot
if (-not $ParameterFile) {
    $ParameterFile = Join-Path $fabricRoot 'deployment-parameters\novasteelv3.parameters.json'
}
if (-not $CatalogFile) {
    $CatalogFile = Join-Path $fabricRoot 'catalog\fabric-items.json'
}
foreach ($pathVariable in @('ParameterFile', 'CatalogFile')) {
    $value = Get-Variable -Name $pathVariable -ValueOnly
    if (-not [IO.Path]::IsPathRooted($value)) {
        Set-Variable -Name $pathVariable -Value (Join-Path (Get-Location) $value)
    }
}

Import-Module (Join-Path $PSScriptRoot 'FabricDeployment.psm1') -Force
Assert-NsParameterFileHasNoSecrets -Path $ParameterFile

$parameters = Get-Content -LiteralPath $ParameterFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100
$catalog = Get-Content -LiteralPath $CatalogFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100

$workspaceId = [string]$parameters.workspace.id
$workspaceName = [string]$parameters.workspace.displayName
if ([string]::IsNullOrWhiteSpace($workspaceId)) {
    throw 'Parameter file is missing workspace.id.'
}

$itemSpec = $catalog.items | Where-Object { [string]$_.key -eq $ItemKey }
if (-not $itemSpec) {
    throw "Catalog item '$ItemKey' not found in $CatalogFile."
}

# Build the replacement map from the single-workspace parameters file. Every
# catalog workspace key collapses onto the one live workspace, and every item
# token resolves from the parameters `items` map (already populated with the
# real deployed GUIDs).
$replacements = @{}
$replacements['{{environment}}'] = [string]$parameters.environment
foreach ($workspaceSpec in $catalog.workspaces) {
    $key = [string]$workspaceSpec.key
    $replacements["{{workspace.$key.id}}"] = $workspaceId
    $replacements["{{workspace.$key.displayName}}"] = $workspaceName
}
foreach ($itemProperty in $parameters.items.PSObject.Properties) {
    $replacements["{{item.$($itemProperty.Name).id}}"] = [string]$itemProperty.Value.id
    $replacements["{{item.$($itemProperty.Name).displayName}}"] = [string]$itemProperty.Value.displayName
}
foreach ($retentionProperty in $parameters.retention.PSObject.Properties) {
    $replacements["{{retention.$($retentionProperty.Name)}}"] = [string]$retentionProperty.Value
}

# Fail fast on the specific dependencies this item declares so a missing id in
# the parameters file is a clear error rather than an "unresolved token".
foreach ($dependency in @($itemSpec.dependencies)) {
    if (-not $replacements.ContainsKey("{{item.$dependency.id}}") -or
        [string]::IsNullOrWhiteSpace($replacements["{{item.$dependency.id}}"])) {
        throw "Eventstream depends on '$dependency' but items.$dependency.id is absent from the parameter file."
    }
}

$authMode = [string]$parameters.authentication.mode
$managedIdentityClientId = [string]$parameters.authentication.managedIdentityClientId
# The parameters file records the CI/production auth mode (ManagedIdentity).
# Interactive/tenant runs pass -AuthenticationMode AzureCli (the default) and
# rely on an existing `az login`. The explicit switch always wins.
$resolvedAuthMode = $AuthenticationMode
$token = Get-NsAccessToken `
    -Resource 'https://api.fabric.microsoft.com' `
    -AuthenticationMode $resolvedAuthMode `
    -ManagedIdentityClientId $managedIdentityClientId

$sourceDirectory = Join-Path $fabricRoot ([string]$itemSpec.sourceDirectory)
$definition = ConvertTo-NsFabricDefinition `
    -SourceDirectory $sourceDirectory `
    -DefinitionParts @($itemSpec.definitionParts) `
    -Replacements $replacements `
    -Format ([string]$itemSpec.definitionFormat)

$parameterItem = $parameters.items.PSObject.Properties[$ItemKey]
$displayName = if ($parameterItem -and $parameterItem.Value.displayName) {
    [string]$parameterItem.Value.displayName
}
else {
    [string]$itemSpec.displayName
}

$existing = Find-NsItem `
    -WorkspaceId $workspaceId `
    -DisplayName $displayName `
    -Type ([string]$itemSpec.type) `
    -Token $token

if ($null -eq $existing) {
    $body = [ordered]@{
        displayName = $displayName
        description = [string]$itemSpec.description
        definition  = $definition
    }
    if ($PSCmdlet.ShouldProcess("$workspaceName/$displayName", "Create $($itemSpec.type)")) {
        Invoke-NsFabricRequest `
            -Method POST `
            -Path "/workspaces/$workspaceId$($itemSpec.restCollection)" `
            -Token $token `
            -Body $body `
            -TimeoutSeconds $OperationTimeoutSeconds | Out-Null
    }
}
else {
    if ($PSCmdlet.ShouldProcess("$workspaceName/$displayName", "Update $($itemSpec.type) definition")) {
        Invoke-NsFabricRequest `
            -Method POST `
            -Path "/workspaces/$workspaceId/items/$($existing.id)/updateDefinition?updateMetadata=true" `
            -Token $token `
            -Body @{ definition = $definition } `
            -TimeoutSeconds $OperationTimeoutSeconds | Out-Null
    }
}

$resolved = Find-NsItem `
    -WorkspaceId $workspaceId `
    -DisplayName $displayName `
    -Type ([string]$itemSpec.type) `
    -Token $token
if ($null -eq $resolved) {
    throw "Eventstream '$displayName' was not found after deployment."
}

if (-not $StateOutputPath) {
    $StateOutputPath = Join-Path $fabricRoot "deployment-state\$($parameters.environment)-eventstream.json"
}
if (-not [IO.Path]::IsPathRooted($StateOutputPath)) {
    $StateOutputPath = Join-Path (Get-Location) $StateOutputPath
}
New-Item -ItemType Directory -Path (Split-Path -Parent $StateOutputPath) -Force | Out-Null
[ordered]@{
    schemaVersion = 1
    environment   = [string]$parameters.environment
    generatedAt   = [DateTimeOffset]::UtcNow.ToString('o')
    workspaceId   = $workspaceId
    eventstream   = [ordered]@{
        key         = $ItemKey
        displayName = $displayName
        id          = [string]$resolved.id
        type        = [string]$itemSpec.type
    }
} | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $StateOutputPath -Encoding UTF8

[pscustomobject]@{
    status        = 'EVENTSTREAM_DEPLOYED'
    environment   = [string]$parameters.environment
    workspaceId   = $workspaceId
    eventstreamId = [string]$resolved.id
    displayName   = $displayName
    stateFile     = $StateOutputPath
} | ConvertTo-Json -Depth 20
