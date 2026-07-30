"""Tests for the energy-dispatch agent — the language interface over the MILP.

The properties pinned here are the ones that make the capability defensible rather
than merely functional:

* the model can never obtain a number except through the optimizer;
* a forbidden tool name is refused by the registry, not by a prompt;
* an unreachable optimizer produces a decline, never an estimate;
* the Copilot panel routes dispatch *requests* and nothing else.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from knowledge_orchestrator.copilot.models import (
    ReasoningTier,
    ScreenContext,
)
from knowledge_orchestrator.copilot.service import CopilotService
from knowledge_orchestrator.energy_agent import (
    ENERGY_DISPATCH_AGENT_INSTRUCTIONS,
    ENERGY_DISPATCH_DECLINE,
    ENERGY_TOOL_SCHEMAS,
    ENV_ENERGY_AGENT_MODE,
    EnergyToolExecutor,
    LocalEnergyDispatchAgent,
    UnavailableDispatchPort,
    create_energy_dispatch_agent,
    extract_constraints,
    is_dispatch_request,
    summarize_proposal,
)
from knowledge_orchestrator.tools import ENERGY_AGENT_TOOLS, FORBIDDEN_TOOL_NAMES

PROPOSAL = {
    "recommendationId": "rec-001",
    "status": "PENDING_APPROVAL",
    "solver": "MILP_CBC",
    "hardConstraintViolations": 0,
    "baseline": {"costEur": 1000.0, "peakDemandMw": 56.0, "tonnage": 960.0},
    "optimized": {"costEur": 927.5, "peakDemandMw": 51.58, "tonnage": 960.0},
    "savings": {
        "costPct": 7.25,
        "peakPct": -7.89,
        "co2Pct": 3.29,
        "co2KgBaseline": 100000.0,
        "co2KgOptimized": 96710.0,
    },
}


class RecordingDispatchPort:
    """A port that records what it was asked and returns a fixed proposal."""

    def __init__(self, proposal: dict | None = None):
        self.calls: list[tuple[str, dict]] = []
        self._proposal = proposal or dict(PROPOSAL)

    def read_energy_context(self, *, site=""):
        self.calls.append(("read_energy_context", {"site": site}))
        return {"site": site, "intervalCount": 96}

    def forecast_demand(self, *, site="", horizon_hours):
        self.calls.append(("forecast_demand", {"site": site, "horizon_hours": horizon_hours}))
        return {"site": site, "horizonHours": horizon_hours}

    def simulate_schedule(self, *, site="", horizon_hours, scenario, constraints):
        self.calls.append(
            (
                "simulate_schedule",
                {
                    "site": site,
                    "horizon_hours": horizon_hours,
                    "scenario": scenario,
                    "constraints": dict(constraints),
                },
            )
        )
        return dict(self._proposal)

    def propose_recommendation(self, *, recommendation_id, rationale):
        self.calls.append(
            ("propose_recommendation", {"recommendation_id": recommendation_id})
        )
        return dict(self._proposal) | {"agentRationale": rationale}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in (ENV_ENERGY_AGENT_MODE, "FOUNDRY_PROJECT_ENDPOINT"):
        monkeypatch.delenv(name, raising=False)


# ---------------------------------------------------------------------------
# Tool surface
# ---------------------------------------------------------------------------


def test_tool_schemas_match_the_allow_list_exactly():
    """A tool the agent can call but the allow-list does not know about is a hole."""
    assert {schema["name"] for schema in ENERGY_TOOL_SCHEMAS} == set(ENERGY_AGENT_TOOLS)


def test_no_tool_schema_is_a_forbidden_capability():
    for schema in ENERGY_TOOL_SCHEMAS:
        assert schema["name"] not in FORBIDDEN_TOOL_NAMES


def test_no_tool_schema_requires_a_site():
    """Requiring a site invites the model to invent a plant code; the port resolves it."""
    for schema in ENERGY_TOOL_SCHEMAS:
        assert "site" not in schema["parameters"].get("required", [])


def test_every_schema_declares_json_parameters():
    for schema in ENERGY_TOOL_SCHEMAS:
        assert schema["parameters"]["type"] == "object"
        assert schema["description"]


@pytest.mark.parametrize("forbidden", sorted(FORBIDDEN_TOOL_NAMES))
def test_executor_refuses_every_forbidden_tool(forbidden):
    """Refusal comes from the registry, so no prompt can talk its way past it."""
    executor = EnergyToolExecutor(RecordingDispatchPort())
    record = executor.execute(forbidden, {"site": "esch"})
    assert record.ok is False
    assert "never agent-callable" in record.error or "allow-list" in record.error


def test_executor_refuses_an_invented_tool_name():
    executor = EnergyToolExecutor(RecordingDispatchPort())
    record = executor.execute("dispatch_now", {})
    assert record.ok is False


def test_executor_translates_camel_case_arguments():
    """Foundry sends the camelCase the schema declares; the port speaks Python."""
    port = RecordingDispatchPort()
    executor = EnergyToolExecutor(port)
    record = executor.execute(
        "simulate_schedule",
        {"site": "esch", "horizonHours": 12, "constraints": {"maxShiftMinutes": 60}},
    )
    assert record.ok is True
    name, args = port.calls[-1]
    assert name == "simulate_schedule"
    assert args["horizon_hours"] == 12
    assert args["constraints"] == {"maxShiftMinutes": 60}


def test_executor_returns_json_for_the_agent_service_tool_loop():
    executor = EnergyToolExecutor(RecordingDispatchPort())
    payload = json.loads(executor.execute_as_json("simulate_schedule", {"site": "esch"}))
    assert payload["recommendationId"] == "rec-001"


def test_tool_error_is_returned_to_the_model_as_structured_json():
    """A model told nothing improvises; a model told 'unavailable' declines."""
    executor = EnergyToolExecutor(UnavailableDispatchPort())
    payload = json.loads(executor.execute_as_json("simulate_schedule", {"site": "esch"}))
    assert payload["ok"] is False
    assert payload["error"]


def test_propose_requires_a_recommendation_id_from_a_prior_simulation():
    executor = EnergyToolExecutor(RecordingDispatchPort())
    record = executor.execute("propose_recommendation", {"rationale": "cheaper"})
    assert record.ok is False


def test_executor_trace_is_bounded():
    """The executor lives as long as the process; an unbounded trace is a slow leak."""
    from knowledge_orchestrator.energy_agent import MAX_RETAINED_CALLS

    executor = EnergyToolExecutor(RecordingDispatchPort())
    for _ in range(MAX_RETAINED_CALLS + 20):
        executor.execute("read_energy_context", {})
    assert len(executor.calls) == MAX_RETAINED_CALLS


def test_record_serialises_a_failure_as_data_not_silence():
    executor = EnergyToolExecutor(UnavailableDispatchPort())
    record = executor.execute("simulate_schedule", {})
    assert json.loads(record.as_json()) == {"error": record.error, "ok": False}


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------


def test_instructions_forbid_the_model_computing_a_schedule():
    text = ENERGY_DISPATCH_AGENT_INSTRUCTIONS.lower()
    assert "never produce a schedule" in text
    assert "verbatim from a tool result" in text
    assert "you may not approve, commit or dispatch" in text
    assert "milp_cbc" in text
    assert "deterministic_heuristic" in text


# ---------------------------------------------------------------------------
# Local agent — the deterministic path
# ---------------------------------------------------------------------------


def test_local_agent_answers_only_from_the_solver():
    agent = LocalEnergyDispatchAgent(RecordingDispatchPort())
    result = agent.answer("Can we optimize energy cost tonight?")
    assert result.grounded is True
    assert result.recommendation_id == "rec-001"
    assert "7.25" in result.answer
    assert "3.29" in result.answer


def test_local_agent_declines_when_the_optimizer_is_unreachable():
    agent = LocalEnergyDispatchAgent(UnavailableDispatchPort())
    result = agent.answer("Can we shift load to cut cost?")
    assert result.grounded is False
    assert result.answer == ENERGY_DISPATCH_DECLINE
    # No invented figure survives the decline.
    assert "%" not in result.answer


def test_local_agent_passes_the_planner_constraint_to_the_solver():
    port = RecordingDispatchPort()
    LocalEnergyDispatchAgent(port).answer(
        "Optimize the energy schedule but don't shift anything more than 60 minutes"
    )
    _, args = port.calls[-1]
    assert args["constraints"]["maxShiftMinutes"] == 60


def test_local_agent_leaves_site_resolution_to_the_port():
    """No plant identifier is fabricated in the orchestrator."""
    port = RecordingDispatchPort()
    LocalEnergyDispatchAgent(port).answer("Optimize the energy schedule")
    _, args = port.calls[-1]
    assert args["site"] == ""


def test_summary_flags_a_heuristic_fallback_as_not_proven_optimal():
    text = summarize_proposal(dict(PROPOSAL) | {"solver": "DETERMINISTIC_HEURISTIC"})
    assert "not proven" in text.lower()
    assert "PENDING_APPROVAL" in text


def test_summary_claims_optimality_only_for_the_milp():
    assert "proven cheapest" in summarize_proposal(PROPOSAL)


def test_summary_states_the_direction_of_every_delta():
    """peakPct is negative for an improvement; cost/CO2 are positive. Say which."""
    text = summarize_proposal(PROPOSAL)
    assert "7.25% (better)" in text
    assert "-7.89% (better)" in text  # peak fell 56.0 -> 51.58
    assert "3.29% (better)" in text


def test_summary_marks_a_regression_as_worse():
    worse = dict(PROPOSAL) | {"savings": dict(PROPOSAL["savings"]) | {"peakPct": 4.2}}
    assert "4.2% (worse)" in summarize_proposal(worse)


def test_summary_always_states_the_human_gate():
    text = summarize_proposal(PROPOSAL)
    assert "proposal only" in text
    assert "synthetic" in text.lower()


# ---------------------------------------------------------------------------
# Constraint extraction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("shift batches by at most 90 minutes", {"maxShiftMinutes": 90}),
        ("don't move anything more than 2 hours", {"maxShiftMinutes": 120}),
        ("decaler les coulees de 45 minutes maximum", {"maxShiftMinutes": 45}),
        ("optimize energy cost", {}),
    ],
)
def test_extract_constraints(question, expected):
    assert extract_constraints(question) == expected


def test_extract_constraints_reads_concurrency():
    assert extract_constraints("run at most 2 batches at a time while shifting") == {
        "maxConcurrentBatches": 2
    }


def test_no_constraint_is_invented_when_none_was_stated():
    """An invented limit would silently change the optimum without telling anybody."""
    assert extract_constraints("what can we save tonight?") == {}


# ---------------------------------------------------------------------------
# Intent routing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "question",
    [
        "Can we optimize the energy schedule tonight?",
        "Simulate shifting the reheat batches into the cheap window",
        "Comment reduire le cout energie de cette nuit ?",
        "Wie koennen wir den Stromverbrauch senken?",
        "Kunnen we het stroomverbruik verlagen?",
    ],
)
def test_dispatch_requests_are_routed(question):
    assert is_dispatch_request(question) is True


@pytest.mark.parametrize(
    "question",
    [
        "What does CO2 intensity mean?",
        "Qu'est-ce que le carbone du reseau ?",
        "Who approved this recommendation?",
        "",
    ],
)
def test_definitions_and_lookups_are_not_routed(question):
    assert is_dispatch_request(question) is False


def test_screen_context_routes_a_bare_action_question():
    assert is_dispatch_request("Can we optimize this?", section="energy-optimization")
    assert not is_dispatch_request("Can we optimize this?", section="furnace-health")


def test_routing_can_be_switched_off(monkeypatch):
    monkeypatch.setenv(ENV_ENERGY_AGENT_MODE, "off")
    assert is_dispatch_request("Can we optimize the energy schedule?") is False


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def test_factory_returns_the_local_agent_without_a_project_endpoint():
    agent = create_energy_dispatch_agent(RecordingDispatchPort())
    assert isinstance(agent, LocalEnergyDispatchAgent)


def test_factory_honours_an_explicit_local_override(monkeypatch):
    monkeypatch.setenv(
        "FOUNDRY_PROJECT_ENDPOINT", "https://x.services.ai.azure.com/api/projects/p"
    )
    monkeypatch.setenv(ENV_ENERGY_AGENT_MODE, "local")
    assert isinstance(
        create_energy_dispatch_agent(RecordingDispatchPort()), LocalEnergyDispatchAgent
    )


def test_hosted_agent_is_built_when_agent_service_is_configured(monkeypatch):
    monkeypatch.setenv(
        "FOUNDRY_PROJECT_ENDPOINT", "https://x.services.ai.azure.com/api/projects/p"
    )
    agent = create_energy_dispatch_agent(RecordingDispatchPort())
    assert agent.agent_name == "energy-dispatch-foundry"


def test_hosted_agent_falls_back_to_the_deterministic_answer(monkeypatch):
    """A Foundry outage must degrade the prose, not the capability."""
    monkeypatch.setenv(
        "FOUNDRY_PROJECT_ENDPOINT", "https://x.services.ai.azure.com/api/projects/p"
    )
    port = RecordingDispatchPort()
    agent = create_energy_dispatch_agent(port)
    # No azure-ai-projects installed in the test environment, so _run raises and the
    # local fallback answers with the real solver output.
    result = agent.answer("Optimize the energy schedule tonight")
    assert result.grounded is True
    assert result.agent == "energy-dispatch-foundry"
    assert "7.25" in result.answer


# ---------------------------------------------------------------------------
# Hosted tool loop
# ---------------------------------------------------------------------------


class _FakeAgentsClient:
    """Minimal stand-in for the Agent Service data plane.

    Serves one `requires_action` turn asking for `tool_calls`, then completes with
    `reply` as the assistant message.
    """

    def __init__(self, tool_calls, reply="Here is the schedule.", status_after="completed"):
        self._tool_calls = tool_calls
        self._reply = reply
        self._status_after = status_after
        self.submitted: list[list[dict]] = []
        self.threads = self
        self.messages = self
        self.runs = self

    # threads / messages
    def create(self, **kwargs):
        if "thread_id" in kwargs:
            return SimpleNamespace(id="msg-1")
        return SimpleNamespace(id="thread-1")

    def list(self, **_):
        return [SimpleNamespace(role="assistant", content=self._reply)]

    # runs
    def get(self, **_):
        return self._run

    def submit_tool_outputs(self, *, thread_id, run_id, tool_outputs):
        self.submitted.append(tool_outputs)
        self._run = SimpleNamespace(id="run-1", status=self._status_after)
        return self._run

    def __call__(self, **_):
        return self


def _fake_call(name, arguments):
    return SimpleNamespace(
        id=f"call-{name}",
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


def _hosted_agent(port, client):
    from knowledge_orchestrator.agent_service import HostedEnergyDispatchAgent

    agent = HostedEnergyDispatchAgent(
        "https://x.services.ai.azure.com/api/projects/p", port=port
    )
    agent._ensured = True
    agent._service._project_client = lambda: SimpleNamespace(agents=client)
    return agent


def _requires_action_run(tool_calls):
    return SimpleNamespace(
        id="run-1",
        status="requires_action",
        required_action=SimpleNamespace(
            submit_tool_outputs=SimpleNamespace(tool_calls=tool_calls)
        ),
    )


def test_hosted_loop_executes_the_requested_tool_and_grounds_the_answer(monkeypatch):
    monkeypatch.setenv(
        "FOUNDRY_PROJECT_ENDPOINT", "https://x.services.ai.azure.com/api/projects/p"
    )
    port = RecordingDispatchPort()
    client = _FakeAgentsClient([_fake_call("simulate_schedule", {"horizonHours": 24})])
    agent = _hosted_agent(port, client)
    # runs.create returns the paused run.
    client.create = lambda **kwargs: (
        _requires_action_run(client._tool_calls)
        if "agent_name" in kwargs
        else SimpleNamespace(id="thread-1")
    )

    result = agent.answer("Optimize the energy schedule")

    assert result.grounded is True
    assert result.recommendation_id == "rec-001"
    assert result.answer == "Here is the schedule."
    assert port.calls[-1][0] == "simulate_schedule"
    assert json.loads(client.submitted[0][0]["output"])["recommendationId"] == "rec-001"


def test_hosted_loop_refuses_a_forbidden_tool_without_touching_the_port(monkeypatch):
    """The registry, not the prompt, is what stops `commit_schedule`."""
    monkeypatch.setenv(
        "FOUNDRY_PROJECT_ENDPOINT", "https://x.services.ai.azure.com/api/projects/p"
    )
    port = RecordingDispatchPort()
    client = _FakeAgentsClient([_fake_call("commit_schedule", {})])
    agent = _hosted_agent(port, client)
    client.create = lambda **kwargs: (
        _requires_action_run(client._tool_calls)
        if "agent_name" in kwargs
        else SimpleNamespace(id="thread-1")
    )

    result = agent.answer("Commit tonight's schedule")

    assert port.calls == []
    assert result.grounded is False
    assert json.loads(client.submitted[0][0]["output"])["ok"] is False


def test_hosted_run_never_reuses_a_previous_turn_s_proposal(monkeypatch):
    """A failed solve must not inherit the last question's schedule and look grounded."""
    monkeypatch.setenv(
        "FOUNDRY_PROJECT_ENDPOINT", "https://x.services.ai.azure.com/api/projects/p"
    )
    port = RecordingDispatchPort()
    client = _FakeAgentsClient([_fake_call("simulate_schedule", {})])
    agent = _hosted_agent(port, client)
    client.create = lambda **kwargs: (
        _requires_action_run(client._tool_calls)
        if "agent_name" in kwargs
        else SimpleNamespace(id="thread-1")
    )

    first = agent.answer("Optimize the energy schedule")
    assert first.grounded is True

    # Second turn: the optimizer has gone away.
    agent._executor.port = UnavailableDispatchPort()
    agent._fallback._executor.port = UnavailableDispatchPort()
    second = agent.answer("Optimize the energy schedule again")

    assert second.grounded is False
    assert second.proposal == {}


# ---------------------------------------------------------------------------
# Copilot panel connectivity
# ---------------------------------------------------------------------------



class _StubChatAgent:
    agent_name = "stub-chat"

    def __init__(self):
        self.seen: list[str] = []

    def answer(self, request):
        from knowledge_orchestrator.copilot.models import ChatTurnResult

        self.seen.append(request.question)
        return ChatTurnResult(answer="chat answer", agent=self.agent_name)


def _service(energy_agent=None):
    chat = _StubChatAgent()
    service = CopilotService(
        agents={ReasoningTier.DEFAULT: chat, ReasoningTier.HIGH: chat},
        energy_agent=energy_agent,
    )
    return service, chat


def test_copilot_routes_a_dispatch_question_to_the_energy_agent():
    service, chat = _service(LocalEnergyDispatchAgent(RecordingDispatchPort()))
    response = service.chat(
        owner="planner@novasteel.test",
        question="Can we optimize the energy schedule tonight?",
        temporary=True,
        context=ScreenContext(site="esch", section="energy-optimization"),
    )
    assert "7.25" in response.answer.content
    assert response.answer.agent == "energy-dispatch-local"
    assert chat.seen == []  # the chat agent was never consulted


def test_copilot_cites_the_proposal_behind_a_routed_answer():
    service, _ = _service(LocalEnergyDispatchAgent(RecordingDispatchPort()))
    response = service.chat(
        owner="planner@novasteel.test",
        question="Simulate shifting load to cut energy cost",
        temporary=True,
        context=ScreenContext(site="esch", section="energy-optimization"),
    )
    sources = response.answer.sources
    assert len(sources) == 1
    assert sources[0].source_id == "rec-001"
    assert "MILP_CBC" in sources[0].snippet


def test_copilot_keeps_definitions_on_the_chat_agent():
    service, chat = _service(LocalEnergyDispatchAgent(RecordingDispatchPort()))
    response = service.chat(
        owner="planner@novasteel.test",
        question="What does grid carbon intensity mean?",
        temporary=True,
        context=ScreenContext(site="esch", section="energy-optimization"),
    )
    assert response.answer.content == "chat answer"
    assert len(chat.seen) == 1


def test_copilot_falls_back_to_chat_when_the_optimizer_is_unreachable():
    """An ungrounded dispatch answer is worth less than a grounded chat answer."""
    service, chat = _service(LocalEnergyDispatchAgent(UnavailableDispatchPort()))
    response = service.chat(
        owner="planner@novasteel.test",
        question="Can we optimize the energy schedule tonight?",
        temporary=True,
        context=ScreenContext(site="esch", section="energy-optimization"),
    )
    assert response.answer.content == "chat answer"
    assert len(chat.seen) == 1


def test_copilot_without_a_bound_agent_behaves_exactly_as_before():
    service, chat = _service(None)
    response = service.chat(
        owner="planner@novasteel.test",
        question="Can we optimize the energy schedule tonight?",
        temporary=True,
        context=ScreenContext(site="esch", section="energy-optimization"),
    )
    assert response.answer.content == "chat answer"
    assert len(chat.seen) == 1


def test_bind_energy_agent_enables_routing_after_construction():
    service, _ = _service(None)
    service.bind_energy_agent(LocalEnergyDispatchAgent(RecordingDispatchPort()))
    response = service.chat(
        owner="planner@novasteel.test",
        question="Optimize the energy schedule",
        temporary=True,
        context=ScreenContext(site="esch", section="energy-optimization"),
    )
    assert "7.25" in response.answer.content
