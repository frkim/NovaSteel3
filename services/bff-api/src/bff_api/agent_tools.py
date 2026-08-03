"""Implementations for the agent function tools, bound to one caller.

The schemas live in :mod:`knowledge_orchestrator.agent_tools`, in the service that
talks to Foundry. The bodies live here, in the service that owns identity, because
that is the only place the two things a tool needs are both available: the validated
:class:`~bff_api.auth.UserContext` and the deterministic calculations on
:class:`~bff_api.services.BffServices`.

**The authorization rule.** A hosted agent runs as the service's managed identity,
not as the operator. Nothing about a ``function_call`` carries a caller. So a tool
that trusted its arguments would let any operator ask the assistant for any plant's
figures and get them — the model would happily supply a site it was told about, and
the platform would have no way to know it should not have. Every builder below
therefore closes over the ``UserContext`` established by the HTTP request and applies
exactly the checks the equivalent route applies, ``require_any_role`` and
``require_site``, before touching a calculation. The model may *propose* a site; only
this layer decides whether the caller may have it.

**No new capability.** Each tool is a thin call onto a method the REST API already
exposes, so the agent surface grants no reach the caller did not already have, and
the existing audit record, model version and idempotency behaviour come along
unchanged. A tool that reached past ``BffServices`` into a repository would quietly
become a second, unaudited API.
"""

from __future__ import annotations

import logging
import sys
from math import isfinite
from pathlib import Path
from typing import Any, Mapping

from .auth import UserContext, require_any_role, require_site
from .errors import ApiError

logger = logging.getLogger(__name__)

# Same path injection as `copilot_adapter` and `services`: the orchestrator package
# is a sibling source tree, not an installed wheel, in this repository layout.
_ROOT = Path(__file__).resolve().parents[4]
_KNOWLEDGE_SRC = _ROOT / "services" / "knowledge-orchestrator" / "src"
if str(_KNOWLEDGE_SRC) not in sys.path:
    sys.path.insert(0, str(_KNOWLEDGE_SRC))

from knowledge_orchestrator.agent_tools import (  # noqa: E402
    ToolError,
    ToolRegistry,
)

# Defaults applied when the model omits a value. Strict function-tool schemas cannot
# express optional properties, so the agent is instructed to send these explicitly;
# these are the backstop for when it does not, and they mirror the demo defaults in
# the energy screens rather than being invented here.
DEFAULT_HORIZON_HOURS = 24
DEFAULT_SCENARIO = "baseline"
DEFAULT_MAX_SHIFT_MINUTES = 120

# A model can emit an arbitrarily large integer. The optimizer would either reject it
# or spend real CPU on a horizon nobody asked for, so it is clamped at the boundary.
MAX_HORIZON_HOURS = 72
MAX_SHIFT_MINUTES_CEILING = 480


class ToolRefused(ToolError):
    """A tool call was refused for authorization or validation reasons.

    A subclass of the orchestrator's ``ToolError`` so the run loop treats it as an
    expected outcome — logged as a warning and handed back to the model — rather
    than as a fault worth a stack trace. It never becomes an HTTP status: the
    operator sees "I cannot get that for the Liège plant" inside the answer instead
    of a 403 page mid-chat.
    """


def build_registry(
    user: UserContext, services: Any, correlation_id: str
) -> ToolRegistry:
    """Build the tool registry for one request, scoped to one caller.

    Per request, never cached: each implementation closes over this caller's
    validated scope, so reusing a registry across callers would let a tool answer
    with someone else's plants.

    Every operations agent's tools come from this one registry, including the
    orchestrator's four. That is deliberate: which tools an agent may *declare* is
    decided by the manifest, but what any of them can *reach* is decided here, once,
    under this caller's roles and plant scope. A second registry built for the
    orchestrator would be a second place for that to drift.
    """
    registry = ToolRegistry()
    registry.register(
        "simulate_energy_dispatch",
        _simulate_energy_dispatch(user, services, correlation_id),
    )
    registry.register(
        "lining_rul_forecast", _lining_rul_forecast(user, services, correlation_id)
    )
    registry.register(
        "carbon_footprint_summary",
        _carbon_footprint_summary(user, services, correlation_id),
    )
    registry.register(
        "quality_yield_what_if",
        _quality_yield_what_if(user, services, correlation_id),
    )
    return registry


def _simulate_energy_dispatch(user: UserContext, services: Any, correlation_id: str):
    """Bind the energy-dispatch simulation to this caller."""

    def _run(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        site = _authorized_site(user, arguments.get("site"))
        # Same role gate as POST /v1/energy/schedules:simulate. Asking through the
        # assistant must not be a way around the role that guards the route.
        _require_role(user, "EnergyPlanner.Approve")

        horizon = _bounded_int(
            arguments.get("horizonHours"), DEFAULT_HORIZON_HOURS, 1, MAX_HORIZON_HOURS
        )
        max_shift = _bounded_int(
            arguments.get("maxShiftMinutes"),
            DEFAULT_MAX_SHIFT_MINUTES,
            0,
            MAX_SHIFT_MINUTES_CEILING,
        )
        scenario = str(arguments.get("scenario") or DEFAULT_SCENARIO).strip() or DEFAULT_SCENARIO

        try:
            result = services.simulate_energy(
                site=site,
                horizon_hours=horizon,
                scenario=scenario,
                constraints={"maxShiftMinutes": max_shift},
                correlation_id=correlation_id,
                actor=f"agent:{user.user_id}",
            )
        except Exception as exc:
            # OptimizationError and ValueError are the optimizer saying "these inputs
            # are not feasible", which is an answer the agent should relay, not a
            # fault. Anything else is still relayed rather than raised, because a
            # half-finished chat turn is worse than a named failure.
            raise ToolRefused(str(exc)) from exc

        # Deliberately a projection, not the whole payload. The full recommendation
        # carries every batch row; feeding that to a model wastes context and invites
        # it to re-derive the schedule in prose. It gets the decision-grade figures
        # and the identifiers that let a planner open the real record.
        return {
            "recommendationId": result.get("recommendationId"),
            "site": result.get("site"),
            "scenario": result.get("scenario"),
            "horizonHours": horizon,
            "maxShiftMinutes": max_shift,
            "savings": result.get("savings"),
            "hardConstraintViolations": result.get("hardConstraintViolations"),
            "strategy": result.get("strategy"),
            "modelVersion": result.get("modelVersion"),
            "auditRef": result.get("auditRef"),
            "status": "PROPOSAL_PENDING_HUMAN_APPROVAL",
        }

    return _run


def _lining_rul_forecast(user: UserContext, services: Any, correlation_id: str):
    """Bind the lining RUL forecast to this caller."""

    def _run(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        # Same role gate as GET /v1/furnaces/{assetId}/lining-forecast.
        _require_role(user, "MaintenanceEngineer.Read", "Operator.Read")
        asset_id = str(arguments.get("assetId") or "").strip()
        if not asset_id:
            raise ToolRefused("assetId is required.")

        # The asset's plant is resolved from the repository, exactly as the route's
        # `_asset_access` does, rather than parsed out of the id the model supplied.
        # An operator scoped to Gent cannot read a Liège furnace by naming it.
        site = services.repository.asset_site(asset_id)
        if site is None:
            raise ToolRefused(f"Asset {asset_id} was not found.")
        _authorized_site(user, site)

        try:
            result = services.lining_forecast(
                asset_id=asset_id, correlation_id=correlation_id
            )
        except Exception as exc:
            raise ToolRefused(str(exc)) from exc

        return {
            "assetId": asset_id,
            "site": site,
            "componentId": result.get("componentId"),
            "remainingUsefulLife": result.get("value"),
            "unit": result.get("unit"),
            "riskScore": result.get("riskScore"),
            "riskLevel": result.get("riskLevel"),
            "confidence": result.get("confidence"),
            "modelConfidence": result.get("modelConfidence"),
            "estimatedMinimumLiningMm": result.get("estimatedMinimumLiningMm"),
            # The top feature attributions, so the agent can say *why* rather than
            # only *when*. Truncated because the full list is model detail, not
            # something an engineer reads in a chat answer.
            "drivers": list(result.get("drivers") or [])[:3],
            "scoredAt": result.get("scoredAt"),
            "modelVersion": result.get("modelVersion"),
            "auditRef": result.get("auditRef"),
            "status": "FORECAST_FOR_HUMAN_DECISION",
        }

    return _run


def _carbon_footprint_summary(user: UserContext, services: Any, correlation_id: str):
    """Bind the plant carbon summary to this caller."""

    def _run(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        # Same gate as GET /v1/sustainability/summary: a reader may see the plant's
        # carbon position, and no stronger role is invented for the agent path.
        # Reaching this through the assistant must be neither easier nor harder
        # than reaching it through the dashboard.
        site = _authorized_site(user, arguments.get("site"))

        try:
            summary = services.repository.sustainability_summary(site)
        except Exception as exc:
            raise ToolRefused(str(exc)) from exc

        scope1 = float(summary.get("scope1KgCo2e") or 0.0)
        scope2 = float(summary.get("scope2KgCo2e") or 0.0)
        return {
            "site": site,
            "energyConsumptionMwh": summary.get("energyConsumptionMwh"),
            "scope1KgCo2e": scope1,
            "scope2KgCo2e": scope2,
            # Pre-summed here rather than left to the model: adding two numbers is
            # the sort of arithmetic a model does correctly almost always, and
            # "almost always" is not a property an emissions figure may have.
            "totalKgCo2e": round(scope1 + scope2, 2),
            "etsAllowancePriceEurTonne": summary.get("etsAllowancePriceEurTonne"),
            "modeledEtsExposureEur": round(
                (scope1 + scope2) / 1000.0
                * float(summary.get("etsAllowancePriceEurTonne") or 0.0),
                2,
            ),
            "modeledDispatchCo2ReductionPct": summary.get(
                "modeledDispatchCo2ReductionPct"
            ),
            # Carried through rather than dropped: the agent is instructed to say a
            # figure is modelled, and it can only do that if it is told.
            "dataClassification": summary.get("dataClassification", "SYNTHETIC"),
            "synthetic": bool(summary.get("synthetic", True)),
            "status": "MODELLED_POSITION_NOT_AN_AUDITED_STATEMENT",
        }

    return _run


def _quality_yield_what_if(user: UserContext, services: Any, correlation_id: str):
    """Bind the bounded quality what-if to this caller."""

    def _run(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        # Same role gate as POST /v1/quality/what-if.
        _require_role(user, "ProcessEngineer.Contribute")
        batch_id = str(arguments.get("batchId") or "").strip()
        if not batch_id:
            raise ToolRefused("batchId is required.")

        # The batch's plant is resolved from the repository, exactly as the route
        # does, rather than parsed out of the identifier the model supplied.
        batch = services.repository.quality_batch(batch_id)
        if batch is None:
            raise ToolRefused(f"Batch {batch_id} was not found.")
        _authorized_site(user, batch.get("site"))

        adjustments = _bounded_adjustments(arguments)

        try:
            result = services.scorer.quality_what_if(
                batch=batch, adjustments=adjustments
            )
        except Exception as exc:
            # A ScoringError here is the model saying "these inputs are not
            # supported", which the agent should relay rather than raise.
            raise ToolRefused(str(exc)) from exc

        record = services.audit.append(
            domain="quality",
            entity_id=batch["batchId"],
            correlation_id=correlation_id,
            action="quality.what_if",
            actor=f"agent:{user.user_id}",
            input_snapshot_ref=batch.get("sourceRef", ""),
            model_version=result["modelVersion"],
            output={"value": result["value"], "unit": result["unit"]},
        )

        current = result.get("current") or {}
        proposed = result.get("proposed") or {}
        return {
            "batchId": batch["batchId"],
            "site": batch.get("site"),
            "grade": batch.get("grade"),
            "adjustments": adjustments,
            "currentPredictedFirstPassYieldPct": current.get(
                "predictedFirstPassYieldPct"
            ),
            "currentRiskScore": current.get("riskScore"),
            "proposedPredictedFirstPassYieldPct": proposed.get(
                "predictedFirstPassYieldPct"
            ),
            "unit": result.get("unit"),
            "confidence": result.get("confidence"),
            # Truncated for the same reason as the lining drivers: the full list is
            # model detail, not something an engineer reads in a chat answer.
            "drivers": list(result.get("drivers") or [])[:3],
            "operationalWrite": False,
            "scoredAt": result.get("scoredAt"),
            "modelVersion": result.get("modelVersion"),
            "auditRef": record.audit_id,
            "status": "PROPOSAL_PENDING_HUMAN_APPROVAL",
        }

    return _run


# --- Guards -----------------------------------------------------------------


def _bounded_adjustments(arguments: Mapping[str, Any]) -> dict[str, float]:
    """Collect the process levers the model moved, clamped to the model's range.

    Zero deltas are dropped rather than passed through. The strict function-tool
    schema has no optional properties, so the agent is told to send 0 for a lever it
    is not touching; forwarding those zeros would record an adjustment that was never
    made in the audit entry and in the ``proposed.adjustments`` echo.

    The bounds mirror ``ScoringWorker.quality_what_if``. Duplicating them is
    deliberate: out-of-range values are clamped here so a model that overshoots still
    gets a usable answer with stated assumptions, while the scorer keeps its own
    check as the authority for anything that reaches it by another path.
    """
    bounds = {
        "coilingTempDeltaC": (-20.0, 20.0),
        "forceBalanceDeltaPct": (-10.0, 10.0),
        "carbonEquivalentDeltaPct": (-0.05, 0.05),
    }
    adjustments: dict[str, float] = {}
    for name, (low, high) in bounds.items():
        if name not in arguments:
            continue
        try:
            value = float(arguments[name])
        except (TypeError, ValueError):
            continue
        if not isfinite(value) or value == 0.0:
            continue
        adjustments[name] = max(low, min(high, value))
    return adjustments


def _bounded_int(value: Any, default: int, low: int, high: int) -> int:
    """Coerce a model-supplied number into a sane range.

    A model can emit any integer, including one large enough to make the optimizer
    spend real CPU on a horizon nobody asked for. Out-of-range values are clamped
    rather than refused: the agent is told to state the assumptions it used, and a
    clamped horizon still answers the planner's question.
    """
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, parsed))


def _require_role(user: UserContext, *roles: str) -> None:
    try:
        require_any_role(user, *roles)
    except ApiError as exc:
        raise ToolRefused(
            "The signed-in user does not hold a role that permits this "
            f"({', '.join(roles)})."
        ) from exc


def _authorized_site(user: UserContext, requested: Any) -> str:
    """Resolve and authorize the plant for a tool call.

    A model-supplied site is checked, never trusted. When the model omits one and the
    caller is scoped to exactly one plant, that plant is used — an unambiguous
    default is helpful. When the caller is scoped to several, the tool refuses rather
    than picking, because guessing which plant a planner meant is precisely the kind
    of silent assumption that makes an operational answer untrustworthy.
    """
    site = str(requested or "").strip()
    if not site:
        if len(user.plant_scope) == 1:
            return next(iter(user.plant_scope))
        raise ToolRefused(
            "Specify which plant you mean. You have access to: "
            f"{', '.join(sorted(user.plant_scope))}."
        )

    try:
        require_site(user, site)
    except ApiError as exc:
        raise ToolRefused(
            f"You do not have access to plant {site}. You have access to: "
            f"{', '.join(sorted(user.plant_scope)) or 'no plants'}."
        ) from exc
    return site


__all__ = ["ToolRefused", "build_registry"]
