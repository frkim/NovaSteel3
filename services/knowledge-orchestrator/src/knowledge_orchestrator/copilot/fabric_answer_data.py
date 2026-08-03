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

from dataclasses import dataclass
from typing import Final

from .fabric_answers_de import ANSWERS as _DE
from .fabric_answers_en import ANSWERS as _EN
from .fabric_answers_es import ANSWERS as _ES
from .fabric_answers_fr import ANSWERS as _FR
from .fabric_answers_nl import ANSWERS as _NL

WORKSPACE: Final[str] = "NovaSteelV3-Demo"
LAKEHOUSE: Final[str] = "lh_novasteelv3_core"
KQL_DATABASE: Final[str] = "kql-ns-operations"
ONTOLOGY: Final[str] = "onto_novasteelv3"
DATA_AGENT: Final[str] = "da-novasteelv3"


@dataclass(frozen=True)
class FabricDataset:
    """One Fabric artefact cited as the origin of an answer's figures."""

    source_id: str
    title: str
    snippet: str


@dataclass(frozen=True)
class FabricCard:
    """One predefined question and the answer the platform serves for it."""

    card_id: str
    section: str
    index: int
    datasets: tuple[FabricDataset, ...]
    body: dict[str, str]


def _gold(table: str, snippet: str) -> FabricDataset:
    return FabricDataset(
        source_id=f"fabric:{LAKEHOUSE}.{table}",
        title=f"{LAKEHOUSE}.{table}",
        snippet=snippet,
    )


def _kql(table: str, snippet: str) -> FabricDataset:
    return FabricDataset(
        source_id=f"fabric:{KQL_DATABASE}.{table}",
        title=f"{KQL_DATABASE}.{table}",
        snippet=snippet,
    )


def _graph(snippet: str) -> FabricDataset:
    return FabricDataset(
        source_id=f"fabric:{ONTOLOGY}",
        title=f"{ONTOLOGY} (GQL)",
        snippet=snippet,
    )


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
            _kql("alarm_event", "Open alarms by severity for the selected site."),
            _gold("fact_furnace_rul", "rul_days_p50, risk_score, alert_issued_at for LUX-BF-01."),
        ),
    ),
    (
        "command-center-q2",
        "command-center",
        1,
        (
            _kql("alarm_event", "Highest-severity open alarm per domain."),
            _gold(
                "fact_dispatch_recommendation",
                "expected_cost_avoidance_eur, status for REC-DEMO-LUX-240725.",
            ),
            _gold("fact_emissions_daily", "ets_exposure_eur, free_allocation_t."),
        ),
    ),
    (
        "command-center-q3",
        "command-center",
        2,
        (
            _kql("alarm_event", "Alarms raised or acknowledged since the previous handover."),
            _gold("fact_ai_decision_audit", "domain, recommendation_status, human_decision_at."),
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
            ),
            _gold("fact_furnace_rul", "risk_score, predicted_failure_date, unplanned_outage_flag."),
        ),
    ),
    # -- operations --------------------------------------------------------
    (
        "operations-q1",
        "operations",
        0,
        (
            _kql("telemetry", "production_rate for the site, current shift."),
            _gold("fact_production_shift", "throughput and OEE against shift plan."),
        ),
    ),
    (
        "operations-q2",
        "operations",
        1,
        (
            _kql("telemetry", "production_rate per asset, last 24 h."),
            _graph("Asset -[supplies]-> Asset genealogy for the Luxembourg line."),
        ),
    ),
    (
        "operations-q3",
        "operations",
        2,
        (
            _kql("alarm_event", "Open and acknowledged alarms for the shift window."),
            _gold("fact_ai_decision_audit", "Decisions recorded during the shift."),
        ),
    ),
    (
        "operations-q4",
        "operations",
        4,
        (
            _kql("alarm_event", "Severity, status and confidence of open alarms."),
            _gold("fact_furnace_rul", "risk_score and rul_days_p50 for the alerting asset."),
        ),
    ),
    # -- furnace-health ----------------------------------------------------
    (
        "furnace-health-q1",
        "furnace-health",
        0,
        (
            _kql(
                "telemetry",
                "hearth_shell_temperature, local_heat_flux, cooling_water_* for LUX-BF-01.",
            ),
            _kql("model_inference", "lining-rul-piml/1.3.0-demo feature contributions."),
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
            ),
            _kql("telemetry", "hearth_refractory_estimate for HEARTH-SECTOR-07."),
        ),
    ),
    (
        "furnace-health-q3",
        "furnace-health",
        2,
        (
            _gold("fact_furnace_rul", "top_factors_json for the latest LUX-BF-01 score."),
            _kql("telemetry", "6 h slopes on the hearth thermal signature."),
        ),
    ),
    (
        "furnace-health-q4",
        "furnace-health",
        4,
        (
            _gold("fact_furnace_rul", "risk_score, predicted_failure_date, model_version."),
            _gold("fact_knowledge_procedure", "Approved procedures linked to furnace equipment."),
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
            ),
            _kql("energy_interval", "Day-ahead price curve, 96 quarter-hour slots."),
        ),
    ),
    (
        "energy-optimization-q2",
        "energy-optimization",
        1,
        (
            _kql("energy_interval", "priceEurMwh per slot, evening scarcity window."),
            _gold("fact_energy_daily", "energy_cost_eur against baseline_cost_eur."),
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
            ),
        ),
    ),
    (
        "energy-optimization-q4",
        "energy-optimization",
        4,
        (
            _gold("fact_dispatch_recommendation", "expected_co2_avoided_t, status."),
            _kql("energy_interval", "grid_carbon_intensity per slot."),
        ),
    ),
    # -- quality -----------------------------------------------------------
    (
        "quality-q1",
        "quality",
        0,
        (
            _kql("quality_measurement", "Batch risk score and status, current heats."),
            _gold("fact_quality_yield", "high_grade_flag, first_pass_good_tons, defect_count."),
        ),
    ),
    (
        "quality-q2",
        "quality",
        1,
        (
            _kql("quality_measurement", "Control-chart series, last 20 subgroups."),
            _gold("fact_quality_yield", "defect_count and loss breakdown, 30-day window."),
        ),
    ),
    (
        "quality-q3",
        "quality",
        2,
        (
            _kql("heat_batch", "Genealogy envelope from source heat to shipped coil."),
            _graph("Asset -[supplies]-> Asset path behind the affected coil."),
        ),
    ),
    (
        "quality-q4",
        "quality",
        4,
        (
            _kql("model_inference", "quality-yield-gbm/2.1.0-demo bounded what-if."),
            _gold("fact_quality_yield", "first_pass_good_tons / attempted_tons against KPI-QUA-01."),
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
            ),
            _gold("dim_kpi_target", "KPI-CO2-01 baseline and target."),
        ),
    ),
    (
        "sustainability-compliance-q2",
        "sustainability-compliance",
        1,
        (
            _gold("fact_emissions_daily", "Monthly allowance consumption trend."),
            _gold("dim_kpi_target", "KPI-CO2-01 direction and target."),
        ),
    ),
    (
        "sustainability-compliance-q3",
        "sustainability-compliance",
        2,
        (
            _gold("fact_emissions_daily", "scope1_co2e_t, scope2_co2e_t, crude_steel_tons."),
            _kql("energy_interval", "consumption and grid_carbon_intensity per interval."),
        ),
    ),
    (
        "sustainability-compliance-q4",
        "sustainability-compliance",
        4,
        (
            _gold("fact_dispatch_recommendation", "expected_co2_avoided_t per accepted dispatch."),
            _gold("fact_emissions_daily", "total_co2e_t and ets_exposure_eur."),
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
            ),
        ),
    ),
    (
        "knowledge-hub-q2",
        "knowledge-hub",
        1,
        (
            _gold("fact_knowledge_usage", "Coverage and lookup counts per knowledge domain."),
            _gold("fact_knowledge_procedure", "Domains with no approved procedure."),
        ),
    ),
    (
        "knowledge-hub-q3",
        "knowledge-hub",
        2,
        (
            _gold("fact_knowledge_procedure", "review_status, published_date, procedure_id."),
        ),
    ),
    (
        "knowledge-hub-q4",
        "knowledge-hub",
        4,
        (
            _gold("fact_knowledge_procedure", "Approved hearth procedure and its citations."),
            _kql("operator_knowledge", "Consent-bound interview transcript segments."),
        ),
    ),
    # -- executive-overview ------------------------------------------------
    (
        "executive-overview-q1",
        "executive-overview",
        0,
        (
            _gold("dim_kpi_target", "kpi_id, baseline_value, target_value, target_direction."),
            _gold("fact_energy_daily", "energy_gj / crude_steel_tons, July 2026."),
            _gold("fact_quality_yield", "high-grade first-pass yield, July 2026."),
        ),
    ),
    (
        "executive-overview-q2",
        "executive-overview",
        1,
        (
            _gold("fact_energy_daily", "Energy intensity by plant_id."),
            _gold("fact_emissions_daily", "CO2 intensity by plant_id."),
            _kql("alarm_event", "Open alarms per site."),
        ),
    ),
    (
        "executive-overview-q3",
        "executive-overview",
        2,
        (
            _gold("dim_kpi_target", "Programme targets, stated as targets."),
            _gold("fact_ai_decision_audit", "complete_audit_flag across domains."),
        ),
    ),
    (
        "executive-overview-q4",
        "executive-overview",
        4,
        (
            _gold("dim_kpi_target", "Pilot targets."),
            _gold("fact_dispatch_recommendation", "realized_cost_avoidance_eur, measured."),
        ),
    ),
    # -- platform-ops ------------------------------------------------------
    (
        "platform-ops-q1",
        "platform-ops",
        0,
        (
            _kql("gateway_health", "Capacity lifecycle state and transitions."),
        ),
    ),
    (
        "platform-ops-q2",
        "platform-ops",
        1,
        (
            _kql("gateway_health", "Pipeline run status and duration, latest five runs."),
        ),
    ),
    (
        "platform-ops-q3",
        "platform-ops",
        2,
        (
            _kql("gateway_health", "Capacity-unit consumption and cost telemetry."),
        ),
    ),
    (
        "platform-ops-q4",
        "platform-ops",
        4,
        (
            _kql("gateway_health", "In-flight pipeline runs and capacity state."),
        ),
    ),
    # -- device-operations -------------------------------------------------
    (
        "device-operations-q1",
        "device-operations",
        0,
        (
            _kql("gateway_health", "Device state, uptime and last-seen per gateway."),
            _kql("telemetry", "Signal freshness per device."),
        ),
    ),
    (
        "device-operations-q2",
        "device-operations",
        1,
        (
            _kql("gateway_health", "Health-score inputs: uptime, alarms, staleness."),
        ),
    ),
    (
        "device-operations-q3",
        "device-operations",
        2,
        (
            _kql("telemetry", "Last event timestamp per signal against its emission period."),
            _kql("quarantine", "Rejected or late envelopes."),
        ),
    ),
    (
        "device-operations-q4",
        "device-operations",
        3,
        (
            _kql("telemetry", "Signals driven by the lining-degradation scenario."),
        ),
    ),
    # -- dashboards --------------------------------------------------------
    (
        "dashboards-q1",
        "dashboards",
        0,
        (
            _kql("alarm_event", "Open alarms the handover collection triages."),
        ),
    ),
    (
        "dashboards-q2",
        "dashboards",
        1,
        (
            _gold("fact_ai_decision_audit", "domain, complete_audit_flag, model_version."),
            _gold("fact_emissions_daily", "Reported emissions behind the evidence pack."),
        ),
    ),
    (
        "dashboards-q3",
        "dashboards",
        2,
        (
            _gold("fact_ai_decision_audit", "Domains each collection investigates."),
        ),
    ),
    (
        "dashboards-q4",
        "dashboards",
        3,
        (
            _gold("fact_furnace_rul", "risk_score and rul_days_p50 behind the investigation."),
            _kql("telemetry", "Thermal signature backing the same investigation."),
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


def _bodies(card_id: str) -> dict[str, str]:
    """Collect every translation that exists for one card."""
    return {
        language: pack[card_id]
        for language, pack in _PACKS.items()
        if card_id in pack and pack[card_id].strip()
    }


CARDS: Final[tuple[FabricCard, ...]] = tuple(
    FabricCard(
        card_id=card_id,
        section=section,
        index=index,
        datasets=datasets,
        body=_bodies(card_id),
    )
    for card_id, section, index, datasets in _SPECS
)
