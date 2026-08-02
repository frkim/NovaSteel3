<#
.SYNOPSIS
    Deploys the authored NovaSteel V3 Fabric IQ Ontology item.

.DESCRIPTION
    Walks fabric/items/onto-novasteelv3.Ontology, base64-encodes every file into
    an item-definition part, and creates or updates the Ontology item in the
    target workspace. What is committed in git is exactly what is deployed.

    The ontology is the AI-facing semantic layer: it binds the gold serving
    tables (onto_*) to an enterprise vocabulary of Plant / Asset / Sensor /
    Grade so the data agent reasons in business terms instead of column names.

.NOTES
    Ontology item display names may only contain letters, numbers and
    underscores - hyphens are rejected by the service.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$WorkspaceId,
    [string]$SourceDirectory,
    [string]$DisplayName = 'onto_novasteelv3',
    [switch]$WhatIfOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not $SourceDirectory) {
    $SourceDirectory = Join-Path $PSScriptRoot '..\..\fabric\items\onto-novasteelv3.Ontology'
}
$SourceDirectory = (Resolve-Path -LiteralPath $SourceDirectory).Path

function Get-FabricToken {
    $token = az account get-access-token --resource 'https://api.fabric.microsoft.com' --query accessToken -o tsv
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) {
        throw 'Unable to acquire a Fabric access token. Run az login first.'
    }
    return $token.Trim()
}

function Invoke-FabricLro {
    param([string]$Token, [string]$Method, [string]$Uri, [string]$Body)

    $headers = @{ Authorization = "Bearer $Token" }
    $response = Invoke-WebRequest -Method $Method -Uri $Uri -Headers $headers `
        -ContentType 'application/json' -Body $Body -SkipHttpErrorCheck

    if ($response.StatusCode -ge 400) {
        throw "Fabric API $Method $Uri failed with $($response.StatusCode): $($response.Content)"
    }

    if ($response.StatusCode -ne 202) {
        if ([string]::IsNullOrWhiteSpace($response.Content)) { return $null }
        return $response.Content | ConvertFrom-Json
    }

    # Long running operation: poll until terminal.
    $operation = $response.Headers['Location']
    if (-not $operation) { return $null }
    $operation = @($operation)[0]

    for ($i = 0; $i -lt 120; $i++) {
        Start-Sleep -Seconds 5
        $status = Invoke-RestMethod -Uri $operation -Headers $headers
        if ($status.status -eq 'Succeeded') {
            try { return Invoke-RestMethod -Uri "$operation/result" -Headers $headers } catch { return $null }
        }
        if ($status.status -in @('Failed', 'Cancelled')) {
            throw "Fabric operation $($status.status): $($status | ConvertTo-Json -Depth 6 -Compress)"
        }
    }
    throw 'Timed out waiting for the Fabric long running operation to complete.'
}

Write-Host "Reading ontology definition from $SourceDirectory" -ForegroundColor Cyan

$parts = @()
foreach ($file in Get-ChildItem -LiteralPath $SourceDirectory -Recurse -File | Sort-Object FullName) {
    $relative = $file.FullName.Substring($SourceDirectory.Length).TrimStart('\', '/').Replace('\', '/')
    $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
    $parts += [ordered]@{
        path        = $relative
        payload     = [Convert]::ToBase64String($bytes)
        payloadType = 'InlineBase64'
    }
    Write-Host "  part $relative"
}

if (-not ($parts.path -contains 'definition.json')) { throw 'definition.json is required.' }
if (-not ($parts.path -contains '.platform')) { throw '.platform is required.' }

$entityTypes = @($parts.path | Where-Object { $_ -match '^EntityTypes/\d+/definition\.json$' }).Count
$bindings = @($parts.path | Where-Object { $_ -match '^EntityTypes/\d+/DataBindings/' }).Count
$relationships = @($parts.path | Where-Object { $_ -match '^RelationshipTypes/\d+/definition\.json$' }).Count
Write-Host "Ontology contains $entityTypes entity types, $bindings data bindings, $relationships relationship types." -ForegroundColor Cyan

if ($WhatIfOnly) {
    Write-Host 'WhatIfOnly specified - not calling the Fabric API.' -ForegroundColor Yellow
    return
}

$token = Get-FabricToken
$existing = (Invoke-RestMethod -Uri "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items" `
        -Headers @{ Authorization = "Bearer $token" }).value |
    Where-Object { $_.type -eq 'Ontology' -and $_.displayName -eq $DisplayName }

if ($existing) {
    $itemId = $existing.id
    Write-Host "Updating existing ontology $itemId" -ForegroundColor Cyan
    $body = @{ definition = @{ parts = $parts } } | ConvertTo-Json -Depth 10
    Invoke-FabricLro -Token $token -Method 'POST' `
        -Uri "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items/$itemId/updateDefinition?updateMetadata=true" `
        -Body $body | Out-Null
}
else {
    Write-Host "Creating ontology $DisplayName" -ForegroundColor Cyan
    $body = @{
        displayName = $DisplayName
        type        = 'Ontology'
        definition  = @{ parts = $parts }
    } | ConvertTo-Json -Depth 10
    $created = Invoke-FabricLro -Token $token -Method 'POST' `
        -Uri "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items" -Body $body
    if ($created -and $created.id) { $itemId = $created.id }
    else {
        $itemId = ((Invoke-RestMethod -Uri "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items" `
                    -Headers @{ Authorization = "Bearer $token" }).value |
                Where-Object { $_.type -eq 'Ontology' -and $_.displayName -eq $DisplayName }).id
    }
}

Write-Host "Ontology deployed: $itemId" -ForegroundColor Green
[pscustomobject]@{ OntologyId = $itemId; EntityTypes = $entityTypes; RelationshipTypes = $relationships }
