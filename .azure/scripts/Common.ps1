Set-StrictMode -Version Latest

$script:NovaSteelSubscriptionId = '3377065c-bf76-4767-a982-32bce4ffb592'
$script:NovaSteelTenantId = '9d94eb6e-d45e-4f05-bc1b-d0bbd2421561'
$script:NovaSteelLocation = 'swedencentral'
$script:NovaSteelResourceGroup = 'rg-novasteelv3-demo-sc'

function Get-NovaSteelDemoPaths {
    [CmdletBinding()]
    param()

    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    $infraRoot = Join-Path $repoRoot '.azure\infra'

    return [pscustomobject]@{
        RepoRoot = $repoRoot
        InfraRoot = $infraRoot
        TemplateFile = Join-Path $infraRoot 'main.bicep'
        ParameterFile = Join-Path $infraRoot 'main.bicepparam'
    }
}

function Get-NovaSteelDemoParameterDocument {
    [CmdletBinding()]
    param(
        [hashtable]$Overrides = @{}
    )

    $paths = Get-NovaSteelDemoPaths
    $buildOutput = & az bicep build-params --file $paths.ParameterFile --stdout --only-show-errors
    if ($LASTEXITCODE -ne 0) {
        throw "Could not compile Bicep parameter file '$($paths.ParameterFile)'."
    }

    try {
        $compiledOutput = ($buildOutput | Out-String | ConvertFrom-Json -NoEnumerate)
        $parameterDocument = if ($compiledOutput.parametersJson) {
            $compiledOutput.parametersJson | ConvertFrom-Json -NoEnumerate -DateKind String
        } else {
            $compiledOutput
        }
    } catch {
        throw "Could not parse compiled Bicep parameter file '$($paths.ParameterFile)': $($_.Exception.Message)"
    }

    if ($null -eq $parameterDocument.parameters) {
        throw "Compiled Bicep parameter file '$($paths.ParameterFile)' does not contain a parameters object."
    }

    foreach ($property in $parameterDocument.parameters.PSObject.Properties) {
        if ($null -eq $property.Value.PSObject.Properties['value']) {
            throw "Parameter '$($property.Name)' has no literal value in '$($paths.ParameterFile)'."
        }
    }

    foreach ($entry in $Overrides.GetEnumerator()) {
        $parameter = $parameterDocument.parameters.PSObject.Properties[$entry.Key]
        if ($null -eq $parameter) {
            throw "Override '$($entry.Key)' is not declared in '$($paths.ParameterFile)'."
        }
        $parameter.Value.value = $entry.Value
    }

    return $parameterDocument
}

function New-NovaSteelDemoParameterFile {
    [CmdletBinding()]
    param(
        [hashtable]$Overrides = @{}
    )

    $paths = Get-NovaSteelDemoPaths
    $parameterDocument = Get-NovaSteelDemoParameterDocument -Overrides $Overrides
    $parameterFile = Join-Path $paths.InfraRoot ".novasteel-deployment-$([guid]::NewGuid().ToString('N')).parameters.json"

    try {
        $json = $parameterDocument | ConvertTo-Json -Depth 100
        [System.IO.File]::WriteAllText(
            $parameterFile,
            $json,
            [System.Text.UTF8Encoding]::new($false)
        )
    } catch {
        Remove-Item -LiteralPath $parameterFile -Force -ErrorAction SilentlyContinue
        throw "Could not create temporary deployment parameter file '$parameterFile': $($_.Exception.Message)"
    }

    return $parameterFile
}

function Assert-NovaSteelTargetContext {
    [CmdletBinding()]
    param()

    $accountJson = & az account show --only-show-errors 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($accountJson)) {
        throw "No active Azure CLI session. Authenticate to Contoso Fx ($script:NovaSteelSubscriptionId) before running this script."
    }

    $account = $accountJson | ConvertFrom-Json
    if ($account.id -ne $script:NovaSteelSubscriptionId -or $account.tenantId -ne $script:NovaSteelTenantId) {
        throw "Refusing to run in Azure context '$($account.name)' ($($account.id), tenant $($account.tenantId)). Expected Contoso Fx ($script:NovaSteelSubscriptionId, tenant $script:NovaSteelTenantId). This script never switches the active subscription."
    }

    return $account
}

function Invoke-NovaSteelSubscriptionDeployment {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [hashtable]$TemplateParameters
    )

    $paths = Get-NovaSteelDemoPaths
    $parameterFile = New-NovaSteelDemoParameterFile -Overrides $TemplateParameters
    try {
        $arguments = @(
            'deployment', 'sub', 'create',
            '--subscription', $script:NovaSteelSubscriptionId,
            '--name', $Name,
            '--location', $script:NovaSteelLocation,
            '--template-file', $paths.TemplateFile,
            '--parameters', $parameterFile,
            '--only-show-errors',
            '--output', 'json'
        )

        $deploymentJson = & az @arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Azure deployment '$Name' failed."
        }

        return $deploymentJson | ConvertFrom-Json
    } finally {
        Remove-Item -LiteralPath $parameterFile -Force -ErrorAction SilentlyContinue
    }
}

function Get-NovaSteelBootstrapOutputs {
    [CmdletBinding()]
    param(
        [string]$DeploymentName = 'novasteelv3-bootstrap'
    )

    $outputsJson = & az deployment sub show `
        --subscription $script:NovaSteelSubscriptionId `
        --name $DeploymentName `
        --query 'properties.outputs' `
        --only-show-errors `
        --output json
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($outputsJson)) {
        throw "Bootstrap deployment '$DeploymentName' was not found. Run the Bootstrap phase successfully before the Apps phase."
    }

    return $outputsJson | ConvertFrom-Json
}

function Assert-NovaSteelImmutableAcrImage {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Image,

        [Parameter(Mandatory = $true)]
        [string]$AcrName,

        [Parameter(Mandatory = $true)]
        [string]$AcrLoginServer
    )

    $expectedPrefix = "$AcrLoginServer/"
    if (-not $Image.StartsWith($expectedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Image '$Image' is not hosted by the isolated demo ACR '$AcrLoginServer'."
    }
    if ($Image -notmatch '@sha256:[a-fA-F0-9]{64}$') {
        throw "Image '$Image' must use an immutable sha256 digest, not a mutable tag."
    }

    $repositoryAndDigest = $Image.Substring($expectedPrefix.Length)
    & az acr repository show `
        --subscription $script:NovaSteelSubscriptionId `
        --name $AcrName `
        --image $repositoryAndDigest `
        --only-show-errors `
        --output none
    if ($LASTEXITCODE -ne 0) {
        throw "Image '$Image' was not found in ACR '$AcrName'. Publish it after bootstrap and before the Apps phase."
    }
}

function Write-NovaSteelDeploymentOutputs {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject]$Deployment
    )

    $outputs = $Deployment.properties.outputs
    Write-Host "`nResource IDs:" -ForegroundColor Cyan
    $outputs.resourceIds.value.psobject.Properties | ForEach-Object {
        Write-Host ("  {0}: {1}" -f $_.Name, $_.Value)
    }
    Write-Host "`nHostnames:" -ForegroundColor Cyan
    $outputs.hostnames.value.psobject.Properties | ForEach-Object {
        Write-Host ("  {0}: {1}" -f $_.Name, $_.Value)
    }
}
