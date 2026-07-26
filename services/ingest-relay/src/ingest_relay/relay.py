"""Validation-first relay port for Event Hubs -> Eventstream delivery."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Protocol


REQUIRED_ENVELOPE_FIELDS = frozenset(
    {
        "schema_name",
        "schema_version",
        "event_id",
        "event_ts",
        "ingest_ts",
        "sequence",
        "source_id",
        "plant_id",
        "asset_id",
        "correlation_id",
        "data_classification",
        "privacy_label",
        "payload",
    }
)


class EventstreamPublisher(Protocol):
    """Cloud adapters publish validated events using a workload identity."""

    def publish(self, event: Mapping[str, Any]) -> None:
        """Publish one canonical event to the Eventstream Custom Endpoint."""


class EventHubConsumer(Protocol):
    """Production port for a managed-identity Event Hubs consumer."""

    def receive(self, max_events: int) -> Iterable[Mapping[str, Any]]:
        """Return a bounded batch while preserving original envelope content."""


@dataclass(frozen=True, slots=True)
class RelayResult:
    status: str
    event_id: str | None
    reason: str | None = None


class CanonicalEnvelopeValidator:
    """Small dependency-free validator at the untrusted ingress boundary."""

    def __init__(self, *, synthetic_only: bool = False) -> None:
        self._synthetic_only = synthetic_only

    def validate(self, event: Mapping[str, Any]) -> str | None:
        missing = REQUIRED_ENVELOPE_FIELDS - set(event)
        if missing:
            return f"missing required envelope field '{sorted(missing)[0]}'"
        if event.get("schema_version") != 1:
            return "unsupported schema_version"
        if not isinstance(event.get("payload"), Mapping):
            return "payload must be an object"
        if not isinstance(event.get("sequence"), int) or event["sequence"] < 1:
            return "sequence must be a positive integer"
        if not str(event.get("event_id", "")).strip():
            return "event_id must be non-empty"
        if not str(event.get("plant_id", "")).startswith("NS-"):
            return "plant_id must be an approved namespace"
        if not str(event.get("data_classification", "")).strip():
            return "data_classification must be declared"
        if not str(event.get("privacy_label", "")).strip():
            return "privacy_label must be declared"
        if self._synthetic_only and (
            event.get("data_classification") != "SYNTHETIC"
            or event.get("privacy_label") != "DEMO-NONPERSONAL"
        ):
            return "local relay accepts only SYNTHETIC / DEMO-NONPERSONAL events"
        if not str(event["payload"].get("type", "")).strip():
            return "payload.type must be non-empty"
        return None


@dataclass
class InMemoryEventstreamPublisher:
    """Local test/demo sink implementing the production publisher port."""

    published: list[dict[str, Any]] = field(default_factory=list)

    def publish(self, event: Mapping[str, Any]) -> None:
        self.published.append(dict(event))


class IngestRelay:
    """Deduplicates and quarantines events before a publisher ever sees them."""

    def __init__(
        self,
        publisher: EventstreamPublisher,
        validator: CanonicalEnvelopeValidator | None = None,
    ) -> None:
        self._publisher = publisher
        self._validator = validator or CanonicalEnvelopeValidator()
        self._event_hashes: dict[str, str] = {}
        self.quarantine: list[dict[str, Any]] = []
        self.metrics = {"accepted": 0, "duplicates": 0, "quarantined": 0}

    def relay(self, event: Mapping[str, Any]) -> RelayResult:
        reason = self._validator.validate(event)
        event_id = str(event.get("event_id", "")) or None
        if reason:
            return self._quarantine(event, event_id, reason)
        assert event_id is not None
        digest = self._digest(event)
        previous = self._event_hashes.get(event_id)
        if previous == digest:
            self.metrics["duplicates"] += 1
            return RelayResult("DUPLICATE", event_id)
        if previous is not None:
            return self._quarantine(event, event_id, "conflicting duplicate event_id")
        self._publisher.publish(event)
        self._event_hashes[event_id] = digest
        self.metrics["accepted"] += 1
        return RelayResult("ACCEPTED", event_id)

    def health(self) -> dict[str, int]:
        """Return safe replay/health counters without exposing event content."""
        return dict(self.metrics)

    def relay_batch(self, consumer: EventHubConsumer, max_events: int = 100) -> list[RelayResult]:
        """Consume a bounded Event Hubs batch through the same validation path."""
        if max_events < 1:
            raise ValueError("max_events must be positive")
        return [self.relay(event) for event in consumer.receive(max_events)]

    def _quarantine(
        self, event: Mapping[str, Any], event_id: str | None, reason: str
    ) -> RelayResult:
        self.quarantine.append(
            {
                "eventId": event_id,
                "reason": reason,
                "schemaName": event.get("schema_name"),
                "correlationId": event.get("correlation_id"),
            }
        )
        self.metrics["quarantined"] += 1
        return RelayResult("QUARANTINED", event_id, reason)

    @staticmethod
    def _digest(event: Mapping[str, Any]) -> str:
        blob = json.dumps(event, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()
