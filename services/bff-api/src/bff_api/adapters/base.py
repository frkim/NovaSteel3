"""Port definitions for the audit and idempotency stores.

Each port is a Protocol that both the in-memory (local/demo) and durable (Azure)
adapters implement.  Configuration-driven selection with graceful degradation
mirrors the pattern in knowledge-orchestrator/adapters/base.py.
"""

from __future__ import annotations

import abc
from typing import Any, Mapping

from ..audit import AuditRecord


class AuditStorePort(abc.ABC):
    """Append-only, hash-chained audit store port.

    Implementations MUST preserve the SHA-256 hash chain across
    append/query/verify cycles, including after process restarts.
    """

    @abc.abstractmethod
    def append(
        self,
        *,
        domain: str,
        entity_id: str,
        correlation_id: str,
        action: str,
        actor: str,
        input_snapshot_ref: str,
        model_version: str | None = None,
        output: Mapping[str, Any] | None = None,
        human_action: Mapping[str, Any] | None = None,
        outcome: Mapping[str, Any] | None = None,
    ) -> AuditRecord:
        """Append a new record to the chain and return it."""
        raise NotImplementedError

    @abc.abstractmethod
    def query(
        self, *, domain: str | None = None, entity_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Query records, optionally filtered by domain and/or entity."""
        raise NotImplementedError

    @abc.abstractmethod
    def verify(self) -> bool:
        """Verify the integrity of the entire hash chain."""
        raise NotImplementedError


class IdempotencyStorePort(abc.ABC):
    """Idempotency store port for deduplicating mutation requests.

    Durable implementations MUST be safe under concurrent access from
    multiple replicas (atomic insert / optimistic concurrency).
    """

    @staticmethod
    def require_key(value: str | None) -> str:
        """Validate and return the idempotency key; raise ApiError if invalid."""
        # Delegate to the shared static validation (avoids duplication).
        from ..idempotency import IdempotencyStore

        return IdempotencyStore.require_key(value)

    @abc.abstractmethod
    def replay_or_none(
        self, *, route: str, key: str, body: Mapping[str, Any]
    ) -> Any | None:
        """Return a stored response if this key was already processed, else None."""
        raise NotImplementedError

    @abc.abstractmethod
    def store(
        self,
        *,
        route: str,
        key: str,
        body: Mapping[str, Any],
        status_code: int,
        response: Mapping[str, Any],
    ) -> None:
        """Persist a response for the given route/key pair."""
        raise NotImplementedError
