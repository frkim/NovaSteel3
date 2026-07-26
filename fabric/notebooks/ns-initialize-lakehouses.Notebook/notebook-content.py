# Fabric notebook source

# METADATA ********************
# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************
from datetime import date, datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import functions as F

# Pipeline parameters. The deployment script renders the defaults, and a
# Fabric Notebook activity can override them per environment/run.
ENVIRONMENT = "{{environment}}"
LANDING_TABLES_URI = "{{onelake.landingTablesUri}}"
CORE_TABLES_URI = "{{onelake.coreTablesUri}}"
CALCULATION_VERSION = "novasteel-medallion/1.0.0"


def require_resolved(name: str, value: str) -> None:
    if not value or value.startswith("{{"):
        raise ValueError(f"{name} must be resolved to an environment value")


def table_path(root: str, table_name: str) -> str:
    return f"{root.rstrip('/')}/{table_name}"


def ensure_delta_table(root: str, table_name: str, schema_ddl: str, partitions=()) -> None:
    path = table_path(root, table_name)
    if DeltaTable.isDeltaTable(spark, path):
        return
    frame = spark.createDataFrame([], schema_ddl)
    writer = frame.write.format("delta").mode("ignore")
    if partitions:
        writer = writer.partitionBy(*partitions)
    writer.save(path)


require_resolved("ENVIRONMENT", ENVIRONMENT)
require_resolved("LANDING_TABLES_URI", LANDING_TABLES_URI)
require_resolved("CORE_TABLES_URI", CORE_TABLES_URI)

landing_specs = {
    "bronze_event_envelope": (
        "event_id string, event_ts timestamp, ingest_ts timestamp, sequence long, "
        "source_id string, plant_id string, asset_id string, schema_name string, "
        "schema_version int, correlation_id string, data_classification string, "
        "privacy_label string, scenario_id string, seed long, generator_version string, "
        "clock_mode string, payload_json string, payload_hash string, run_id string, "
        "event_date date, landed_at timestamp",
        ("event_date", "plant_id"),
    ),
    "quarantine_event": (
        "quarantine_id string, event_id string, event_ts timestamp, plant_id string, "
        "asset_id string, quarantine_reason string, rule_id string, detail string, "
        "payload_json string, payload_hash string, correlation_id string, "
        "quarantined_at timestamp, quarantine_date date",
        ("quarantine_date", "plant_id"),
    ),
    "quarantine_batch": (
        "quarantine_id string, batch_id string, source_system string, source_record_id string, "
        "quarantine_reason string, rule_id string, detail string, payload_json string, "
        "payload_hash string, quarantined_at timestamp, quarantine_date date",
        ("quarantine_date", "source_system"),
    ),
}

core_specs = {
    "dim_plant": (
        "plant_key long, plant_id string, plant_name string, country_code string, "
        "time_zone string, route string, valid_from timestamp, valid_to timestamp, "
        "is_current boolean, version int, change_reason string",
        (),
    ),
    "dim_asset": (
        "asset_key long, asset_id string, plant_id string, parent_asset_id string, area string, "
        "line_id string, asset_type string, criticality string, commissioned_state string, "
        "valid_from timestamp, valid_to timestamp, is_current boolean, version int, "
        "change_reason string",
        ("plant_id",),
    ),
    "dim_sensor": (
        "sensor_key long, sensor_id string, plant_id string, asset_id string, signal_code string, "
        "canonical_unit string, hard_min double, hard_max double, sample_period_ms long, "
        "calibration_version string, valid_from timestamp, valid_to timestamp, "
        "is_current boolean, version int, change_reason string",
        ("plant_id",),
    ),
    "dim_grade": (
        "grade_key long, grade_code string, grade_family string, high_grade_flag boolean, "
        "target_json string, valid_from timestamp, valid_to timestamp, is_current boolean, "
        "version int, change_reason string",
        (),
    ),
    "dim_calendar": (
        "date_key date, plant_id string, local_date date, year int, month int, iso_week int, "
        "day_of_week int, is_holiday boolean",
        (),
    ),
    "fact_telemetry": (
        "event_id string, event_ts timestamp, ingest_ts timestamp, event_date date, "
        "plant_key long, asset_key long, sensor_key long, plant_id string, asset_id string, "
        "sensor_id string, signal_code string, value double, unit string, source_quality string, "
        "uncertainty double, late_flag boolean, scenario_id string, seed long, "
        "correlation_id string, data_classification string",
        ("event_date", "plant_id"),
    ),
    "fact_energy_interval": (
        "meter_id string, plant_id string, interval_start timestamp, interval_end timestamp, "
        "event_date date, energy_type string, energy_mwh double, energy_gj double, "
        "spot_price_eur_per_mwh double, grid_carbon_kg_per_mwh double, cost_eur double, "
        "co2e_t double, source_version string, data_classification string",
        ("event_date", "plant_id"),
    ),
    "fact_quality_measurement": (
        "sample_id string, characteristic_code string, event_ts timestamp, event_date date, "
        "plant_id string, asset_id string, material_id string, heat_id string, grade_key long, "
        "grade_code string, value double, unit string, lower_spec_limit double, "
        "upper_spec_limit double, measurement_method string, result_status string, "
        "first_pass_flag boolean, tons double",
        ("event_date", "plant_id"),
    ),
    "fact_maintenance_event": (
        "work_order_id string, event_ts timestamp, event_date date, plant_id string, "
        "asset_id string, component_id string, event_type string, failure_mode string, "
        "action_code string, planned_flag boolean, downtime_hours double, "
        "linked_inference_id string",
        ("event_date", "plant_id"),
    ),
    "fact_alarm_event": (
        "alarm_id string, transition_id string, event_ts timestamp, event_date date, "
        "plant_id string, asset_id string, severity string, state string, alarm_type string, "
        "confidence double, correlation_id string",
        ("event_date", "plant_id"),
    ),
    "fact_model_inference": (
        "inference_id string, event_date date, feature_snapshot_ts timestamp, scored_at timestamp, "
        "plant_id string, entity_id string, component_id string, model_id string, "
        "model_version string, prediction_type string, prediction_value double, unit string, "
        "p10 double, p50 double, p90 double, risk_score double, confidence double, "
        "top_factors_json string, feature_snapshot_ref string, scenario_id string, seed long",
        ("event_date", "plant_id"),
    ),
    "fact_ai_decision": (
        "audit_event_id string, audit_id string, event_ts timestamp, event_date date, "
        "domain string, entity_id string, event_type string, recommendation_status string, "
        "input_snapshot_ref string, model_version string, output_json string, confidence double, "
        "actor_id string, reason_code string, correlation_id string, complete_audit_flag boolean",
        ("event_date", "domain"),
    ),
    "fact_energy_daily": (
        "date_key date, plant_id string, energy_gj double, electricity_mwh double, "
        "energy_cost_eur double, baseline_energy_gj double, baseline_cost_eur double, "
        "crude_steel_tons double, calculation_version string",
        ("date_key", "plant_id"),
    ),
    "fact_emissions_daily": (
        "date_key date, plant_id string, scope1_co2e_t double, scope2_co2e_t double, "
        "total_co2e_t double, baseline_co2e_t double, crude_steel_tons double, "
        "free_allocation_t double, ets_allowance_price_eur_per_t double, "
        "ets_exposure_eur double, calculation_version string",
        ("date_key", "plant_id"),
    ),
    "fact_production_shift": (
        "shift_id string, shift_date date, plant_id string, line_id string, "
        "planned_minutes double, runtime_minutes double, ideal_rate_tph double, "
        "total_tons double, good_tons double, crude_steel_tons double, "
        "on_time_orders long, total_orders long, calculation_version string",
        ("shift_date", "plant_id"),
    ),
    "fact_quality_yield": (
        "date_key date, plant_id string, grade_code string, high_grade_flag boolean, "
        "attempted_tons double, first_pass_good_tons double, rework_tons double, "
        "downgrade_tons double, scrap_tons double, defect_count long, produced_units long, "
        "open_ncr_count long, calculation_version string",
        ("date_key", "plant_id"),
    ),
    "fact_furnace_rul": (
        "inference_id string, scored_date date, scored_at timestamp, plant_id string, "
        "asset_id string, component_id string, rul_days_p10 double, rul_days_p50 double, "
        "rul_days_p90 double, risk_score double, confidence double, predicted_failure_date date, "
        "alert_issued_at timestamp, actual_reline_or_failure_at timestamp, "
        "unplanned_outage_flag boolean, model_version string, top_factors_json string, "
        "scenario_id string, seed long",
        ("scored_date", "plant_id"),
    ),
    "fact_dispatch_recommendation": (
        "recommendation_id string, recommendation_date date, issued_at timestamp, plant_id string, "
        "status string, baseline_cost_eur double, optimized_cost_eur double, as_run_cost_eur double, "
        "expected_cost_avoidance_eur double, realized_cost_avoidance_eur double, "
        "expected_co2_avoided_t double, shiftable_mw double, hard_constraint_violations long, "
        "model_version string, correlation_id string",
        ("recommendation_date", "plant_id"),
    ),
    "fact_knowledge_procedure": (
        "procedure_id string, version int, topic_id string, equipment_id string, "
        "review_status string, approved_flag boolean, published_date date, "
        "source_citation_count long, content_hash string",
        ("published_date",),
    ),
    "fact_ai_decision_audit": (
        "audit_id string, recorded_date date, recorded_at timestamp, domain string, entity_id string, "
        "recommendation_status string, input_snapshot_ref string, model_version string, "
        "confidence double, human_decision_at timestamp, outcome_recorded_at timestamp, "
        "complete_audit_flag boolean, correlation_id string, projection_version string",
        ("recorded_date", "domain"),
    ),
    "dim_kpi_target": (
        "kpi_id string, environment string, baseline_value double, target_value double, unit string, "
        "target_direction string, valid_from date, valid_to date, source string",
        (),
    ),
    "fact_model_evaluation": (
        "evaluation_id string, evaluation_date date, domain string, model_id string, "
        "model_version string, true_positive long, false_positive long, false_negative long, "
        "true_negative long, drift_score double, passed_gate boolean",
        ("evaluation_date", "domain"),
    ),
    "fact_customer_claim": (
        "claim_id string, claim_date date, plant_id string, material_id string, "
        "non_conformance_count long, tons_shipped double, predicted_risk_flag boolean",
        ("claim_date", "plant_id"),
    ),
    "fact_knowledge_usage": (
        "query_id string, query_date date, topic_id string, retrieval_ms long, "
        "cited_answer_flag boolean",
        ("query_date",),
    ),
    "fact_platform_usage": (
        "week_start date, persona_group string, user_subject string, active_flag boolean, "
        "target_user_flag boolean",
        ("week_start",),
    ),
    "dq_run_result": (
        "run_id string, run_date date, table_name string, rule_id string, status string, "
        "evaluated_rows long, failed_rows long, metric_value double, threshold double, "
        "recorded_at timestamp",
        ("run_date",),
    ),
    "pipeline_run_reconciliation": (
        "run_id string, run_date date, dataset string, bronze_rows long, silver_rows long, "
        "quarantine_rows long, duplicate_rows long, unexplained_rows long, status string, "
        "recorded_at timestamp",
        ("run_date",),
    ),
}

for table_name, (schema_ddl, partitions) in landing_specs.items():
    ensure_delta_table(LANDING_TABLES_URI, table_name, schema_ddl, partitions)

for table_name, (schema_ddl, partitions) in core_specs.items():
    ensure_delta_table(CORE_TABLES_URI, table_name, schema_ddl, partitions)

kpi_targets = [
    ("KPI-ENE-01", ENVIRONMENT, 19.5, 16.77, "GJ/t", "decrease", "Energy SEC baseline/target"),
    ("KPI-CO2-01", ENVIRONMENT, 2.10, 1.638, "tCO2e/t", "decrease", "Specific CO2 baseline/target"),
    ("KPI-FUR-01", ENVIRONMENT, 0.0, 21.0, "days", "minimum", "Lining warning target"),
    ("KPI-QUA-01", ENVIRONMENT, 0.90, 0.972, "ratio", "increase", "High-grade first-pass yield target"),
    ("KPI-ENE-03", ENVIRONMENT, None, 0.70, "ratio", "minimum", "Dispatch adoption target"),
    ("KPI-ADO-01", ENVIRONMENT, None, 0.80, "ratio", "minimum", "Pilot weekly adoption target"),
    ("KPI-GOV-01", ENVIRONMENT, None, 1.00, "ratio", "minimum", "Audit completeness target"),
]
target_frame = (
    spark.createDataFrame(
        kpi_targets,
        "kpi_id string, environment string, baseline_value double, target_value double, "
        "unit string, target_direction string, source string",
    )
    .withColumn("valid_from", F.lit(date(2026, 7, 25)))
    .withColumn("valid_to", F.lit(None).cast("date"))
)
target_path = table_path(CORE_TABLES_URI, "dim_kpi_target")
(
    DeltaTable.forPath(spark, target_path)
    .alias("target")
    .merge(
        target_frame.alias("source"),
        "target.kpi_id = source.kpi_id AND "
        "target.environment = source.environment AND "
        "target.valid_from = source.valid_from",
    )
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)

print(
    {
        "status": "initialized",
        "environment": ENVIRONMENT,
        "landing_table_count": len(landing_specs),
        "core_table_count": len(core_specs),
        "calculation_version": CALCULATION_VERSION,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
)

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
