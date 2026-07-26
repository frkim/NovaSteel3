#!/usr/bin/env pwsh
<#
.SYNOPSIS
    TENANT-ADMIN-GATED alternative to setup-github-oidc-managed-identity.ps1: creates a Microsoft
    Entra App Registration + federated identity credential for GitHub OIDC, instead of a plain
    ARM user-assigned managed identity.

.DESCRIPTION
    *** THIS SCRIPT IS NOT RUN BY ANY AUTOMATED PIPELINE. IT IS A MANUAL, TENANT-ADMIN-GATED
        TEMPLATE ONLY. ***

    Prefer setup-github-oidc-managed-identity.ps1 (a plain ARM resource created by
    infra/bicep/modules/identity.bicep, requiring only resource-group Contributor). Use THIS
    script only if organizational policy specifically requires an App Registration / Service
    Principal identity instead of a user-assigned managed identity for GitHub OIDC (for example,
    a cross-tenant or non-Azure-hosted federation scenario that a managed identity cannot serve).

    Creating an Entra App Registration and its federated identity credential requires the
    Application Administrator or Cloud Application Administrator Entra role (a TENANT-level
    permission, not a subscription/resource-group RBAC role) — see
    security-governance-and-threat-model.md §3.2. This is exactly the class of tenant-admin
    action the azure-infrastructure task calls out as requiring an explicit human gate:
      1. This script performs NO Azure resource deployment by itself.
      2. It refuses to run without -Confirm (typed, not just -Force) and prints the exact Entra
         role required before making any Graph call.
      3. It never stores or prints a client secret — the whole point of federation is that none
         is created; if a future requirement needs a client secret instead, that is explicitly
         out of scope for this repository's "no static cloud credentials" policy (§3.2).

.PARAMETER Environment
    dev | test | demo | prod — used to build the app display name and the federated-credential
    subject `repo:<GithubOrg>/<GithubRepo>:environment:<Environment>`. Production MUST NOT use a
    wildcard branch/ref subject (§3.2).

.PARAMETER GithubOrg
    GitHub organization/user that owns the deploying repository.

.PARAMETER GithubRepo
    GitHub repository name (without org prefix).

.PARAMETER Confirm
    Must be passed with value $true to actually perform the Graph calls (az ad app create, az ad
    app federated-credential create). Without it, the script only prints what it WOULD do
    (dry run) — this is deliberately stricter than a simple -WhatIf so a tenant-admin action
    cannot be triggered by an unattended/scripted invocation.

.EXAMPLE
    # Dry run (default) — prints the plan, makes no Graph call:
    ./infra/scripts/setup-github-oidc-app-registration.ps1 -Environment prod -GithubOrg my-org -GithubRepo novasteel

.EXAMPLE
    # Actually create the app registration + federated credential (requires Application
    # Administrator / Cloud Application Administrator in Entra ID):
    ./infra/scripts/setup-github-oidc-app-registration.ps1 -Environment prod -GithubOrg my-org -GithubRepo novasteel -Confirm:$true
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dev', 'test', 'demo', 'prod')]
    [string]$Environment,

    [Parameter(Mandatory = $true)]
    [string]$GithubOrg,

    [Parameter(Mandatory = $true)]
    [string]$GithubRepo,

    [bool]$Confirm = $false
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$appName = "novasteel-cicd-$Environment"
$subject = "repo:${GithubOrg}/${GithubRepo}:environment:$Environment"
$federatedCredentialName = "github-$Environment"

Write-Host "=== TENANT-ADMIN GATE ===" -ForegroundColor Red
Write-Host "This script creates a Microsoft Entra App Registration ('$appName') and a federated"
Write-Host "identity credential (subject: $subject)."
Write-Host "Required Entra role: Application Administrator or Cloud Application Administrator."
Write-Host "This is a TENANT-level permission — confirm with your Entra ID tenant administrator"
Write-Host "before proceeding. RBAC (Contributor on a resource group) is NOT sufficient."
Write-Host ""

if (-not $Confirm) {
    Write-Host "DRY RUN (no -Confirm:`$true passed) — the following commands would run:" -ForegroundColor Yellow
    Write-Host "  az ad app create --display-name '$appName'"
    Write-Host "  az ad sp create --id <appId-from-above>"
    Write-Host "  az ad app federated-credential create --id <appId-from-above> --parameters '{...subject: $subject...}'"
    Write-Host "  az role assignment create --assignee <spId-from-above> --role Contributor --scope /subscriptions/<sub>/resourceGroups/rg-ns-$Environment-<rg>"
    Write-Host ""
    Write-Host "Re-run with -Confirm:`$true after tenant-admin approval to execute for real." -ForegroundColor Yellow
    return
}

$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    throw "No active Azure CLI session. Run 'az login' as an account holding Application Administrator / Cloud Application Administrator."
}
Write-Host "Subscription: $($account.name) ($($account.id))" -ForegroundColor Cyan
Write-Host "Tenant      : $($account.tenantId)"

Write-Host "Creating app registration '$appName'..."
$app = az ad app create --display-name $appName | ConvertFrom-Json
Write-Host "  appId: $($app.appId)"

Write-Host "Creating service principal for app..."
$sp = az ad sp create --id $app.appId | ConvertFrom-Json
Write-Host "  spId: $($sp.id)"

Write-Host "Adding federated identity credential (subject: $subject)..."
$federatedCredentialJson = @{
    name        = $federatedCredentialName
    issuer      = 'https://token.actions.githubusercontent.com'
    subject     = $subject
    description = "NovaSteel GitHub OIDC — $Environment"
    audiences   = @('api://AzureADTokenExchange')
} | ConvertTo-Json -Compress

# Written to a temp file (not a secret — issuer/subject/audiences are all public values) because
# az ad app federated-credential create expects a JSON file/string parameter, not inline flags.
$tempFile = New-TemporaryFile
try {
    Set-Content -Path $tempFile -Value $federatedCredentialJson
    az ad app federated-credential create --id $app.appId --parameters $tempFile
} finally {
    Remove-Item $tempFile -ErrorAction SilentlyContinue
}

Write-Host "Done. No client secret was created — configure the GitHub repository/environment with:" -ForegroundColor Green
Write-Host "  AZURE_CLIENT_ID       = $($app.appId)"
Write-Host "  AZURE_TENANT_ID       = $($account.tenantId)"
Write-Host "  AZURE_SUBSCRIPTION_ID = $($account.id)"
Write-Host ""
Write-Host "Next: grant '$appName' least-privilege RBAC (Contributor scoped to rg-ns-$Environment-* resource groups, never subscription Owner) — this still requires a separate RBAC-privileged (Owner/User Access Administrator) run, e.g. by adapting setup-github-oidc-managed-identity.ps1's role-assignment loop to this service principal's object ID ($($sp.id))." -ForegroundColor Yellow
