"""Deterministic simulated clock (docs section 7).

Supports ``real``, ``accelerated``, ``paused``, and ``replay`` clock modes.
The clock is purely a function of an integer "tick" counter so that two
runs with the same manifest produce byte-identical ``event_ts`` sequences
regardless of wall-clock time.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class SimClock:
    """A deterministic simulated clock.

    Parameters
    ----------
    start:
        Simulated start time (UTC).
    mode:
        One of ``real``, ``accelerated``, ``paused``, ``replay``.
    acceleration_factor:
        Simulated seconds elapsed per real second when paced/live
        publishing is used. Has no effect on offline batch generation,
        which always advances the clock by the requested step.
    """

    start: datetime
    mode: str = "accelerated"
    acceleration_factor: float = 1.0
    _elapsed_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.start.tzinfo is None:
            self.start = self.start.replace(tzinfo=timezone.utc)
        if self.mode not in {"real", "accelerated", "paused", "replay"}:
            raise ValueError(f"Unknown clock mode: {self.mode}")

    @property
    def now(self) -> datetime:
        return self.start + timedelta(seconds=self._elapsed_seconds)

    def advance(self, seconds: float) -> datetime:
        """Advance the simulated clock and return the new simulated time."""
        if self.mode == "paused":
            return self.now
        self._elapsed_seconds += seconds
        return self.now

    def wall_clock_sleep_seconds(self, simulated_seconds: float) -> float:
        """Real (wall-clock) seconds to sleep for a given simulated-time step
        when paced publishing is enabled."""
        if self.mode == "paused":
            return 0.0
        factor = max(self.acceleration_factor, 1e-6)
        return simulated_seconds / factor

    def reset(self, start: datetime | None = None) -> None:
        if start is not None:
            self.start = start if start.tzinfo else start.replace(tzinfo=timezone.utc)
        self._elapsed_seconds = 0.0


def iso(dt: datetime) -> str:
    """Format a datetime as UTC ISO-8601 with millisecond precision and a
    trailing ``Z``, matching the envelope examples in the specification."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"
