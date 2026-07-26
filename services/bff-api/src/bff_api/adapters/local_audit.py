"""In-memory audit store adapter — the default for local demo and tests.

This wraps the existing AppendOnlyAudit implementation behind the
AuditStorePort interface.  Behaviour is byte-for-byte identical to the
pre-adapter codebase when no cloud configuration is present.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..audit import AppendOnlyAudit, AuditRecord
from .base import AuditStorePort


class InMemoryAuditStore(AuditStorePort):
    """Volatile audit store — data lives only for the process lifetime."""

    def __init__(self) -> None:
        self._inner = AppendOnlyAudit()

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
        return self._inner.append(
            domain=domain,
            entity_id=entity_id,
            correlation_id=correlation_id,
            action=action,
            actor=actor,
            input_snapshot_ref=input_snapshot_ref,
            model_version=model_version,
            output=output,
            human_action=human_action,
            outcome=outcome,
        )

    def query(
        self, *, domain: str | None = None, entity_id: str | None = None
    ) -> list[dict[str, Any]]:
        return self._inner.query(domain=domain, entity_id=entity_id)

    def verify(self) -> bool:
        return self._inner.verify()
