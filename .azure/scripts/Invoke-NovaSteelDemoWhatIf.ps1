#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$DeployApps,

    [string]$PortalImage = 'placeholder.invalid/novasteelv3/portal@sha256:0000000000000000000000000000000000000000000000000000000000000000',

    [string]$BffImage = 'placeholder.invalid/novasteelv3/bff@sha256:1111111111111111111111111111111111111111111111111111111111111111',

    [switch]$DeployAiServices,

    [switch]$DeployBudget,

    [ValidateRange(1, 1000000)]
    [int]$MonthlyBudgetAmount = 250,

    [string]$DeploymentName = 'novasteelv3-whatif'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot 'Common.ps1')

$paths = Get-NovaSteelDemoPaths
Assert-NovaSteelTargetContext | Out-Null

if (-not (Test-Path -LiteralPath $paths.TemplateFile) -or -not (Test-Path -LiteralPath $paths.ParameterFile)) {
    throw 'The isolated NovaSteel v3 Bicep template or parameter file is missing.'
}

$parameterFile = New-NovaSteelDemoParameterFile -Overrides @{
    deployApps = $DeployApps.IsPresent
    portalImage = $PortalImage
    bffImage = $BffImage
    deployAiServices = $DeployAiServices.IsPresent
    deployBudget = $DeployBudget.IsPresent
    monthlyBudgetAmount = $MonthlyBudgetAmount
}

try {
    $arguments = @(
        'deployment', 'sub', 'what-if',
        '--subscription', $script:NovaSteelSubscriptionId,
        '--name', $DeploymentName,
        '--location', $script:NovaSteelLocation,
        '--template-file', $paths.TemplateFile,
        '--parameters', $parameterFile,
        '--result-format', 'FullResourcePayloads',
        '--only-show-errors'
    )

    Write-Host "Running read-only what-if against Contoso Fx ($script:NovaSteelSubscriptionId)." -ForegroundColor Cyan
    & az @arguments
    if ($LASTEXITCODE -ne 0) {
        throw 'Azure deployment what-if failed.'
    }
} finally {
    Remove-Item -LiteralPath $parameterFile -Force -ErrorAction SilentlyContinue
}
