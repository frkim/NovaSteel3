<#
.SYNOPSIS
    Idempotently creates or binds the single, synthetic-only NovaSteelV3-Demo
    Fabric workspace to the isolated novasteelv3 F2 capacity.

.DESCRIPTION
    This script never touches any workspace other than the one resolved from
    -WorkspaceId (bind mode) or parameters.workspace.displayName (create-or-find
    mode). It refuses to run against a display name that does not match the
    configured isolation.workspaceNamePattern, or that starts with a reserved
    prefix used by the existing four-workspace NovaSteel estate.

    No Fabric or Azure resource is deployed by running this script today: use
    -DryRun (default recommendation) to validate the plan with zero network
    calls, and -WhatIf to preview the exact write calls once real IDs are
    supplied. Only an explicit run without -DryRun/-WhatIf performs a mutation,
    and only after the referenced capacity is confirmed Active/Succeeded.

.PARAMETER ParameterFile
    Path to a novasteelv3 parameter file matching
    fabric/deployment-parameters/novasteelv3.schema.json.

.PARAMETER WorkspaceId
    Optional. Bind to an already-created workspace by ID instead of resolving
    it by display name. The workspace's own display name is still validated
    against the isolation guard before any further action.

.PARAMETER DryRun
    Validate parameters and print the intended plan without making any network
    call (no az/Fabric/ARM calls at all). Safe to run without any credentials.

.PARAMETER StateOutputPath
    Where to write the workspace binding state JSON. Defaults to
    .azure/fabric/deployment-state/novasteelv3.workspace.json.
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$ParameterFile,

    [string]$WorkspaceId = '',

    [switch]$DryRun,

    [string]$StateOutputPath = '',

    [int]$OperationTimeoutSeconds = 1800
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$azureFabricRoot = $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $azureFabricRoot)
$fabricScriptsPath = Join-Path $repoRoot 'fabric\scripts\FabricDeployment.psm1'
if (-not (Test-Path -LiteralPath $fabricScriptsPath -PathType Leaf)) {
    throw "Shared Fabric deployment helpers not found at '$fabricScriptsPath'."
}

if (-not [IO.Path]::IsPathRooted($ParameterFile)) {
    $ParameterFile = Join-Path (Get-Location) $ParameterFile
}

Import-Module $fabricScriptsPath -Force
Assert-NsParameterFileHasNoSecrets -Path $ParameterFile

$parameters = Get-Content -LiteralPath $ParameterFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100

function Assert-NonPlaceholderGuidValue {
    param([string]$Name, [string]$Value)
    $parsed = [Guid]::Empty
    if (-not [Guid]::TryParse($Value, [ref]$parsed) -or $parsed -eq [Guid]::Empty) {
        throw "$Name must be a non-zero GUID before this script can call any Fabric/Azure API. Use -DryRun to validate the plan without real IDs."
    }
}

function Test-WorkspaceNameIsolated {
    param([string]$DisplayName)
    $pattern = [string]$parameters.isolation.workspaceNamePattern
    if ($DisplayName -notmatch $pattern) {
        throw "Workspace display name '$DisplayName' does not match the required isolation pattern '$pattern'."
    }
    foreach ($reserved in @($parameters.isolation.reservedNamePrefixes)) {
        if ($DisplayName.StartsWith([string]$reserved, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Workspace display name '$DisplayName' starts with the reserved prefix '$reserved', which belongs to the existing NovaSteel estate. Refusing to proceed."
        }
    }
}

# --- Structural validation (always runs, even in -DryRun) ---------------------------------
if ([string]$parameters.project -ne 'novasteelv3') {
    throw "Unsupported project '$($parameters.project)'. This script only binds the isolated novasteelv3 workspace."
}
if ([string]$parameters.environment -ne 'novasteelv3-demo') {
    throw "Unsupported environment '$($parameters.environment)'."
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

$workspaceDisplayName = [string]$parameters.workspace.displayName
Test-WorkspaceNameIsolated -DisplayName $workspaceDisplayName

$capacityArmResourceId = ([string]$parameters.capacity.armResourceId).TrimEnd('/')
if (-not $capacityArmResourceId.StartsWith('/subscriptions/', [StringComparison]::OrdinalIgnoreCase) -or
    $capacityArmResourceId -notmatch '/providers/Microsoft\.Fabric/capacities/') {
    throw 'capacity.armResourceId is not an exact Microsoft.Fabric capacity resource ID.'
}

if (-not $StateOutputPath) {
    $StateOutputPath = Join-Path $azureFabricRoot 'deployment-state\novasteelv3.workspace.json'
}
if (-not [IO.Path]::IsPathRooted($StateOutputPath)) {
    $StateOutputPath = Join-Path (Get-Location) $StateOutputPath
}

$plan = [ordered]@{
    action              = if ($WorkspaceId) { 'Bind existing workspace by ID' } else { 'Find or create workspace by display name' }
    workspaceDisplayName = $workspaceDisplayName
    workspaceId         = $WorkspaceId
    capacityArmResourceId = $capacityArmResourceId
    capacityFabricId    = [string]$parameters.capacity.fabricCapacityId
    assignCapacity      = [bool]$parameters.deploymentOptions.assignCapacity
    createOrBindWorkspace = [bool]$parameters.deploymentOptions.createOrBindWorkspace
}

if ($DryRun) {
    Write-Host 'DRY RUN: no network call will be made. Planned action:' -ForegroundColor Cyan
    $plan | ConvertTo-Json -Depth 10
    [pscustomobject]@{
        status = 'DRY_RUN_OK'
        plan   = $plan
    } | ConvertTo-Json -Depth 10
    return
}

# --- Live validation and execution (network calls from this point on) ---------------------
Assert-NonPlaceholderGuidValue -Name 'tenantId' -Value ([string]$parameters.tenantId)
Assert-NonPlaceholderGuidValue -Name 'subscriptionId' -Value ([string]$parameters.subscriptionId)
Assert-NonPlaceholderGuidValue -Name 'capacity.fabricCapacityId' -Value ([string]$parameters.capacity.fabricCapacityId)

$authMode = [string]$parameters.authentication.mode
$managedIdentityClientId = [string]$parameters.authentication.managedIdentityClientId

# Precondition: the F2 capacity must already exist and be usable before any workspace bind.
$armToken = Get-NsAccessToken `
    -Resource 'https://management.azure.com/' `
    -AuthenticationMode $authMode `
    -ManagedIdentityClientId $managedIdentityClientId
$capacityResponse = Invoke-NsHttp `
    -Method GET `
    -Uri "https://management.azure.com$capacityArmResourceId`?api-version=2023-11-01" `
    -Token $armToken
$capacityState = $null
if ($capacityResponse.Json -and $capacityResponse.Json.properties) {
    $capacityState = [string]$capacityResponse.Json.properties.state
    if (-not $capacityState) {
        $capacityState = [string]$capacityResponse.Json.properties.provisioningState
    }
}
if ($capacityState -notmatch '^(Active|Succeeded)$') {
    throw "Capacity '$capacityArmResourceId' is not Active/Succeeded (observed state: '$capacityState'). Confirm the F2 capacity exists and is running before binding the novasteelv3 workspace."
}

$fabricToken = Get-NsAccessToken `
    -Resource 'https://api.fabric.microsoft.com' `
    -AuthenticationMode $authMode `
    -ManagedIdentityClientId $managedIdentityClientId

$workspace = $null
if ($WorkspaceId) {
    $workspace = Invoke-NsFabricRequest -Method GET -Path "/workspaces/$WorkspaceId" -Token $fabricToken
    if ($null -eq $workspace) {
        throw "Workspace ID '$WorkspaceId' was not found."
    }
    Test-WorkspaceNameIsolated -DisplayName ([string]$workspace.displayName)
}
else {
    $workspace = Find-NsWorkspace -DisplayName $workspaceDisplayName -Token $fabricToken
    if ($null -eq $workspace) {
        if (-not [bool]$parameters.deploymentOptions.createOrBindWorkspace) {
            throw "Workspace '$workspaceDisplayName' does not exist and deploymentOptions.createOrBindWorkspace=false."
        }
        if ($PSCmdlet.ShouldProcess($workspaceDisplayName, 'Create isolated novasteelv3 Fabric workspace')) {
            $body = [ordered]@{
                displayName = $workspaceDisplayName
                description = 'Isolated synthetic-only novasteelv3 demo workspace. Never used by the existing NovaSteel dev/test/demo/prod estate.'
                capacityId  = [string]$parameters.capacity.fabricCapacityId
            }
            Invoke-NsFabricRequest `
                -Method POST `
                -Path '/workspaces' `
                -Token $fabricToken `
                -Body $body `
                -TimeoutSeconds $OperationTimeoutSeconds | Out-Null
        }
        $workspace = Find-NsWorkspace -DisplayName $workspaceDisplayName -Token $fabricToken
        if ($null -eq $workspace) {
            throw "Workspace '$workspaceDisplayName' was not found after creation."
        }
    }
}

if ([bool]$parameters.deploymentOptions.assignCapacity) {
    $currentCapacity = if ($workspace.PSObject.Properties.Name -contains 'capacityId') { [string]$workspace.capacityId } else { '' }
    if ($currentCapacity -ne [string]$parameters.capacity.fabricCapacityId) {
        if ($PSCmdlet.ShouldProcess($workspaceDisplayName, "Assign capacity $($parameters.capacity.fabricCapacityId)")) {
            $assignmentResponse = Invoke-NsHttp `
                -Method POST `
                -Uri "https://api.fabric.microsoft.com/v1/workspaces/$($workspace.id)/assignToCapacity" `
                -Token $fabricToken `
                -Body @{ capacityId = [string]$parameters.capacity.fabricCapacityId }
            if ($assignmentResponse.StatusCode -eq 202) {
                Wait-NsFabricOperation `
                    -InitialResponse $assignmentResponse `
                    -Token $fabricToken `
                    -TimeoutSeconds $OperationTimeoutSeconds | Out-Null
            }

            $deadline = [DateTimeOffset]::UtcNow.AddSeconds($OperationTimeoutSeconds)
            $assignmentVerified = $false
            while ([DateTimeOffset]::UtcNow -lt $deadline) {
                $workspace = Invoke-NsFabricRequest -Method GET -Path "/workspaces/$($workspace.id)" -Token $fabricToken
                $assignedCapacity = if ($workspace.PSObject.Properties.Name -contains 'capacityId') { [string]$workspace.capacityId } else { '' }
                $progress = if ($workspace.PSObject.Properties.Name -contains 'capacityAssignmentProgress') { [string]$workspace.capacityAssignmentProgress } else { '' }
                if ($progress -eq 'Failed') {
                    throw "Workspace '$workspaceDisplayName' capacity assignment failed."
                }
                if ($assignedCapacity -eq [string]$parameters.capacity.fabricCapacityId -and
                    ([string]::IsNullOrWhiteSpace($progress) -or $progress -eq 'Completed')) {
                    $assignmentVerified = $true
                    break
                }
                Start-Sleep -Seconds 5
            }
            if (-not $assignmentVerified) {
                throw "Workspace '$workspaceDisplayName' capacity assignment did not complete before timeout."
            }
        }
    }
}

$state = [ordered]@{
    schemaVersion = 1
    project       = 'novasteelv3'
    generatedAt   = [DateTimeOffset]::UtcNow.ToString('o')
    workspace     = [ordered]@{
        id          = [string]$workspace.id
        displayName = $workspaceDisplayName
        capacityId  = [string]$parameters.capacity.fabricCapacityId
    }
}
$stateDirectory = Split-Path -Parent $StateOutputPath
New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
$state | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $StateOutputPath -Encoding UTF8

[pscustomobject]@{
    status        = 'BOUND'
    workspaceId   = [string]$workspace.id
    displayName   = $workspaceDisplayName
    portalUrl     = "https://app.fabric.microsoft.com/groups/$($workspace.id)/list"
    stateFile     = $StateOutputPath
} | ConvertTo-Json -Depth 10
