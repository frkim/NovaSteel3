"""Domain models for the NovaSteel knowledge-orchestrator service.

Pure standard-library dataclasses/enums shared by the consent, audio, workflow,
prompt-defense, grounding, tool, adapter, audit, and orchestration modules.

References:
* solution-architecture.md §4.2-4.3, §5.2, §8
* api-contracts.md §4.7, §10
* security-governance-and-threat-model.md §12-14
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp (deterministic callers inject their own)."""
    return datetime.now(timezone.utc)


def iso(ts: datetime) -> str:
    """Render a UTC ISO-8601 ``Z`` timestamp, matching the API ``asOf`` contract."""
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- Data classification (security §6) --------------------------------------


class Classification(str, enum.Enum):
    """Sensitivity labels used to gate export/DLP behaviour."""

    INTERNAL = "Internal"
    CONFIDENTIAL = "Confidential"
    HIGHLY_CONFIDENTIAL = "Highly Confidential"


# --- Consent (security §13) -------------------------------------------------


class ConsentState(str, enum.Enum):
    """Lifecycle of an operator's recorded consent for knowledge capture."""

    PENDING = "PENDING"
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"


CONSENT_SCOPE = "knowledge-capture"
"""The only permitted consent scope. Surveillance/performance-monitoring reuse is
explicitly out of scope (security §13) and rejected."""


@dataclass(frozen=True)
class ConsentRecord:
    """An immutable snapshot of consent state for an interview session."""

    session_id: str
    operator_ref: str
    scope: str
    state: ConsentState
    granted_at: Optional[datetime]
    retention_days: int
    retention_deadline: Optional[datetime]
    language: str
    speaker_role: str
    deletion_request_ref: Optional[str] = None
    updated_at: datetime = field(default_factory=utcnow)

    def with_state(self, state: ConsentState, **changes) -> "ConsentRecord":
        return replace(self, state=state, updated_at=utcnow(), **changes)


# --- Audio metadata (architecture §4.3 item 5) ------------------------------


@dataclass(frozen=True)
class AudioMetadata:
    """Metadata describing consent-approved interview audio prior to submission."""

    session_id: str
    content_type: str
    duration_seconds: float
    sample_rate_hz: int
    channels: int
    size_bytes: int
    language: str
    speaker_role: str
    checksum: str


# --- Transcription (api-contracts §10.3) ------------------------------------


@dataclass(frozen=True)
class TranscriptSegment:
    """A single diarized transcript segment with a stable citable id."""

    segment_id: str
    speaker: str
    start_seconds: float
    end_seconds: float
    text: str
    confidence: float


@dataclass(frozen=True)
class Transcript:
    """A Fast Transcription result classified Highly Confidential until approved."""

    session_id: str
    language: str
    status: str  # PROCESSING | COMPLETED
    segments: tuple[TranscriptSegment, ...] = ()
    classification: Classification = Classification.HIGHLY_CONFIDENTIAL
    created_at: datetime = field(default_factory=utcnow)

    def segment_ids(self) -> set[str]:
        return {s.segment_id for s in self.segments}


# --- Grounding / citations (security §12 item 8) ----------------------------


class SourceType(str, enum.Enum):
    APPROVED_PROCEDURE = "procedure"
    TRANSCRIPT_SEGMENT = "transcript-segment"


@dataclass(frozen=True)
class Citation:
    """A grounded reference to an approved procedure or a transcript segment."""

    source_type: SourceType
    source_id: str
    quote: str = ""

    def to_ref(self) -> str:
        return f"{self.source_type.value}:{self.source_id}"


# --- Procedures (api-contracts §4.7, §10.2) ---------------------------------


class ProcedureStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ExtractedKnowledge:
    """The four extraction fields required by demo-runbook §7 / api-contracts §10.3."""

    observation: str
    recommended_check: str
    rationale: str
    safety_boundary: str
    citations: tuple[Citation, ...]


@dataclass(frozen=True)
class Procedure:
    """A versioned knowledge procedure moving through draft -> review -> approved."""

    procedure_id: str
    title: str
    status: ProcedureStatus
    version: int
    knowledge: ExtractedKnowledge
    session_id: Optional[str]
    created_by: str
    updated_at: datetime = field(default_factory=utcnow)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    @property
    def citations(self) -> tuple[Citation, ...]:
        return self.knowledge.citations
