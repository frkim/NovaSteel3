"""Fail-safe OpenTelemetry / Azure Monitor instrumentation for device-simulator.

Activates only when APPLICATIONINSIGHTS_CONNECTION_STRING is present.
When absent (local/offline demo), all instrumentation is a no-op.
Import failures and exporter errors never crash or block startup.

See ``services/knowledge-orchestrator/src/knowledge_orchestrator/telemetry.py``
for the project-wide pattern this module mirrors.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

logger = logging.getLogger(__name__)

_telemetry_active = False
_meter: Any = None
_tracer: Any = None


def _json_log_format() -> bool:
    return os.getenv("NOVASTEEL_LOG_FORMAT", "").lower() == "json"


def configure_logging() -> None:
    """Set up structured logging. JSON when ``NOVASTEEL_LOG_FORMAT=json``."""
    root = logging.getLogger()
    if root.handlers:
        root.handlers.clear()

    if _json_log_format():
        import json as _json
        from datetime import UTC, datetime

        class _JsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                obj: dict[str, Any] = {
                    "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                if record.exc_info and record.exc_info[1]:
                    obj["exception"] = self.formatException(record.exc_info)
                return _json.dumps(obj, default=str)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter())
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s [%(name)s] %(message)s")
        )

    root.addHandler(handler)
    root.setLevel(logging.INFO)


def configure_telemetry(service_name: str = "novasteel-device-simulator") -> None:
    """Conditionally initialise Azure Monitor. No-op without connection string."""
    global _telemetry_active, _meter, _tracer  # noqa: PLW0603

    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "").strip()
    if not connection_string:
        logger.debug("APPLICATIONINSIGHTS_CONNECTION_STRING not set; telemetry disabled.")
        return

    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=connection_string,
            service_name=service_name,
            enable_live_metrics=True,
        )
        _telemetry_active = True
        logger.info("Azure Monitor OpenTelemetry configured for %s.", service_name)
    except Exception as exc:
        logger.warning(
            "Azure Monitor initialisation failed (service continues without telemetry): %s",
            exc,
        )
        return

    try:
        from opentelemetry import metrics, trace

        _meter = metrics.get_meter("novasteel", "1.0.0")
        _tracer = trace.get_tracer("novasteel.device_simulator", "1.0.0")
    except Exception as exc:
        logger.warning("OpenTelemetry meter/tracer creation failed: %s", exc)


def get_meter() -> Any:
    """Return the OpenTelemetry meter, or ``None`` if telemetry is inactive."""
    return _meter


def get_tracer() -> Any:
    """Return the OpenTelemetry tracer, or ``None`` if telemetry is inactive."""
    return _tracer


def is_active() -> bool:
    """Return whether telemetry was successfully configured."""
    return _telemetry_active
