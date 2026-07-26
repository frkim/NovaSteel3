-- Run with lh-ns-core attached as the default Lakehouse.
-- Gold is the only semantic-model source.

CREATE TABLE IF NOT EXISTS fact_energy_daily (
  date_key DATE NOT NULL,
  plant_id STRING NOT NULL,
  energy_gj DOUBLE NOT NULL,
  electricity_mwh DOUBLE,
  energy_cost_eur DOUBLE,
  baseline_energy_gj DOUBLE,
  baseline_cost_eur DOUBLE,
  crude_steel_tons DOUBLE NOT NULL,
  calculation_version STRING NOT NULL
) USING DELTA
PARTITIONED BY (date_key, plant_id);

CREATE TABLE IF NOT EXISTS fact_emissions_daily (
  date_key DATE NOT NULL,
  plant_id STRING NOT NULL,
  scope1_co2e_t DOUBLE NOT NULL,
  scope2_co2e_t DOUBLE NOT NULL,
  total_co2e_t DOUBLE NOT NULL,
  baseline_co2e_t DOUBLE,
  crude_steel_tons DOUBLE NOT NULL,
  free_allocation_t DOUBLE,
  ets_allowance_price_eur_per_t DOUBLE,
  ets_exposure_eur DOUBLE,
  calculation_version STRING NOT NULL
) USING DELTA
PARTITIONED BY (date_key, plant_id);

CREATE TABLE IF NOT EXISTS fact_production_shift (
  shift_id STRING NOT NULL,
  shift_date DATE NOT NULL,
  plant_id STRING NOT NULL,
  line_id STRING NOT NULL,
  planned_minutes DOUBLE NOT NULL,
  runtime_minutes DOUBLE NOT NULL,
  ideal_rate_tph DOUBLE NOT NULL,
  total_tons DOUBLE NOT NULL,
  good_tons DOUBLE NOT NULL,
  crude_steel_tons DOUBLE NOT NULL,
  on_time_orders BIGINT NOT NULL,
  total_orders BIGINT NOT NULL,
  calculation_version STRING NOT NULL
) USING DELTA
PARTITIONED BY (shift_date, plant_id);

CREATE TABLE IF NOT EXISTS fact_quality_yield (
  date_key DATE NOT NULL,
  plant_id STRING NOT NULL,
  grade_code STRING NOT NULL,
  high_grade_flag BOOLEAN NOT NULL,
  attempted_tons DOUBLE NOT NULL,
  first_pass_good_tons DOUBLE NOT NULL,
  rework_tons DOUBLE NOT NULL,
  downgrade_tons DOUBLE NOT NULL,
  scrap_tons DOUBLE NOT NULL,
  defect_count BIGINT NOT NULL,
  produced_units BIGINT NOT NULL,
  open_ncr_count BIGINT NOT NULL,
  calculation_version STRING NOT NULL
) USING DELTA
PARTITIONED BY (date_key, plant_id);

CREATE TABLE IF NOT EXISTS fact_furnace_rul (
  inference_id STRING NOT NULL,
  scored_date DATE NOT NULL,
  scored_at TIMESTAMP NOT NULL,
  plant_id STRING NOT NULL,
  asset_id STRING NOT NULL,
  component_id STRING NOT NULL,
  rul_days_p10 DOUBLE NOT NULL,
  rul_days_p50 DOUBLE NOT NULL,
  rul_days_p90 DOUBLE NOT NULL,
  risk_score DOUBLE NOT NULL,
  confidence DOUBLE NOT NULL,
  predicted_failure_date DATE NOT NULL,
  alert_issued_at TIMESTAMP,
  actual_reline_or_failure_at TIMESTAMP,
  unplanned_outage_flag BOOLEAN NOT NULL,
  model_version STRING NOT NULL,
  top_factors_json STRING NOT NULL,
  scenario_id STRING,
  seed BIGINT
) USING DELTA
PARTITIONED BY (scored_date, plant_id);

CREATE TABLE IF NOT EXISTS fact_dispatch_recommendation (
  recommendation_id STRING NOT NULL,
  recommendation_date DATE NOT NULL,
  issued_at TIMESTAMP NOT NULL,
  plant_id STRING NOT NULL,
  status STRING NOT NULL,
  baseline_cost_eur DOUBLE NOT NULL,
  optimized_cost_eur DOUBLE NOT NULL,
  as_run_cost_eur DOUBLE,
  expected_cost_avoidance_eur DOUBLE NOT NULL,
  realized_cost_avoidance_eur DOUBLE,
  expected_co2_avoided_t DOUBLE,
  shiftable_mw DOUBLE,
  hard_constraint_violations BIGINT NOT NULL,
  model_version STRING NOT NULL,
  correlation_id STRING NOT NULL
) USING DELTA
PARTITIONED BY (recommendation_date, plant_id);

CREATE TABLE IF NOT EXISTS fact_knowledge_procedure (
  procedure_id STRING NOT NULL,
  version INT NOT NULL,
  topic_id STRING NOT NULL,
  equipment_id STRING,
  review_status STRING NOT NULL,
  approved_flag BOOLEAN NOT NULL,
  published_date DATE,
  source_citation_count BIGINT NOT NULL,
  content_hash STRING NOT NULL
) USING DELTA
PARTITIONED BY (published_date);

CREATE TABLE IF NOT EXISTS fact_ai_decision_audit (
  audit_id STRING NOT NULL,
  recorded_date DATE NOT NULL,
  recorded_at TIMESTAMP NOT NULL,
  domain STRING NOT NULL,
  entity_id STRING NOT NULL,
  recommendation_status STRING NOT NULL,
  input_snapshot_ref STRING NOT NULL,
  model_version STRING,
  confidence DOUBLE,
  human_decision_at TIMESTAMP,
  outcome_recorded_at TIMESTAMP,
  complete_audit_flag BOOLEAN NOT NULL,
  correlation_id STRING NOT NULL,
  projection_version STRING NOT NULL
) USING DELTA
PARTITIONED BY (recorded_date, domain);

CREATE TABLE IF NOT EXISTS dim_kpi_target (
  kpi_id STRING NOT NULL,
  environment STRING NOT NULL,
  baseline_value DOUBLE,
  target_value DOUBLE,
  unit STRING NOT NULL,
  target_direction STRING NOT NULL,
  valid_from DATE NOT NULL,
  valid_to DATE,
  source STRING NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS fact_model_evaluation (
  evaluation_id STRING NOT NULL,
  evaluation_date DATE NOT NULL,
  domain STRING NOT NULL,
  model_id STRING NOT NULL,
  model_version STRING NOT NULL,
  true_positive BIGINT NOT NULL,
  false_positive BIGINT NOT NULL,
  false_negative BIGINT NOT NULL,
  true_negative BIGINT NOT NULL,
  drift_score DOUBLE,
  passed_gate BOOLEAN NOT NULL
) USING DELTA
PARTITIONED BY (evaluation_date, domain);

CREATE TABLE IF NOT EXISTS fact_customer_claim (
  claim_id STRING NOT NULL,
  claim_date DATE NOT NULL,
  plant_id STRING NOT NULL,
  material_id STRING,
  non_conformance_count BIGINT NOT NULL,
  tons_shipped DOUBLE NOT NULL,
  predicted_risk_flag BOOLEAN
) USING DELTA
PARTITIONED BY (claim_date, plant_id);

CREATE TABLE IF NOT EXISTS fact_knowledge_usage (
  query_id STRING NOT NULL,
  query_date DATE NOT NULL,
  topic_id STRING,
  retrieval_ms BIGINT NOT NULL,
  cited_answer_flag BOOLEAN NOT NULL
) USING DELTA
PARTITIONED BY (query_date);

CREATE TABLE IF NOT EXISTS fact_platform_usage (
  week_start DATE NOT NULL,
  persona_group STRING NOT NULL,
  user_subject STRING NOT NULL,
  active_flag BOOLEAN NOT NULL,
  target_user_flag BOOLEAN NOT NULL
) USING DELTA
PARTITIONED BY (week_start);

CREATE TABLE IF NOT EXISTS dq_run_result (
  run_id STRING NOT NULL,
  run_date DATE NOT NULL,
  table_name STRING NOT NULL,
  rule_id STRING NOT NULL,
  status STRING NOT NULL,
  evaluated_rows BIGINT NOT NULL,
  failed_rows BIGINT NOT NULL,
  metric_value DOUBLE,
  threshold DOUBLE,
  recorded_at TIMESTAMP NOT NULL
) USING DELTA
PARTITIONED BY (run_date);

CREATE TABLE IF NOT EXISTS pipeline_run_reconciliation (
  run_id STRING NOT NULL,
  run_date DATE NOT NULL,
  dataset STRING NOT NULL,
  bronze_rows BIGINT NOT NULL,
  silver_rows BIGINT NOT NULL,
  quarantine_rows BIGINT NOT NULL,
  duplicate_rows BIGINT NOT NULL,
  unexplained_rows BIGINT NOT NULL,
  status STRING NOT NULL,
  recorded_at TIMESTAMP NOT NULL
) USING DELTA
PARTITIONED BY (run_date);
