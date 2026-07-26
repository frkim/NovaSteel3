[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$ParameterFile,

    [string]$CatalogFile = '',

    [string]$StateOutputPath = '',

    [int]$OperationTimeoutSeconds = 1800
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$fabricRoot = Split-Path -Parent $PSScriptRoot
if (-not $CatalogFile) {
    $CatalogFile = Join-Path $fabricRoot 'catalog\fabric-items.json'
}
if (-not [IO.Path]::IsPathRooted($ParameterFile)) {
    $ParameterFile = Join-Path (Get-Location) $ParameterFile
}
if (-not [IO.Path]::IsPathRooted($CatalogFile)) {
    $CatalogFile = Join-Path (Get-Location) $CatalogFile
}

Import-Module (Join-Path $PSScriptRoot 'FabricDeployment.psm1') -Force
Assert-NsParameterFileHasNoSecrets -Path $ParameterFile

$parameters = Get-Content -LiteralPath $ParameterFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100
$catalog = Get-Content -LiteralPath $CatalogFile -Raw -Encoding UTF8 |
    ConvertFrom-Json -Depth 100

function Get-DynamicProperty {
    param(
        [Parameter(Mandatory)]$Object,
        [Parameter(Mandatory)][string]$Name,
        $Default = $null
    )
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $Default
    }
    return $property.Value
}

function Assert-NonPlaceholderGuid {
    param([string]$Name, [string]$Value)
    $parsed = [Guid]::Empty
    if (-not [Guid]::TryParse($Value, [ref]$parsed) -or $parsed -eq [Guid]::Empty) {
        throw "$Name must be a non-zero GUID before tenant deployment."
    }
}

if ($parameters.environment -notin @('dev', 'test', 'demo', 'prod')) {
    throw "Unsupported environment '$($parameters.environment)'."
}
if ($parameters.region -ne 'Sweden Central') {
    throw 'NovaSteel Fabric assets are approved for Sweden Central by default.'
}
if ($parameters.environment -eq 'demo') {
    if (-not $parameters.syntheticOnly -or $parameters.dataClassification -ne 'SYNTHETIC') {
        throw 'Demo deployment must be synthetic-only and classified SYNTHETIC.'
    }
    foreach ($workspaceProperty in $parameters.workspaces.PSObject.Properties) {
        if (-not ([string]$workspaceProperty.Value.displayName).StartsWith('NS-DEMO-')) {
            throw "Demo workspace '$($workspaceProperty.Name)' must start with NS-DEMO-."
        }
    }
}
if ($parameters.environment -eq 'prod' -and $parameters.lifecycle.automationEnabled) {
    throw 'Production capacity lifecycle automation is hard-denied.'
}

Assert-NonPlaceholderGuid -Name 'tenantId' -Value ([string]$parameters.tenantId)
Assert-NonPlaceholderGuid -Name 'subscriptionId' -Value ([string]$parameters.subscriptionId)
Assert-NonPlaceholderGuid -Name 'capacity.fabricCapacityId' -Value ([string]$parameters.capacity.fabricCapacityId)

$authMode = [string]$parameters.authentication.mode
$managedIdentityClientId = [string]$parameters.authentication.managedIdentityClientId
$token = Get-NsAccessToken `
    -Resource 'https://api.fabric.microsoft.com' `
    -AuthenticationMode $authMode `
    -ManagedIdentityClientId $managedIdentityClientId

$state = [ordered]@{
    schemaVersion = 1
    environment   = [string]$parameters.environment
    generatedAt   = [DateTimeOffset]::UtcNow.ToString('o')
    workspaces    = [ordered]@{}
    items         = [ordered]@{}
}

foreach ($workspaceSpec in $catalog.workspaces) {
    $key = [string]$workspaceSpec.key
    $workspaceParameters = Get-DynamicProperty -Object $parameters.workspaces -Name $key
    if ($null -eq $workspaceParameters) {
        throw "Missing workspace parameters for '$key'."
    }
    $displayName = [string]$workspaceParameters.displayName
    $workspace = Find-NsWorkspace -DisplayName $displayName -Token $token

    if ($null -eq $workspace) {
        if (-not $parameters.deploymentOptions.createWorkspaces) {
            throw "Workspace '$displayName' does not exist and createWorkspaces=false."
        }
        if ($PSCmdlet.ShouldProcess($displayName, 'Create Fabric workspace')) {
            $body = [ordered]@{
                displayName = $displayName
                description = [string]$workspaceSpec.purpose
                capacityId  = [string]$parameters.capacity.fabricCapacityId
            }
            Invoke-NsFabricRequest `
                -Method POST `
                -Path '/workspaces' `
                -Token $token `
                -Body $body `
                -TimeoutSeconds $OperationTimeoutSeconds | Out-Null
        }
        $workspace = Find-NsWorkspace -DisplayName $displayName -Token $token
        if ($null -eq $workspace) {
            throw "Workspace '$displayName' was not found after creation."
        }
    }

    if ($parameters.deploymentOptions.assignCapacity) {
        $currentCapacity = Get-DynamicProperty -Object $workspace -Name 'capacityId' -Default ''
        if ([string]$currentCapacity -ne [string]$parameters.capacity.fabricCapacityId) {
            if ($PSCmdlet.ShouldProcess($displayName, "Assign capacity $($parameters.capacity.fabricCapacityId)")) {
                $assignmentResponse = Invoke-NsHttp `
                    -Method POST `
                    -Uri "https://api.fabric.microsoft.com/v1/workspaces/$($workspace.id)/assignToCapacity" `
                    -Token $token `
                    -Body @{ capacityId = [string]$parameters.capacity.fabricCapacityId }
                $operationLocation = Get-NsHeaderValue -Headers $assignmentResponse.Headers -Name 'Location'
                $operationId = Get-NsHeaderValue -Headers $assignmentResponse.Headers -Name 'x-ms-operation-id'
                if ($assignmentResponse.StatusCode -eq 202 -and ($operationLocation -or $operationId)) {
                    Wait-NsFabricOperation `
                        -InitialResponse $assignmentResponse `
                        -Token $token `
                        -TimeoutSeconds $OperationTimeoutSeconds | Out-Null
                }

                $deadline = [DateTimeOffset]::UtcNow.AddSeconds($OperationTimeoutSeconds)
                $assignmentVerified = $false
                while ([DateTimeOffset]::UtcNow -lt $deadline) {
                    $workspace = Invoke-NsFabricRequest `
                        -Method GET `
                        -Path "/workspaces/$($workspace.id)" `
                        -Token $token
                    $assignedCapacity = Get-DynamicProperty -Object $workspace -Name 'capacityId' -Default ''
                    $assignmentProgress = Get-DynamicProperty -Object $workspace -Name 'capacityAssignmentProgress' -Default ''
                    if ([string]$assignmentProgress -eq 'Failed') {
                        throw "Workspace '$displayName' capacity assignment failed."
                    }
                    if ([string]$assignedCapacity -eq [string]$parameters.capacity.fabricCapacityId -and
                        ([string]::IsNullOrWhiteSpace([string]$assignmentProgress) -or
                         [string]$assignmentProgress -eq 'Completed')) {
                        $assignmentVerified = $true
                        break
                    }
                    Start-Sleep -Seconds 5
                }
                if (-not $assignmentVerified) {
                    throw "Workspace '$displayName' capacity assignment did not reach the configured capacity before timeout."
                }
            }
        }
    }

    $state.workspaces[$key] = [ordered]@{
        id          = [string]$workspace.id
        displayName = $displayName
    }
}

function New-ReplacementMap {
    $map = @{}
    $map['{{environment}}'] = [string]$parameters.environment
    foreach ($workspaceEntry in $state.workspaces.GetEnumerator()) {
        $map["{{workspace.$($workspaceEntry.Key).id}}"] = [string]$workspaceEntry.Value.id
        $map["{{workspace.$($workspaceEntry.Key).displayName}}"] = [string]$workspaceEntry.Value.displayName
    }
    foreach ($itemEntry in $state.items.GetEnumerator()) {
        $map["{{item.$($itemEntry.Key).id}}"] = [string]$itemEntry.Value.id
        $map["{{item.$($itemEntry.Key).displayName}}"] = [string]$itemEntry.Value.displayName
    }
    foreach ($retentionProperty in $parameters.retention.PSObject.Properties) {
        $map["{{retention.$($retentionProperty.Name)}}"] = [string]$retentionProperty.Value
    }

    $landingUri = [string]$parameters.onelake.landingTablesUri
    if ($landingUri.Contains('<') -and
        $state.items.Contains('landingLakehouse')) {
        $landingUri = "abfss://$($state.workspaces.rtiIngress.id)@onelake.dfs.fabric.microsoft.com/$($state.items.landingLakehouse.id)/Tables"
    }
    $coreUri = [string]$parameters.onelake.coreTablesUri
    if ($coreUri.Contains('<') -and
        $state.items.Contains('coreLakehouse')) {
        $coreUri = "abfss://$($state.workspaces.dataCore.id)@onelake.dfs.fabric.microsoft.com/$($state.items.coreLakehouse.id)/Tables"
    }
    $map['{{onelake.landingTablesUri}}'] = $landingUri
    $map['{{onelake.coreTablesUri}}'] = $coreUri
    return $map
}

foreach ($itemSpec in $catalog.items) {
    $optionName = [string]$itemSpec.deploymentOption
    $enabled = [bool](Get-DynamicProperty -Object $parameters.deploymentOptions -Name $optionName -Default $true)
    if (-not $enabled) {
        Write-Host "SKIP $($itemSpec.key): $optionName=false"
        continue
    }

    if ($itemSpec.bindingGate) {
        $gatePassed = [bool](Get-DynamicProperty -Object $parameters.deploymentOptions -Name ([string]$itemSpec.bindingGate) -Default $false)
        if (-not $gatePassed) {
            Write-Host "GATE $($itemSpec.key): $($itemSpec.bindingGate)=false"
            continue
        }
    }

    foreach ($dependency in @($itemSpec.dependencies)) {
        if (-not $state.items.Contains([string]$dependency)) {
            throw "Item '$($itemSpec.key)' depends on '$dependency', which has not been deployed."
        }
    }

    $workspaceState = $state.workspaces[[string]$itemSpec.workspaceKey]
    if ($null -eq $workspaceState) {
        throw "Unknown workspace key '$($itemSpec.workspaceKey)' for item '$($itemSpec.key)'."
    }
    $workspaceId = [string]$workspaceState.id
    $displayName = [string]$itemSpec.displayName

    $parameterItem = Get-DynamicProperty -Object $parameters.items -Name ([string]$itemSpec.key)
    if ($null -ne $parameterItem -and $parameterItem.displayName) {
        $displayName = [string]$parameterItem.displayName
    }

    $existing = Find-NsItem `
        -WorkspaceId $workspaceId `
        -DisplayName $displayName `
        -Type ([string]$itemSpec.type) `
        -Token $token

    $definition = $null
    if (-not [bool]$itemSpec.createWithoutDefinition) {
        $sourceDirectory = Join-Path $fabricRoot ([string]$itemSpec.sourceDirectory)
        $definition = ConvertTo-NsFabricDefinition `
            -SourceDirectory $sourceDirectory `
            -DefinitionParts @($itemSpec.definitionParts) `
            -Replacements (New-ReplacementMap) `
            -Format ([string]$itemSpec.definitionFormat)
    }

    if ($null -eq $existing) {
        $body = [ordered]@{
            displayName = $displayName
            description = [string]$itemSpec.description
        }
        if ($null -ne $definition) {
            $body.definition = $definition
        }
        $labelId = [string]$parameters.bindings.sensitivityLabelId
        $labelGuid = [Guid]::Empty
        if ([Guid]::TryParse($labelId, [ref]$labelGuid) -and $labelGuid -ne [Guid]::Empty) {
            $body.sensitivityLabelSettings = @{
                labelId                      = $labelId
                sensitivityLabelApplyStrategy = 'ApplyOrFail'
            }
        }

        if ($PSCmdlet.ShouldProcess("$($workspaceState.displayName)/$displayName", "Create $($itemSpec.type)")) {
            Invoke-NsFabricRequest `
                -Method POST `
                -Path "/workspaces/$workspaceId$($itemSpec.restCollection)" `
                -Token $token `
                -Body $body `
                -TimeoutSeconds $OperationTimeoutSeconds | Out-Null
        }
    }
    elseif ($null -ne $definition) {
        if ($PSCmdlet.ShouldProcess("$($workspaceState.displayName)/$displayName", "Update $($itemSpec.type) definition")) {
            Invoke-NsFabricRequest `
                -Method POST `
                -Path "/workspaces/$workspaceId/items/$($existing.id)/updateDefinition?updateMetadata=true" `
                -Token $token `
                -Body @{ definition = $definition } `
                -TimeoutSeconds $OperationTimeoutSeconds | Out-Null
        }
    }

    $resolved = Find-NsItem `
        -WorkspaceId $workspaceId `
        -DisplayName $displayName `
        -Type ([string]$itemSpec.type) `
        -Token $token
    if ($null -eq $resolved) {
        throw "Item '$displayName' ($($itemSpec.type)) was not found after deployment."
    }
    $state.items[[string]$itemSpec.key] = [ordered]@{
        id          = [string]$resolved.id
        displayName = $displayName
        type        = [string]$itemSpec.type
        workspaceKey = [string]$itemSpec.workspaceKey
    }
}

if ($parameters.deploymentOptions.applyIngressPublisherAclWithFabricCli) {
    $publisherObjectId = [string]$parameters.bindings.eventstreamPublisherObjectId
    Assert-NonPlaceholderGuid -Name 'bindings.eventstreamPublisherObjectId' -Value $publisherObjectId
    if (-not (Get-Command fab -ErrorAction SilentlyContinue)) {
        throw 'Fabric CLI (fab) is required for applyIngressPublisherAclWithFabricCli.'
    }
    if ($authMode -eq 'ManagedIdentity') {
        $fabLogin = @('auth', 'login', '--identity')
        if ($managedIdentityClientId) {
            $fabLogin += @('-u', $managedIdentityClientId)
        }
        & fab @fabLogin
        if ($LASTEXITCODE -ne 0) {
            throw 'Fabric CLI managed-identity login failed.'
        }
    }
    $ingressPath = "$($state.workspaces.rtiIngress.displayName).Workspace"
    if ($PSCmdlet.ShouldProcess($ingressPath, "Grant publisher $publisherObjectId Contributor")) {
        & fab acl set $ingressPath -I $publisherObjectId -R contributor -f
        if ($LASTEXITCODE -ne 0) {
            throw 'Fabric CLI failed to apply the isolated ingress publisher ACL.'
        }
    }
}

if ($parameters.deploymentOptions.runInitializationJobs) {
    if (-not $state.items.Contains('notebookInitialize')) {
        throw 'runInitializationJobs=true but ns-initialize-lakehouses was not deployed.'
    }
    $initialize = $state.items.notebookInitialize
    $workspaceId = $state.workspaces[[string]$initialize.workspaceKey].id
    $replacements = New-ReplacementMap
    $jobBody = @{
        executionData = @{
            parameters = @{
                ENVIRONMENT = @{ value = [string]$parameters.environment; type = 'string' }
                LANDING_TABLES_URI = @{ value = [string]$replacements['{{onelake.landingTablesUri}}']; type = 'string' }
                CORE_TABLES_URI = @{ value = [string]$replacements['{{onelake.coreTablesUri}}']; type = 'string' }
            }
        }
    }
    if ($PSCmdlet.ShouldProcess($initialize.displayName, 'Run initialization notebook')) {
        Invoke-NsFabricRequest `
            -Method POST `
            -Path "/workspaces/$workspaceId/items/$($initialize.id)/jobs/instances?jobType=RunNotebook" `
            -Token $token `
            -Body $jobBody `
            -TimeoutSeconds 3600 | Out-Null
    }
}

if (-not $StateOutputPath) {
    $StateOutputPath = Join-Path $fabricRoot "deployment-state\$($parameters.environment).json"
}
if (-not [IO.Path]::IsPathRooted($StateOutputPath)) {
    $StateOutputPath = Join-Path (Get-Location) $StateOutputPath
}
$stateDirectory = Split-Path -Parent $StateOutputPath
New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
$state.generatedAt = [DateTimeOffset]::UtcNow.ToString('o')
$state | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $StateOutputPath -Encoding UTF8

$manualGates = foreach ($manualAsset in $catalog.manualAssets) {
    [pscustomobject]@{
        key    = [string]$manualAsset.key
        reason = [string]$manualAsset.reason
    }
}

[pscustomobject]@{
    status       = 'DEPLOYED'
    environment  = [string]$parameters.environment
    stateFile    = $StateOutputPath
    workspaces   = $state.workspaces.Count
    items        = $state.items.Count
    manualGates  = $manualGates
} | ConvertTo-Json -Depth 20
