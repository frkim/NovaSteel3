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
