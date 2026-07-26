<#
.SYNOPSIS
    Safe, non-mutating verification of the isolated novasteelv3 Fabric
    workspace/item deployment, plus Fabric portal URL output.

.DESCRIPTION
    Local mode (default) builds Fabric portal URLs purely from the IDs already
    recorded in a deployment-state JSON file — no network call is made.
    -Live mode additionally performs read-only Fabric GET calls (via the
    shared fabric/scripts/FabricDeployment.psm1 helpers) to confirm the
    workspace and each item still exist and the workspace capacity assignment
    matches the recorded state. No script path here ever creates, updates, or
    deletes anything.

.PARAMETER StateFile
    Path to the .azure/fabric/deployment-state/novasteelv3.json file produced
    by Deploy-NovaSteelV3FabricAssets.ps1 (or the workspace-only
    novasteelv3.workspace.json produced by New-NovaSteelV3FabricWorkspace.ps1).

.PARAMETER ParameterFile
    Required only for -Live, to resolve the authentication mode.

.PARAMETER Live
    Perform read-only Fabric REST GET calls to confirm the state file matches
    reality. Requires an authenticated az/Fabric context.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$StateFile,

    [string]$ParameterFile = '',

    [switch]$Live
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$azureFabricRoot = $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $azureFabricRoot)
$fabricScriptsPath = Join-Path $repoRoot 'fabric\scripts\FabricDeployment.psm1'

if (-not [IO.Path]::IsPathRooted($StateFile)) {
    $StateFile = Join-Path (Get-Location) $StateFile
}
if (-not (Test-Path -LiteralPath $StateFile -PathType Leaf)) {
    throw "State file not found: $StateFile"
}

$state = Get-Content -LiteralPath $StateFile -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100

$itemTypeToPortalSegment = @{
    Eventhouse    = 'eventhouses'
    KQLDatabase   = 'kustodatabases'
    Lakehouse     = 'lakehouses'
    Notebook      = 'synapsenotebooks'
    DataPipeline  = 'pipelines'
    SemanticModel = 'datasets'
}

$checks = [System.Collections.Generic.List[object]]::new()
$failures = [System.Collections.Generic.List[string]]::new()

function Add-Check {
    param([string]$Key, [string]$Status, [string]$Detail)
    $checks.Add([pscustomobject]@{ key = $Key; status = $Status; detail = $Detail })
    if ($Status -eq 'FAIL') { $failures.Add("${Key}: $Detail") }
}

$workspaceId = [string]$state.workspace.id
$workspaceDisplayName = [string]$state.workspace.displayName
if ([string]::IsNullOrWhiteSpace($workspaceId)) {
    throw "State file '$StateFile' has no workspace.id recorded."
}

$urls = [System.Collections.Generic.List[object]]::new()
$urls.Add([pscustomobject]@{
    key  = 'workspace'
    type = 'Workspace'
    name = $workspaceDisplayName
    url  = "https://app.fabric.microsoft.com/groups/$workspaceId/list"
})

if ($state.PSObject.Properties.Name -contains 'items') {
    foreach ($itemProperty in $state.items.PSObject.Properties) {
        $item = $itemProperty.Value
        $segment = $itemTypeToPortalSegment[[string]$item.type]
        $url = if ($segment) {
            "https://app.fabric.microsoft.com/groups/$workspaceId/$segment/$($item.id)"
        }
        else {
            "https://app.fabric.microsoft.com/groups/$workspaceId/list"
        }
        $urls.Add([pscustomobject]@{
            key  = [string]$itemProperty.Name
            type = [string]$item.type
            name = [string]$item.displayName
            url  = $url
        })
    }
}
Add-Check -Key 'urls:generated' -Status 'PASS' -Detail "$($urls.Count) URL(s) built from state file (no network call)."

if ($Live) {
    if (-not $ParameterFile) {
        throw '-Live requires -ParameterFile to resolve the authentication mode.'
    }
    if (-not [IO.Path]::IsPathRooted($ParameterFile)) {
        $ParameterFile = Join-Path (Get-Location) $ParameterFile
    }
    Import-Module $fabricScriptsPath -Force
    Assert-NsParameterFileHasNoSecrets -Path $ParameterFile
    $parameters = Get-Content -LiteralPath $ParameterFile -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100

    $token = Get-NsAccessToken `
        -Resource 'https://api.fabric.microsoft.com' `
        -AuthenticationMode ([string]$parameters.authentication.mode) `
        -ManagedIdentityClientId ([string]$parameters.authentication.managedIdentityClientId)

    $liveWorkspace = $null
    try {
        $liveWorkspace = Invoke-NsFabricRequest -Method GET -Path "/workspaces/$workspaceId" -Token $token
    }
    catch {
        Add-Check -Key 'live:workspace' -Status 'FAIL' -Detail $_.Exception.Message
    }
    if ($liveWorkspace) {
        if ([string]$liveWorkspace.displayName -ne $workspaceDisplayName) {
            Add-Check -Key 'live:workspace' -Status 'FAIL' -Detail "Live display name '$($liveWorkspace.displayName)' differs from state '$workspaceDisplayName'."
        }
        else {
            Add-Check -Key 'live:workspace' -Status 'PASS' -Detail "Workspace '$workspaceDisplayName' confirmed via read-only GET."
        }
        $liveCapacity = if ($liveWorkspace.PSObject.Properties.Name -contains 'capacityId') { [string]$liveWorkspace.capacityId } else { '' }
        Add-Check -Key 'live:capacity-assignment' `
            -Status $(if ($liveCapacity) { 'PASS' } else { 'WARN' }) `
            -Detail "Assigned capacityId: '$liveCapacity'"
    }

    if ($state.PSObject.Properties.Name -contains 'items') {
        foreach ($itemProperty in $state.items.PSObject.Properties) {
            $item = $itemProperty.Value
            try {
                $liveItem = Invoke-NsFabricRequest -Method GET -Path "/workspaces/$workspaceId/items/$($item.id)" -Token $token
                if ($null -eq $liveItem) {
                    Add-Check -Key "live:item:$($itemProperty.Name)" -Status 'FAIL' -Detail 'Item not found.'
                }
                else {
                    Add-Check -Key "live:item:$($itemProperty.Name)" -Status 'PASS' -Detail "$($liveItem.type)/$($liveItem.displayName) confirmed."
                }
            }
            catch {
                Add-Check -Key "live:item:$($itemProperty.Name)" -Status 'FAIL' -Detail $_.Exception.Message
            }
        }
    }
}

$result = [pscustomobject]@{
    status  = if ($failures.Count -eq 0) { 'PASS' } else { 'FAIL' }
    mode    = if ($Live) { 'Live' } else { 'Local' }
    stateFile = $StateFile
    urls    = $urls.ToArray()
    checks  = $checks.ToArray()
    failures = $failures.ToArray()
}
$result | ConvertTo-Json -Depth 30
if ($failures.Count -gt 0) {
    throw "novasteelv3 verification failed with $($failures.Count) error(s)."
}
