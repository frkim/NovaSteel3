#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Static + ARM validation of the NovaSteel infra Bicep templates for one environment.

.DESCRIPTION
    Runs, in order:
      1. `bicep build` on every .bicep file (fast, no Azure context required — catches syntax,
         type, and linter issues before any network call).
      2. `bicep build-params` on the target environment's .bicepparam file.
      3. `az deployment sub validate` against the live subscription in the CURRENT az/OIDC
         context (no secrets are read or written; this script never calls `az login` itself —
         it expects the caller — a developer's `az login`, or the `azure/login@v2` GitHub Action
         using Workload Identity Federation per security-governance-and-threat-model.md §3.2 —
         to have already established context).

.PARAMETER Environment
    dev | test | demo | prod — selects infra/bicep/parameters/<Environment>.bicepparam.

.PARAMETER SkipArmValidate
    Skip step 3 (useful for fully offline static-only validation, e.g. in a sandbox with no
    Azure credentials at all).

.EXAMPLE
    ./infra/scripts/validate.ps1 -Environment dev
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dev', 'test', 'demo', 'prod')]
    [string]$Environment,

    [switch]$SkipArmValidate
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..' '..')
$bicepDir = Join-Path $repoRoot 'infra' 'bicep'
$mainTemplate = Join-Path $bicepDir 'main.bicep'
$paramFile = Join-Path $bicepDir 'parameters' "$Environment.bicepparam"

if (-not (Test-Path $paramFile)) {
    throw "Parameter file not found: $paramFile"
}

Write-Host "== Step 1: bicep build (static validation of every module) ==" -ForegroundColor Cyan
$bicepFiles = Get-ChildItem -Path $bicepDir -Recurse -Filter '*.bicep'
$failures = @()
foreach ($file in $bicepFiles) {
    Write-Host "  building $($file.FullName.Substring($repoRoot.Path.Length + 1))"
    $output = az bicep build --file $file.FullName --stdout 2>&1
    if ($LASTEXITCODE -ne 0) {
        $failures += $file.FullName
        Write-Host $output -ForegroundColor Red
    }
}
if ($failures.Count -gt 0) {
    throw "bicep build failed for $($failures.Count) file(s): $($failures -join ', ')"
}
Write-Host "  OK: $($bicepFiles.Count) .bicep file(s) build cleanly." -ForegroundColor Green

Write-Host "== Step 2: bicep build-params ($Environment.bicepparam) ==" -ForegroundColor Cyan
az bicep build-params --file $paramFile --stdout | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "bicep build-params failed for $paramFile"
}
Write-Host "  OK" -ForegroundColor Green

if ($SkipArmValidate) {
    Write-Host "Skipping ARM 'what-if'-class validation (-SkipArmValidate). Static validation passed." -ForegroundColor Yellow
    return
}

Write-Host "== Step 3: az deployment sub validate ($Environment) ==" -ForegroundColor Cyan
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "  No active Azure CLI/OIDC session found. Skipping ARM validation — run 'az login' (developer) or ensure the azure/login@v2 OIDC step ran (CI) to enable this step." -ForegroundColor Yellow
    return
}
Write-Host "  Subscription: $($account.name) ($($account.id))"

# Location for the subscription-scope deployment call itself (metadata only — actual resource
# locations come from the template's `location` parameter, Sweden Central by default).
$deploymentLocation = 'swedencentral'

az deployment sub validate `
    --name "ns-$Environment-validate" `
    --location $deploymentLocation `
    --template-file $mainTemplate `
    --parameters $paramFile

if ($LASTEXITCODE -ne 0) {
    throw "az deployment sub validate failed for environment '$Environment'"
}
Write-Host "  OK: ARM validation passed for '$Environment'." -ForegroundColor Green
