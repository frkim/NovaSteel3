"""Adapter ports and implementations for the knowledge-orchestrator.

Only the deterministic local adapters are imported eagerly; the Azure adapters are
imported on demand so the package has zero cloud dependencies for tests/the demo.
"""

from .base import (
    AgentResult,
    AudioStorageAdapter,
    FoundryAgentAdapter,
    SpeechTranscriptionAdapter,
)
from .local_audio import LocalAudioStorageAdapter
from .local_foundry import LocalFoundryKnowledgeAgent
from .local_speech import LocalSpeechTranscriptionAdapter

__all__ = [
    "AgentResult",
    "AudioStorageAdapter",
    "FoundryAgentAdapter",
    "SpeechTranscriptionAdapter",
    "LocalAudioStorageAdapter",
    "LocalFoundryKnowledgeAgent",
    "LocalSpeechTranscriptionAdapter",
]
