"""Hosting the NovaSteel agents in Microsoft Foundry Agent Service.

Until now every agent in this service was a Python object that happened to call a
model endpoint. This module moves the agent *definitions* into Foundry Agent Service,
so that the platform — not our process — owns the agent, its tools, its threads and
its telemetry.

What that buys, concretely:

* **Conversations are durable and server-side.** Conversation state lives in the
  Cosmos account provisioned by ``infra/bicep/modules/cosmos.bicep`` instead of
  process memory, so a replica restart does not lose an operator's conversation, and
  GDPR erasure can delete a conversation by id.
* **Tool calling is the platform's problem.** The procedure agent reaches Azure AI
  Search through the Foundry IQ knowledge base's MCP endpoint. We declare the tool;
  the service runs the loop.
* **Observability is automatic.** Because the Foundry account carries an
  Application Insights connection (``modules/foundry-agents.bicep``), every run
  emits OpenTelemetry GenAI spans — model, token counts, tool calls, latency — into
  the same workspace as our own traces, with no instrumentation code here.

There is no ARM resource type for an agent: agents are data-plane objects. The
roster therefore lives in :mod:`agent_manifest` and is applied by
:mod:`agent_reconciler`; ``infra`` only provides the project endpoints they need.

**On the runtime API.** Agent *definitions* are managed through
``AIProjectClient.agents`` (``create_version``), but agent *runs* go through the
OpenAI Responses API obtained from ``AIProjectClient.get_openai_client()``, with the
agent selected by an ``agent_reference`` in the request body. There is no
threads/messages/runs surface on this client — that was the older
``azure-ai-agents`` shape, and calling it here raises ``AttributeError`` at the first
request rather than failing at import, which is why it survived undetected in a
service that had never been deployed.

Function tools are executed **client-side**: the service returns a ``function_call``
item and :meth:`FoundryAgentService.run` executes it through the caller's
:class:`~knowledge_orchestrator.agent_tools.ToolRegistry`. See that module for why
that direction matters for both private networking and authorization.

As everywhere else in this service, the Azure SDKs are imported lazily and every
failure degrades to the local implementations rather than raising.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .agent_manifest import (
    BUILTIN_TOOLS,
    ENERGY_ADVISOR_AGENT_NAME,
    KNOWLEDGE_MCP_ALLOWED_TOOLS,
    KNOWLEDGE_MCP_LABEL,
    MANIFEST,
    PROCEDURE_AGENT_DECLINE,
    PROCEDURE_AGENT_INSTRUCTIONS,
    PROCEDURE_AGENT_NAME,
    PROJECT_ENDPOINT_ENV,
    PROJECT_KNOWLEDGE,
    PROJECT_OPERATIONS,
    TOOL_KNOWLEDGE_MCP,
    TOOL_WEB_SEARCH,
    WEB_SEARCH_AGENT_NAME,
    AgentSpec,
    agent_spec,
    agents_for_project,
)
from .agent_tools import ToolError, ToolRegistry
from .foundry_endpoints import normalize_endpoint
from .foundry_iq import (
    KnowledgeBaseConfig,
    knowledge_base_config_from_env,
)

logger = logging.getLogger(__name__)

ENV_PROJECT_ENDPOINT = PROJECT_ENDPOINT_ENV[PROJECT_KNOWLEDGE]
ENV_OPERATIONS_PROJECT_ENDPOINT = PROJECT_ENDPOINT_ENV[PROJECT_OPERATIONS]
ENV_CHAT_DEPLOYMENT = "FOUNDRY_CHAT_DEPLOYMENT"
ENV_AGENT_MODE = "FOUNDRY_AGENT_SERVICE_MODE"  # "azure" | "local" (explicit override)

# Path that distinguishes a Foundry *project* endpoint from the account endpoint.
# The project model addresses agents per project; there is no account-level agents
# API, and the classic hub-based equivalent was a connection string instead.
PROJECT_PATH_SEGMENT = "/api/projects/"

DEFAULT_MODEL = "gpt-5.4-mini"

# A tool-calling turn is a loop: the model may call a tool, read the result, and call
# another. It is bounded so that a model which keeps re-calling the same tool — a
# known failure mode when a tool returns an error it cannot act on — costs a fixed
# number of requests instead of running until the request times out.
#
# Six, not four, because the orchestrator holds four tools and a genuinely
# cross-domain question can need all of them plus a round to answer; a specialist
# still only ever needs one or two, so the higher bound costs it nothing.
MAX_TOOL_ITERATIONS = 6



@dataclass
class HostedAgent:
    """A reference to an agent definition living in Foundry Agent Service."""

    name: str
    agent_id: str
    model: str
    tools: tuple[str, ...] = ()
    version: str = ""


@dataclass
class AgentServiceStatus:
    """Outcome of an attempt to host the agents in Agent Service."""

    enabled: bool
    project_endpoint: str = ""
    agents: tuple[HostedAgent, ...] = ()
    reason: str = ""
    project: str = PROJECT_KNOWLEDGE


class FoundryAgentService:
    """Creates and runs the NovaSteel agents in Foundry Agent Service."""

    def __init__(
        self,
        project_endpoint: str,
        model: str = DEFAULT_MODEL,
        knowledge_base: Optional[KnowledgeBaseConfig] = None,
        credential: Any = None,
    ) -> None:
        self.project_endpoint = normalize_endpoint(project_endpoint)
        self.model = model
        self._knowledge_base = knowledge_base
        self._credential = credential
        self._client: Any = None
        self._openai: Any = None

    def _get_credential(self) -> Any:
        if self._credential is None:
            from azure.identity import DefaultAzureCredential

            self._credential = DefaultAzureCredential()
        return self._credential

    def _project_client(self) -> Any:
        if self._client is None:
            from azure.ai.projects import AIProjectClient

            self._client = AIProjectClient(
                endpoint=self.project_endpoint, credential=self._get_credential()
            )
        return self._client

    def _openai_client(self) -> Any:
        """The Responses-API client for this project.

        ``get_openai_client`` points itself at ``{endpoint}/openai/v1`` and
        authenticates for ``https://ai.azure.com/.default`` — the same versionless
        route and Foundry audience :mod:`foundry_endpoints` builds by hand for the
        direct inference calls, which is the confirmation that those are right.
        """
        if self._openai is None:
            self._openai = self._project_client().get_openai_client()
        return self._openai

    # -- tools -------------------------------------------------------------

    def _knowledge_tool(self) -> Optional[Any]:
        """Build the MCP tool that points the agent at the Foundry IQ knowledge base.

        Returns ``None`` when no knowledge base is configured, in which case the agent
        is still created but will correctly decline every question — which is the
        right failure mode for a grounded assistant.
        """
        if self._knowledge_base is None:
            return None

        from azure.ai.projects.models import MCPTool

        return MCPTool(
            server_label=KNOWLEDGE_MCP_LABEL,
            server_url=self._knowledge_base.mcp_url,
            # No approval prompts: retrieval is a read against our own index, and an
            # operator on a plant floor cannot answer an approval dialog.
            require_approval="never",
            allowed_tools=list(KNOWLEDGE_MCP_ALLOWED_TOOLS),
        )

    def _resolve_tools(
        self, spec: AgentSpec, registry: Optional[ToolRegistry] = None
    ) -> tuple[list[Any], tuple[str, ...]]:
        """Turn a spec's tool names into SDK tool objects plus readable names.

        A declared tool is dropped rather than faked when the process cannot back it:
        no knowledge base means no MCP tool, and no registered implementation means no
        function tool. Declaring a tool the run loop would have to fail on turns a
        configuration gap into what looks to the operator like a broken assistant.
        """
        tools: list[Any] = []
        names: list[str] = []
        for name in spec.tools:
            if name == TOOL_KNOWLEDGE_MCP:
                tool = self._knowledge_tool()
                if tool is not None:
                    tools.append(tool)
                    names.extend(KNOWLEDGE_MCP_ALLOWED_TOOLS)
                continue
            if name == TOOL_WEB_SEARCH:
                from azure.ai.projects.models import WebSearchTool

                tools.append(WebSearchTool())
                names.append("web_search")
                continue
            # Reconciling a definition (no registry) declares every function tool,
            # because the definition must describe the agent as deployed rather than
            # as one process happens to be configured. Serving a request declares
            # only what this process can actually execute.
            if registry is None or name in registry.implementations:
                tools.append(_sdk_tool(name))
                names.append(name)
            else:
                logger.warning(
                    "Agent %s declares tool %s with no registered implementation — "
                    "omitting it from this run",
                    spec.name,
                    name,
                )
        return tools, tuple(names)

    # -- agent lifecycle ---------------------------------------------------

    def ensure_agent(
        self, spec: AgentSpec, registry: Optional[ToolRegistry] = None
    ) -> HostedAgent:
        """Create or update one manifest agent. Idempotent by agent name."""
        from azure.ai.projects.models import PromptAgentDefinition

        tools, tool_names = self._resolve_tools(spec, registry)
        model = os.environ.get(spec.model_env, self.model)

        agent = self._project_client().agents.create_version(
            agent_name=spec.name,
            definition=PromptAgentDefinition(
                model=model,
                instructions=spec.instructions,
                tools=tools,
            ),
        )

        hosted = HostedAgent(
            name=spec.name,
            agent_id=getattr(agent, "id", spec.name),
            model=model,
            tools=tool_names,
            version=str(getattr(agent, "version", "") or ""),
        )
        logger.info(
            "Agent hosted in Agent Service: %s (id %s, model %s, tools %s)",
            hosted.name,
            hosted.agent_id,
            hosted.model,
            ", ".join(hosted.tools) or "none",
        )
        return hosted

    def ensure_procedure_agent(self) -> HostedAgent:
        """Create or update the procedure agent. Idempotent by agent name."""
        return self.ensure_agent(agent_spec(PROCEDURE_AGENT_NAME))

    # -- runs ---------------------------------------------------------------

    def run(
        self,
        question: str,
        agent_name: str = PROCEDURE_AGENT_NAME,
        conversation_id: Optional[str] = None,
        registry: Optional[ToolRegistry] = None,
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """Run one turn against a hosted agent, executing any tool calls it makes.

        Returns the answer text, the conversation id so a caller can continue on the
        server-side conversation instead of resending history, and the tool calls
        that were executed — the latter so the BFF can surface *which* calculation
        produced a number rather than asking the operator to trust the prose.
        """
        openai = self._openai_client()
        conversation = (
            conversation_id
            if conversation_id
            else getattr(openai.conversations.create(), "id", "")
        )
        agent_reference = {"agent_reference": {"name": agent_name, "type": "agent_reference"}}

        response = openai.responses.create(
            input=_turn_input(question, context),
            conversation=conversation,
            extra_body=agent_reference,
        )

        executed: list[dict[str, Any]] = []
        for _ in range(MAX_TOOL_ITERATIONS):
            outputs = _tool_outputs(response, registry, executed)
            if not outputs:
                break
            response = openai.responses.create(
                input=outputs,
                conversation=conversation,
                extra_body=agent_reference,
            )
        else:
            logger.warning(
                "Agent %s hit the %d-iteration tool limit; answering with what it has",
                agent_name,
                MAX_TOOL_ITERATIONS,
            )

        return {
            "answer": (getattr(response, "output_text", "") or "").strip(),
            "conversation_id": conversation,
            "response_id": getattr(response, "id", ""),
            "tool_calls": tuple(executed),
        }

    def ask(self, question: str, conversation_id: Optional[str] = None) -> dict[str, Any]:
        """Run one turn against the procedure agent."""
        return self.run(question, PROCEDURE_AGENT_NAME, conversation_id)

    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a server-side conversation.

        The GDPR erasure path calls this: once conversations live in Agent Service
        rather than process memory, forgetting an operator means deleting theirs.
        """
        self._openai_client().conversations.delete(conversation_id=conversation_id)


def _sdk_tool(name: str) -> Any:
    """Build the SDK function tool for a catalogue name."""
    from .agent_tools import tool_spec

    return tool_spec(name).to_sdk_tool()


def _turn_input(question: str, context: Optional[str]) -> Any:
    """Build the Responses API input for one operator turn."""
    caller_context = (context or "").strip()
    if not caller_context:
        return question
    return [
        {"type": "message", "role": "developer", "content": caller_context},
        {"type": "message", "role": "user", "content": question},
    ]


def _tool_outputs(
    response: Any, registry: Optional[ToolRegistry], executed: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Execute every ``function_call`` in a response and build its outputs.

    A tool failure is reported back to the model as a result rather than raised. The
    model is instructed to surface an error rather than answer around it, and that is
    a far better operator experience than a 500 — but the failure is also recorded in
    ``executed`` so the caller can tell that a number was never produced.
    """
    outputs: list[dict[str, Any]] = []
    for item in getattr(response, "output", None) or []:
        if getattr(item, "type", "") != "function_call":
            continue
        name = getattr(item, "name", "")
        call_id = getattr(item, "call_id", "")
        arguments = getattr(item, "arguments", "") or "{}"

        if registry is None:
            payload: Mapping[str, Any] = {
                "error": f"Tool {name!r} is not available in this context."
            }
            ok = False
        else:
            try:
                payload = registry.execute(name, arguments)
                ok = True
            except ToolError as exc:
                logger.warning("Agent tool %s refused: %s", name, exc)
                payload = {"error": str(exc)}
                ok = False
            except Exception as exc:
                logger.exception("Agent tool %s failed", name)
                payload = {"error": f"{type(exc).__name__}: {exc}"}
                ok = False

        executed.append({"name": name, "ok": ok, "arguments": arguments})
        outputs.append(
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(payload, default=str),
            }
        )
    return outputs


def run_web_search(question: str, limit: int = 3) -> list:
    """Run the Agent Service web-search agent for a single question.

    Used by the ``web_search`` online-search backend when Foundry IQ's web knowledge
    source is unavailable. Kept here rather than in the copilot package because it is
    an Agent Service capability, and it is deliberately a thin one-shot call: online
    search enriches an answer, it does not need a durable conversation.
    """
    status = agent_service_status()
    if not status.enabled:
        raise RuntimeError(f"Agent Service is not available: {status.reason}")

    service = FoundryAgentService(
        project_endpoint=status.project_endpoint,
        model=os.environ.get(ENV_CHAT_DEPLOYMENT, DEFAULT_MODEL),
    )
    spec = agent_spec(WEB_SEARCH_AGENT_NAME)
    service.ensure_agent(spec)
    result = service.run(question, agent_name=spec.name)

    from .copilot.online import OnlineHit

    text = result.get("answer", "")
    if not text:
        return []
    return [
        OnlineHit(
            source_id="web-1",
            title="Public web context",
            snippet=text[:600],
            url="",
        )
    ][:limit]



def agent_service_status(project: str = PROJECT_KNOWLEDGE) -> AgentServiceStatus:
    """Report whether Agent Service hosting is configured for one project."""
    if os.environ.get(ENV_AGENT_MODE, "").lower() == "local":
        return AgentServiceStatus(
            enabled=False, reason="FOUNDRY_AGENT_SERVICE_MODE=local", project=project
        )

    env_name = PROJECT_ENDPOINT_ENV.get(project)
    if env_name is None:
        return AgentServiceStatus(
            enabled=False,
            project=project,
            reason=(
                f"{project!r} is not a known Foundry project. Known: "
                f"{', '.join(sorted(PROJECT_ENDPOINT_ENV))}"
            ),
        )

    endpoint = os.environ.get(env_name, "").strip()
    if not endpoint:
        return AgentServiceStatus(
            enabled=False,
            project=project,
            reason=(
                f"{env_name} is not set — the Foundry {project} project or its "
                "capability host has not been deployed"
            ),
        )

    # Rewrites a classic `<account>.cognitiveservices.azure.com` host onto the
    # Foundry-model `<account>.services.ai.azure.com` one; a correctly configured
    # deployment is already on the latter.
    endpoint = normalize_endpoint(endpoint)
    if PROJECT_PATH_SEGMENT not in endpoint:
        # An account endpoint is not a project endpoint. AIProjectClient would accept
        # it and then fail on the first agent call with a 404, which is a much harder
        # failure to read than refusing here and staying on the local agents.
        return AgentServiceStatus(
            enabled=False,
            project=project,
            reason=(
                f"{env_name}={endpoint!r} is an account endpoint, not a "
                f"Foundry project endpoint. Expected "
                f"https://<account>.services.ai.azure.com{PROJECT_PATH_SEGMENT}<project> "
                "— the classic hub connection string is not supported."
            ),
        )
    return AgentServiceStatus(enabled=True, project_endpoint=endpoint, project=project)


def host_agents(project: str = PROJECT_KNOWLEDGE) -> AgentServiceStatus:
    """Create one project's manifest agents at startup, degrading gracefully.

    Call this once during service startup. If Agent Service is not deployed, the SDK
    is missing, or the project is unreachable, the service continues on its local
    agents and the reason is logged and returned — a demo environment with no Azure
    at all must still start.

    This is a convenience for the serving process. The authoritative path is
    :mod:`agent_reconciler`, run at release time: relying on startup alone is what
    left both deployed projects empty, because the container hosting this code was
    never deployed at all.
    """
    status = agent_service_status(project)
    if not status.enabled:
        logger.info(
            "Agent Service hosting not enabled for the %s project: %s",
            project,
            status.reason,
        )
        return status

    try:
        service = FoundryAgentService(
            project_endpoint=status.project_endpoint,
            model=os.environ.get(ENV_CHAT_DEPLOYMENT, DEFAULT_MODEL),
            knowledge_base=knowledge_base_config_from_env(),
        )
        agents = tuple(
            service.ensure_agent(spec) for spec in agents_for_project(project)
        )
        return AgentServiceStatus(
            enabled=True,
            project_endpoint=status.project_endpoint,
            agents=agents,
            project=project,
        )
    except ImportError as exc:
        logger.warning(
            "azure-ai-projects not available (%s) — agents stay local. Install the "
            "'azure' extra from the approved feed to host them in Agent Service.",
            exc,
        )
        return AgentServiceStatus(
            enabled=False, reason=f"SDK unavailable: {exc}", project=project
        )
    except Exception as exc:
        logger.warning(
            "Failed to host agents in Agent Service (%s) — agents stay local", exc
        )
        return AgentServiceStatus(enabled=False, reason=str(exc), project=project)
