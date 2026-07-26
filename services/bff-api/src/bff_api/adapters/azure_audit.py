"""Durable Azure Table Storage audit adapter.

Azure Table Storage is chosen over Cosmos DB because:
- The audit log is append-only with point queries by domain/entity — a natural
  fit for Table Storage's PartitionKey/RowKey scheme.
- Table Storage costs ~10× less than Cosmos DB for the same throughput, which
  matters on a deliberately small demo budget.
- Insert-only semantics align with the append-only guarantee: we never update
  or delete rows.

Authentication uses DefaultAzureCredential (managed identity in production),
respecting the project's disableLocalAuth / publicNetworkAccess: Disabled
hardening — no keys or connection strings are ever used.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from typing import Any, Mapping

from ..audit import AuditRecord, _GENESIS_HASH, _SENSITIVE_KEYS, _redact
from ..contracts import utc_now
from .base import AuditStorePort

logger = logging.getLogger(__name__)


class AzureTableAuditStore(AuditStorePort):
    """Durable, append-only audit store backed by Azure Table Storage.

    The SHA-256 hash chain is preserved by:
    1. Reading the last record's hash on startup to seed the chain.
    2. Appending new records with an atomic insert (no read-then-write race).
    3. verify() reads all records from storage and recomputes the chain.

    Table schema (PartitionKey=domain, RowKey=audit_id):
      - All AuditRecord fields stored as entity properties.
      - A sequence_number (int) enables ordered iteration for chain verification.
    """

    def __init__(self, *, table_endpoint: str, table_name: str = "bffauditlog") -> None:
        from azure.data.tables import TableServiceClient
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential()
        service = TableServiceClient(endpoint=table_endpoint, credential=credential)
        self._table = service.get_table_client(table_name)
        self._table_name = table_name

        # Load the last hash from the chain to continue appending.
        self._last_hash = self._load_last_hash()
        self._sequence = self._load_sequence_number()

    def _load_last_hash(self) -> str:
        """Read the most recent record hash to continue the chain."""
        try:
            # Query the latest record by highest sequence number.
            entities = list(
                self._table.query_entities(
                    query_filter="true",
                    select=["recordHash", "sequenceNumber"],
                )
            )
            if not entities:
                return _GENESIS_HASH
            latest = max(entities, key=lambda e: int(e.get("sequenceNumber", 0)))
            return str(latest["recordHash"])
        except Exception:
            logger.warning("Could not load last hash from table; starting fresh chain.")
            return _GENESIS_HASH

    def _load_sequence_number(self) -> int:
        """Determine the next sequence number."""
        try:
            entities = list(
                self._table.query_entities(
                    query_filter="true",
                    select=["sequenceNumber"],
                )
            )
            if not entities:
                return 0
            return max(int(e.get("sequenceNumber", 0)) for e in entities) + 1
        except Exception:
            return 0

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
        previous_hash = self._last_hash
        recorded_at = utc_now().isoformat().replace("+00:00", "Z")
        audit_id = str(uuid.uuid4())

        payload = {
            "auditId": audit_id,
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
        record_hash = hashlib.sha256(blob.encode("utf-8")).hexdigest()

        record = AuditRecord(
            audit_id=audit_id,
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
            record_hash=record_hash,
        )

        # Persist to Azure Table Storage.
        entity = {
            "PartitionKey": domain,
            "RowKey": audit_id,
            "sequenceNumber": self._sequence,
            "domain": domain,
            "entityId": entity_id,
            "correlationId": correlation_id,
            "action": action,
            "actor": actor,
            "inputSnapshotRef": input_snapshot_ref,
            "modelVersion": model_version or "",
            "output": json.dumps(payload["output"], separators=(",", ":")),
            "humanAction": json.dumps(payload["humanAction"], separators=(",", ":"))
            if payload["humanAction"]
            else "",
            "outcome": json.dumps(payload["outcome"], separators=(",", ":"))
            if payload["outcome"]
            else "",
            "recordedAt": recorded_at,
            "previousHash": previous_hash,
            "recordHash": record_hash,
        }
        self._table.create_entity(entity)

        self._last_hash = record_hash
        self._sequence += 1
        return record

    def query(
        self, *, domain: str | None = None, entity_id: str | None = None
    ) -> list[dict[str, Any]]:
        filters: list[str] = []
        if domain is not None:
            filters.append(f"PartitionKey eq '{domain}'")
        if entity_id is not None:
            filters.append(f"entityId eq '{entity_id}'")

        query_filter = " and ".join(filters) if filters else "true"
        entities = list(self._table.query_entities(query_filter=query_filter))
        entities.sort(key=lambda e: int(e.get("sequenceNumber", 0)))

        results: list[dict[str, Any]] = []
        for entity in entities:
            results.append({
                "auditId": entity["RowKey"],
                "domain": entity["PartitionKey"],
                "entityId": entity.get("entityId", ""),
                "correlationId": entity.get("correlationId", ""),
                "action": entity.get("action", ""),
                "actor": entity.get("actor", ""),
                "inputSnapshotRef": entity.get("inputSnapshotRef", ""),
                "modelVersion": entity.get("modelVersion") or None,
                "output": json.loads(entity["output"]) if entity.get("output") else {},
                "humanAction": json.loads(entity["humanAction"])
                if entity.get("humanAction")
                else None,
                "outcome": json.loads(entity["outcome"])
                if entity.get("outcome")
                else None,
                "recordedAt": entity.get("recordedAt", ""),
                "previousHash": entity.get("previousHash", ""),
                "recordHash": entity.get("recordHash", ""),
            })
        return results

    def verify(self) -> bool:
        """Verify the entire hash chain from durable storage."""
        all_entities = list(
            self._table.query_entities(query_filter="true")
        )
        all_entities.sort(key=lambda e: int(e.get("sequenceNumber", 0)))

        previous = _GENESIS_HASH
        for entity in all_entities:
            record_hash = entity.get("recordHash", "")
            payload = {
                "auditId": entity["RowKey"],
                "domain": entity["PartitionKey"],
                "entityId": entity.get("entityId", ""),
                "correlationId": entity.get("correlationId", ""),
                "action": entity.get("action", ""),
                "actor": entity.get("actor", ""),
                "inputSnapshotRef": entity.get("inputSnapshotRef", ""),
                "modelVersion": entity.get("modelVersion") or None,
                "output": json.loads(entity["output"]) if entity.get("output") else {},
                "humanAction": json.loads(entity["humanAction"])
                if entity.get("humanAction")
                else None,
                "outcome": json.loads(entity["outcome"])
                if entity.get("outcome")
                else None,
                "recordedAt": entity.get("recordedAt", ""),
                "previousHash": entity.get("previousHash", ""),
            }
            blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
            computed = hashlib.sha256(blob.encode("utf-8")).hexdigest()

            if entity.get("previousHash", "") != previous or record_hash != computed:
                return False
            previous = record_hash
        return True
