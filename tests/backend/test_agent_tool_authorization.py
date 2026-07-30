"""Tests for the authorization boundary around the agent function tools.

This is the part of the multi-agent design that is genuinely load-bearing. A hosted
agent runs as the service's managed identity, so when Foundry emits a
``function_call`` there is nothing in it that says who asked. If the tool trusted its
arguments, any operator could ask the assistant for any plant's figures and get them.

Every test below is a variant of the same question: does the tool re-apply the
caller's roles and plant scope, or does it believe the model?
"""

from __future__ import annotations

import pytest

from bff_api.agent_tools import (
    DEFAULT_HORIZON_HOURS,
    DEFAULT_MAX_SHIFT_MINUTES,
    MAX_HORIZON_HOURS,
    ToolRefused,
    build_registry,
)
from bff_api.auth import UserContext
from bff_api.main import create_app

ALL_ROLES = frozenset(
    {
        "Operator.Read",
        "ProcessEngineer.Contribute",
        "EnergyPlanner.Approve",
        "MaintenanceEngineer.Read",
        "Compliance.Auditor",
    }
)


@pytest.fixture(scope="module")
def services():
    return create_app().state.services


@pytest.fixture(scope="module")
def demo_site(services) -> str:
    return services.repository.site


def _user(roles=ALL_ROLES, plants=("NS-DEMO-LUX-01",)) -> UserContext:
    return UserContext(
        user_id="u-1",
        display_name="Test User",
        roles=frozenset(roles),
        plant_scope=frozenset(plants),
    )


def _registry(services, user):
    return build_registry(user=user, services=services, correlation_id="corr-1")


# --- plant scope -------------------------------------------------------------


def test_a_site_outside_the_callers_scope_is_refused(services, demo_site):
    """The model may propose a site. Only the BFF decides whether the caller may
    have it."""
    registry = _registry(services, _user(plants=("NS-DEMO-OTHER-01",)))
    with pytest.raises(ToolRefused) as excinfo:
        registry.execute(
            "simulate_energy_dispatch",
            {
                "site": demo_site,
                "horizonHours": 24,
                "scenario": "baseline",
                "maxShiftMinutes": 120,
            },
        )
    assert demo_site in str(excinfo.value)


def test_the_refusal_names_the_plants_the_caller_does_have(services, demo_site):
    """A refusal that does not say what the operator *can* ask about turns into a
    support ticket."""
    registry = _registry(services, _user(plants=("NS-DEMO-OTHER-01",)))
    with pytest.raises(ToolRefused) as excinfo:
        registry.execute("simulate_energy_dispatch", {"site": demo_site})
    assert "NS-DEMO-OTHER-01" in str(excinfo.value)


def test_a_single_plant_scope_supplies_the_default_site(services, demo_site):
    registry = _registry(services, _user(plants=(demo_site,)))
    result = registry.execute("simulate_energy_dispatch", {})
    assert result["site"] == demo_site


def test_a_multi_plant_scope_refuses_rather_than_guessing(services, demo_site):
    """Silently picking one of an operator's plants is exactly the kind of unstated
    assumption that makes an operational answer untrustworthy."""
    registry = _registry(services, _user(plants=(demo_site, "NS-DEMO-OTHER-01")))
    with pytest.raises(ToolRefused) as excinfo:
        registry.execute("simulate_energy_dispatch", {})
    assert "which plant" in str(excinfo.value).lower()


# --- roles -------------------------------------------------------------------


def test_dispatch_requires_the_same_role_as_its_rest_route(services, demo_site):
    """Asking through the assistant must not be a way around the role that guards
    POST /v1/energy/schedules:simulate."""
    registry = _registry(
        services, _user(roles={"Operator.Read"}, plants=(demo_site,))
    )
    with pytest.raises(ToolRefused) as excinfo:
        registry.execute("simulate_energy_dispatch", {"site": demo_site})
    assert "EnergyPlanner.Approve" in str(excinfo.value)


def test_rul_forecast_requires_a_maintenance_or_operator_role(services):
    registry = _registry(services, _user(roles={"Compliance.Auditor"}))
    with pytest.raises(ToolRefused) as excinfo:
        registry.execute("lining_rul_forecast", {"assetId": "anything"})
    assert "MaintenanceEngineer.Read" in str(excinfo.value)


# --- asset scope -------------------------------------------------------------


def test_an_asset_outside_the_callers_scope_is_refused(services):
    """The asset's plant is resolved from the repository, not parsed out of the id
    the model supplied, so naming a furnace is not a way to read it."""
    asset_id = services.repository.furnaces()[0]["assetId"]
    site = services.repository.asset_site(asset_id)
    registry = _registry(services, _user(plants=("NS-DEMO-OTHER-01",)))
    with pytest.raises(ToolRefused):
        registry.execute("lining_rul_forecast", {"assetId": asset_id})
    assert site != "NS-DEMO-OTHER-01"


def test_an_unknown_asset_is_refused_rather_than_invented(services):
    registry = _registry(services, _user())
    with pytest.raises(ToolRefused) as excinfo:
        registry.execute("lining_rul_forecast", {"assetId": "NOT-A-FURNACE"})
    assert "not found" in str(excinfo.value).lower()


def test_a_missing_asset_id_is_refused(services):
    registry = _registry(services, _user())
    with pytest.raises(ToolRefused):
        registry.execute("lining_rul_forecast", {"assetId": "  "})


# --- happy paths and payload shape -------------------------------------------


def test_an_authorized_dispatch_returns_a_proposal(services, demo_site):
    """ADR-007: the agent may propose, never decide. The status is part of the tool
    payload so the model cannot report the result as a committed change."""
    registry = _registry(services, _user(plants=(demo_site,)))
    result = registry.execute(
        "simulate_energy_dispatch",
        {
            "site": demo_site,
            "horizonHours": 12,
            "scenario": "baseline",
            "maxShiftMinutes": 60,
        },
    )
    assert result["status"] == "PROPOSAL_PENDING_HUMAN_APPROVAL"
    assert result["site"] == demo_site
    assert result["horizonHours"] == 12


def test_a_dispatch_result_carries_its_provenance(services, demo_site):
    """A number the operator cannot trace back to an audit record is not usable in
    an industrial setting, so the model is given both identifiers to quote."""
    registry = _registry(services, _user(plants=(demo_site,)))
    result = registry.execute("simulate_energy_dispatch", {"site": demo_site})
    assert result["modelVersion"]
    assert result["auditRef"]
    assert result["recommendationId"]


def test_the_dispatch_payload_omits_the_full_batch_schedule(services, demo_site):
    """Handing the model every batch row wastes context and invites it to re-derive
    the schedule in prose, which ADR-006 says is not its job."""
    registry = _registry(services, _user(plants=(demo_site,)))
    result = registry.execute("simulate_energy_dispatch", {"site": demo_site})
    assert "batches" not in result
    assert "schedule" not in result


def test_an_authorized_forecast_reports_its_confidence_not_just_a_number(services):
    """The agent's instructions forbid quoting a point estimate on its own, so the
    tool has to hand it the confidence and risk level to quote alongside."""
    asset_id = services.repository.furnaces()[0]["assetId"]
    site = services.repository.asset_site(asset_id)
    registry = _registry(services, _user(plants=(site,)))
    result = registry.execute("lining_rul_forecast", {"assetId": asset_id})
    assert result["assetId"] == asset_id
    assert result["site"] == site
    assert result["modelVersion"]
    assert result["remainingUsefulLife"] is not None
    assert result["confidence"] is not None
    assert result["riskLevel"]
    assert result["status"] == "FORECAST_FOR_HUMAN_DECISION"


def test_a_forecast_carries_at_most_three_drivers(services):
    """Feature attributions explain the number, but the full list is model detail
    that would only pad the model's context."""
    asset_id = services.repository.furnaces()[0]["assetId"]
    site = services.repository.asset_site(asset_id)
    registry = _registry(services, _user(plants=(site,)))
    result = registry.execute("lining_rul_forecast", {"assetId": asset_id})
    assert len(result["drivers"]) <= 3
    assert "featureSnapshot" not in result


# --- argument hardening ------------------------------------------------------


def test_an_absurd_horizon_is_clamped_not_honoured(services, demo_site):
    """A model can emit any integer. The optimizer should not spend real CPU on a
    horizon nobody asked for."""
    registry = _registry(services, _user(plants=(demo_site,)))
    result = registry.execute(
        "simulate_energy_dispatch", {"site": demo_site, "horizonHours": 10_000}
    )
    assert result["horizonHours"] == MAX_HORIZON_HOURS


def test_a_non_numeric_horizon_falls_back_to_the_default(services, demo_site):
    registry = _registry(services, _user(plants=(demo_site,)))
    result = registry.execute(
        "simulate_energy_dispatch", {"site": demo_site, "horizonHours": "soon"}
    )
    assert result["horizonHours"] == DEFAULT_HORIZON_HOURS


def test_omitted_constraints_fall_back_to_the_stated_defaults(services, demo_site):
    """Strict tool schemas cannot express optional properties, so the agent is told
    to send these explicitly. This is the backstop for when it does not."""
    registry = _registry(services, _user(plants=(demo_site,)))
    result = registry.execute("simulate_energy_dispatch", {"site": demo_site})
    assert result["horizonHours"] == DEFAULT_HORIZON_HOURS
    assert result["maxShiftMinutes"] == DEFAULT_MAX_SHIFT_MINUTES


def test_registries_are_not_shared_between_callers(services, demo_site):
    """Each registry closes over one caller's scope. Reusing one across callers
    would let a tool answer with someone else's plants."""
    permitted = _registry(services, _user(plants=(demo_site,)))
    denied = _registry(services, _user(plants=("NS-DEMO-OTHER-01",)))

    assert permitted.execute("simulate_energy_dispatch", {"site": demo_site})
    with pytest.raises(ToolRefused):
        denied.execute("simulate_energy_dispatch", {"site": demo_site})


def test_the_registry_exposes_exactly_the_catalogued_tools(services):
    registry = _registry(services, _user())
    assert sorted(registry.implementations) == [
        "lining_rul_forecast",
        "simulate_energy_dispatch",
    ]
