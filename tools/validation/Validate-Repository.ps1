#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Runs the feasible NovaSteel validation suite and writes an evidence manifest.

.DESCRIPTION
    This is the Windows-friendly local equivalent of the GitHub Actions gates.
    It never authenticates to Azure and never deploys resources. By default it
    uses already-restored dependencies; -RestoreDependencies performs protected
    Python/NuGet restores and an npm ci only when NPM_CONFIG_REGISTRY is set.

.EXAMPLE
    pwsh .\tools\validation\Validate-Repository.ps1

.EXAMPLE
    $env:NPM_CONFIG_REGISTRY = 'https://<approved-feed>'
    pwsh .\tools\validation\Validate-Repository.ps1 -RestoreDependencies -Strict
#>
[CmdletBinding()]
param(
    [ValidateSet(
        'all',
        'protected-feeds',
        'contract',
        'simulator',
        'backend',
        'knowledge',
        'frontend',
        'portal',
        'infra',
        'fabric',
        'presentation',
        'security',
        'sbom'
    )]
    [string[]]$Suite = @('all'),

    [string]$EvidencePath = '',

    [switch]$RestoreDependencies,

    [switch]$Strict
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path
$allSuites = @(
    'protected-feeds',
    'contract',
    'simulator',
    'backend',
    'knowledge',
    'frontend',
    'portal',
    'infra',
    'fabric',
    'presentation',
    'security',
    'sbom'
)
$selectedSuites = if ($Suite -contains 'all') {
    $allSuites
} else {
    @($Suite | Select-Object -Unique)
}

if ([string]::IsNullOrWhiteSpace($EvidencePath)) {
    $EvidencePath = Join-Path $repoRoot 'artifacts\validation\evidence-manifest.json'
} elseif (-not [IO.Path]::IsPathRooted($EvidencePath)) {
    $EvidencePath = Join-Path $repoRoot $EvidencePath
}
$evidenceDirectory = Split-Path -Parent $EvidencePath
New-Item -ItemType Directory -Force -Path $evidenceDirectory | Out-Null

$records = [System.Collections.Generic.List[object]]::new()
$script:hasFailures = $false
$script:hasStrictSkips = $false

function Get-ToolPath {
    param([Parameter(Mandatory)][string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        return $null
    }
    return $command.Source
}

function Get-ValidationPython {
    if ($env:NOVASTEEL_PYTHON -and (Test-Path -LiteralPath $env:NOVASTEEL_PYTHON)) {
        return (Resolve-Path -LiteralPath $env:NOVASTEEL_PYTHON).Path
    }

    $windowsVenv = Join-Path $repoRoot 'services\bff-api\.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $windowsVenv) {
        return $windowsVenv
    }
    $unixVenv = Join-Path $repoRoot 'services/bff-api/.venv/bin/python'
    if (Test-Path -LiteralPath $unixVenv) {
        return $unixVenv
    }
    return Get-ToolPath -Name 'python'
}

function Get-NpmPath {
    if ($IsWindows) {
        $windowsNpm = Get-ToolPath -Name 'npm.cmd'
        if ($windowsNpm) {
            return $windowsNpm
        }
    }
    return Get-ToolPath -Name 'npm'
}

function Add-SkippedCheck {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Reason
    )

    $records.Add([pscustomobject]@{
        name            = $Name
        status          = 'SKIPPED'
        exitCode        = $null
        durationSeconds = 0
        command         = ''
        log             = ''
        reason          = $Reason
    })
    Write-Host "SKIPPED: $Name — $Reason" -ForegroundColor Yellow
    if ($Strict) {
        $script:hasStrictSkips = $true
    }
}

function Invoke-ValidationCommand {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Executable,
        [string[]]$Arguments = @()
    )

    $safeName = $Name -replace '[^A-Za-z0-9_.-]', '-'
    $logPath = Join-Path $evidenceDirectory "$safeName.log"
    $started = [DateTimeOffset]::UtcNow
    $exitCode = 1
    $errorMessage = ''

    Write-Host "== $Name ==" -ForegroundColor Cyan
    Write-Host "$Executable $($Arguments -join ' ')"
    try {
        $global:LASTEXITCODE = 0
        & $Executable @Arguments *> $logPath
        $exitCode = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
    } catch {
        $errorMessage = $_.Exception.Message
        $errorMessage | Set-Content -LiteralPath $logPath -Encoding utf8
        $exitCode = 1
    }
    $duration = [Math]::Round(([DateTimeOffset]::UtcNow - $started).TotalSeconds, 3)

    if (Test-Path -LiteralPath $logPath) {
        Get-Content -LiteralPath $logPath | Write-Host
    }
    if ($errorMessage) {
        Write-Host $errorMessage -ForegroundColor Red
    }

    $status = if ($exitCode -eq 0) { 'PASS' } else { 'FAIL' }
    $records.Add([pscustomobject]@{
        name            = $Name
        status          = $status
        exitCode        = $exitCode
        durationSeconds = $duration
        command         = "$Executable $($Arguments -join ' ')"
        log             = (Resolve-Path -LiteralPath $logPath -ErrorAction SilentlyContinue).Path
        reason          = $errorMessage
    })
    if ($exitCode -ne 0) {
        $script:hasFailures = $true
        Write-Host "FAILED: $Name" -ForegroundColor Red
    } else {
        Write-Host "PASSED: $Name" -ForegroundColor Green
    }
}

function Set-PythonSourcePath {
    $sourceDirectories = @(
        'services\bff-api\src',
        'services\optimizer-worker\src',
        'services\scoring-worker\src',
        'services\ingest-relay\src',
        'services\knowledge-orchestrator\src',
        '.'
    ) | ForEach-Object { (Resolve-Path (Join-Path $repoRoot $_)).Path }
    $env:PYTHONPATH = $sourceDirectories -join [IO.Path]::PathSeparator
}

function Set-ProtectedPythonEnvironment {
    $env:PIP_CONFIG_FILE = Join-Path $repoRoot 'pip.conf'
    $env:PIP_INDEX_URL = 'https://packagefeedproxy.microsoft.io/pypi/simple'
    $env:PIP_EXTRA_INDEX_URL = ''
    $env:PIP_NO_INPUT = '1'
}

function Test-ApprovedNpmRegistry {
    param([string]$Registry)

    if ([string]::IsNullOrWhiteSpace($Registry)) {
        return $false
    }
    $uri = $null
    if (-not [Uri]::TryCreate($Registry, [UriKind]::Absolute, [ref]$uri)) {
        return $false
    }
    return $uri.Scheme -eq 'https' -and $uri.Host -notin @(
        'registry.npmjs.org',
        'registry.yarnpkg.com'
    )
}

function Save-EvidenceManifest {
    $git = Get-ToolPath -Name 'git'
    $commit = 'unavailable'
    if ($git) {
        try {
            $commit = (& $git -C $repoRoot rev-parse HEAD 2>$null).Trim()
            if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($commit)) {
                $commit = 'unavailable'
            }
        } catch {
            $commit = 'unavailable'
        }
    }

    $manifest = [ordered]@{
        status         = if ($script:hasFailures -or $script:hasStrictSkips) { 'FAIL' } else { 'PASS' }
        generatedAtUtc = [DateTimeOffset]::UtcNow.ToString('o')
        repositoryRoot = $repoRoot
        commit         = $commit
        suites         = $selectedSuites
        strict         = [bool]$Strict
        restore        = [bool]$RestoreDependencies
        checks         = $records.ToArray()
    }
    $manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $EvidencePath -Encoding utf8
    Write-Host "Evidence manifest: $EvidencePath"
}

Push-Location $repoRoot
try {
    $python = Get-ValidationPython
    $npm = Get-NpmPath
    $dotnet = Get-ToolPath -Name 'dotnet'
    $pwsh = Get-ToolPath -Name 'pwsh'
    $az = Get-ToolPath -Name 'az'

    if ($python) {
        Set-PythonSourcePath
    }

    foreach ($currentSuite in $selectedSuites) {
        switch ($currentSuite) {
            'protected-feeds' {
                if ($python) {
                    Invoke-ValidationCommand -Name 'verify-protected-feeds' -Executable $python -Arguments @(
                        'tools/validation/verify_protected_feeds.py',
                        '--root',
                        $repoRoot,
                        '--json',
                        (Join-Path $evidenceDirectory 'protected-feeds.json')
                    )
                } else {
                    Add-SkippedCheck -Name 'verify-protected-feeds' -Reason 'Python was not found.'
                }
            }
            'contract' {
                if ($python) {
                    Invoke-ValidationCommand -Name 'contract-tests' -Executable $python -Arguments @(
                        '-m', 'pytest', 'tests/contract', 'services/bff-api/tests/test_contracts.py', '-q'
                    )
                } else {
                    Add-SkippedCheck -Name 'contract-tests' -Reason 'Python was not found.'
                }
            }
            'simulator' {
                if ($python) {
                    Invoke-ValidationCommand -Name 'simulator-tests' -Executable $python -Arguments @(
                        '-m', 'pytest', 'tests/simulator', '-q'
                    )
                } else {
                    Add-SkippedCheck -Name 'simulator-tests' -Reason 'Python was not found.'
                }
            }
            'backend' {
                if ($python) {
                    if ($RestoreDependencies) {
                        Set-ProtectedPythonEnvironment
                        Invoke-ValidationCommand -Name 'restore-python-test-dependencies' -Executable $python -Arguments @(
                            '-m', 'pip', 'install', '--disable-pip-version-check',
                            '-r', 'services/bff-api/requirements.txt'
                        )
                    }
                    Invoke-ValidationCommand -Name 'backend-and-integration-tests' -Executable $python -Arguments @(
                        '-m', 'pytest',
                        'services/bff-api/tests',
                        'tests/backend',
                        'tests/integration',
                        'tests/e2e',
                        '-q'
                    )
                } else {
                    Add-SkippedCheck -Name 'backend-and-integration-tests' -Reason 'Python was not found.'
                }
            }
            'knowledge' {
                if ($python) {
                    Invoke-ValidationCommand -Name 'knowledge-workflow-tests' -Executable $python -Arguments @(
                        '-m', 'pytest', 'tests/knowledge', '-q'
                    )
                } else {
                    Add-SkippedCheck -Name 'knowledge-workflow-tests' -Reason 'Python was not found.'
                }
            }
            'frontend' {
                if (-not $npm) {
                    Add-SkippedCheck -Name 'frontend-tests' -Reason 'npm was not found.'
                    break
                }
                if ($RestoreDependencies) {
                    if (-not (Test-ApprovedNpmRegistry -Registry $env:NPM_CONFIG_REGISTRY)) {
                        Add-SkippedCheck -Name 'restore-npm-dependencies' -Reason (
                            'A non-public HTTPS NPM_CONFIG_REGISTRY is required to restore dependencies.'
                        )
                    } else {
                        Invoke-ValidationCommand -Name 'restore-npm-dependencies' -Executable $npm -Arguments @(
                            'ci', '--ignore-scripts'
                        )
                    }
                }
                Invoke-ValidationCommand -Name 'frontend-lint' -Executable $npm -Arguments @(
                    'run', 'lint:frontend'
                )
                Invoke-ValidationCommand -Name 'frontend-tests' -Executable $npm -Arguments @(
                    'run', 'test:frontend'
                )
                Invoke-ValidationCommand -Name 'frontend-build' -Executable $npm -Arguments @(
                    'run', 'build:analytics'
                )
                if (-not (Test-ApprovedNpmRegistry -Registry $env:NPM_CONFIG_REGISTRY)) {
                    Add-SkippedCheck -Name 'npm-vulnerability-audit' -Reason (
                        'A non-public HTTPS NPM_CONFIG_REGISTRY is required to audit dependencies.'
                    )
                } else {
                    Invoke-ValidationCommand -Name 'npm-vulnerability-audit' -Executable $npm -Arguments @(
                        'audit',
                        '--omit=dev',
                        '--audit-level=high',
                        '--registry',
                        $env:NPM_CONFIG_REGISTRY,
                        '--json'
                    )
                }
            }
            'portal' {
                if (-not $dotnet) {
                    Add-SkippedCheck -Name 'portal-build' -Reason 'dotnet was not found.'
                    break
                }
                Invoke-ValidationCommand -Name 'portal-protected-restore' -Executable $dotnet -Arguments @(
                    'restore',
                    'apps/portal-shell/PortalShell.csproj',
                    '--configfile',
                    'NuGet.Config',
                    '--locked-mode'
                )
                Invoke-ValidationCommand -Name 'portal-build' -Executable $dotnet -Arguments @(
                    'build',
                    'apps/portal-shell/PortalShell.csproj',
                    '--no-restore',
                    '--configuration',
                    'Release'
                )
                if ($python) {
                    $nugetReport = Join-Path $evidenceDirectory 'portal-vulnerability-report.log'
                    Invoke-ValidationCommand -Name 'portal-vulnerability-report' -Executable $dotnet -Arguments @(
                        'package',
                        'list',
                        '--project',
                        'apps/portal-shell/PortalShell.csproj',
                        '--vulnerable',
                        '--include-transitive',
                        '--format',
                        'json',
                        '--config',
                        'NuGet.Config',
                        '--no-restore'
                    )
                    if (Test-Path -LiteralPath $nugetReport) {
                        Invoke-ValidationCommand -Name 'portal-vulnerability-gate' -Executable $python -Arguments @(
                            'tools/validation/check_dotnet_vulnerabilities.py',
                            '--input',
                            $nugetReport
                        )
                    }
                } else {
                    Add-SkippedCheck -Name 'portal-vulnerability-gate' -Reason (
                        'Python was not found to evaluate the NuGet vulnerability report.'
                    )
                }
            }
            'infra' {
                if ($python) {
                    if ($az) {
                        & $az bicep version *> $null
                        if ($LASTEXITCODE -ne 0) {
                            Invoke-ValidationCommand -Name 'install-bicep-cli' -Executable $az -Arguments @(
                                'bicep', 'install'
                            )
                        }
                    }
                    Invoke-ValidationCommand -Name 'infra-tests' -Executable $python -Arguments @(
                        '-m', 'pytest', 'tests/infra', '-q'
                    )
                } else {
                    Add-SkippedCheck -Name 'infra-tests' -Reason 'Python was not found.'
                }
                if ($pwsh -and $az) {
                    Invoke-ValidationCommand -Name 'infra-static-validation' -Executable $pwsh -Arguments @(
                        '-NoProfile', '-NonInteractive', '-File',
                        'infra/scripts/validate.ps1', '-Environment', 'dev', '-SkipArmValidate'
                    )
                } else {
                    Add-SkippedCheck -Name 'infra-static-validation' -Reason (
                        'pwsh and Azure CLI are both required for Bicep validation.'
                    )
                }
            }
            'fabric' {
                if ($pwsh) {
                    Invoke-ValidationCommand -Name 'fabric-local-validator' -Executable $pwsh -Arguments @(
                        '-NoProfile', '-NonInteractive', '-File',
                        'fabric/scripts/Test-FabricAssetsLocal.ps1'
                    )
                } else {
                    Add-SkippedCheck -Name 'fabric-local-validator' -Reason 'pwsh was not found.'
                }
            }
            'presentation' {
                if ($python) {
                    Invoke-ValidationCommand -Name 'presentation-package-validator' -Executable $python -Arguments @(
                        'tools/validation/validate_pptx.py',
                        '--presentation',
                        'docs/presentation/NovaSteel-Oral-Defense.pptx',
                        '--json',
                        (Join-Path $evidenceDirectory 'presentation.json')
                    )
                } else {
                    Add-SkippedCheck -Name 'presentation-package-validator' -Reason 'Python was not found.'
                }
            }
            'security' {
                if ($python) {
                    Invoke-ValidationCommand -Name 'security-gates' -Executable $python -Arguments @(
                        'tools/validation/security_scan.py',
                        '--root',
                        $repoRoot,
                        '--json',
                        (Join-Path $evidenceDirectory 'security.json')
                    )
                    Invoke-ValidationCommand -Name 'python-dependency-integrity' -Executable $python -Arguments @(
                        '-m', 'pip', 'check'
                    )
                } else {
                    Add-SkippedCheck -Name 'security-gates' -Reason 'Python was not found.'
                }
            }
            'sbom' {
                if ($python) {
                    Invoke-ValidationCommand -Name 'generate-sbom' -Executable $python -Arguments @(
                        'tools/validation/generate_sbom.py',
                        '--root',
                        $repoRoot,
                        '--output',
                        (Join-Path $evidenceDirectory 'novasteel.sbom.cdx.json')
                    )
                } else {
                    Add-SkippedCheck -Name 'generate-sbom' -Reason 'Python was not found.'
                }
            }
        }
    }
} finally {
    Save-EvidenceManifest
    Pop-Location
}

if ($script:hasFailures -or $script:hasStrictSkips) {
    exit 1
}
