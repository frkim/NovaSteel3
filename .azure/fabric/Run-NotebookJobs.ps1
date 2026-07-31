<#
.SYNOPSIS
    Triggers Fabric notebook job runs (via Fabric REST Jobs API) in dependency
    order and waits for each to complete.
#>
[CmdletBinding()]
param(
    [string]$WorkspaceId    = '3d9c0b49-5201-4914-8149-06071b529918',
    [string]$LandingTablesUri = '',
    [string]$CoreTablesUri    = '',
    [string[]]$NotebookDisplayName = @(
        'v3-initialize-lakehouses',
        'v3-steel-ontology',
        'v3-bronze-to-silver',
        'v3-silver-to-gold',
        'v3-deterministic-demo-scoring',
        'v3-validate-data-quality'
    ),
    [int]$MaxWaitMinutes    = 30,
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Import-Module (Join-Path $repoRoot 'fabric\scripts\FabricDeployment.psm1') -Force

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Acquiring Fabric API token..." -ForegroundColor Cyan
$token = Get-NsAccessToken -Resource 'https://api.fabric.microsoft.com' -AuthenticationMode 'AzureCli'

# Resolve OneLake URIs from lakehouse IDs if not provided
function Resolve-OneLakeUri {
    param([string]$WorkspaceId, [string]$LakehouseId)
    return "abfss://$WorkspaceId@onelake.dfs.fabric.microsoft.com/$LakehouseId/Tables"
}

if (-not $LandingTablesUri -or $LandingTablesUri.Contains('<')) {
    Write-Host "Resolving landing lakehouse URI from workspace items..." -ForegroundColor DarkCyan
    $allItems = Invoke-NsFabricRequest -Method GET -Path "/workspaces/$WorkspaceId/lakehouses" -Token $token
    $landing  = $allItems.value | Where-Object { $_.displayName -like '*landing*' } | Select-Object -First 1
    if ($landing) {
        $LandingTablesUri = Resolve-OneLakeUri -WorkspaceId $WorkspaceId -LakehouseId $landing.id
        Write-Host "  Landing URI: $LandingTablesUri"
    }
}
if (-not $CoreTablesUri -or $CoreTablesUri.Contains('<')) {
    $allItems = Invoke-NsFabricRequest -Method GET -Path "/workspaces/$WorkspaceId/lakehouses" -Token $token
    $core     = $allItems.value | Where-Object { $_.displayName -like '*core*' } | Select-Object -First 1
    if ($core) {
        $CoreTablesUri = Resolve-OneLakeUri -WorkspaceId $WorkspaceId -LakehouseId $core.id
        Write-Host "  Core URI: $CoreTablesUri"
    }
}

$results = [System.Collections.Generic.List[pscustomobject]]::new()

foreach ($nbName in $NotebookDisplayName) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Looking up notebook: $nbName" -ForegroundColor DarkCyan
    $nb = Find-NsItem -WorkspaceId $WorkspaceId -DisplayName $nbName -Type 'Notebook' -Token $token
    if ($null -eq $nb) {
        Write-Warning "Notebook '$nbName' not found in workspace. Skipping."
        $results.Add([pscustomobject]@{ Notebook = $nbName; Status = 'NOT_FOUND'; Duration = 'N/A' })
        continue
    }

    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Starting notebook: $nbName (id: $($nb.id))" -ForegroundColor Cyan

    if ($WhatIf) {
        Write-Host "  [WhatIf] Would trigger job for $nbName" -ForegroundColor DarkGray
        $results.Add([pscustomobject]@{ Notebook = $nbName; Status = 'WHATIF'; Duration = 'N/A' })
        continue
    }

    $jobBody = @{
        executionData = @{
            parameters = @{
                ENVIRONMENT        = @{ value = 'novasteelv3-demo'; type = 'string' }
                LANDING_TABLES_URI = @{ value = $LandingTablesUri;  type = 'string' }
                CORE_TABLES_URI    = @{ value = $CoreTablesUri;      type = 'string' }
            }
        }
    }

    $jobStart = [DateTimeOffset]::UtcNow
    try {
        $jobUri     = "/workspaces/$WorkspaceId/items/$($nb.id)/jobs/instances?jobType=RunNotebook"
        $jobHeaders = @{
            Authorization  = "Bearer $token"
            Accept         = 'application/json'
            'Content-Type' = 'application/json'
        }
        $bodyJson = $jobBody | ConvertTo-Json -Depth 10 -Compress
        $jobResp  = Invoke-WebRequest `
            -Uri "https://api.fabric.microsoft.com/v1$jobUri" `
            -Method POST -Headers $jobHeaders -Body $bodyJson `
            -ContentType 'application/json' -SkipHttpErrorCheck -ErrorAction Stop

        if ($jobResp.StatusCode -ge 400) {
            $errMsg = $jobResp.Content.Substring(0, [Math]::Min(400, $jobResp.Content.Length))
            Write-Warning "  Failed to start: HTTP $($jobResp.StatusCode) - $errMsg"
            $results.Add([pscustomobject]@{ Notebook = $nbName; Status = 'START_FAILED'; Duration = 'N/A' })
            continue
        }

        # Get the Location header for polling
        $locationUri = $null
        foreach ($hkey in $jobResp.Headers.Keys) {
            if ($hkey -ieq 'Location') {
                $locationUri = ($jobResp.Headers[$hkey] | Select-Object -First 1)
                break
            }
        }
        if (-not $locationUri) {
            foreach ($hkey in $jobResp.Headers.Keys) {
                if ($hkey -ieq 'x-ms-operation-id') {
                    $opId = ($jobResp.Headers[$hkey] | Select-Object -First 1)
                    $locationUri = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items/$($nb.id)/jobs/instances/$opId"
                    break
                }
            }
        }

        if (-not $locationUri) {
            Write-Warning "  Job submitted (HTTP $($jobResp.StatusCode)) but no Location/operation-id returned. Cannot poll status."
            $results.Add([pscustomobject]@{ Notebook = $nbName; Status = 'SUBMITTED_NO_POLL'; Duration = '?' })
            continue
        }

        Write-Host "  Polling: $locationUri"
        $deadline  = [DateTimeOffset]::UtcNow.AddMinutes($MaxWaitMinutes)
        $finalStatus = 'UNKNOWN'
        while ([DateTimeOffset]::UtcNow -lt $deadline) {
            Start-Sleep -Seconds 15
            $pollResp = Invoke-WebRequest `
                -Uri $locationUri -Method GET -Headers $jobHeaders `
                -SkipHttpErrorCheck -ErrorAction Stop
            if ($pollResp.StatusCode -ge 400) { break }
            $pollJson = $pollResp.Content | ConvertFrom-Json -Depth 20 -ErrorAction SilentlyContinue
            $status = [string]$pollJson.status
            Write-Host "  ...status: $status"
            if ($status -match '^(Succeeded|Completed|Success)$') { $finalStatus = 'SUCCESS'; break }
            if ($status -match '^(Failed|Cancelled|Canceled)$')   { $finalStatus = 'FAILED';  break }
            if ($status -eq 'Deduped') { Write-Host "  Job deduplicated (another instance running)."; $finalStatus = 'SUCCESS'; break }
        }
        if ($finalStatus -eq 'UNKNOWN') { $finalStatus = 'TIMEOUT' }

        $dur = [Math]::Round(([DateTimeOffset]::UtcNow - $jobStart).TotalSeconds)
        if ($finalStatus -eq 'SUCCESS') {
            Write-Host "  DONE in ${dur}s" -ForegroundColor Green
        } else {
            Write-Warning "  $finalStatus after ${dur}s"
        }
        $results.Add([pscustomobject]@{ Notebook = $nbName; Status = $finalStatus; Duration = "${dur}s" })
    }
    catch {
        $dur = [Math]::Round(([DateTimeOffset]::UtcNow - $jobStart).TotalSeconds)
        Write-Warning "  ERROR: $($_.Exception.Message)"
        $results.Add([pscustomobject]@{ Notebook = $nbName; Status = 'ERROR'; Duration = "${dur}s" })
    }
}

Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Notebook run summary:" -ForegroundColor Cyan
$results | Format-Table -AutoSize
$failed = @($results | Where-Object { $_.Status -notin @('SUCCESS','WHATIF','SUBMITTED_NO_POLL') })
if ($failed.Count -gt 0) {
    Write-Warning "$($failed.Count) notebook(s) did not succeed. Check Fabric workspace for details."
}
