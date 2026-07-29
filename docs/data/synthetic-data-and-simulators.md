# NovaSteel Synthetic Data and Simulator Specification

## 1. Purpose and guardrails

This specification defines realistic, fully synthetic data for demonstrating the NovaSteel platform without using production records, personal data, customer formulas, or plant-confidential operating limits. The data must preserve plausible steelmaking relationships while remaining visibly unsuitable for operational control.

Every generated record carries:

```json
{
  "data_classification": "SYNTHETIC",
  "privacy_label": "DEMO-NONPERSONAL",
  "generator_version": "novasteel-sim/1.0.0",
  "scenario_id": "demo-21d-warning",
  "seed": 240725
}
```

Rules:

- Never mix synthetic and production topics, storage accounts, workspaces, or semantic models.
- Prefix synthetic entities with `NS-DEMO-` and add a visible **Synthetic demo data** banner in every UI.
- Use invented operator identifiers such as `OP-DEMO-014`; do not generate names, voices, emails, or free text modeled on real people.
- Generated maintenance notes and interviews are templates composed from an approved synthetic phrase library.
- Synthetic data is not a safety system and must not be used to set equipment controls.
- All timestamps are UTC ISO 8601; plant local time is a derived presentation field with the plant time zone.

The committed local fixture pack is checksum-protected and is not rewritten for
each demo day. When the BFF loads it in local demo mode, it can rebase fixture
timestamps in memory by a whole number of days so the newest synthetic event
lands within the last 24 hours while preserving hour-of-day patterns. Set
`DEMO_CLOCK_REBASE=false` to serve the byte-faithful fixture timestamps for
contract tests or forensic replay.

The analytics micro-frontend keeps its own offline fixture pack for the
zero-network fallback rung, and it is anchored the same way:
`apps\analytics-mfe\src\utils\demoClock.ts` resolves the authored fixture day
onto the most recent 18:45 UTC snapshot at or before now, and every offline
timestamp, the device `asOf` marker, the maintenance-planner Gantt baseline and
the lining-inspection dates are derived from it. Neither side regenerates or
reseeds anything — both shift an authored dataset by whole days so a predicted
failure date or a planned work order never lands in the past. The anchors are
resolved at module load, so a browser tab left open across midnight keeps the
previous day until it is reloaded.

Because the pack is verified by SHA-256, it has to be **byte-exact on every
platform**. The generator writes every output — NDJSON, `manifest.json` and
`checksums.json` — with `newline="\n"`, and `.gitattributes` pins
`services/bff-api/fixtures/**` to LF so a Windows clone with
`core.autocrlf=true` cannot silently rewrite the line endings. Without both,
the digests stop matching on checkout and the BFF refuses to start.
`services\bff-api\tests\test_fixture_integrity.py` fails loudly if either
guard is removed.

## 2. Demonstration estate

### 2.1 Plants

| Plant ID | Synthetic name | Country | Time zone | Process focus | Nominal annual output |
|---|---|---|---|---|---:|
| `NS-DEMO-LUX-01` | Moselle Integrated Works | Luxembourg | Europe/Luxembourg | Blast furnace, basic oxygen furnace, hot strip mill | 3.2 Mt |
| `NS-DEMO-DE-01` | Saarbrücken Steelworks | Germany | Europe/Berlin | Electric arc furnace, ladle furnace, billet caster | 2.4 Mt |
| `NS-DEMO-BE-01` | Liège Melt & Rolling Works | Belgium | Europe/Brussels | Electric arc furnace, caster, cold rolling, galvanizing | 1.5 Mt |
| `NS-DEMO-ES-01` | Asturias Long Products | Spain | Europe/Madrid | Electric arc furnace, billet caster, wire rod mill | 1.1 Mt |

The default 10-minute demo focuses on `NS-DEMO-LUX-01`. The other plants provide fleet comparisons and enough history for cross-site analytics.

### 2.2 Asset hierarchy

`enterprise > plant > area > line > asset > component > sensor`

| Asset ID | Area | Asset type | Key components/sensors |
|---|---|---|---|
| `LUX-BF-01` | Ironmaking | Blast furnace | Hearth lining zones 01-12, shell thermocouples, cooling circuits, pressure, burden probes |
| `LUX-BOF-01` | Steelmaking | Basic oxygen furnace | Lance, vessel lining, off-gas analyzer, tilt drive |
| `LUX-CC-01` | Casting | Slab caster | Mold, strands 1-2, secondary cooling, withdrawal drive |
| `LUX-RHF-01` | Rolling | Reheat furnace | Zones preheat/heat/soak, burners, oxygen probes |
| `LUX-HSM-01` | Rolling | Hot strip mill | Roughing stands R1-R2, finishing stands F1-F7, descaler, coiler |
| `LUX-UTIL-01` | Utilities | Energy system | Electricity, natural gas, oxygen, steam, compressed air meters |

Reference assets at the other plants use the same pattern with `DE`, `BE`, or `ES` prefixes. Each sensor has a stable ID such as `LUX-BF-01-TC-H07-03`.

## 3. Dataset catalog

### 3.1 Dataset summary

| Dataset | Grain | Main keys | Retention in demo | Typical rate | Approximate volume/day |
|---|---|---|---|---:|---:|
| `telemetry_furnace` | Sensor observation | `event_id`, `sensor_id`, `event_ts` | 90 days hot, 3 years lake | 1-10 seconds | 5.2M |
| `telemetry_rolling` | Sensor observation | same | 30 days hot, 2 years lake | 100 ms-10 seconds | 14.8M raw; 2.1M demo-thinned |
| `energy_interval` | Meter/interval | `meter_id`, `interval_start` | 3 years | 1 minute; price 15 minutes | 28.8K |
| `heat_batch` | Heat/coil/slab genealogy event | `material_id`, `operation_id` | 5 years | Event-driven | 4K |
| `quality_measurement` | Test/measurement | `sample_id`, `characteristic_code` | 5 years | Event-driven | 40K |
| `maintenance_event` | Work order/action | `work_order_id`, `event_ts` | 5 years | Event-driven | 50 |
| `alarm_event` | Alarm lifecycle transition | `alarm_id`, `event_ts` | 1 year | Event-driven | 100 |
| `operator_knowledge` | Interview utterance/fact/procedure | `interview_id`, `segment_id` | Demo session | Event-driven | 100 segments |
| `reference_*` | Master/reference row | Natural key + validity | Full history | On change | <10K |
| `model_inference` | Asset/material prediction | `inference_id` | 3 years | 1-15 minutes | 25K |

Volumes are design targets, not production claims. The demo may use a 1:60 accelerated clock and pre-aggregated history while preserving event-time semantics.

### 3.2 Furnace and process data

Signals for `LUX-BF-01`:

| Signal | Unit | Normal range | Demo sampling | Relationship |
|---|---|---:|---:|---|
| Hearth shell temperature | °C | 75-185 | 5 s | Rises with lining loss and local heat flux |
| Cooling-water inlet temperature | °C | 20-36 | 5 s | Ambient and season dependent |
| Cooling-water outlet temperature | °C | 28-58 | 5 s | Inlet plus heat extraction / flow |
| Cooling-water flow | m³/h | 110-310 per circuit | 5 s | Lower flow increases shell temperature with lag |
| Local heat flux | kW/m² | 35-190 | 5 s | Derived from flow, water ΔT, and cooled area |
| Hearth refractory estimate | mm | 280-950 | 15 min inference | Monotonic trend plus bounded model noise |
| Hot blast temperature | °C | 1,050-1,250 | 10 s | Affects thermal load and fuel rate |
| Top pressure | bar(g) | 1.4-2.6 | 1 s | Correlates with blast and permeability |
| Pulverized coal injection | kg/t hot metal | 100-190 | 1 min | Inversely influences coke rate |
| Hot metal temperature | °C | 1,440-1,530 | Per tap | Influences downstream energy demand |
| Production rate | t/h | 180-360 | 1 min | Drives heat load and utility use |

BOF and caster event data include heat number, charge mix, oxygen volume, tap temperature, treatment time, caster speed, mold level, cooling rate, and slab dimensions. Heat numbers are synthetic, for example `H-LUX-260725-0042`.

### 3.3 Rolling-mill data

| Signal | Unit | Normal range | Sampling |
|---|---|---:|---:|
| Reheat-zone temperature | °C | 850-1,285 | 2 s |
| Furnace gas flow | Nm³/h | 4,000-42,000 | 2 s |
| Furnace excess O₂ | % vol | 0.8-4.5 | 2 s |
| Slab discharge temperature | °C | 1,160-1,270 | Per slab |
| Stand motor current | A | 1,000-12,000 | 100 ms raw, 1 s demo |
| Rolling force | MN | 4-38 | 100 ms raw, 1 s demo |
| Entry/exit thickness | mm | 1.2-250 by stage | 100 ms raw, per coil summary |
| Strip speed | m/s | 0.2-22 | 100 ms raw, 1 s demo |
| Finishing temperature | °C | 820-940 | Per coil |
| Coiling temperature | °C | 520-720 | Per coil |
| Flatness | I-unit | -20 to 20 | Per coil and 10 m segment |

Relationships include conservation of mass within 0.8%, increasing motor power with rolling force and speed, decreasing thickness through successive stands, and grade-specific temperature targets.

### 3.4 Energy, emissions, and market data

| Field | Unit | Plausible range |
|---|---|---:|
| Electricity demand | MW | 8-180 by plant |
| Electricity consumption | MWh/interval | Derived |
| Natural gas flow | MWh(th)/h | 5-220 |
| Oxygen flow | kNm³/h | 0-95 |
| Steam export/import | t/h | -80 to 120 |
| Grid carbon intensity | kgCO₂e/MWh | 35-650 |
| EU ETS allowance price | EUR/tCO₂e | 55-130 |
| Day-ahead electricity spot price | EUR/MWh | -50 to 350 normally; capped synthetic stress at 600 |
| Scope 1 process emissions | kgCO₂e/t product | 700-2,100 by route |
| Scope 2 location-based emissions | kgCO₂e/t | Derived from meter and carbon intensity |

Spot-price scenarios:

1. `baseline-summer`: smooth diurnal profile, 55-115 EUR/MWh.
2. `renewables-midday`: midday trough from -10 to 35 EUR/MWh.
3. `evening-scarcity`: 17:00-20:00 spike from 180 to 350 EUR/MWh.
4. `stress-price-spike`: one 15-minute interval at 600 EUR/MWh, clearly tagged synthetic.

The optimization scenario may shift reheat batches and EAF starts only inside approved scheduling windows. It never changes safety limits, promised delivery dates, minimum soak times, or metallurgical recipes. Report both baseline and optimized cost, energy, carbon, production delay, and constraint status.

### 3.5 Quality and genealogy data

The synthetic genealogy graph is:

`raw material lots -> heat -> ladle treatment -> slab/billet -> reheating -> coil/bar -> sample -> test result -> shipment`

Representative grades:

| Grade code | Synthetic use | Key targets |
|---|---|---|
| `NS-AUTO-DP780` | Automotive dual-phase sheet | Tensile 780-930 MPa, yield 450-620 MPa, elongation 12-20% |
| `NS-AUTO-HSLA420` | Automotive structural sheet | Yield 420-540 MPa, controlled flatness |
| `NS-LONG-B500` | Reinforcing bar | Yield 500-650 MPa |

Quality data includes chemistry (% mass), dimensions, surface defect class, tensile properties, hardness, flatness, and disposition. Chemistry uses compositional constraints: percentages are non-negative; major alloy sums stay plausible; carbon-equivalent is derived rather than sampled independently.

The demo quality-drift scenario gradually adds:

- +8 to +18 °C coiling-temperature bias over 36 simulated hours;
- +0.015 to +0.035 percentage-point carbon-equivalent shift within the synthetic recipe envelope;
- +3% to +7% finishing-stand force imbalance;
- increased probability of edge-wave and tensile deviation.

Drift is latent for the first 12 hours, produces early model warnings next, and generates visible off-target samples only later. Causal features remain correlated; defects are never assigned by a purely random toggle.

### 3.6 Maintenance and reliability data

Maintenance records include:

- asset/component, notification and work-order identifiers;
- detected, acknowledged, planned, started, and completed timestamps;
- symptom, failure mode, action code, labor hours, synthetic parts, and downtime;
- condition-monitoring snapshot references;
- inspection thickness measurements and uncertainty;
- model warning linkage and operator feedback.

Failure modes include refractory wear, cooling-circuit restriction, bearing vibration, roll wear, burner imbalance, thermocouple bias, and hydraulic leakage. Work-order notes are synthetic templates such as: “Demo inspection found localized warm zone near hearth sector 07; verify circuit flow and schedule ultrasound survey.”

### 3.7 Operator knowledge data

The knowledge-capture dataset has four layers:

1. `interview_session`: synthetic operator ID, role, plant, language, consent state, scenario.
2. `transcript_segment`: timestamps, synthetic transcript, STT confidence, speaker role.
3. `knowledge_fact`: normalized trigger, observation, action, rationale, cautions, source segment.
4. `procedure_draft`: ordered steps, prerequisites, safety boundary, reviewer status, citations.

All voices, if used, are licensed synthetic voices. The demo default is microphone input; offline fallback replays a pre-approved WAV and transcript. Captured guidance is always a **draft requiring expert review**, never an automatically approved work instruction.

## 4. Event contracts

### 4.1 Common envelope

```json
{
  "schema_name": "novasteel.telemetry.v1",
  "schema_version": 1,
  "event_id": "018f6dd0-b36a-7bd1-8ef8-087264aa8f21",
  "event_ts": "2026-07-25T08:15:10.000Z",
  "ingest_ts": "2026-07-25T08:15:10.420Z",
  "sequence": 82711,
  "source_id": "edge-LUX-01",
  "plant_id": "NS-DEMO-LUX-01",
  "asset_id": "LUX-BF-01",
  "scenario_id": "demo-21d-warning",
  "correlation_id": "run-20260725-a",
  "data_classification": "SYNTHETIC",
  "privacy_label": "DEMO-NONPERSONAL",
  "generator_version": "novasteel-sim/1.0.0",
  "seed": 240725,
  "payload": {}
}
```

Required envelope validation:

- `event_id` is UUIDv7 and globally unique.
- `event_ts <= ingest_ts + 5 seconds`; simulated future time is allowed only when `clock_mode=accelerated`.
- Sequence is strictly increasing per `source_id` and partition.
- Plant and asset exist in valid-time reference data at `event_ts`.
- Unknown fields are tolerated within a major schema version; required field removal requires a new major version.
- Duplicate `event_id` payloads are idempotent; conflicting duplicates are quarantined.

### 4.2 Telemetry payload

```json
{
  "schema_name": "novasteel.telemetry.v1",
  "schema_version": 1,
  "event_id": "018f6dd0-b36a-7bd1-8ef8-087264aa8f21",
  "event_ts": "2026-07-25T08:15:10.000Z",
  "ingest_ts": "2026-07-25T08:15:10.420Z",
  "sequence": 82711,
  "source_id": "edge-LUX-01",
  "plant_id": "NS-DEMO-LUX-01",
  "asset_id": "LUX-BF-01",
  "scenario_id": "demo-21d-warning",
  "correlation_id": "run-20260725-a",
  "data_classification": "SYNTHETIC",
  "privacy_label": "DEMO-NONPERSONAL",
  "generator_version": "novasteel-sim/1.0.0",
  "seed": 240725,
  "payload": {
    "sensor_id": "LUX-BF-01-TC-H07-03",
    "signal_code": "hearth_shell_temperature",
    "value": 171.4,
    "unit": "Cel",
    "quality": "GOOD",
    "uncertainty": 0.6,
    "sample_period_ms": 5000
  }
}
```

Use UCUM codes where possible: `Cel`, `bar`, `m3/h`, `kW/m2`, `MW`, `MWh`, `EUR/MWh`, `kg/t`, and `mm`. Store the canonical value and unit; presentation conversion is separate.

### 4.3 Material and quality event

```json
{
  "schema_name": "novasteel.quality-measurement.v1",
  "event_id": "018f6e11-95cb-7637-aabb-d68a41f26a05",
  "event_ts": "2026-07-25T08:30:00Z",
  "plant_id": "NS-DEMO-LUX-01",
  "asset_id": "LUX-HSM-01",
  "material_id": "COIL-LUX-260725-017",
  "heat_id": "H-LUX-260725-0042",
  "grade_code": "NS-AUTO-DP780",
  "sample_id": "LAB-260725-0091",
  "characteristic_code": "tensile_strength",
  "value": 801.2,
  "unit": "MPa",
  "lower_spec_limit": 780.0,
  "upper_spec_limit": 930.0,
  "measurement_method": "SYNTHETIC-LAB-TENSILE",
  "result_status": "PASS",
  "data_classification": "SYNTHETIC",
  "privacy_label": "DEMO-NONPERSONAL"
}
```

### 4.4 Model inference and alert

```json
{
  "schema_name": "novasteel.model-inference.v1",
  "inference_id": "INF-LUX-BF01-20260725T0830Z",
  "model_id": "lining-rul-piml",
  "model_version": "1.3.0-demo",
  "feature_snapshot_ts": "2026-07-25T08:30:00Z",
  "asset_id": "LUX-BF-01",
  "component_id": "HEARTH-SECTOR-07",
  "prediction": {
    "remaining_useful_life_days_p50": 19.65,
    "remaining_useful_life_days_p10": 18.69,
    "remaining_useful_life_days_p90": 20.61,
    "estimated_minimum_lining_mm": 344,
    "risk_score": 0.8995,
    "severity": "HIGH"
  },
  "top_factors": [
    {"feature": "heat_flux_6h_slope", "contribution": 0.29},
    {"feature": "sector_to_ring_temp_delta", "contribution": 0.24},
    {"feature": "cooling_efficiency_residual", "contribution": 0.18}
  ],
  "label": "degraded_lining",
  "scenario_id": "demo-21d-warning",
  "data_classification": "SYNTHETIC"
}
```

Alert lifecycle states are `OPEN -> ACKNOWLEDGED -> WORK_ORDER_LINKED -> MITIGATED -> CLOSED`. State transitions carry actor type (`DEMO_USER` or `SYSTEM`), reason, timestamp, and correlation ID.

## 5. Reference and slowly changing data

| Table | SCD approach | Notes |
|---|---|---|
| `reference_plant` | Type 2 | Name, time zone, region, route |
| `reference_asset` | Type 2 | Hierarchy, criticality, commissioned state |
| `reference_sensor` | Type 2 | Signal, unit, calibration, valid range, sampling rate |
| `reference_grade_recipe` | Type 2 | Synthetic target bands and approved process windows |
| `reference_tariff` | Type 2 | Contract and grid tariff periods |
| `reference_failure_mode` | Type 1 | Controlled vocabulary corrections |
| `reference_unit` | Type 1 | UCUM mapping |
| `reference_calendar` | Static | UTC/local shifts, holidays, price intervals |

Type 2 rows contain `surrogate_key`, natural key, `valid_from`, `valid_to`, `is_current`, `version`, and `change_reason`. Intervals are half-open `[valid_from, valid_to)` and may not overlap. Facts resolve the surrogate key valid at event time, not ingest time. Sensor replacement creates a new sensor ID; recalibration that changes scaling creates a new SCD version.

## 6. Deterministic generation model

### 6.1 Seeds and reproducibility

- Root seed: `240725`.
- Derive stable child seeds with `SHA-256(root_seed | scenario_id | plant_id | asset_id | signal_code)`, using the first 64 bits as an unsigned integer.
- Do not use process-dependent language hash functions.
- Record root seed, child-seed derivation version, generator version, configuration checksum, and simulated clock in the manifest.
- Given the same manifest, output must match by primary key and numeric value within documented floating-point tolerance.

Recommended scenario seeds:

| Scenario | Seed |
|---|---:|
| Healthy baseline | 240725 |
| 21-day lining warning | 240726 |
| Evening energy spike | 240727 |
| Quality drift | 240728 |
| Edge outage/recovery | 240729 |

### 6.2 Generator architecture

```text
Scenario manifest + reference data
                 |
       deterministic clock
                 |
    process-state simulation
      /       |         \
 physics   schedules   market/weather
      \       |         /
      sensor observation models
                 |
 edge simulator: sample -> buffer -> batch -> publish
                 |
 event stream + lake files + expected-label ledger
                 |
 validation/reconciliation reports
```

Components:

1. **Scenario compiler** validates YAML/JSON manifests and expands plant/asset templates.
2. **Process simulator** models mass/energy balance, operating modes, shift schedules, and material genealogy.
3. **Observation model** adds calibration bias, quantization, heteroscedastic noise, lag, and realistic missingness.
4. **Edge simulator** emits protocol-neutral events and optionally adapters for OPC UA, MQTT, or file drop.
5. **Anomaly controller** injects named, time-bounded faults at the process or sensor layer.
6. **Historical writer** produces partitioned Parquet/Delta-compatible data by date, plant, and dataset.
7. **Truth ledger** records hidden state, injected anomalies, labels, and expected KPI outcomes.
8. **Contract validator** checks schemas, units, relationships, duplicates, ordering, and scenario assertions.

The process state is generated first; sensors observe it. This prevents contradictory signals and data leakage from independently sampled columns.

## 7. Edge/captor simulator behavior

Each simulated edge gateway supports:

- real-time, accelerated, paused, and replay clock modes;
- configurable sampling, deadband, batching, compression, and publish interval;
- monotonic sequence numbers per partition;
- at-least-once delivery with deterministic duplicate replay;
- disk-backed store-and-forward with capacity and age limits;
- jitter of 0-500 ms normally and configurable latency spikes;
- connectivity states `ONLINE`, `DEGRADED`, `OFFLINE`, and `RECOVERING`;
- quality flags `GOOD`, `UNCERTAIN`, `BAD`, `STALE`, and `SUBSTITUTED`;
- sensor warm-up, drift, freeze, dropout, spike, clipping, calibration, and replacement;
- NTP offset simulation, while preserving original event time and gateway ingest time;
- graceful backfill with throttling so recovered traffic does not starve live events;
- heartbeat every 30 seconds containing queue depth, oldest buffered event, clock offset, and connection state.

Default outage scenario:

1. Gateway goes `DEGRADED` for 30 simulated seconds with 10% packet loss.
2. It goes `OFFLINE` for 3 simulated minutes and buffers events.
3. On recovery it publishes current data first, then backfills at 2x normal throughput.
4. Delayed records retain original `event_ts`; duplicates are intentionally replayed for idempotency testing.
5. UI shows data freshness and never draws a continuous line across a known gap without marking it.

## 8. Anomaly scenarios

### 8.1 Furnace lining degradation

The model simulates effective refractory thickness \(L\), thermal conductivity \(k\), inner refractory temperature \(T_i\), shell temperature \(T_s\), and cooling boundary. First-order conductive heat flux is:

`q = k * (T_i - T_s) / L`

As `L` declines in hearth sector 07, the synthetic signature develops:

- localized shell-temperature rise of 12-35 °C relative to adjacent sectors;
- increasing heat-flux level and 6-hour slope;
- larger cooling-water outlet-minus-inlet temperature;
- reduced cooling-efficiency residual after controlling for flow and inlet temperature;
- slower post-tap thermal decay and higher thermal persistence;
- spatial gradient centered on sector 07 rather than a plant-wide increase;
- intermittent 2-5 °C excursions before sustained warming;
- no impossible step change in true lining thickness.

The accelerated demo maps 45 historical days into roughly 45 seconds and then streams the final hours. The truth ledger sets the threshold-crossing such that the model emits a calibrated **21-day P50 warning**, with uncertainty shown. A sensor-bias control scenario raises one thermocouple but not cooling ΔT or neighboring sensors, allowing the model to distinguish instrumentation fault from lining degradation.

### 8.2 Energy price and dispatch

At a deterministic simulated time, a day-ahead scarcity interval raises spot price to 280 EUR/MWh. The optimizer:

- shifts two eligible reheat batches by 45 and 60 minutes;
- preheats before the peak within maximum hold-time limits;
- leaves an urgent automotive coil fixed;
- reduces modeled peak demand without changing total finished tonnage;
- reports savings separately from tariff and carbon effects.

Expected demo result: 7.25% energy-cost reduction (whole-dispatch basis), 3.29% CO₂ reduction, 7.89% peak-demand reduction (baseline 56.0 → optimized 51.58 MW), equal tonnage (960 t conserved), and no violated production or quality constraint. These are scenario results, not promises of realized production savings. Flexible-load-only figures (21.74% cost / 31.71% CO₂) are available in the API for transparency but must not be quoted as headlines.

### 8.3 Quality drift

Inject coiling-temperature sensor bias and burner imbalance gradually. The quality model detects multivariate drift before laboratory failures. Expected demo result: recommended setpoint correction returns predicted first-pass yield from approximately 88% to 95%, a relative improvement of about 8%, while the UI distinguishes predicted from measured yield.

### 8.4 Additional test anomalies

| Anomaly | Injection layer | Expected behavior |
|---|---|---|
| Frozen thermocouple | Sensor | Repeated identical value, stale flag, no false lining alert |
| Cooling-flow restriction | Process | Lower flow, higher ΔT and shell temperature after lag |
| Mill bearing defect | Process/sensor | Vibration sidebands, rising RMS and kurtosis |
| Bad unit mapping | Contract | Quarantine event; do not silently convert |
| Duplicate batch | Transport | Idempotent sink, duplicate metric increments |
| Late laboratory result | Business event | Event-time genealogy remains correct |
| Clock skew | Edge | Watermark handles lateness; gateway health alert |

## 9. Labels and physics-informed features

### 9.1 Ground-truth labels

| Label | Definition |
|---|---|
| `lining_state` | `healthy`, `watch`, `degraded`, `critical` from hidden thickness and thermal state |
| `rul_days` | Simulated time until minimum safe synthetic thickness |
| `failure_within_21d` | 1 when truth RUL is ≤21 days |
| `sensor_fault_type` | `none`, `bias`, `freeze`, `dropout`, `spike`, `drift` |
| `quality_outcome` | `pass`, `rework`, `downgrade`, `scrap` |
| `quality_drift_active` | Latent drift controller state |
| `energy_schedule_optimality_gap` | Cost gap to synthetic solver optimum |
| `anomaly_id` | Truth-ledger link to exact injection |

Training labels must be generated from hidden simulator state, not model predictions. Split by time and asset campaign to prevent leakage. Keep the final 20% of campaigns as an untouched test set; use a separate scenario seed for demo inference.

### 9.2 Physics-informed features

- heat flux from water mass flow, heat capacity, and cooling-water ΔT;
- apparent thermal resistance `(T_inner_est - T_shell) / heat_flux`;
- sector-to-ring and sector-to-neighbor temperature deltas;
- 1 h, 6 h, and 24 h robust slopes and exponentially weighted trends;
- thermal recovery half-life after tap;
- cooling efficiency residual conditioned on inlet temperature and flow;
- energy balance residual across furnace zones;
- specific electricity and gas per tonne;
- rolling power approximation from force × speed;
- mass-yield residual from slab to coil;
- carbon equivalent derived consistently from chemistry;
- time-above-target and area under temperature deviation;
- grade-normalized rolling force and coiling-temperature residual;
- monotonic campaign age and cumulative hot-metal throughput.

Physical constraints:

- predicted lining thickness cannot increase except after a recorded repair/reline;
- RUL cannot be negative and should decline consistently in expectation;
- outlet cooling-water temperature must not be below inlet temperature beyond measurement tolerance during heat extraction;
- energy and mass balances must reconcile within configured tolerances;
- counterfactual recommendations must stay inside grade and equipment operating envelopes.

## 10. Validation and acceptance rules

### 10.1 Contract checks

- 100% of records conform to their declared schema version.
- 100% carry synthetic classification and scenario lineage.
- Primary-key uniqueness is 100% after idempotent deduplication.
- Referential integrity for plant, asset, sensor, material, grade, and work order is ≥99.99%; all exceptions are intentional negative tests in quarantine.
- Canonical units match the signal registry; incompatible units are rejected.
- Nulls are allowed only where declared; `NaN` and infinity are rejected.
- Enumerations are case-sensitive and versioned.

### 10.2 Statistical and physical checks

- At least 99.7% of healthy observations lie within configured hard sensor ranges.
- Healthy missingness stays below 0.2% unless a scenario overrides it.
- Event-time lateness p95 is below 2 seconds online and is explicitly tagged during recovery.
- Furnace heat balance closes within ±5%; rolling mass balance within ±0.8%; interval energy reconciliation within ±1.5%.
- Adjacent furnace sectors are correlated in baseline data, while the degraded sector develops the specified spatial contrast.
- Quality outcomes correlate with chemistry and process deviations; no protected or personal attribute exists.
- Spot prices align to 15-minute market intervals and energy optimization cannot schedule an asset in two states simultaneously.
- SCD validity intervals do not overlap and exactly one current row exists per active natural key.

### 10.3 Scenario assertions

For seed `240726`, the lining model must show a 21-day P50 warning for `HEARTH-SECTOR-07`, with P10 < P50 < P90 and risk ≥0.80. For seed `240727`, the optimized schedule must cost less than baseline with equal planned tonnage and zero hard-constraint violations. For seed `240728`, the quality warning must precede the first off-spec result and the recommended correction must improve predicted first-pass yield.

Each generation run writes a manifest containing row counts, minimum/maximum event times, checksums, anomaly intervals, expected KPI ranges, and validator results. A run is demo-ready only when all required assertions pass.

## 11. Storage and Fabric mapping

The logical Fabric core is:

- **Eventstream/Real-Time Intelligence** for live telemetry and alerts;
- **OneLake lakehouse bronze** for immutable envelopes;
- **silver Delta tables** for typed, deduplicated, unit-normalized facts and SCD dimensions;
- **gold Delta tables and Direct Lake semantic model** for production, energy, quality, maintenance, and model KPIs;
- **notebooks/data science** for feature engineering and model evaluation;
- **Power BI** persona views with Direct Lake where available;
- **lineage and monitoring** for freshness, quarantine, and contract health.

Partition historical data by `event_date`, `plant_id`, and dataset; do not over-partition by sensor. Streaming and batch paths must converge on the same silver contract and deduplication keys.

## 12. Package-feed-safe implementation commands

No package installation is required to read or validate this specification. If a future Python simulator implementation requires dependencies on a Microsoft-managed device, use the approved protected feed explicitly and never point commands at public PyPI:

```powershell
$env:PIP_CONFIG_FILE = "$PWD\pip.conf"
$env:PIP_INDEX_URL = "https://packagefeedproxy.microsoft.io/pypi/simple"
$env:PIP_EXTRA_INDEX_URL = ""
& .\services\bff-api\.venv\Scripts\python.exe -m pip install `
    --disable-pip-version-check `
    -r .\services\bff-api\requirements.txt
```

The committed requirements are exact-version pins but do not carry hash entries,
so do not add `--require-hashes` until a hash-locked file is committed. Do not
add `--extra-index-url` for public registries. NuGet-based components must use
`https://packagefeedproxy.microsoft.io/nuget/v3/index.json`.

## 13. Device Operations simulator estate

Wave 3 introduces a real-time device-telemetry simulator (`services/device-simulator`) that is separate from the batch scenario generator above. It produces a live, clock-driven ring buffer of sensor readings from a seventeen-device, four-site industrial estate and is consumed by the BFF's Device Operations routes. Wave 6 extended the estate from the original Luxembourg-only six devices to all four demo plants so that the site selector exercises a genuinely different fleet at every site.

### 13.1 Device catalog

**Total: 17 devices across 4 sites, 91 sensors.**

| Device ID | Site | Area | Asset type | Sensors |
|---|---|---|---|---|
| `LUX-BF-01` | `NS-DEMO-LUX-01` | Ironmaking | Blast furnace | 11 |
| `LUX-BOF-01` | `NS-DEMO-LUX-01` | Steelmaking | Basic oxygen furnace | 5 |
| `LUX-CC-01` | `NS-DEMO-LUX-01` | Casting | Slab caster | 5 |
| `LUX-RHF-01` | `NS-DEMO-LUX-01` | Rolling | Reheat furnace | 3 |
| `LUX-HSM-01` | `NS-DEMO-LUX-01` | Rolling | Hot strip mill | 4 |
| `LUX-UTIL-01` | `NS-DEMO-LUX-01` | Utilities | Energy system | 6 |
| `DE-EAF-01` | `NS-DEMO-DE-01` | Steelmaking | Electric arc furnace | 6 |
| `DE-LF-01` | `NS-DEMO-DE-01` | Steelmaking | Ladle furnace | 5 |
| `DE-BCM-01` | `NS-DEMO-DE-01` | Casting | Billet caster | 5 |
| `DE-UTIL-01` | `NS-DEMO-DE-01` | Utilities | Energy system | 6 |
| `BE-EAF-01` | `NS-DEMO-BE-01` | Steelmaking | Electric arc furnace | 5 |
| `BE-CRM-01` | `NS-DEMO-BE-01` | Rolling | Cold rolling mill | 5 |
| `BE-GAL-01` | `NS-DEMO-BE-01` | Coating | Hot-dip galvanizing line | 5 |
| `BE-UTIL-01` | `NS-DEMO-BE-01` | Utilities | Energy system | 6 |
| `ES-EAF-01` | `NS-DEMO-ES-01` | Steelmaking | Electric arc furnace | 4 |
| `ES-WRM-01` | `NS-DEMO-ES-01` | Rolling | Wire rod mill | 5 |
| `ES-UTIL-01` | `NS-DEMO-ES-01` | Utilities | Energy system | 5 |

Site totals: Luxembourg 6 devices / 34 sensors, Germany 4 / 22, Belgium 4 / 21, Spain 3 / 14.

The estate is deliberately heterogeneous by route: Luxembourg runs the integrated blast-furnace/BOF route, Germany and Spain run electric-arc-furnace routes, and Belgium is a downstream finishing site with no melting at all. This means the Device Operations screen shows a materially different asset mix per site rather than a renamed copy, and it lets the demo contrast the CO2 profile of the BF/BOF route against the EAF route.

Sensor signals on `LUX-BF-01` mirror the thermal-process signals defined in `simulator/config.py` (hearth-shell thermocouples by sector, cooling-water inlet/outlet temperatures and flow, local heat flux, hot-blast temperature and pressure, top pressure, PCI rate, hot-metal temperature, production rate). The remaining devices add steelmaking, casting, rolling, coating, and utility-energy signals specific to those asset classes.

### 13.1.1 Site filtering contract

`GET /v1/devices` and `GET /v1/devices/sensors` both accept an optional `site` query parameter (default `all`). Two independent filters apply, in this order:

1. **Plant scope** — rows whose `site` is outside the caller's `plant_scope` are removed. This is an authorisation boundary and is never bypassable from the client.
2. **Site selection** — when `site != "all"`, the remaining rows are narrowed to that single site. This is a presentation filter reflecting the portal's site selector.

Sensors carry no `site` field of their own; they are filtered by resolving their parent `deviceId` through the device catalog. Regression coverage lives in `services/bff-api/tests/test_device_routes.py`.

### 13.2 Determinism guarantees

| Parameter | Value |
|---|---|
| Simulation start | `2024-07-25T06:00:00Z` |
| Default tick interval | 5 seconds |
| Ring buffer capacity | 1 440 samples per sensor |
| Maximum catch-up ticks per read | 500 |
| Seed derivation | child seed = first 64 bits of `SHA-256(parent_seed ‖ scenario ‖ sensor_id)` |

Reads auto-advance the deterministic clock by the elapsed wall-clock delta (up to 500 ticks per call) without requiring a background thread, which makes the adapter safe to run in-process inside the BFF.

### 13.3 Scenarios

| Scenario ID | Nominal seed | Characteristic |
|---|---|---|
| `healthy-baseline` | 240725 | All signals nominal; no incidents |
| `lining-degradation-21d` | 240726 | Hearth lining wear develops on `LUX-BF-01` over ~21 simulated days |
| `energy-price-spike` | 240727 | Spot price and site-active-power spike on `LUX-UTIL-01` |
| `quality-drift` | 240728 | Dimensional signals drift on `LUX-CC-01` and `LUX-HSM-01` |
| `edge-outage-recovery` | 240729 | Sensors go stale then recover, exercising buffering and reconnect |
| `demo-full` | 240725 | Full-estate composite; the BFF demo-mode adapter starts this with seed `240726` (lining-degradation seed) to pre-warm hearth thermal signals |

> **Note:** The device-simulator `README.md` states "23 signals" and "5 demo scenarios." These figures are incorrect; the source code (`catalog.py`) is the authoritative source and defines **17 devices / 91 sensors** across four sites, with `SCENARIO_SEEDS` containing **6 entries**. The README predates both the extension of the catalog and the wave-6 multi-site expansion.

### 13.4 Incident catalog

Seven parameterised incidents can be injected at runtime. `Platform.Capacity.Manage` is required.

| Incident ID | Severity | Default duration | Default target | Effect |
|---|---|---|---|---|
| `degrading-furnace` | high | 30 min | `LUX-BF-01` | Hearth-shell-temperature rise and heat-flux increase; mirrors lining-wear signature |
| `cooling-water-loss` | critical | 15 min | `LUX-BF-01` | Cooling-circuit signals drop; shell temperature rises sharply |
| `sensor-drift` | medium | 60 min | (operator-selected) | Additive bias applied to the target sensor |
| `sensor-dropout` | medium | 10 min | (operator-selected) | Sensor quality goes `bad`; status becomes `stale` |
| `energy-price-spike` | medium | 45 min | `LUX-UTIL-01` | `spot_price` and `site_active_power` spike |
| `quality-drift` | high | 45 min | `LUX-CC-01`, `LUX-HSM-01` | Dimensional signals drift progressively |
| `edge-outage-recovery` | low | 20 min | (operator-selected) | All sensors on the target go stale, then recover sequentially |

Active incidents are visible in the Device Simulator panel's active-incident list with elapsed time and a progress bar. Any incident can be cleared early via `DELETE /v1/devices/incidents/{activeIncidentId}`.

### 13.5 Sensor status — approach-band rule

The status module (`status.py`) applies an OT-standard approach-band algorithm rather than a naive "outside range" test:

| Condition (evaluated in order) | Status |
|---|---|
| Sensor quality is `bad` | `stale` |
| Sample age exceeds 3 × sample period | `stale` |
| Value is within the inner 90 % of the `[low, high]` span (i.e., > 5 % away from either limit) | `normal` |
| Value is within 5 % of span from either limit (on the inside) | `warning` |
| Value exceeds a limit by more than 5 % of span (on the outside) | `alarm` |

**Rationale:** the waveform generator clamps output values to the `[low, high]` range before writing to the ring buffer. A naive "outside range" check would therefore never fire `alarm`, because a saturated sensor appears healthy. The approach band solves this by firing `warning` as the value approaches the clamp point, and `alarm` when the signal would have exceeded the limit. This is consistent with IEC 62682 alarm-management practice.

Device health scores and device-level status are derived from sensor states:

- `alarm` or `stale` → penalty 1.0; `warning` → penalty 0.4; `normal` → penalty 0.0.
- Device score = 1 − weighted bad-sensor fraction.
- Device status: any `stale` sensor → `offline`; any `alarm` → `fault`; any `warning` → `degraded`; all `normal` → `healthy`.

### 13.6 Demo-mode auto-seeding

When the BFF starts in demo mode the `DeviceAdapter`:

1. Starts with scenario `demo-full`, seed `240726`, speed factor 1.0.
2. Runs 720 warm-up ticks (≈ 8 hours of simulated history).
3. Seeds a `degrading-furnace` incident on `LUX-BF-01` for 90 minutes, then advances 918 more ticks (~85 % incident progress).
4. On every subsequent read, re-arms the incident when it expires (`_ensure_demo_incident()`), so the Device Fleet page is never an all-green, empty-chart fleet.
5. Any explicit `Platform.Capacity.Manage` simulator command sets `_auto_demo = False` and disables re-arming permanently for that process lifetime.

This is a deliberate design choice: the demo must immediately show meaningful sensor deviation without the presenter having to manually inject an incident.

### 13.7 Relationship to the batch scenario generator

The device simulator (`services/device-simulator`) and the batch scenario generator (`simulator/`) address different layers:

| | Batch generator | Device simulator |
|---|---|---|
| Output | JSON fixture files for the BFF's fixture adapters | In-process ring buffer for the `/v1/devices/*` routes |
| Clock model | Static manifest with configurable simulated clock | Advancing wall-clock delta on each read |
| Primary use | RUL / energy / quality / knowledge demo moments | Device Operations screen (fleet, sensor explorer, simulator controls) |
| Storage | `services/bff-api/fixtures/demo-full/` | In-memory ring buffer (per-process) |

Both paths use deterministic seeds, so results are reproducible independently of one another.
