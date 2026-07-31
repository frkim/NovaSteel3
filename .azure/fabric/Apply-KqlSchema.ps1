<#
.SYNOPSIS
    Applies the NovaSteel KQL database schema (tables, mappings, materialized views,
    functions) to the kql-novasteelv3-operations database.
#>
[CmdletBinding()]
param(
    [string]$ClusterUri     = 'https://trd-q10bnypm07cdfv120p.z8.kusto.fabric.microsoft.com',
    [string]$DatabaseName   = 'kql-novasteelv3-operations',
    [string]$SchemaFile     = '',
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot  = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $SchemaFile) {
    $SchemaFile = Join-Path $repoRoot 'fabric\items\kql-ns-operations.KQLDatabase\DatabaseSchema.kql'
}

if (-not (Test-Path -LiteralPath $SchemaFile -PathType Leaf)) {
    throw "Schema file not found: $SchemaFile"
}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Acquiring Kusto token..." -ForegroundColor Cyan
$token = & az account get-access-token --resource https://help.kusto.windows.net --query accessToken --output tsv
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) {
    throw 'Failed to acquire Kusto access token. Run az login first.'
}
$token = $token.Trim()

$retentionMap = @{
    '{{retention.telemetryHot}}'     = '90.00:00:00'
    '{{retention.alarmHot}}'         = '365.00:00:00'
    '{{retention.gatewayHealthHot}}' = '30.00:00:00'
    '{{retention.modelInferenceHot}}' = '90.00:00:00'
    '{{retention.quarantineHot}}'    = '30.00:00:00'
}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Reading schema: $SchemaFile" -ForegroundColor Cyan
$raw = Get-Content -LiteralPath $SchemaFile -Raw -Encoding UTF8
foreach ($key in $retentionMap.Keys) {
    $raw = $raw.Replace($key, $retentionMap[$key])
}

$unresolved = [regex]::Matches($raw, '\{\{[^{}]+\}\}') | ForEach-Object { $_.Value } | Sort-Object -Unique
if ($unresolved) {
    throw "Unresolved tokens in schema: $($unresolved -join ', ')"
}

# Split into individual commands. Commands start with a dot at the beginning of a line.
$blocks = [System.Collections.Generic.List[string]]::new()
$current = [System.Text.StringBuilder]::new()
foreach ($line in ($raw -split '\r?\n')) {
    $trimmed = $line.TrimEnd()
    # Skip pure comment lines
    if ($trimmed -match '^\s*//') { continue }
    # A new command starts with a dot at the beginning (after optional whitespace)
    if ($trimmed -match '^\s*\.' -and $current.Length -gt 0) {
        $cmd = $current.ToString().Trim()
        if ($cmd) { $blocks.Add($cmd) }
        $current = [System.Text.StringBuilder]::new()
    }
    if ($trimmed) {
        [void]$current.AppendLine($trimmed)
    }
}
if ($current.Length -gt 0) {
    $cmd = $current.ToString().Trim()
    if ($cmd) { $blocks.Add($cmd) }
}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Applying $($blocks.Count) schema commands to $DatabaseName..." -ForegroundColor Cyan

$headers = @{
    Authorization  = "Bearer $token"
    Accept         = 'application/json'
    'Content-Type' = 'application/json'
}
$mgmtUri = "$($ClusterUri.TrimEnd('/'))/v1/rest/mgmt"

$ok = 0
$skipped = 0
$failed = 0

foreach ($cmd in $blocks) {
    $preview = ($cmd -split '\n')[0]
    if ($preview.Length -gt 80) { $preview = $preview.Substring(0, 77) + '...' }
    Write-Host "  CMD: $preview"

    if ($WhatIf) {
        Write-Host "  [WhatIf] Would execute command" -ForegroundColor DarkGray
        $skipped++
        continue
    }

    $body = @{
        csl        = $cmd
        db         = $DatabaseName
        properties = @{ Options = @{ queryconsistency = 'weakconsistency' } }
    } | ConvertTo-Json -Depth 10 -Compress

    try {
        $response = Invoke-WebRequest -Uri $mgmtUri -Method POST -Headers $headers -Body $body `
            -ContentType 'application/json' -SkipHttpErrorCheck -ErrorAction Stop
        if ($response.StatusCode -ge 400) {
            $errContent = $response.Content
            if ($errContent.Length -gt 300) { $errContent = $errContent.Substring(0, 300) + '...' }
            Write-Warning "  WARN HTTP $($response.StatusCode): $errContent"
            $failed++
        }
        else {
            Write-Host "  OK  HTTP $($response.StatusCode)" -ForegroundColor Green
            $ok++
        }
    }
    catch {
        Write-Warning "  ERROR: $($_.Exception.Message)"
        $failed++
    }
}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Schema apply complete: $ok OK, $skipped skipped (WhatIf), $failed failed." -ForegroundColor $(if ($failed -eq 0) { 'Green' } else { 'Yellow' })
if ($failed -gt 0) {
    Write-Warning "Some schema commands failed. Check the KQL database is initialized and the token has admin rights."
}
