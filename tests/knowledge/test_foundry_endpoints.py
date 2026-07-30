"""The data plane must address Foundry through the project model, not the classic one.

These are cheap assertions guarding an easy regression: the classic Azure OpenAI
route (``/openai/deployments/<name>?api-version=<date>`` on
``*.cognitiveservices.azure.com``) still exists and still works for *some* calls,
so a copy-pasted URL would fail only in a deployed environment — and then only for
the features the v1 surface adds.
"""

from __future__ import annotations

import pytest

from knowledge_orchestrator.foundry_endpoints import (
    FOUNDRY_SCOPE,
    LEGACY_COGNITIVE_SERVICES_SCOPE,
    normalize_endpoint,
    openai_v1_url,
    token_scope,
)


class TestNormalizeEndpoint:
    @pytest.mark.parametrize(
        "given",
        [
            "https://aif-novasteel-demo.cognitiveservices.azure.com",
            "https://aif-novasteel-demo.cognitiveservices.azure.com/",
            "https://aif-novasteel-demo.openai.azure.com",
        ],
    )
    def test_classic_hosts_are_rewritten_to_the_project_model_host(
        self, given: str
    ) -> None:
        assert (
            normalize_endpoint(given)
            == "https://aif-novasteel-demo.services.ai.azure.com"
        )

    def test_a_project_model_endpoint_is_left_alone(self) -> None:
        endpoint = "https://aif-novasteel-demo.services.ai.azure.com"
        assert normalize_endpoint(f"{endpoint}/") == endpoint

    def test_a_project_endpoint_keeps_its_project_path(self) -> None:
        assert (
            normalize_endpoint(
                "https://aif.cognitiveservices.azure.com/api/projects/proj-novasteel"
            )
            == "https://aif.services.ai.azure.com/api/projects/proj-novasteel"
        )

    @pytest.mark.parametrize("given", ["", "   ", None])
    def test_missing_configuration_stays_empty(self, given) -> None:
        assert normalize_endpoint(given) == ""

    def test_an_unrecognised_host_is_passed_through(self) -> None:
        """Guessing at a sovereign or proxied host is worse than leaving it alone."""
        assert (
            normalize_endpoint("https://foundry.internal.novasteel.example/")
            == "https://foundry.internal.novasteel.example"
        )


class TestOpenAiV1Url:
    def test_uses_the_versionless_v1_route(self) -> None:
        url = openai_v1_url(
            "https://aif-novasteel-demo.services.ai.azure.com", "chat/completions"
        )
        assert url == (
            "https://aif-novasteel-demo.services.ai.azure.com/openai/v1/chat/completions"
        )

    def test_never_emits_the_classic_deployments_route(self) -> None:
        url = openai_v1_url(
            "https://aif-novasteel-demo.cognitiveservices.azure.com", "embeddings"
        )
        assert "/openai/deployments/" not in url
        assert "api-version" not in url
        assert url.startswith("https://aif-novasteel-demo.services.ai.azure.com/")

    def test_an_unset_endpoint_is_an_error_not_a_relative_url(self) -> None:
        with pytest.raises(ValueError):
            openai_v1_url("", "chat/completions")


class TestTokenScope:
    def test_defaults_to_the_foundry_audience(self, monkeypatch) -> None:
        monkeypatch.delenv("FOUNDRY_TOKEN_SCOPE", raising=False)
        assert token_scope() == FOUNDRY_SCOPE
        assert token_scope() != LEGACY_COGNITIVE_SERVICES_SCOPE

    def test_is_overridable_for_sovereign_clouds(self, monkeypatch) -> None:
        monkeypatch.setenv("FOUNDRY_TOKEN_SCOPE", "https://ai.azure.us/.default")
        assert token_scope() == "https://ai.azure.us/.default"


class TestCallSitesUseTheProjectModel:
    """The adapters must not carry their own classic URL builders."""

    def test_knowledge_adapter_builds_a_v1_url(self, monkeypatch) -> None:
        from knowledge_orchestrator.adapters.azure_foundry import (
            AzureFoundryKnowledgeAgent,
        )

        agent = AzureFoundryKnowledgeAgent(
            endpoint="https://aif.cognitiveservices.azure.com"
        )
        assert agent.endpoint == "https://aif.services.ai.azure.com"
        assert not hasattr(agent, "api_version")

    def test_copilot_chat_agent_sends_the_deployment_as_the_model(self) -> None:
        from knowledge_orchestrator.copilot.agents import AzureFoundryChatAgent
        from knowledge_orchestrator.copilot.models import ReasoningTier

        agent = AzureFoundryChatAgent(
            tier=ReasoningTier.DEFAULT,
            endpoint="https://aif.openai.azure.com",
            deployment="gpt-5.4-mini",
        )
        assert agent.endpoint == "https://aif.services.ai.azure.com"
        assert agent._request_body("sys", "user")["model"] == "gpt-5.4-mini"

    def test_embedding_provider_normalises_its_endpoint(self) -> None:
        from knowledge_orchestrator.retrieval import AzureOpenAIEmbeddingProvider

        provider = AzureOpenAIEmbeddingProvider(
            endpoint="https://aif.cognitiveservices.azure.com/"
        )
        assert provider._endpoint == "https://aif.services.ai.azure.com"
