"""Adapter abstractions for Speech Fast Transcription and Foundry Agent Service.

Two implementations exist for each port:
* ``azure_*`` - production adapters using Entra managed identity / DefaultAzureCredential
  (no API keys in source), per solution-architecture.md §4.3 item 1 and §8.
* ``local_*`` - fully deterministic, offline fakes for tests and the local demo.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Optional

from ..models import AudioMetadata, ExtractedKnowledge, Transcript


class SpeechTranscriptionAdapter(abc.ABC):
    """Port for Azure Speech **Fast Transcription** (api-contracts §10.3)."""

    @abc.abstractmethod
    def transcribe(self, audio_ref: str, meta: AudioMetadata) -> Transcript:
        """Transcribe consent-approved audio into a diarized :class:`Transcript`."""
        raise NotImplementedError


class AudioStorageAdapter(abc.ABC):
    """Port for durable storage of consent-approved interview audio.

    ``store`` returns an **opaque** reference (never a raw SAS URL): the reference
    is what the orchestrator hands to the Speech adapter and records in the audit
    log, so it must not leak a directly fetchable, credentialed URL. ``delete``
    supports the raw-audio deletion directive emitted on consent withdrawal
    (security §13 / GDPR Art. 17).
    """

    @abc.abstractmethod
    def store(self, *, session_id: str, data: bytes, content_type: str) -> str:
        """Persist raw audio bytes and return an opaque storage reference."""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, audio_ref: str) -> None:
        """Erase the audio behind ``audio_ref``; a no-op if it does not exist."""
        raise NotImplementedError


@dataclass(frozen=True)
class AgentResult:
    """Result of a knowledge-capture agent turn."""

    refused: bool
    knowledge: Optional[ExtractedKnowledge]
    trace: tuple[str, ...]
    refusal_reason: Optional[str] = None


class FoundryAgentAdapter(abc.ABC):
    """Port for a Microsoft Foundry Agent Service knowledge-capture agent."""

    agent_name: str = "knowledge-capture"

    @abc.abstractmethod
    def extract_draft(self, task: str, transcript: Transcript) -> AgentResult:
        """Run the agent to extract a grounded draft from an interview transcript."""
        raise NotImplementedError
