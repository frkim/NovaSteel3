[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$ParameterFile,

    [Parameter(Mandatory)]
    [ValidateSet('Status', 'Resume', 'Suspend')]
    [string]$Action,

    [string]$PreconditionEvidenceFile = '',

    [string]$Actor = '',

    [string]$CorrelationId = '',

    [string]$ResultOutputPath = '',

    [int]$TimeoutSeconds = 1800
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$fabricRoot = Split-Path -Parent $PSScriptRoot
if (-not [IO.Path]::IsPathRooted($ParameterFile)) {
    $ParameterFile = Join-Path (Get-Location) $ParameterFile
}
if ($PreconditionEvidenceFile -and -not [IO.Path]::IsPathRooted($PreconditionEvidenceFile)) {
    $PreconditionEvidenceFile = Join-Path (Get-Location) $PreconditionEvidenceFile
}
if ($ResultOutputPath -and -not [IO.Path]::IsPathRooted($ResultOutputPath)) {
    $ResultOutputPath = Join-Path (Get-Location) $ResultOutputPath
}

Import-Module (Join-Path $PSScriptRoot 'FabricDeployment.psm1') -Force
Assert-NsParameterFileHasNoSecrets -Path $ParameterFile
$parameters = Get-Content -LiteralPath $ParameterFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100

$environment = [string]$parameters.environment
$capacityResourceId = ([string]$parameters.capacity.armResourceId).TrimEnd('/')
$policyVersion = [string]$parameters.lifecycle.policyVersion
$apiVersion = '2023-11-01'
$started = [DateTimeOffset]::UtcNow
$Actor = if ($Actor) { $Actor } else { "PowerShell:$([Environment]::UserName)" }
$correlationWasProvided = -not [string]::IsNullOrWhiteSpace($CorrelationId)
$CorrelationId = if ($CorrelationId) {
    $CorrelationId
}
else {
    "capacity-$($Action.ToLowerInvariant())-$([Guid]::NewGuid().ToString('N'))"
}

function Write-LifecycleResult {
    param(
        [string]$Result,
        [string]$StartState,
        [string]$EndState,
        [string]$ArmOperationId,
        $Evidence,
        [string]$ErrorMessage
    )
    $completed = [DateTimeOffset]::UtcNow
    $output = [ordered]@{
        schemaVersion        = 1
        correlationId       = $CorrelationId
        actor               = $Actor
        policyVersion       = $policyVersion
        environment         = $environment
        capacityResourceId  = $capacityResourceId
        action              = $Action
        startedAt           = $started.ToString('o')
        completedAt         = $completed.ToString('o')
        durationSeconds     = [Math]::Round(($completed - $started).TotalSeconds, 3)
        result              = $Result
        startState          = if ($StartState) { $StartState } else { $null }
        endState            = if ($EndState) { $EndState } else { $null }
        armOperationId      = if ($ArmOperationId) { $ArmOperationId } else { $null }
        preconditionEvidence = $Evidence
        error               = if ($ErrorMessage) { $ErrorMessage } else { $null }
    }
    $json = $output | ConvertTo-Json -Depth 30
    if ($ResultOutputPath) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $ResultOutputPath) -Force |
            Out-Null
        Set-Content -LiteralPath $ResultOutputPath -Value $json -Encoding UTF8
    }
    $json
}

function Get-CapacityState {
    param([string]$Token)
    $response = Invoke-NsHttp `
        -Method GET `
        -Uri "https://management.azure.com$capacityResourceId?api-version=$apiVersion" `
        -Token $Token
    $payload = $response.Json
    if ($null -eq $payload) {
        return $null
    }
    if ($payload.properties -and
        $payload.properties.PSObject.Properties.Name -contains 'state') {
        return [string]$payload.properties.state
    }
    if ($payload.properties -and
        $payload.properties.PSObject.Properties.Name -contains 'provisioningState') {
        return [string]$payload.properties.provisioningState
    }
    return $null
}

if ($environment -eq 'prod') {
    Write-LifecycleResult `
        -Result 'POLICY_DENIED' `
        -StartState '' `
        -EndState '' `
        -ArmOperationId '' `
        -Evidence $null `
        -ErrorMessage 'Production capacity lifecycle automation is hard-denied.'
    throw 'Production capacity lifecycle automation is hard-denied.'
}
if ($environment -notin @('dev', 'test', 'demo')) {
    throw "Unsupported lifecycle environment '$environment'."
}
if (-not $capacityResourceId.StartsWith('/subscriptions/', [StringComparison]::OrdinalIgnoreCase) -or
    $capacityResourceId -notmatch '/providers/Microsoft\.Fabric/capacities/') {
    throw 'capacity.armResourceId is not an exact Microsoft.Fabric capacity resource ID.'
}
if ($capacityResourceId -match '00000000-0000-0000-0000-000000000000|<') {
    throw 'capacity.armResourceId still contains a placeholder.'
}

$token = Get-NsAccessToken `
    -Resource 'https://management.azure.com/' `
    -AuthenticationMode ([string]$parameters.authentication.mode) `
    -ManagedIdentityClientId ([string]$parameters.authentication.managedIdentityClientId)
$startState = Get-CapacityState -Token $token

if ($Action -eq 'Status') {
    Write-LifecycleResult `
        -Result 'STATUS_ONLY' `
        -StartState $startState `
        -EndState $startState `
        -ArmOperationId '' `
        -Evidence $null `
        -ErrorMessage ''
    return
}

$evidence = $null
if ($Action -eq 'Suspend') {
    if (-not $PreconditionEvidenceFile -or
        -not (Test-Path -LiteralPath $PreconditionEvidenceFile -PathType Leaf)) {
        throw 'Suspend requires a precondition evidence JSON file.'
    }
    $evidence = Get-Content -LiteralPath $PreconditionEvidenceFile -Raw -Encoding UTF8 |
        ConvertFrom-Json -Depth 100
    if ([string]$evidence.environment -ne $environment) {
        throw 'Precondition evidence targets a different environment.'
    }
    if ([string]$evidence.capacityResourceId -ine $capacityResourceId) {
        throw 'Precondition evidence targets a different capacity resource ID.'
    }
    if (-not $correlationWasProvided -and $evidence.correlationId) {
        $CorrelationId = [string]$evidence.correlationId
    }
    elseif ($evidence.correlationId -and
        [string]$evidence.correlationId -ne $CorrelationId) {
        throw 'Precondition evidence correlationId does not match.'
    }
    $checkedAt = [DateTimeOffset]::Parse([string]$evidence.checkedAt)
    $evidenceAge = ([DateTimeOffset]::UtcNow - $checkedAt).TotalMinutes
    if ($evidenceAge -lt -1 -or
        $evidenceAge -gt [int]$parameters.lifecycle.preconditionMaxAgeMinutes) {
        throw "Precondition evidence is not fresh (age: $([Math]::Round($evidenceAge, 2)) minutes)."
    }

    $busyReasons = [System.Collections.Generic.List[string]]::new()
    if (-not [bool]$evidence.simulatorStopped) { $busyReasons.Add('simulator is running') }
    if (-not [bool]$evidence.relayDrainedOrCheckpointed) { $busyReasons.Add('relay is not drained/checkpointed') }
    if ([bool]$evidence.protectedRehearsalActive) { $busyReasons.Add('protected rehearsal is active') }
    if ([bool]$evidence.criticalFabricJobActive) { $busyReasons.Add('critical Fabric job is active') }
    if ([bool]$evidence.approvedConsumerActive) { $busyReasons.Add('approved consumer is active') }
    if ([bool]$evidence.budgetBlock) { $busyReasons.Add('policy/budget block is active') }
    if ($busyReasons.Count -gt 0) {
        Write-LifecycleResult `
            -Result 'SKIPPED_BUSY' `
            -StartState $startState `
            -EndState $startState `
            -ArmOperationId '' `
            -Evidence $evidence `
            -ErrorMessage ($busyReasons -join '; ')
        return
    }
}

$operationName = if ($Action -eq 'Resume') { 'resume' } else { 'suspend' }
$operationUri = "https://management.azure.com$capacityResourceId/$operationName?api-version=$apiVersion"
$armOperationId = ''

try {
    if (-not $PSCmdlet.ShouldProcess($capacityResourceId, $Action)) {
        Write-LifecycleResult `
            -Result 'POLICY_DENIED' `
            -StartState $startState `
            -EndState $startState `
            -ArmOperationId '' `
            -Evidence $evidence `
            -ErrorMessage 'Operation not executed because ShouldProcess declined.'
        return
    }

    $response = Invoke-NsHttp -Method POST -Uri $operationUri -Token $token
    $armOperationId = Get-NsHeaderValue -Headers $response.Headers -Name 'x-ms-request-id'
    if (-not $armOperationId) {
        $armOperationId = Get-NsHeaderValue -Headers $response.Headers -Name 'x-ms-operation-id'
    }
    $pollUri = Get-NsHeaderValue -Headers $response.Headers -Name 'Azure-AsyncOperation'
    if (-not $pollUri) {
        $pollUri = Get-NsHeaderValue -Headers $response.Headers -Name 'Location'
    }

    if ($response.StatusCode -eq 202) {
        $deadline = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
        $operationSucceeded = $false
        while ([DateTimeOffset]::UtcNow -lt $deadline) {
            $retryAfter = Get-NsHeaderValue -Headers $response.Headers -Name 'Retry-After'
            $delay = if ($retryAfter -as [int]) { [int]$retryAfter } else { 10 }
            Start-Sleep -Seconds ([Math]::Max(1, [Math]::Min(60, $delay)))

            if ($pollUri) {
                $poll = Invoke-NsHttp -Method GET -Uri $pollUri -Token $token
                $status = if ($poll.Json -and
                    $poll.Json.PSObject.Properties.Name -contains 'status') {
                    [string]$poll.Json.status
                }
                else {
                    ''
                }
                if ($status -match '^(Failed|Cancelled|Canceled)$') {
                    throw "ARM operation failed: $($poll.Content)"
                }
                if ($status -match '^(Succeeded|Completed|Success)$') {
                    $operationSucceeded = $true
                    break
                }
                $response = $poll
            }
            else {
                $state = Get-CapacityState -Token $token
                if (($Action -eq 'Resume' -and $state -match '^(Active|Running|Succeeded)$') -or
                    ($Action -eq 'Suspend' -and $state -match '^(Paused|Suspended|Succeeded)$')) {
                    $operationSucceeded = $true
                    break
                }
            }
        }
        if (-not $operationSucceeded) {
            throw "ARM capacity $Action timed out after $TimeoutSeconds seconds."
        }
    }

    $endState = Get-CapacityState -Token $token
    Write-LifecycleResult `
        -Result 'SUCCEEDED' `
        -StartState $startState `
        -EndState $endState `
        -ArmOperationId $armOperationId `
        -Evidence $evidence `
        -ErrorMessage ''
}
catch {
    $endState = $null
    try { $endState = Get-CapacityState -Token $token } catch { }
    Write-LifecycleResult `
        -Result 'FAILED' `
        -StartState $startState `
        -EndState $endState `
        -ArmOperationId $armOperationId `
        -Evidence $evidence `
        -ErrorMessage $_.Exception.Message
    throw
}
