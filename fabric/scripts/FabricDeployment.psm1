Set-StrictMode -Version Latest

$script:FabricApiBase = 'https://api.fabric.microsoft.com/v1'

function Get-NsAccessToken {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Resource,

        [ValidateSet('AzureCli', 'ManagedIdentity')]
        [string]$AuthenticationMode = 'AzureCli',

        [string]$ManagedIdentityClientId = ''
    )

    if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
        throw 'Azure CLI (az) is required and was not found on PATH.'
    }

    if ($AuthenticationMode -eq 'ManagedIdentity') {
        $loginArguments = @('login', '--identity', '--allow-no-subscriptions')
        if ($ManagedIdentityClientId) {
            $loginArguments += @('--username', $ManagedIdentityClientId)
        }
        & az @loginArguments | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw 'Azure CLI managed-identity login failed.'
        }
    }

    $token = & az account get-access-token `
        --resource $Resource `
        --query accessToken `
        --output tsv
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) {
        throw "Could not acquire an access token for resource '$Resource'."
    }
    return $token.Trim()
}

function Get-NsHeaderValue {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Headers,
        [Parameter(Mandatory)][string]$Name
    )

    foreach ($key in $Headers.Keys) {
        if ([string]$key -ieq $Name) {
            $value = $Headers[$key]
            if ($value -is [System.Array]) {
                return [string]$value[0]
            }
            return [string]$value
        }
    }
    return $null
}

function Invoke-NsHttp {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet('GET', 'POST', 'PUT', 'PATCH', 'DELETE')]
        [string]$Method,

        [Parameter(Mandatory)]
        [string]$Uri,

        [Parameter(Mandatory)]
        [string]$Token,

        $Body,

        [int]$MaxRetries = 6
    )

    $attempt = 0
    while ($true) {
        $attempt++
        $parameters = @{
            Method            = $Method
            Uri               = $Uri
            Headers           = @{
                Authorization = "Bearer $Token"
                Accept        = 'application/json'
            }
            SkipHttpErrorCheck = $true
            ErrorAction       = 'Stop'
        }
        if ($null -ne $Body) {
            $parameters.ContentType = 'application/json'
            $parameters.Body = if ($Body -is [string]) {
                $Body
            }
            else {
                $Body | ConvertTo-Json -Depth 100 -Compress
            }
        }

        try {
            $response = Invoke-WebRequest @parameters
        }
        catch {
            if ($attempt -ge $MaxRetries) {
                throw
            }
            Start-Sleep -Seconds ([Math]::Min(60, [Math]::Pow(2, $attempt)))
            continue
        }

        $statusCode = [int]$response.StatusCode
        $content = [string]$response.Content
        $json = $null
        if (-not [string]::IsNullOrWhiteSpace($content)) {
            try {
                $json = $content | ConvertFrom-Json -Depth 100
            }
            catch {
                $json = $null
            }
        }

        if ($statusCode -eq 429 -or $statusCode -eq 408 -or $statusCode -ge 500) {
            if ($attempt -ge $MaxRetries) {
                throw "HTTP $statusCode after $attempt attempts: $Method $Uri`n$content"
            }
            $retryAfter = Get-NsHeaderValue -Headers $response.Headers -Name 'Retry-After'
            $delay = if ($retryAfter -as [int]) {
                [int]$retryAfter
            }
            else {
                [Math]::Min(60, [Math]::Pow(2, $attempt))
            }
            Start-Sleep -Seconds $delay
            continue
        }

        if ($statusCode -ge 400) {
            throw "HTTP ${statusCode}: $Method $Uri`n$content"
        }

        return [pscustomobject]@{
            StatusCode = $statusCode
            Headers    = $response.Headers
            Content    = $content
            Json       = $json
        }
    }
}

function Wait-NsFabricOperation {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$InitialResponse,
        [Parameter(Mandatory)][string]$Token,
        [int]$TimeoutSeconds = 1800
    )

    if ($InitialResponse.StatusCode -ne 202) {
        return $InitialResponse.Json
    }

    $operationUri = Get-NsHeaderValue -Headers $InitialResponse.Headers -Name 'Location'
    if (-not $operationUri) {
        $operationUri = Get-NsHeaderValue -Headers $InitialResponse.Headers -Name 'Azure-AsyncOperation'
    }
    if (-not $operationUri) {
        $operationId = Get-NsHeaderValue -Headers $InitialResponse.Headers -Name 'x-ms-operation-id'
        if ($operationId) {
            $operationUri = "$script:FabricApiBase/operations/$operationId"
        }
    }
    if (-not $operationUri) {
        throw 'Fabric returned 202 without Location, Azure-AsyncOperation, or x-ms-operation-id.'
    }

    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTimeOffset]::UtcNow -lt $deadline) {
        $retryAfter = Get-NsHeaderValue -Headers $InitialResponse.Headers -Name 'Retry-After'
        $delay = if ($retryAfter -as [int]) { [int]$retryAfter } else { 5 }
        Start-Sleep -Seconds ([Math]::Max(1, [Math]::Min(60, $delay)))

        $poll = Invoke-NsHttp -Method GET -Uri $operationUri -Token $Token
        $payload = $poll.Json
        if ($null -eq $payload) {
            if ($poll.StatusCode -eq 200) {
                return $null
            }
            $InitialResponse = $poll
            continue
        }

        $status = [string]$payload.status
        if (-not $status -and $payload.PSObject.Properties.Name -contains 'state') {
            $status = [string]$payload.state
        }
        switch -Regex ($status) {
            '^(Succeeded|Completed|Success)$' { return $payload }
            '^(Failed|Cancelled|Canceled)$' {
                throw "Fabric long-running operation failed: $($payload | ConvertTo-Json -Depth 20 -Compress)"
            }
            default {
                if (-not $status -and $poll.StatusCode -eq 200) {
                    return $payload
                }
            }
        }
        $InitialResponse = $poll
    }

    throw "Fabric long-running operation timed out after $TimeoutSeconds seconds: $operationUri"
}

function Invoke-NsFabricRequest {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet('GET', 'POST', 'PUT', 'PATCH', 'DELETE')]
        [string]$Method,

        [Parameter(Mandatory)]
        [string]$Path,

        [Parameter(Mandatory)]
        [string]$Token,

        $Body,

        [int]$TimeoutSeconds = 1800
    )

    $uri = if ($Path.StartsWith('http', [System.StringComparison]::OrdinalIgnoreCase)) {
        $Path
    }
    else {
        "$script:FabricApiBase$Path"
    }
    $response = Invoke-NsHttp -Method $Method -Uri $uri -Token $Token -Body $Body
    return Wait-NsFabricOperation -InitialResponse $response -Token $Token -TimeoutSeconds $TimeoutSeconds
}

function Get-NsFabricCollection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Token
    )

    $items = [System.Collections.Generic.List[object]]::new()
    $nextUri = "$script:FabricApiBase$Path"
    while ($nextUri) {
        $response = Invoke-NsHttp -Method GET -Uri $nextUri -Token $Token
        $payload = $response.Json
        if ($null -eq $payload) {
            break
        }
        if ($payload.PSObject.Properties.Name -contains 'value') {
            foreach ($item in @($payload.value)) {
                $items.Add($item)
            }
        }
        else {
            $items.Add($payload)
        }

        $nextUri = $null
        if ($payload.PSObject.Properties.Name -contains 'continuationUri' -and $payload.continuationUri) {
            $nextUri = [string]$payload.continuationUri
        }
        elseif ($payload.PSObject.Properties.Name -contains 'continuationToken' -and $payload.continuationToken) {
            $separator = if ($Path.Contains('?')) { '&' } else { '?' }
            $encoded = [Uri]::EscapeDataString([string]$payload.continuationToken)
            $nextUri = "$script:FabricApiBase$Path${separator}continuationToken=$encoded"
        }
    }
    return $items.ToArray()
}

function Find-NsWorkspace {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$DisplayName,
        [Parameter(Mandatory)][string]$Token
    )

    $matches = @(
        Get-NsFabricCollection -Path '/workspaces' -Token $Token |
            Where-Object { [string]$_.displayName -ieq $DisplayName }
    )
    if ($matches.Count -gt 1) {
        throw "More than one workspace is named '$DisplayName'."
    }
    if ($matches.Count -eq 1) {
        return $matches[0]
    }
    return $null
}

function Find-NsItem {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$WorkspaceId,
        [Parameter(Mandatory)][string]$DisplayName,
        [Parameter(Mandatory)][string]$Type,
        [Parameter(Mandatory)][string]$Token
    )

    $matches = @(
        Get-NsFabricCollection -Path "/workspaces/$WorkspaceId/items" -Token $Token |
            Where-Object {
                [string]$_.displayName -ieq $DisplayName -and
                [string]$_.type -ieq $Type
            }
    )
    if ($matches.Count -gt 1) {
        throw "More than one $Type item is named '$DisplayName' in workspace $WorkspaceId."
    }
    if ($matches.Count -eq 1) {
        return $matches[0]
    }
    return $null
}

function ConvertTo-NsNotebookIpynb {
    <#
    .SYNOPSIS
        Converts Fabric's "notebook-content.py" source format into a Jupyter
        .ipynb document.
    .DESCRIPTION
        The Fabric REST API accepts notebook definitions in two formats. The
        "fabricGitSource" format (the .py representation) is accepted with an
        HTTP 202 and a long-running operation that reports Succeeded, but the
        service silently discards every cell: a subsequent getDefinition returns
        a three-line stub and getDefinition?format=ipynb returns "cells": [].
        The "ipynb" format round-trips faithfully, so we convert on the fly and
        deploy notebooks as .ipynb.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Content)

    $lines = ($Content -replace "`r`n", "`n") -split "`n"
    $markerPattern = '^#\s+(CELL|MARKDOWN|METADATA)\s+\*{3,}\s*$'

    $sections = [System.Collections.Generic.List[object]]::new()
    $currentKind = 'HEADER'
    $buffer = [System.Collections.Generic.List[string]]::new()

    $flush = {
        $sections.Add([pscustomobject]@{ Kind = $currentKind; Lines = $buffer.ToArray() })
        $buffer.Clear()
    }

    foreach ($line in $lines) {
        $m = [regex]::Match($line, $markerPattern)
        if ($m.Success) {
            & $flush
            $currentKind = $m.Groups[1].Value
            continue
        }
        $buffer.Add($line)
    }
    & $flush

    # Trim blank padding that the .py format inserts around markers.
    $trim = {
        param([string[]]$Value)
        $list = [System.Collections.Generic.List[string]]$Value
        while ($list.Count -gt 0 -and [string]::IsNullOrWhiteSpace($list[0])) { $list.RemoveAt(0) }
        while ($list.Count -gt 0 -and [string]::IsNullOrWhiteSpace($list[$list.Count - 1])) { $list.RemoveAt($list.Count - 1) }
        return , $list.ToArray()
    }

    $parseMeta = {
        param([string[]]$Value)
        $json = ($Value |
            Where-Object { $_ -match '^#\s?META(\s|$)' } |
            ForEach-Object { $_ -replace '^#\s?META\s?', '' }) -join "`n"
        if ([string]::IsNullOrWhiteSpace($json)) { return $null }
        try { return $json | ConvertFrom-Json -Depth 20 } catch { return $null }
    }

    $notebookMeta = $null
    $cells = [System.Collections.Generic.List[object]]::new()

    foreach ($section in $sections) {
        switch ($section.Kind) {
            'CELL' {
                $body = & $trim $section.Lines
                $source = ConvertTo-NsIpynbSource -Lines $body
                $cells.Add([ordered]@{
                    cell_type       = 'code'
                    source          = $source
                    execution_count = $null
                    outputs         = @()
                    metadata        = [ordered]@{}
                })
            }
            'MARKDOWN' {
                $body = @(& $trim $section.Lines | ForEach-Object { $_ -replace '^#\s?', '' })
                $source = ConvertTo-NsIpynbSource -Lines $body
                $cells.Add([ordered]@{
                    cell_type = 'markdown'
                    source    = $source
                    metadata  = [ordered]@{}
                })
            }
            'METADATA' {
                $meta = & $parseMeta $section.Lines
                if ($null -eq $meta) { break }
                if ($cells.Count -eq 0) {
                    $notebookMeta = $meta
                }
                else {
                    $cells[$cells.Count - 1].metadata = $meta
                }
            }
        }
    }

    $kernelName = 'synapse_pyspark'
    if ($notebookMeta -and $notebookMeta.kernel_info -and $notebookMeta.kernel_info.name) {
        $kernelName = [string]$notebookMeta.kernel_info.name
    }

    $metadata = [ordered]@{
        language_info = [ordered]@{ name = 'python' }
        kernelspec    = [ordered]@{
            name         = $kernelName
            language     = 'Python'
            display_name = 'Synapse PySpark'
        }
    }
    if ($notebookMeta -and $notebookMeta.PSObject.Properties.Name -contains 'dependencies') {
        $metadata['dependencies'] = $notebookMeta.dependencies
    }

    $document = [ordered]@{
        nbformat       = 4
        nbformat_minor = 5
        metadata       = $metadata
        cells          = $cells.ToArray()
    }
    return ($document | ConvertTo-Json -Depth 30 -Compress)
}

function ConvertTo-NsIpynbSource {
    <#
    .SYNOPSIS
        Renders an array of raw lines as an .ipynb "source" array, where every
        line except the last carries a trailing newline.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][AllowEmptyCollection()][AllowEmptyString()][string[]]$Lines)

    if ($Lines.Count -eq 0) { return @() }
    $out = [System.Collections.Generic.List[string]]::new()
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ($i -eq $Lines.Count - 1) { $out.Add($Lines[$i]) }
        else { $out.Add($Lines[$i] + "`n") }
    }
    return , $out.ToArray()
}

function ConvertTo-NsFabricDefinition {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$SourceDirectory,
        [Parameter(Mandatory)][object[]]$DefinitionParts,
        [Parameter(Mandatory)][hashtable]$Replacements,
        [AllowEmptyString()][string]$Format = ''
    )

    $parts = [System.Collections.Generic.List[object]]::new()
    foreach ($partPath in $DefinitionParts) {
        $fullPath = Join-Path $SourceDirectory ([string]$partPath)
        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
            throw "Definition part not found: $fullPath"
        }
        $content = Get-Content -LiteralPath $fullPath -Raw -Encoding UTF8
        foreach ($key in @($Replacements.Keys | Sort-Object Length -Descending)) {
            $content = $content.Replace([string]$key, [string]$Replacements[$key])
        }
        # Fabric's fabricGitSource parser splits notebooks on literal
        # "# CELL ********************" lines and TMDL is likewise newline
        # sensitive. On a Windows checkout with core.autocrlf=true these files
        # carry CRLF, the markers never match, and Fabric silently accepts the
        # upload while storing a notebook with ZERO cells. Normalize to LF so
        # the deployed definition does not depend on the caller's checkout.
        $content = $content -replace "`r`n", "`n"
        $unresolved = [regex]::Matches($content, '\{\{[^{}]+\}\}') |
            ForEach-Object { $_.Value } |
            Sort-Object -Unique
        if ($unresolved) {
            throw "Unresolved definition tokens in '$fullPath': $($unresolved -join ', ')"
        }
        $emitPath = ([string]$partPath).Replace('\', '/')
        if ($Format -eq 'ipynb' -and $emitPath -like '*.py') {
            $content = ConvertTo-NsNotebookIpynb -Content $content
            $emitPath = [System.IO.Path]::ChangeExtension($emitPath, 'ipynb')
        }
        $payload = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($content))
        $parts.Add([ordered]@{
            path        = $emitPath
            payload     = $payload
            payloadType = 'InlineBase64'
        })
    }

    $definition = [ordered]@{ parts = $parts.ToArray() }
    if ($Format) {
        $definition = [ordered]@{
            format = $Format
            parts  = $parts.ToArray()
        }
    }
    return $definition
}

function Assert-NsParameterFileHasNoSecrets {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)

    $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $secretKeyPattern = '(?i)"(?:clientSecret|password|sasToken|sasKey|connectionString|accessKey|accountKey|sharedAccessKey)"\s*:'
    if ($raw -match $secretKeyPattern) {
        throw "Parameter file contains a prohibited secret-bearing key: $Path"
    }
}

Export-ModuleMember -Function @(
    'Get-NsAccessToken',
    'Get-NsHeaderValue',
    'Invoke-NsHttp',
    'Wait-NsFabricOperation',
    'Invoke-NsFabricRequest',
    'Get-NsFabricCollection',
    'Find-NsWorkspace',
    'Find-NsItem',
    'ConvertTo-NsFabricDefinition',
    'ConvertTo-NsNotebookIpynb',
    'ConvertTo-NsIpynbSource',
    'Assert-NsParameterFileHasNoSecrets'
)
