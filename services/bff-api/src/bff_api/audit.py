"""Append-only, hash-chained BFF decision audit."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, Mapping

from .contracts import utc_now


_GENESIS_HASH = "0" * 64
_SENSITIVE_KEYS = frozenset({"audio", "transcript", "token", "secret", "key", "prompt"})


@dataclass(frozen=True, slots=True)
class AuditRecord:
    audit_id: str
    domain: str
    entity_id: str
    correlation_id: str
    action: str
    actor: str
    input_snapshot_ref: str
    model_version: str | None
    output: dict[str, Any]
    human_action: dict[str, Any] | None
    outcome: dict[str, Any] | None
    recorded_at: str
    previous_hash: str
    record_hash: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "auditId": self.audit_id,
            "domain": self.domain,
            "entityId": self.entity_id,
            "correlationId": self.correlation_id,
            "action": self.action,
            "actor": self.actor,
            "inputSnapshotRef": self.input_snapshot_ref,
            "modelVersion": self.model_version,
            "output": self.output,
            "humanAction": self.human_action,
            "outcome": self.outcome,
            "recordedAt": self.recorded_at,
            "previousHash": self.previous_hash,
            "recordHash": self.record_hash,
        }


class AppendOnlyAudit:
    """Only appends records; no public mutation or deletion operation exists."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

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
        previous_hash = self._records[-1].record_hash if self._records else _GENESIS_HASH
        recorded_at = utc_now().isoformat().replace("+00:00", "Z")
        payload = {
            "auditId": str(uuid.uuid4()),
            "domain": domain,
            "entityId": entity_id,
            "correlationId": correlation_id,
            "action": action,
            "actor": actor,
            "inputSnapshotRef": input_snapshot_ref,
            "modelVersion": model_version,
            "output": _redact(dict(output or {})),
            "humanAction": _redact(dict(human_action or {})) or None,
            "outcome": _redact(dict(outcome or {})) or None,
            "recordedAt": recorded_at,
            "previousHash": previous_hash,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        record = AuditRecord(
            audit_id=payload["auditId"],
            domain=domain,
            entity_id=entity_id,
            correlation_id=correlation_id,
            action=action,
            actor=actor,
            input_snapshot_ref=input_snapshot_ref,
            model_version=model_version,
            output=payload["output"],
            human_action=payload["humanAction"],
            outcome=payload["outcome"],
            recorded_at=recorded_at,
            previous_hash=previous_hash,
            record_hash=hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        )
        self._records.append(record)
        return record

    def query(self, *, domain: str | None = None, entity_id: str | None = None) -> list[dict[str, Any]]:
        return [
            record.as_dict()
            for record in self._records
            if (domain is None or record.domain == domain)
            and (entity_id is None or record.entity_id == entity_id)
        ]

    def verify(self) -> bool:
        previous = _GENESIS_HASH
        for record in self._records:
            payload = record.as_dict()
            expected_hash = payload.pop("recordHash")
            blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
            if record.previous_hash != previous or expected_hash != hashlib.sha256(
                blob.encode("utf-8")
            ).hexdigest():
                return False
            previous = expected_hash
        return True


def _redact(data: dict[str, Any]) -> dict[str, Any]:
    return {
        key: "[REDACTED]" if key.lower() in _SENSITIVE_KEYS else value
        for key, value in data.items()
    }
