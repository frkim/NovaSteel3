"""DeviceSimulatorEngine — state machine, ring buffer, and auto-advance.

The engine is the central runtime component. It owns the simulated clock,
all sensor ring buffers, the active-incident list, and the state machine
(stopped → running ⇄ paused). All public mutation methods are guarded by a
``threading.RLock`` so the service is safe under concurrent BFF workers.

Determinism guarantee: two engines constructed with the same ``(seed,
scenario)`` and advanced by the same number of ticks produce byte-identical
sensor series regardless of wall-clock time or process.

Auto-advance: any read method (``status``, ``sensors``, ``series``) calls
``_catch_up()`` which advances ticks based on elapsed wall-clock time while
the engine is in ``"running"`` state. An injectable ``clock`` callable
(default ``time.monotonic``) lets tests drive time deterministically.

See ``docs/data/synthetic-data-and-simulators.md`` sections 6-8.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from .catalog import AVAILABLE_SCENARIOS, SCENARIO_SEEDS
from .incidents import (
    INCIDENT_CATALOG,
    ActiveIncident,
    trigger_incident as _trigger,
)
from .registry import DEVICES, SENSORS, Device, Sensor
from .series import (
    compute_stats,
    downsample,
    normalize_points,
    parse_window,
)
from .signals import generate_value
from .status import (
    device_health_score,
    device_status_from_sensors,
    deviation_pct,
    sensor_status,
    sensor_trend,
)
from .views import (
    active_incident_view,
    device_detail_view,
    device_view,
    incident_catalog_entry_view,
    sensor_view,
    series_view,
    simulator_status_view,
)

_RING_BUFFER_CAP = 1440
_SIM_START = datetime(2024, 7, 25, 6, 0, 0, tzinfo=timezone.utc)
_MAX_CATCH_UP_TICKS = 500
_EVENT_SIM_INTERVAL_S = 3600.0  # cadence for sample_period_ms == 0 (per-heat/per-coil)

_SCENARIO_INCIDENTS: dict[str, list[dict]] = {
    "healthy-baseline": [],
    "demo-full": [
        {"incident_id": "degrading-furnace", "offset_hours": 0.5},
        {"incident_id": "energy-price-spike", "offset_hours": 2.0, "device_id": "LUX-UTIL-01"},
        {"incident_id": "quality-drift", "offset_hours": 4.0, "device_id": "LUX-CC-01"},
    ],
    "lining-degradation-21d": [
        {"incident_id": "degrading-furnace", "offset_hours": 0.0},
    ],
    "energy-price-spike": [
        {"incident_id": "energy-price-spike", "offset_hours": 0.25, "device_id": "LUX-UTIL-01"},
    ],
    "quality-drift": [
        {"incident_id": "quality-drift", "offset_hours": 0.0, "device_id": "LUX-CC-01"},
    ],
    "edge-outage-recovery": [
        {"incident_id": "edge-outage-recovery", "offset_hours": 0.1, "device_id": "LUX-HSM-01"},
    ],
}


class IllegalTransitionError(RuntimeError):
    """Raised when an illegal state-machine transition is requested."""


class DeviceSimulatorEngine:
    """Live deterministic device simulator.

    Parameters
    ----------
    tick_interval_seconds:
        Simulated seconds advanced per ``tick()`` call (default 5 s).
    clock:
        Callable returning a monotonic wall-clock float (default
        ``time.monotonic``).  Inject a controlled value in tests.
    """

    def __init__(
        self,
        tick_interval_seconds: float = 5.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._tick_interval = tick_interval_seconds
        self._clock = clock
        self._lock = threading.RLock()
        self._state = "stopped"
        self._scenario = "healthy-baseline"
        self._seed = SCENARIO_SEEDS["healthy-baseline"]
        self._speed_factor = 1.0
        self._tick_count = 0
        self._simulated_clock: datetime = _SIM_START
        self._started_at: Optional[datetime] = None
        self._last_wall: Optional[float] = None
        self._buffers: dict[str, deque] = {sid: deque(maxlen=_RING_BUFFER_CAP) for sid in SENSORS}
        self._last_sample_at: dict[str, Optional[datetime]] = {sid: None for sid in SENSORS}
        self._active_incidents: dict[str, ActiveIncident] = {}
        self._scenario_armed_ids: set[str] = set()
        self._uptime_start: Optional[datetime] = None
        self._total_ticks_run: int = 0

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def start(
        self,
        scenario: str = "healthy-baseline",
        seed: Optional[int] = None,
        speed_factor: float = 1.0,
    ) -> None:
        """Transition ``stopped`` → ``running``."""
        with self._lock:
            if self._state != "stopped":
                raise IllegalTransitionError(
                    f"start() called in state {self._state!r}; must be 'stopped'."
                )
            if scenario not in SCENARIO_SEEDS:
                raise ValueError(
                    f"Unknown scenario {scenario!r}. "
                    f"Available: {sorted(SCENARIO_SEEDS)}"
                )
            self._scenario = scenario
            self._seed = seed if seed is not None else SCENARIO_SEEDS[scenario]
            self._speed_factor = float(speed_factor)
            self._tick_count = 0
            self._simulated_clock = _SIM_START
            self._state = "running"
            self._started_at = datetime.now(timezone.utc)
            self._last_wall = self._clock()
            self._scenario_armed_ids = set()
            for buf in self._buffers.values():
                buf.clear()
            for sid in self._last_sample_at:
                self._last_sample_at[sid] = None
            self._active_incidents = {}
            self._uptime_start = datetime.now(timezone.utc)

    def pause(self) -> None:
        """Transition ``running`` → ``paused``."""
        with self._lock:
            if self._state != "running":
                raise IllegalTransitionError(
                    f"pause() called in state {self._state!r}; must be 'running'."
                )
            self._state = "paused"
            self._last_wall = None

    def resume(self) -> None:
        """Transition ``paused`` → ``running``."""
        with self._lock:
            if self._state != "paused":
                raise IllegalTransitionError(
                    f"resume() called in state {self._state!r}; must be 'paused'."
                )
            self._state = "running"
            self._last_wall = self._clock()

    def stop(self) -> None:
        """Transition ``running`` or ``paused`` → ``stopped``."""
        with self._lock:
            if self._state == "stopped":
                raise IllegalTransitionError("stop() called when already 'stopped'.")
            self._state = "stopped"
            self._last_wall = None

    def reset(self) -> None:
        """Reset to ``stopped`` state, clearing all buffers and incidents."""
        with self._lock:
            self._state = "stopped"
            self._tick_count = 0
            self._simulated_clock = _SIM_START
            self._started_at = None
            self._last_wall = None
            self._active_incidents = {}
            self._scenario_armed_ids = set()
            self._total_ticks_run = 0
            for buf in self._buffers.values():
                buf.clear()
            for sid in self._last_sample_at:
                self._last_sample_at[sid] = None

    def set_speed(self, factor: float) -> None:
        """Update speed factor. Callable in any state."""
        with self._lock:
            self._speed_factor = max(0.001, float(factor))
            if self._state == "running":
                self._last_wall = self._clock()

    def set_scenario(self, name: str) -> None:
        """Change scenario. Engine must be ``stopped``."""
        with self._lock:
            if self._state != "stopped":
                raise IllegalTransitionError(
                    f"set_scenario() called in state {self._state!r}; must be 'stopped'."
                )
            if name not in SCENARIO_SEEDS:
                raise ValueError(f"Unknown scenario {name!r}.")
            self._scenario = name
            self._seed = SCENARIO_SEEDS[name]

    # ------------------------------------------------------------------
    # Tick and auto-advance
    # ------------------------------------------------------------------

    def tick(self) -> None:
        """Advance one simulation step and compute all sensor values."""
        with self._lock:
            self._simulated_clock += timedelta(seconds=self._tick_interval)
            now_sim = self._simulated_clock
            elapsed_hours = (now_sim - _SIM_START).total_seconds() / 3600.0

            self._arm_scenario_incidents(elapsed_hours, now_sim)
            self._expire_incidents(now_sim)

            incident_dicts = [
                {
                    "incidentId": inc.incidentId,
                    "deviceId": inc.deviceId,
                    "sensorId": inc.sensorId,
                    "progress": inc.progress(now_sim),
                }
                for inc in self._active_incidents.values()
            ]

            for sensor_id, sensor in SENSORS.items():
                # Event-driven signals (sample_period_ms == 0) are per-heat /
                # per-coil; emit once per simulated hour to avoid flooding the
                # buffer and to model the batch nature of the measurement.
                if sensor.samplePeriodMs == 0:
                    ticks_per_event = max(1, int(_EVENT_SIM_INTERVAL_S / self._tick_interval))
                    if self._tick_count % ticks_per_event != 0:
                        continue

                value, quality, clamped = generate_value(
                    sensor_id=sensor_id,
                    device_id=sensor.deviceId,
                    signal_code=sensor.signalCode,
                    tick=self._tick_count,
                    seed=self._seed,
                    scenario=self._scenario,
                    low=sensor.low,
                    high=sensor.high,
                    active_incidents=incident_dicts,
                )
                self._buffers[sensor_id].append(
                    {
                        "tick": self._tick_count,
                        "t": self._iso(now_sim),
                        "v": value,
                        "q": quality,
                        "clamped": clamped,
                    }
                )
                self._last_sample_at[sensor_id] = now_sim

            self._tick_count += 1
            self._total_ticks_run += 1

    def _arm_scenario_incidents(self, elapsed_hours: float, now_sim: datetime) -> None:
        """Trigger pre-armed scenario incidents that have reached their offset."""
        for spec in _SCENARIO_INCIDENTS.get(self._scenario, []):
            key = f"{spec['incident_id']}@{spec['offset_hours']}"
            if key in self._scenario_armed_ids:
                continue
            if elapsed_hours >= spec["offset_hours"]:
                dev = spec.get("device_id") or ""
                if not dev:
                    entry = INCIDENT_CATALOG.get(spec["incident_id"])
                    if entry and entry.targetDeviceIds:
                        dev = entry.targetDeviceIds[0]
                if dev:
                    try:
                        inc = _trigger(
                            incident_id=spec["incident_id"],
                            simulated_now=now_sim,
                            device_id=dev,
                        )
                        self._active_incidents[inc.activeIncidentId] = inc
                    except Exception:
                        pass
                self._scenario_armed_ids.add(key)

    def _expire_incidents(self, now_sim: datetime) -> None:
        expired = [k for k, v in self._active_incidents.items() if v.is_expired(now_sim)]
        for k in expired:
            del self._active_incidents[k]

    def _catch_up(self) -> None:
        """Advance ticks based on wall-clock delta (called by read methods)."""
        if self._state != "running" or self._last_wall is None:
            return
        wall_now = self._clock()
        wall_delta = wall_now - self._last_wall
        ticks_needed = int(wall_delta * self._speed_factor / self._tick_interval)
        if ticks_needed <= 0:
            return
        ticks_needed = min(ticks_needed, _MAX_CATCH_UP_TICKS)
        for _ in range(ticks_needed):
            self.tick()
        self._last_wall += ticks_needed * self._tick_interval / self._speed_factor

    # ------------------------------------------------------------------
    # Incident management
    # ------------------------------------------------------------------

    def trigger_incident(
        self,
        incident_id: str,
        device_id: Optional[str] = None,
        sensor_id: Optional[str] = None,
        duration_minutes: Optional[float] = None,
    ) -> dict:
        """Trigger an incident and return its ``activeIncident`` view dict."""
        with self._lock:
            self._catch_up()
            now_sim = self._simulated_clock
            inc = _trigger(
                incident_id=incident_id,
                simulated_now=now_sim,
                device_id=device_id,
                sensor_id=sensor_id,
                duration_minutes=duration_minutes,
            )
            self._active_incidents[inc.activeIncidentId] = inc
            return active_incident_view(inc, now_sim)

    def clear_incident(self, active_incident_id: str) -> None:
        """Remove an active incident before it expires."""
        with self._lock:
            if active_incident_id not in self._active_incidents:
                raise KeyError(f"Active incident not found: {active_incident_id!r}")
            del self._active_incidents[active_incident_id]

    # ------------------------------------------------------------------
    # Read API
    # ------------------------------------------------------------------

    def status(self) -> dict:
        """Return the frozen ``simulatorStatus`` dict."""
        with self._lock:
            self._catch_up()
            now_sim = self._simulated_clock
            elapsed_hours = (now_sim - _SIM_START).total_seconds() / 3600.0
            ai_views = [active_incident_view(inc, now_sim) for inc in self._active_incidents.values()]
            catalog_views = [incident_catalog_entry_view(e) for e in INCIDENT_CATALOG.values()]
            return simulator_status_view(
                state=self._state,
                scenario=self._scenario,
                seed=self._seed,
                speed_factor=self._speed_factor,
                tick_interval_seconds=self._tick_interval,
                simulated_clock=now_sim if self._state != "stopped" else None,
                elapsed_hours=elapsed_hours,
                tick_count=self._tick_count,
                device_count=len(DEVICES),
                sensor_count=len(SENSORS),
                active_incidents=ai_views,
                available_scenarios=AVAILABLE_SCENARIOS,
                available_incidents=catalog_views,
                started_at=self._started_at,
            )

    def devices(self) -> list[dict]:
        """Return a list of ``device`` view dicts for all devices."""
        with self._lock:
            self._catch_up()
            result = []
            now_sim = self._simulated_clock
            for device in DEVICES.values():
                result.append(self._build_device_view(device, now_sim))
            return result

    def device(self, device_id: str) -> dict:
        """Return a ``deviceDetail`` view dict for one device."""
        with self._lock:
            self._catch_up()
            dev = DEVICES.get(device_id)
            if dev is None:
                raise KeyError(f"Device not found: {device_id!r}")
            now_sim = self._simulated_clock
            return self._build_device_detail_view(dev, now_sim)

    def sensors(self, device_id: Optional[str] = None) -> list[dict]:
        """Return ``sensor`` view dicts, optionally filtered by device."""
        with self._lock:
            self._catch_up()
            now_sim = self._simulated_clock
            result = []
            for sensor in SENSORS.values():
                if device_id is not None and sensor.deviceId != device_id:
                    continue
                result.append(self._build_sensor_view(sensor, now_sim))
            return result

    def series(
        self,
        sensor_id: str,
        window: str = "1h",
        points: int = 100,
    ) -> dict:
        """Return a ``series`` view dict for one sensor."""
        with self._lock:
            self._catch_up()
            sensor = SENSORS.get(sensor_id)
            if sensor is None:
                raise KeyError(f"Sensor not found: {sensor_id!r}")
            now_sim = self._simulated_clock
            window_sec = parse_window(window)
            cutoff = now_sim - timedelta(seconds=window_sec)
            raw = [
                {"t": p["t"], "v": p["v"], "q": p["q"]}
                for p in self._buffers[sensor_id]
                if self._parse_iso(p["t"]) >= cutoff
            ]
            downsampled = downsample(raw, points)
            normalized = normalize_points(downsampled, sensor.low, sensor.high)
            stats = compute_stats(downsampled)
            return series_view(
                sensor=sensor,
                window=window,
                points=downsampled,
                normalized_points=normalized,
                stats=stats,
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"

    @staticmethod
    def _parse_iso(s: str) -> datetime:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))

    def _sensor_history(self, sensor_id: str) -> list[float]:
        return [p["v"] for p in self._buffers[sensor_id] if p["v"] is not None]

    def _build_sensor_view(self, sensor: Sensor, now_sim: datetime) -> dict:
        buf = self._buffers[sensor.sensorId]
        last_pt = buf[-1] if buf else None
        value = last_pt["v"] if last_pt else None
        quality = last_pt["q"] if last_pt else "bad"
        clamped = last_pt["clamped"] if last_pt else False
        last_at = self._last_sample_at[sensor.sensorId]

        st = sensor_status(
            value=value,
            quality=quality,
            low=sensor.low,
            high=sensor.high,
            sample_period_ms=sensor.samplePeriodMs,
            last_sample_at=last_at,
            now=now_sim,
        )
        history = self._sensor_history(sensor.sensorId)
        trend = sensor_trend(history)
        dev_pct = deviation_pct(value, sensor.low, sensor.high) if value is not None else 0.0

        return sensor_view(
            sensor=sensor,
            value=value,
            quality=quality,
            status=st,
            trend=trend,
            dev_pct=dev_pct,
            clamped=clamped,
            last_sample_at=last_at,
        )

    def _build_device_view(self, device: Device, now_sim: datetime) -> dict:
        sensor_views = [
            self._build_sensor_view(SENSORS[sid], now_sim) for sid in device.sensorIds
        ]
        statuses = [sv["status"] for sv in sensor_views]
        health = device_health_score(statuses)
        dev_status = device_status_from_sensors(statuses)
        active_ids = [
            inc.activeIncidentId
            for inc in self._active_incidents.values()
            if inc.deviceId == device.deviceId
        ]
        last_ats = [
            self._last_sample_at[sid]
            for sid in device.sensorIds
            if self._last_sample_at[sid] is not None
        ]
        last_at = max(last_ats) if last_ats else None
        uptime = 1.0 if dev_status != "offline" else 0.0
        return device_view(
            device=device,
            sensors_status=statuses,
            active_incident_ids=active_ids,
            last_sample_at=last_at,
            health_score=health,
            uptime_pct=uptime,
            status=dev_status,
        )

    def _build_device_detail_view(self, device: Device, now_sim: datetime) -> dict:
        sensor_views = [
            self._build_sensor_view(SENSORS[sid], now_sim) for sid in device.sensorIds
        ]
        statuses = [sv["status"] for sv in sensor_views]
        health = device_health_score(statuses)
        dev_status = device_status_from_sensors(statuses)
        active_ids = [
            inc.activeIncidentId
            for inc in self._active_incidents.values()
            if inc.deviceId == device.deviceId
        ]
        last_ats = [
            self._last_sample_at[sid]
            for sid in device.sensorIds
            if self._last_sample_at[sid] is not None
        ]
        last_at = max(last_ats) if last_ats else None
        uptime = 1.0 if dev_status != "offline" else 0.0
        return device_detail_view(
            device=device,
            sensors_status=statuses,
            active_incident_ids=active_ids,
            last_sample_at=last_at,
            health_score=health,
            uptime_pct=uptime,
            status=dev_status,
            sensors=sensor_views,
        )
