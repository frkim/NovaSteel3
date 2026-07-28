"""Tests for the GPT-5 reasoning tiers and the online-search backend selection.

Two behaviours matter here and neither is visible from the outside:

* "High reasoning" must be a genuinely different deployment *and* a genuinely
  larger reasoning budget, not a prompt tweak.
* The online-search toggle must fail closed — misconfiguration keeps operator
  questions inside the curated corpus rather than sending them to the public web.
"""

from __future__ import annotations

import pytest

from knowledge_orchestrator.copilot.agents import (
    DEFAULT_CHAT_DEPLOYMENT,
    DEFAULT_REASONING_DEPLOYMENT,
    ENV_DEPLOYMENT_DEFAULT,
    ENV_DEPLOYMENT_HIGH,
    ENV_ENDPOINT,
    ENV_MODE,
    MAX_COMPLETION_TOKENS_BY_TIER,
    REASONING_EFFORT_BY_TIER,
    AzureFoundryChatAgent,
    LocalCopilotChatAgent,
    _deployment_for,
    create_chat_agents,
)
from knowledge_orchestrator.copilot.models import ReasoningTier
from knowledge_orchestrator.copilot.online_provider import (
    CuratedOnlineSearchProvider,
    WebIQOnlineSearchProvider,
    WebSearchToolProvider,
    _hits_from_references,
    create_online_search_provider,
)
from knowledge_orchestrator.foundry_iq import (
    ENV_ONLINE_SEARCH_MODE,
    ONLINE_MODE_WEB_IQ,
    ONLINE_MODE_WEB_SEARCH,
)
from knowledge_orchestrator.search_store import ENV_SEARCH_ENDPOINT


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in (
        ENV_ENDPOINT,
        ENV_MODE,
        ENV_DEPLOYMENT_DEFAULT,
        ENV_DEPLOYMENT_HIGH,
        ENV_ONLINE_SEARCH_MODE,
        ENV_SEARCH_ENDPOINT,
    ):
        monkeypatch.delenv(name, raising=False)


# ---------------------------------------------------------------------------
# Model selection
# ---------------------------------------------------------------------------


def test_defaults_are_five_series_models():
    assert DEFAULT_CHAT_DEPLOYMENT.startswith("gpt-5")
    assert "mini" in DEFAULT_CHAT_DEPLOYMENT
    assert DEFAULT_REASONING_DEPLOYMENT.startswith("gpt-5")
    # The high tier must not silently reuse the mini model.
    assert DEFAULT_REASONING_DEPLOYMENT != DEFAULT_CHAT_DEPLOYMENT
    assert "mini" not in DEFAULT_REASONING_DEPLOYMENT


def test_tier_selects_a_different_deployment():
    assert _deployment_for(ReasoningTier.DEFAULT) == DEFAULT_CHAT_DEPLOYMENT
    assert _deployment_for(ReasoningTier.HIGH) == DEFAULT_REASONING_DEPLOYMENT


def test_deployment_names_are_overridable(monkeypatch):
    monkeypatch.setenv(ENV_DEPLOYMENT_DEFAULT, "gpt-5-mini")
    monkeypatch.setenv(ENV_DEPLOYMENT_HIGH, "gpt-5")
    assert _deployment_for(ReasoningTier.DEFAULT) == "gpt-5-mini"
    assert _deployment_for(ReasoningTier.HIGH) == "gpt-5"


# ---------------------------------------------------------------------------
# Reasoning effort
# ---------------------------------------------------------------------------


def test_high_tier_gets_a_larger_reasoning_budget():
    agent_default = AzureFoundryChatAgent(
        tier=ReasoningTier.DEFAULT, endpoint="https://foundry.example"
    )
    agent_high = AzureFoundryChatAgent(
        tier=ReasoningTier.HIGH, endpoint="https://foundry.example"
    )

    assert agent_default.reasoning_effort == "minimal"
    assert agent_high.reasoning_effort == "high"
    assert agent_high.max_completion_tokens > agent_default.max_completion_tokens


@pytest.mark.parametrize("tier", [ReasoningTier.DEFAULT, ReasoningTier.HIGH])
def test_request_body_uses_max_completion_tokens_and_effort(tier):
    """5-series models reject `max_tokens`; reasoning tokens share the budget."""
    agent = AzureFoundryChatAgent(tier=tier, endpoint="https://foundry.example")
    body = agent._request_body("system prompt", "user question")

    assert "max_tokens" not in body
    assert body["max_completion_tokens"] == MAX_COMPLETION_TOKENS_BY_TIER[tier.value]
    assert body["reasoning_effort"] == REASONING_EFFORT_BY_TIER[tier.value]
    assert body["messages"][0]["role"] == "system"
    assert body["messages"][1]["content"] == "user question"


def test_effort_values_are_valid_for_the_five_series():
    valid = {"none", "minimal", "low", "medium", "high", "xhigh"}
    assert set(REASONING_EFFORT_BY_TIER.values()) <= valid


def test_create_chat_agents_wires_both_tiers(monkeypatch):
    monkeypatch.setenv(ENV_ENDPOINT, "https://foundry.example")
    agents = create_chat_agents()

    assert agents[ReasoningTier.DEFAULT].deployment == DEFAULT_CHAT_DEPLOYMENT
    assert agents[ReasoningTier.HIGH].deployment == DEFAULT_REASONING_DEPLOYMENT
    assert agents[ReasoningTier.HIGH].reasoning_effort == "high"


def test_create_chat_agents_stays_local_without_endpoint():
    agents = create_chat_agents()
    assert all(isinstance(a, LocalCopilotChatAgent) for a in agents.values())


# ---------------------------------------------------------------------------
# Online search backend selection
# ---------------------------------------------------------------------------


def test_online_provider_defaults_to_the_curated_corpus():
    provider = create_online_search_provider()
    assert isinstance(provider, CuratedOnlineSearchProvider)
    assert provider.mode == "offline"


def test_web_iq_requires_search_to_be_configured(monkeypatch):
    """Asking for Web IQ without AI Search must not leave the toggle broken."""
    monkeypatch.setenv(ENV_ONLINE_SEARCH_MODE, ONLINE_MODE_WEB_IQ)
    assert isinstance(create_online_search_provider(), CuratedOnlineSearchProvider)


def test_web_iq_selected_when_fully_configured(monkeypatch):
    monkeypatch.setenv(ENV_ONLINE_SEARCH_MODE, ONLINE_MODE_WEB_IQ)
    monkeypatch.setenv(ENV_SEARCH_ENDPOINT, "https://srch-test.search.windows.net")
    provider = create_online_search_provider()
    assert isinstance(provider, WebIQOnlineSearchProvider)
    assert provider.mode == ONLINE_MODE_WEB_IQ


def test_web_search_tool_selected_when_requested(monkeypatch):
    monkeypatch.setenv(ENV_ONLINE_SEARCH_MODE, ONLINE_MODE_WEB_SEARCH)
    monkeypatch.setenv(ENV_SEARCH_ENDPOINT, "https://srch-test.search.windows.net")
    provider = create_online_search_provider()
    assert isinstance(provider, WebSearchToolProvider)
    assert provider.mode == ONLINE_MODE_WEB_SEARCH


def test_unknown_mode_falls_back_to_curated(monkeypatch):
    monkeypatch.setenv(ENV_ONLINE_SEARCH_MODE, "bing")
    monkeypatch.setenv(ENV_SEARCH_ENDPOINT, "https://srch-test.search.windows.net")
    assert isinstance(create_online_search_provider(), CuratedOnlineSearchProvider)


# ---------------------------------------------------------------------------
# Web IQ retrieval + fallback
# ---------------------------------------------------------------------------


def _resolved_context():
    from knowledge_orchestrator.copilot.context import resolve
    from knowledge_orchestrator.copilot.models import ScreenContext

    return resolve("ETS carbon price", ScreenContext(section="energy", sub_view="overview"))


def test_web_iq_falls_back_to_curated_on_failure(monkeypatch):
    from knowledge_orchestrator.foundry_iq import KnowledgeBaseConfig

    config = KnowledgeBaseConfig(
        search_endpoint="https://srch-test.search.windows.net",
        index_name="novasteel-procedures",
    )
    provider = WebIQOnlineSearchProvider(config, credential=object())

    def _boom(question, limit):
        raise RuntimeError("knowledge base unreachable")

    monkeypatch.setattr(provider, "_retrieve", _boom)

    resolved = _resolved_context()
    hits = provider.search(resolved, "ETS carbon price", "en")
    curated = CuratedOnlineSearchProvider().search(resolved, "ETS carbon price", "en")

    # Losing public context must never cost the operator their answer.
    assert [h.source_id for h in hits] == [h.source_id for h in curated]


def test_web_iq_falls_back_when_it_finds_nothing(monkeypatch):
    from knowledge_orchestrator.foundry_iq import KnowledgeBaseConfig

    provider = WebIQOnlineSearchProvider(
        KnowledgeBaseConfig(
            search_endpoint="https://srch-test.search.windows.net",
            index_name="novasteel-procedures",
        ),
        credential=object(),
    )
    monkeypatch.setattr(provider, "_retrieve", lambda question, limit: [])

    resolved = _resolved_context()
    assert provider.search(resolved, "ETS carbon price", "en")


def test_web_iq_returns_its_own_hits_when_it_finds_something(monkeypatch):
    from knowledge_orchestrator.copilot.online import OnlineHit
    from knowledge_orchestrator.foundry_iq import KnowledgeBaseConfig

    provider = WebIQOnlineSearchProvider(
        KnowledgeBaseConfig(
            search_endpoint="https://srch-test.search.windows.net",
            index_name="novasteel-procedures",
        ),
        credential=object(),
    )
    hit = OnlineHit(source_id="web-1", title="ISO 14404", snippet="CO2 intensity", url="u")
    monkeypatch.setattr(provider, "_retrieve", lambda question, limit: [hit])

    hits = provider.search(_resolved_context(), "ETS carbon price", "en")
    assert hits == [hit]


# ---------------------------------------------------------------------------
# Response normalisation
# ---------------------------------------------------------------------------


def test_hits_from_references_handles_dict_payloads():
    response = {
        "references": [
            {"title": "ISO 14404", "content": "CO2 intensity method", "url": "https://iso.org/x"},
            {"title": "No content", "url": "https://iso.org/y"},
        ]
    }
    hits = _hits_from_references(response, limit=5)

    # The entry without a snippet is dropped rather than surfaced empty.
    assert len(hits) == 1
    assert hits[0].title == "ISO 14404"
    assert hits[0].url == "https://iso.org/x"


def test_hits_from_references_respects_limit():
    response = {
        "references": [
            {"title": f"t{i}", "content": f"c{i}", "url": f"u{i}"} for i in range(10)
        ]
    }
    assert len(_hits_from_references(response, limit=3)) == 3


@pytest.mark.parametrize("response", [None, {}, {"references": []}, object()])
def test_hits_from_references_is_defensive(response):
    """Preview API surface: an unrecognised shape degrades, it does not raise."""
    assert _hits_from_references(response, limit=3) == []
