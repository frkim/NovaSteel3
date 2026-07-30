"""Adapter from the BFF boundary to the tool-calling operations agents.

Mirrors :mod:`copilot_adapter`: the orchestrator package is injected onto
``sys.path`` once and imports stay lazy, so the BFF keeps no build-time coupling
to it.

What makes this path different from ``copilot_adapter`` is *authorization*. A
hosted agent runs as the project managed identity, so when it emits a function
call that call carries no caller identity — nothing in the request says which
operator asked. The tool bodies therefore close over the request's already
validated :class:`~bff_api.auth.UserContext` and re-apply the same role and site
checks the equivalent REST route applies (see :mod:`bff_api.agent_tools`). The
model may *propose* a site; only the BFF decides whether the caller may have it.

The agent is also not the calculator. Every tool call lands in the same audited,
version-pinned service the REST routes call, and every result comes back marked
``PROPOSAL_PENDING_HUMAN_APPROVAL`` (ADR-006, ADR-007).
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from .contracts import ErrorCode
from .errors import ApiError

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[4]
_KNOWLEDGE_SRC = _ROOT / "services" / "knowledge-orchestrator" / "src"


class OperationsAgentAdapter:
    """Runs a turn against an operations agent with caller-scoped tools."""

    def __init__(self) -> None:
        if str(_KNOWLEDGE_SRC) not in sys.path:
            sys.path.insert(0, str(_KNOWLEDGE_SRC))
        try:
            from knowledge_orchestrator.agent_manifest import (
                ENERGY_ADVISOR_AGENT_NAME,
                PROJECT_ENDPOINT_ENV,
                PROJECT_OPERATIONS,
                agent_spec,
                agents_for_project,
            )
            from knowledge_orchestrator.agent_service import FoundryAgentService
        except ImportError as exc:  # pragma: no cover - repository integration failure
            raise RuntimeError("knowledge-orchestrator is required by the BFF.") from exc

        self._service_cls = FoundryAgentService
        self._agent_spec = agent_spec
        self._project = PROJECT_OPERATIONS
        self._endpoint_env = PROJECT_ENDPOINT_ENV[PROJECT_OPERATIONS]
        self._default_agent = ENERGY_ADVISOR_AGENT_NAME
        self._agents_for_project = agents_for_project

    def roster(self) -> list[dict[str, Any]]:
        """The operations agents this deployment knows about, and their tools.

        Read from the same manifest the reconciler applies, so what the UI offers
        and what exists in Foundry cannot drift apart in the code — only in the
        estate, and that is exactly what the reconciler exists to close.
        """
        return [
            {
                "name": spec.name,
                "description": spec.description,
                "tools": list(spec.tools),
            }
            for spec in self._agents_for_project(self._project)
        ]

    @property
    def configured(self) -> bool:
        """True when the operations project endpoint is present in the environment.

        Deliberately not a fallback to the knowledge project. The two projects are
        a trust boundary: an agent can only call the tools declared on its own
        definition, so quietly running an operations agent in the knowledge
        project would hand tool access to the project that reads untrusted
        content.
        """
        return bool(os.environ.get(self._endpoint_env, "").strip())

    def _build_service(self) -> Any:
        """Construct the runtime for the operations project.

        ``FoundryAgentService`` takes a project *endpoint*, not a project name: one
        class serves both projects and the endpoint is what selects between them.
        The model and knowledge-base configuration are read from the environment
        the same way the orchestrator's own hosting path reads them, so a turn
        served through the BFF and a turn served by the reconciler resolve to the
        same agent definition.
        """
        from knowledge_orchestrator.agent_service import (
            DEFAULT_MODEL,
            ENV_CHAT_DEPLOYMENT,
        )

        return self._service_cls(
            project_endpoint=os.environ.get(self._endpoint_env, "").strip(),
            model=os.environ.get(ENV_CHAT_DEPLOYMENT, DEFAULT_MODEL),
        )

    def ask(
        self,
        *,
        user: Any,
        services: Any,
        question: str,
        conversation_id: str | None,
        correlation_id: str,
        agent_name: str | None = None,
    ) -> dict[str, Any]:
        from .agent_tools import build_registry

        if not self.configured:
            raise ApiError(
                503,
                ErrorCode.UPSTREAM_UNAVAILABLE,
                "Operations agents are not configured in this environment.",
            )

        name = (agent_name or self._default_agent).strip() or self._default_agent
        try:
            spec = self._agent_spec(name)
        except KeyError as exc:
            raise ApiError(
                404, ErrorCode.NOT_FOUND, f"Unknown agent '{name}'."
            ) from exc
        if spec.project != self._project:
            raise ApiError(
                403,
                ErrorCode.FORBIDDEN_ROLE,
                f"Agent '{name}' is not an operations agent.",
            )

        registry = build_registry(
            user=user, services=services, correlation_id=correlation_id
        )
        context = _caller_scope_context(user, services)
        service = self._build_service()
        result = service.run(
            question,
            agent_name=name,
            conversation_id=conversation_id,
            registry=registry,
            context=context,
        )

        tool_calls = [
            {
                "tool": call.get("name", ""),
                "status": "succeeded" if call.get("ok") else "failed",
                "arguments": _decode_arguments(call.get("arguments")),
            }
            for call in result.get("tool_calls", ())
        ]
        logger.info(
            "operations agent answered correlation_id=%s agent=%s tools=%s",
            correlation_id,
            name,
            ",".join(call["tool"] for call in tool_calls) or "-",
        )
        return {
            "agent": name,
            "project": self._project,
            "answer": result.get("answer", ""),
            "conversationId": result.get("conversation_id", ""),
            "toolCalls": tool_calls,
        }


def _decode_arguments(raw: Any) -> dict[str, Any]:
    """Return the model's tool arguments as an object for the response envelope.

    The arguments arrive as the raw JSON string the model produced. Echoing them
    back lets the UI show *what* the agent asked for, which is the point of
    surfacing tool calls at all — but a malformed string must not fail the
    request, so anything unparseable degrades to an empty object.
    """
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return {}
    try:
        decoded = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _caller_scope_context(user: Any, services: Any) -> str:
    """Return the compact server-validated scope block supplied to operations agents."""
    sites = sorted(str(site) for site in getattr(user, "plant_scope", frozenset()))
    assets_by_site: dict[str, list[str]] = {site: [] for site in sites}
    repository = services.repository

    for asset in repository.furnaces():
        asset_id = str(asset.get("assetId") or "").strip()
        if not asset_id:
            continue
        site = repository.asset_site(asset_id)
        if site not in assets_by_site:
            continue
        asset_type = str(asset.get("assetType") or "").strip()
        label = f"{asset_id} ({asset_type})" if asset_type else asset_id
        assets_by_site[site].append(label)

    lines = [
        "Caller scope (server-validated):",
        f"- Authorized sites: {', '.join(sites) or 'none'}",
        "- Tool assets by site:",
    ]
    for site in sites:
        assets = sorted(set(assets_by_site[site]))
        lines.append(f"  - {site}: {', '.join(assets) if assets else 'none'}")
    return "\n".join(lines)


__all__ = ["OperationsAgentAdapter"]
