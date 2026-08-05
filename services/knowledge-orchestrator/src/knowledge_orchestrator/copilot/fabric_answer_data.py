"""Card metadata for the Copilot's Fabric-answered predefined questions.

Pure data module: the matching logic lives in
``knowledge_orchestrator.copilot.fabric_answers`` and the answer prose lives in
the per-language ``fabric_answers_<lang>`` modules.

A card binds one chip -- identified by its screen slug and its position in
``suggestion_data.SUGGESTIONS_BY_SECTION`` -- to the Fabric datasets that carry
its figures and to the localized bodies that report them. The chips that ask for
*public* context ("Search for recent ...") deliberately have no card: those still
go to the online-search corpus.

Every figure quoted in the bodies is the synthetic value the demo already shows:
the fixture pack behind the screens (``apps/analytics-mfe/src/api/fixtures.ts``),
the device simulator manifest, or the verified July-2026 gold scorecard in
``docs/demo/data-agent-question-script.md``.
"""

from __future__ import annotations

from typing import Final

from .fabric_answers_de import ANSWERS as _DE
from .fabric_answers_en import ANSWERS as _EN
from .fabric_answers_es import ANSWERS as _ES
from .fabric_answers_fr import ANSWERS as _FR
from .fabric_answers_nl import ANSWERS as _NL
from .fabric_persona_data import PERSONA_CARDS
from .fabric_sources import (
    DATA_AGENT,
    KQL_DATABASE,
    LAKEHOUSE,
    ONTOLOGY,
    WORKSPACE,
    FabricCard,
    FabricDataset,
    bodies,
)
from .fabric_sources import gold as _gold
from .fabric_sources import graph as _graph
from .fabric_sources import kql as _kql

__all__ = [
    "CARDS",
    "DATA_AGENT",
    "KQL_DATABASE",
    "LAKEHOUSE",
    "ONTOLOGY",
    "WORKSPACE",
    "FabricCard",
    "FabricDataset",
]


# card id -> (section, chip index, datasets). The chip index is the position in
# SUGGESTIONS_BY_SECTION[section][language]; every language carries the same
# question in the same slot, which is what lets one card serve all five.
_SPECS: Final[tuple[tuple[str, str, int, tuple[FabricDataset, ...]], ...]] = (
    # -- command-center ----------------------------------------------------
    (
        "command-center-q1",
        "command-center",
        0,
        (
            _kql(
                "mv_alarm_current",
                "Open alarms by severity for the selected site.",
                statement="mv_alarm_current | where state !in ('MITIGATED','CLOSED') and plant_id == 'NS-DEMO-LUX-01' | project alarm_id, severity, state, alarm_type, confidence",
                rows=16,
                elapsed_ms=320,
            ),
            _gold(
                "fact_furnace_rul",
                "rul_days_p50, risk_score, alert_issued_at for LUX-BF-01.",
                statement="SELECT TOP 1 rul_days_p50, risk_score, alert_issued_at FROM fact_furnace_rul WHERE asset_id = 'LUX-BF-01' AND scored_date = '2026-07-25' ORDER BY scored_at DESC",
                rows=1,
                elapsed_ms=880,
            ),
        ),
    ),
    (
        "command-center-q2",
        "command-center",
        1,
        (
            _kql(
                "mv_alarm_current",
                "Highest-severity open alarm per domain.",
                statement="mv_alarm_current | where state !in ('MITIGATED','CLOSED') | summarize arg_max(severity, alarm_id) by alarm_type",
                rows=4,
                elapsed_ms=260,
            ),
            _gold(
                "fact_dispatch_recommendation",
                "expected_cost_avoidance_eur, status for REC-DEMO-LUX-240725.",
                statement="SELECT expected_cost_avoidance_eur, status FROM fact_dispatch_recommendation WHERE recommendation_id = 'REC-DEMO-LUX-240725' AND recommendation_date = '2026-07-25'",
                rows=1,
                elapsed_ms=910,
            ),
            _gold(
                "fact_emissions_daily",
                "ets_exposure_eur, free_allocation_t.",
                statement="SELECT ets_exposure_eur, free_allocation_t FROM fact_emissions_daily WHERE plant_id = 'NS-DEMO-LUX-01' AND date_key = '2026-07-25'",
                rows=1,
                elapsed_ms=740,
            ),
        ),
    ),
    (
        "command-center-q3",
        "command-center",
        2,
        (
            _kql(
                "alarm_hot",
                "Alarms raised or acknowledged since the previous handover.",
                statement="alarm_hot | where plant_id == 'NS-DEMO-LUX-01' and event_ts between(datetime(2026-07-25 06:00) .. datetime(2026-07-25 14:00)) | project alarm_id, state, event_ts",
                rows=5,
                elapsed_ms=290,
            ),
            _gold(
                "fact_ai_decision_audit",
                "domain, recommendation_status, human_decision_at.",
                statement="SELECT domain, recommendation_status, human_decision_at FROM fact_ai_decision_audit WHERE recorded_date = '2026-07-25' AND audit_id BETWEEN 'AUD-0001' AND 'AUD-0005'",
                rows=5,
                elapsed_ms=860,
            ),
        ),
    ),
    (
        "command-center-q4",
        "command-center",
        4,
        (
            _gold(
                "fact_dispatch_recommendation",
                "expected_cost_avoidance_eur, expected_co2_avoided_t, hard_constraint_violations.",
                statement="SELECT TOP 1 expected_cost_avoidance_eur,expected_co2_avoided_t,hard_constraint_violations FROM fact_dispatch_recommendation WHERE recommendation_date='2026-07-25' ORDER BY issued_at DESC",
                rows=1,
                elapsed_ms=950,
            ),
            _gold(
                "fact_furnace_rul",
                "risk_score, predicted_failure_date, unplanned_outage_flag.",
                statement="SELECT TOP 1 risk_score, predicted_failure_date, unplanned_outage_flag FROM fact_furnace_rul WHERE asset_id = 'LUX-BF-01' AND scored_date = '2026-07-25' ORDER BY scored_at DESC",
                rows=1,
                elapsed_ms=830,
            ),
        ),
    ),
    # -- operations --------------------------------------------------------
    (
        "operations-q1",
        "operations",
        0,
        (
            _kql(
                "telemetry_hot",
                "production_rate for the site, current shift.",
                statement="telemetry_hot | where signal_code == 'production_rate' and plant_id == 'NS-DEMO-LUX-01' and event_ts > ago(8h) | top 1 by event_ts desc | project value, unit, event_ts",
                rows=1,
                elapsed_ms=240,
            ),
            _gold(
                "fact_production_shift",
                "throughput and OEE against shift plan.",
                statement="SELECT TOP 1 total_tons, good_tons, runtime_minutes, planned_minutes FROM fact_production_shift WHERE plant_id = 'NS-DEMO-LUX-01' AND shift_date = '2026-07-25' ORDER BY shift_id DESC",
                rows=1,
                elapsed_ms=790,
            ),
        ),
    ),
    (
        "operations-q2",
        "operations",
        1,
        (
            _kql(
                "mv_telemetry_latest_by_signal",
                "production_rate per asset, last 24 h.",
                statement="mv_telemetry_latest_by_signal | where signal_code == 'production_rate' and plant_id == 'NS-DEMO-LUX-01' | project asset_id, value, event_ts",
                rows=5,
                elapsed_ms=270,
            ),
            _graph(
                "Asset -[supplies]-> Asset genealogy for the Luxembourg line.",
                statement="MATCH p=(a:Asset {AssetId:'LUX-BF-01'})-[:supplies*1..4]->(b:Asset {AssetId:'LUX-HSM-01'}) RETURN p",
                rows=4,
                elapsed_ms=540,
            ),
        ),
    ),
    (
        "operations-q3",
        "operations",
        2,
        (
            _kql(
                "mv_alarm_current",
                "Open and acknowledged alarms for the shift window.",
                statement="mv_alarm_current | where plant_id == 'NS-DEMO-LUX-01' and state !in ('MITIGATED','CLOSED') | project alarm_id, severity, state, alarm_type",
                rows=16,
                elapsed_ms=310,
            ),
            _gold(
                "fact_ai_decision_audit",
                "Decisions recorded during the shift.",
                statement="SELECT audit_id, domain, recommendation_status FROM fact_ai_decision_audit WHERE recorded_date = '2026-07-25' AND domain IN ('energy','quality','safety','maintenance')",
                rows=5,
                elapsed_ms=900,
            ),
        ),
    ),
    (
        "operations-q4",
        "operations",
        4,
        (
            _kql(
                "mv_alarm_current",
                "Severity, status and confidence of open alarms.",
                statement="mv_alarm_current | where plant_id == 'NS-DEMO-LUX-01' and state !in ('MITIGATED','CLOSED') | project alarm_id, severity, state, confidence",
                rows=16,
                elapsed_ms=280,
            ),
            _gold(
                "fact_furnace_rul",
                "risk_score and rul_days_p50 for the alerting asset.",
                statement="SELECT TOP 1 risk_score, rul_days_p50 FROM fact_furnace_rul WHERE asset_id = 'LUX-BF-01' AND scored_date = '2026-07-25' ORDER BY scored_at DESC",
                rows=1,
                elapsed_ms=820,
            ),
        ),
    ),
    # -- furnace-health ----------------------------------------------------
    (
        "furnace-health-q1",
        "furnace-health",
        0,
        (
            _kql(
                "telemetry_hot",
                "hearth_shell_temperature, local_heat_flux, cooling_water_* for LUX-BF-01.",
                statement="telemetry_hot | where asset_id == 'LUX-BF-01' and signal_code in ('hearth_shell_temperature','local_heat_flux','cooling_water_delta_t') and event_ts > ago(24h) | summarize avg(value) by sensor_id",
                rows=5,
                elapsed_ms=340,
            ),
            _kql(
                "mv_model_latest",
                "lining-rul-piml/1.3.0-demo feature contributions.",
                statement="mv_model_latest | where model_version == 'lining-rul-piml/1.3.0-demo' and asset_id == 'LUX-BF-01' | project top_factors, confidence, risk_score",
                rows=3,
                elapsed_ms=220,
            ),
        ),
    ),
    (
        "furnace-health-q2",
        "furnace-health",
        1,
        (
            _gold(
                "fact_furnace_rul",
                "rul_days_p10/p50/p90, risk_score, confidence, predicted_failure_date.",
                statement="SELECT asset_id,rul_days_p10,rul_days_p50,rul_days_p90,risk_score,confidence,predicted_failure_date FROM fact_furnace_rul WHERE asset_id IN('LUX-BF-01','LUX-RHF-01') AND scored_date='2026-07-25'",
                rows=2,
                elapsed_ms=970,
            ),
            _kql(
                "telemetry_hot",
                "hearth_refractory_estimate for HEARTH-SECTOR-07.",
                statement="telemetry_hot | where asset_id == 'LUX-BF-01' and signal_code == 'hearth_refractory_estimate' and sensor_id == 'HEARTH-SECTOR-07' | top 1 by event_ts desc | project value, event_ts",
                rows=1,
                elapsed_ms=250,
            ),
        ),
    ),
    (
        "furnace-health-q3",
        "furnace-health",
        2,
        (
            _gold(
                "fact_furnace_rul",
                "top_factors_json for the latest LUX-BF-01 score.",
                statement="SELECT TOP 1 top_factors_json FROM fact_furnace_rul WHERE asset_id = 'LUX-BF-01' AND scored_date = '2026-07-25' ORDER BY scored_at DESC",
                rows=1,
                elapsed_ms=760,
            ),
            _kql(
                "telemetry_hot",
                "6 h slopes on the hearth thermal signature.",
                statement="telemetry_hot | where asset_id == 'LUX-BF-01' and signal_code == 'hearth_shell_temperature' and event_ts > ago(6h) | summarize avg(value) by sensor_id",
                rows=5,
                elapsed_ms=330,
            ),
        ),
    ),
    (
        "furnace-health-q4",
        "furnace-health",
        4,
        (
            _gold(
                "fact_furnace_rul",
                "risk_score, predicted_failure_date, model_version.",
                statement="SELECT TOP 1 risk_score, predicted_failure_date, model_version FROM fact_furnace_rul WHERE asset_id = 'LUX-BF-01' AND scored_date = '2026-07-25' ORDER BY scored_at DESC",
                rows=1,
                elapsed_ms=840,
            ),
            _gold(
                "fact_knowledge_procedure",
                "Approved procedures linked to furnace equipment.",
                statement="SELECT procedure_id, version, approved_flag, source_citation_count FROM fact_knowledge_procedure WHERE equipment_id = 'LUX-BF-01' AND published_date BETWEEN '2026-07-01' AND '2026-07-29'",
                rows=2,
                elapsed_ms=680,
            ),
        ),
    ),
    # -- energy-optimization -----------------------------------------------
    (
        "energy-optimization-q1",
        "energy-optimization",
        0,
        (
            _gold(
                "fact_dispatch_recommendation",
                "baseline_cost_eur, optimized_cost_eur, shiftable_mw, status.",
                statement="SELECT baseline_cost_eur, optimized_cost_eur, shiftable_mw, status FROM fact_dispatch_recommendation WHERE recommendation_id = 'REC-DEMO-LUX-240725' AND recommendation_date = '2026-07-25'",
                rows=1,
                elapsed_ms=910,
            ),
            _kql(
                "telemetry_hot",
                "Day-ahead price curve, 96 quarter-hour slots.",
                statement="telemetry_hot | where asset_id == 'LUX-UTIL-01' and signal_code == 'spot_price' and event_ts between(datetime(2026-07-25) .. datetime(2026-07-26)) | project event_ts, value, unit | order by event_ts asc",
                rows=96,
                elapsed_ms=430,
            ),
        ),
    ),
    (
        "energy-optimization-q2",
        "energy-optimization",
        1,
        (
            _kql(
                "telemetry_hot",
                "spot_price per slot, evening scarcity window.",
                statement="telemetry_hot | where asset_id == 'LUX-UTIL-01' and signal_code == 'spot_price' and event_ts between(datetime(2026-07-25 17:00) .. datetime(2026-07-25 20:00)) | project event_ts, value",
                rows=12,
                elapsed_ms=290,
            ),
            _gold(
                "fact_energy_daily",
                "energy_cost_eur against baseline_cost_eur.",
                statement="SELECT energy_cost_eur, baseline_cost_eur FROM fact_energy_daily WHERE plant_id = 'NS-DEMO-LUX-01' AND date_key = '2026-07-25'",
                rows=1,
                elapsed_ms=730,
            ),
        ),
    ),
    (
        "energy-optimization-q3",
        "energy-optimization",
        2,
        (
            _gold(
                "fact_dispatch_recommendation",
                "hard_constraint_violations and the constraint report of the dispatch.",
                statement="SELECT hard_constraint_violations, status, model_version FROM fact_dispatch_recommendation WHERE recommendation_id = 'REC-DEMO-LUX-240725' AND recommendation_date = '2026-07-25'",
                rows=1,
                elapsed_ms=880,
            ),
        ),
    ),
    (
        "energy-optimization-q4",
        "energy-optimization",
        4,
        (
            _gold(
                "fact_dispatch_recommendation",
                "expected_co2_avoided_t, status.",
                statement="SELECT expected_co2_avoided_t, status FROM fact_dispatch_recommendation WHERE recommendation_id = 'REC-DEMO-LUX-240725' AND recommendation_date = '2026-07-25'",
                rows=1,
                elapsed_ms=820,
            ),
            _kql(
                "telemetry_hot",
                "grid_carbon_intensity per slot.",
                statement="telemetry_hot | where asset_id == 'LUX-UTIL-01' and signal_code == 'grid_carbon_intensity' and event_ts between(datetime(2026-07-25) .. datetime(2026-07-26)) | project event_ts, value | order by event_ts asc",
                rows=96,
                elapsed_ms=410,
            ),
        ),
    ),
    # -- quality -----------------------------------------------------------
    (
        "quality-q1",
        "quality",
        0,
        (
            _kql(
                "model_inference_hot",
                "Batch quality risk score and predicted yield, current heats.",
                statement="model_inference_hot | where plant_id == 'NS-DEMO-LUX-01' and prediction_type == 'quality' and scored_at > ago(24h) | summarize arg_max(scored_at, quality_risk_score, predicted_first_pass_yield) by asset_id",
                rows=20,
                elapsed_ms=360,
            ),
            _gold(
                "fact_quality_yield",
                "high_grade_flag, first_pass_good_tons, defect_count.",
                statement="SELECT high_grade_flag, first_pass_good_tons, defect_count FROM fact_quality_yield WHERE plant_id = 'NS-DEMO-LUX-01' AND date_key = '2026-07-25'",
                rows=1,
                elapsed_ms=710,
            ),
        ),
    ),
    (
        "quality-q2",
        "quality",
        1,
        (
            _kql(
                "model_inference_hot",
                "Control-chart series, last 20 quality inferences.",
                statement="model_inference_hot | where plant_id == 'NS-DEMO-LUX-01' and prediction_type == 'quality' and scored_at > ago(48h) | top 20 by scored_at desc | project asset_id, quality_risk_score, scored_at",
                rows=20,
                elapsed_ms=370,
            ),
            _gold(
                "fact_quality_yield",
                "defect_count and loss breakdown, 30-day window.",
                statement="SELECT date_key, defect_count, rework_tons, downgrade_tons, scrap_tons FROM fact_quality_yield WHERE plant_id = 'NS-DEMO-LUX-01' AND date_key BETWEEN '2026-07-01' AND '2026-07-30'",
                rows=30,
                elapsed_ms=980,
            ),
        ),
    ),
    (
        "quality-q3",
        "quality",
        2,
        (
            _kql(
                "telemetry_hot",
                "Batch signal genealogy from source heat to shipped coil.",
                statement="telemetry_hot | where asset_id == 'LUX-HSM-01' and signal_code == 'coiling_temperature' and correlation_id has 'COIL-LUX-260725-017' | project event_ts, sensor_id, value, correlation_id | order by event_ts asc",
                rows=8,
                elapsed_ms=300,
            ),
            _graph(
                "Asset -[supplies]-> Asset path feeding the mill that coiled it.",
                statement="MATCH p=(a:Asset {AssetId:'LUX-CC-01'})-[:supplies*1..3]->(b:Asset {AssetId:'LUX-HSM-01'}) RETURN p",
                rows=3,
                elapsed_ms=510,
            ),
        ),
    ),
    (
        "quality-q4",
        "quality",
        4,
        (
            _kql(
                "mv_model_latest",
                "quality-yield-gbm/2.1.0-demo bounded what-if.",
                statement="mv_model_latest | where model_version == 'quality-yield-gbm/2.1.0-demo' and label == 'bounded-what-if' | project predicted_first_pass_yield, quality_risk_score, confidence",
                rows=1,
                elapsed_ms=230,
            ),
            _gold(
                "fact_quality_yield",
                "first_pass_good_tons / attempted_tons against KPI-QUA-01.",
                statement="SELECT TOP 1 attempted_tons, first_pass_good_tons FROM fact_quality_yield WHERE plant_id = 'NS-DEMO-LUX-01' AND high_grade_flag = 1 AND date_key = '2026-07-25'",
                rows=1,
                elapsed_ms=720,
            ),
        ),
    ),
    # -- sustainability-compliance -----------------------------------------
    (
        "sustainability-compliance-q1",
        "sustainability-compliance",
        0,
        (
            _gold(
                "fact_emissions_daily",
                "ets_exposure_eur, free_allocation_t, ets_allowance_price_eur_per_t.",
                statement="SELECT ets_exposure_eur, free_allocation_t, ets_allowance_price_eur_per_t FROM fact_emissions_daily WHERE plant_id = 'NS-DEMO-LUX-01' AND date_key = '2026-07-25'",
                rows=1,
                elapsed_ms=770,
            ),
            _gold(
                "dim_kpi_target",
                "KPI-CO2-01 baseline and target.",
                statement="SELECT TOP 1 kpi_id, baseline_value, target_value FROM dim_kpi_target WHERE kpi_id = 'KPI-CO2-01' AND valid_from <= '2026-07-25' ORDER BY valid_from DESC",
                rows=1,
                elapsed_ms=620,
            ),
        ),
    ),
    (
        "sustainability-compliance-q2",
        "sustainability-compliance",
        1,
        (
            _gold(
                "fact_emissions_daily",
                "Monthly allowance consumption trend.",
                statement="SELECT TOP 7 DATETRUNC(month,date_key), SUM(total_co2e_t), SUM(free_allocation_t) FROM fact_emissions_daily WHERE plant_id = 'NS-DEMO-LUX-01' AND date_key <= '2026-07-31' GROUP BY DATETRUNC(month,date_key)",
                rows=7,
                elapsed_ms=930,
            ),
            _gold(
                "dim_kpi_target",
                "KPI-CO2-01 direction and target.",
                statement="SELECT TOP 1 kpi_id, target_direction, target_value FROM dim_kpi_target WHERE kpi_id = 'KPI-CO2-01' AND valid_from <= '2026-07-25' ORDER BY valid_from DESC",
                rows=1,
                elapsed_ms=640,
            ),
        ),
    ),
    (
        "sustainability-compliance-q3",
        "sustainability-compliance",
        2,
        (
            _gold(
                "fact_emissions_daily",
                "scope1_co2e_t, scope2_co2e_t, crude_steel_tons.",
                statement="SELECT scope1_co2e_t, scope2_co2e_t, crude_steel_tons FROM fact_emissions_daily WHERE plant_id = 'NS-DEMO-LUX-01' AND date_key = '2026-07-25'",
                rows=1,
                elapsed_ms=750,
            ),
            _kql(
                "telemetry_hot",
                "consumption and grid_carbon_intensity per interval.",
                statement="telemetry_hot | where asset_id == 'LUX-UTIL-01' and signal_code in ('grid_carbon_intensity','electricity_consumption') and event_ts between(datetime(2026-07-25) .. datetime(2026-07-26)) | project event_ts, signal_code, value | order by event_ts asc",
                rows=96,
                elapsed_ms=420,
            ),
        ),
    ),
    (
        "sustainability-compliance-q4",
        "sustainability-compliance",
        4,
        (
            _gold(
                "fact_dispatch_recommendation",
                "expected_co2_avoided_t per accepted dispatch.",
                statement="SELECT expected_co2_avoided_t, status FROM fact_dispatch_recommendation WHERE recommendation_id = 'REC-DEMO-LUX-240725' AND recommendation_date = '2026-07-25'",
                rows=1,
                elapsed_ms=810,
            ),
            _gold(
                "fact_emissions_daily",
                "total_co2e_t and ets_exposure_eur.",
                statement="SELECT total_co2e_t, ets_exposure_eur FROM fact_emissions_daily WHERE plant_id = 'NS-DEMO-LUX-01' AND date_key = '2026-07-25'",
                rows=1,
                elapsed_ms=700,
            ),
        ),
    ),
    # -- knowledge-hub -----------------------------------------------------
    (
        "knowledge-hub-q1",
        "knowledge-hub",
        0,
        (
            _gold(
                "fact_knowledge_procedure",
                "approved_flag, review_status, source_citation_count, equipment_id.",
                statement="SELECT approved_flag,review_status,source_citation_count,equipment_id FROM fact_knowledge_procedure WHERE procedure_id IN('PROC-DEMO-0001','PROC-DEMO-0002') AND published_date<='2026-07-25'",
                rows=2,
                elapsed_ms=660,
            ),
        ),
    ),
    (
        "knowledge-hub-q2",
        "knowledge-hub",
        1,
        (
            _gold(
                "fact_knowledge_usage",
                "Coverage and lookup counts per knowledge domain.",
                statement="SELECT TOP 5 topic_id, COUNT(*) AS hits, AVG(retrieval_ms) AS avg_ms FROM fact_knowledge_usage WHERE query_date BETWEEN '2026-07-01' AND '2026-07-29' GROUP BY topic_id ORDER BY hits DESC",
                rows=5,
                elapsed_ms=690,
            ),
            _gold(
                "fact_knowledge_procedure",
                "Domains with no approved procedure.",
                statement="SELECT TOP 3 procedure_id, topic_id, approved_flag FROM fact_knowledge_procedure WHERE published_date BETWEEN '2026-07-01' AND '2026-07-29' ORDER BY approved_flag ASC, procedure_id",
                rows=3,
                elapsed_ms=720,
            ),
        ),
    ),
    (
        "knowledge-hub-q3",
        "knowledge-hub",
        2,
        (
            _gold(
                "fact_knowledge_procedure",
                "review_status, published_date, procedure_id.",
                statement="SELECT procedure_id, review_status, published_date FROM fact_knowledge_procedure WHERE published_date BETWEEN '2026-07-01' AND '2026-07-29'",
                rows=3,
                elapsed_ms=650,
            ),
        ),
    ),
    (
        "knowledge-hub-q4",
        "knowledge-hub",
        4,
        (
            _gold(
                "fact_knowledge_procedure",
                "Approved hearth procedure and its citations.",
                statement="SELECT procedure_id, source_citation_count, content_hash FROM fact_knowledge_procedure WHERE procedure_id = 'PROC-DEMO-0001' AND published_date <= '2026-07-25'",
                rows=1,
                elapsed_ms=670,
            ),
            _gold(
                "fact_knowledge_procedure",
                "Captured procedure citations grounding the interview guide.",
                statement="SELECT procedure_id, version, topic_id, source_citation_count, review_status FROM fact_knowledge_procedure WHERE procedure_id = 'PROC-DEMO-0001'",
                rows=1,
                elapsed_ms=650,
            ),
        ),
    ),
    # -- executive-overview ------------------------------------------------
    (
        "executive-overview-q1",
        "executive-overview",
        0,
        (
            _gold(
                "dim_kpi_target",
                "kpi_id, baseline_value, target_value, target_direction.",
                statement="SELECT TOP 7 kpi_id, baseline_value, target_value, target_direction FROM dim_kpi_target WHERE environment = 'pilot' AND valid_from <= '2026-07-25' ORDER BY kpi_id",
                rows=7,
                elapsed_ms=780,
            ),
            _gold(
                "fact_energy_daily",
                "energy_gj / crude_steel_tons, July 2026.",
                statement="SELECT date_key, energy_gj, crude_steel_tons FROM fact_energy_daily WHERE plant_id = 'NS-DEMO-LUX-01' AND date_key BETWEEN '2026-07-01' AND '2026-07-29'",
                rows=29,
                elapsed_ms=1040,
            ),
            _gold(
                "fact_quality_yield",
                "high-grade first-pass yield, July 2026.",
                statement="SELECT date_key, first_pass_good_tons, attempted_tons FROM fact_quality_yield WHERE plant_id = 'NS-DEMO-LUX-01' AND date_key BETWEEN '2026-07-01' AND '2026-07-29'",
                rows=29,
                elapsed_ms=1120,
            ),
        ),
    ),
    (
        "executive-overview-q2",
        "executive-overview",
        1,
        (
            _gold(
                "fact_energy_daily",
                "Energy intensity by plant_id.",
                statement="SELECT plant_id, energy_gj, crude_steel_tons FROM fact_energy_daily WHERE date_key = '2026-07-25'",
                rows=4,
                elapsed_ms=820,
            ),
            _gold(
                "fact_emissions_daily",
                "CO2 intensity by plant_id.",
                statement="SELECT plant_id, total_co2e_t, crude_steel_tons FROM fact_emissions_daily WHERE date_key = '2026-07-25'",
                rows=4,
                elapsed_ms=860,
            ),
            _kql(
                "mv_alarm_current",
                "Open alarms per site.",
                statement="mv_alarm_current | where state !in ('MITIGATED','CLOSED') | summarize open_alarms=count() by plant_id",
                rows=4,
                elapsed_ms=240,
            ),
        ),
    ),
    (
        "executive-overview-q3",
        "executive-overview",
        2,
        (
            _gold(
                "dim_kpi_target",
                "Programme targets, stated as targets.",
                statement="SELECT TOP 4 kpi_id, target_value, unit FROM dim_kpi_target WHERE environment = 'programme' AND valid_from <= '2026-07-25' ORDER BY kpi_id",
                rows=4,
                elapsed_ms=700,
            ),
            _gold(
                "fact_ai_decision_audit",
                "complete_audit_flag across domains.",
                statement="SELECT audit_id, domain, complete_audit_flag FROM fact_ai_decision_audit WHERE recorded_date = '2026-07-25'",
                rows=5,
                elapsed_ms=880,
            ),
        ),
    ),
    (
        "executive-overview-q4",
        "executive-overview",
        4,
        (
            _gold(
                "dim_kpi_target",
                "Pilot targets.",
                statement="SELECT TOP 7 kpi_id, target_value, unit FROM dim_kpi_target WHERE environment = 'pilot' AND valid_from <= '2026-07-25' ORDER BY kpi_id",
                rows=7,
                elapsed_ms=760,
            ),
            _gold(
                "fact_dispatch_recommendation",
                "realized_cost_avoidance_eur, measured.",
                statement="SELECT recommendation_id, realized_cost_avoidance_eur, as_run_cost_eur FROM fact_dispatch_recommendation WHERE recommendation_id = 'REC-DEMO-LUX-240725' AND recommendation_date = '2026-07-25'",
                rows=1,
                elapsed_ms=830,
            ),
        ),
    ),
    # -- platform-ops ------------------------------------------------------
    (
        "platform-ops-q1",
        "platform-ops",
        0,
        (
            _kql(
                "mv_gateway_latest",
                "Gateway connection state and freshness for the demo capacity.",
                statement="mv_gateway_latest | where plant_id == 'NS-DEMO-LUX-01' | project gateway_id, connection_state, event_time_lag_ms, queue_depth",
                rows=4,
                elapsed_ms=210,
            ),
        ),
    ),
    (
        "platform-ops-q2",
        "platform-ops",
        1,
        (
            _gold(
                "pipeline_run_reconciliation",
                "Pipeline run status and row counts, latest five runs.",
                statement="SELECT TOP 5 run_id, dataset, status, bronze_rows, silver_rows, quarantine_rows, recorded_at FROM pipeline_run_reconciliation WHERE run_date = '2026-07-25' ORDER BY recorded_at DESC",
                rows=5,
                elapsed_ms=780,
            ),
        ),
    ),
    (
        "platform-ops-q3",
        "platform-ops",
        2,
        (
            _kql(
                "gateway_health_hot",
                "Gateway heartbeat lag and queue depth telemetry.",
                statement="gateway_health_hot | where plant_id == 'NS-DEMO-LUX-01' and event_ts > ago(13h) | summarize avg(event_time_lag_ms), avg(queue_depth) by bin(event_ts, 1h)",
                rows=13,
                elapsed_ms=300,
            ),
        ),
    ),
    (
        "platform-ops-q4",
        "platform-ops",
        4,
        (
            _gold(
                "pipeline_run_reconciliation",
                "In-flight and recent pipeline runs with reconciliation status.",
                statement="SELECT TOP 5 run_id, dataset, status, unexplained_rows, recorded_at FROM pipeline_run_reconciliation WHERE run_date = '2026-07-25' ORDER BY recorded_at DESC",
                rows=5,
                elapsed_ms=810,
            ),
        ),
    ),
    # -- device-operations -------------------------------------------------
    (
        "device-operations-q1",
        "device-operations",
        0,
        (
            _kql(
                "mv_gateway_latest",
                "Device connection state and last-seen per gateway.",
                statement="mv_gateway_latest | project gateway_id, plant_id, connection_state, event_time_lag_ms, heartbeat_ts",
                rows=17,
                elapsed_ms=240,
            ),
            _kql(
                "mv_telemetry_latest_by_signal",
                "Signal freshness per device.",
                statement="mv_telemetry_latest_by_signal | where plant_id == 'NS-DEMO-LUX-01' | project asset_id, signal_code, event_ts, sample_period_ms",
                rows=91,
                elapsed_ms=310,
            ),
        ),
    ),
    (
        "device-operations-q2",
        "device-operations",
        1,
        (
            _kql(
                "mv_gateway_latest",
                "Health-score inputs: connection state, lag, queue depth.",
                statement="mv_gateway_latest | project gateway_id, connection_state, event_time_lag_ms, queue_depth, duplicate_count, publish_retry_count",
                rows=17,
                elapsed_ms=260,
            ),
        ),
    ),
    (
        "device-operations-q3",
        "device-operations",
        2,
        (
            _kql(
                "mv_telemetry_latest_by_signal",
                "Last event timestamp per signal against its sample period.",
                statement="mv_telemetry_latest_by_signal | project signal_code, asset_id, event_ts, sample_period_ms | extend stale=datetime_diff('ms', now(), event_ts) > sample_period_ms",
                rows=91,
                elapsed_ms=320,
            ),
            _kql(
                "ingest_quarantine_hot",
                "Rejected or late envelopes.",
                statement="ingest_quarantine_hot | where quarantined_at > ago(24h) | summarize rejected=count() by quarantine_reason",
                rows=1,
                elapsed_ms=190,
            ),
        ),
    ),
    (
        "device-operations-q4",
        "device-operations",
        3,
        (
            _kql(
                "telemetry_hot",
                "Signals driven by the lining-degradation scenario.",
                statement="telemetry_hot | where scenario_id == 'degrading-furnace' and signal_code in ('local_heat_flux','hearth_refractory_estimate','hearth_shell_temperature') | project signal_code, value, event_ts",
                rows=3,
                elapsed_ms=280,
            ),
        ),
    ),
    # -- dashboards --------------------------------------------------------
    (
        "dashboards-q1",
        "dashboards",
        0,
        (
            _kql(
                "mv_alarm_current",
                "Open alarms the handover collection triages.",
                statement="mv_alarm_current | where state !in ('MITIGATED','CLOSED') and plant_id == 'NS-DEMO-LUX-01' | project alarm_id, severity, state, alarm_type",
                rows=16,
                elapsed_ms=230,
            ),
        ),
    ),
    (
        "dashboards-q2",
        "dashboards",
        1,
        (
            _gold(
                "fact_ai_decision_audit",
                "domain, complete_audit_flag, model_version.",
                statement="SELECT audit_id, domain, complete_audit_flag, model_version FROM fact_ai_decision_audit WHERE recorded_date = '2026-07-25'",
                rows=5,
                elapsed_ms=840,
            ),
            _gold(
                "fact_emissions_daily",
                "Reported emissions behind the evidence pack.",
                statement="SELECT total_co2e_t, ets_exposure_eur FROM fact_emissions_daily WHERE plant_id = 'NS-DEMO-LUX-01' AND date_key = '2026-07-25'",
                rows=1,
                elapsed_ms=690,
            ),
        ),
    ),
    (
        "dashboards-q3",
        "dashboards",
        2,
        (
            _gold(
                "fact_ai_decision_audit",
                "Domains each collection investigates.",
                statement="SELECT domain, entity_id, correlation_id FROM fact_ai_decision_audit WHERE recorded_date = '2026-07-25'",
                rows=5,
                elapsed_ms=800,
            ),
        ),
    ),
    (
        "dashboards-q4",
        "dashboards",
        3,
        (
            _gold(
                "fact_furnace_rul",
                "risk_score and rul_days_p50 behind the investigation.",
                statement="SELECT TOP 1 risk_score, rul_days_p50 FROM fact_furnace_rul WHERE asset_id = 'LUX-BF-01' AND scored_date = '2026-07-25' ORDER BY scored_at DESC",
                rows=1,
                elapsed_ms=780,
            ),
            _kql(
                "telemetry_hot",
                "Thermal signature backing the same investigation.",
                statement="telemetry_hot | where asset_id == 'LUX-BF-01' and signal_code == 'hearth_shell_temperature' and event_ts > ago(24h) | summarize arg_max(event_ts, value) by sensor_id",
                rows=5,
                elapsed_ms=350,
            ),
        ),
    ),
)


_PACKS: Final[dict[str, dict[str, str]]] = {
    "en": _EN,
    "fr": _FR,
    "de": _DE,
    "nl": _NL,
    "es": _ES,
}


_SCREEN_CARDS: Final[tuple[FabricCard, ...]] = tuple(
    FabricCard(
        card_id=card_id,
        section=section,
        index=index,
        datasets=datasets,
        body=bodies(card_id, _PACKS),
    )
    for card_id, section, index, datasets in _SPECS
)

# Screen chips first, then the per-persona questions the chat panel offers
# before any screen is chosen. Both packs are served by the same agent path.
CARDS: Final[tuple[FabricCard, ...]] = _SCREEN_CARDS + PERSONA_CARDS
