#!/usr/bin/env pwsh
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot 'Common.ps1')

$paths = Get-NovaSteelDemoPaths
foreach ($requiredPath in @($paths.TemplateFile, $paths.ParameterFile)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required infrastructure artifact not found: $requiredPath"
    }
}

$bicepFiles = Get-ChildItem -LiteralPath $paths.InfraRoot -Recurse -File -Filter '*.bicep' |
    Sort-Object FullName

foreach ($bicepFile in $bicepFiles) {
    Write-Host "Building $($bicepFile.FullName)" -ForegroundColor Cyan
    & az bicep build --file $bicepFile.FullName --stdout --only-show-errors | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Bicep build failed: $($bicepFile.FullName)"
    }
}

Write-Host "Building parameter file $($paths.ParameterFile)" -ForegroundColor Cyan
& az bicep build-params --file $paths.ParameterFile --stdout --only-show-errors | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Bicep parameter build failed: $($paths.ParameterFile)"
}

Write-Host "All NovaSteel v3 deployment Bicep files built successfully." -ForegroundColor Green
