"""Optional FastAPI wiring for device-simulator (BFF-compatible routes).

This module is imported only when FastAPI is available (resolved from the
approved feed). The core library (engine, signals, incidents, …) is
transport-agnostic. Routes expose the ``/devices/…`` prefix plus
``/health/live`` and ``/health/ready``.

See ``README.md`` for the frozen response shapes and ``docs/api-contracts.md``
§6 for the BFF route mapping.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - exercised only when FastAPI is installed
    from fastapi import Body, FastAPI, HTTPException, Query
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover
    FastAPI = None  # type: ignore

from .engine import DeviceSimulatorEngine, IllegalTransitionError
from .telemetry import configure_logging, configure_telemetry

_engine: Optional[DeviceSimulatorEngine] = None


def _get_engine() -> DeviceSimulatorEngine:
    global _engine  # noqa: PLW0603
    if _engine is None:
        _engine = DeviceSimulatorEngine()
    return _engine


def create_app(engine: Optional[DeviceSimulatorEngine] = None) -> "FastAPI":  # pragma: no cover
    """Build a FastAPI application exposing device-simulator routes."""
    if FastAPI is None:
        raise RuntimeError(
            "FastAPI is not installed; resolve it from the approved feed to serve HTTP."
        )

    configure_logging()
    configure_telemetry()

    used_engine = engine or _get_engine()

    application = FastAPI(
        title="NovaSteel device-simulator",
        version="1.0",
        description="Deterministic live device simulator for the NovaSteel demo estate.",
    )

    def _guard(fn):
        try:
            return fn()
        except IllegalTransitionError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    # -- Health ----------------------------------------------------------

    @application.get("/health/live")
    def health_live():
        return {"status": "ok"}

    @application.get("/health/ready")
    def health_ready():
        return {"status": "ok", "simulatorState": used_engine._state}

    # -- Simulator control -----------------------------------------------

    @application.post("/devices/simulator/start")
    def simulator_start(body: dict = Body(default={})):
        return _guard(
            lambda: used_engine.start(
                scenario=body.get("scenario", "healthy-baseline"),
                seed=body.get("seed"),
                speed_factor=float(body.get("speedFactor", 1.0)),
            )
            or used_engine.status()
        )

    @application.post("/devices/simulator/pause")
    def simulator_pause():
        return _guard(lambda: used_engine.pause() or used_engine.status())

    @application.post("/devices/simulator/resume")
    def simulator_resume():
        return _guard(lambda: used_engine.resume() or used_engine.status())

    @application.post("/devices/simulator/stop")
    def simulator_stop():
        return _guard(lambda: used_engine.stop() or used_engine.status())

    @application.post("/devices/simulator/reset")
    def simulator_reset():
        return _guard(lambda: used_engine.reset() or used_engine.status())

    @application.put("/devices/simulator/speed")
    def simulator_speed(body: dict = Body(...)):
        return _guard(
            lambda: used_engine.set_speed(float(body["speedFactor"])) or used_engine.status()
        )

    @application.put("/devices/simulator/scenario")
    def simulator_scenario(body: dict = Body(...)):
        return _guard(
            lambda: used_engine.set_scenario(body["scenario"]) or used_engine.status()
        )

    @application.get("/devices/simulator/status")
    def simulator_status():
        return _guard(lambda: used_engine.status())

    # -- Device / sensor reads -------------------------------------------

    @application.get("/devices")
    def list_devices():
        return _guard(lambda: used_engine.devices())

    @application.get("/devices/{device_id}")
    def get_device(device_id: str):
        return _guard(lambda: used_engine.device(device_id))

    @application.get("/devices/{device_id}/sensors")
    def list_sensors(device_id: str):
        return _guard(lambda: used_engine.sensors(device_id=device_id))

    @application.get("/devices/sensors/{sensor_id}/series")
    def get_series(
        sensor_id: str,
        window: str = Query("1h"),
        points: int = Query(100, ge=1, le=1440),
    ):
        return _guard(lambda: used_engine.series(sensor_id=sensor_id, window=window, points=points))

    # -- Incident management ---------------------------------------------

    @application.post("/devices/incidents/trigger")
    def trigger_incident(body: dict = Body(...)):
        return _guard(
            lambda: used_engine.trigger_incident(
                incident_id=body["incidentId"],
                device_id=body.get("deviceId"),
                sensor_id=body.get("sensorId"),
                duration_minutes=body.get("durationMinutes"),
            )
        )

    @application.delete("/devices/incidents/{active_incident_id}")
    def clear_incident(active_incident_id: str):
        return _guard(lambda: used_engine.clear_incident(active_incident_id) or {"cleared": True})

    return application


try:  # pragma: no cover
    app = create_app()
except Exception:  # pragma: no cover
    app = None  # type: ignore
