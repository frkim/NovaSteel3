<#
.SYNOPSIS
    Land the multi-month analytical gold dataset into the deployed
    lh_novasteelv3_core lakehouse, resuming/suspending the F2 capacity around
    the load for cost control.

.DESCRIPTION
    The analytical (static) data stream is produced locally by the simulator:

        python -m simulator generate-analytics --scenario analytical-programme-24m

    which writes eight gold-grain CSVs plus manifest.json/checksums.json into
    output\analytical-programme-24m. This script:

      1. (optional) Resumes the paused Fabric capacity so Spark can run.
      2. Uploads the generated CSVs (+ manifest) to OneLake under
         Files/<FilesSubPath>/ in the core lakehouse, using your Azure AD
         identity (az login locally, or the deployment managed identity in
         Azure). No secrets are read or written.
      3. (optional) Triggers the ns-load-analytical-gold notebook via the
         Fabric REST API to MERGE the CSVs into the core Delta Tables/.
      4. (optional) Suspends the capacity again.

    Authentication uses Azure AD only (managed identity where available,
    otherwise the signed-in az context). Nothing here embeds a credential.

.NOTES
    F2 heavily throttles Spark. For a large one-shot backfill you may want to
    temporarily scale the capacity to F4/F8, run the load, then scale back and
    suspend. See README.md in this folder for the exact az commands.

.EXAMPLE
    ./Load-AnalyticalGold.ps1 -ResumeCapacity -RunNotebook -SuspendAfter

.EXAMPLE
    # Upload only (capacity already running), no notebook trigger:
    ./Load-AnalyticalGold.ps1 -RunDir ..\..\output\analytical-programme-24m
#>
[CmdletBinding()]
param(
    [string]$ParametersFile = (Join-Path $PSScriptRoot '..\..\fabric\deployment-parameters\novasteelv3.parameters.json'),
    [ValidateSet('gold', 'operational', 'reference')]
    [string]$Layer = 'gold',
    [string]$RunDir,
    [string]$ScenarioId = 'analytical-programme-24m',
    [string]$FilesSubPath,
    [string]$NotebookParamKey,
    [switch]$ResumeCapacity,
    [switch]$RunNotebook,
    [switch]$SuspendAfter
)

$ErrorActionPreference = 'Stop'

function Assert-Command($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "Required command '$name' was not found on PATH."
    }
}

Assert-Command az

# Layer defaults: 'gold' lands the eight fact_* tables (semantic model / Power BI);
# 'operational' seeds bronze and lands the nine envelope tables the BFF reads (BFF_DATA_SOURCE=fabric);
# 'reference' lands the dimensions that bronze-to-silver resolves every event against.
if ($Layer -eq 'operational') {
    if (-not $RunDir)           { $RunDir = (Join-Path $PSScriptRoot '..\..\output\operational-envelopes') }
    if (-not $FilesSubPath)     { $FilesSubPath = 'operational-envelopes' }
    if (-not $NotebookParamKey) { $NotebookParamKey = 'notebookSeedBronzeFromPack' }
    $generateHint = "python -m simulator generate-operational"
} elseif ($Layer -eq 'reference') {
    if (-not $RunDir)           { $RunDir = (Join-Path $PSScriptRoot '..\..\output\reference-data') }
    if (-not $FilesSubPath)     { $FilesSubPath = 'reference-data' }
    if (-not $NotebookParamKey) { $NotebookParamKey = 'notebookLoadReferenceData' }
    $generateHint = "python -m simulator generate-reference"
} else {
    if (-not $RunDir)           { $RunDir = (Join-Path $PSScriptRoot '..\..\output\analytical-programme-24m') }
    if (-not $FilesSubPath)     { $FilesSubPath = "analytical-gold/$ScenarioId" }
    if (-not $NotebookParamKey) { $NotebookParamKey = 'notebookLoadAnalyticalGold' }
    $generateHint = "python -m simulator generate-analytics --scenario $ScenarioId"
}

if (-not (Test-Path $ParametersFile)) { throw "Parameters file not found: $ParametersFile" }
if (-not (Test-Path $RunDir)) {
    throw "Run directory not found: $RunDir. Generate it first with '$generateHint'."
}

$params = Get-Content -Raw -Path $ParametersFile | ConvertFrom-Json
$workspaceId   = $params.workspace.id
$coreLakehouse = $params.items.coreLakehouse.id
$capacityArmId = $params.capacity.armResourceId
$notebookId    = $params.items.$NotebookParamKey.id  # optional; may be absent until deployed

if (-not $workspaceId)   { throw 'workspace.id missing from parameters file.' }
if (-not $coreLakehouse) { throw 'items.coreLakehouse.id missing from parameters file.' }

Write-Host "Layer         : $Layer"
Write-Host "Workspace     : $workspaceId"
Write-Host "Core lakehouse: $coreLakehouse"
Write-Host "Files subpath : $FilesSubPath"

# --- 1. Resume capacity ----------------------------------------------------
if ($ResumeCapacity) {
    if (-not $capacityArmId) { throw 'capacity.armResourceId missing; cannot resume.' }
    Write-Host "Resuming capacity $capacityArmId ..."
    az resource invoke-action --action resume --ids $capacityArmId | Out-Null
    Write-Host 'Capacity resume requested; waiting 60s for it to become active...'
    Start-Sleep -Seconds 60
}

# --- 2. Upload CSVs to OneLake Files ---------------------------------------
# OneLake speaks the ADLS Gen2 DFS/Blob APIs. azcopy with AAD auto-login is the
# most reliable uploader; fall back to 'az storage fs file upload --auth-mode login'.
$oneLakeDfs = "https://onelake.dfs.fabric.microsoft.com/$workspaceId/$coreLakehouse/Files/$FilesSubPath"
$files = Get-ChildItem -Path $RunDir -File | Where-Object { $_.Extension -in '.csv', '.json', '.ndjson' }
if (-not $files) { throw "No .csv/.json/.ndjson files found in $RunDir." }

$useAzcopy = [bool](Get-Command azcopy -ErrorAction SilentlyContinue)
if ($useAzcopy) {
    Write-Host 'Uploading via azcopy (AAD auto-login)...'
    $env:AZCOPY_AUTO_LOGIN_TYPE = if ($env:MSI_ENDPOINT -or $env:IDENTITY_ENDPOINT) { 'MSI' } else { 'AZCLI' }
    foreach ($f in $files) {
        $dest = "$oneLakeDfs/$($f.Name)"
        Write-Host "  -> $($f.Name)"
        azcopy copy "$($f.FullName)" "$dest" --overwrite=true --from-to=LocalBlob | Out-Null
    }
} else {
    # OneLake does not support the Blob endpoint that `az storage fs file upload`
    # targets (it fails with EndpointUnsupportedAccountFeatures). Use the ADLS
    # Gen2 DFS REST API directly: create -> append -> flush.
    Write-Host 'azcopy not found; uploading via OneLake DFS REST (AAD login)...'
    $dfsToken = az account get-access-token --resource 'https://storage.azure.com' --query accessToken -o tsv
    if (-not $dfsToken) { throw 'Could not acquire a storage.azure.com token via az.' }
    $dfsHeaders = @{ Authorization = "Bearer $dfsToken"; 'x-ms-version' = '2023-11-03' }
    $uploadFailures = @()
    foreach ($f in $files) {
        $target = "$oneLakeDfs/$($f.Name)"
        Write-Host "  -> $($f.Name)"
        try {
            Invoke-RestMethod -Uri "${target}?resource=file" -Method PUT -Headers $dfsHeaders -ErrorAction Stop | Out-Null
            $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
            if ($bytes.Length -gt 0) {
                Invoke-RestMethod -Uri "${target}?action=append&position=0" -Method PATCH -Headers $dfsHeaders `
                    -Body $bytes -ContentType 'application/octet-stream' -ErrorAction Stop | Out-Null
            }
            Invoke-RestMethod -Uri "${target}?action=flush&position=$($bytes.Length)" -Method PATCH -Headers $dfsHeaders -ErrorAction Stop | Out-Null
        }
        catch {
            $uploadFailures += "$($f.Name): $($_.Exception.Message)"
        }
    }
    if ($uploadFailures.Count -gt 0) {
        throw "Upload failed for $($uploadFailures.Count) file(s):`n  " + ($uploadFailures -join "`n  ")
    }
}
Write-Host "Uploaded $($files.Count) file(s) to Files/$FilesSubPath."

# --- 3. Trigger the loader notebook (optional) -----------------------------
if ($RunNotebook) {
    if (-not $notebookId) {
        Write-Warning ("items.$NotebookParamKey.id is not set in the parameters file. " +
            "Deploy the loader notebook and add its id, or run the notebook manually in the workspace. " +
            "Skipping automatic trigger.")
    } else {
        Write-Host "Triggering notebook $notebookId via Fabric REST..."
        $token = az account get-access-token --resource 'https://api.fabric.microsoft.com' --query accessToken -o tsv
        $uri = "https://api.fabric.microsoft.com/v1/workspaces/$workspaceId/items/$notebookId/jobs/instances?jobType=RunNotebook"
        $headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
        Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body '{}' | Out-Null
        Write-Host 'Notebook run submitted. Poll the workspace Monitoring hub for completion.'
    }
}

# --- 4. Suspend capacity ---------------------------------------------------
if ($SuspendAfter) {
    if (-not $capacityArmId) { throw 'capacity.armResourceId missing; cannot suspend.' }
    Write-Host "Suspending capacity $capacityArmId ..."
    az resource invoke-action --action suspend --ids $capacityArmId | Out-Null
    Write-Host 'Capacity suspend requested.'
}

Write-Host 'Done.'
