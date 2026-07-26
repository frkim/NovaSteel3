#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploys the NovaSteel infra Bicep templates for one environment.

.DESCRIPTION
    Requires an existing az CLI/OIDC session (developer `az login`, or the azure/login@v2 step
    using GitHub Workload Identity Federation per security-governance-and-threat-model.md §3.2 —
    `cd-infra.yml`). No secrets are read, written, or accepted by this script; it does not accept
    a client-secret parameter and will refuse to run if AZURE_CLIENT_SECRET/AZURE_CREDENTIALS are
    set in the environment, to fail closed against an accidental non-OIDC credential path.

    Requires explicit confirmation (-Confirm:$true is the PowerShell default for ShouldProcess;
    pass -Force to skip the interactive prompt in a non-interactive CI job that has already gated
    approval via a GitHub Environment reviewer).

.PARAMETER Environment
    dev | test | demo | prod.

.PARAMETER Force
    Skip the interactive confirmation prompt (use only when the calling pipeline/environment has
    already enforced a human-approval gate, e.g. cd-infra.yml's `environment: <env>` protection).

.EXAMPLE
    ./infra/scripts/deploy.ps1 -Environment dev
.EXAMPLE
    ./infra/scripts/deploy.ps1 -Environment prod -Force   # only from an approved cd-infra.yml run
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dev', 'test', 'demo', 'prod')]
    [string]$Environment,

    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($env:AZURE_CLIENT_SECRET -or $env:AZURE_CREDENTIALS) {
    throw "Refusing to deploy: AZURE_CLIENT_SECRET/AZURE_CREDENTIALS is set in the environment. This repository's convention is OIDC/Workload Identity Federation ONLY (security-governance-and-threat-model.md §3.2) — unset these variables and authenticate via 'az login' or azure/login@v2 without a client secret."
}

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

if ($Environment -eq 'prod') {
    Write-Host "PRODUCTION deployment — confirm all gates in deployment-topology.md §9 'Before non-synthetic pilot/production' and solution-architecture.md §13 step 8 have been signed before proceeding." -ForegroundColor Yellow
}

$target = "environment '$Environment' (subscription $($account.id))"
if (-not $Force -and -not $PSCmdlet.ShouldProcess($target, 'az deployment sub create')) {
    Write-Host "Aborted (no -Force and confirmation declined)." -ForegroundColor Yellow
    return
}

$deploymentLocation = 'swedencentral'

az deployment sub create `
    --name "ns-$Environment-deploy-$(Get-Date -Format 'yyyyMMddHHmmss')" `
    --location $deploymentLocation `
    --template-file $mainTemplate `
    --parameters $paramFile `
    --confirm-with-what-if

if ($LASTEXITCODE -ne 0) {
    throw "az deployment sub create failed for environment '$Environment'"
}
Write-Host "Deployment succeeded for '$Environment'." -ForegroundColor Green
