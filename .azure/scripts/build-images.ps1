<#
.SYNOPSIS
  Build the NovaSteel v3 portal, BFF and operator-capture production container
  images locally with Docker Desktop + BuildKit, using immutable tags.

.DESCRIPTION
  The applications depend on sibling source trees, so the images are built with
  BuildKit named build contexts (the main context stays the app folder so its
  own .dockerignore is honoured):

    BFF     (services/bff-api)              + optimizer-worker, scoring-worker,
                                             knowledge, device-simulator
    Portal  (apps/portal-shell)             + analytics-mfe, contracts, reporoot
    Capture (apps/operator-capture-mfe)     + contracts, reporoot

  Python (pip) and .NET (NuGet) restores resolve ONLY from the Microsoft
  protected feeds with no public fallback (enforced in the Dockerfiles,
  pip.conf and NuGet.Config).

  This script does NOT push to a registry and does NOT deploy any Azure
  resource unless -Push is given with -Registry.

.PARAMETER Tag
  Explicit immutable tag. Default: 1.0.0-<utc-timestamp>-<git-sha>[-dirty].

.PARAMETER Registry
  Optional registry login server (e.g. novasteelv3acrXXXX.azurecr.io). When set,
  images are also tagged <registry>/novasteelv3/<name>:<tag>.

.PARAMETER Target
  bff | portal | capture | all (default all).

.PARAMETER Push
  Push the immutable image(s) to -Registry. Off by default (packaging only).

.EXAMPLE
  pwsh .azure/scripts/build-images.ps1
.EXAMPLE
  pwsh .azure/scripts/build-images.ps1 -Registry novasteelv3acr1234.azurecr.io -Push
#>
[CmdletBinding()]
param(
    [string]$Tag,
    [string]$Registry = "",
    [string]$RepoNamespace = "novasteelv3",
    [ValidateSet("bff", "portal", "capture", "all")]
    [string]$Target = "all",
    [string]$ViteBffBaseUrl = "",
    [string]$LocalAlias = "local",
    [switch]$Push,
    [switch]$NoLoad
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$StageDir = Join-Path $RepoRoot ".azure\docker\.buildstage"
$RepoRootStage = Join-Path $StageDir "reporoot"

function Get-ImmutableTag {
    $sha = "nogit"
    $dirty = ""
    try {
        $sha = (& git -C $RepoRoot rev-parse --short=12 HEAD 2>$null).Trim()
        if (-not $sha) { $sha = "nogit" }
        $status = & git -C $RepoRoot status --porcelain 2>$null
        if ($status) { $dirty = "-dirty" }
    } catch { $sha = "nogit" }
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddHHmmss")
    return "1.0.0-$stamp-$sha$dirty"
}

function Get-Ref([string]$name, [string]$tag, [string]$registry) {
    if ($registry) { return "$registry/$RepoNamespace/${name}:$tag" }
    return "$RepoNamespace/${name}:$tag"
}

function Invoke-Buildx {
    param([string[]]$BuildArgs, [string]$Name)
    Write-Host "==> docker buildx build $($BuildArgs -join ' ')" -ForegroundColor Cyan
    & docker buildx build @BuildArgs
    if ($LASTEXITCODE -ne 0) { throw "Build failed for image '$Name' (exit $LASTEXITCODE)." }
}

if (-not $Tag) { $Tag = Get-ImmutableTag }
if ($Push -and -not $Registry) { throw "-Push requires -Registry." }

$outputArg = if ($Push) { "--push" } elseif ($NoLoad) { $null } else { "--load" }

Write-Host "NovaSteel v3 image build" -ForegroundColor Green
Write-Host "  Repo root : $RepoRoot"
Write-Host "  Tag       : $Tag"
Write-Host "  Registry  : $(if ($Registry) { $Registry } else { '(local only)' })"
Write-Host "  Target    : $Target"
Write-Host "  Output    : $(if ($outputArg) { $outputArg } else { '(build cache only)' })"

$results = [ordered]@{}

Push-Location $RepoRoot
try {
    # Stage the minimal npm workspace root + NuGet config for the 'reporoot'
    # context, so the portal build never transfers the 160 MB root node_modules.
    if ($Target -in @("portal", "capture", "all")) {
        Remove-Item -Recurse -Force $StageDir -ErrorAction SilentlyContinue
        New-Item -ItemType Directory -Force -Path $RepoRootStage | Out-Null
        foreach ($f in @("package.json", "package-lock.json", ".npmrc", "NuGet.Config")) {
            Copy-Item (Join-Path $RepoRoot $f) $RepoRootStage
        }
    }

    if ($Target -in @("bff", "all")) {
        $ref = Get-Ref "bff" $Tag $Registry
        $buildxArgs = @(
            "--build-context", "optimizer-worker=services/optimizer-worker",
            "--build-context", "scoring-worker=services/scoring-worker",
            "--build-context", "knowledge=services/knowledge-orchestrator",
            "--build-context", "device-simulator=services/device-simulator",
            "-t", $ref
        )
        if (-not $Push -and -not $NoLoad -and $LocalAlias) { $buildxArgs += @("-t", (Get-Ref "bff" $LocalAlias "")) }
        if ($outputArg) { $buildxArgs += $outputArg }
        $buildxArgs += "services/bff-api"
        Invoke-Buildx -BuildArgs $buildxArgs -Name "bff"
        $results["bff"] = $ref
    }

    if ($Target -in @("portal", "all")) {
        $ref = Get-Ref "portal" $Tag $Registry
        $buildxArgs = @(
            "--build-context", "analytics-mfe=apps/analytics-mfe",
            "--build-context", "contracts=contracts",
            "--build-context", "reporoot=$RepoRootStage",
            "--build-arg", "VITE_BFF_BASE_URL=$ViteBffBaseUrl",
            "-t", $ref
        )
        if (-not $Push -and -not $NoLoad -and $LocalAlias) { $buildxArgs += @("-t", (Get-Ref "portal" $LocalAlias "")) }
        if ($outputArg) { $buildxArgs += $outputArg }
        $buildxArgs += "apps/portal-shell"
        Invoke-Buildx -BuildArgs $buildxArgs -Name "portal"
        $results["portal"] = $ref
    }

    if ($Target -in @("capture", "all")) {
        $ref = Get-Ref "capture" $Tag $Registry
        $buildxArgs = @(
            "--build-context", "contracts=contracts",
            "--build-context", "reporoot=$RepoRootStage",
            "-t", $ref
        )
        if (-not $Push -and -not $NoLoad -and $LocalAlias) { $buildxArgs += @("-t", (Get-Ref "capture" $LocalAlias "")) }
        if ($outputArg) { $buildxArgs += $outputArg }
        $buildxArgs += "apps/operator-capture-mfe"
        Invoke-Buildx -BuildArgs $buildxArgs -Name "capture"
        $results["capture"] = $ref
    }
}
finally {
    Remove-Item -Recurse -Force $StageDir -ErrorAction SilentlyContinue
    Pop-Location
}

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host ("{0,-8} {1,-60} {2}" -f "IMAGE", "REFERENCE", "LOCAL IMAGE ID (sha256 config digest)")
foreach ($name in $results.Keys) {
    $ref = $results[$name]
    $id = ""
    if (-not $Push) {
        try { $id = (& docker image inspect $ref --format '{{.Id}}' 2>$null) } catch { $id = "(n/a)" }
    } else {
        $id = "(pushed; use registry digest)"
    }
    Write-Host ("{0,-8} {1,-60} {2}" -f $name, $ref, $id)
}
Write-Host ""
Write-Host "Ports: portal -> 8080 (SPA), capture -> 8080 (SPA, /healthz), bff -> 8080 (/health/live, /health/ready)."
if (-not $Push) {
    Write-Host "Local convenience tags: $RepoNamespace/bff:$LocalAlias, $RepoNamespace/portal:$LocalAlias, $RepoNamespace/capture:$LocalAlias"
    Write-Host "Immutable deploy tag  : $Tag  (push later with -Registry -Push)"
}
