"""Adapter factory: selects Azure or local adapters based on configuration.

Selection logic:
- If ``FOUNDRY_ENDPOINT`` is set AND azure-identity is importable → Azure adapter.
- Otherwise → local fixture adapter (demo-mode default, offline fallback).

Failure to reach Azure degrades gracefully to fixtures with a logged warning.
"""

from __future__ import annotations

import logging
import os

from .adapters.base import FoundryAgentAdapter
from .adapters.local_foundry import LocalFoundryKnowledgeAgent

logger = logging.getLogger(__name__)

ENV_ENDPOINT = "FOUNDRY_ENDPOINT"
ENV_MODE = "KNOWLEDGE_AGENT_MODE"  # "azure" | "local" (explicit override)


def create_agent(fixtures_path=None) -> FoundryAgentAdapter:
    """Create the appropriate agent adapter based on environment configuration.

    Returns the Azure adapter when credentials are available, otherwise the local
    fixture adapter. Explicit ``KNOWLEDGE_AGENT_MODE=local`` forces fixture mode.
    """
    mode = os.environ.get(ENV_MODE, "").lower()

    if mode == "local":
        logger.info("Agent mode explicitly set to 'local' — using fixture adapter")
        return LocalFoundryKnowledgeAgent()

    endpoint = os.environ.get(ENV_ENDPOINT, "")

    if not endpoint:
        logger.info("No FOUNDRY_ENDPOINT configured — using local fixture adapter")
        return LocalFoundryKnowledgeAgent()

    # Try to import Azure adapter (requires azure-identity + requests).
    try:
        from .adapters.azure_foundry import AzureFoundryKnowledgeAgent

        agent = AzureFoundryKnowledgeAgent(endpoint=endpoint)
        logger.info("Azure Foundry adapter configured: %s", endpoint)
        return agent
    except ImportError as exc:
        logger.warning(
            "Azure SDK not available (%s) — falling back to local fixture adapter. "
            "Install azure-identity and requests from the approved feed to enable "
            "live model calls.",
            exc,
        )
        return LocalFoundryKnowledgeAgent()
    except Exception as exc:
        logger.warning(
            "Failed to initialize Azure adapter (%s) — falling back to fixtures",
            exc,
        )
        return LocalFoundryKnowledgeAgent()
