[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$ParameterFile,

    [Parameter(Mandatory)]
    [string]$StateFile,

    [string]$CatalogFile = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$fabricRoot = Split-Path -Parent $PSScriptRoot
if (-not $CatalogFile) {
    $CatalogFile = Join-Path $fabricRoot 'catalog\fabric-items.json'
}
foreach ($pathVariable in @('ParameterFile', 'StateFile', 'CatalogFile')) {
    $value = Get-Variable -Name $pathVariable -ValueOnly
    if (-not [IO.Path]::IsPathRooted($value)) {
        Set-Variable -Name $pathVariable -Value (Join-Path (Get-Location) $value)
    }
}

Import-Module (Join-Path $PSScriptRoot 'FabricDeployment.psm1') -Force
Assert-NsParameterFileHasNoSecrets -Path $ParameterFile

if (-not (Get-Command fab -ErrorAction SilentlyContinue)) {
    throw 'Fabric CLI (fab) is required. Install it only through the approved protected package feed.'
}

$parameters = Get-Content -LiteralPath $ParameterFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100
$state = Get-Content -LiteralPath $StateFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -AsHashtable -Depth 100
$catalog = Get-Content -LiteralPath $CatalogFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100

if ([string]$state.environment -ne [string]$parameters.environment) {
    throw 'State file and parameter file target different environments.'
}

if ([string]$parameters.authentication.mode -eq 'ManagedIdentity') {
    $arguments = @('auth', 'login', '--identity')
    if ($parameters.authentication.managedIdentityClientId) {
        $arguments += @('-u', [string]$parameters.authentication.managedIdentityClientId)
    }
    & fab @arguments
    if ($LASTEXITCODE -ne 0) {
        throw 'Fabric CLI managed-identity login failed.'
    }
}
else {
    & fab ls --output_format json | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw 'Fabric CLI is not authenticated. Run fab auth login before this script.'
    }
}

function Get-OptionValue {
    param([string]$Name, [bool]$Default = $true)
    $property = $parameters.deploymentOptions.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $Default
    }
    return [bool]$property.Value
}

function New-Replacements {
    $map = @{}
    $map['{{environment}}'] = [string]$parameters.environment
    foreach ($workspaceEntry in $state.workspaces.GetEnumerator()) {
        $map["{{workspace.$($workspaceEntry.Key).id}}"] = [string]$workspaceEntry.Value.id
        $map["{{workspace.$($workspaceEntry.Key).displayName}}"] = [string]$workspaceEntry.Value.displayName
    }
    foreach ($itemEntry in $state.items.GetEnumerator()) {
        $map["{{item.$($itemEntry.Key).id}}"] = [string]$itemEntry.Value.id
        $map["{{item.$($itemEntry.Key).displayName}}"] = [string]$itemEntry.Value.displayName
    }
    foreach ($retentionProperty in $parameters.retention.PSObject.Properties) {
        $map["{{retention.$($retentionProperty.Name)}}"] = [string]$retentionProperty.Value
    }
    $landingUri = [string]$parameters.onelake.landingTablesUri
    if ($landingUri.Contains('<')) {
        $landingUri = "abfss://$($state.workspaces.rtiIngress.id)@onelake.dfs.fabric.microsoft.com/$($state.items.landingLakehouse.id)/Tables"
    }
    $coreUri = [string]$parameters.onelake.coreTablesUri
    if ($coreUri.Contains('<')) {
        $coreUri = "abfss://$($state.workspaces.dataCore.id)@onelake.dfs.fabric.microsoft.com/$($state.items.coreLakehouse.id)/Tables"
    }
    $map['{{onelake.landingTablesUri}}'] = $landingUri
    $map['{{onelake.coreTablesUri}}'] = $coreUri
    return $map
}

$renderRoot = Join-Path $fabricRoot "deployment-state\rendered\$($parameters.environment)"
if (Test-Path -LiteralPath $renderRoot) {
    Remove-Item -LiteralPath $renderRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $renderRoot -Force | Out-Null
$replacements = New-Replacements
$results = [System.Collections.Generic.List[object]]::new()

foreach ($itemSpec in $catalog.items) {
    if (-not [bool]$itemSpec.cliDeployable) {
        continue
    }
    if (-not (Get-OptionValue -Name ([string]$itemSpec.deploymentOption))) {
        continue
    }
    if ($itemSpec.bindingGate -and
        -not (Get-OptionValue -Name ([string]$itemSpec.bindingGate) -Default $false)) {
        continue
    }
    if (-not $state.items.Contains([string]$itemSpec.key)) {
        throw "CLI deployment requires '$($itemSpec.key)' in the REST bootstrap state file."
    }

    $sourceDirectory = Join-Path $fabricRoot ([string]$itemSpec.sourceDirectory)
    $renderDirectory = Join-Path $renderRoot "$($itemSpec.displayName).$($itemSpec.type)"
    New-Item -ItemType Directory -Path $renderDirectory -Force | Out-Null
    foreach ($part in @($itemSpec.definitionParts)) {
        $sourcePath = Join-Path $sourceDirectory ([string]$part)
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
            throw "Definition part not found: $sourcePath"
        }
        $content = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
        foreach ($key in @($replacements.Keys | Sort-Object Length -Descending)) {
            $content = $content.Replace([string]$key, [string]$replacements[$key])
        }
        $unresolved = [regex]::Matches($content, '\{\{[^{}]+\}\}') |
            ForEach-Object { $_.Value } |
            Sort-Object -Unique
        if ($unresolved) {
            throw "Unresolved tokens for '$($itemSpec.key)': $($unresolved -join ', ')"
        }
        $destinationPath = Join-Path $renderDirectory ([string]$part)
        New-Item -ItemType Directory -Path (Split-Path -Parent $destinationPath) -Force |
            Out-Null
        Set-Content -LiteralPath $destinationPath -Value $content -Encoding UTF8
    }

    $workspaceName = [string]$state.workspaces[[string]$itemSpec.workspaceKey].displayName
    $target = "$workspaceName.Workspace/$($itemSpec.displayName).$($itemSpec.type)"
    if ($PSCmdlet.ShouldProcess($target, 'Fabric CLI import create/update')) {
        & fab import $target -i $renderDirectory -f
        if ($LASTEXITCODE -ne 0) {
            throw "fab import failed for $target"
        }
        & fab exists $target
        if ($LASTEXITCODE -ne 0) {
            throw "fab exists failed after import for $target"
        }
    }
    $results.Add([pscustomobject]@{
        key    = [string]$itemSpec.key
        target = $target
        status = 'IMPORTED'
    })
}

[pscustomobject]@{
    status      = 'CLI_DEFINITIONS_DEPLOYED'
    environment = [string]$parameters.environment
    renderedAt  = $renderRoot
    items       = $results.ToArray()
} | ConvertTo-Json -Depth 20
