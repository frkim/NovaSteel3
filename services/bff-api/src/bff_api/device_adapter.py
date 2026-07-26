"""Adapter from the BFF boundary to the in-process device simulator engine.

The simulator runs as an importable library inside the BFF process (the same
pattern as ``optimizer-worker`` and ``scoring-worker``) so the demo needs no
extra Container App. ``services/device-simulator`` also ships a standalone
FastAPI app for teams that prefer to run it out-of-process.

Reads auto-advance the deterministic clock, so the fleet keeps moving without a
background task; writes are explicit commands from the Device Operations page.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from .contracts import ErrorCode
from .errors import ApiError

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[4]
_DEVICE_SRC = _ROOT / "services" / "device-simulator" / "src"

_COMMANDS = frozenset(
    {"start", "pause", "resume", "stop", "reset", "set-speed", "set-scenario"}
)

# 8 simulated hours of history at the 5 s tick interval, so every window
# (15m .. 24h) renders a populated chart the moment the page is opened.
_WARM_UP_TICKS = 720

# The seeded lining incident drives the demo story. It is deliberately short
# and lazily re-armed on read so the fleet never silently returns to an
# all-healthy state while the container waits for a demo to start.
_DEMO_INCIDENT_ID = "degrading-furnace"
_DEMO_INCIDENT_DEVICE = "LUX-BF-01"
_DEMO_INCIDENT_MINUTES = 90.0
# ~85 % of the incident duration at the 5 s tick interval: far enough along to
# push the hearth signals into their warning bands, with time left to watch.
_POST_INCIDENT_TICKS = 918


class DeviceAdapter:
    """Exposes fleet, sensor, series, simulator-control and incident surfaces."""

    def __init__(self, *, demo_mode: bool) -> None:
        if str(_DEVICE_SRC) not in sys.path:
            sys.path.insert(0, str(_DEVICE_SRC))
        try:
            from device_simulator import DeviceSimulatorEngine, IllegalTransitionError
        except ImportError as exc:  # pragma: no cover - repository integration failure
            raise RuntimeError("device-simulator is required by the BFF.") from exc

        self._engine = DeviceSimulatorEngine()
        self._illegal = IllegalTransitionError
        self._auto_demo = demo_mode
        if demo_mode:
            # A cold demo should show live sensors immediately, not a dead fleet.
            # Real-time speed keeps the seeded incident alive for the whole
            # defense instead of expiring a few minutes in.
            self._engine.start(scenario="demo-full", seed=240726, speed_factor=1.0)
            self._warm_up(_WARM_UP_TICKS)
            self._seed_demo_incident()

    def _warm_up(self, ticks: int) -> None:
        """Pre-fill the ring buffers so the first chart open already has history."""
        for _ in range(ticks):
            self._engine.tick()

    def _seed_demo_incident(self) -> None:
        """Arm the signature lining incident and advance to a visible progress.

        The ``demo-full`` scenario arms incidents on a simulated timeline, so a
        freshly warmed engine can land between two of them and show an entirely
        healthy fleet. Explicitly arming the lining incident keeps the Device
        Operations page telling the same story as the furnace screens.
        """
        try:
            self._engine.trigger_incident(
                incident_id=_DEMO_INCIDENT_ID,
                device_id=_DEMO_INCIDENT_DEVICE,
                duration_minutes=_DEMO_INCIDENT_MINUTES,
            )
            self._warm_up(_POST_INCIDENT_TICKS)
        except Exception:  # pragma: no cover - never block startup on demo garnish
            logger.warning("Could not seed the demo lining incident", exc_info=True)

    def _ensure_demo_incident(self) -> None:
        """Re-arm the demo incident once it has expired (demo mode only).

        Stops as soon as the operator takes manual control of the simulator, so
        a deliberate 'clear all incidents' during the demo is never undone.
        """
        if not self._auto_demo:
            return
        status = self._engine.status()
        if status["state"] != "running":
            return
        if any(
            item["incidentId"] == _DEMO_INCIDENT_ID
            for item in status["activeIncidents"]
        ):
            return
        self._seed_demo_incident()

    # -- reads --------------------------------------------------------------

    def devices(self) -> list[dict[str, Any]]:
        self._ensure_demo_incident()
        return self._guard(self._engine.devices)

    def device(self, device_id: str) -> dict[str, Any]:
        self._ensure_demo_incident()
        return self._guard(lambda: self._engine.device(device_id))

    def sensors(self, *, device_id: str | None = None) -> list[dict[str, Any]]:
        self._ensure_demo_incident()
        return self._guard(lambda: self._engine.sensors(device_id=device_id))

    def series(self, *, sensor_id: str, window: str, points: int) -> dict[str, Any]:
        return self._guard(
            lambda: self._engine.series(
                sensor_id=sensor_id, window=window, points=points
            )
        )

    def simulator(self) -> dict[str, Any]:
        self._ensure_demo_incident()
        return self._guard(self._engine.status)

    # -- commands -----------------------------------------------------------

    def command(
        self,
        *,
        command: str,
        scenario: str | None = None,
        speed_factor: float | None = None,
        seed: int | None = None,
    ) -> dict[str, Any]:
        if command not in _COMMANDS:
            raise ApiError(
                400,
                ErrorCode.VALIDATION_ERROR,
                f"Unknown simulator command '{command}'.",
            )
        # The operator now owns the simulator; stop re-arming the demo incident.
        self._auto_demo = False

        def run() -> dict[str, Any]:
            if command == "start":
                self._engine.start(
                    scenario=scenario or "healthy-baseline",
                    seed=seed,
                    speed_factor=float(speed_factor or 1.0),
                )
                self._warm_up(_WARM_UP_TICKS)
            elif command == "pause":
                self._engine.pause()
            elif command == "resume":
                self._engine.resume()
            elif command == "stop":
                self._engine.stop()
            elif command == "reset":
                self._engine.reset()
            elif command == "set-speed":
                if speed_factor is None:
                    raise ValueError("speedFactor is required for set-speed.")
                self._engine.set_speed(float(speed_factor))
            elif command == "set-scenario":
                if not scenario:
                    raise ValueError("scenario is required for set-scenario.")
                self._engine.set_scenario(scenario)
            return self._engine.status()

        return self._guard(run)

    def trigger_incident(
        self,
        *,
        incident_id: str,
        device_id: str | None = None,
        sensor_id: str | None = None,
        duration_minutes: float | None = None,
    ) -> dict[str, Any]:
        incident = self._guard(
            lambda: self._engine.trigger_incident(
                incident_id=incident_id,
                device_id=device_id,
                sensor_id=sensor_id,
                duration_minutes=duration_minutes,
            )
        )
        return {"incident": incident, "simulator": self._engine.status()}

    def clear_incident(self, active_incident_id: str) -> dict[str, Any]:
        self._auto_demo = False
        self._guard(lambda: self._engine.clear_incident(active_incident_id))
        return {"cleared": True, "simulator": self._engine.status()}

    # -- helpers ------------------------------------------------------------

    def _guard(self, fn: Any) -> Any:
        try:
            return fn()
        except self._illegal as exc:
            raise ApiError(409, ErrorCode.SIMULATOR_STATE_CONFLICT, str(exc)) from exc
        except KeyError as exc:
            raise ApiError(404, ErrorCode.NOT_FOUND, str(exc).strip("'")) from exc
        except (ValueError, TypeError) as exc:
            raise ApiError(400, ErrorCode.VALIDATION_ERROR, str(exc)) from exc


__all__ = ["DeviceAdapter"]
