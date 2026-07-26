"""Fail-safe OpenTelemetry / Azure Monitor instrumentation for the BFF.

Activates only when APPLICATIONINSIGHTS_CONNECTION_STRING is present.
When absent (local/offline demo), all instrumentation is a no-op and the
service behaves exactly as before.  Import failures and exporter errors
are caught and logged — they never crash or block startup.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

logger = logging.getLogger(__name__)

# Sentinel: telemetry is active only after successful configure()
_telemetry_active = False
_meter: Any = None


def _json_log_format() -> bool:
    """Return True if structured JSON logs are requested (production path)."""
    return os.getenv("NOVASTEEL_LOG_FORMAT", "").lower() == "json"


def configure_logging() -> None:
    """Set up structured logging.

    JSON format activates when NOVASTEEL_LOG_FORMAT=json (Container Apps).
    Otherwise keeps human-readable console output for local dev.
    """
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
                if hasattr(record, "correlation_id"):
                    obj["correlation_id"] = record.correlation_id
                # Inject trace context when OTel is active
                try:
                    from opentelemetry import trace

                    span = trace.get_current_span()
                    ctx = span.get_span_context()
                    if ctx and ctx.trace_id:
                        obj["trace_id"] = format(ctx.trace_id, "032x")
                        obj["span_id"] = format(ctx.span_id, "016x")
                except Exception:
                    pass
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


def configure_telemetry(service_name: str = "novasteel-bff-api") -> None:
    """Conditionally initialize Azure Monitor OpenTelemetry.

    Safe to call unconditionally — returns silently when the connection
    string is absent or when the package is unavailable.
    """
    global _telemetry_active, _meter  # noqa: PLW0603

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
            "Azure Monitor initialization failed (service continues without telemetry): %s",
            exc,
        )
        return

    # Create a meter for business KPI metrics
    try:
        from opentelemetry import metrics

        _meter = metrics.get_meter("novasteel", "1.0.0")
    except Exception as exc:
        logger.warning("OpenTelemetry meter creation failed: %s", exc)


def get_meter() -> Any:
    """Return the OpenTelemetry meter, or None if telemetry is inactive."""
    return _meter


def is_active() -> bool:
    """Return whether telemetry was successfully configured."""
    return _telemetry_active


def inject_correlation_to_trace(correlation_id: str) -> None:
    """Map X-Correlation-ID onto the current span as a baggage/attribute.

    When Azure Monitor is active, this ties the caller's correlation ID
    to the W3C trace context so distributed tracing works end-to-end.
    """
    if not _telemetry_active:
        return
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.is_recording():
            span.set_attribute("novasteel.correlation_id", correlation_id)
    except Exception:
        pass
