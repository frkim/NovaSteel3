"""Grounded-citation enforcement (security §12 item 8, api-contracts §10).

Every consequential AI output must be grounded: retrieval answers cite approved
procedures; extracted drafts cite transcript segments. This module rejects answers
that lack citations or that cite an unapproved/draft procedure or a non-existent
transcript segment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Citation, SourceType


class GroundingError(Exception):
    """Raised when an AI output cannot be grounded to approved/allowed sources."""

    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


@dataclass(frozen=True)
class GroundingResult:
    grounded: bool
    reasons: tuple[str, ...] = ()


def enforce_retrieval_grounding(
    answer: str,
    citations: Iterable[Citation],
    approved_procedure_ids: set[str],
) -> GroundingResult:
    """Enforce that a retrieval answer cites only approved procedures.

    Raises :class:`GroundingError` if the answer is empty, has no citations, or
    references any procedure id outside ``approved_procedure_ids`` (e.g. a draft).
    """
    reasons: list[str] = []
    cites = list(citations)

    if not (answer or "").strip():
        reasons.append("empty answer")
    if not cites:
        reasons.append("answer has no citations")

    for c in cites:
        if c.source_type is not SourceType.APPROVED_PROCEDURE:
            reasons.append(
                f"retrieval citation must reference an approved procedure, got "
                f"{c.source_type.value}:{c.source_id}"
            )
        elif c.source_id not in approved_procedure_ids:
            reasons.append(
                f"citation '{c.source_id}' is not an approved procedure "
                "(drafts are never retrievable)"
            )

    if reasons:
        raise GroundingError(reasons)
    return GroundingResult(True)


def enforce_extraction_grounding(
    citations: Iterable[Citation],
    transcript_segment_ids: set[str],
) -> GroundingResult:
    """Enforce that an extracted draft cites only real transcript segments.

    Every citation must reference a ``transcript-segment`` id that exists in the
    session transcript, so a draft can never invent an unsourced instruction.
    """
    reasons: list[str] = []
    cites = list(citations)

    if not cites:
        reasons.append("extraction has no source-segment citations")

    for c in cites:
        if c.source_type is not SourceType.TRANSCRIPT_SEGMENT:
            reasons.append(
                f"extraction citation must be a transcript-segment, got "
                f"{c.source_type.value}:{c.source_id}"
            )
        elif c.source_id not in transcript_segment_ids:
            reasons.append(
                f"citation '{c.source_id}' does not exist in the transcript"
            )

    if reasons:
        raise GroundingError(reasons)
    return GroundingResult(True)
