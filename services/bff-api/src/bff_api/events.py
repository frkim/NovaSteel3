"""SSE replay buffer and polling fallback for BFF alert events."""

from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, AsyncIterator, Iterable, Mapping


@dataclass(frozen=True, slots=True)
class BufferedEvent:
    event_id: str
    event_type: str
    data: dict[str, Any]

    def as_poll_item(self) -> dict[str, Any]:
        return {"id": self.event_id, "type": self.event_type, "data": self.data}


class AlertEventBuffer:
    """Short-lived replay buffer with standard SSE reconnect IDs."""

    def __init__(self, alerts: Iterable[Mapping[str, Any]]) -> None:
        self._events: deque[BufferedEvent] = deque(maxlen=512)
        self._sequence = 0
        for alert in alerts:
            self.publish("alert.created", dict(alert))

    def publish(self, event_type: str, data: Mapping[str, Any]) -> BufferedEvent:
        self._sequence += 1
        event = BufferedEvent(
            event_id=f"{self._sequence:08d}",
            event_type=event_type,
            data=dict(data),
        )
        self._events.append(event)
        return event

    def after(self, last_event_id: str | None) -> list[BufferedEvent]:
        if not last_event_id:
            return list(self._events)
        return [event for event in self._events if event.event_id > last_event_id]

    async def stream(self, last_event_id: str | None) -> AsyncIterator[str]:
        """Yield replayable events followed by periodic SSE heartbeats."""
        cursor = last_event_id
        last_heartbeat = 0.0
        while True:
            sent = self.after(cursor)
            for event in sent:
                cursor = event.event_id
                encoded = json.dumps(event.data, separators=(",", ":"), default=str)
                yield f"id: {event.event_id}\nevent: {event.event_type}\ndata: {encoded}\n\n"
            if time.monotonic() - last_heartbeat >= 15:
                yield ":heartbeat\n\n"
                last_heartbeat = time.monotonic()
            await asyncio.sleep(0.25)
