"""The function-tool boundary between a Foundry agent and NovaSteel's calculations.

ADR-006 keeps the deterministic Python services authoritative for optimization and
scoring; an agent may decide *which* calculation to run and explain the result, but
it may not be the calculation. This module is where that line is drawn: it declares
the tools an agent is allowed to call, as JSON schemas, and nothing else. The
implementations live in the layer that owns the caller's identity — see
``bff_api.agent_tools`` — and are injected as a :class:`ToolRegistry`.

Three properties are deliberate.

**Client-side, not server-side.** These are OpenAI *function* tools, so Foundry
returns a ``function_call`` item and our process executes it. It is not an OpenAPI
or MCP tool that the platform calls over the network. That matters here because the
production estate runs with ``publicNetworkAccess: 'Disabled'`` and no inbound path
from Foundry into the VNet — a server-side tool would need one. It also means the
tool body runs under our managed identity and inside our request scope, which is
what makes the next property possible.

**Authorization is not the model's job.** The agent runs as the service, not as the
operator, so a tool call carries no caller identity of its own. Every executor is
therefore bound to an already-validated ``UserContext`` at construction time and
re-checks role and plant scope itself. The ``site`` argument below is accepted from
the model — an operator with three plants must be able to say "for Gent" — but it is
*checked*, never trusted: an out-of-scope site is refused by the executor exactly as
the HTTP route would refuse it. A tool that took the caller's scope from the model
would hand the model a privilege-escalation primitive.

**Deny by default.** :meth:`ToolRegistry.execute` refuses any name it was not given
an implementation for, rather than falling through to something plausible. A model
that hallucinates a tool gets an error it must report, not a silent no-op.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

logger = logging.getLogger(__name__)

# Tool arguments are model output. They are small by construction (a site name, an
# hour count, a handful of numeric constraints), so anything large is a sign the
# model is being driven rather than reasoning, and is refused before it reaches a
# JSON parser or a solver.
MAX_TOOL_ARGUMENTS_CHARS = 4096


class ToolError(RuntimeError):
    """A tool call could not be completed.

    Raised rather than returned so an executor cannot accidentally hand the model a
    success-shaped payload. The run loop converts it into a ``function_call_output``
    the model must account for in its answer.
    """


class UnknownToolError(ToolError):
    """The model asked for a tool that is not registered for this agent."""


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """A function tool an agent may call, as name, description and JSON schema."""

    name: str
    description: str
    parameters: Mapping[str, Any]

    def to_sdk_tool(self) -> Any:
        """Build the SDK ``FunctionTool`` for this spec.

        ``strict=True`` is not decoration. It makes the service constrain generation
        to the schema, so the arguments an executor receives are already the right
        shape and an executor cannot be reached with a field the schema never
        declared. Every schema below therefore also sets
        ``additionalProperties: false``, which strict mode requires.
        """
        from azure.ai.projects.models import FunctionTool

        return FunctionTool(
            name=self.name,
            description=self.description,
            parameters=dict(self.parameters),
            strict=True,
        )


# --- The tool catalogue -----------------------------------------------------
#
# Adding an entry here widens what an agent can reach, so this list is the review
# surface. Keep it short, keep every parameter necessary, and keep anything that
# writes, commits or actuates out of it entirely (ADR-007: no direct OT action, and
# every financially or physically consequential step needs a human approval event).

SIMULATE_ENERGY_DISPATCH = ToolSpec(
    name="simulate_energy_dispatch",
    description=(
        "Run the deterministic energy-dispatch optimizer for a plant and return the "
        "proposed schedule, its savings, and its rationale. This SIMULATES only: it "
        "produces a proposal for human approval and never commits a schedule or "
        "writes to any plant system. Call it whenever the operator asks what a shift "
        "in the heat schedule would cost, save, or emit."
    ),
    parameters={
        "type": "object",
        "properties": {
            "site": {
                "type": "string",
                "description": (
                    "Plant identifier, e.g. NS-DEMO-GENT. Must be a plant the "
                    "operator is authorized for; the request is refused otherwise."
                ),
            },
            "horizonHours": {
                "type": "integer",
                "description": "Planning horizon in hours, typically 8 to 24.",
            },
            "scenario": {
                "type": "string",
                "description": (
                    "Named scenario to optimize, e.g. 'baseline' or 'price-peak'."
                ),
            },
            "maxShiftMinutes": {
                "type": "integer",
                "description": (
                    "Hard constraint: the furthest any batch may move from its "
                    "planned slot. Use the operator's stated limit; do not invent a "
                    "looser one to improve the result."
                ),
            },
        },
        # Every property is required because strict mode does not support optional
        # keys. The model is told the defaults in the agent instructions instead.
        "required": ["site", "horizonHours", "scenario", "maxShiftMinutes"],
        "additionalProperties": False,
    },
)

LINING_RUL_FORECAST = ToolSpec(
    name="lining_rul_forecast",
    description=(
        "Return the physics-informed remaining-useful-life forecast for a furnace "
        "lining: RUL in days with P10/P90 bands, a risk score, model confidence and "
        "the model version. Read-only. Call it before discussing when a reline is "
        "needed; never estimate a lining's remaining life yourself."
    ),
    parameters={
        "type": "object",
        "properties": {
            "assetId": {
                "type": "string",
                "description": "Furnace asset identifier, e.g. NS-DEMO-GENT-EAF-01.",
            },
        },
        "required": ["assetId"],
        "additionalProperties": False,
    },
)

TOOL_CATALOGUE: Mapping[str, ToolSpec] = {
    spec.name: spec
    for spec in (SIMULATE_ENERGY_DISPATCH, LINING_RUL_FORECAST)
}


def tool_spec(name: str) -> ToolSpec:
    """Look a tool up by name, failing loudly on a typo in a manifest."""
    try:
        return TOOL_CATALOGUE[name]
    except KeyError:
        raise UnknownToolError(
            f"{name!r} is not in the tool catalogue. Known tools: "
            f"{', '.join(sorted(TOOL_CATALOGUE))}"
        ) from None


# --- Execution --------------------------------------------------------------

ToolCallable = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass
class ToolRegistry:
    """The implementations available to one agent run, for one caller.

    Construct a registry per request, not per process: an implementation is expected
    to close over the caller's validated ``UserContext``, so sharing one across
    callers would let a tool answer with another operator's scope.
    """

    implementations: dict[str, ToolCallable] = field(default_factory=dict)

    def register(self, name: str, implementation: ToolCallable) -> "ToolRegistry":
        """Register an implementation, rejecting anything not in the catalogue."""
        tool_spec(name)
        self.implementations[name] = implementation
        return self

    @property
    def specs(self) -> tuple[ToolSpec, ...]:
        """The specs this registry can actually serve.

        An agent is declared with the tools it should have, but is only ever given
        the ones backed by an implementation here. Declaring a tool the process
        cannot execute would produce a call the run loop must fail, which reads to
        the operator as the assistant breaking rather than as a misconfiguration.
        """
        return tuple(tool_spec(name) for name in sorted(self.implementations))

    def execute(self, name: str, arguments: str | Mapping[str, Any]) -> Mapping[str, Any]:
        """Execute one model-issued tool call and return its result payload."""
        implementation = self.implementations.get(name)
        if implementation is None:
            raise UnknownToolError(
                f"Tool {name!r} is not available. Available: "
                f"{', '.join(sorted(self.implementations)) or 'none'}"
            )

        parsed = _parse_arguments(name, arguments)
        logger.info("Executing agent tool %s with keys %s", name, sorted(parsed))
        return implementation(parsed)


def _parse_arguments(name: str, arguments: str | Mapping[str, Any]) -> Mapping[str, Any]:
    """Decode the model's arguments, refusing anything oversized or malformed."""
    if isinstance(arguments, Mapping):
        return dict(arguments)

    text = arguments or "{}"
    if len(text) > MAX_TOOL_ARGUMENTS_CHARS:
        raise ToolError(
            f"Tool {name!r} arguments exceed {MAX_TOOL_ARGUMENTS_CHARS} characters."
        )
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ToolError(f"Tool {name!r} arguments are not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ToolError(f"Tool {name!r} arguments must be a JSON object.")
    return parsed


__all__ = [
    "LINING_RUL_FORECAST",
    "SIMULATE_ENERGY_DISPATCH",
    "TOOL_CATALOGUE",
    "ToolCallable",
    "ToolError",
    "ToolRegistry",
    "ToolSpec",
    "UnknownToolError",
    "tool_spec",
]
