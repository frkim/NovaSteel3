[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ParameterFile,

    [Parameter(Mandatory)]
    [string]$StateFile,

    [string]$CatalogFile = '',

    [switch]$Deep,

    [switch]$KqlSmoke,

    [switch]$UseFabricCli
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$fabricRoot = Split-Path -Parent $PSScriptRoot
if (-not $CatalogFile) {
    $CatalogFile = Join-Path $fabricRoot 'catalog\fabric-items.json'
}
foreach ($pathVariable in @('ParameterFile', 'StateFile', 'CatalogFile')) {
    $value = Get-Variable -Name $pathVariable -ValueOnly
    if (-not [IO.Path]::IsPathRooted($value)) {
        Set-Variable -Name $pathVariable -Value (Join-Path (Get-Location) $value)
    }
}

Import-Module (Join-Path $PSScriptRoot 'FabricDeployment.psm1') -Force
Assert-NsParameterFileHasNoSecrets -Path $ParameterFile

$parameters = Get-Content -LiteralPath $ParameterFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100
$state = Get-Content -LiteralPath $StateFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -AsHashtable -Depth 100
$catalog = Get-Content -LiteralPath $CatalogFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100

if ([string]$parameters.environment -ne [string]$state.environment) {
    throw 'State file and parameter file target different environments.'
}

$token = Get-NsAccessToken `
    -Resource 'https://api.fabric.microsoft.com' `
    -AuthenticationMode ([string]$parameters.authentication.mode) `
    -ManagedIdentityClientId ([string]$parameters.authentication.managedIdentityClientId)

$checks = [System.Collections.Generic.List[object]]::new()
$failures = [System.Collections.Generic.List[string]]::new()

function Add-Check {
    param([string]$Key, [string]$Status, [string]$Detail)
    $checks.Add([pscustomobject]@{
        key    = $Key
        status = $Status
        detail = $Detail
    })
    if ($Status -eq 'FAIL') {
        $failures.Add("${Key}: $Detail")
    }
}

foreach ($workspaceSpec in $catalog.workspaces) {
    $key = [string]$workspaceSpec.key
    if (-not $state.workspaces.Contains($key)) {
        Add-Check -Key "workspace:$key" -Status FAIL -Detail 'Missing from state file.'
        continue
    }
    $expected = [string]$state.workspaces[$key].displayName
    $actual = Find-NsWorkspace -DisplayName $expected -Token $token
    if ($null -eq $actual) {
        Add-Check -Key "workspace:$key" -Status FAIL -Detail "Workspace '$expected' not found."
    }
    elseif ([string]$actual.id -ne [string]$state.workspaces[$key].id) {
        Add-Check -Key "workspace:$key" -Status FAIL -Detail 'Workspace ID differs from deployment state.'
    }
    else {
        Add-Check -Key "workspace:$key" -Status PASS -Detail ([string]$actual.id)
    }
}

foreach ($itemSpec in $catalog.items) {
    $optionProperty = $parameters.deploymentOptions.PSObject.Properties[[string]$itemSpec.deploymentOption]
    $enabled = $null -eq $optionProperty -or [bool]$optionProperty.Value
    if (-not $enabled) {
        Add-Check -Key "item:$($itemSpec.key)" -Status SKIP -Detail "$($itemSpec.deploymentOption)=false"
        continue
    }
    if ($itemSpec.bindingGate) {
        $gate = $parameters.deploymentOptions.PSObject.Properties[[string]$itemSpec.bindingGate]
        if ($null -eq $gate -or -not [bool]$gate.Value) {
            Add-Check -Key "item:$($itemSpec.key)" -Status GATE -Detail "$($itemSpec.bindingGate)=false"
            continue
        }
    }
    if (-not $state.items.Contains([string]$itemSpec.key)) {
        Add-Check -Key "item:$($itemSpec.key)" -Status FAIL -Detail 'Missing from state file.'
        continue
    }

    $itemState = $state.items[[string]$itemSpec.key]
    $workspaceId = [string]$state.workspaces[[string]$itemSpec.workspaceKey].id
    $actual = Find-NsItem `
        -WorkspaceId $workspaceId `
        -DisplayName ([string]$itemState.displayName) `
        -Type ([string]$itemSpec.type) `
        -Token $token
    if ($null -eq $actual) {
        Add-Check -Key "item:$($itemSpec.key)" -Status FAIL -Detail 'Item not found.'
        continue
    }
    if ([string]$actual.id -ne [string]$itemState.id) {
        Add-Check -Key "item:$($itemSpec.key)" -Status FAIL -Detail 'Item ID differs from deployment state.'
        continue
    }

    if ($Deep -and -not [bool]$itemSpec.createWithoutDefinition) {
        try {
            $definition = Invoke-NsFabricRequest `
                -Method POST `
                -Path "/workspaces/$workspaceId/items/$($actual.id)/getDefinition" `
                -Token $token `
                -Body @{}
            $actualParts = @()
            if ($definition -and
                $definition.PSObject.Properties.Name -contains 'definition') {
                $actualParts = @($definition.definition.parts | ForEach-Object { [string]$_.path })
            }
            elseif ($definition -and
                $definition.PSObject.Properties.Name -contains 'parts') {
                $actualParts = @($definition.parts | ForEach-Object { [string]$_.path })
            }
            $missingParts = @(
                $itemSpec.definitionParts |
                    Where-Object { [string]$_ -notin $actualParts }
            )
            if ($missingParts.Count -gt 0) {
                Add-Check -Key "definition:$($itemSpec.key)" -Status FAIL -Detail "Missing parts: $($missingParts -join ', ')"
            }
            else {
                Add-Check -Key "definition:$($itemSpec.key)" -Status PASS -Detail "$($actualParts.Count) definition parts."
            }
        }
        catch {
            Add-Check -Key "definition:$($itemSpec.key)" -Status FAIL -Detail $_.Exception.Message
        }
    }

    Add-Check -Key "item:$($itemSpec.key)" -Status PASS -Detail ([string]$actual.id)

    if ($UseFabricCli) {
        if (-not (Get-Command fab -ErrorAction SilentlyContinue)) {
            Add-Check -Key "cli:$($itemSpec.key)" -Status FAIL -Detail 'fab command not found.'
        }
        else {
            $workspaceName = [string]$state.workspaces[[string]$itemSpec.workspaceKey].displayName
            $target = "$workspaceName.Workspace/$($itemState.displayName).$($itemSpec.type)"
            & fab exists $target | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Add-Check -Key "cli:$($itemSpec.key)" -Status PASS -Detail $target
            }
            else {
                Add-Check -Key "cli:$($itemSpec.key)" -Status FAIL -Detail "$target not visible through Fabric CLI."
            }
        }
    }
}

if ($KqlSmoke) {
    $queryUri = ([string]$parameters.bindings.kqlQueryServiceUri).TrimEnd('/')
    if (-not $queryUri) {
        Add-Check -Key 'kql:runtime' -Status FAIL -Detail 'bindings.kqlQueryServiceUri is empty.'
    }
    else {
        try {
            $kustoToken = Get-NsAccessToken `
                -Resource 'https://api.kusto.windows.net' `
                -AuthenticationMode ([string]$parameters.authentication.mode) `
                -ManagedIdentityClientId ([string]$parameters.authentication.managedIdentityClientId)
            $command = @'
.show tables
| where TableName in ('telemetry_hot','alarm_hot','gateway_health_hot','model_inference_hot','ingest_quarantine_hot')
| summarize tables=count()
'@
            $response = Invoke-NsHttp `
                -Method POST `
                -Uri "$queryUri/v1/rest/mgmt" `
                -Token $kustoToken `
                -Body @{
                    db = [string]$parameters.items.kqlOperations.displayName
                    csl = $command
                }
            Add-Check -Key 'kql:runtime' -Status PASS -Detail "HTTP $($response.StatusCode)"
        }
        catch {
            Add-Check -Key 'kql:runtime' -Status FAIL -Detail $_.Exception.Message
        }
    }
}

foreach ($manualAsset in $catalog.manualAssets) {
    Add-Check `
        -Key "manual:$($manualAsset.key)" `
        -Status MANUAL `
        -Detail ([string]$manualAsset.reason)
}

$result = [pscustomobject]@{
    status      = if ($failures.Count -eq 0) { 'PASS' } else { 'FAIL' }
    environment = [string]$parameters.environment
    checkedAt   = [DateTimeOffset]::UtcNow.ToString('o')
    checks      = $checks.ToArray()
    failures    = $failures.ToArray()
}
$result | ConvertTo-Json -Depth 30
if ($failures.Count -gt 0) {
    throw "Fabric deployment validation failed with $($failures.Count) error(s)."
}
