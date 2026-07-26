#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Grants the Bicep-provisioned GitHub OIDC managed identity (mi-ns-cicd-<env>, created by
    infra/bicep/modules/identity.bicep) the RBAC it needs on its environment's resource groups.

.DESCRIPTION
    This is the RECOMMENDED, LOWER-PRIVILEGE path for GitHub OIDC (security-governance-and-
    threat-model.md §3.2): a user-assigned managed identity + a
    Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials child resource
    are both plain ARM resources created by infra/bicep/modules/identity.bicep — creating them
    requires only Contributor on the target resource group, NOT any Microsoft Entra
    tenant-admin/Graph permission (unlike the app-registration alternative in
    setup-github-oidc-app-registration.ps1).

    What Bicep does NOT do for you (by design — RBAC role assignment scoped across resource
    groups belongs to a human decision, not a template default): grant that identity Contributor
    on the resource groups it needs to deploy into. This script performs that one-time grant.
    It requires the CALLER to already hold `Microsoft.Authorization/roleAssignments/write`
    (e.g. Owner or User Access Administrator) on the target resource groups — this is a
    privileged action and the script prompts for confirmation unless -Force is passed.

    Sequencing note (chicken-and-egg): the very first deployment of infra/bicep/main.bicep for a
    new environment must be run by a human/admin identity (or an already-privileged pipeline
    identity) BEFORE mi-ns-cicd-<env> exists. Once it exists, run this script once to hand off
    future deployments to the federated GitHub identity.

.PARAMETER Environment
    dev | test | demo | prod.

.PARAMETER Force
    Skip confirmation prompt.

.EXAMPLE
    ./infra/scripts/setup-github-oidc-managed-identity.ps1 -Environment dev
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

$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    throw "No active Azure CLI session. Run 'az login' as a human account holding Owner/User Access Administrator on the target resource groups."
}
Write-Host "Subscription: $($account.name) ($($account.id))" -ForegroundColor Cyan

$identityName = "mi-ns-cicd-$Environment"
$rgApps = "rg-ns-$Environment-apps"

Write-Host "Looking up identity '$identityName' in resource group '$rgApps'..."
$identity = az identity show --name $identityName --resource-group $rgApps 2>$null | ConvertFrom-Json
if (-not $identity) {
    throw "Identity '$identityName' not found in '$rgApps'. Deploy infra/bicep/main.bicep for '$Environment' first (with deployGitHubOidcIdentity=true, the default) so this identity exists."
}

$resourceGroups = @(
    "rg-ns-$Environment-hub"
    "rg-ns-$Environment-integration"
    "rg-ns-$Environment-apps"
    "rg-ns-$Environment-ai"
    "rg-ns-$Environment-fabric"
    "rg-ns-$Environment-monitoring"
)

Write-Host "This will grant '$identityName' Contributor on:" -ForegroundColor Yellow
$resourceGroups | ForEach-Object { Write-Host "  - $_" }
Write-Host "Never subscription-level Owner (security-governance-and-threat-model.md §3.2 rule 3)." -ForegroundColor Yellow

if (-not $Force -and -not $PSCmdlet.ShouldProcess("mi-ns-cicd-$Environment RBAC grant", 'az role assignment create (Contributor) x6 resource groups')) {
    Write-Host "Aborted (no -Force and confirmation declined)." -ForegroundColor Yellow
    return
}

foreach ($rg in $resourceGroups) {
    $scope = "/subscriptions/$($account.id)/resourceGroups/$rg"
    Write-Host "Granting Contributor on $scope ..."
    az role assignment create `
        --assignee-object-id $identity.principalId `
        --assignee-principal-type ServicePrincipal `
        --role Contributor `
        --scope $scope | Out-Null
}

Write-Host "Done. Configure the GitHub repository/environment variables with:" -ForegroundColor Green
Write-Host "  AZURE_CLIENT_ID       = $($identity.clientId)"
Write-Host "  AZURE_TENANT_ID       = $($account.tenantId)"
Write-Host "  AZURE_SUBSCRIPTION_ID = $($account.id)"
Write-Host "No client secret is generated or required — the federated identity credential trusting 'repo:<org>/<repo>:environment:$Environment' was already created by infra/bicep/modules/identity.bicep when githubOrg/githubRepo parameters were set."
