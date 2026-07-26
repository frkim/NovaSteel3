"""In-memory idempotency store adapter — the default for local demo and tests.

This wraps the existing IdempotencyStore implementation behind the
IdempotencyStorePort interface.  Behaviour is byte-for-byte identical to the
pre-adapter codebase when no cloud configuration is present.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..idempotency import IdempotencyStore, StoredResponse
from .base import IdempotencyStorePort


class InMemoryIdempotencyStore(IdempotencyStorePort):
    """Volatile idempotency store — data lives only for the process lifetime."""

    def __init__(self) -> None:
        self._inner = IdempotencyStore()

    def replay_or_none(
        self, *, route: str, key: str, body: Mapping[str, Any]
    ) -> StoredResponse | None:
        return self._inner.replay_or_none(route=route, key=key, body=body)

    def store(
        self,
        *,
        route: str,
        key: str,
        body: Mapping[str, Any],
        status_code: int,
        response: Mapping[str, Any],
    ) -> None:
        self._inner.store(
            route=route, key=key, body=body, status_code=status_code, response=response
        )
