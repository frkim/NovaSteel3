"""In-process dispatch port: the bridge from the energy agent to the MILP optimizer.

The energy-dispatch agent lives in the knowledge-orchestrator, but the optimizer, the
plant fixtures, the RBAC checks and the audit trail all live here in the BFF. This
module is the seam between them.

It is deliberately an **in-process** port rather than an HTTP call back into our own
API. Two reasons:

* The Copilot route has already authenticated the caller and applied
  ``require_reader`` before anything reaches the agent. Re-entering through HTTP would
  either need a second, service-to-service identity — a new credential to protect for
  no gain — or would silently drop the user's identity from the audit record.
* ``BffServices.simulate_energy`` already writes the ``energy.simulate`` audit entry,
  emits dispatch metrics and de-duplicates by recommendation id. Calling it directly
  means an agent-initiated solve is indistinguishable, in the audit trail, from one a
  planner launched from the screen — which is exactly the property an auditor wants.

The agent still cannot approve or commit: those are separate, policy-gated routes, and
``commit_schedule``/``approve_recommendation`` are in the orchestrator's
``FORBIDDEN_TOOL_NAMES``, so no port method exists for them here either.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

logger = logging.getLogger(__name__)

#: Anything the agent proposes is attributed to the agent identity, never to the
#: signed-in planner. A recommendation must never look as though a human made it.
AGENT_ACTOR = "energy-dispatch-agent"


def _payload(row: Mapping[str, Any]) -> Mapping[str, Any]:
    """Unwrap the event envelope the fixtures and the Fabric source both use."""
    inner = row.get("payload")
    return inner if isinstance(inner, Mapping) else row


def _number(row: Mapping[str, Any], *names: str) -> float:
    """First numeric value among *names*, tolerating both key conventions."""
    payload = _payload(row)
    for name in names:
        if name in payload:
            try:
                return float(payload[name])
            except (TypeError, ValueError):
                continue
    return 0.0


class BffDispatchPort:
    """Runs the agent's dispatch tools against the BFF's own optimizer and data."""

    def __init__(self, services: Any):
        self._services = services

    def _site(self, site: str) -> str:
        """Resolve a blank site to this deployment's configured plant.

        Site resolution belongs here, not in the orchestrator: the plant identifier
        comes from the data namespace this BFF was deployed against. Asking the model
        to supply one would only invite it to invent a plausible-looking code.
        """
        candidate = (site or "").strip()
        if candidate:
            return candidate
        settings = getattr(self._services, "settings", None)
        return str(
            getattr(settings, "data_namespace", "")
            or getattr(self._services.repository, "site", "")
        )

    # -- read ---------------------------------------------------------------

    def read_energy_context(self, *, site: str = "") -> dict[str, Any]:
        """Day-ahead price/carbon intervals and the planned batches, read-only."""
        site = self._site(site)
        repository = self._services.repository
        intervals = list(repository.raw_energy(site))
        batches = list(repository.raw_heat_batches(site))
        if not intervals:
            raise ValueError(f"No energy intervals are available for site {site!r}.")
        prices = [_number(row, "price", "priceEurMwh") for row in intervals]
        return {
            "site": site,
            "source": repository.source,
            "intervalCount": len(intervals),
            "plannedBatchCount": len(batches),
            "priceEurMwh": {
                "min": round(min(prices), 2) if prices else 0.0,
                "max": round(max(prices), 2) if prices else 0.0,
                "mean": round(sum(prices) / len(prices), 2) if prices else 0.0,
            },
            "urgentBatchCount": sum(
                1 for row in batches if _payload(row).get("urgent")
            ),
            "note": "Synthetic demo data. Read-only; no schedule is implied.",
        }

    def forecast_demand(self, *, site: str = "", horizon_hours: int) -> dict[str, Any]:
        """Aggregate the baseline demand profile the optimizer will start from."""
        site = self._site(site)
        intervals = list(self._services.repository.raw_energy(site))
        slots = max(1, min(len(intervals), int(horizon_hours) * 4))
        window = intervals[:slots]
        demand = [
            _number(row, "baseline_demand_mw", "baselineDemandMw", "demand", "demandMw")
            for row in window
        ]
        return {
            "site": site,
            "horizonHours": int(horizon_hours),
            "slots": slots,
            "baselineDemandMw": {
                "peak": round(max(demand), 2) if demand else 0.0,
                "mean": round(sum(demand) / len(demand), 2) if demand else 0.0,
            },
            "note": "Baseline profile before optimization. Synthetic demo data.",
        }

    # -- simulate & propose --------------------------------------------------

    def simulate_schedule(
        self,
        *,
        site: str = "",
        horizon_hours: int,
        scenario: str,
        constraints: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Run the MILP. This is the only path from the agent to a number."""
        site = self._site(site)
        return self._services.simulate_energy(
            site=site,
            horizon_hours=int(horizon_hours),
            scenario=scenario,
            constraints=dict(constraints or {}),
            correlation_id=f"agent-{site}-{scenario}",
            actor=AGENT_ACTOR,
        )

    def propose_recommendation(
        self, *, recommendation_id: str, rationale: str
    ) -> dict[str, Any]:
        """Return the stored proposal, which is already ``PENDING_APPROVAL``.

        There is nothing to write: ``simulate_energy`` persists the recommendation in
        the pending state and records the audit entry. Making this a no-op read is the
        point — the agent's "propose" step must not be able to change a status, or the
        propose/approve boundary would exist only in the prose.
        """
        proposal = self._services.energy_recommendation(recommendation_id)
        if proposal is None:
            raise ValueError(
                f"No simulated recommendation {recommendation_id!r} exists. "
                "Run simulate_schedule first."
            )
        return dict(proposal) | {
            "status": proposal.get("status", "PENDING_APPROVAL"),
            "agentRationale": rationale,
            "requiresHumanApproval": True,
        }


def bind_dispatch_agent(services: Any) -> bool:
    """Attach a dispatch-capable energy agent to the Copilot service.

    Returns whether the wiring succeeded. A failure is logged and swallowed: the panel
    without dispatch routing is the pre-existing, working behaviour, and a demo that
    cannot reach the orchestrator must still serve every other route.
    """
    copilot = getattr(services, "copilot", None)
    service = getattr(copilot, "_service", None)
    if service is None or not hasattr(service, "bind_energy_agent"):
        logger.info("Copilot service does not support dispatch routing — skipping.")
        return False

    try:
        from knowledge_orchestrator.energy_agent import create_energy_dispatch_agent
    except ImportError as exc:  # pragma: no cover - repository integration failure
        logger.warning("Energy-dispatch agent unavailable (%s)", exc)
        return False

    try:
        service.bind_energy_agent(create_energy_dispatch_agent(BffDispatchPort(services)))
    except Exception as exc:  # noqa: BLE001 - optional capability
        logger.warning("Could not bind the energy-dispatch agent (%s)", exc)
        return False

    logger.info("Energy-dispatch agent bound to the Copilot panel.")
    return True


__all__ = ["AGENT_ACTOR", "BffDispatchPort", "bind_dispatch_agent"]
