"""Restricted agent tool allow-list and registry (api-contracts §10, security §12.5).

Foundry agent identities are granted ONLY named read/simulate/propose (energy) or
search/draft-write (knowledge) tools. Approve/publish/commit/schedule/delete are
human-role actions and are not in any agent's allow-list — the registry refuses to
dispatch them under any prompt.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Callable


class ToolPermission(str, enum.Enum):
    READ = "read"
    SIMULATE = "simulate"
    PROPOSE = "propose"
    SEARCH = "search"
    DRAFT_WRITE = "draft-write"


@dataclass(frozen=True)
class ToolSpec:
    """A single named tool an agent may call, with its capability classification."""

    name: str
    permission: ToolPermission
    description: str


# Knowledge-capture agent (api-contracts §10.2): search approved procedures + write
# a DRAFT only. It cannot transition status or publish.
KNOWLEDGE_AGENT_TOOLS: dict[str, ToolSpec] = {
    "search_approved_procedures": ToolSpec(
        "search_approved_procedures",
        ToolPermission.SEARCH,
        "Search the derived retrieval index of APPROVED procedures only.",
    ),
    "write_draft_procedure": ToolSpec(
        "write_draft_procedure",
        ToolPermission.DRAFT_WRITE,
        "Write a DRAFT procedure record; cannot transition status.",
    ),
}

# Energy-dispatch agent (api-contracts §10.1): read/forecast/simulate/propose only.
ENERGY_AGENT_TOOLS: dict[str, ToolSpec] = {
    "read_energy_context": ToolSpec(
        "read_energy_context", ToolPermission.READ, "Read energy context (read-only)."
    ),
    "forecast_demand": ToolSpec(
        "forecast_demand", ToolPermission.READ, "Internal forecast (read-only)."
    ),
    "simulate_schedule": ToolSpec(
        "simulate_schedule", ToolPermission.SIMULATE, "Propose-only schedule simulation."
    ),
    "propose_recommendation": ToolSpec(
        "propose_recommendation",
        ToolPermission.PROPOSE,
        "Create a PENDING recommendation for human review; never approves/commits.",
    ),
}

AGENT_TOOL_ALLOWLIST: dict[str, dict[str, ToolSpec]] = {
    "knowledge-capture": KNOWLEDGE_AGENT_TOOLS,
    "energy-dispatch": ENERGY_AGENT_TOOLS,
}

# Capabilities that no agent identity may ever hold (human-role/policy-gated actions).
FORBIDDEN_TOOL_NAMES = frozenset(
    {
        "approve_procedure",
        "publish_procedure",
        "reject_procedure",
        "approve_recommendation",
        "commit_schedule",
        "delete_audio",
        "delete_procedure",
        "transition_status",
    }
)


class ToolNotAllowed(Exception):
    """Raised when an agent attempts a tool outside its least-privilege allow-list."""


class ToolRegistry:
    """Dispatches only allow-listed tool calls for a given agent identity."""

    def __init__(self, agent_name: str):
        if agent_name not in AGENT_TOOL_ALLOWLIST:
            raise ToolNotAllowed(f"unknown agent identity '{agent_name}'")
        self.agent_name = agent_name
        self._allowed = AGENT_TOOL_ALLOWLIST[agent_name]
        self._handlers: dict[str, Callable[..., object]] = {}

    def register(self, name: str, handler: Callable[..., object]) -> None:
        """Bind an implementation to an allow-listed tool name."""
        self._require_allowed(name)
        self._handlers[name] = handler

    def is_allowed(self, name: str) -> bool:
        return name in self._allowed and name not in FORBIDDEN_TOOL_NAMES

    def call(self, name: str, **kwargs):
        """Invoke ``name`` if and only if it is on this agent's allow-list."""
        self._require_allowed(name)
        if name not in self._handlers:
            raise ToolNotAllowed(f"tool '{name}' has no registered handler")
        return self._handlers[name](**kwargs)

    def _require_allowed(self, name: str) -> None:
        if name in FORBIDDEN_TOOL_NAMES:
            raise ToolNotAllowed(
                f"tool '{name}' is a human-role action and is never agent-callable"
            )
        if name not in self._allowed:
            raise ToolNotAllowed(
                f"tool '{name}' is not in the allow-list for agent "
                f"'{self.agent_name}'"
            )
