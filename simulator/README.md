# NovaSteel synthetic captor/sensor simulator

Deterministic, fully synthetic generator for the NovaSteel demo estate:
blast-furnace/rolling-mill telemetry, electricity market/dispatch,
quality/genealogy, maintenance, alarms, model inference, operator
knowledge, and a hidden-state truth ledger. It implements
[`docs/data/synthetic-data-and-simulators.md`](../docs/data/synthetic-data-and-simulators.md)
and is compatible with the canonical event contracts under
[`contracts/events`](../contracts/events) (see [Canonical wire contract](#canonical-wire-contract) below).

Every record is tagged `data_classification: SYNTHETIC` and
`privacy_label: DEMO-NONPERSONAL`. This is a demo data generator, not a
safety system, and must never be used to set real equipment controls.

Implemented entirely with the **Python standard library** (Python 3.11+).
No third-party runtime dependencies. If a future change genuinely needs
one, install it only through the approved feed already configured in the
repository root `pip.conf` (`https://packagefeedproxy.microsoft.io/pypi/simple`)
— never a public registry.

## Quick start: one-command fast demo

```powershell
python -m simulator.cli demo
```

This generates the full `demo-full` narrative (hearth-sector-07 lining
degradation, an evening energy-price spike with schedule optimization,
gradual quality drift, a maintenance work order, an operator-knowledge
capture session, and a gateway outage/recovery cycle) at a compressed
"fast" window into `output/demo/`, in well under a few seconds. Validate
it immediately with:

```powershell
python -m simulator.cli validate --run-dir output\demo
```

## Scenarios

| Scenario id | Seed | Narrative |
|---|---:|---|
| `healthy-baseline` | 240725 | No active anomalies; negative control. |
| `lining-degradation-21d` | 240726 | Hearth sector 07 refractory wear -> calibrated 21-day P50 RUL warning. |
| `energy-price-spike` | 240727 | Evening 17:00-20:00 scarcity interval at 280 EUR/MWh; batches rescheduled. |
| `quality-drift` | 240728 | Gradual coiling-temperature/carbon-equivalent drift; warning precedes first off-spec sample. |
| `demo-full` | 240725 | All of the above combined, plus a gateway outage/recovery window. |

List them (with descriptions) at any time:

```powershell
python -m simulator.cli list-scenarios
```

## Analytical (static) gold data stream

Alongside the streaming event generator above, the simulator emits a
**multi-month analytical** dataset of **gold-grain star-schema facts**
(`contracts/data/gold.v2.json`) for the Microsoft Fabric Lakehouse. Where the
event path shows a single shift, this shows the **programme** trend.

| Analytical scenario | Seed | Span | What it shows |
|---|---:|---|---|
| `analytical-programme-24m` | 240801 | ~24 months, daily/shift grain | The four-plant efficiency programme with an explicit rollout boundary. |

It emits eight gold facts — `fact_production_shift`, `fact_energy_daily`,
`fact_emissions_daily`, `fact_quality_yield`, `fact_furnace_rul`,
`fact_dispatch_recommendation`, `fact_knowledge_procedure`,
`fact_ai_decision_audit` — with columns matching the deployed
`lh_novasteelv3_core` Delta DDL so the loader can MERGE straight in.

These facts use **natural business keys** (e.g. `date_key, plant_id`,
`shift_id`, `date_key, plant_id, grade_code`, `inference_id`), not surrogate
`*_key` dimension keys. `contracts/data/gold.v2.json` is **contractVersion 2**
and its `keyDesign` block explains why: the demo runs no SCD2 dimension load, so
a surrogate key would reference a dimension row nothing produces.
`validate-analytics` asserts the produced tables against that contract (columns,
order, keys present, primary/idempotency uniqueness, and generator↔contract key
agreement), so the contract and the tables cannot silently drift.

```powershell
python -m simulator.cli list-analytical-scenarios
python -m simulator.cli generate-analytics --scenario analytical-programme-24m [--fast] [--parquet]
python -m simulator.cli validate-analytics --run-dir output\analytical-programme-24m [--skip-checksum]
```

The headline improvements are **computed from the emitted rows**, not asserted,
against an explicit `rollout_date` before/after boundary:

| KPI | Target | Source of truth |
|---|---:|---|
| Energy per ton | −14 % | `Σ energy_gj / Σ crude_steel_tons`, after ÷ before |
| Specific CO₂ | −22 % | `Σ total_co2e_t / Σ crude_steel_tons`, after ÷ before |
| High-grade first-pass yield | +8 pts | `Σ first_pass_good_tons / Σ attempted_tons` (high-grade) |
| Furnace-lining advance warning | 21 days | first `fact_furnace_rul` alert: `predicted_failure_date − scored_date` |

The lining alert fires exactly when `rul_days_p50 <= 21` **and**
`risk_score >= 0.80`, and those thresholds coincide at 21 days, so the warning
genuinely falls out of the data (no "High = 7–20 days" style contradiction).
CSV is the canonical, byte-reproducible, checksummed format; `--parquet` adds
Fabric-idiomatic Parquet when `pyarrow` is available. The loader notebook
(`fabric/notebooks/ns-load-analytical-gold.Notebook`) and the upload/capacity
script (`tools/fabric/Load-AnalyticalGold.ps1`) are documented in
[`tools/fabric/README.md`](../tools/fabric/README.md).

### Operational envelope tables (what the application reads)

The **gold facts above** feed the semantic model / Power BI / KPI trends. The
*application* (BFF) reads a **second** layer from the same lakehouse: the nine
raw simulator-envelope datasets, landed as Delta tables the BFF consumes when
`BFF_DATA_SOURCE=fabric`. Reshape the committed pack into loader-ready tables
with:

```powershell
python -m simulator.cli generate-operational
# -> output\operational-envelopes\{telemetry,...,truth_ledger,manifest}.ndjson
```

Each row is `{event_id, envelope}` where `envelope` is the full envelope as a
JSON string — a lossless round trip proven by
`tests/integration/test_fabric_operational_round_trip.py`. Loading is documented
in [`tools/fabric/README.md`](../tools/fabric/README.md)
(`Load-AnalyticalGold.ps1 -Layer operational`).

## CLI reference

```powershell
python -m simulator.cli generate --scenario lining-degradation-21d --out output\lining [--fast] [--format ndjson|csv|json]
python -m simulator.cli demo [--out output\demo] [--format ndjson|csv|json]
python -m simulator.cli validate --run-dir output\lining [--only contract physics scenario checksum contract-schema]
python -m simulator.cli checksum --run-dir output\lining [--verify]
python -m simulator.cli reset --out output\lining
python -m simulator.cli publish --run-dir output\lining --sink-url https://<eventstream-custom-endpoint-or-local-bff>/ingest `
    [--datasets telemetry energy_interval ...] [--batch-size 10] [--rate 20] [--token-env NOVASTEEL_SINK_TOKEN] `
    [--replay-duplicate-fraction 0.05]
```

`--fast` uses each manifest's `fast_window_hours`/`fast_sample_interval_seconds`
instead of the full window, trading dataset richness for generation speed
(the `demo` subcommand always uses `--fast`). Every run writes:

- one file per dataset (`telemetry`, `energy_interval`, `quality_measurement`,
  `heat_batch`, `maintenance_event`, `alarm_event`, `operator_knowledge`,
  `model_inference`) in the requested format, plus `truth_ledger.ndjson`
  (always NDJSON);
- `manifest.json`: the run manifest (row counts, min/max event time, config
  checksum, clock mode, summary metrics used by the scenario-assertion
  validator);
- `checksums.json`: a SHA-256 + byte-size per output file, for
  reproducibility/tamper checks (`checksum --verify`).

## Deterministic generation

Child seeds are derived as
`SHA-256(root_seed | scenario_id | plant_id | asset_id | signal_code)`
(first 64 bits, big-endian) rather than Python's process-salted `hash()`,
so two runs of the same manifest on any machine produce **byte-identical**
output, including `event_id` (a deterministic UUIDv7). See
`simulator/determinism.py` and `tests/simulator/test_determinism.py`.

## Architecture

```
scenario manifest (simulator/manifests/*.json)
        |
   deterministic clock (simulator/clock.py)
        |
  process-state models (simulator/process/*.py: furnace, rolling, energy, quality)
        |
  anomaly controller (simulator/anomalies.py) + observation model (simulator/observation.py)
        |
  edge gateway: sequencing, connectivity state, jitter (simulator/edge.py)
        |
  canonical event envelopes (simulator/envelope.py) -> local NDJSON/CSV/JSON (simulator/writer.py)
        |                                            -> paced HTTP sink publish (simulator/sink_http.py)
  truth ledger (simulator/truth_ledger.py)
        |
  contract / physics / determinism / scenario-assertion validators (simulator/validators/*.py)
```

The process state is generated first; sensors only ever *observe* it, so
telemetry values are never sampled independently of one another (no
data leakage between correlated signals).

## Canonical event envelope

```json
{
  "schema_name": "novasteel.telemetry.v1",
  "schema_version": 1,
  "event_id": "018f6dd0-b36a-7bd1-8ef8-087264aa8f21",
  "event_ts": "2026-06-10T00:05:00.000Z",
  "ingest_ts": "2026-06-10T00:05:00.221Z",
  "sequence": 42,
  "source_id": "edge-lux-01",
  "plant_id": "NS-DEMO-LUX-01",
  "asset_id": "LUX-BF-01",
  "scenario_id": "lining-degradation-21d",
  "correlation_id": "run-lining-degradation-21d-240726",
  "data_classification": "SYNTHETIC",
  "privacy_label": "DEMO-NONPERSONAL",
  "generator_version": "novasteel-sim/1.0.0",
  "seed": 240726,
  "payload": {
    "type": "telemetry.furnace.thermal",
    "sensor_id": "...", "signal_code": "...", "value": 171.4, "unit": "Cel",
    "quality": "GOOD", "uncertainty": 0.6, "sample_period_ms": 5000, "...": "..."
  }
}
```

## Canonical wire contract

Local files, the truth ledger, and everything published to the HTTP sink
all use the same **rich, docs-native payload** shown above (`sensor_id`,
`signal_code`, `quality` with the full `GOOD|UNCERTAIN|BAD|STALE|SUBSTITUTED`
enum, `uncertainty`, `sample_period_ms`, ...) plus one addition: a closed
`type` discriminator (`telemetry.furnace.thermal` / `telemetry.rolling.mill`
/ `energy.interval` / `quality.measurement`, `simulator/config.py::TELEMETRY_EVENT_TYPES`),
which the generator stamps directly onto the native payload. Nothing from
docs section 4.2 is dropped or renamed.

**Status (confirmed authoritative 2026-07-25):** this was coordinated
directly with the `app-scaffold`/application-foundation workstream, which
owns `contracts/events/*.schema.json`. Their first draft of
`telemetry.v1.schema.json` used `additionalProperties: false` with a
narrower `signal`/`quality_flag` shape, which conflicted with the
authoritative data spec and the architecture's additive-v1 rule; they
corrected `telemetry.v1`, `model-inference.v1`, and `alarm.v1` the same
day to require exactly the rich fields above (telemetry), the full docs
section 4.4 `prediction`/`top_factors` shape (model-inference), and the
full 5-state `OPEN|ACKNOWLEDGED|WORK_ORDER_LINKED|MITIGATED|CLOSED`
lifecycle plus `alert_id`/`reason`/`transitioned_at`/`work_order_id`
(alarm) -- all with additive fields explicitly allowed. Reference fixtures
live at `contracts/events/fixtures/*.valid.v1.json`;
`tests/simulator/test_authoritative_fixtures.py` validates the simulator's
generated payloads directly against those fixtures' required keys and the
live schema files (no projection needed for these three event types
anymore). `simulator/contract_projection.py` is now a no-op passthrough
for telemetry/energy/quality/model_inference/alarm (it only backfills
`type` for a hand-built fixture that omits it).
`simulator/validators/contract_schema.py::payload_schema_is_restrictive()`
is kept as a safety net: if a future schema revision ever regresses to
`additionalProperties: false`, the CLI's `contract-schema` check and the
corresponding tests degrade to a skip with an explicit message instead of
failing, so this suite is never blocked on another workstream's in-flight
file. `energy_interval`/`quality_measurement` now also validate directly
against dedicated schemas added the same day,
`contracts/events/energy-interval.v1.schema.json` (`meter_id`,
`interval_start`, `price`, `demand`, plus additive `interval_end`,
`price_unit`, `demand_unit`, `consumption_mwh`,
`grid_carbon_intensity_kgco2e_per_mwh`, `scenario`) and
`quality-measurement.v1.schema.json` (`material_id`, `heat_id`,
`grade_code`, `sample_id`, `characteristic_code`, `value`, `unit`, spec
limits, `measurement_method`, `result_status`) -- both under their own
schema_name (`novasteel.energy-interval.v1` /
`novasteel.quality-measurement.v1`) per docs section 4.3's genealogy
model. Every envelope's top-level fields already validate unmodified
against `contracts/events/event-envelope.v1.schema.json`.

## Anomaly injection

Declared per-scenario in each manifest's `anomalies` list (`anomaly_id`,
`type`, `layer`, `target`, `start_hours`/`end_hours`, `params`).
Implemented types: `lining_degradation` (process layer, localized hearth
sector shell-temperature/cooling-ΔT signature), `price_spike` (business
layer, day-ahead scarcity interval), `quality_drift` (process layer,
latent coiling-temperature/carbon-equivalent/force-imbalance drift), and
`gateway_outage` (edge layer, `DEGRADED`->`OFFLINE`->`RECOVERING`
connectivity cycle). The sensor observation model
(`simulator/observation.py`) additionally supports `bias`, `freeze`,
`spike`, `drift`, and `dropout` sensor-layer faults for ad hoc testing.

## 21-day RUL truth ledger

`truth_ledger.ndjson` records the *hidden* simulator state independent of
any model prediction: `lining_state`, `rul_days`, `failure_within_21d`,
`sensor_fault_type`, `quality_outcome`, `quality_drift_active`,
`energy_schedule_optimality_gap`, and `anomaly_id` (docs section 9.1).
`lining-degradation-21d` is calibrated so `rul_days` is exactly 21.0 at
the evaluation timestamp, matching the worked example in
`docs/data/synthetic-data-and-simulators.md` section 4.4 (P10=16.8,
P50=21.0, P90=27.5, risk=0.87).

## Validators

- **Contract** (`simulator/validators/contract.py`): envelope shape,
  classification/privacy labels, `event_id` uniqueness/UUIDv7 format,
  per-source sequence monotonicity, unit-registry membership, quality-flag
  enum, no NaN/Infinity.
- **Physics** (`simulator/validators/physics.py`): cooling outlet >= inlet,
  non-negative heat flux, monotonic non-increasing hearth thickness
  (absent a declared repair), rolling mass-balance within ±0.8%.
- **Determinism** (`simulator/validators/determinism.py`): compares two
  runs' checksums or datasets field-by-field.
- **Scenario assertions** (`simulator/validators/scenario_assertions.py`):
  the three acceptance thresholds from docs section 10.3 (21-day lining
  warning, energy optimizer savings, quality-drift warning ordering).
- **Contract schema** (`simulator/validators/contract_schema.py`):
  validates `telemetry`, `energy_interval`, `quality_measurement`,
  `model_inference`, and `alarm_event` directly against the matching
  `contracts/events/*.schema.json` files.

Run them all via `python -m simulator.cli validate --run-dir <dir>`.

## Testing

```powershell
python -m unittest discover -s tests\simulator -p "test_*.py"
# or, equivalently:
python -m pytest tests\simulator
```

55 tests cover: same-seed determinism (checksums, field-by-field records,
and stable `event_id`s), contract/physics validators (including injected
violations), the three documented scenario-acceptance thresholds, direct
validation against the authoritative `contracts/events` schema files and
their `fixtures/*.valid.v1.json` reference fixtures, all documented
datasets (electricity, production/genealogy, quality, maintenance,
operator knowledge, truth ledger), NDJSON/CSV/JSON output, the
one-command fast `demo` CLI path, paced HTTP-sink publishing
(batching/pacing/retry/duplicate replay), and reset/checksum controls.
Tests never write outside `tests/simulator/.tmp/` (cleaned up
automatically) or the repository.

## Directory layout

```
simulator/
  manifests/*.json        scenario manifests (seeds, windows, anomalies, expected assertions)
  process/                furnace, rolling, energy, quality, maintenance, knowledge models
  validators/              contract, physics, determinism, scenario-assertion, contract-schema
  cli.py                   command-line entry point (python -m simulator.cli / simulator.cli:main)
  generator.py             run orchestrator
  envelope.py              canonical envelope + deterministic UUIDv7
  contract_projection.py   projection to the contracts/events canonical wire shape
  sink_http.py             paced HTTP publisher (Eventstream Custom Endpoint / local BFF compatible)
  writer.py, checksum.py, reset.py, truth_ledger.py, edge.py, anomalies.py, observation.py, clock.py,
  determinism.py, scenario.py, config.py
tests/simulator/           unittest-based test suite (also pytest-collectible)
```
