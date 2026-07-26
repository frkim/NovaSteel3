"""Capacity lifecycle state machine and ARM adapter boundary."""

from __future__ import annotations

import itertools
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol


SCALABLE_SKUS: tuple[str, ...] = ("F2", "F4", "F8")

_MID_TRANSITION_STATES = frozenset({
    "ResumeRequested",
    "Resuming",
    "ReadinessCheck",
    "DrainRequested",
    "Draining",
    "SuspendRequested",
})

CAPACITY_STATES = frozenset(
    {
        "Paused",
        "ResumeRequested",
        "Resuming",
        "ReadinessCheck",
        "Running",
        "DrainRequested",
        "Draining",
        "SuspendRequested",
        "Failed",
    }
)


class CapacityError(ValueError):
    """Raised for a lifecycle state or policy violation."""


class CapacityUpstreamError(RuntimeError):
    """Raised when a configured cloud capacity adapter is unavailable."""


class CapacityAdapter(Protocol):
    """Shared local/cloud lifecycle surface consumed by BFF routes."""

    def status(self) -> dict[str, Any]:
        """Return the current or safely cached capacity state."""

    def start(self, *, reason: str, actor: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Request a start transition."""

    def pause(self, *, reason: str, actor: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Request a pause transition."""

    def scale(self, *, sku: str, reason: str, actor: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Request a SKU change."""

    def operation(self, operation_id: str) -> dict[str, Any] | None:
        """Read a lifecycle operation."""


class ArmCapacityClient(Protocol):
    """Production port for the pinned Fabric capacity ARM operations."""

    def get_capacity(self, capacity_id: str) -> Mapping[str, Any]:
        """Read state through ARM API version 2023-11-01."""

    def resume(self, capacity_id: str) -> Mapping[str, Any]:
        """POST the pinned /resume ARM operation and return LRO metadata."""

    def suspend(self, capacity_id: str) -> Mapping[str, Any]:
        """POST the pinned /suspend ARM operation and return LRO metadata."""

    def poll(self, operation_id: str) -> Mapping[str, Any]:
        """Poll ARM long-running operation state respecting Retry-After."""

    def update_sku(self, capacity_id: str, sku: str) -> Mapping[str, Any]:
        """PATCH the capacity SKU and return LRO metadata."""


@dataclass
class LocalCapacityAdapter:
    """Deterministic local implementation; no cloud operation is attempted."""

    capacity_id: str = "cap-novasteel-demo-sc"
    environment: str = "demo"
    sku: str = "F2"
    state: str = "Paused"
    operations: dict[str, dict[str, Any]] = field(default_factory=dict)
    _sequence: itertools.count = field(default_factory=lambda: itertools.count(1))
    sku_options: tuple[str, ...] = field(default_factory=lambda: SCALABLE_SKUS)

    def status(self) -> dict[str, Any]:
        return {
            "capacityId": self.capacity_id,
            "environment": self.environment,
            "state": self.state,
            "sku": self.sku,
            "demoModeSimulated": True,
            "stale": False,
            "skuOptions": list(self.sku_options),
        }

    def start(self, *, reason: str, actor: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        if self.state != "Paused":
            raise CapacityError("Capacity must be Paused before a start request.")
        transitions = self._transition(
            ["ResumeRequested", "Resuming", "ReadinessCheck", "Running"], actor
        )
        operation_id = f"cap-local-{next(self._sequence):05d}"
        self.operations[operation_id] = {
            "operationId": operation_id,
            "state": "Running",
            "armStatus": "SimulatedSucceeded",
            "startedAt": _utc_now(),
            "reason": reason,
            "simulated": True,
        }
        return (
            {
                "status": "SIMULATED",
                "state": "Running",
                "operationId": operation_id,
                "capacityId": self.capacity_id,
            },
            transitions,
        )

    def pause(self, *, reason: str, actor: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        if self.state != "Running":
            raise CapacityError("Capacity must be Running before a pause request.")
        transitions = self._transition(
            ["DrainRequested", "Draining", "SuspendRequested", "Paused"], actor
        )
        operation_id = f"cap-local-{next(self._sequence):05d}"
        self.operations[operation_id] = {
            "operationId": operation_id,
            "state": "Paused",
            "armStatus": "SimulatedSucceeded",
            "startedAt": _utc_now(),
            "reason": reason,
            "simulated": True,
        }
        return (
            {
                "status": "SIMULATED",
                "state": "Paused",
                "operationId": operation_id,
                "capacityId": self.capacity_id,
            },
            transitions,
        )

    def operation(self, operation_id: str) -> dict[str, Any] | None:
        operation = self.operations.get(operation_id)
        return dict(operation) if operation else None

    def scale(self, *, sku: str, reason: str, actor: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        if self.state in _MID_TRANSITION_STATES:
            raise CapacityError("A lifecycle operation is already in progress.")
        if sku == self.sku:
            raise CapacityError(f"Capacity is already running SKU {sku}.")
        previous_sku = self.sku
        self.sku = sku
        operation_id = f"cap-local-{next(self._sequence):05d}"
        self.operations[operation_id] = {
            "operationId": operation_id,
            "state": self.state,
            "armStatus": "SimulatedSucceeded",
            "startedAt": _utc_now(),
            "reason": reason,
            "simulated": True,
        }
        transitions = [
            {
                "capacityId": self.capacity_id,
                "fromState": self.state,
                "toState": self.state,
                "actor": actor,
                "fromSku": previous_sku,
                "toSku": sku,
            }
        ]
        return (
            {
                "status": "SIMULATED",
                "state": self.state,
                "sku": sku,
                "previousSku": previous_sku,
                "operationId": operation_id,
                "capacityId": self.capacity_id,
            },
            transitions,
        )

    def _transition(self, states: list[str], actor: str) -> list[dict[str, Any]]:
        transitions = []
        for next_state in states:
            previous = self.state
            self.state = next_state
            transitions.append(
                {
                    "capacityId": self.capacity_id,
                    "fromState": previous,
                    "toState": next_state,
                    "actor": actor,
                }
            )
        return transitions


class ArmCapacityAdapter:
    """Cloud-mode adapter interface for the official pinned ARM lifecycle API."""

    api_version = "2023-11-01"

    def __init__(
        self,
        client: ArmCapacityClient,
        capacity_id: str,
        environment: str,
        sku_options: tuple[str, ...] = SCALABLE_SKUS,
    ) -> None:
        self._client = client
        self._capacity_id = capacity_id
        self._environment = environment
        self._sku_options = sku_options

    def status(self) -> dict[str, Any]:
        remote = self._client.get_capacity(self._capacity_id)
        return {
            "capacityId": self._capacity_id,
            "environment": self._environment,
            "state": str(remote.get("state", "Failed")),
            "sku": str(remote.get("sku", "F2")),
            "demoModeSimulated": False,
            "stale": False,
            "skuOptions": list(self._sku_options),
        }

    def start(self, *, reason: str, actor: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        result = self._client.resume(self._capacity_id)
        return (
            {
                "status": "ACCEPTED",
                "state": "Resuming",
                "operationId": result.get("operationId"),
                "capacityId": self._capacity_id,
            },
            [],
        )

    def pause(self, *, reason: str, actor: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        result = self._client.suspend(self._capacity_id)
        return (
            {
                "status": "ACCEPTED",
                "state": "SuspendRequested",
                "operationId": result.get("operationId"),
                "capacityId": self._capacity_id,
            },
            [],
        )

    def scale(self, *, sku: str, reason: str, actor: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        result = self._client.update_sku(self._capacity_id, sku)
        return (
            {
                "status": "ACCEPTED",
                "state": str(result.get("state", "Running")),
                "sku": sku,
                "previousSku": str(result.get("previousSku", "")),
                "operationId": result.get("operationId"),
                "capacityId": self._capacity_id,
            },
            [],
        )

    def operation(self, operation_id: str) -> dict[str, Any] | None:
        return dict(self._client.poll(operation_id))


@dataclass
class UnconfiguredArmCapacityAdapter:
    """Fail-closed cloud boundary until a managed-identity ARM client is injected."""

    capacity_id: str
    environment: str
    sku_options: tuple[str, ...] = field(default_factory=lambda: SCALABLE_SKUS)

    def status(self) -> dict[str, Any]:
        return {
            "capacityId": self.capacity_id,
            "environment": self.environment,
            "state": "Failed",
            "sku": "unknown",
            "demoModeSimulated": False,
            "stale": True,
            "skuOptions": list(self.sku_options),
        }

    def start(self, *, reason: str, actor: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        raise CapacityUpstreamError("Managed-identity ARM capacity adapter is not configured.")

    def pause(self, *, reason: str, actor: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        raise CapacityUpstreamError("Managed-identity ARM capacity adapter is not configured.")

    def scale(self, *, sku: str, reason: str, actor: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        raise CapacityUpstreamError("Managed-identity ARM capacity adapter is not configured.")

    def operation(self, operation_id: str) -> dict[str, Any] | None:
        return None


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
