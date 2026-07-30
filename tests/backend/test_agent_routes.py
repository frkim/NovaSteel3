"""Route-level behaviour for the tool-calling operations agents.

``/v1/copilot/agent`` is deliberately a different endpoint from
``/v1/copilot/chat``. Chat is the grounded answering surface that has no tools
(ADR-011); this one reaches agents that can call the deterministic NovaSteel
calculations. These tests pin the two things a caller can observe without a
Foundry project: the roster the UI renders from, and what happens when the
operations project is not deployed.
"""

from __future__ import annotations

import pytest

from bff_api.agent_adapter import _decode_arguments


@pytest.fixture
def unconfigured(monkeypatch):
    """Guarantee the operations project looks absent regardless of the shell."""
    monkeypatch.delenv("FOUNDRY_OPERATIONS_PROJECT_ENDPOINT", raising=False)


def test_the_roster_lists_only_operations_agents(client, admin_headers, unconfigured):
    """The knowledge agents live in the other project and cannot be asked here."""
    response = client.get("/v1/copilot/agents", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    names = {agent["name"] for agent in data["agents"]}
    assert names == {"novasteel-energy-advisor", "novasteel-maintenance-advisor"}
    assert "novasteel-procedure-agent" not in names


def test_every_rostered_agent_declares_its_tools(client, admin_headers, unconfigured):
    """An operations agent with no tools would just be a chat agent in the project
    that is allowed to call things, which is the shape we are avoiding."""
    data = client.get("/v1/copilot/agents", headers=admin_headers).json()["data"]
    for agent in data["agents"]:
        assert agent["tools"], f"{agent['name']} declares no tools"
        assert agent["description"]


def test_the_roster_reports_whether_the_project_is_deployed(
    client, admin_headers, unconfigured
):
    """The roster comes from the manifest, so it is answerable even when nothing is
    deployed. ``configured`` is how the UI knows not to offer the ask box."""
    data = client.get("/v1/copilot/agents", headers=admin_headers).json()["data"]
    assert data["configured"] is False
    assert data["agents"]


def test_asking_without_the_operations_project_fails_loudly(
    client, admin_headers, unconfigured
):
    """No silent fallback to the knowledge project: that project reads untrusted
    content, so borrowing it would hand tool access across the trust boundary."""
    response = client.post(
        "/v1/copilot/agent",
        headers=admin_headers,
        json={"question": "What is the cheapest dispatch for tomorrow?"},
    )
    assert response.status_code == 503
    assert response.json()["code"] == "UPSTREAM_UNAVAILABLE"


def test_an_unknown_agent_is_rejected_before_any_upstream_call(
    client, admin_headers, unconfigured
):
    """Ordering matters only cosmetically here, but a 503 for a typo would send an
    operator looking at the wrong problem."""
    response = client.post(
        "/v1/copilot/agent",
        headers=admin_headers,
        json={"question": "hello", "agent": "novasteel-nonexistent"},
    )
    assert response.status_code in (404, 503)


def test_the_question_is_required(client, admin_headers, unconfigured):
    response = client.post("/v1/copilot/agent", headers=admin_headers, json={})
    assert response.status_code == 400


def test_unexpected_body_keys_are_refused(client, admin_headers, unconfigured):
    """The endpoint takes a question, not a free-form payload that could smuggle
    tool arguments past the authorization layer."""
    response = client.post(
        "/v1/copilot/agent",
        headers=admin_headers,
        json={"question": "hi", "site": "NS-DEMO-OTHER-01"},
    )
    assert response.status_code == 400


def test_the_roster_requires_authentication(client):
    assert client.get("/v1/copilot/agents").status_code == 401


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('{"site": "NS-DEMO-LUX-01"}', {"site": "NS-DEMO-LUX-01"}),
        ({"site": "x"}, {"site": "x"}),
        ("not json", {}),
        ("[1, 2]", {}),
        (None, {}),
    ],
)
def test_tool_arguments_are_echoed_but_never_trusted_to_parse(raw, expected):
    """Surfacing what the agent asked for is the point of returning tool calls, but
    the model produces that string, so a malformed one must not fail the request."""
    assert _decode_arguments(raw) == expected
