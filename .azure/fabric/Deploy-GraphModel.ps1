<#
.SYNOPSIS
    Deploys the authored NovaSteel V3 GraphModel projection.

.DESCRIPTION
    Fabric creates the GraphModel automatically when the Ontology is first
    published, but it never re-projects it afterwards: the RefreshGraph job only
    reloads rows for node and edge tables that already exist. Adding an entity
    type or relationship type to the ontology therefore leaves the graph on its
    old schema, and every GQL query against a new label fails with
    "syntax error or access rule violation".

    This script closes that gap. Run tools/fabric/generate-graphmodel-definition.py
    to derive the projection from the ontology tree, then this script to publish
    it, then a RefreshGraph job to load the data.

    It only ever UPDATES an existing GraphModel - creation stays with the
    Ontology, so the item id and its auto-generated display name are preserved.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$WorkspaceId,
    [string]$SourceDirectory,
    [string]$GraphModelId,
    [switch]$Refresh,
    [switch]$WhatIfOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not $SourceDirectory) {
    $SourceDirectory = Join-Path $PSScriptRoot '..\..\fabric\items\onto-novasteelv3-graph.GraphModel'
}
$SourceDirectory = (Resolve-Path -LiteralPath $SourceDirectory).Path

function Get-FabricToken {
    $token = az account get-access-token --resource 'https://api.fabric.microsoft.com' --query accessToken -o tsv
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) {
        throw 'Unable to acquire a Fabric access token. Run az login first.'
    }
    return $token.Trim()
}

function Wait-FabricOperation {
    param([hashtable]$Headers, [string]$Location, [string]$What)

    for ($i = 0; $i -lt 240; $i++) {
        Start-Sleep -Seconds 5
        $status = Invoke-RestMethod -Uri $Location -Headers $Headers
        $state = if ($status.PSObject.Properties.Name -contains 'status') { $status.status } else { $null }
        if ($state -in @('Succeeded', 'Completed')) { return }
        if ($state -in @('Failed', 'Cancelled')) {
            throw "$What $state : $($status | ConvertTo-Json -Depth 6 -Compress)"
        }
    }
    throw "Timed out waiting for $What."
}

Write-Host "Reading graph projection from $SourceDirectory" -ForegroundColor Cyan

$parts = @()
foreach ($file in Get-ChildItem -LiteralPath $SourceDirectory -Recurse -File | Sort-Object FullName) {
    $relative = $file.FullName.Substring($SourceDirectory.Length).TrimStart('\', '/').Replace('\', '/')
    $parts += [ordered]@{
        path        = $relative
        payload     = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($file.FullName))
        payloadType = 'InlineBase64'
    }
    Write-Host "  part $relative"
}

foreach ($required in @('.platform', 'graphDefinition.json', 'graphType.json', 'dataSources.json')) {
    if (-not ($parts.path -contains $required)) { throw "$required is required." }
}

$graphType = Get-Content -LiteralPath (Join-Path $SourceDirectory 'graphType.json') -Raw | ConvertFrom-Json
Write-Host ("Projection contains {0} node types and {1} edge types." -f `
        $graphType.nodeTypes.Count, $graphType.edgeTypes.Count) -ForegroundColor Cyan

if ($WhatIfOnly) {
    Write-Host 'WhatIfOnly specified - not calling the Fabric API.' -ForegroundColor Yellow
    return
}

$token = Get-FabricToken
$headers = @{ Authorization = "Bearer $token" }

if (-not $GraphModelId) {
    $found = (Invoke-RestMethod -Uri "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items" `
            -Headers $headers).value | Where-Object { $_.type -eq 'GraphModel' }
    if (-not $found) { throw 'No GraphModel found in the workspace. Deploy the ontology first.' }
    if (@($found).Count -gt 1) {
        throw "Workspace has $(@($found).Count) GraphModels - pass -GraphModelId explicitly."
    }
    $GraphModelId = @($found)[0].id
}

Write-Host "Updating GraphModel $GraphModelId" -ForegroundColor Cyan
$body = @{ definition = @{ parts = $parts } } | ConvertTo-Json -Depth 10
$response = Invoke-WebRequest -Method POST `
    -Uri "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items/$GraphModelId/updateDefinition?updateMetadata=true" `
    -Headers $headers -ContentType 'application/json' -Body $body -SkipHttpErrorCheck

if ($response.StatusCode -ge 400) {
    throw "updateDefinition failed with HTTP $($response.StatusCode): $($response.Content)"
}
if ($response.StatusCode -eq 202) {
    $location = @($response.Headers['Location'])[0]
    if ($location) { Wait-FabricOperation -Headers $headers -Location $location -What 'updateDefinition' }
}

Write-Host "GraphModel definition published." -ForegroundColor Green

if ($Refresh) {
    # The projection defines the schema; the refresh job is what actually loads
    # the rows behind it, so a schema change is only visible to GQL after this.
    Write-Host 'Refreshing the graph...' -ForegroundColor Cyan
    $job = Invoke-WebRequest -Method POST `
        -Uri "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items/$GraphModelId/jobs/instances?jobType=RefreshGraph" `
        -Headers $headers -ContentType 'application/json' -Body '{}' -SkipHttpErrorCheck
    if ($job.StatusCode -ge 400) {
        throw "RefreshGraph failed with HTTP $($job.StatusCode): $($job.Content)"
    }
    $location = @($job.Headers['Location'])[0]
    if ($location) { Wait-FabricOperation -Headers $headers -Location $location -What 'RefreshGraph' }
    Write-Host 'Graph refreshed.' -ForegroundColor Green
}

[pscustomobject]@{
    GraphModelId = $GraphModelId
    NodeTypes    = $graphType.nodeTypes.Count
    EdgeTypes    = $graphType.edgeTypes.Count
}
