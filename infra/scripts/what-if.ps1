#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Runs `az deployment sub what-if` for one NovaSteel environment and prints/saves the diff.

.DESCRIPTION
    implementation-guide.md §10: "every PR touching infra/bicep runs az deployment ... what-if
    and attaches the diff to the PR; a human with infra ownership approves before merge."
    This script produces that diff. It never applies any change — see deploy.ps1 for that.
    Uses whatever az CLI/OIDC context is already active (developer `az login`, or the
    azure/login@v2 Workload Identity Federation step in cd-infra.yml) — no secrets are read,
    written, or required by this script.

.PARAMETER Environment
    dev | test | demo | prod.

.PARAMETER OutFile
    Optional path to also save the what-if result as text (e.g. for attaching to a PR comment).

.EXAMPLE
    ./infra/scripts/what-if.ps1 -Environment demo -OutFile whatif-demo.txt
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dev', 'test', 'demo', 'prod')]
    [string]$Environment,

    [string]$OutFile
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

$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    throw "No active Azure CLI/OIDC session. Run 'az login' (developer) or ensure azure/login@v2 (CI, Workload Identity Federation) ran before this script."
}
Write-Host "Subscription: $($account.name) ($($account.id))" -ForegroundColor Cyan
Write-Host "Environment : $Environment"

$deploymentLocation = 'swedencentral'

$whatIfArgs = @(
    'deployment', 'sub', 'what-if',
    '--name', "ns-$Environment-whatif",
    '--location', $deploymentLocation,
    '--template-file', $mainTemplate,
    '--parameters', $paramFile,
    '--result-format', 'FullResourcePayloads'
)

if ($OutFile) {
    az @whatIfArgs | Tee-Object -FilePath $OutFile
} else {
    az @whatIfArgs
}

if ($LASTEXITCODE -ne 0) {
    throw "az deployment sub what-if failed for environment '$Environment'"
}
