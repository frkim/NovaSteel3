"""Edge/captor gateway simulator (docs section 7).

Models one simulated edge gateway per plant: monotonic per-source sequence
numbers, connectivity state machine (``ONLINE``/``DEGRADED``/``OFFLINE``/
``RECOVERING``), disk-backed store-and-forward buffering during outages,
jitter, and periodic heartbeats. Offline generation uses this to produce
the sequence numbers and connectivity-conditioned quality flags that the
contract validator checks; paced publishing (``sink_http.py``) reuses the
same gateway state to pace real HTTP delivery.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HeartbeatSample:
    source_id: str
    elapsed_hours: float
    queue_depth: int
    oldest_buffered_event: str | None
    clock_offset_ms: float
    connection_state: str


class EdgeGateway:
    """Deterministic per-source sequence counter and connectivity state."""

    def __init__(self, source_id: str, rng, outage_spec: dict | None = None):
        self.source_id = source_id
        self.rng = rng
        self._sequence = 0
        self.outage_spec = outage_spec or {}
        self._buffer: list[dict] = []

    def next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    def connectivity_state(self, elapsed_hours: float) -> str:
        if not self.outage_spec:
            return "ONLINE"
        degraded_start = self.outage_spec.get("degraded_start_hours")
        degraded_end = self.outage_spec.get("degraded_end_hours")
        offline_end = self.outage_spec.get("offline_end_hours")
        recovering_end = self.outage_spec.get("recovering_end_hours")
        if degraded_start is None:
            return "ONLINE"
        if elapsed_hours < degraded_start:
            return "ONLINE"
        if elapsed_hours < degraded_end:
            return "DEGRADED"
        if offline_end is not None and elapsed_hours < offline_end:
            return "OFFLINE"
        if recovering_end is not None and elapsed_hours < recovering_end:
            return "RECOVERING"
        return "ONLINE"

    def jitter_ms(self) -> float:
        return self.rng.uniform(0, 500)

    def packet_is_dropped(self, connectivity_state: str) -> bool:
        if connectivity_state == "DEGRADED":
            return self.rng.random() < 0.10
        if connectivity_state == "OFFLINE":
            return True
        return False

    def heartbeat(self, elapsed_hours: float, clock_offset_ms: float = 0.0) -> HeartbeatSample:
        state = self.connectivity_state(elapsed_hours)
        oldest = self._buffer[0]["event_id"] if self._buffer else None
        return HeartbeatSample(
            source_id=self.source_id,
            elapsed_hours=elapsed_hours,
            queue_depth=len(self._buffer),
            oldest_buffered_event=oldest,
            clock_offset_ms=clock_offset_ms,
            connection_state=state,
        )

    def buffer_event(self, envelope: dict) -> None:
        self._buffer.append(envelope)

    def drain_buffer(self, max_events: int) -> list[dict]:
        drained, self._buffer = self._buffer[:max_events], self._buffer[max_events:]
        return drained
