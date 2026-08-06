"""Adapter factory: selects Azure or local adapters based on configuration.

Selection logic:
- If ``FOUNDRY_ENDPOINT`` is set AND azure-identity is importable → Azure adapter.
- Otherwise → local fixture adapter (demo-mode default, offline fallback).

Failure to reach Azure degrades gracefully to fixtures with a logged warning.
"""

from __future__ import annotations

import logging
import os

from .adapters.base import (
    AudioStorageAdapter,
    FoundryAgentAdapter,
    SpeechTranscriptionAdapter,
)
from .adapters.local_audio import LocalAudioStorageAdapter
from .adapters.local_foundry import LocalFoundryKnowledgeAgent
from .adapters.local_speech import LocalSpeechTranscriptionAdapter

logger = logging.getLogger(__name__)

ENV_ENDPOINT = "FOUNDRY_ENDPOINT"
ENV_MODE = "KNOWLEDGE_AGENT_MODE"  # "azure" | "local" (explicit override)

# Speech Fast Transcription selection (mirrors the agent selection below).
ENV_SPEECH_ENDPOINT = "SPEECH_ENDPOINT"
ENV_SPEECH_REGION = "SPEECH_REGION"
ENV_SPEECH_MODE = "KNOWLEDGE_SPEECH_MODE"  # "azure" | "local" (explicit override)

# Blob audio storage selection.
ENV_AUDIO_ACCOUNT_URL = "AUDIO_STORAGE_ACCOUNT_URL"
ENV_AUDIO_CONTAINER = "AUDIO_STORAGE_CONTAINER"
ENV_AUDIO_MODE = "KNOWLEDGE_AUDIO_MODE"  # "azure" | "local" (explicit override)


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


def create_speech() -> SpeechTranscriptionAdapter:
    """Create the Speech Fast Transcription adapter based on environment config.

    Returns the Azure adapter when ``SPEECH_ENDPOINT`` is set and the SDK is
    importable, otherwise the deterministic local fixture adapter. Explicit
    ``KNOWLEDGE_SPEECH_MODE=local`` forces fixture mode. An unreachable or
    unconfigured cloud backend degrades gracefully — never a startup failure — so
    the demo and the offline tests keep working with no environment at all.
    """
    mode = os.environ.get(ENV_SPEECH_MODE, "").lower()

    if mode == "local":
        logger.info("Speech mode explicitly set to 'local' — using fixture adapter")
        return LocalSpeechTranscriptionAdapter()

    endpoint = os.environ.get(ENV_SPEECH_ENDPOINT, "")

    if not endpoint:
        logger.info("No SPEECH_ENDPOINT configured — using local fixture transcription")
        return LocalSpeechTranscriptionAdapter()

    try:
        from .adapters.azure_speech import AzureSpeechFastTranscriptionAdapter

        region = os.environ.get(ENV_SPEECH_REGION, "swedencentral")
        adapter = AzureSpeechFastTranscriptionAdapter(endpoint=endpoint, region=region)
        logger.info("Azure Speech Fast Transcription configured: %s", endpoint)
        return adapter
    except ImportError as exc:
        logger.warning(
            "Azure Speech SDK/requests not available (%s) — falling back to local "
            "fixture transcription. Install the 'azure' extra from the approved feed "
            "to enable live transcription.",
            exc,
        )
        return LocalSpeechTranscriptionAdapter()
    except Exception as exc:
        logger.warning(
            "Failed to initialize Azure Speech adapter (%s) — falling back to fixtures",
            exc,
        )
        return LocalSpeechTranscriptionAdapter()


def create_audio_storage() -> AudioStorageAdapter:
    """Create the audio storage adapter based on environment config.

    Returns the Azure Blob adapter when ``AUDIO_STORAGE_ACCOUNT_URL`` is set and
    the SDK is importable, otherwise the local in-memory adapter used by default
    and in demo mode. Explicit ``KNOWLEDGE_AUDIO_MODE=local`` forces the local
    store. Failure to reach Azure degrades gracefully to local storage.
    """
    mode = os.environ.get(ENV_AUDIO_MODE, "").lower()

    if mode == "local":
        logger.info("Audio storage explicitly set to 'local' — using in-memory store")
        return LocalAudioStorageAdapter()

    account_url = os.environ.get(ENV_AUDIO_ACCOUNT_URL, "")

    if not account_url:
        logger.info("No AUDIO_STORAGE_ACCOUNT_URL configured — using in-memory audio store")
        return LocalAudioStorageAdapter()

    try:
        from .adapters.azure_audio import AzureBlobAudioStorageAdapter

        container = os.environ.get(ENV_AUDIO_CONTAINER, "knowledge-audio")
        adapter = AzureBlobAudioStorageAdapter(
            account_url=account_url, container=container
        )
        logger.info("Azure Blob audio storage configured: %s", account_url)
        return adapter
    except ImportError as exc:
        logger.warning(
            "azure-storage-blob not available (%s) — falling back to the in-memory "
            "audio store. Install the 'azure' extra from the approved feed to enable "
            "durable blob storage.",
            exc,
        )
        return LocalAudioStorageAdapter()
    except Exception as exc:
        logger.warning(
            "Failed to initialize Azure Blob audio storage (%s) — falling back to "
            "the in-memory store",
            exc,
        )
        return LocalAudioStorageAdapter()
