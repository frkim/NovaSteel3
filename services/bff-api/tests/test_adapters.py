"""Tests for the hexagonal audit and idempotency adapters.

Covers:
- Hash-chain verification surviving a simulated restart
- Tamper detection after reload from durable storage
- Concurrent idempotency-key insertion yielding exactly one winner
- Redaction still applied in the durable path
- Automatic fallback to in-memory when cloud config is absent

All tests use in-process fakes that implement the same adapter interfaces —
no live Azure credentials required.
"""

from __future__ import annotations

import hashlib
import json
import threading
import uuid
from collections import defaultdict
from typing import Any, Mapping
from unittest.mock import patch

import pytest

from bff_api.adapters.base import AuditStorePort, IdempotencyStorePort
from bff_api.adapters.local_audit import InMemoryAuditStore
from bff_api.adapters.local_idempotency import InMemoryIdempotencyStore
from bff_api.adapters.factory import create_audit_store, create_idempotency_store
from bff_api.audit import AuditRecord, _GENESIS_HASH, _redact
from bff_api.contracts import utc_now
from bff_api.idempotency import StoredResponse


# ---------------------------------------------------------------------------
# Fake Azure Table Storage adapter for testing without credentials
# ---------------------------------------------------------------------------

class FakeTableClient:
    """In-process fake for azure.data.tables.TableClient.

    Implements create_entity, get_entity, and query_entities with
    insert-if-not-exists semantics for concurrency testing.
    """

    def __init__(self) -> None:
        self._entities: dict[tuple[str, str], dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_entity(self, entity: dict[str, Any]) -> None:
        """Atomic insert; raises ResourceExistsError if already present."""
        pk = entity["PartitionKey"]
        rk = entity["RowKey"]
        with self._lock:
            if (pk, rk) in self._entities:
                from azure.core.exceptions import ResourceExistsError

                raise ResourceExistsError("Entity already exists")
            self._entities[(pk, rk)] = dict(entity)

    def get_entity(self, partition_key: str, row_key: str) -> dict[str, Any]:
        """Point read."""
        with self._lock:
            entity = self._entities.get((partition_key, row_key))
        if entity is None:
            from azure.core.exceptions import ResourceNotFoundError

            raise ResourceNotFoundError("Entity not found")
        return dict(entity)

    def query_entities(
        self,
        query_filter: str = "true",
        select: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Simple query — supports 'true', PartitionKey eq, entityId eq."""
        with self._lock:
            results = list(self._entities.values())

        if query_filter and query_filter != "true":
            filtered = []
            for entity in results:
                match = True
                for part in query_filter.split(" and "):
                    part = part.strip()
                    if " eq " in part:
                        field, value = part.split(" eq ", 1)
                        value = value.strip("'")
                        if entity.get(field.strip(), "") != value:
                            match = False
                            break
                if match:
                    filtered.append(entity)
            results = filtered

        if select:
            results = [{k: e.get(k, "") for k in select} for e in results]

        return [dict(e) for e in results]


class FakeAzureTableAuditStore(AuditStorePort):
    """Fake durable audit store using FakeTableClient for tests.

    Replicates AzureTableAuditStore logic so we can test hash-chain
    persistence, restart survival, and tamper detection without Azure.
    """

    def __init__(self, table: FakeTableClient) -> None:
        self._table = table
        self._last_hash = self._load_last_hash()
        self._sequence = self._load_sequence_number()

    def _load_last_hash(self) -> str:
        entities = self._table.query_entities(
            query_filter="true", select=["recordHash", "sequenceNumber"]
        )
        if not entities:
            return _GENESIS_HASH
        latest = max(entities, key=lambda e: int(e.get("sequenceNumber", 0)))
        return str(latest["recordHash"])

    def _load_sequence_number(self) -> int:
        entities = self._table.query_entities(
            query_filter="true", select=["sequenceNumber"]
        )
        if not entities:
            return 0
        return max(int(e.get("sequenceNumber", 0)) for e in entities) + 1

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
        entities = self._table.query_entities(query_filter=query_filter)
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
        all_entities = self._table.query_entities(query_filter="true")
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


class FakeAzureTableIdempotencyStore(IdempotencyStorePort):
    """Fake durable idempotency store using FakeTableClient for tests."""

    def __init__(self, table: FakeTableClient) -> None:
        self._table = table

    @staticmethod
    def _hash(body: Mapping[str, Any]) -> str:
        blob = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def replay_or_none(
        self, *, route: str, key: str, body: Mapping[str, Any]
    ) -> StoredResponse | None:
        try:
            entity = self._table.get_entity(partition_key=route, row_key=key)
        except Exception:
            return None

        saved_hash = entity.get("requestHash", "")
        if saved_hash != self._hash(body):
            from bff_api.contracts import ErrorCode
            from bff_api.errors import ApiError

            raise ApiError(
                409,
                ErrorCode.IDEMPOTENCY_CONFLICT,
                "This Idempotency-Key was previously used with a different request.",
            )
        return StoredResponse(
            request_hash=saved_hash,
            status_code=int(entity.get("statusCode", 200)),
            body=json.loads(entity.get("responseBody", "{}")),
        )

    def store(
        self,
        *,
        route: str,
        key: str,
        body: Mapping[str, Any],
        status_code: int,
        response: Mapping[str, Any],
    ) -> None:
        from azure.core.exceptions import ResourceExistsError

        entity = {
            "PartitionKey": route,
            "RowKey": key,
            "requestHash": self._hash(body),
            "statusCode": status_code,
            "responseBody": json.dumps(dict(response), separators=(",", ":")),
        }
        try:
            self._table.create_entity(entity)
        except ResourceExistsError:
            pass  # First writer wins.


# ---------------------------------------------------------------------------
# Test: Hash-chain verification survives a simulated restart
# ---------------------------------------------------------------------------


class TestHashChainSurvivesRestart:
    """Verify the hash chain is intact after constructing a fresh store
    against the same backing data (simulating process restart)."""

    def test_chain_valid_after_restart(self) -> None:
        table = FakeTableClient()
        store1 = FakeAzureTableAuditStore(table)

        # Write records in first "process lifetime"
        store1.append(
            domain="energy",
            entity_id="REC-001",
            correlation_id="c1",
            action="energy.simulate",
            actor="planner",
            input_snapshot_ref="simulator:demo",
        )
        store1.append(
            domain="furnace",
            entity_id="LUX-BF-01",
            correlation_id="c2",
            action="lining.score",
            actor="scoring-worker",
            input_snapshot_ref="simulator:demo",
            model_version="v2.1",
            output={"value": 42.3, "unit": "mm"},
        )
        assert store1.verify() is True

        # Simulate restart: create a new store against the same table
        store2 = FakeAzureTableAuditStore(table)
        assert store2.verify() is True

        # Continue appending in the "new process"
        store2.append(
            domain="energy",
            entity_id="REC-002",
            correlation_id="c3",
            action="energy.approve",
            actor="admin",
            input_snapshot_ref="simulator:demo",
        )
        assert store2.verify() is True

    def test_chain_continues_correctly_after_restart(self) -> None:
        """The new process's first record links to the last record of process 1."""
        table = FakeTableClient()
        store1 = FakeAzureTableAuditStore(table)

        rec1 = store1.append(
            domain="furnace",
            entity_id="BF-01",
            correlation_id="c1",
            action="score",
            actor="worker",
            input_snapshot_ref="sim:demo",
        )

        store2 = FakeAzureTableAuditStore(table)
        rec2 = store2.append(
            domain="furnace",
            entity_id="BF-02",
            correlation_id="c2",
            action="score",
            actor="worker",
            input_snapshot_ref="sim:demo",
        )
        assert rec2.previous_hash == rec1.record_hash


# ---------------------------------------------------------------------------
# Test: Tamper detection after reload
# ---------------------------------------------------------------------------


class TestTamperDetectionAfterReload:
    """Tamper with a record in backing storage and verify detect fails."""

    def test_tampered_record_detected(self) -> None:
        table = FakeTableClient()
        store = FakeAzureTableAuditStore(table)

        store.append(
            domain="energy",
            entity_id="REC-001",
            correlation_id="c1",
            action="energy.simulate",
            actor="planner",
            input_snapshot_ref="simulator:demo",
        )
        store.append(
            domain="energy",
            entity_id="REC-002",
            correlation_id="c2",
            action="energy.approve",
            actor="admin",
            input_snapshot_ref="simulator:demo",
        )
        assert store.verify() is True

        # Tamper with the first record in the backing store
        for key, entity in table._entities.items():
            if entity.get("sequenceNumber") == 0:
                entity["action"] = "TAMPERED"
                break

        # Construct fresh store and verify — should detect the tamper
        store2 = FakeAzureTableAuditStore(table)
        assert store2.verify() is False

    def test_hash_chain_broken_by_missing_link(self) -> None:
        """Deleting a record's previousHash breaks the chain."""
        table = FakeTableClient()
        store = FakeAzureTableAuditStore(table)

        store.append(
            domain="energy",
            entity_id="REC-001",
            correlation_id="c1",
            action="simulate",
            actor="planner",
            input_snapshot_ref="sim:demo",
        )
        store.append(
            domain="energy",
            entity_id="REC-002",
            correlation_id="c2",
            action="approve",
            actor="admin",
            input_snapshot_ref="sim:demo",
        )

        # Corrupt the second record's previousHash
        for key, entity in table._entities.items():
            if entity.get("sequenceNumber") == 1:
                entity["previousHash"] = "deadbeef" * 8
                break

        store2 = FakeAzureTableAuditStore(table)
        assert store2.verify() is False


# ---------------------------------------------------------------------------
# Test: Concurrent idempotency-key insertion yields exactly one winner
# ---------------------------------------------------------------------------


class TestConcurrentIdempotency:
    """Multiple replicas racing to store the same key."""

    def test_only_one_winner(self) -> None:
        """Exactly one thread succeeds at insert; others get a silent conflict."""
        table = FakeTableClient()
        store = FakeAzureTableIdempotencyStore(table)

        route = "/v1/energy/simulate"
        key = str(uuid.uuid4())
        body = {"site": "NS-DEMO-LUX-01", "horizon": 24}
        response = {"recommendationId": "REC-001", "savings": 0.12}

        results: list[str] = []
        barrier = threading.Barrier(10)

        def attempt(thread_id: int) -> None:
            barrier.wait()
            try:
                store.store(
                    route=route,
                    key=key,
                    body=body,
                    status_code=200,
                    response=response,
                )
                results.append(f"stored-{thread_id}")
            except Exception as e:
                results.append(f"error-{thread_id}: {e}")

        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly one create_entity call succeeded; others were silently handled.
        # The table should have exactly one entity.
        entities = table.query_entities(query_filter="true")
        assert len(entities) == 1
        assert entities[0]["RowKey"] == key

    def test_replay_after_concurrent_store(self) -> None:
        """After concurrent stores, replay returns the correct response."""
        table = FakeTableClient()
        store = FakeAzureTableIdempotencyStore(table)

        route = "/v1/energy/simulate"
        key = str(uuid.uuid4())
        body = {"site": "NS-DEMO-LUX-01"}
        response = {"id": "R1"}

        store.store(route=route, key=key, body=body, status_code=200, response=response)

        replayed = store.replay_or_none(route=route, key=key, body=body)
        assert replayed is not None
        assert replayed.status_code == 200
        assert replayed.body == {"id": "R1"}

    def test_conflict_on_different_body(self) -> None:
        """Using the same key with a different body raises a conflict error."""
        table = FakeTableClient()
        store = FakeAzureTableIdempotencyStore(table)

        route = "/v1/energy/simulate"
        key = str(uuid.uuid4())

        store.store(
            route=route,
            key=key,
            body={"original": True},
            status_code=200,
            response={"ok": True},
        )

        from bff_api.errors import ApiError

        with pytest.raises(ApiError, match="different request"):
            store.replay_or_none(
                route=route, key=key, body={"different": True}
            )


# ---------------------------------------------------------------------------
# Test: Redaction still applied in the durable path
# ---------------------------------------------------------------------------


class TestRedactionInDurablePath:
    """Sensitive fields are redacted before persistence."""

    def test_sensitive_keys_redacted_on_append(self) -> None:
        table = FakeTableClient()
        store = FakeAzureTableAuditStore(table)

        record = store.append(
            domain="knowledge",
            entity_id="IV-001",
            correlation_id="c1",
            action="interview.transcribe",
            actor="speech-adapter",
            input_snapshot_ref="blob:audio.wav",
            output={"transcript": "secret words", "duration": 120},
            human_action={"token": "bearer-xyz", "reviewer": "admin"},
        )
        assert record.output["transcript"] == "[REDACTED]"
        assert record.output["duration"] == 120
        assert record.human_action["token"] == "[REDACTED]"
        assert record.human_action["reviewer"] == "admin"

    def test_redacted_data_persisted_to_table(self) -> None:
        """The backing store also contains redacted values (not originals)."""
        table = FakeTableClient()
        store = FakeAzureTableAuditStore(table)

        store.append(
            domain="knowledge",
            entity_id="IV-001",
            correlation_id="c1",
            action="transcribe",
            actor="worker",
            input_snapshot_ref="blob:audio",
            output={"secret": "hunter2", "public": "visible"},
        )

        rows = store.query(domain="knowledge")
        assert len(rows) == 1
        assert rows[0]["output"]["secret"] == "[REDACTED]"
        assert rows[0]["output"]["public"] == "visible"

    def test_chain_verification_with_redacted_data(self) -> None:
        """Hash chain is valid even when fields are redacted."""
        table = FakeTableClient()
        store = FakeAzureTableAuditStore(table)

        store.append(
            domain="knowledge",
            entity_id="IV-001",
            correlation_id="c1",
            action="transcribe",
            actor="worker",
            input_snapshot_ref="ref",
            output={"key": "api-secret-123", "count": 5},
        )
        store.append(
            domain="knowledge",
            entity_id="IV-002",
            correlation_id="c2",
            action="extract",
            actor="agent",
            input_snapshot_ref="ref",
            output={"prompt": "system prompt", "knowledge": "safe"},
        )
        assert store.verify() is True


# ---------------------------------------------------------------------------
# Test: Automatic fallback to in-memory when cloud config is absent
# ---------------------------------------------------------------------------


class TestGracefulDegradation:
    """With no cloud config, behaviour is identical to today (in-memory)."""

    def test_no_env_produces_in_memory_audit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("BFF_STORAGE_TABLE_ENDPOINT", raising=False)
        store = create_audit_store()
        assert isinstance(store, InMemoryAuditStore)

    def test_no_env_produces_in_memory_idempotency(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("BFF_STORAGE_TABLE_ENDPOINT", raising=False)
        store = create_idempotency_store()
        assert isinstance(store, InMemoryIdempotencyStore)

    def test_empty_endpoint_produces_in_memory(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BFF_STORAGE_TABLE_ENDPOINT", "  ")
        assert isinstance(create_audit_store(), InMemoryAuditStore)
        assert isinstance(create_idempotency_store(), InMemoryIdempotencyStore)

    def test_in_memory_audit_still_verifies(self) -> None:
        """The in-memory adapter's hash chain works identically to before."""
        store = InMemoryAuditStore()
        store.append(
            domain="energy",
            entity_id="REC-001",
            correlation_id="c1",
            action="simulate",
            actor="planner",
            input_snapshot_ref="sim:demo",
        )
        store.append(
            domain="energy",
            entity_id="REC-002",
            correlation_id="c2",
            action="approve",
            actor="admin",
            input_snapshot_ref="sim:demo",
        )
        assert store.verify() is True

    def test_in_memory_idempotency_replay(self) -> None:
        """In-memory idempotency works identically to the original."""
        store = InMemoryIdempotencyStore()
        route = "/v1/energy/simulate"
        key = str(uuid.uuid4())
        body = {"site": "NS-DEMO-LUX-01"}

        assert store.replay_or_none(route=route, key=key, body=body) is None

        store.store(
            route=route, key=key, body=body, status_code=200, response={"ok": True}
        )

        replayed = store.replay_or_none(route=route, key=key, body=body)
        assert replayed is not None
        assert replayed.body == {"ok": True}


# ---------------------------------------------------------------------------
# Test: In-memory audit port interface conformance
# ---------------------------------------------------------------------------


class TestInMemoryAuditConformance:
    """The in-memory adapter conforms to AuditStorePort."""

    def test_is_instance_of_port(self) -> None:
        assert isinstance(InMemoryAuditStore(), AuditStorePort)

    def test_query_filters_by_domain(self) -> None:
        store = InMemoryAuditStore()
        store.append(
            domain="energy", entity_id="R1", correlation_id="c1",
            action="sim", actor="a", input_snapshot_ref="ref",
        )
        store.append(
            domain="furnace", entity_id="B1", correlation_id="c2",
            action="score", actor="b", input_snapshot_ref="ref",
        )
        assert len(store.query(domain="energy")) == 1
        assert len(store.query(domain="furnace")) == 1
        assert len(store.query()) == 2


class TestInMemoryIdempotencyConformance:
    """The in-memory adapter conforms to IdempotencyStorePort."""

    def test_is_instance_of_port(self) -> None:
        assert isinstance(InMemoryIdempotencyStore(), IdempotencyStorePort)
