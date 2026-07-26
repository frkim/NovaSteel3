-- Run with lh-ns-landing attached as the default Lakehouse.
-- Append-only landing and queryable quarantine; no DROP/TRUNCATE statements.

CREATE TABLE IF NOT EXISTS bronze_event_envelope (
  event_id STRING NOT NULL,
  event_ts TIMESTAMP NOT NULL,
  ingest_ts TIMESTAMP NOT NULL,
  sequence BIGINT NOT NULL,
  source_id STRING NOT NULL,
  plant_id STRING NOT NULL,
  asset_id STRING,
  schema_name STRING NOT NULL,
  schema_version INT NOT NULL,
  correlation_id STRING NOT NULL,
  data_classification STRING NOT NULL,
  privacy_label STRING,
  scenario_id STRING,
  seed BIGINT,
  generator_version STRING,
  clock_mode STRING,
  payload_json STRING NOT NULL,
  payload_hash STRING NOT NULL,
  run_id STRING,
  event_date DATE NOT NULL,
  landed_at TIMESTAMP NOT NULL
) USING DELTA
PARTITIONED BY (event_date, plant_id);

CREATE TABLE IF NOT EXISTS bronze_batch_mes (
  batch_id STRING NOT NULL,
  source_system STRING NOT NULL,
  source_record_id STRING NOT NULL,
  source_updated_at TIMESTAMP NOT NULL,
  event_date DATE NOT NULL,
  plant_id STRING NOT NULL,
  dataset STRING NOT NULL,
  payload_json STRING NOT NULL,
  payload_hash STRING NOT NULL,
  data_classification STRING NOT NULL,
  landed_at TIMESTAMP NOT NULL
) USING DELTA
PARTITIONED BY (event_date, plant_id);

CREATE TABLE IF NOT EXISTS bronze_batch_cmms (
  batch_id STRING NOT NULL,
  source_system STRING NOT NULL,
  source_record_id STRING NOT NULL,
  source_updated_at TIMESTAMP NOT NULL,
  event_date DATE NOT NULL,
  plant_id STRING NOT NULL,
  payload_json STRING NOT NULL,
  payload_hash STRING NOT NULL,
  data_classification STRING NOT NULL,
  landed_at TIMESTAMP NOT NULL
) USING DELTA
PARTITIONED BY (event_date, plant_id);

CREATE TABLE IF NOT EXISTS bronze_batch_market (
  batch_id STRING NOT NULL,
  source_system STRING NOT NULL,
  source_record_id STRING NOT NULL,
  source_updated_at TIMESTAMP NOT NULL,
  event_date DATE NOT NULL,
  market_zone STRING NOT NULL,
  payload_json STRING NOT NULL,
  payload_hash STRING NOT NULL,
  data_classification STRING NOT NULL,
  landed_at TIMESTAMP NOT NULL
) USING DELTA
PARTITIONED BY (event_date, market_zone);

CREATE TABLE IF NOT EXISTS quarantine_event (
  quarantine_id STRING NOT NULL,
  event_id STRING,
  event_ts TIMESTAMP,
  plant_id STRING,
  asset_id STRING,
  quarantine_reason STRING NOT NULL,
  rule_id STRING NOT NULL,
  detail STRING NOT NULL,
  payload_json STRING NOT NULL,
  payload_hash STRING NOT NULL,
  correlation_id STRING,
  quarantined_at TIMESTAMP NOT NULL,
  quarantine_date DATE NOT NULL
) USING DELTA
PARTITIONED BY (quarantine_date, plant_id);

CREATE TABLE IF NOT EXISTS quarantine_batch (
  quarantine_id STRING NOT NULL,
  batch_id STRING NOT NULL,
  source_system STRING NOT NULL,
  source_record_id STRING,
  quarantine_reason STRING NOT NULL,
  rule_id STRING NOT NULL,
  detail STRING NOT NULL,
  payload_json STRING NOT NULL,
  payload_hash STRING NOT NULL,
  quarantined_at TIMESTAMP NOT NULL,
  quarantine_date DATE NOT NULL
) USING DELTA
PARTITIONED BY (quarantine_date, source_system);
