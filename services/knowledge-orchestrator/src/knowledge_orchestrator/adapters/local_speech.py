"""Deterministic, offline Speech Fast Transcription fake for tests and the demo.

Given a session's audio metadata, it returns a fixed, diarized transcript derived
from the approved synthetic interview fixture (demo-runbook.md §7). No cloud access,
no randomness — the same session id always yields the same transcript.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..models import AudioMetadata, Classification, Transcript, TranscriptSegment
from .base import SpeechTranscriptionAdapter

_DEFAULT_FIXTURE = (
    Path(__file__).resolve().parents[3] / "fixtures" / "interview_transcript.json"
)


class LocalSpeechTranscriptionAdapter(SpeechTranscriptionAdapter):
    """A deterministic Fast Transcription stand-in backed by a JSON fixture."""

    def __init__(self, fixture_path: Optional[Path] = None):
        self._fixture_path = Path(fixture_path) if fixture_path else _DEFAULT_FIXTURE
        self._fixture = json.loads(self._fixture_path.read_text(encoding="utf-8"))

    def transcribe(self, audio_ref: str, meta: AudioMetadata) -> Transcript:
        segments = tuple(
            TranscriptSegment(
                segment_id=s["segment_id"],
                speaker=s["speaker"],
                start_seconds=float(s["start_seconds"]),
                end_seconds=float(s["end_seconds"]),
                text=s["text"],
                confidence=float(s["confidence"]),
            )
            for s in self._fixture["segments"]
        )
        return Transcript(
            session_id=meta.session_id,
            language=meta.language,
            status="COMPLETED",
            segments=segments,
            classification=Classification.HIGHLY_CONFIDENTIAL,
        )
