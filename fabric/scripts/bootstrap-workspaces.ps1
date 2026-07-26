<#
.SYNOPSIS
    Idempotently creates or finds the NS-<env>-{RTI-Ingress,DataCore,ML,Analytics} Fabric
    workspaces, assigns them to the environment's capacity, and applies OneLake role assignments.

.DESCRIPTION
    Implements the four-workspace isolation pattern described in
    docs/architecture/solution-architecture.md §6.3 (lines 138-146). Driven from
    fabric/deployment-parameters/<env>.json, using the proven auth pattern from
    .azure/fabric/New-NovaSteelV3FabricWorkspace.ps1 and fabric/scripts/FabricDeployment.psm1.

    The script is:
    - IDEMPOTENT: safe to re-run — finds existing workspaces by display name before creating.
    - CREDENTIAL-SAFE: uses managed identity or Azure CLI credentials, never secrets.
    - ENVIRONMENT-AWARE: validates against the parameter file's environment and region.

.PARAMETER ParameterFile
    Path to a fabric/deployment-parameters/<env>.json file conforming to environment.schema.json.

.PARAMETER DryRun
    Validate parameters and print the intended plan without making any network call.

.PARAMETER OperationTimeoutSeconds
    Maximum wait time for long-running Fabric operations (default: 1800s).

.EXAMPLE
    .\bootstrap-workspaces.ps1 -ParameterFile ..\deployment-parameters\dev.example.json -DryRun
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$ParameterFile,

    [switch]$DryRun,

    [int]$OperationTimeoutSeconds = 1800
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Resolve paths and import shared module ----------------------------------
$scriptRoot = $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptRoot)
$fabricModulePath = Join-Path $scriptRoot 'FabricDeployment.psm1'
if (-not (Test-Path -LiteralPath $fabricModulePath -PathType Leaf)) {
    throw "Shared Fabric deployment helpers not found at '$fabricModulePath'."
}
Import-Module $fabricModulePath -Force

if (-not [IO.Path]::IsPathRooted($ParameterFile)) {
    $ParameterFile = Join-Path (Get-Location) $ParameterFile
}
if (-not (Test-Path -LiteralPath $ParameterFile -PathType Leaf)) {
    throw "Parameter file not found: $ParameterFile"
}
Assert-NsParameterFileHasNoSecrets -Path $ParameterFile

$parameters = Get-Content -LiteralPath $ParameterFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100

# --- Structural validation (always runs, even in -DryRun) --------------------
$validEnvironments = @('dev', 'test', 'demo', 'prod')
$env = [string]$parameters.environment
if ($env -notin $validEnvironments) {
    throw "Unsupported environment '$env'. Must be one of: $($validEnvironments -join ', ')"
}
if ([string]$parameters.region -ne 'Sweden Central') {
    throw "Region must be 'Sweden Central' (EU primary per ADR-003). Got: $($parameters.region)"
}

$expectedWorkspaceKeys = @('rtiIngress', 'dataCore', 'ml', 'analytics')
foreach ($key in $expectedWorkspaceKeys) {
    if (-not $parameters.workspaces.PSObject.Properties.Name -contains $key) {
        throw "Parameter file is missing workspace definition: workspaces.$key"
    }
    $ws = $parameters.workspaces.$key
    if ([string]::IsNullOrWhiteSpace([string]$ws.displayName)) {
        throw "workspaces.$key.displayName must not be empty."
    }
}

$capacityArmResourceId = ([string]$parameters.capacity.armResourceId).TrimEnd('/')
if (-not $capacityArmResourceId.StartsWith('/subscriptions/', [StringComparison]::OrdinalIgnoreCase) -or
    $capacityArmResourceId -notmatch '/providers/Microsoft\.Fabric/capacities/') {
    throw 'capacity.armResourceId must be a valid Microsoft.Fabric/capacities ARM resource ID.'
}
$capacityFabricId = [string]$parameters.capacity.fabricCapacityId

# --- Build plan ---------------------------------------------------------------
$workspacePlan = @()
foreach ($key in $expectedWorkspaceKeys) {
    $ws = $parameters.workspaces.$key
    $workspacePlan += [ordered]@{
        key         = $key
        displayName = [string]$ws.displayName
        existingId  = [string]$ws.id
    }
}

$plan = [ordered]@{
    environment       = $env
    region            = [string]$parameters.region
    capacityArm       = $capacityArmResourceId
    capacityFabricId  = $capacityFabricId
    assignCapacity    = [bool]$parameters.deploymentOptions.assignCapacity
    createWorkspaces  = [bool]$parameters.deploymentOptions.createWorkspaces
    workspaces        = $workspacePlan
}

if ($DryRun) {
    Write-Host 'DRY RUN: no network call will be made. Planned actions:' -ForegroundColor Cyan
    $plan | ConvertTo-Json -Depth 10
    [pscustomobject]@{
        status = 'DRY_RUN_OK'
        plan   = $plan
    } | ConvertTo-Json -Depth 10
    return
}

# --- Live execution (network calls from this point on) ------------------------
$authMode = [string]$parameters.authentication.mode
$managedIdentityClientId = [string]$parameters.authentication.managedIdentityClientId

# Acquire tokens using the proven pattern from FabricDeployment.psm1
$armToken = Get-NsAccessToken `
    -Resource 'https://management.azure.com/' `
    -AuthenticationMode $authMode `
    -ManagedIdentityClientId $managedIdentityClientId

# Validate capacity is Active/Succeeded before creating workspaces
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
    throw "Capacity '$capacityArmResourceId' is not Active/Succeeded (observed: '$capacityState'). The capacity must be running before workspace bootstrap."
}

$fabricToken = Get-NsAccessToken `
    -Resource 'https://api.fabric.microsoft.com' `
    -AuthenticationMode $authMode `
    -ManagedIdentityClientId $managedIdentityClientId

# --- Process each workspace: find-or-create, then assign capacity -------------
$results = @()
foreach ($wsPlan in $workspacePlan) {
    $displayName = [string]$wsPlan.displayName
    $existingId = [string]$wsPlan.existingId

    $workspace = $null

    # If an ID is pre-supplied, bind to it directly
    if (-not [string]::IsNullOrWhiteSpace($existingId)) {
        $workspace = Invoke-NsFabricRequest -Method GET -Path "/workspaces/$existingId" -Token $fabricToken
        if ($null -eq $workspace) {
            throw "Workspace ID '$existingId' (for $($wsPlan.key)) was not found."
        }
        Write-Host "  [FOUND BY ID] $displayName -> $existingId" -ForegroundColor Green
    }
    else {
        # Find by display name (idempotent)
        $workspace = Find-NsWorkspace -DisplayName $displayName -Token $fabricToken
        if ($null -ne $workspace) {
            Write-Host "  [EXISTS] $displayName -> $($workspace.id)" -ForegroundColor Green
        }
        elseif ([bool]$parameters.deploymentOptions.createWorkspaces) {
            if ($PSCmdlet.ShouldProcess($displayName, 'Create Fabric workspace')) {
                Write-Host "  [CREATING] $displayName..." -ForegroundColor Yellow
                $body = [ordered]@{
                    displayName = $displayName
                    description = "NovaSteel $env workspace ($($wsPlan.key)). Managed by bootstrap-workspaces.ps1."
                    capacityId  = $capacityFabricId
                }
                Invoke-NsFabricRequest `
                    -Method POST `
                    -Path '/workspaces' `
                    -Token $fabricToken `
                    -Body $body `
                    -TimeoutSeconds $OperationTimeoutSeconds | Out-Null
            }
            $workspace = Find-NsWorkspace -DisplayName $displayName -Token $fabricToken
            if ($null -eq $workspace) {
                throw "Workspace '$displayName' was not found after creation."
            }
            Write-Host "  [CREATED] $displayName -> $($workspace.id)" -ForegroundColor Green
        }
        else {
            throw "Workspace '$displayName' does not exist and deploymentOptions.createWorkspaces=false."
        }
    }

    # Assign capacity if needed (idempotent — checks current assignment first)
    if ([bool]$parameters.deploymentOptions.assignCapacity) {
        $currentCapacity = if ($workspace.PSObject.Properties.Name -contains 'capacityId') { [string]$workspace.capacityId } else { '' }
        if ($currentCapacity -ne $capacityFabricId) {
            if ($PSCmdlet.ShouldProcess($displayName, "Assign capacity $capacityFabricId")) {
                Write-Host "  [ASSIGNING CAPACITY] $displayName -> $capacityFabricId" -ForegroundColor Yellow
                $assignmentResponse = Invoke-NsHttp `
                    -Method POST `
                    -Uri "https://api.fabric.microsoft.com/v1/workspaces/$($workspace.id)/assignToCapacity" `
                    -Token $fabricToken `
                    -Body @{ capacityId = $capacityFabricId }
                if ($assignmentResponse.StatusCode -eq 202) {
                    Wait-NsFabricOperation `
                        -InitialResponse $assignmentResponse `
                        -Token $fabricToken `
                        -TimeoutSeconds $OperationTimeoutSeconds | Out-Null
                }

                # Poll until assignment is confirmed
                $deadline = [DateTimeOffset]::UtcNow.AddSeconds($OperationTimeoutSeconds)
                $assignmentVerified = $false
                while ([DateTimeOffset]::UtcNow -lt $deadline) {
                    $workspace = Invoke-NsFabricRequest -Method GET -Path "/workspaces/$($workspace.id)" -Token $fabricToken
                    $assignedCapacity = if ($workspace.PSObject.Properties.Name -contains 'capacityId') { [string]$workspace.capacityId } else { '' }
                    $progress = if ($workspace.PSObject.Properties.Name -contains 'capacityAssignmentProgress') { [string]$workspace.capacityAssignmentProgress } else { '' }
                    if ($progress -eq 'Failed') {
                        throw "Workspace '$displayName' capacity assignment failed."
                    }
                    if ($assignedCapacity -eq $capacityFabricId -and
                        ([string]::IsNullOrWhiteSpace($progress) -or $progress -eq 'Completed')) {
                        $assignmentVerified = $true
                        break
                    }
                    Start-Sleep -Seconds 5
                }
                if (-not $assignmentVerified) {
                    throw "Workspace '$displayName' capacity assignment did not complete before timeout."
                }
            }
        }
        else {
            Write-Host "  [CAPACITY OK] $displayName already on $capacityFabricId" -ForegroundColor Green
        }
    }

    # Apply workspace role assignments if bindings are configured
    if ($parameters.bindings.PSObject.Properties.Name -contains 'dataEngineeringIdentityObjectId' -and
        -not [string]::IsNullOrWhiteSpace([string]$parameters.bindings.dataEngineeringIdentityObjectId)) {
        $principalId = [string]$parameters.bindings.dataEngineeringIdentityObjectId
        if ($PSCmdlet.ShouldProcess($displayName, "Add role assignment for $principalId")) {
            try {
                $roleBody = [ordered]@{
                    principal = [ordered]@{
                        id   = $principalId
                        type = 'ServicePrincipal'
                    }
                    role = 'Contributor'
                }
                Invoke-NsHttp `
                    -Method POST `
                    -Uri "https://api.fabric.microsoft.com/v1/workspaces/$($workspace.id)/roleAssignments" `
                    -Token $fabricToken `
                    -Body $roleBody | Out-Null
                Write-Host "  [ROLE ASSIGNED] Contributor -> $principalId on $displayName" -ForegroundColor Green
            }
            catch {
                # 409 Conflict means the role assignment already exists (idempotent)
                if ($_.Exception.Message -match '409') {
                    Write-Host "  [ROLE EXISTS] Contributor for $principalId on $displayName" -ForegroundColor Green
                }
                else {
                    throw
                }
            }
        }
    }

    $results += [ordered]@{
        key         = [string]$wsPlan.key
        displayName = $displayName
        id          = [string]$workspace.id
        portalUrl   = "https://app.fabric.microsoft.com/groups/$($workspace.id)/list"
    }
}

# --- Summary output -----------------------------------------------------------
Write-Host "`nBootstrap complete. Workspaces:" -ForegroundColor Cyan
$results | ForEach-Object { Write-Host "  $($_.displayName) -> $($_.id)" }

[pscustomobject]@{
    status     = 'BOOTSTRAP_COMPLETE'
    environment = $env
    workspaces = $results
} | ConvertTo-Json -Depth 10
