"""Card metadata for the Copilot's per-persona predefined questions.

Pure data module: matching lives in
``knowledge_orchestrator.copilot.fabric_answers`` and the prose lives in the
per-language ``fabric_persona_<lang>`` modules.

Why these cards exist
---------------------
The chat panel offers each of the eight personas four questions before any
screen is chosen (``PERSONA_QUESTIONS`` in
``apps/analytics-mfe/src/components/copilot/CopilotPanel.tsx``). They arrive as
free text with no screen attached, so before this pack they fell through to the
glossary and dead-ended on "that is not in my knowledge base yet". Each one is
now answered the way the screen chips are: by the Fabric data agent
``da-novasteelv3``, with the query steps it ran shown above the figures.

Matching is by verbatim prompt because the panel sends the English wording
whatever the UI language is; the answer itself is served in the caller's
language.

Every figure quoted in the bodies is the synthetic value the demo already shows:
the fixture pack behind the screens (``apps/analytics-mfe/src/api/fixtures.ts``),
the device simulator manifest, or the verified July-2026 gold scorecard in
``docs/demo/data-agent-question-script.md``.
"""

from __future__ import annotations

from typing import Final

from .fabric_persona_de import ANSWERS as _DE
from .fabric_persona_en import ANSWERS as _EN
from .fabric_persona_es import ANSWERS as _ES
from .fabric_persona_fr import ANSWERS as _FR
from .fabric_persona_nl import ANSWERS as _NL
from .fabric_sources import FabricCard, FabricDataset, bodies
from .fabric_sources import gold as _gold
from .fabric_sources import graph as _graph
from .fabric_sources import kql as _kql

# card id -> (verbatim prompts, query steps). The prompts are the exact strings
# the chat panel sends, so a wording change in the panel must be mirrored here;
# tests/knowledge/test_copilot_persona_questions.py fails when it is not.
_SPECS: Final[tuple[tuple[str, tuple[str, ...], tuple[FabricDataset, ...]], ...]] = (
    # -- plant-manager -------------------------------------------------------
    (
        "persona-plant-manager-q1",
        ("Which line is furthest behind target today?",),
        (
            _kql(
                "mv_telemetry_1m",
                "Live production-rate trend by Luxembourg asset for 2026-07-25.",
                "mv_telemetry_1m | where signal_code == 'production_rate' and plant_id == 'NS-DEMO-LUX-01' | summarize avg_rate=avg(value_avg) by asset_id",
                6,
                412,
            ),
            _gold(
                "fact_production_shift",
                "Throughput and OEE inputs for the 2026-07-25 Luxembourg shifts.",
                "SELECT line_id, total_tons / NULLIF(runtime_minutes,0) * 60 AS tph, runtime_minutes, planned_minutes, good_tons, total_tons FROM fact_production_shift WHERE shift_date = '2026-07-25' AND plant_id = 'NS-DEMO-LUX-01'",
                3,
                921,
            ),
        ),
    ),
    (
        "persona-plant-manager-q2",
        ("Why did the night shift have lower yield than usual?",),
        (
            _kql(
                "mv_model_latest",
                "Latest quality-model status for Luxembourg coils.",
                "mv_model_latest | where model_version == 'quality-yield-gbm/2.1.0-demo' and plant_id == 'NS-DEMO-LUX-01' | project asset_id, label, quality_risk_score, severity",
                4,
                366,
            ),
            _gold(
                "fact_quality_yield",
                "July-2026 defect counts and high-grade yield for Luxembourg.",
                "SELECT grade_code, defect_count, first_pass_good_tons, attempted_tons FROM fact_quality_yield WHERE plant_id = 'NS-DEMO-LUX-01' AND date_key BETWEEN '2026-07-01' AND '2026-07-29'",
                6,
                1188,
            ),
        ),
    ),
    (
        "persona-plant-manager-q3",
        ("What should I prioritise in this morning\u2019s triage?",),
        (
            _kql(
                "fn_active_alarms",
                "Current open alarms for the Luxembourg site.",
                "fn_active_alarms('NS-DEMO-LUX-01') | project alarm_id, severity, state, asset_id",
                16,
                287,
            ),
            _gold(
                "fact_dispatch_recommendation",
                "Dispatch recommendation REC-DEMO-LUX-240725.",
                "SELECT recommendation_id, expected_cost_avoidance_eur, expected_co2_avoided_t, status FROM fact_dispatch_recommendation WHERE recommendation_id = 'REC-DEMO-LUX-240725'",
                1,
                844,
            ),
            _gold(
                "fact_furnace_rul",
                "Latest BF-01 hearth risk and remaining-life score.",
                "SELECT asset_id, component_id, risk_score, rul_days_p50 FROM fact_furnace_rul WHERE asset_id = 'LUX-BF-01' AND scored_date = '2026-07-25'",
                1,
                1093,
            ),
        ),
    ),
    (
        "persona-plant-manager-q4",
        ("What is the current overall equipment effectiveness (OEE)?",),
        (
            _gold(
                "fact_production_shift",
                "Luxembourg shift KPI roll-up for 2026-07-25.",
                "SELECT line_id, runtime_minutes / NULLIF(planned_minutes,0) AS avail, total_tons / NULLIF(runtime_minutes,0) * 60 AS tph, good_tons, total_tons FROM fact_production_shift WHERE shift_date = '2026-07-25' AND plant_id = 'NS-DEMO-LUX-01'",
                1,
                903,
            ),
            _kql(
                "mv_telemetry_1m",
                "Live production-rate trend behind the shift KPI.",
                "mv_telemetry_1m | where signal_code == 'production_rate' and plant_id == 'NS-DEMO-LUX-01' | summarize avg_rate=avg(value_avg) by bin(event_ts, 15m)",
                16,
                331,
            ),
        ),
    ),
    # -- furnace-operator ----------------------------------------------------
    (
        "persona-furnace-operator-q1",
        ("What is the current thermal profile of BF-01 hearth?",),
        (
            _kql(
                "fn_latest_telemetry",
                "Latest BF-01 shell temperature, heat-flux and cooling readings.",
                "fn_latest_telemetry('NS-DEMO-LUX-01') | where asset_id == 'LUX-BF-01' and signal_code in ('hearth_shell_temperature','local_heat_flux','cooling_water_delta_t','cooling_water_flow')",
                5,
                248,
            ),
            _kql(
                "fn_latest_model_scores",
                "Latest lining-rul-piml score for BF-01.",
                "fn_latest_model_scores('NS-DEMO-LUX-01') | where asset_id == 'LUX-BF-01' and model_version == 'lining-rul-piml/1.3.0-demo'",
                1,
                294,
            ),
        ),
    ),
    (
        "persona-furnace-operator-q2",
        ("Why is the temperature rising at sensor T12-North?",),
        (
            _kql(
                "mv_telemetry_latest_by_signal",
                "Closest live thermal drifts: TC-114 and SECTOR-07 sensors.",
                "mv_telemetry_latest_by_signal | where asset_id == 'LUX-BF-01' and sensor_id in ('TC-114','LUX-BF-01-HERE-H07') | project sensor_id, signal_code, value, quality",
                2,
                321,
            ),
            _kql(
                "mv_model_latest",
                "Latest anomaly scores tied to the BF-01 hearth.",
                "mv_model_latest | where asset_id == 'LUX-BF-01' and model_version == 'lining-rul-piml/1.3.0-demo' | project component_id, risk_score, top_factors",
                2,
                279,
            ),
        ),
    ),
    (
        "persona-furnace-operator-q3",
        ("What tap parameters should I adjust for the next cast?",),
        (
            _gold(
                "fact_knowledge_procedure",
                "Furnace procedures linked to BF-01 and its cooling circuit.",
                "SELECT procedure_id, review_status, version, equipment_id FROM fact_knowledge_procedure WHERE equipment_id IN ('LUX-BF-01','HEARTH-SECTOR-07')",
                2,
                771,
            ),
            _graph(
                "Process-chain path from blast furnace into the downstream steelmaking route.",
                "MATCH p=(a:EquipmentClass {ClassId:'BlastFurnace'})-[:feeds*1..3]->(c:EquipmentClass {ClassId:'ContinuousCaster'}) RETURN p",
                3,
                614,
            ),
            _kql(
                "fn_latest_telemetry",
                "Current BF-01 thermal cues that contextualise the next cast.",
                "fn_latest_telemetry('NS-DEMO-LUX-01') | where asset_id == 'LUX-BF-01' and signal_code in ('local_heat_flux','cooling_water_delta_t','cooling_water_flow')",
                3,
                233,
            ),
        ),
    ),
    (
        "persona-furnace-operator-q4",
        ("How does coke rate affect hearth wear?",),
        (
            _gold(
                "fact_furnace_rul",
                "Latest BF-01 driver weights for hearth wear.",
                "SELECT asset_id, top_factors_json, risk_score FROM fact_furnace_rul WHERE asset_id = 'LUX-BF-01' AND scored_date = '2026-07-25'",
                1,
                1018,
            ),
            _kql(
                "mv_telemetry_1m",
                "Live thermal-load covariates around the hearth.",
                "mv_telemetry_1m | where asset_id == 'LUX-BF-01' and signal_code in ('local_heat_flux','cooling_water_delta_t','cooling_water_flow','pulverized_coal_injection')",
                4,
                347,
            ),
        ),
    ),
    # -- maintenance-engineer ------------------------------------------------
    (
        "persona-maintenance-engineer-q1",
        ("Which assets have the highest failure probability this week?",),
        (
            _gold(
                "fact_furnace_rul",
                "Latest furnace-risk rows within the July-2026 history window.",
                "SELECT asset_id, component_id, risk_score, rul_days_p50 FROM fact_furnace_rul WHERE scored_date BETWEEN '2026-07-19' AND '2026-07-25'",
                3,
                958,
            ),
            _kql(
                "fn_latest_model_scores",
                "Current furnace model scores by asset.",
                "fn_latest_model_scores('') | where model_version == 'lining-rul-piml/1.3.0-demo' | project asset_id, component_id, risk_score, remaining_useful_life_days_p50",
                2,
                271,
            ),
        ),
    ),
    (
        "persona-maintenance-engineer-q2",
        ("Why is the predicted RUL dropping faster than the historical trend?",),
        (
            _gold(
                "fact_furnace_rul",
                "June-to-July alert-history rows for BF-01 and RHF-01.",
                "SELECT asset_id, scored_date, rul_days_p50, risk_score, predicted_failure_date FROM fact_furnace_rul WHERE scored_date BETWEEN '2026-06-01' AND '2026-07-29'",
                9,
                1266,
            ),
            _kql(
                "mv_telemetry_1m",
                "Current BF-01 sector and refractory movement over the last 24 hours.",
                "mv_telemetry_1m | where asset_id == 'LUX-BF-01' and signal_code in ('hearth_shell_temperature','hearth_refractory_estimate') | summarize min_v=min(value_min), max_v=max(value_max) by signal_code",
                2,
                338,
            ),
        ),
    ),
    (
        "persona-maintenance-engineer-q3",
        ("What maintenance should I schedule before the next planned stop?",),
        (
            _gold(
                "fact_furnace_rul",
                "Latest BF-01 forecast row with the reline window.",
                "SELECT asset_id, component_id, risk_score, rul_days_p50, predicted_failure_date FROM fact_furnace_rul WHERE asset_id = 'LUX-BF-01' AND scored_date = '2026-07-25'",
                1,
                874,
            ),
            _gold(
                "fact_knowledge_procedure",
                "Approved and in-review furnace procedures.",
                "SELECT procedure_id, review_status, version FROM fact_knowledge_procedure WHERE equipment_id IN ('LUX-BF-01','HEARTH-SECTOR-07')",
                2,
                744,
            ),
            _kql(
                "fn_active_alarms",
                "Open BF-01 hearth alert tied to the work order.",
                "fn_active_alarms('NS-DEMO-LUX-01') | where asset_id == 'LUX-BF-01' and alarm_id == 'ALERT-HEARTH-SECTOR-07-260725'",
                1,
                214,
            ),
        ),
    ),
    (
        "persona-maintenance-engineer-q4",
        ("What is the difference between P50 and P90 remaining useful life?",),
        (
            _gold(
                "fact_furnace_rul",
                "Latest BF-01 prediction band.",
                "SELECT asset_id, rul_days_p10, rul_days_p50, rul_days_p90, risk_score FROM fact_furnace_rul WHERE asset_id = 'LUX-BF-01' AND scored_date = '2026-07-25'",
                1,
                801,
            ),
            _gold(
                "dim_kpi_target",
                "Programme target for furnace advance-warning days.",
                "SELECT kpi_id, target_value, unit FROM dim_kpi_target WHERE kpi_id = 'KPI-FUR-01'",
                1,
                632,
            ),
        ),
    ),
    # -- energy-manager ------------------------------------------------------
    (
        "persona-energy-manager-q1",
        ("When is the next low-carbon electricity window today?",),
        (
            _kql(
                "mv_telemetry_1m",
                "Live spot-price and grid-carbon windows for 2026-07-25.",
                "mv_telemetry_1m | where plant_id == 'NS-DEMO-LUX-01' and signal_code in ('spot_price','grid_carbon_intensity') | summarize avg_v=avg(value_avg) by signal_code, bin(event_ts, 15m)",
                12,
                401,
            ),
            _gold(
                "fact_dispatch_recommendation",
                "Dispatch move REC-DEMO-LUX-240725 and its low-carbon window.",
                "SELECT recommendation_id, baseline_cost_eur, optimized_cost_eur, expected_co2_avoided_t FROM fact_dispatch_recommendation WHERE recommendation_id = 'REC-DEMO-LUX-240725'",
                1,
                919,
            ),
        ),
    ),
    (
        "persona-energy-manager-q2",
        ("Why did energy intensity spike during the last shift?",),
        (
            _gold(
                "fact_energy_daily",
                "Luxembourg energy cost and intensity for 2026-07-25.",
                "SELECT energy_cost_eur, energy_gj, crude_steel_tons, energy_cost_eur / NULLIF(crude_steel_tons,0) AS eur_per_t FROM fact_energy_daily WHERE date_key = '2026-07-25' AND plant_id = 'NS-DEMO-LUX-01'",
                1,
                882,
            ),
            _kql(
                "mv_telemetry_1m",
                "Spot-price and throughput behaviour across the evening scarcity window.",
                "mv_telemetry_1m | where plant_id == 'NS-DEMO-LUX-01' and signal_code in ('spot_price','production_rate') | where event_ts between(datetime(2026-07-25T17:00:00Z)..datetime(2026-07-25T20:00:00Z))",
                8,
                354,
            ),
        ),
    ),
    (
        "persona-energy-manager-q3",
        ("What load-shift opportunities can save the most this week?",),
        (
            _gold(
                "fact_dispatch_recommendation",
                "Latest dispatch candidate plus July-2026 adoption context.",
                "SELECT recommendation_id, baseline_cost_eur, optimized_cost_eur, expected_cost_avoidance_eur, status FROM fact_dispatch_recommendation WHERE recommendation_date BETWEEN '2026-07-19' AND '2026-07-25'",
                4,
                1134,
            ),
            _kql(
                "mv_telemetry_1m",
                "Near-term spot-price windows behind the dispatch advice.",
                "mv_telemetry_1m | where signal_code == 'spot_price' and plant_id == 'NS-DEMO-LUX-01' | summarize avg_v=avg(value_avg) by bin(event_ts, 15m)",
                16,
                289,
            ),
        ),
    ),
    (
        "persona-energy-manager-q4",
        ("What is the Scope 2 emissions impact of shifting EAF heats to off-peak?",),
        (
            _gold(
                "fact_dispatch_recommendation",
                "Measured CO2 reduction from REC-DEMO-LUX-240725.",
                "SELECT recommendation_id, expected_co2_avoided_t, baseline_cost_eur, optimized_cost_eur FROM fact_dispatch_recommendation WHERE recommendation_id = 'REC-DEMO-LUX-240725'",
                1,
                907,
            ),
            _kql(
                "mv_telemetry_1m",
                "Grid-carbon intensity across off-peak and scarcity slots.",
                "mv_telemetry_1m | where signal_code == 'grid_carbon_intensity' and plant_id == 'NS-DEMO-LUX-01' | summarize avg_v=avg(value_avg) by bin(event_ts, 15m)",
                16,
                318,
            ),
        ),
    ),
    # -- quality-engineer ----------------------------------------------------
    (
        "persona-quality-engineer-q1",
        ("Which coils failed the surface quality check today?",),
        (
            _kql(
                "mv_model_latest",
                "Current Luxembourg quality scores on the live board.",
                "mv_model_latest | where model_version == 'quality-yield-gbm/2.1.0-demo' and plant_id == 'NS-DEMO-LUX-01' | project asset_id, label, quality_risk_score, predicted_first_pass_yield",
                1,
                267,
            ),
            _kql(
                "mv_alarm_current",
                "Quality-drift alert for the failing coil.",
                "mv_alarm_current | where alarm_id == 'ALERT-QUALITY-DRIFT-DP780' | project alarm_id, severity, state, asset_id, observed_value",
                1,
                198,
            ),
        ),
    ),
    (
        "persona-quality-engineer-q2",
        ("Why is the defect rate trending up on Line 3?",),
        (
            _gold(
                "fact_quality_yield",
                "July-2026 defect counts and yield loss breakdown for Luxembourg.",
                "SELECT grade_code, defect_count, rework_tons, downgrade_tons, scrap_tons FROM fact_quality_yield WHERE date_key BETWEEN '2026-07-01' AND '2026-07-29' AND plant_id = 'NS-DEMO-LUX-01'",
                6,
                1217,
            ),
            _kql(
                "mv_alarm_current",
                "Latest quality drift alert for the Luxembourg hot-strip path.",
                "mv_alarm_current | where plant_id == 'NS-DEMO-LUX-01' and alarm_type == 'quality_drift' | project alarm_id, asset_id, severity, state, observed_value",
                1,
                296,
            ),
        ),
    ),
    (
        "persona-quality-engineer-q3",
        ("What process parameters correlate with centreline segregation?",),
        (
            _kql(
                "fn_latest_telemetry",
                "Latest caster variables available for segregation-style triage.",
                "fn_latest_telemetry('NS-DEMO-LUX-01') | where asset_id == 'LUX-CC-01' and signal_code in ('superheat','casting_speed','secondary_cooling_flow')",
                3,
                262,
            ),
            _graph(
                "Supply-chain path from caster to hot-strip mill for the Luxembourg line.",
                "MATCH p=(a:Asset {AssetId:'LUX-CC-01'})-[:supplies*1..3]->(b:Asset {AssetId:'LUX-HSM-01'}) RETURN p",
                3,
                702,
            ),
            _gold(
                "fact_quality_yield",
                "Luxembourg coil-level aggregate quality for the DP780 grade.",
                "SELECT grade_code, first_pass_good_tons, attempted_tons, defect_count, open_ncr_count FROM fact_quality_yield WHERE date_key = '2026-07-25' AND plant_id = 'NS-DEMO-LUX-01'",
                1,
                846,
            ),
        ),
    ),
    (
        "persona-quality-engineer-q4",
        ("What is statistical process control telling us about thickness variation?",),
        (
            _gold(
                "fact_quality_yield",
                "July-2026 aggregate yield and defect context for Luxembourg.",
                "SELECT grade_code, first_pass_good_tons, attempted_tons, defect_count FROM fact_quality_yield WHERE date_key BETWEEN '2026-07-01' AND '2026-07-29' AND plant_id = 'NS-DEMO-LUX-01'",
                1,
                972,
            ),
            _kql(
                "mv_model_latest",
                "Latest quality-model output with coiling-temperature bias context.",
                "mv_model_latest | where model_version == 'quality-yield-gbm/2.1.0-demo' and plant_id == 'NS-DEMO-LUX-01' | project asset_id, label, quality_risk_score, predicted_first_pass_yield, top_factors",
                1,
                281,
            ),
        ),
    ),
    # -- sustainability-officer ---------------------------------------------
    (
        "persona-sustainability-officer-q1",
        ("Are we on track to meet this quarter\u2019s ETS compliance target?",),
        (
            _gold(
                "fact_emissions_daily",
                "Current-day ETS status for Luxembourg on 2026-07-25.",
                "SELECT plant_id, ets_exposure_eur, free_allocation_t, total_co2e_t, crude_steel_tons, total_co2e_t / NULLIF(crude_steel_tons,0) AS co2_intensity FROM fact_emissions_daily WHERE date_key = '2026-07-25' AND plant_id = 'NS-DEMO-LUX-01'",
                1,
                933,
            ),
            _gold(
                "dim_kpi_target",
                "Programme CO2-intensity target used as the benchmark.",
                "SELECT kpi_id, baseline_value, target_value FROM dim_kpi_target WHERE kpi_id = 'KPI-CO2-01'",
                1,
                684,
            ),
            _kql(
                "fn_active_alarms",
                "Current ETS-related warning state.",
                "fn_active_alarms('NS-DEMO-LUX-01') | where alarm_id == 'ALERT-ETS-ALLOWANCE-Q3' | project alarm_id, severity, state",
                1,
                206,
            ),
        ),
    ),
    (
        "persona-sustainability-officer-q2",
        ("What would a 10% production increase mean for our CBAM exposure?",),
        (
            _gold(
                "fact_emissions_daily",
                "Current-day emissions intensity and ETS exposure for Luxembourg.",
                "SELECT plant_id, crude_steel_tons, scope1_co2e_t, scope2_co2e_t, ets_exposure_eur, ets_allowance_price_eur_per_t FROM fact_emissions_daily WHERE date_key = '2026-07-25' AND plant_id = 'NS-DEMO-LUX-01'",
                1,
                1042,
            ),
            _gold(
                "dim_kpi_target",
                "Programme carbon-intensity benchmark for scaling scenarios.",
                "SELECT kpi_id, target_value, baseline_value FROM dim_kpi_target WHERE kpi_id = 'KPI-CO2-01'",
                1,
                618,
            ),
        ),
    ),
    (
        "persona-sustainability-officer-q3",
        ("What is our current carbon intensity per tonne of steel?",),
        (
            _gold(
                "fact_emissions_daily",
                "Current-day Luxembourg CO2 intensity.",
                "SELECT plant_id, total_co2e_t, crude_steel_tons, total_co2e_t / NULLIF(crude_steel_tons,0) AS co2_intensity FROM fact_emissions_daily WHERE date_key = '2026-07-25' AND plant_id = 'NS-DEMO-LUX-01'",
                1,
                856,
            ),
            _gold(
                "fact_emissions_daily",
                "Closed-book July-2026 CO2 intensity benchmark.",
                "SELECT SUM(total_co2e_t) AS total_co2e, SUM(crude_steel_tons) AS crude_steel FROM fact_emissions_daily WHERE date_key BETWEEN '2026-07-01' AND '2026-07-29'",
                1,
                1106,
            ),
        ),
    ),
    (
        "persona-sustainability-officer-q4",
        ("How does our emissions performance compare to the benchmark?",),
        (
            _gold(
                "fact_emissions_daily",
                "Current-day and July-2026 CO2 intensity comparison points.",
                "SELECT date_key, total_co2e_t, crude_steel_tons, ets_exposure_eur FROM fact_emissions_daily WHERE date_key IN ('2026-07-25','2026-07-29') AND plant_id = 'NS-DEMO-LUX-01'",
                2,
                932,
            ),
            _gold(
                "dim_kpi_target",
                "Benchmark and baseline for KPI-CO2-01.",
                "SELECT kpi_id, baseline_value, target_value FROM dim_kpi_target WHERE kpi_id = 'KPI-CO2-01'",
                1,
                691,
            ),
        ),
    ),
    # -- knowledge-engineer --------------------------------------------------
    (
        "persona-knowledge-engineer-q1",
        ("Which glossary terms are most frequently looked up?",),
        (
            _gold(
                "fact_knowledge_usage",
                "Knowledge-domain query activity and citation signals.",
                "SELECT topic_id, COUNT(*) AS query_count, SUM(CASE WHEN cited_answer_flag THEN 1 ELSE 0 END) AS cited FROM fact_knowledge_usage WHERE query_date BETWEEN '2026-07-01' AND '2026-07-29' GROUP BY topic_id",
                5,
                972,
            ),
            _gold(
                "fact_knowledge_procedure",
                "Procedure status by equipment for the captured knowledge base.",
                "SELECT procedure_id, review_status, topic_id, equipment_id FROM fact_knowledge_procedure",
                3,
                647,
            ),
        ),
    ),
    (
        "persona-knowledge-engineer-q2",
        ("How does the Copilot decide which sources to cite?",),
        (
            _gold(
                "fact_ai_decision_audit",
                "Recent decision-audit rows with model and completion status.",
                "SELECT audit_id, domain, model_version, complete_audit_flag FROM fact_ai_decision_audit WHERE recorded_date BETWEEN '2026-07-01' AND '2026-07-29'",
                5,
                914,
            ),
            _gold(
                "fact_knowledge_procedure",
                "Procedure review state and citation readiness.",
                "SELECT procedure_id, review_status, approved_flag, source_citation_count FROM fact_knowledge_procedure",
                3,
                702,
            ),
        ),
    ),
    (
        "persona-knowledge-engineer-q3",
        ("What is the knowledge grounding architecture of this platform?",),
        (
            _gold(
                "fact_knowledge_procedure",
                "Procedure states across the governed knowledge corpus.",
                "SELECT procedure_id, review_status, version, approved_flag, equipment_id FROM fact_knowledge_procedure",
                3,
                761,
            ),
            _gold(
                "fact_ai_decision_audit",
                "Audit completeness across the grounded decision domains.",
                "SELECT audit_id, domain, complete_audit_flag, correlation_id FROM fact_ai_decision_audit WHERE recorded_date BETWEEN '2026-07-01' AND '2026-07-29'",
                5,
                889,
            ),
            _graph(
                "Ontology path showing operational lineage available for grounding.",
                "MATCH p=(a:Asset {AssetId:'LUX-BF-01'})-[:supplies*1..4]->(b:Asset {AssetId:'LUX-HSM-01'}) RETURN p",
                5,
                655,
            ),
        ),
    ),
    (
        "persona-knowledge-engineer-q4",
        ("What are the guardrails against prompt injection?",),
        (
            _gold(
                "fact_ai_decision_audit",
                "Audit completeness and human decision points across AI domains.",
                "SELECT audit_id, domain, recommendation_status, complete_audit_flag, human_decision_at FROM fact_ai_decision_audit WHERE recorded_date BETWEEN '2026-07-01' AND '2026-07-29'",
                5,
                947,
            ),
            _gold(
                "fact_knowledge_procedure",
                "Approved versus non-approved procedures in the governed corpus.",
                "SELECT procedure_id, review_status, approved_flag FROM fact_knowledge_procedure",
                3,
                689,
            ),
        ),
    ),
    # -- ot-systems-engineer -------------------------------------------------
    (
        "persona-ot-systems-engineer-q1",
        ("Which OT data feeds are currently delayed or missing?",),
        (
            _kql(
                "fn_data_freshness",
                "Current freshness across all live OT streams.",
                "fn_data_freshness('') | project stream, last_event",
                91,
                418,
            ),
            _kql(
                "fn_quarantine_rate",
                "Current 15-minute quarantine rate.",
                "fn_quarantine_rate(15m) | project plant_id, quarantine_reason, quarantine_id",
                1,
                187,
            ),
            _gold(
                "pipeline_run_reconciliation",
                "Latest bronze-to-gold reconciliation checks.",
                "SELECT run_id, dataset, status, bronze_rows, silver_rows, quarantine_rows FROM pipeline_run_reconciliation WHERE run_date BETWEEN '2026-07-25' AND '2026-07-29'",
                3,
                978,
            ),
        ),
    ),
    (
        "persona-ot-systems-engineer-q2",
        ("What is the polling latency for the furnace sensor network?",),
        (
            _kql(
                "fn_data_freshness",
                "Current cadence and freshness for the BF-01 furnace signals.",
                "fn_data_freshness('NS-DEMO-LUX-01') | project stream, last_event",
                3,
                236,
            ),
            _kql(
                "mv_gateway_latest",
                "Latest Luxembourg gateway lag and queue state.",
                "mv_gateway_latest | where plant_id == 'NS-DEMO-LUX-01' | project gateway_id, event_time_lag_ms, queue_depth",
                1,
                201,
            ),
        ),
    ),
    (
        "persona-ot-systems-engineer-q3",
        ("How do I configure a new PLC tag for ingestion?",),
        (
            _kql(
                "ingest_quarantine_hot",
                "Recent quarantine rows that show envelope and schema failures.",
                "ingest_quarantine_hot | where event_ts > datetime(2026-07-25T00:00:00Z) | project schema_name, quarantine_reason, source_id",
                2,
                264,
            ),
            _gold(
                "dq_run_result",
                "Recent contract checks on telemetry envelopes.",
                "SELECT rule_id, status, failed_rows, table_name FROM dq_run_result WHERE run_date BETWEEN '2026-07-25' AND '2026-07-29' AND table_name = 'telemetry_hot'",
                4,
                842,
            ),
        ),
    ),
    (
        "persona-ot-systems-engineer-q4",
        ("What communication protocol does the thermal sensor array use?",),
        (
            _kql(
                "fn_gateway_status",
                "Current gateway status and health for the four plants.",
                "fn_gateway_status('') | project plant_id, gateway_id, connection_state, queue_depth",
                4,
                193,
            ),
            _kql(
                "mv_telemetry_latest_by_signal",
                "Sample-period and source metadata for thermal sensors.",
                "mv_telemetry_latest_by_signal | where asset_id == 'LUX-BF-01' and signal_code in ('hearth_shell_temperature','local_heat_flux') | project sensor_id, signal_code, sample_period_ms, source_id",
                4,
                734,
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

PERSONA_CARDS: Final[tuple[FabricCard, ...]] = tuple(
    FabricCard(
        card_id=card_id,
        prompts=prompts,
        datasets=datasets,
        body=bodies(card_id, _PACKS),
    )
    for card_id, prompts, datasets in _SPECS
)
