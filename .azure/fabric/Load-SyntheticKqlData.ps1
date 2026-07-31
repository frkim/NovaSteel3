<#
.SYNOPSIS
    Injects deterministic synthetic demo data into the NovaSteel KQL tables via
    .ingest inline commands. Run AFTER Apply-KqlSchema.ps1 succeeds.
#>
[CmdletBinding()]
param(
    [string]$ClusterUri   = 'https://trd-q10bnypm07cdfv120p.z8.kusto.fabric.microsoft.com',
    [string]$DatabaseName = '7c3ab91a-c8ac-4658-83b5-f500dad946ec',
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Acquiring Kusto token..." -ForegroundColor Cyan
$token = (& az account get-access-token --resource https://help.kusto.windows.net --query accessToken --output tsv).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) {
    throw 'Failed to acquire Kusto access token.'
}

$headers  = @{ Authorization = "Bearer $token"; Accept = 'application/json'; 'Content-Type' = 'application/json' }
$mgmtUri  = "$($ClusterUri.TrimEnd('/'))/v1/rest/mgmt"
$base     = [datetime]::new(2026, 7, 31, 8, 0, 0, [System.DateTimeKind]::Utc)
$scenario = 'NS-DEMO-synthetic-load'
$plants   = @('NS-DEMO-LUX-01','NS-DEMO-BE-01','NS-DEMO-NL-01','NS-DEMO-DE-01')
$assets   = @('NS-DEMO-BF-01','NS-DEMO-EAF-01','NS-DEMO-RF-01','NS-DEMO-CC-01')
$signals  = @('hearth_shell_temperature','cooling_water_flow','local_heat_flux','production_rate','rolling_force','strip_speed','electrode_voltage','tap_temperature')

function Invoke-KqlCommand {
    param([string]$Csl, [string]$Label)
    $preview = $Csl.Substring(0, [Math]::Min(80, $Csl.Length)) + '...'
    Write-Host "  $Label" -ForegroundColor DarkCyan
    if ($WhatIf) { Write-Host "  [WhatIf] $preview" -ForegroundColor DarkGray; return }
    $body = @{ csl = $Csl; db = $DatabaseName; properties = @{ Options = @{ queryconsistency = 'weakconsistency' } } } | ConvertTo-Json -Depth 5 -Compress
    $r = Invoke-WebRequest -Uri $mgmtUri -Method POST -Headers $headers -Body $body -ContentType 'application/json' -SkipHttpErrorCheck -ErrorAction Stop
    if ($r.StatusCode -ge 400) { Write-Warning "  HTTP $($r.StatusCode): $($r.Content.Substring(0,[Math]::Min(300,$r.Content.Length)))"; return }
    Write-Host "  OK ($($r.StatusCode))" -ForegroundColor Green
}

function Ts([int]$minOffset) { return $base.AddMinutes($minOffset).ToString('yyyy-MM-ddTHH:mm:ssZ') }

# ---------------------------------------------------------------------------
# telemetry_hot  (200 rows, 4 plants x 8 signals x ~6 timestamps each)
# ---------------------------------------------------------------------------
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Loading telemetry_hot..." -ForegroundColor Cyan
$telRows = [System.Collections.Generic.List[string]]::new()
$valueMap = @{
    'hearth_shell_temperature' = @(1180,1195,1210,1205,1190,1220,'Celsius','Good')
    'cooling_water_flow'       = @(120,115,118,122,117,119,'m3/h','Good')
    'local_heat_flux'          = @(42.1,43.5,44.0,41.8,43.2,42.7,'kW/m2','Good')
    'production_rate'          = @(95.0,97.5,94.0,96.2,98.1,93.5,'t/h','Good')
    'rolling_force'            = @(2800,2850,2750,2900,2820,2780,'kN','Good')
    'strip_speed'              = @(12.5,13.0,12.8,13.2,12.3,12.9,'m/s','Good')
    'electrode_voltage'        = @(610,615,608,620,612,618,'V','Good')
    'tap_temperature'          = @(1680,1695,1670,1685,1690,1675,'Celsius','Good')
}
$row = 0
for ($pi = 0; $pi -lt $plants.Count; $pi++) {
    $plant = $plants[$pi]
    $asset = $assets[$pi]
    for ($si = 0; $si -lt $signals.Count; $si++) {
        $signal = $signals[$si]
        $vals   = $valueMap[$signal]
        for ($ti = 0; $ti -lt 6; $ti++) {
            $t   = Ts(($pi * 30) + ($si * 4) + $ti)
            $val = $vals[$ti % 6]
            $unit= $vals[6]
            $q   = $vals[7]
            $eid = "NS-DEMO-TEL-$($row.ToString('D5'))"
            $sid = "NS-DEMO-SEN-$($pi.ToString('D2'))$($si.ToString('D2'))"
            $telRows.Add("$eid,$t,$t,NS-DEMO-GW-$pi,$plant,$asset,$row,NS-DEMO-CORR-$row,novasteel.telemetry.v1,1,SYNTHETIC,DEMO-NONPERSONAL,$scenario,100,sim/1.0,live,$sid,$signal,$val,$unit,$q,0.5,1000,{}")
            $row++
        }
    }
}
$telCsv  = $telRows -join "`n"
Invoke-KqlCommand -Label "Insert $($telRows.Count) telemetry rows" -Csl ".ingest inline into table telemetry_hot <|`n$telCsv"

# ---------------------------------------------------------------------------
# alarm_hot  (30 rows)
# ---------------------------------------------------------------------------
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Loading alarm_hot..." -ForegroundColor Cyan
$alarmTypes = @('HeatExcess','CoolantLow','HighVibration','QualityAlert','EnergySpike','PressureLow')
$severities = @('Critical','High','High','Medium','Medium','Low')
$states     = @('Active','Active','Acknowledged','Resolved','Active','Resolved')
$alarmRows  = [System.Collections.Generic.List[string]]::new()
for ($i = 0; $i -lt 30; $i++) {
    $pi    = $i % 4
    $at    = $alarmTypes[$i % 6]
    $sev   = $severities[$i % 6]
    $state = $states[$i % 6]
    $t     = Ts($i * 20 - 600)
    $eid   = "NS-DEMO-ALM-EV-$($i.ToString('D4'))"
    $aid   = "NS-DEMO-ALM-$($i.ToString('D4'))"
    $tid   = "NS-DEMO-ALM-TR-$($i.ToString('D4'))"
    $plant = $plants[$pi]; $asset = $assets[$pi]
    $thr   = 1200.0 + ($i % 5) * 10
    $obs   = $thr + 15.0 + ($i % 3) * 5
    $alarmRows.Add("$eid,$aid,$tid,$t,$t,NS-DEMO-GW-$pi,$plant,$asset,$at,$sev,Alarm: $at,Auto-detected deviation,$state,$thr,$obs,Celsius,0.92,SYSTEM,NS-DEMO-MON,high-confidence,NS-DEMO-WO-$($i.ToString('D3')),NS-DEMO-CORR-ALM-$i,novasteel.alarm.v1,1,SYNTHETIC,DEMO-NONPERSONAL,$scenario,100,{}")
}
$alarmCsv  = $alarmRows -join "`n"
Invoke-KqlCommand -Label "Insert $($alarmRows.Count) alarm rows" -Csl ".ingest inline into table alarm_hot <|`n$alarmCsv"

# ---------------------------------------------------------------------------
# gateway_health_hot  (20 rows)
# ---------------------------------------------------------------------------
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Loading gateway_health_hot..." -ForegroundColor Cyan
$connStates = @('Connected','Connected','Connected','Degraded')
$gwRows     = [System.Collections.Generic.List[string]]::new()
for ($i = 0; $i -lt 20; $i++) {
    $pi    = $i % 4
    $plant = $plants[$pi]
    $gw    = "NS-DEMO-GW-$pi"
    $cs    = $connStates[$i % 4]
    $t     = Ts($i * 15 - 300)
    $lag   = if ($cs -eq 'Degraded') { 5500 + $i * 100 } else { 150 + $i * 10 }
    $eid   = "NS-DEMO-GH-$($i.ToString('D4'))"
    $gwRows.Add("$eid,$t,$t,$t,NS-DEMO-SRC-$pi,$gw,$plant,$cs,0,$(1000 + $i * 10),${i},,$lag,12,0,0,NS-DEMO-CORR-GH-$i,novasteel.gateway-health.v1,1,SYNTHETIC,DEMO-NONPERSONAL,$scenario,100,{}")
}
$gwCsv  = $gwRows -join "`n"
Invoke-KqlCommand -Label "Insert $($gwRows.Count) gateway_health rows" -Csl ".ingest inline into table gateway_health_hot <|`n$gwCsv"

# ---------------------------------------------------------------------------
# model_inference_hot  (50 rows — RUL and quality scores)
# ---------------------------------------------------------------------------
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Loading model_inference_hot..." -ForegroundColor Cyan
$predTypes  = @('furnace_rul','quality_yield')
$rulAssets  = @('NS-DEMO-BF-01','NS-DEMO-RF-01')
$miRows     = [System.Collections.Generic.List[string]]::new()
for ($i = 0; $i -lt 50; $i++) {
    $pi    = $i % 4
    $plant = $plants[$pi]
    $pt    = $predTypes[$i % 2]
    $asset = if ($pt -eq 'furnace_rul') { $rulAssets[$pi % 2] } else { $assets[$pi % 4] }
    $t     = Ts($i * 30 - 1200)
    $p50   = if ($pt -eq 'furnace_rul') { 21.0 - ($i % 10) * 0.3 } else { 0.0 }
    $p10   = if ($pt -eq 'furnace_rul') { $p50 * 0.85 } else { 0.0 }
    $p90   = if ($pt -eq 'furnace_rul') { $p50 * 1.15 } else { 0.0 }
    $lmm   = if ($pt -eq 'furnace_rul') { 220.0 - ($i % 15) * 3.5 } else { 0.0 }
    $risk  = [Math]::Round(0.6 + ($i % 20) * 0.017, 3)
    $sev   = if ($risk -gt 0.85) { 'HIGH' } elseif ($risk -gt 0.70) { 'MEDIUM' } else { 'LOW' }
    $qrisk = [Math]::Round(0.3 + ($i % 15) * 0.02, 3)
    $fpyld = [Math]::Round(0.88 + ($i % 10) * 0.005, 3)
    $eid   = "NS-DEMO-MI-$($i.ToString('D4'))"
    $iid   = "NS-DEMO-INF-$($i.ToString('D4'))"
    $comp  = if ($pt -eq 'furnace_rul') { 'furnace_lining' } else { 'quality_gate' }
    $miRows.Add("$eid,$iid,$t,$t,$t,$t,$plant,$asset,$comp,novasteel-rul-v2,2.0.0,$pt,$p10,$p50,$p90,$lmm,$risk,$sev,$qrisk,$fpyld,0.87,[],HIGH,NS-DEMO-CORR-MI-$i,novasteel.model-inference.v1,1,SYNTHETIC,DEMO-NONPERSONAL,$scenario,100,{}")
}
$miCsv  = $miRows -join "`n"
Invoke-KqlCommand -Label "Insert $($miRows.Count) model_inference rows" -Csl ".ingest inline into table model_inference_hot <|`n$miCsv"

# ---------------------------------------------------------------------------
# ingest_quarantine_hot  (10 rows)
# ---------------------------------------------------------------------------
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Loading ingest_quarantine_hot..." -ForegroundColor Cyan
$qReasons = @('unknown_unit','missing_asset_id','duplicate_event','schema_version_mismatch','value_out_of_range')
$qRows    = [System.Collections.Generic.List[string]]::new()
for ($i = 0; $i -lt 10; $i++) {
    $pi    = $i % 4
    $plant = $plants[$pi]
    $t     = Ts($i * 60 - 600)
    $qid   = "NS-DEMO-QR-$($i.ToString('D4'))"
    $eid   = "NS-DEMO-QE-$($i.ToString('D4'))"
    $reason= $qReasons[$i % 5]
    $qRows.Add("$qid,$t,$eid,$t,$t,NS-DEMO-GW-$pi,$plant,${assets[$pi]},novasteel.telemetry.v1,1,$reason,Automated quarantine rule QR-$(($i%5)+1),Celsius,bar,,{},NS-DEMO-CORR-QR-$i,SYNTHETIC,DEMO-NONPERSONAL,$scenario,100")
}
$qCsv  = $qRows -join "`n"
Invoke-KqlCommand -Label "Insert $($qRows.Count) quarantine rows" -Csl ".ingest inline into table ingest_quarantine_hot <|`n$qCsv"

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Synthetic KQL data load complete." -ForegroundColor Green


