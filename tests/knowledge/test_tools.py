import pytest

from knowledge_orchestrator import tools as t


def test_knowledge_agent_allows_only_two_tools():
    reg = t.ToolRegistry("knowledge-capture")
    assert reg.is_allowed("search_approved_procedures")
    assert reg.is_allowed("write_draft_procedure")
    assert not reg.is_allowed("propose_recommendation")


def test_energy_agent_allowlist():
    reg = t.ToolRegistry("energy-dispatch")
    for name in ("read_energy_context", "forecast_demand", "simulate_schedule", "propose_recommendation"):
        assert reg.is_allowed(name)


def test_forbidden_tools_never_allowed():
    reg = t.ToolRegistry("knowledge-capture")
    for name in t.FORBIDDEN_TOOL_NAMES:
        assert not reg.is_allowed(name)
        with pytest.raises(t.ToolNotAllowed):
            reg.call(name)


def test_publish_and_approve_rejected_for_energy_agent():
    reg = t.ToolRegistry("energy-dispatch")
    with pytest.raises(t.ToolNotAllowed):
        reg.call("approve_recommendation")
    with pytest.raises(t.ToolNotAllowed):
        reg.call("commit_schedule")


def test_register_and_call_allowed_tool():
    reg = t.ToolRegistry("knowledge-capture")
    reg.register("search_approved_procedures", lambda q: [f"hit:{q}"])
    assert reg.call("search_approved_procedures", q="hearth") == ["hit:hearth"]


def test_register_forbidden_raises():
    reg = t.ToolRegistry("knowledge-capture")
    with pytest.raises(t.ToolNotAllowed):
        reg.register("approve_procedure", lambda: None)


def test_unknown_agent_rejected():
    with pytest.raises(t.ToolNotAllowed):
        t.ToolRegistry("some-random-agent")


def test_call_out_of_allowlist_raises():
    reg = t.ToolRegistry("knowledge-capture")
    with pytest.raises(t.ToolNotAllowed):
        reg.call("simulate_schedule")
