<#
.SYNOPSIS
    End-to-end NovaSteel V3 demo setup orchestrator.
    Order of operations:
      1. Resume capacity (if suspended)
      2. Deploy / update all Fabric items (Deploy-NovaSteelV3FabricAssets.ps1)
      3. Apply KQL schema (Apply-KqlSchema.ps1)
      4. Load synthetic KQL data (Load-SyntheticKqlData.ps1)
      5. Run notebooks in order (Run-NotebookJobs.ps1)
      6. Optionally pause capacity

.PARAMETER ParameterFile
    Path to novasteelv3.parameters.json (default: fabric/deployment-parameters/novasteelv3.parameters.json)
.PARAMETER WorkspaceId
    Fabric workspace ID (overrides whatever is in the state file)
.PARAMETER PauseCapacityAtEnd
    If specified, suspends the Fabric capacity after setup completes
.PARAMETER SkipCapacityResume
    Skip the capacity resume step (capacity already running)
.PARAMETER SkipDeploy
    Skip deploying item definitions (items already up to date)
.PARAMETER SkipKqlSchema
    Skip applying KQL schema (already applied)
.PARAMETER SkipKqlData
    Skip loading synthetic KQL data
.PARAMETER SkipNotebooks
    Skip running notebook jobs
.PARAMETER WhatIf
    Dry-run: report what would happen without making any changes
#>
[CmdletBinding()]
param(
    [string]$ParameterFile     = '',
    [string]$WorkspaceId       = '3d9c0b49-5201-4914-8149-06071b529918',
    [switch]$PauseCapacityAtEnd,
    [switch]$SkipCapacityResume,
    [switch]$SkipDeploy,
    [switch]$SkipKqlSchema,
    [switch]$SkipKqlData,
    [switch]$SkipNotebooks,
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$here     = $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $here)

if (-not $ParameterFile) {
    $ParameterFile = Join-Path $repoRoot 'fabric\deployment-parameters\novasteelv3.parameters.json'
}
if (-not (Test-Path $ParameterFile)) {
    throw "Parameter file not found: $ParameterFile"
}

$params = Get-Content $ParameterFile -Raw | ConvertFrom-Json -Depth 50

$capacityResourceId = '/subscriptions/3377065c-bf76-4767-a982-32bce4ffb592/resourceGroups/rg-novasteelv3-demo-sc/providers/Microsoft.Fabric/capacities/novasteelv3fabric'
$clusterUri         = 'https://trd-q10bnypm07cdfv120p.z8.kusto.fabric.microsoft.com'
$kqlDatabase        = 'kql-novasteelv3-operations'

$summary = [ordered]@{}

function Step([string]$Name, [scriptblock]$Action) {
    Write-Host "`n=== $Name ===" -ForegroundColor Yellow
    $t0 = [DateTimeOffset]::UtcNow
    try {
        & $Action
        $dur = [Math]::Round(([DateTimeOffset]::UtcNow - $t0).TotalSeconds)
        $summary[$Name] = "OK (${dur}s)"
        Write-Host "=== $Name: DONE in ${dur}s ===" -ForegroundColor Green
    } catch {
        $dur = [Math]::Round(([DateTimeOffset]::UtcNow - $t0).TotalSeconds)
        $summary[$Name] = "FAILED (${dur}s): $($_.Exception.Message.Substring(0,[Math]::Min(120,$_.Exception.Message.Length)))"
        Write-Error "=== $Name: FAILED after ${dur}s: $($_.Exception.Message)"
        throw
    }
}

# ---------------------------------------------------------------------------
# 1. Resume capacity
# ---------------------------------------------------------------------------
if (-not $SkipCapacityResume) {
    Step '1-Resume-Capacity' {
        if ($WhatIf) { Write-Host "[WhatIf] Would resume capacity $capacityResourceId"; return }

        $armToken    = (& az account get-access-token --resource https://management.azure.com/ --query accessToken --output tsv).Trim()
        $statusUri   = "https://management.azure.com$capacityResourceId`?api-version=2022-07-01-preview"
        $statusResp  = Invoke-RestMethod -Uri $statusUri -Method GET -Headers @{ Authorization = "Bearer $armToken" } -ErrorAction Stop
        $state       = $statusResp.properties.state
        Write-Host "Current capacity state: $state"

        if ($state -eq 'Paused') {
            Write-Host "Resuming capacity..." -ForegroundColor Cyan
            $resumeUri  = "https://management.azure.com$capacityResourceId/resume?api-version=2022-07-01-preview"
            Invoke-RestMethod -Uri $resumeUri -Method POST -Headers @{ Authorization = "Bearer $armToken" } -ErrorAction Stop | Out-Null
            Write-Host "Waiting for capacity to become Active..."
            $deadline = [DateTimeOffset]::UtcNow.AddMinutes(10)
            while ([DateTimeOffset]::UtcNow -lt $deadline) {
                Start-Sleep -Seconds 20
                $st = (Invoke-RestMethod -Uri $statusUri -Method GET -Headers @{ Authorization = "Bearer $armToken" }).properties.state
                Write-Host "  ...state: $st"
                if ($st -eq 'Active') { break }
            }
        } else {
            Write-Host "Capacity already in state: $state (no resume needed)"
        }
    }
}

# ---------------------------------------------------------------------------
# 2. Deploy Fabric items
# ---------------------------------------------------------------------------
if (-not $SkipDeploy) {
    Step '2-Deploy-Fabric-Items' {
        $deployScript = Join-Path $here 'Deploy-NovaSteelV3FabricAssets.ps1'
        $deployArgs   = @(
            '-ParameterFile', $ParameterFile,
            '-WorkspaceId',   $WorkspaceId
        )
        if ($WhatIf) { $deployArgs += '-WhatIf' }
        Write-Host "Calling: $deployScript $($deployArgs -join ' ')"
        & pwsh -NoProfile -NonInteractive -File $deployScript @deployArgs
        if ($LASTEXITCODE -ne 0) { throw "Deploy-NovaSteelV3FabricAssets.ps1 exited with code $LASTEXITCODE" }
    }
}

# ---------------------------------------------------------------------------
# 3. Apply KQL schema
# ---------------------------------------------------------------------------
if (-not $SkipKqlSchema) {
    Step '3-Apply-KQL-Schema' {
        $schemaScript = Join-Path $here 'Apply-KqlSchema.ps1'
        $schemaArgs   = @(
            '-ClusterUri',   $clusterUri,
            '-DatabaseName', $kqlDatabase
        )
        if ($WhatIf) { $schemaArgs += '-WhatIf' }
        Write-Host "Calling: $schemaScript $($schemaArgs -join ' ')"
        & pwsh -NoProfile -NonInteractive -File $schemaScript @schemaArgs
        if ($LASTEXITCODE -ne 0) { throw "Apply-KqlSchema.ps1 exited with code $LASTEXITCODE" }
    }
}

# ---------------------------------------------------------------------------
# 4. Load synthetic KQL data
# ---------------------------------------------------------------------------
if (-not $SkipKqlData) {
    Step '4-Load-KQL-Data' {
        $dataScript = Join-Path $here 'Load-SyntheticKqlData.ps1'
        $dataArgs   = @(
            '-ClusterUri',   $clusterUri,
            '-DatabaseName', $kqlDatabase
        )
        if ($WhatIf) { $dataArgs += '-WhatIf' }
        Write-Host "Calling: $dataScript $($dataArgs -join ' ')"
        & pwsh -NoProfile -NonInteractive -File $dataScript @dataArgs
        if ($LASTEXITCODE -ne 0) { throw "Load-SyntheticKqlData.ps1 exited with code $LASTEXITCODE" }
    }
}

# ---------------------------------------------------------------------------
# 5. Run notebook jobs
# ---------------------------------------------------------------------------
if (-not $SkipNotebooks) {
    Step '5-Run-Notebooks' {
        $nbScript = Join-Path $here 'Run-NotebookJobs.ps1'
        $nbArgs   = @('-WorkspaceId', $WorkspaceId)
        if ($WhatIf) { $nbArgs += '-WhatIf' }
        Write-Host "Calling: $nbScript $($nbArgs -join ' ')"
        & pwsh -NoProfile -NonInteractive -File $nbScript @nbArgs
        if ($LASTEXITCODE -ne 0) { throw "Run-NotebookJobs.ps1 exited with code $LASTEXITCODE" }
    }
}

# ---------------------------------------------------------------------------
# 6. Pause capacity
# ---------------------------------------------------------------------------
if ($PauseCapacityAtEnd) {
    Step '6-Pause-Capacity' {
        if ($WhatIf) { Write-Host "[WhatIf] Would suspend capacity $capacityResourceId"; return }

        $armToken  = (& az account get-access-token --resource https://management.azure.com/ --query accessToken --output tsv).Trim()
        $pauseUri  = "https://management.azure.com$capacityResourceId/suspend?api-version=2022-07-01-preview"
        $statusUri = "https://management.azure.com$capacityResourceId`?api-version=2022-07-01-preview"
        Write-Host "Suspending capacity..." -ForegroundColor Cyan
        Invoke-RestMethod -Uri $pauseUri -Method POST -Headers @{ Authorization = "Bearer $armToken" } -ErrorAction Stop | Out-Null
        Write-Host "Waiting for capacity to pause..."
        $deadline = [DateTimeOffset]::UtcNow.AddMinutes(10)
        while ([DateTimeOffset]::UtcNow -lt $deadline) {
            Start-Sleep -Seconds 20
            $st = (Invoke-RestMethod -Uri $statusUri -Method GET -Headers @{ Authorization = "Bearer $armToken" }).properties.state
            Write-Host "  ...state: $st"
            if ($st -eq 'Paused') { break }
        }
    }
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  NovaSteel V3 Demo Setup — Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
foreach ($k in $summary.Keys) {
    $color = if ($summary[$k] -like 'OK*') { 'Green' } else { 'Red' }
    Write-Host ("  {0,-30} {1}" -f $k, $summary[$k]) -ForegroundColor $color
}
Write-Host "========================================`n" -ForegroundColor Cyan

$anyFailed = ($summary.Values | Where-Object { $_ -like 'FAILED*' }).Count -gt 0
if ($anyFailed) {
    Write-Error "One or more steps failed. Review errors above."
    exit 1
}
Write-Host "All steps completed successfully." -ForegroundColor Green
