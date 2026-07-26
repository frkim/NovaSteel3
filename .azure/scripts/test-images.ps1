<#
.SYNOPSIS
  Packaging smoke tests for the NovaSteel v3 portal and BFF images.

.DESCRIPTION
  Runs the built images locally and asserts the production contract:

  BFF (port 8080)
    * /health/live  and /health/ready return 200/ok
    * /v1/meta reports deterministic demo mode (demoMode=true, environment=demo)
    * CORS allows the env-provided portal origin and rejects others
    * the full deterministic simulator fixture (demo-full) is loaded

  Portal (port 8080)
    * / and /index.html return the SPA host page (probe path)
    * SPA fallback: an unknown deep route returns index.html
    * the React analytics MFE bundle is packaged under /analytics-mfe
    * .wasm assets are served as application/wasm
    * the runtime BFF URL is injected into appsettings.json from
      PORTAL_BFF_BASE_URL / BFF_BASE_URL

  Exits non-zero if any assertion fails.

.EXAMPLE
  pwsh .azure/scripts/test-images.ps1
.EXAMPLE
  pwsh .azure/scripts/test-images.ps1 -BffImage novasteelv3/bff:1.0.0-... -PortalImage novasteelv3/portal:1.0.0-...
#>
[CmdletBinding()]
param(
    [string]$BffImage = "novasteelv3/bff:local",
    [string]$PortalImage = "novasteelv3/portal:local",
    [int]$BffPort = 18080,
    [int]$PortalPort = 18081,
    [switch]$Keep
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$BffName = "ns-bff-smoke"
$PortalName = "ns-portal-smoke"
$PortalOrigin = "https://novasteelv3-portal.smoke.azurecontainerapps.io"
$BffUrl = "https://novasteelv3-bff.smoke.azurecontainerapps.io"

$script:Pass = 0
$script:Fail = 0

function Assert([string]$name, [bool]$ok, [string]$detail = "") {
    if ($ok) { Write-Host ("  [PASS] {0}" -f $name) -ForegroundColor Green; $script:Pass++ }
    else { Write-Host ("  [FAIL] {0} {1}" -f $name, $detail) -ForegroundColor Red; $script:Fail++ }
}

function Get-Http([string]$url, [hashtable]$headers = @{}, [string]$method = "GET") {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Method $method -Uri $url -Headers $headers -TimeoutSec 10
        return @{ ok = $true; code = [int]$r.StatusCode; body = $r.Content; headers = $r.Headers }
    } catch {
        # Under Set-StrictMode -Version Latest, connection failures (container not
        # ready yet) raise exceptions without a .Response property, so probe for it
        # safely before reading the HTTP status code.
        $code = 0
        $response = if ($_.Exception -and $_.Exception.PSObject.Properties['Response']) { $_.Exception.Response } else { $null }
        if ($response -and $response.PSObject.Properties['StatusCode'] -and $null -ne $response.StatusCode) {
            $code = [int]$response.StatusCode
        }
        return @{ ok = $false; code = $code; body = ""; headers = @{}; error = $_.Exception.Message }
    }
}

function Wait-Ready([string]$url, [int]$tries = 30) {
    for ($i = 0; $i -lt $tries; $i++) {
        $r = Get-Http $url
        if ($r.ok -and $r.code -eq 200) { return $true }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Remove-Containers {
    docker rm -f $BffName $PortalName 2>$null | Out-Null
}

Remove-Containers
try {
    Write-Host "Starting BFF container ($BffImage) ..." -ForegroundColor Cyan
    docker run -d --name $BffName -p "${BffPort}:8080" -e "BFF_CORS_ORIGINS=$PortalOrigin" $BffImage | Out-Null
    $bffBase = "http://localhost:$BffPort"
    if (-not (Wait-Ready "$bffBase/health/live")) { throw "BFF did not become healthy on $bffBase/health/live" }

    Write-Host "BFF assertions:" -ForegroundColor Cyan
    $live = Get-Http "$bffBase/health/live"
    Assert "/health/live 200 + status ok" ($live.code -eq 200 -and $live.body -match '"status"\s*:\s*"ok"') $live.body
    $ready = Get-Http "$bffBase/health/ready"
    Assert "/health/ready 200 + status ok" ($ready.code -eq 200 -and $ready.body -match '"status"\s*:\s*"ok"') $ready.body
    $meta = Get-Http "$bffBase/v1/meta"
    Assert "/v1/meta demoMode=true" ($meta.body -match '"demoMode"\s*:\s*true') $meta.body
    Assert "/v1/meta environment=demo" ($meta.body -match '"environment"\s*:\s*"demo"') $meta.body
    $cors = Get-Http "$bffBase/v1/meta" @{ Origin = $PortalOrigin }
    $allow = ($cors.headers['Access-Control-Allow-Origin'] -join ',')
    Assert "CORS allows configured portal origin" ($allow -eq $PortalOrigin) "got '$allow'"
    $badcors = Get-Http "$bffBase/v1/meta" @{ Origin = "https://evil.example.com" }
    $badallow = ($badcors.headers['Access-Control-Allow-Origin'] -join ',')
    Assert "CORS rejects unlisted origin" ([string]::IsNullOrEmpty($badallow)) "got '$badallow'"
    $src = (docker exec $BffName python -c "from bff_api.services import BffServices; from bff_api.config import Settings; print(BffServices.create(Settings.from_environment()).repository.source)" 2>$null)
    Assert "Deterministic demo fixture (demo-full) loaded" ("$src".Trim() -eq "simulator-fixture:demo-full") "source='$src'"

    Write-Host "Starting portal container ($PortalImage) ..." -ForegroundColor Cyan
    docker run -d --name $PortalName -p "${PortalPort}:8080" -e "PORTAL_BFF_BASE_URL=$BffUrl" $PortalImage | Out-Null
    $portalBase = "http://localhost:$PortalPort"
    if (-not (Wait-Ready "$portalBase/healthz")) { throw "Portal did not become ready on $portalBase/healthz" }

    Write-Host "Portal assertions:" -ForegroundColor Cyan
    $root = Get-Http "$portalBase/"
    Assert "/ 200 (probe path) serves SPA host" ($root.code -eq 200 -and $root.body -match '<div id="app"') "code=$($root.code)"
    $health = Get-Http "$portalBase/healthz"
    Assert "/healthz 200" ($health.code -eq 200) "code=$($health.code)"
    $deep = Get-Http "$portalBase/operations/energy"
    Assert "SPA fallback for deep route" ($deep.code -eq 200 -and $deep.body -match '<div id="app"') "code=$($deep.code)"
    $mfe = Get-Http "$portalBase/analytics-mfe/analytics-mfe.js"
    Assert "React MFE bundle packaged + served" ($mfe.code -eq 200 -and $mfe.body.Length -gt 100000) "code=$($mfe.code) len=$($mfe.body.Length)"
    $appsettings = Get-Http "$portalBase/appsettings.json"
    Assert "Runtime BFF URL injected into appsettings.json" ($appsettings.body -match [regex]::Escape($BffUrl)) $appsettings.body
    # .wasm MIME type
    $wasmList = (docker exec $PortalName sh -lc "ls -1 /usr/share/nginx/html/_framework/*.wasm 2>/dev/null | head -1")
    $wasmName = ([string]$wasmList).Trim().Split("`n")[0]
    if ($wasmName) {
        $leaf = Split-Path $wasmName -Leaf
        $wasm = Get-Http "$portalBase/_framework/$leaf" @{} "HEAD"
        $ct = ($wasm.headers['Content-Type'] -join ',')
        Assert ".wasm served as application/wasm" ($ct -eq "application/wasm") "got '$ct'"
    } else {
        Assert ".wasm asset present in _framework" $false "no .wasm found"
    }
}
finally {
    if (-not $Keep) { Remove-Containers } else { Write-Host "Leaving containers running (-Keep)." -ForegroundColor Yellow }
}

Write-Host ""
Write-Host ("Smoke tests: {0} passed, {1} failed." -f $script:Pass, $script:Fail) -ForegroundColor $(if ($script:Fail -eq 0) { "Green" } else { "Red" })
if ($script:Fail -gt 0) { exit 1 }
