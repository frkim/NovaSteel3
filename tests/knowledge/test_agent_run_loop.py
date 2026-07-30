"""Tests for the Responses-API run loop that executes agent tool calls.

Two things are worth pinning here. The first is the loop itself: Foundry returns a
``function_call`` item, our process executes it locally and resubmits a
``function_call_output``, and the answer is whatever the model says once it has the
result. The second is what happens when that goes wrong -- a refused or failing tool
must come back to the model as a result it has to account for, never as an exception
that ends the operator's turn.

The SDK is faked rather than mocked at the transport layer, because what is being
tested is our loop, not the wire format.
"""

from __future__ import annotations

import importlib.util
import json

import pytest

from knowledge_orchestrator.agent_manifest import (
    ENERGY_ADVISOR_AGENT_NAME,
    agent_spec,
)
from knowledge_orchestrator.agent_service import (
    MAX_TOOL_ITERATIONS,
    FoundryAgentService,
)
from knowledge_orchestrator.agent_tools import ToolError, ToolRegistry

ENDPOINT = "https://x.services.ai.azure.com/api/projects/p"

# Building an SDK `FunctionTool` needs the optional `azure` extra, which the
# offline suite does not install. Only the assertions that reach that call skip.
requires_sdk = pytest.mark.skipif(
    importlib.util.find_spec("azure.ai.projects") is None,
    reason="azure-ai-projects is an optional extra; the SDK object cannot be built without it",
)


class _FunctionCall:
    type = "function_call"

    def __init__(self, name: str, call_id: str, arguments: str):
        self.name = name
        self.call_id = call_id
        self.arguments = arguments


class _Response:
    def __init__(self, output=(), output_text: str = "", response_id: str = "resp-1"):
        self.output = list(output)
        self.output_text = output_text
        self.id = response_id


class _Conversations:
    def __init__(self):
        self.created = 0
        self.deleted: list[str] = []

    def create(self):
        self.created += 1
        return type("Conv", (), {"id": f"conv-{self.created}"})()

    def delete(self, conversation_id: str):
        self.deleted.append(conversation_id)


class _Responses:
    def __init__(self, script):
        self._script = list(script)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._script:
            return self._script.pop(0)
        return _Response(output_text="done")


class _FakeOpenAI:
    def __init__(self, script):
        self.conversations = _Conversations()
        self.responses = _Responses(script)


def _service(script) -> tuple[FoundryAgentService, _FakeOpenAI]:
    service = FoundryAgentService(project_endpoint=ENDPOINT, credential=object())
    fake = _FakeOpenAI(script)
    service._openai = fake
    return service, fake


def _dispatch_call(site="NS-DEMO-LUX-01"):
    return _FunctionCall(
        "simulate_energy_dispatch",
        "call-1",
        json.dumps(
            {
                "site": site,
                "horizonHours": 24,
                "scenario": "baseline",
                "maxShiftMinutes": 120,
            }
        ),
    )


def test_a_plain_answer_needs_no_tool_round_trip():
    service, fake = _service([_Response(output_text="Hello.")])
    result = service.run("hi", ENERGY_ADVISOR_AGENT_NAME)
    assert result["answer"] == "Hello."
    assert result["tool_calls"] == ()
    assert len(fake.responses.calls) == 1


def test_a_function_call_is_executed_locally_and_resubmitted():
    service, fake = _service(
        [
            _Response(output=[_dispatch_call()]),
            _Response(output_text="Shifting saves 4.2 MWh. This is a proposal."),
        ]
    )
    executed = []

    def _impl(arguments):
        executed.append(arguments)
        return {"savings": {"energyMwh": 4.2}, "modelVersion": "2.1.0"}

    registry = ToolRegistry().register("simulate_energy_dispatch", _impl)

    result = service.run("what if", ENERGY_ADVISOR_AGENT_NAME, registry=registry)

    assert executed == [
        {
            "site": "NS-DEMO-LUX-01",
            "horizonHours": 24,
            "scenario": "baseline",
            "maxShiftMinutes": 120,
        }
    ]
    assert result["answer"].startswith("Shifting saves 4.2")
    assert result["tool_calls"][0]["name"] == "simulate_energy_dispatch"
    assert result["tool_calls"][0]["ok"] is True

    resubmitted = fake.responses.calls[1]["input"]
    assert resubmitted[0]["type"] == "function_call_output"
    assert resubmitted[0]["call_id"] == "call-1"
    assert json.loads(resubmitted[0]["output"])["savings"]["energyMwh"] == 4.2


def test_every_turn_carries_the_agent_reference():
    """Without it the request runs against the bare model, tool-less and
    instruction-less, which would answer plausibly and wrongly."""
    service, fake = _service(
        [_Response(output=[_dispatch_call()]), _Response(output_text="ok")]
    )
    registry = ToolRegistry().register("simulate_energy_dispatch", lambda a: {})
    service.run("q", ENERGY_ADVISOR_AGENT_NAME, registry=registry)

    for call in fake.responses.calls:
        reference = call["extra_body"]["agent_reference"]
        assert reference["name"] == ENERGY_ADVISOR_AGENT_NAME
        assert reference["type"] == "agent_reference"


def test_a_conversation_is_created_once_and_reused_across_the_loop():
    service, fake = _service(
        [_Response(output=[_dispatch_call()]), _Response(output_text="ok")]
    )
    registry = ToolRegistry().register("simulate_energy_dispatch", lambda a: {})
    result = service.run("q", ENERGY_ADVISOR_AGENT_NAME, registry=registry)

    assert fake.conversations.created == 1
    assert result["conversation_id"] == "conv-1"
    assert {call["conversation"] for call in fake.responses.calls} == {"conv-1"}


def test_an_existing_conversation_is_continued_not_recreated():
    """Server-side conversation state is why a follow-up question does not have to
    resend the transcript."""
    service, fake = _service([_Response(output_text="ok")])
    result = service.run("q", ENERGY_ADVISOR_AGENT_NAME, conversation_id="conv-existing")

    assert fake.conversations.created == 0
    assert result["conversation_id"] == "conv-existing"


def test_a_refused_tool_is_reported_to_the_model_not_raised():
    """An authorization refusal must read as "I cannot get that" inside the answer,
    not as a 500 in the middle of a chat turn."""
    service, fake = _service(
        [
            _Response(output=[_dispatch_call(site="NS-DEMO-OTHER")]),
            _Response(output_text="You do not have access to that plant."),
        ]
    )

    def _refuse(arguments):
        raise ToolError("You do not have access to plant NS-DEMO-OTHER.")

    registry = ToolRegistry().register("simulate_energy_dispatch", _refuse)
    result = service.run("q", ENERGY_ADVISOR_AGENT_NAME, registry=registry)

    assert result["tool_calls"][0]["ok"] is False
    payload = json.loads(fake.responses.calls[1]["input"][0]["output"])
    assert "NS-DEMO-OTHER" in payload["error"]
    assert result["answer"] == "You do not have access to that plant."


def test_an_unexpected_tool_failure_is_also_reported_not_raised():
    service, fake = _service(
        [_Response(output=[_dispatch_call()]), _Response(output_text="Sorry.")]
    )

    def _explode(arguments):
        raise ZeroDivisionError("boom")

    registry = ToolRegistry().register("simulate_energy_dispatch", _explode)
    result = service.run("q", ENERGY_ADVISOR_AGENT_NAME, registry=registry)

    assert result["tool_calls"][0]["ok"] is False
    payload = json.loads(fake.responses.calls[1]["input"][0]["output"])
    assert "ZeroDivisionError" in payload["error"]


def test_a_tool_call_with_no_registry_is_refused():
    """The knowledge agents run with no registry. If one ever emitted a function
    call it must be told the tool does not exist, not handed a plausible answer."""
    service, fake = _service(
        [_Response(output=[_dispatch_call()]), _Response(output_text="I cannot.")]
    )
    result = service.run("q", ENERGY_ADVISOR_AGENT_NAME)

    assert result["tool_calls"][0]["ok"] is False
    payload = json.loads(fake.responses.calls[1]["input"][0]["output"])
    assert "not available" in payload["error"]


def test_the_loop_is_bounded():
    """A model that keeps calling a tool must not keep the request open forever."""
    service, fake = _service(
        [_Response(output=[_dispatch_call()]) for _ in range(MAX_TOOL_ITERATIONS + 5)]
    )
    calls = []
    registry = ToolRegistry().register(
        "simulate_energy_dispatch", lambda a: calls.append(a) or {}
    )

    service.run("q", ENERGY_ADVISOR_AGENT_NAME, registry=registry)

    assert len(calls) == MAX_TOOL_ITERATIONS


def test_non_function_output_items_are_ignored():
    """Reasoning and message items share the output list with function calls."""
    other = type("Item", (), {"type": "message"})()
    service, _ = _service([_Response(output=[other], output_text="Just prose.")])
    result = service.run("q", ENERGY_ADVISOR_AGENT_NAME)
    assert result["answer"] == "Just prose."
    assert result["tool_calls"] == ()


def test_delete_conversation_reaches_the_server_side_store():
    """GDPR erasure: once conversations live in Agent Service, forgetting an
    operator means deleting theirs there."""
    service, fake = _service([])
    service.delete_conversation("conv-9")
    assert fake.conversations.deleted == ["conv-9"]


def test_resolve_tools_drops_a_function_tool_with_no_implementation():
    """Serving a request must declare only what this process can execute."""
    service, _ = _service([])
    spec = agent_spec(ENERGY_ADVISOR_AGENT_NAME)
    _, names = service._resolve_tools(spec, ToolRegistry())
    assert names == ()


@requires_sdk
def test_resolve_tools_declares_every_function_tool_when_reconciling():
    """A definition must describe the agent as deployed, not as one process happens
    to be configured, so reconciliation passes no registry."""
    service, _ = _service([])
    spec = agent_spec(ENERGY_ADVISOR_AGENT_NAME)
    _, names = service._resolve_tools(spec, None)
    assert names == ("simulate_energy_dispatch",)


@pytest.mark.parametrize("blank", ["", "   ", None])
def test_a_blank_answer_is_normalised(blank):
    service, _ = _service([_Response(output_text=blank)])
    assert service.run("q", ENERGY_ADVISOR_AGENT_NAME)["answer"] == ""
