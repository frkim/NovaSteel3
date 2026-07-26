"""Shared pytest fixtures for the knowledge-orchestrator tests.

Adds the service ``src`` directory to ``sys.path`` so tests import the package
without an install step, and points fixtures at the service ``fixtures`` folder.
Everything runs offline with the deterministic local adapters.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SERVICE = Path(__file__).resolve().parents[2] / "services" / "knowledge-orchestrator"
_SRC = _SERVICE / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

FIXTURES = _SERVICE / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def audio_meta():
    from knowledge_orchestrator.models import AudioMetadata

    def _make(session_id: str = "IV-00001", **overrides):
        base = dict(
            session_id=session_id,
            content_type="audio/wav",
            duration_seconds=95.0,
            sample_rate_hz=16000,
            channels=1,
            size_bytes=3_000_000,
            language="en",
            speaker_role="operator",
            checksum="sha256:demo",
        )
        base.update(overrides)
        return AudioMetadata(**base)

    return _make


@pytest.fixture
def orchestrator():
    from knowledge_orchestrator import KnowledgeOrchestrator
    from knowledge_orchestrator.adapters import (
        LocalFoundryKnowledgeAgent,
        LocalSpeechTranscriptionAdapter,
    )

    return KnowledgeOrchestrator(
        speech=LocalSpeechTranscriptionAdapter(FIXTURES / "interview_transcript.json"),
        agent=LocalFoundryKnowledgeAgent(),
    )
