"""Tests for copilot_adapter, copilot_online_corpus and copilot_steel_corpus."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the BFF package is importable
_BFF_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_BFF_SRC) not in sys.path:
    sys.path.insert(0, str(_BFF_SRC))

from bff_api.copilot_adapter import CopilotAdapter
from bff_api.copilot_online_corpus import (
    CORPUS_LABEL,
    RETRIEVAL_DATE,
    search_offline_corpus,
)
from bff_api.copilot_steel_corpus import search_steel_corpus


# --- Online corpus tests ---------------------------------------------------


class TestOfflineCorpus:
    def test_eu_ets_revision_found(self):
        results = search_offline_corpus("When was released the latest EU ETS?")
        assert any(r.source_id == "eu-ets-revision-2026" for r in results)
        hit = next(r for r in results if r.source_id == "eu-ets-revision-2026")
        assert "July 17, 2026" in hit.snippet
        assert hit.url.startswith("https://")

    def test_cbam_found(self):
        results = search_offline_corpus("CBAM reporting compliance steel")
        assert any(r.source_id == "cbam-transitional-reporting-2026" for r in results)

    def test_empty_query_returns_nothing(self):
        assert search_offline_corpus("") == []

    def test_limit_respected(self):
        results = search_offline_corpus("steel energy emissions carbon", limit=2)
        assert len(results) <= 2

    def test_corpus_label_is_honest(self):
        assert "offline" in CORPUS_LABEL.lower()
        assert "demo" in CORPUS_LABEL.lower()


# --- Steel corpus tests ----------------------------------------------------


class TestSteelCorpus:
    def test_processes_question(self):
        results = search_steel_corpus("What are the different processes to create steel?")
        assert any(r.entry_id == "steelmaking-routes" for r in results)

    def test_thermal_signature(self):
        results = search_steel_corpus("Explain how thermal signature works")
        assert any(r.entry_id == "thermal-signature" for r in results)

    def test_blast_furnace_lining(self):
        results = search_steel_corpus("What is a blast furnace lining?")
        assert any(
            r.entry_id in ("refractory-lining", "blast-furnace") for r in results
        )

    def test_out_of_scope_query(self):
        results = search_steel_corpus("How do I bake a chocolate cake?")
        assert len(results) == 0

    def test_empty_returns_nothing(self):
        assert search_steel_corpus("") == []


# --- Adapter integration tests ---------------------------------------------


class TestCopilotAdapterIntegration:
    """Integration tests that exercise the real adapter against the orchestrator."""

    @pytest.fixture()
    def adapter(self) -> CopilotAdapter:
        return CopilotAdapter()

    def test_delete_conversation_is_durable(self, adapter: CopilotAdapter):
        """A deleted conversation stays gone across subsequent list calls."""
        owner = "test-user-delete"
        # Create a conversation by chatting
        adapter.chat(
            owner=owner,
            question="Hello, test question",
            language="en",
            reasoning=None,
            online_search=False,
            temporary=False,
            conversation_id=None,
            context={"section": "command-center"},
            correlation_id="test-1",
        )
        convs = adapter.list_conversations(owner=owner)["conversations"]
        assert len(convs) >= 1
        conv_id = convs[0]["conversationId"]

        # Delete
        adapter.delete_conversation(owner=owner, conversation_id=conv_id)

        # Stays gone
        convs_after = adapter.list_conversations(owner=owner)["conversations"]
        assert all(c["conversationId"] != conv_id for c in convs_after)

        # Second fetch still gone
        convs_refetch = adapter.list_conversations(owner=owner)["conversations"]
        assert all(c["conversationId"] != conv_id for c in convs_refetch)

    def test_delete_all_conversations(self, adapter: CopilotAdapter):
        """Delete-all empties the list."""
        owner = "test-user-delete-all"
        for i in range(3):
            adapter.chat(
                owner=owner,
                question=f"Question {i}",
                language="en",
                reasoning=None,
                online_search=False,
                temporary=False,
                conversation_id=None,
                context={"section": "command-center"},
                correlation_id=f"test-all-{i}",
            )
        convs = adapter.list_conversations(owner=owner)["conversations"]
        assert len(convs) >= 3

        count = adapter.delete_all_conversations(owner=owner)
        assert count >= 3

        convs_after = adapter.list_conversations(owner=owner)["conversations"]
        assert convs_after == []

    def test_delete_nonexistent_raises_404(self, adapter: CopilotAdapter):
        from bff_api.errors import ApiError

        with pytest.raises(ApiError) as exc_info:
            adapter.delete_conversation(owner="nobody", conversation_id="ghost-id")
        assert exc_info.value.status_code == 404

    def test_online_search_returns_sources_with_metadata(self, adapter: CopilotAdapter, monkeypatch):
        """When online search is on, the response includes corpus metadata."""
        monkeypatch.delenv("COPILOT_SEARCH_ENDPOINT", raising=False)
        result = adapter.chat(
            owner="test-user-online",
            question="When was released the latest EU ETS revision?",
            language="en",
            reasoning=None,
            online_search=True,
            temporary=True,
            conversation_id=None,
            context={"section": "command-center"},
            correlation_id="test-online-1",
        )
        sources = result["answer"]["sources"]
        online_sources = [s for s in sources if s["kind"] == "online"]
        assert len(online_sources) >= 1
        # At least one source has the dated metadata
        dated = [s for s in online_sources if s.get("retrievedAt")]
        assert len(dated) >= 1
        assert dated[0]["corpusLabel"] == CORPUS_LABEL

    def test_online_search_off_no_online_sources_from_supplement(self, adapter: CopilotAdapter, monkeypatch):
        """When online search is OFF, no supplementary online sources are added."""
        monkeypatch.delenv("COPILOT_SEARCH_ENDPOINT", raising=False)
        result = adapter.chat(
            owner="test-user-no-online",
            question="When was released the latest EU ETS revision?",
            language="en",
            reasoning=None,
            online_search=False,
            temporary=True,
            conversation_id=None,
            context={"section": "command-center"},
            correlation_id="test-no-online-1",
        )
        sources = result["answer"]["sources"]
        # No supplementary corpus sources (those have retrievedAt)
        supplementary = [s for s in sources if s.get("retrievedAt")]
        assert supplementary == []

    def test_general_mode_no_context(self, adapter: CopilotAdapter):
        """Without screen context, steel corpus entries are included."""
        result = adapter.chat(
            owner="test-user-general",
            question="What are the different processes to create steel?",
            language="en",
            reasoning=None,
            online_search=False,
            temporary=True,
            conversation_id=None,
            context=None,
            correlation_id="test-general-1",
        )
        sources = result["answer"]["sources"]
        ids = [s.get("sourceId") for s in sources]
        assert "steelmaking-routes" in ids

    def test_context_on_includes_narrow_steel_corpus(self, adapter: CopilotAdapter):
        """With screen context ON, screen and steel-corpus grounding are both present."""
        result = adapter.chat(
            owner="test-user-ctx",
            question="What are the different processes to create steel?",
            language="en",
            reasoning=None,
            online_search=False,
            temporary=True,
            conversation_id=None,
            context={"section": "furnace-health", "subView": "lining-forecast", "site": "de"},
            correlation_id="test-ctx-1",
        )
        sources = result["answer"]["sources"]
        ids = [s.get("sourceId") for s in sources]
        assert "furnace-health" in ids
        assert "steelmaking-routes" in ids
        steelmaking = next(s for s in sources if s.get("sourceId") == "steelmaking-routes")
        assert steelmaking["kind"] == "knowledge"
        assert steelmaking["offlineCorpus"] is True

    def test_glossary_online_fallback(self, adapter: CopilotAdapter):
        """Glossary online fallback returns corpus results."""
        result = adapter.glossary_online_fallback(
            query="EU ETS carbon price",
            language="en",
        )
        assert result["corpusLabel"] == CORPUS_LABEL
        assert len(result["results"]) >= 1
        assert result["results"][0]["url"].startswith("https://")
