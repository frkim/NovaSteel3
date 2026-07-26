-- Run with lh-ns-core attached as the default Lakehouse.
-- Streaming and batch paths converge on these typed/idempotent contracts.

CREATE TABLE IF NOT EXISTS dim_plant (
  plant_key BIGINT NOT NULL,
  plant_id STRING NOT NULL,
  plant_name STRING NOT NULL,
  country_code STRING NOT NULL,
  time_zone STRING NOT NULL,
  route STRING,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP,
  is_current BOOLEAN NOT NULL,
  version INT NOT NULL,
  change_reason STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS dim_asset (
  asset_key BIGINT NOT NULL,
  asset_id STRING NOT NULL,
  plant_id STRING NOT NULL,
  parent_asset_id STRING,
  area STRING,
  line_id STRING,
  asset_type STRING NOT NULL,
  criticality STRING,
  commissioned_state STRING,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP,
  is_current BOOLEAN NOT NULL,
  version INT NOT NULL,
  change_reason STRING
) USING DELTA
PARTITIONED BY (plant_id);

CREATE TABLE IF NOT EXISTS dim_sensor (
  sensor_key BIGINT NOT NULL,
  sensor_id STRING NOT NULL,
  plant_id STRING NOT NULL,
  asset_id STRING NOT NULL,
  signal_code STRING NOT NULL,
  canonical_unit STRING NOT NULL,
  hard_min DOUBLE,
  hard_max DOUBLE,
  sample_period_ms BIGINT,
  calibration_version STRING,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP,
  is_current BOOLEAN NOT NULL,
  version INT NOT NULL,
  change_reason STRING
) USING DELTA
PARTITIONED BY (plant_id);

CREATE TABLE IF NOT EXISTS dim_grade (
  grade_key BIGINT NOT NULL,
  grade_code STRING NOT NULL,
  grade_family STRING,
  high_grade_flag BOOLEAN NOT NULL,
  target_json STRING NOT NULL,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP,
  is_current BOOLEAN NOT NULL,
  version INT NOT NULL,
  change_reason STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS dim_calendar (
  date_key DATE NOT NULL,
  plant_id STRING NOT NULL,
  local_date DATE NOT NULL,
  year INT NOT NULL,
  month INT NOT NULL,
  iso_week INT NOT NULL,
  day_of_week INT NOT NULL,
  is_holiday BOOLEAN NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS fact_telemetry (
  event_id STRING NOT NULL,
  event_ts TIMESTAMP NOT NULL,
  ingest_ts TIMESTAMP NOT NULL,
  event_date DATE NOT NULL,
  plant_key BIGINT NOT NULL,
  asset_key BIGINT NOT NULL,
  sensor_key BIGINT NOT NULL,
  plant_id STRING NOT NULL,
  asset_id STRING NOT NULL,
  sensor_id STRING NOT NULL,
  signal_code STRING NOT NULL,
  value DOUBLE NOT NULL,
  unit STRING NOT NULL,
  source_quality STRING NOT NULL,
  uncertainty DOUBLE,
  late_flag BOOLEAN NOT NULL,
  scenario_id STRING,
  seed BIGINT,
  correlation_id STRING NOT NULL,
  data_classification STRING NOT NULL
) USING DELTA
PARTITIONED BY (event_date, plant_id);

CREATE TABLE IF NOT EXISTS fact_energy_interval (
  meter_id STRING NOT NULL,
  plant_id STRING NOT NULL,
  interval_start TIMESTAMP NOT NULL,
  interval_end TIMESTAMP NOT NULL,
  event_date DATE NOT NULL,
  energy_type STRING NOT NULL,
  energy_mwh DOUBLE,
  energy_gj DOUBLE NOT NULL,
  spot_price_eur_per_mwh DOUBLE,
  grid_carbon_kg_per_mwh DOUBLE,
  cost_eur DOUBLE,
  co2e_t DOUBLE,
  source_version STRING NOT NULL,
  data_classification STRING NOT NULL
) USING DELTA
PARTITIONED BY (event_date, plant_id);

CREATE TABLE IF NOT EXISTS fact_quality_measurement (
  sample_id STRING NOT NULL,
  characteristic_code STRING NOT NULL,
  event_ts TIMESTAMP NOT NULL,
  event_date DATE NOT NULL,
  plant_id STRING NOT NULL,
  asset_id STRING,
  material_id STRING NOT NULL,
  heat_id STRING,
  grade_key BIGINT NOT NULL,
  grade_code STRING NOT NULL,
  value DOUBLE NOT NULL,
  unit STRING NOT NULL,
  lower_spec_limit DOUBLE,
  upper_spec_limit DOUBLE,
  measurement_method STRING NOT NULL,
  result_status STRING NOT NULL,
  first_pass_flag BOOLEAN NOT NULL,
  tons DOUBLE
) USING DELTA
PARTITIONED BY (event_date, plant_id);

CREATE TABLE IF NOT EXISTS fact_maintenance_event (
  work_order_id STRING NOT NULL,
  event_ts TIMESTAMP NOT NULL,
  event_date DATE NOT NULL,
  plant_id STRING NOT NULL,
  asset_id STRING NOT NULL,
  component_id STRING,
  event_type STRING NOT NULL,
  failure_mode STRING,
  action_code STRING NOT NULL,
  planned_flag BOOLEAN NOT NULL,
  downtime_hours DOUBLE,
  linked_inference_id STRING
) USING DELTA
PARTITIONED BY (event_date, plant_id);

CREATE TABLE IF NOT EXISTS fact_alarm_event (
  alarm_id STRING NOT NULL,
  transition_id STRING NOT NULL,
  event_ts TIMESTAMP NOT NULL,
  event_date DATE NOT NULL,
  plant_id STRING NOT NULL,
  asset_id STRING NOT NULL,
  severity STRING NOT NULL,
  state STRING NOT NULL,
  alarm_type STRING NOT NULL,
  confidence DOUBLE,
  correlation_id STRING NOT NULL
) USING DELTA
PARTITIONED BY (event_date, plant_id);

CREATE TABLE IF NOT EXISTS fact_model_inference (
  inference_id STRING NOT NULL,
  event_date DATE NOT NULL,
  feature_snapshot_ts TIMESTAMP NOT NULL,
  scored_at TIMESTAMP NOT NULL,
  plant_id STRING NOT NULL,
  entity_id STRING NOT NULL,
  component_id STRING,
  model_id STRING NOT NULL,
  model_version STRING NOT NULL,
  prediction_type STRING NOT NULL,
  prediction_value DOUBLE NOT NULL,
  unit STRING NOT NULL,
  p10 DOUBLE,
  p50 DOUBLE,
  p90 DOUBLE,
  risk_score DOUBLE,
  confidence DOUBLE,
  top_factors_json STRING NOT NULL,
  feature_snapshot_ref STRING NOT NULL,
  scenario_id STRING,
  seed BIGINT
) USING DELTA
PARTITIONED BY (event_date, plant_id);

CREATE TABLE IF NOT EXISTS fact_ai_decision (
  audit_event_id STRING NOT NULL,
  audit_id STRING NOT NULL,
  event_ts TIMESTAMP NOT NULL,
  event_date DATE NOT NULL,
  domain STRING NOT NULL,
  entity_id STRING NOT NULL,
  event_type STRING NOT NULL,
  recommendation_status STRING,
  input_snapshot_ref STRING NOT NULL,
  model_version STRING,
  output_json STRING,
  confidence DOUBLE,
  actor_id STRING,
  reason_code STRING,
  correlation_id STRING NOT NULL,
  complete_audit_flag BOOLEAN NOT NULL
) USING DELTA
PARTITIONED BY (event_date, domain);
