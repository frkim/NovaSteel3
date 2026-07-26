"""Audio metadata validation for Speech Fast Transcription submissions.

The BFF records consent state, language, speaker role, retention deadline, and
deletion linkage *before* submitting audio (solution-architecture.md §4.3 item 5).
This module validates the technical audio envelope and binds it to a GRANTED,
in-retention consent record so that non-consented or malformed audio never reaches
the Speech adapter.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from . import consent as consent_mod
from .models import AudioMetadata, ConsentRecord

# Fast Transcription-compatible container formats accepted by the orchestrator.
ALLOWED_CONTENT_TYPES = frozenset(
    {
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/ogg",
        "audio/flac",
    }
)

MIN_SAMPLE_RATE_HZ = 8_000
RECOMMENDED_MIN_SAMPLE_RATE_HZ = 16_000
MAX_SAMPLE_RATE_HZ = 48_000
MAX_CHANNELS = 8
MAX_DURATION_SECONDS = 2 * 60 * 60  # Fast Transcription single-request ceiling.
MAX_SIZE_BYTES = 300 * 1024 * 1024

# Permissive BCP-47 language-tag shape check (e.g. en, en-US, sv-SE).
_LANG_RE = re.compile(r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$")


class AudioValidationError(Exception):
    """Raised when audio metadata fails validation; ``errors`` lists every reason."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_audio_metadata(
    meta: AudioMetadata,
    consent: ConsentRecord,
    now: Optional[datetime] = None,
) -> None:
    """Validate ``meta`` against format rules and its consent record.

    Raises :class:`AudioValidationError` aggregating every problem found.
    """
    errors: list[str] = []

    if meta.session_id != consent.session_id:
        errors.append(
            f"audio session_id '{meta.session_id}' does not match consent session "
            f"'{consent.session_id}'"
        )

    if not consent_mod.is_capture_allowed(consent, now):
        errors.append(
            f"consent state '{consent.state.value}' does not permit audio capture"
        )

    ct = meta.content_type.split(";")[0].strip().lower()
    if ct not in ALLOWED_CONTENT_TYPES:
        errors.append(f"unsupported content_type '{meta.content_type}'")

    if not (0 < meta.duration_seconds <= MAX_DURATION_SECONDS):
        errors.append(
            f"duration_seconds {meta.duration_seconds} outside (0, {MAX_DURATION_SECONDS}]"
        )

    if not (MIN_SAMPLE_RATE_HZ <= meta.sample_rate_hz <= MAX_SAMPLE_RATE_HZ):
        errors.append(
            f"sample_rate_hz {meta.sample_rate_hz} outside "
            f"[{MIN_SAMPLE_RATE_HZ}, {MAX_SAMPLE_RATE_HZ}]"
        )

    if not (1 <= meta.channels <= MAX_CHANNELS):
        errors.append(f"channels {meta.channels} outside [1, {MAX_CHANNELS}]")

    if not (0 < meta.size_bytes <= MAX_SIZE_BYTES):
        errors.append(f"size_bytes {meta.size_bytes} outside (0, {MAX_SIZE_BYTES}]")

    if not _LANG_RE.match(meta.language or ""):
        errors.append(f"language '{meta.language}' is not a valid BCP-47 tag")
    elif consent.language and meta.language.lower() != consent.language.lower():
        errors.append(
            f"audio language '{meta.language}' does not match consent language "
            f"'{consent.language}'"
        )

    if not meta.speaker_role:
        errors.append("speaker_role is required")

    if not meta.checksum:
        errors.append("checksum is required for integrity/deletion linkage")

    if errors:
        raise AudioValidationError(errors)


def is_recommended_quality(meta: AudioMetadata) -> bool:
    """Return True when sample rate meets the recommended (>=16 kHz) quality bar."""
    return meta.sample_rate_hz >= RECOMMENDED_MIN_SAMPLE_RATE_HZ
