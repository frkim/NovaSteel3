"""Append-only decision audit (solution-architecture.md §1.1 item 5, §8.3).

Every consequential AI output records its inputs snapshot, version, output,
rationale, human decision, and outcome, correlated and retained. Records are
append-only and chained with a SHA-256 hash so tampering is detectable.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional

from .models import iso, utcnow

GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class AuditRecord:
    """A single immutable audit entry linked to its predecessor by ``prev_hash``."""

    sequence: int
    correlation_id: str
    domain: str  # energy|quality|furnace|knowledge|capacity
    action: str
    entity_id: str
    actor: str
    inputs: dict[str, Any]
    output: dict[str, Any]
    decision: Optional[str]
    at: str
    prev_hash: str
    record_hash: str = ""

    def digest(self) -> str:
        """Compute the deterministic SHA-256 over the record's content + prev_hash."""
        payload = {
            "sequence": self.sequence,
            "correlation_id": self.correlation_id,
            "domain": self.domain,
            "action": self.action,
            "entity_id": self.entity_id,
            "actor": self.actor,
            "inputs": self.inputs,
            "output": self.output,
            "decision": self.decision,
            "at": self.at,
            "prev_hash": self.prev_hash,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class AuditLog:
    """An append-only, hash-chained, queryable audit store.

    The public surface deliberately offers no update or delete method — history can
    only grow. ``verify()`` re-derives the chain to detect tampering.
    """

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def append(
        self,
        *,
        correlation_id: str,
        domain: str,
        action: str,
        entity_id: str,
        actor: str,
        inputs: Optional[dict[str, Any]] = None,
        output: Optional[dict[str, Any]] = None,
        decision: Optional[str] = None,
        at: Optional[datetime] = None,
    ) -> AuditRecord:
        prev_hash = self._records[-1].record_hash if self._records else GENESIS_HASH
        draft = AuditRecord(
            sequence=len(self._records),
            correlation_id=correlation_id,
            domain=domain,
            action=action,
            entity_id=entity_id,
            actor=actor,
            inputs=_redact(inputs or {}),
            output=_redact(output or {}),
            decision=decision,
            at=iso(at or utcnow()),
            prev_hash=prev_hash,
        )
        record = AuditRecord(**{**asdict(draft), "record_hash": draft.digest()})
        self._records.append(record)
        return record

    def query(
        self,
        *,
        domain: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> list[AuditRecord]:
        """Return matching records in append order (a read-only projection)."""
        out = self._records
        if domain is not None:
            out = [r for r in out if r.domain == domain]
        if entity_id is not None:
            out = [r for r in out if r.entity_id == entity_id]
        return list(out)

    def verify(self) -> bool:
        """Re-derive the hash chain; returns False if any record was altered."""
        prev = GENESIS_HASH
        for r in self._records:
            if r.prev_hash != prev or r.record_hash != r.digest():
                return False
            prev = r.record_hash
        return True

    def __len__(self) -> int:
        return len(self._records)


# Fields whose values must never be written verbatim to the audit trail
# (solution-architecture.md §10: redact audio, transcript, secrets, prompt content).
_SENSITIVE_KEYS = frozenset(
    {"audio", "transcript", "raw_text", "secret", "token", "key", "prompt"}
)


def _redact(data: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for k, v in data.items():
        if k.lower() in _SENSITIVE_KEYS:
            redacted[k] = "[REDACTED]"
        else:
            redacted[k] = v
    return redacted
