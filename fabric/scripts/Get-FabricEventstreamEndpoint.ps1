<#
.SYNOPSIS
    Retrieve the generated Custom Endpoint (Event Hubs compatible) connection
    details for the deployed es-ns-telemetry-v1 Eventstream and cache them in a
    git-ignored local settings file - never in source control.

.DESCRIPTION
    A Fabric Eventstream Custom Endpoint exposes its ingress as an Event Hubs
    compatible endpoint (namespace + entity + SAS key), reachable over
    AMQP/Kafka or the Event Hubs REST send API. This script calls
    GET /v1/workspaces/{ws}/eventstreams/{es}/sources/{sourceId}/connection and
    writes the result to deployment-state/<env>-eventstream-endpoint.local.json,
    which the deployment-state/.gitignore already excludes from git.

    The SAS key is a secret. By default it is written only to the git-ignored
    file and is NOT echoed to the console. publish_to_eventstream.py reads the
    same file (or the NS_EVENTSTREAM_* environment variables) to send events.
#>
[CmdletBinding()]
param(
    [string]$ParameterFile = '',

    [string]$StateFile = '',

    [string]$WorkspaceId = '',

    [string]$EventstreamId = '',

    [string]$OutputFile = '',

    [switch]$ShowSecret
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$fabricRoot = Split-Path -Parent $PSScriptRoot
if (-not $ParameterFile) {
    $ParameterFile = Join-Path $fabricRoot 'deployment-parameters\novasteelv3.parameters.json'
}
$parameters = Get-Content -LiteralPath $ParameterFile -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100
$environment = [string]$parameters.environment

if (-not $StateFile) {
    $StateFile = Join-Path $fabricRoot "deployment-state\$environment-eventstream.json"
}
if (-not $WorkspaceId) { $WorkspaceId = [string]$parameters.workspace.id }
if (-not $EventstreamId) {
    if (Test-Path -LiteralPath $StateFile) {
        $state = Get-Content -LiteralPath $StateFile -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100
        $EventstreamId = [string]$state.eventstream.id
    }
}
if (-not $EventstreamId) {
    throw 'EventstreamId could not be resolved. Pass -EventstreamId or run Deploy-FabricEventstream.ps1 first.'
}

$token = az account get-access-token --resource 'https://api.fabric.microsoft.com' --query accessToken -o tsv
if (-not $token) { throw 'Could not acquire a Fabric access token (run az login).' }
$headers = @{ Authorization = "Bearer $token" }

$topology = Invoke-RestMethod -Method GET `
    -Uri "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/eventstreams/$EventstreamId/topology" `
    -Headers $headers
$customSource = @($topology.sources | Where-Object { $_.type -eq 'CustomEndpoint' })
if ($customSource.Count -ne 1) {
    throw "Expected exactly one CustomEndpoint source, found $($customSource.Count)."
}
$sourceId = [string]$customSource[0].id

$connection = Invoke-RestMethod -Method GET `
    -Uri "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/eventstreams/$EventstreamId/sources/$sourceId/connection" `
    -Headers $headers

$keyName = "key_$sourceId"
$connString = [string]$connection.accessKeys.primaryConnectionString
$matchKeyName = [regex]::Match($connString, 'SharedAccessKeyName=([^;]+)')
if ($matchKeyName.Success) { $keyName = $matchKeyName.Groups[1].Value }

$settings = [ordered]@{
    generatedAt             = [DateTimeOffset]::UtcNow.ToString('o')
    environment             = $environment
    workspaceId             = $WorkspaceId
    eventstreamId           = $EventstreamId
    sourceId                = $sourceId
    fullyQualifiedNamespace = [string]$connection.fullyQualifiedNamespace
    eventHubName            = [string]$connection.eventHubName
    sharedAccessKeyName     = $keyName
    sharedAccessKey         = [string]$connection.accessKeys.primaryKey
}

if (-not $OutputFile) {
    $OutputFile = Join-Path $fabricRoot "deployment-state\$environment-eventstream-endpoint.local.json"
}
if (-not [IO.Path]::IsPathRooted($OutputFile)) {
    $OutputFile = Join-Path (Get-Location) $OutputFile
}
New-Item -ItemType Directory -Path (Split-Path -Parent $OutputFile) -Force | Out-Null
$settings | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputFile -Encoding UTF8

Write-Host "Custom Endpoint connection cached (git-ignored): $OutputFile"
Write-Host "  fullyQualifiedNamespace : $($settings.fullyQualifiedNamespace)"
Write-Host "  eventHubName            : $($settings.eventHubName)"
Write-Host "  sharedAccessKeyName     : $($settings.sharedAccessKeyName)"
if ($ShowSecret) {
    Write-Host "  sharedAccessKey         : $($settings.sharedAccessKey)"
}
else {
    Write-Host "  sharedAccessKey         : <hidden - stored in the local file only; pass -ShowSecret to reveal>"
}

[pscustomobject]@{
    status                  = 'ENDPOINT_RETRIEVED'
    settingsFile            = $OutputFile
    fullyQualifiedNamespace = $settings.fullyQualifiedNamespace
    eventHubName            = $settings.eventHubName
    sharedAccessKeyName     = $settings.sharedAccessKeyName
} | ConvertTo-Json -Depth 8
