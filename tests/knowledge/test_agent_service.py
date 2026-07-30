"""Tests for Foundry IQ configuration, Agent Service hosting and online search.

None of these tests touch the network. What they pin down is the behaviour that is
easy to get quietly wrong: the online-search backend must fail closed, the hosted
agent must be wired to the knowledge base's MCP endpoint with a narrow tool
allow-list, and every Azure path must degrade rather than raise.
"""

from __future__ import annotations

import pytest

from knowledge_orchestrator import agent_service, foundry_iq
from knowledge_orchestrator.agent_service import (
    ENV_AGENT_MODE,
    ENV_PROJECT_ENDPOINT,
    KNOWLEDGE_MCP_ALLOWED_TOOLS,
    PROCEDURE_AGENT_INSTRUCTIONS,
    FoundryAgentService,
    agent_service_status,
    host_agents,
)
from knowledge_orchestrator.foundry_iq import (
    DEFAULT_ALLOWED_DOMAINS,
    DEFAULT_KNOWLEDGE_BASE,
    ENV_KNOWLEDGE_BASE,
    ENV_ONLINE_SEARCH_MODE,
    ENV_WEB_ALLOWED_DOMAINS,
    KNOWLEDGE_API_VERSION,
    ONLINE_MODE_OFFLINE,
    ONLINE_MODE_WEB_IQ,
    ONLINE_MODE_WEB_SEARCH,
    KnowledgeBaseConfig,
    knowledge_base_config_from_env,
    online_search_mode,
    provision_knowledge_base,
)
from knowledge_orchestrator.search_store import ENV_SEARCH_ENDPOINT, ENV_SEARCH_INDEX

try:  # pragma: no cover - depends on which extras are installed
    from azure.ai.projects.models import MCPTool as _ProjectsMCPTool
    from azure.ai.projects.models import WebSearchTool as _ProjectsWebSearchTool
except Exception:  # pragma: no cover
    _ProjectsMCPTool = None
    _ProjectsWebSearchTool = None

requires_sdk = pytest.mark.skipif(
    _ProjectsMCPTool is None or _ProjectsWebSearchTool is None,
    reason="azure-ai-projects is an optional extra; platform tools cannot be built without it",
)


def _unary(fn):
    """Adapt a ``self``-only stub to ``ensure_agent(self, spec, registry=None)``.

    ``host_agents`` walks the manifest and calls ``ensure_agent`` once per spec, so
    the stubs below take the extra arguments and ignore them. Keeping the stubs
    themselves ``self``-only keeps each test's intent legible.
    """

    def _wrapped(self, spec=None, registry=None):
        return fn(self)

    return _wrapped


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in (
        ENV_ONLINE_SEARCH_MODE,
        ENV_WEB_ALLOWED_DOMAINS,
        ENV_KNOWLEDGE_BASE,
        ENV_SEARCH_ENDPOINT,
        ENV_SEARCH_INDEX,
        ENV_PROJECT_ENDPOINT,
        ENV_AGENT_MODE,
        "FOUNDRY_ENDPOINT",
        "FOUNDRY_CHAT_DEPLOYMENT",
        "FOUNDRY_EMBED_DEPLOYMENT",
    ):
        monkeypatch.delenv(name, raising=False)


# ---------------------------------------------------------------------------
# Online search mode: fail closed
# ---------------------------------------------------------------------------


def test_online_search_defaults_to_offline():
    assert online_search_mode() == ONLINE_MODE_OFFLINE


@pytest.mark.parametrize(
    "value", [ONLINE_MODE_WEB_IQ, ONLINE_MODE_WEB_SEARCH, ONLINE_MODE_OFFLINE]
)
def test_online_search_accepts_known_modes(monkeypatch, value):
    monkeypatch.setenv(ENV_ONLINE_SEARCH_MODE, value)
    assert online_search_mode() == value


def test_online_search_is_case_insensitive(monkeypatch):
    monkeypatch.setenv(ENV_ONLINE_SEARCH_MODE, "  WEB_IQ ")
    assert online_search_mode() == ONLINE_MODE_WEB_IQ


@pytest.mark.parametrize("value", ["bing", "web", "true", "on", "websearch"])
def test_unrecognised_mode_fails_closed_to_offline(monkeypatch, value):
    """A typo must not silently start sending operator questions to the public web."""
    monkeypatch.setenv(ENV_ONLINE_SEARCH_MODE, value)
    assert online_search_mode() == ONLINE_MODE_OFFLINE


# ---------------------------------------------------------------------------
# Knowledge base configuration
# ---------------------------------------------------------------------------


def test_knowledge_base_config_requires_search_endpoint():
    assert knowledge_base_config_from_env() is None


def test_knowledge_base_config_from_env(monkeypatch):
    monkeypatch.setenv(ENV_SEARCH_ENDPOINT, "https://srch-test.search.windows.net/")
    monkeypatch.setenv(ENV_SEARCH_INDEX, "novasteel-procedures")
    monkeypatch.setenv("FOUNDRY_ENDPOINT", "https://foundry.cognitiveservices.azure.com/")
    monkeypatch.setenv("FOUNDRY_CHAT_DEPLOYMENT", "gpt-5.4-mini")

    config = knowledge_base_config_from_env()

    assert config is not None
    assert config.search_endpoint == "https://srch-test.search.windows.net"
    assert config.knowledge_base_name == DEFAULT_KNOWLEDGE_BASE
    assert config.chat_deployment == "gpt-5.4-mini"
    # Web source stays off unless online search explicitly asks for Web IQ.
    assert config.include_web_source is False


def test_web_source_enabled_only_in_web_iq_mode(monkeypatch):
    monkeypatch.setenv(ENV_SEARCH_ENDPOINT, "https://srch-test.search.windows.net")
    monkeypatch.setenv(ENV_ONLINE_SEARCH_MODE, ONLINE_MODE_WEB_IQ)
    config = knowledge_base_config_from_env()
    assert config is not None and config.include_web_source is True


def test_default_allowed_domains_are_standards_bodies(monkeypatch):
    monkeypatch.setenv(ENV_SEARCH_ENDPOINT, "https://srch-test.search.windows.net")
    config = knowledge_base_config_from_env()
    assert config is not None
    assert config.allowed_domains == DEFAULT_ALLOWED_DOMAINS
    assert "iso.org" in config.allowed_domains


def test_allowed_domains_override(monkeypatch):
    monkeypatch.setenv(ENV_SEARCH_ENDPOINT, "https://srch-test.search.windows.net")
    monkeypatch.setenv(ENV_WEB_ALLOWED_DOMAINS, "iso.org, example.org ,")
    config = knowledge_base_config_from_env()
    assert config is not None
    assert config.allowed_domains == ("iso.org", "example.org")


def test_blank_allowed_domains_falls_back_to_defaults(monkeypatch):
    monkeypatch.setenv(ENV_SEARCH_ENDPOINT, "https://srch-test.search.windows.net")
    monkeypatch.setenv(ENV_WEB_ALLOWED_DOMAINS, "   ,  ")
    config = knowledge_base_config_from_env()
    assert config is not None and config.allowed_domains == DEFAULT_ALLOWED_DOMAINS


def test_mcp_url_targets_the_knowledge_base_and_pins_preview_api():
    config = KnowledgeBaseConfig(
        search_endpoint="https://srch-test.search.windows.net",
        index_name="novasteel-procedures",
        knowledge_base_name="novasteel-procedures-kb",
    )
    assert config.mcp_url == (
        "https://srch-test.search.windows.net/knowledgebases/novasteel-procedures-kb"
        f"/mcp?api-version={KNOWLEDGE_API_VERSION}"
    )


def test_provision_without_search_reports_reason():
    result = provision_knowledge_base()
    assert result.provisioned is False
    assert "AI Search is not configured" in result.reason


def test_provision_without_chat_deployment_reports_reason(monkeypatch):
    monkeypatch.setenv(ENV_SEARCH_ENDPOINT, "https://srch-test.search.windows.net")
    result = provision_knowledge_base()
    assert result.provisioned is False
    assert "query planning" in result.reason


def test_provision_degrades_when_sdk_missing(monkeypatch):
    config = KnowledgeBaseConfig(
        search_endpoint="https://srch-test.search.windows.net",
        index_name="novasteel-procedures",
        foundry_endpoint="https://foundry.cognitiveservices.azure.com",
        chat_deployment="gpt-5.4-mini",
    )

    def _boom(self):
        raise ImportError("azure-search-documents is not installed")

    monkeypatch.setattr(foundry_iq.FoundryIQProvisioner, "provision", _boom)
    result = provision_knowledge_base(config)
    assert result.provisioned is False
    assert "SDK unavailable" in result.reason


# ---------------------------------------------------------------------------
# Agent Service
# ---------------------------------------------------------------------------


def test_agent_service_disabled_without_project_endpoint():
    status = agent_service_status()
    assert status.enabled is False
    assert ENV_PROJECT_ENDPOINT in status.reason


def test_agent_service_explicit_local_override(monkeypatch):
    monkeypatch.setenv(ENV_PROJECT_ENDPOINT, "https://x.services.ai.azure.com/api/projects/p")
    monkeypatch.setenv(ENV_AGENT_MODE, "local")
    assert agent_service_status().enabled is False


def test_agent_service_enabled_with_endpoint(monkeypatch):
    monkeypatch.setenv(
        ENV_PROJECT_ENDPOINT, "https://x.services.ai.azure.com/api/projects/p/"
    )
    status = agent_service_status()
    assert status.enabled is True
    assert status.project_endpoint == "https://x.services.ai.azure.com/api/projects/p"


def test_agent_service_rejects_an_account_endpoint(monkeypatch):
    """Agents live on a project. An account endpoint would 404 on the first call."""
    monkeypatch.setenv(ENV_PROJECT_ENDPOINT, "https://x.services.ai.azure.com")
    status = agent_service_status()
    assert status.enabled is False
    assert "project endpoint" in status.reason


def test_agent_service_rewrites_a_classic_host(monkeypatch):
    """The Foundry project model is served from services.ai.azure.com."""
    monkeypatch.setenv(
        ENV_PROJECT_ENDPOINT, "https://x.cognitiveservices.azure.com/api/projects/p"
    )
    status = agent_service_status()
    assert status.enabled is True
    assert status.project_endpoint == "https://x.services.ai.azure.com/api/projects/p"


def test_host_agents_degrades_when_sdk_missing(monkeypatch):
    monkeypatch.setenv(
        ENV_PROJECT_ENDPOINT, "https://x.services.ai.azure.com/api/projects/p"
    )

    def _boom(self):
        raise ImportError("azure-ai-projects is not installed")

    monkeypatch.setattr(FoundryAgentService, "ensure_agent", _unary(_boom))
    status = host_agents()
    assert status.enabled is False
    assert "SDK unavailable" in status.reason


def test_host_agents_degrades_on_unreachable_project(monkeypatch):
    monkeypatch.setenv(
        ENV_PROJECT_ENDPOINT, "https://x.services.ai.azure.com/api/projects/p"
    )

    def _boom(self):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(FoundryAgentService, "ensure_agent", _unary(_boom))
    status = host_agents()
    assert status.enabled is False
    assert "connection refused" in status.reason


def test_procedure_agent_uses_five_series_mini_by_default(monkeypatch):
    monkeypatch.setenv(
        ENV_PROJECT_ENDPOINT, "https://x.services.ai.azure.com/api/projects/p"
    )
    captured = {}

    def _capture(self):
        captured["model"] = self.model
        return agent_service.HostedAgent(name="a", agent_id="1", model=self.model)

    monkeypatch.setattr(FoundryAgentService, "ensure_agent", _unary(_capture))
    host_agents()
    assert captured["model"].startswith("gpt-5")
    assert "mini" in captured["model"]


def test_procedure_agent_model_follows_chat_deployment(monkeypatch):
    monkeypatch.setenv(
        ENV_PROJECT_ENDPOINT, "https://x.services.ai.azure.com/api/projects/p"
    )
    monkeypatch.setenv("FOUNDRY_CHAT_DEPLOYMENT", "gpt-5-mini")
    captured = {}

    def _capture(self):
        captured["model"] = self.model
        return agent_service.HostedAgent(name="a", agent_id="1", model=self.model)

    monkeypatch.setattr(FoundryAgentService, "ensure_agent", _unary(_capture))
    host_agents()
    assert captured["model"] == "gpt-5-mini"


def test_knowledge_tool_is_none_without_a_knowledge_base():
    service = FoundryAgentService(
        project_endpoint="https://x.services.ai.azure.com/api/projects/p"
    )
    assert service._knowledge_tool() is None


def test_knowledge_tool_points_at_the_knowledge_base_mcp_endpoint(monkeypatch):
    """The agent reaches AI Search through Foundry IQ, with a narrow allow-list."""
    import sys
    import types

    captured = {}

    class _MCPTool:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    azure_module = types.ModuleType("azure")
    ai_module = types.ModuleType("azure.ai")
    projects_module = types.ModuleType("azure.ai.projects")
    module = types.ModuleType("azure.ai.projects.models")
    module.MCPTool = _MCPTool
    projects_module.models = module
    ai_module.projects = projects_module
    azure_module.ai = ai_module
    monkeypatch.setitem(sys.modules, "azure", azure_module)
    monkeypatch.setitem(sys.modules, "azure.ai", ai_module)
    monkeypatch.setitem(sys.modules, "azure.ai.projects", projects_module)
    monkeypatch.setitem(sys.modules, "azure.ai.projects.models", module)

    config = KnowledgeBaseConfig(
        search_endpoint="https://srch-test.search.windows.net",
        index_name="novasteel-procedures",
        knowledge_base_name="novasteel-procedures-kb",
    )
    service = FoundryAgentService(
        project_endpoint="https://x.services.ai.azure.com/api/projects/p",
        knowledge_base=config,
    )
    tool = service._knowledge_tool()

    assert tool is not None
    assert captured["server_url"] == config.mcp_url
    assert captured["allowed_tools"] == list(KNOWLEDGE_MCP_ALLOWED_TOOLS)
    assert captured["allowed_tools"] == ["knowledge_base_retrieve"]
    # An operator on a plant floor cannot answer an approval dialog.
    assert captured["require_approval"] == "never"


@requires_sdk
def test_builtin_agent_tools_are_real_projects_sdk_models():
    """The release reconciler must build the new Foundry project tool models.

    The offline test above stubs the SDK import so CI can run without Azure extras;
    this one uses the installed package when present and would have caught importing
    the classic ``azure.ai.agents`` models instead.
    """
    config = KnowledgeBaseConfig(
        search_endpoint="https://srch-test.search.windows.net",
        index_name="novasteel-procedures",
        knowledge_base_name="novasteel-procedures-kb",
    )
    service = FoundryAgentService(
        project_endpoint="https://x.services.ai.azure.com/api/projects/p",
        knowledge_base=config,
    )

    procedure_tools, procedure_names = service._resolve_tools(
        agent_service.agent_spec(agent_service.PROCEDURE_AGENT_NAME)
    )
    web_tools, web_names = service._resolve_tools(
        agent_service.agent_spec(agent_service.WEB_SEARCH_AGENT_NAME)
    )

    assert procedure_names == KNOWLEDGE_MCP_ALLOWED_TOOLS
    assert len(procedure_tools) == 1
    assert isinstance(procedure_tools[0], _ProjectsMCPTool)
    assert procedure_tools[0].as_dict() == {
        "server_label": "novasteel_procedures",
        "server_url": config.mcp_url,
        "require_approval": "never",
        "allowed_tools": ["knowledge_base_retrieve"],
        "type": "mcp",
    }

    assert web_names == ("web_search",)
    assert len(web_tools) == 1
    assert isinstance(web_tools[0], _ProjectsWebSearchTool)
    assert web_tools[0].as_dict() == {"type": "web_search"}


def test_procedure_agent_instructions_enforce_grounding():
    """The hosted agent must decline in the exact words the citation check allows."""
    from knowledge_orchestrator.retrieval import (
        build_decline_answer,
        enforce_answer_citations,
    )

    decline = build_decline_answer("no_grounded_source")
    assert decline in PROCEDURE_AGENT_INSTRUCTIONS
    # A refusal in these words must survive citation enforcement uncited.
    enforce_answer_citations(decline, allowed_chunk_ids=set())

    text = PROCEDURE_AGENT_INSTRUCTIONS.lower()
    assert "cite" in text
    assert "[[proc-0042]]" in text
    assert "safety" in text
