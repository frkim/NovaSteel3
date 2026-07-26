[CmdletBinding()]
param(
    [string]$FabricRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $FabricRoot) {
    $FabricRoot = Split-Path -Parent $PSScriptRoot
}
if (-not [IO.Path]::IsPathRooted($FabricRoot)) {
    $FabricRoot = Join-Path (Get-Location) $FabricRoot
}

$errors = [System.Collections.Generic.List[string]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()
$checks = [System.Collections.Generic.List[object]]::new()

function Add-Result {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][bool]$Passed,
        [Parameter(Mandatory)][string]$Detail,
        [switch]$Warning
    )
    $status = if ($Passed) { 'PASS' } elseif ($Warning) { 'WARN' } else { 'FAIL' }
    $checks.Add([pscustomobject]@{ name = $Name; status = $status; detail = $Detail })
    if (-not $Passed) {
        if ($Warning) { $warnings.Add("$Name - $Detail") }
        else { $errors.Add("$Name - $Detail") }
    }
}

function Read-JsonFile {
    param([Parameter(Mandatory)][string]$Path)
    try {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 |
            ConvertFrom-Json -Depth 100
    }
    catch {
        Add-Result -Name "json:$Path" -Passed $false -Detail $_.Exception.Message
        return $null
    }
}

if (-not (Test-Path -LiteralPath $FabricRoot -PathType Container)) {
    throw "Fabric root not found: $FabricRoot"
}

$jsonFiles = Get-ChildItem -LiteralPath $FabricRoot -Recurse -File -Filter '*.json'
$parsedJsonCount = 0
foreach ($jsonFile in $jsonFiles) {
    $parsed = Read-JsonFile -Path $jsonFile.FullName
    if ($null -ne $parsed) {
        $parsedJsonCount++
    }
}
Add-Result -Name 'json-parse' -Passed ($parsedJsonCount -eq $jsonFiles.Count) `
    -Detail "$parsedJsonCount of $($jsonFiles.Count) JSON files parsed."

if (Get-Command Test-Json -ErrorAction SilentlyContinue) {
    $schemaPairs = @(
        @('catalog\fabric-items.json', 'catalog\fabric-items.schema.json'),
        @('lakehouse\schema\medallion-catalog.json', 'lakehouse\schema\medallion-catalog.schema.json'),
        @('lakehouse\schema\data-quality-rules.json', 'lakehouse\schema\data-quality-rules.schema.json'),
        @('capacity\precondition-evidence.example.json', 'capacity\precondition-evidence.schema.json')
    )
    foreach ($environmentFile in @(
        'dev.example.json',
        'test.example.json',
        'demo.example.json',
        'prod.example.json'
    )) {
        $schemaPairs += ,@(
            "deployment-parameters\$environmentFile",
            'deployment-parameters\environment.schema.json'
        )
    }
    foreach ($pair in $schemaPairs) {
        $documentPath = Join-Path $FabricRoot $pair[0]
        $schemaPath = Join-Path $FabricRoot $pair[1]
        $valid = Get-Content -LiteralPath $documentPath -Raw -Encoding UTF8 |
            Test-Json -SchemaFile $schemaPath -ErrorAction SilentlyContinue
        Add-Result -Name "json-schema:$($pair[0])" -Passed $valid `
            -Detail "Schema: $($pair[1])"
    }
}
else {
    Add-Result -Name 'json-schema' -Passed $false -Warning `
        -Detail 'Test-Json is unavailable; JSON Schema validation skipped.'
}

$platformFiles = Get-ChildItem -LiteralPath $FabricRoot -Recurse -File -Force |
    Where-Object { $_.Name -eq '.platform' }
$logicalIds = [System.Collections.Generic.List[string]]::new()
foreach ($platformFile in $platformFiles) {
    $platform = Read-JsonFile -Path $platformFile.FullName
    if ($null -ne $platform) {
        if (-not $platform.metadata.type -or -not $platform.metadata.displayName -or
            -not $platform.config.logicalId) {
            Add-Result -Name "platform:$($platformFile.FullName)" -Passed $false `
                -Detail 'metadata.type, metadata.displayName, and config.logicalId are required.'
        }
        else {
            $logicalIds.Add([string]$platform.config.logicalId)
        }
    }
}
$duplicateLogicalIds = @(
    $logicalIds | Group-Object | Where-Object Count -gt 1 | ForEach-Object Name
)
Add-Result -Name 'platform-logical-ids' -Passed ($duplicateLogicalIds.Count -eq 0) `
    -Detail $(if ($duplicateLogicalIds.Count) {
        "Duplicates: $($duplicateLogicalIds -join ', ')"
    } else {
        "$($logicalIds.Count) unique logical IDs."
    })

$catalogPath = Join-Path $FabricRoot 'catalog\fabric-items.json'
$catalog = Read-JsonFile -Path $catalogPath
if ($null -ne $catalog) {
    Add-Result -Name 'catalog-version' -Passed ($catalog.schemaVersion -eq 1) `
        -Detail "schemaVersion=$($catalog.schemaVersion)"
    $itemKeys = @($catalog.items | ForEach-Object { [string]$_.key })
    $duplicateKeys = @(
        $itemKeys | Group-Object | Where-Object Count -gt 1 | ForEach-Object Name
    )
    Add-Result -Name 'catalog-unique-item-keys' -Passed ($duplicateKeys.Count -eq 0) `
        -Detail $(if ($duplicateKeys.Count) { $duplicateKeys -join ', ' } else { "$($itemKeys.Count) item keys." })

    foreach ($item in $catalog.items) {
        foreach ($dependency in @($item.dependencies)) {
            Add-Result -Name "dependency:$($item.key):$dependency" `
                -Passed ([string]$dependency -in $itemKeys) `
                -Detail 'Dependency must reference a catalog item key.'
        }
        if (-not [bool]$item.createWithoutDefinition) {
            $sourceDirectory = Join-Path $FabricRoot ([string]$item.sourceDirectory)
            Add-Result -Name "source:$($item.key)" `
                -Passed (Test-Path -LiteralPath $sourceDirectory -PathType Container) `
                -Detail $sourceDirectory
            foreach ($part in @($item.definitionParts)) {
                $partPath = Join-Path $sourceDirectory ([string]$part)
                Add-Result -Name "part:$($item.key):$part" `
                    -Passed (Test-Path -LiteralPath $partPath -PathType Leaf) `
                    -Detail $partPath
            }
        }
        if ([string]$item.automationTier -eq 'automaticAfterBindingGate') {
            Add-Result -Name "binding-gate:$($item.key)" `
                -Passed (-not [string]::IsNullOrWhiteSpace([string]$item.bindingGate)) `
                -Detail "bindingGate=$($item.bindingGate)"
        }
    }

    foreach ($manual in $catalog.manualAssets) {
        $manualPath = Join-Path $FabricRoot ([string]$manual.sourcePath)
        Add-Result -Name "manual-asset:$($manual.key)" `
            -Passed (Test-Path -LiteralPath $manualPath -PathType Leaf) `
            -Detail $manualPath
        Add-Result -Name "manual-evidence:$($manual.key)" `
            -Passed (@($manual.completionEvidence).Count -gt 0) `
            -Detail "$(@($manual.completionEvidence).Count) evidence requirements."
    }
}

$allowedTokenPattern = '^\{\{(?:environment|workspace\.[A-Za-z0-9]+(?:\.id|\.displayName)|item\.[A-Za-z0-9]+(?:\.id|\.displayName)|retention\.[A-Za-z0-9]+|onelake\.(?:landingTablesUri|coreTablesUri))\}\}$'
$definitionFiles = @()
if ($null -ne $catalog) {
    foreach ($item in $catalog.items | Where-Object { -not [bool]$_.createWithoutDefinition }) {
        $sourceDirectory = Join-Path $FabricRoot ([string]$item.sourceDirectory)
        foreach ($part in @($item.definitionParts)) {
            $definitionFiles += Join-Path $sourceDirectory ([string]$part)
        }
    }
}
$badTokens = [System.Collections.Generic.List[string]]::new()
foreach ($definitionFile in $definitionFiles | Sort-Object -Unique) {
    if (-not (Test-Path -LiteralPath $definitionFile -PathType Leaf)) { continue }
    $content = Get-Content -LiteralPath $definitionFile -Raw -Encoding UTF8
    foreach ($match in [regex]::Matches($content, '\{\{[^{}]+\}\}')) {
        if ($match.Value -notmatch $allowedTokenPattern) {
            $badTokens.Add("$definitionFile -> $($match.Value)")
        }
    }
}
Add-Result -Name 'definition-token-contract' -Passed ($badTokens.Count -eq 0) `
    -Detail $(if ($badTokens.Count) { $badTokens -join '; ' } else { 'All definition tokens are catalogued.' })

$kqlSchemaPath = Join-Path $FabricRoot 'items\kql-ns-operations.KQLDatabase\DatabaseSchema.kql'
$kql = Get-Content -LiteralPath $kqlSchemaPath -Raw -Encoding UTF8
$requiredKqlTables = @(
    'telemetry_hot',
    'alarm_hot',
    'gateway_health_hot',
    'model_inference_hot',
    'ingest_quarantine_hot'
)
foreach ($table in $requiredKqlTables) {
    Add-Result -Name "kql-table:$table" `
        -Passed ($kql -match "(?im)^\s*\.create-merge\s+table\s+$([regex]::Escape($table))\b") `
        -Detail 'Required hot table create-merge command.'
}
$requiredFunctions = @(
    'fn_latest_telemetry',
    'fn_active_alarms',
    'fn_gateway_status',
    'fn_latest_model_scores',
    'fn_data_freshness',
    'fn_quarantine_rate'
)
foreach ($functionName in $requiredFunctions) {
    Add-Result -Name "kql-function:$functionName" `
        -Passed ($kql -match "(?im)\.create-or-alter\s+function.*\b$([regex]::Escape($functionName))\s*\(") `
        -Detail 'Required reusable KQL function.'
}
$requiredViews = @(
    'mv_telemetry_latest_by_signal',
    'mv_telemetry_1m',
    'mv_alarm_current',
    'mv_gateway_latest',
    'mv_model_latest',
    'mv_quarantine_15m'
)
foreach ($viewName in $requiredViews) {
    Add-Result -Name "kql-view:$viewName" `
        -Passed ($kql -match "(?im)\.create-or-alter\s+materialized-view.*\b$([regex]::Escape($viewName))\b") `
        -Detail 'Required KQL materialized view.'
}
$destructiveKql = [regex]::Matches($kql, '(?im)^\s*\.(?:drop|clear|purge|delete)\b')
Add-Result -Name 'kql-no-destructive-management' -Passed ($destructiveKql.Count -eq 0) `
    -Detail "$($destructiveKql.Count) destructive commands."

$eventstreamPath = Join-Path $FabricRoot 'items\es-ns-telemetry-v1.Eventstream\eventstream.json'
$eventstream = Read-JsonFile -Path $eventstreamPath
if ($null -ne $eventstream) {
    $customSources = @($eventstream.sources | Where-Object type -eq 'CustomEndpoint')
    Add-Result -Name 'eventstream-custom-endpoint' -Passed ($customSources.Count -eq 1) `
        -Detail "$($customSources.Count) Custom Endpoint source."
    $destinationNames = @($eventstream.destinations | ForEach-Object name)
    foreach ($destination in @(
        'landing-bronze-envelope',
        'kql-telemetry-hot',
        'kql-alarm-hot',
        'kql-gateway-health-hot',
        'kql-model-inference-hot',
        'kql-ingest-quarantine-hot'
    )) {
        Add-Result -Name "eventstream-destination:$destination" `
            -Passed ($destination -in $destinationNames) `
            -Detail 'Required dual-path destination.'
    }
    $eventstreamRaw = Get-Content -LiteralPath $eventstreamPath -Raw -Encoding UTF8
    Add-Result -Name 'eventstream-no-credential' `
        -Passed ($eventstreamRaw -notmatch '(?i)(sas|password|secret|connectionString|accessKey)') `
        -Detail 'Eventstream definition contains identifiers only.'
}

$medallionPath = Join-Path $FabricRoot 'lakehouse\schema\medallion-catalog.json'
$medallion = Read-JsonFile -Path $medallionPath
$requiredTables = @(
    'bronze_event_envelope',
    'bronze_batch_mes',
    'bronze_batch_cmms',
    'bronze_batch_market',
    'quarantine_event',
    'quarantine_batch',
    'fact_telemetry',
    'fact_energy_interval',
    'fact_quality_measurement',
    'fact_maintenance_event',
    'fact_model_inference',
    'fact_ai_decision',
    'dim_plant',
    'dim_asset',
    'dim_sensor',
    'dim_grade',
    'dim_calendar',
    'fact_energy_daily',
    'fact_emissions_daily',
    'fact_production_shift',
    'fact_quality_yield',
    'fact_furnace_rul',
    'fact_dispatch_recommendation',
    'fact_knowledge_procedure',
    'fact_ai_decision_audit'
)
if ($null -ne $medallion) {
    $zones = @($medallion.zones | ForEach-Object name)
    Add-Result -Name 'medallion-zones' `
        -Passed ((@('bronze', 'silver', 'gold') | Where-Object { $_ -notin $zones } | Measure-Object).Count -eq 0) `
        -Detail ($zones -join ', ')
    $allTables = @($medallion.zones.tables | ForEach-Object name)
    foreach ($table in $requiredTables) {
        Add-Result -Name "lakehouse-table:$table" -Passed ($table -in $allTables) `
            -Detail 'Required architecture table contract.'
    }
    foreach ($zone in $medallion.zones) {
        foreach ($table in $zone.tables) {
            $columnNames = @($table.columns | ForEach-Object name)
            $missingKeys = @($table.primaryKey | Where-Object { [string]$_ -notin $columnNames })
            Add-Result -Name "lakehouse-keys:$($table.name)" `
                -Passed ($missingKeys.Count -eq 0) `
                -Detail $(if ($missingKeys.Count) { "Missing columns: $($missingKeys -join ', ')" } else { 'Primary key columns exist.' })
            Add-Result -Name "lakehouse-no-sensor-partition:$($table.name)" `
                -Passed ('sensor_id' -notin @($table.partitionBy)) `
                -Detail "Partitions: $(@($table.partitionBy) -join ', ')"
        }
    }
    $sql = (
        Get-ChildItem -LiteralPath (Join-Path $FabricRoot 'lakehouse\sql') -File -Filter '*.sql' |
            ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 }
    ) -join "`n"
    foreach ($table in $allTables) {
        Add-Result -Name "ddl:$table" `
            -Passed ($sql -match "(?im)CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+$([regex]::Escape([string]$table))\b") `
            -Detail 'Spark SQL CREATE TABLE contract.'
    }
}

$dqPath = Join-Path $FabricRoot 'lakehouse\schema\data-quality-rules.json'
$dq = Read-JsonFile -Path $dqPath
if ($null -ne $dq) {
    $expectedReasons = @(
        'SCHEMA_INVALID',
        'UNKNOWN_ASSET',
        'LATE_BEYOND_POLICY',
        'DUPLICATE_CONFLICT',
        'INVALID_UNIT'
    )
    $actualReasons = @($dq.quarantineReasons)
    Add-Result -Name 'dq-quarantine-reasons' `
        -Passed (
            (@($expectedReasons | Where-Object { $_ -notin $actualReasons }).Count -eq 0) -and
            (@($actualReasons | Where-Object { $_ -notin $expectedReasons }).Count -eq 0)
        ) `
        -Detail ($actualReasons -join ', ')
    Add-Result -Name 'dq-reconciliation-zero' `
        -Passed ($dq.reconciliation.requiredUnexplainedRows -eq 0) `
        -Detail "requiredUnexplainedRows=$($dq.reconciliation.requiredUnexplainedRows)"
    foreach ($rule in $dq.rules) {
        if ($rule.action -eq 'quarantine') {
            Add-Result -Name "dq-reason:$($rule.id)" `
                -Passed ([string]$rule.quarantineReason -in $expectedReasons) `
                -Detail ([string]$rule.quarantineReason)
        }
    }
}

$notebookFiles = Get-ChildItem -LiteralPath (Join-Path $FabricRoot 'notebooks') `
    -Recurse -File -Filter 'notebook-content.py'
Add-Result -Name 'notebook-count' -Passed ($notebookFiles.Count -ge 5) `
    -Detail "$($notebookFiles.Count) notebook source files."
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
foreach ($notebook in $notebookFiles) {
    $source = Get-Content -LiteralPath $notebook.FullName -Raw -Encoding UTF8
    Add-Result -Name "notebook-marker:$($notebook.Directory.Name)" `
        -Passed ($source.StartsWith('# Fabric notebook source')) `
        -Detail 'FabricGitSource marker.'
    Add-Result -Name "notebook-no-package-install:$($notebook.Directory.Name)" `
        -Passed ($source -notmatch '(?im)^\s*(?:!|%pip|pip\s+install|python\s+-m\s+pip)') `
        -Detail 'No runtime package installation.'
    if ($pythonCommand) {
        & $pythonCommand.Source -c `
            'import ast,pathlib,sys; ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))' `
            $notebook.FullName
        Add-Result -Name "python-ast:$($notebook.Directory.Name)" `
            -Passed ($LASTEXITCODE -eq 0) `
            -Detail 'Python AST parse.'
    }
}
if (-not $pythonCommand) {
    Add-Result -Name 'python-ast' -Passed $false -Warning `
        -Detail 'python not found; notebook AST parse skipped.'
}

$demoScoring = Get-Content -LiteralPath (
    Join-Path $FabricRoot 'notebooks\ns-deterministic-demo-scoring.Notebook\notebook-content.py'
) -Raw -Encoding UTF8
foreach ($cue in @('240726', '21.0', '16.8', '27.5', '0.87', 'HEARTH-SECTOR-07')) {
    Add-Result -Name "demo-score-cue:$cue" -Passed ($demoScoring.Contains($cue)) `
        -Detail 'Deterministic documented cue.'
}
Add-Result -Name 'demo-score-prod-deny' `
    -Passed ($demoScoring -match 'hard-disabled outside dev/test/demo') `
    -Detail 'Synthetic scorer production hard deny.'

$pipelineFiles = Get-ChildItem -LiteralPath (Join-Path $FabricRoot 'pipelines') `
    -Recurse -File -Filter 'pipeline-content.json'
foreach ($pipelineFile in $pipelineFiles) {
    $pipeline = Read-JsonFile -Path $pipelineFile.FullName
    if ($null -ne $pipeline) {
        $activities = @($pipeline.properties.activities)
        Add-Result -Name "pipeline-activities:$($pipelineFile.Directory.Name)" `
            -Passed ($activities.Count -gt 0) `
            -Detail "$($activities.Count) activities."
        $activityNames = @($activities | ForEach-Object name)
        foreach ($activity in $activities) {
            foreach ($dependency in @($activity.dependsOn)) {
                Add-Result -Name "pipeline-dependency:$($activity.name)" `
                    -Passed ([string]$dependency.activity -in $activityNames) `
                    -Detail ([string]$dependency.activity)
            }
        }
    }
}

$kpiPath = Join-Path $FabricRoot 'semantic-model\measures\kpi-measures.json'
$kpis = Read-JsonFile -Path $kpiPath
$expectedKpis = @(
    'KPI-ENE-01', 'KPI-ENE-02', 'KPI-ENE-03',
    'KPI-CO2-01', 'KPI-CO2-02',
    'KPI-FUR-01', 'KPI-FUR-02', 'KPI-FUR-03',
    'KPI-QUA-01', 'KPI-QUA-02',
    'KPI-KNW-01', 'KPI-KNW-02',
    'KPI-TRUST-01', 'KPI-ADO-01', 'KPI-GOV-01'
)
if ($null -ne $kpis) {
    $actualKpis = @($kpis.measures | ForEach-Object kpiId)
    foreach ($kpi in $expectedKpis) {
        Add-Result -Name "semantic-kpi:$kpi" -Passed ($kpi -in $actualKpis) `
            -Detail 'Documented KPI measure mapping.'
    }
}
$dax = Get-Content -LiteralPath (
    Join-Path $FabricRoot 'semantic-model\measures\measures.dax'
) -Raw -Encoding UTF8
foreach ($measure in @(
    'KPI-ENE-01 SEC GJ per t',
    'KPI-CO2-01 Specific CO2 t per t',
    'KPI-FUR-01 Lining Lead Time Days',
    'KPI-QUA-01 High-Grade Yield Rate',
    'KPI-GOV-01 Audit Completeness',
    'OEE'
)) {
    Add-Result -Name "dax:$measure" -Passed ($dax.Contains($measure)) `
        -Detail 'Required DAX measure definition.'
}

$environmentFiles = @(
    'dev.example.json',
    'test.example.json',
    'demo.example.json',
    'prod.example.json',
    'environment.template.json'
)
foreach ($environmentFile in $environmentFiles) {
    $environmentPath = Join-Path $FabricRoot "deployment-parameters\$environmentFile"
    Add-Result -Name "environment-file:$environmentFile" `
        -Passed (Test-Path -LiteralPath $environmentPath -PathType Leaf) `
        -Detail $environmentPath
    if (Test-Path -LiteralPath $environmentPath -PathType Leaf) {
        $raw = Get-Content -LiteralPath $environmentPath -Raw -Encoding UTF8
        Add-Result -Name "environment-no-secrets:$environmentFile" `
            -Passed ($raw -notmatch '(?i)"(?:clientSecret|password|sasToken|sasKey|connectionString|accessKey|accountKey)"\s*:') `
            -Detail 'No secret-bearing parameter keys.'
    }
}
$demoParameters = Read-JsonFile -Path (
    Join-Path $FabricRoot 'deployment-parameters\demo.example.json'
)
$prodParameters = Read-JsonFile -Path (
    Join-Path $FabricRoot 'deployment-parameters\prod.example.json'
)
if ($null -ne $demoParameters) {
    Add-Result -Name 'demo-parameter-boundary' `
        -Passed (
            [bool]$demoParameters.syntheticOnly -and
            [string]$demoParameters.dataClassification -eq 'SYNTHETIC' -and
            @($demoParameters.workspaces.PSObject.Properties |
                Where-Object { -not ([string]$_.Value.displayName).StartsWith('NS-DEMO-') }).Count -eq 0
        ) `
        -Detail 'Demo is synthetic-only and all workspace names use NS-DEMO-.'
}
if ($null -ne $prodParameters) {
    Add-Result -Name 'prod-lifecycle-hard-deny' `
        -Passed (-not [bool]$prodParameters.lifecycle.automationEnabled) `
        -Detail "automationEnabled=$($prodParameters.lifecycle.automationEnabled)"
}

$powerShellFiles = Get-ChildItem -LiteralPath $PSScriptRoot -File |
    Where-Object Extension -in @('.ps1', '.psm1')
foreach ($powerShellFile in $powerShellFiles) {
    $tokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $powerShellFile.FullName,
        [ref]$tokens,
        [ref]$parseErrors
    ) | Out-Null
    Add-Result -Name "powershell-parse:$($powerShellFile.Name)" `
        -Passed ($parseErrors.Count -eq 0) `
        -Detail $(if ($parseErrors.Count) {
            ($parseErrors | ForEach-Object Message) -join '; '
        } else {
            'PowerShell parser clean.'
        })
}

$readme = Get-Content -LiteralPath (Join-Path $FabricRoot 'README.md') -Raw -Encoding UTF8
Add-Result -Name 'bicep-boundary' `
    -Passed (
        $readme.Contains('does **not** deploy Fabric SaaS') -and
        $readme.Contains('Microsoft.Fabric/capacities')
    ) `
    -Detail 'README explicitly limits Bicep to the capacity/Azure control plane.'

$lifecycleScript = Get-Content -LiteralPath (
    Join-Path $PSScriptRoot 'Invoke-FabricCapacityLifecycle.ps1'
) -Raw -Encoding UTF8
foreach ($contractText in @(
    '2023-11-01',
    "environment -eq 'prod'",
    'SKIPPED_BUSY',
    'relayDrainedOrCheckpointed',
    'Azure-AsyncOperation',
    'Retry-After'
)) {
    Add-Result -Name "capacity-contract:$contractText" `
        -Passed ($lifecycleScript.Contains($contractText)) `
        -Detail 'Required lifecycle safeguard.'
}

$result = [pscustomobject]@{
    status      = if ($errors.Count -eq 0) { 'PASS' } else { 'FAIL' }
    checkedAt   = [DateTimeOffset]::UtcNow.ToString('o')
    fabricRoot  = $FabricRoot
    checkCount  = $checks.Count
    errorCount  = $errors.Count
    warningCount = $warnings.Count
    errors      = $errors.ToArray()
    warnings    = $warnings.ToArray()
    checks      = $checks.ToArray()
}
$result | ConvertTo-Json -Depth 30
if ($errors.Count -gt 0) {
    exit 1
}
