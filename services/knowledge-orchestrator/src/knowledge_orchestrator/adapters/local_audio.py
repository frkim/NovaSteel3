"""Deterministic, offline audio storage for tests and the local demo.

Keeps raw audio bytes in an in-memory map by default (zero cloud dependencies,
zero network) and, when a base directory is supplied, also persists them under
that directory. The returned reference is opaque — ``af://<session>/<digest>`` —
so nothing downstream depends on a fetchable, credentialed URL.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from .base import AudioStorageAdapter

_CONTAINER = "novasteel-knowledge-audio"


class LocalAudioStorageAdapter(AudioStorageAdapter):
    """An in-memory (optionally filesystem-backed) audio store for the demo."""

    def __init__(self, base_dir: Optional[Path] = None):
        self._base_dir = Path(base_dir) if base_dir else None
        self._blobs: dict[str, bytes] = {}

    def store(self, *, session_id: str, data: bytes, content_type: str) -> str:
        digest = hashlib.sha256(data).hexdigest()[:16]
        audio_ref = f"af://{_CONTAINER}/{session_id}/{digest}"
        self._blobs[audio_ref] = data
        if self._base_dir is not None:
            target = self._base_dir / session_id / digest
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        return audio_ref

    def delete(self, audio_ref: str) -> None:
        self._blobs.pop(audio_ref, None)
        if self._base_dir is not None:
            _, _, remainder = audio_ref.partition(f"{_CONTAINER}/")
            if remainder:
                candidate = self._base_dir / remainder
                if candidate.exists():
                    candidate.unlink()
