#!/usr/bin/env pwsh
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Bootstrap', 'Apps')]
    [string]$Phase,

    [string]$PortalImage,

    [string]$BffImage,

    [switch]$DeployAiServices,

    [switch]$DeployModelDeployments,

    [switch]$DeployAgentPlatform,

    # A capability host is immutable once created. Passing this is a one-way door.
    [switch]$AgentServiceManuallyValidated,

    [ValidateSet('offline', 'web_iq', 'web_search')]
    [string]$OnlineSearchMode = 'offline',

    [switch]$DeployBudget,

    [ValidateRange(1, 1000000)]
    [int]$MonthlyBudgetAmount = 250,

    [ValidateRange(0, 600)]
    [int]$RolePropagationDelaySeconds = 60,

    [string]$BootstrapDeploymentName = 'novasteelv3-bootstrap',

    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot 'Common.ps1')

$paths = Get-NovaSteelDemoPaths
Assert-NovaSteelTargetContext | Out-Null

if (-not (Test-Path -LiteralPath $paths.TemplateFile) -or -not (Test-Path -LiteralPath $paths.ParameterFile)) {
    throw 'The isolated NovaSteel v3 Bicep template or parameter file is missing.'
}

$commonParameters = @{
    deployAiServices = $DeployAiServices.IsPresent
    deployModelDeployments = $DeployModelDeployments.IsPresent
    deployAgentPlatform = $DeployAgentPlatform.IsPresent
    agentServiceManuallyValidated = $AgentServiceManuallyValidated.IsPresent
    onlineSearchMode = $OnlineSearchMode
    deployBudget = $DeployBudget.IsPresent
    monthlyBudgetAmount = $MonthlyBudgetAmount
}

if ($DeployAgentPlatform.IsPresent -and -not $DeployAiServices.IsPresent) {
    throw 'DeployAgentPlatform requires DeployAiServices: the Foundry project is a child of the AI Services account.'
}

if ($AgentServiceManuallyValidated.IsPresent -and -not $DeployAgentPlatform.IsPresent) {
    throw 'AgentServiceManuallyValidated requires DeployAgentPlatform: a capability host needs the project and its connections.'
}

if ($Phase -eq 'Bootstrap') {
    $target = "bootstrap platform resources in $script:NovaSteelResourceGroup on subscription $script:NovaSteelSubscriptionId"
    if (-not $Force -and -not $PSCmdlet.ShouldProcess($target, 'Create or update Azure resources')) {
        Write-Host 'Deployment cancelled.' -ForegroundColor Yellow
        return
    }

    $bootstrapParameters = @{} + $commonParameters
    $bootstrapParameters['deployApps'] = $false

    $deployment = Invoke-NovaSteelSubscriptionDeployment `
        -Name $BootstrapDeploymentName `
        -TemplateParameters $bootstrapParameters
    Write-NovaSteelDeploymentOutputs -Deployment $deployment

    # The management-group Modify policy `cosmosdb_publicnetwork_modify` overwrites
    # the template's `publicNetworkAccess: Enabled` on every write. The Agent
    # Service reaches its thread storage over the public endpoint here, so the
    # estate deploys clean and then fails at first agent use with
    # `cosmos_vnet_blocked`. Surface it now rather than leaving it to be
    # rediscovered. Reporting only: silently re-enabling it would defeat a
    # corporate security control, so the operator decides.
    if ($DeployAgentPlatform.IsPresent) {
        $cosmosName = [string]$deployment.properties.outputs.resourceNames.value.cosmosAccount
        if (-not [string]::IsNullOrWhiteSpace($cosmosName)) {
            $pna = az cosmosdb show --resource-group $script:NovaSteelResourceGroup --name $cosmosName --query 'publicNetworkAccess' --output tsv 2>$null
            if ($pna -ne 'Enabled') {
                Write-Warning @"
Cosmos DB '$cosmosName' has publicNetworkAccess='$pna'.
Azure Policy 'cosmosdb_publicnetwork_modify' reverts this on every deployment.
Until a policy exemption is granted, the Foundry Agent Service cannot reach its
thread storage and agent creation fails with 'cosmos_vnet_blocked'. To unblock:
  az cosmosdb update -g $script:NovaSteelResourceGroup -n $cosmosName --public-network-access ENABLED
See .azure/infra/README.md for the durable fix.
"@
            }
        }
    }

    Write-Host "`nBootstrap complete. Publish immutable images to the reported ACR, then run the Apps phase." -ForegroundColor Green
    return
}

if ([string]::IsNullOrWhiteSpace($PortalImage) -or [string]::IsNullOrWhiteSpace($BffImage)) {
    throw 'The Apps phase requires both -PortalImage and -BffImage as full ACR sha256-digest references.'
}

$bootstrapOutputs = Get-NovaSteelBootstrapOutputs -DeploymentName $BootstrapDeploymentName
$acrName = [string]$bootstrapOutputs.resourceNames.value.containerRegistry
$acrLoginServer = [string]$bootstrapOutputs.hostnames.value.containerRegistry
if ([string]::IsNullOrWhiteSpace($acrName) -or [string]::IsNullOrWhiteSpace($acrLoginServer)) {
    throw "Bootstrap deployment '$BootstrapDeploymentName' did not return the isolated ACR name and hostname."
}

Assert-NovaSteelImmutableAcrImage -Image $PortalImage -AcrName $acrName -AcrLoginServer $acrLoginServer
Assert-NovaSteelImmutableAcrImage -Image $BffImage -AcrName $acrName -AcrLoginServer $acrLoginServer

$target = "deploy portal and BFF Container Apps in $script:NovaSteelResourceGroup on subscription $script:NovaSteelSubscriptionId"
if (-not $Force -and -not $PSCmdlet.ShouldProcess($target, 'Create or update Azure resources')) {
    Write-Host 'Deployment cancelled.' -ForegroundColor Yellow
    return
}

if ($RolePropagationDelaySeconds -gt 0) {
    Write-Host "Waiting $RolePropagationDelaySeconds seconds for AcrPull assignments to propagate." -ForegroundColor Cyan
    Start-Sleep -Seconds $RolePropagationDelaySeconds
}

$bootstrapAppParameters = @{} + $commonParameters
$bootstrapAppParameters['deployApps'] = $true
$bootstrapAppParameters['portalImage'] = $PortalImage
$bootstrapAppParameters['bffImage'] = $BffImage
$bootstrapAppParameters['portalOrigin'] = 'https://placeholder.invalid'
$bootstrapAppParameters['portalBffBaseUrl'] = 'https://placeholder.invalid'

$initialAppsDeployment = Invoke-NovaSteelSubscriptionDeployment `
    -Name 'novasteelv3-apps-bootstrap' `
    -TemplateParameters $bootstrapAppParameters

$initialHostnames = $initialAppsDeployment.properties.outputs.hostnames.value
$portalFqdn = [string]$initialHostnames.portal
$bffFqdn = [string]$initialHostnames.bff
if ([string]::IsNullOrWhiteSpace($portalFqdn) -or [string]::IsNullOrWhiteSpace($bffFqdn)) {
    throw 'Container App deployment did not return both managed HTTPS hostnames.'
}

$configuredAppParameters = @{} + $bootstrapAppParameters
$configuredAppParameters['portalOrigin'] = "https://$portalFqdn"
$configuredAppParameters['portalBffBaseUrl'] = "https://$bffFqdn"

$configuredAppsDeployment = Invoke-NovaSteelSubscriptionDeployment `
    -Name 'novasteelv3-apps-configure' `
    -TemplateParameters $configuredAppParameters

Write-NovaSteelDeploymentOutputs -Deployment $configuredAppsDeployment
Write-Host "`nApps complete. Portal: https://$portalFqdn" -ForegroundColor Green
Write-Host "BFF:    https://$bffFqdn" -ForegroundColor Green
