"""Fail-safe OpenTelemetry / Azure Monitor instrumentation for the knowledge orchestrator.

Activates only when APPLICATIONINSIGHTS_CONNECTION_STRING is present.
When absent (local/offline demo), all instrumentation is a no-op.
Import failures and exporter errors never crash or block startup.

Provides specialized span helpers for the critic loop and handoff protocol
to make the multi-agent flow legible in Application Insights.
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import contextmanager
from typing import Any, Generator

logger = logging.getLogger(__name__)

_telemetry_active = False
_meter: Any = None
_tracer: Any = None


def _json_log_format() -> bool:
    return os.getenv("NOVASTEEL_LOG_FORMAT", "").lower() == "json"


def configure_logging() -> None:
    """Set up structured logging. JSON when NOVASTEEL_LOG_FORMAT=json."""
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


def configure_telemetry(service_name: str = "novasteel-knowledge-orchestrator") -> None:
    """Conditionally initialize Azure Monitor. No-op without connection string."""
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
            "Azure Monitor initialization failed (service continues without telemetry): %s",
            exc,
        )
        return

    try:
        from opentelemetry import metrics, trace

        _meter = metrics.get_meter("novasteel", "1.0.0")
        _tracer = trace.get_tracer("novasteel.knowledge", "1.0.0")
    except Exception as exc:
        logger.warning("OpenTelemetry meter/tracer creation failed: %s", exc)


def get_meter() -> Any:
    """Return the OpenTelemetry meter, or None if telemetry is inactive."""
    return _meter


def get_tracer() -> Any:
    """Return the OpenTelemetry tracer, or None if telemetry is inactive."""
    return _tracer


def is_active() -> bool:
    """Return whether telemetry was successfully configured."""
    return _telemetry_active


@contextmanager
def critic_span(
    iteration: int, correlation_id: str = ""
) -> Generator[Any, None, None]:
    """Create a span for a single critic iteration.

    Attributes: iteration number, correlation_id. The verdict (APPROVE/REVISE)
    is set after the yield via span.set_attribute.
    """
    if not _telemetry_active or _tracer is None:
        yield None
        return

    try:
        with _tracer.start_as_current_span(
            f"reflection.critic.iter{iteration}",
            attributes={
                "novasteel.critic.iteration": iteration,
                "novasteel.correlation_id": correlation_id,
            },
        ) as span:
            yield span
    except Exception:
        yield None


@contextmanager
def handoff_span(
    step: str, correlation_id: str = "", **attributes: Any
) -> Generator[Any, None, None]:
    """Create a span for a handoff hop (rul_check or replan).

    ``step`` is one of "handoff.rul_check" or "handoff.replan".
    """
    if not _telemetry_active or _tracer is None:
        yield None
        return

    try:
        attrs = {"novasteel.correlation_id": correlation_id}
        for k, v in attributes.items():
            attrs[f"novasteel.handoff.{k}"] = v
        with _tracer.start_as_current_span(step, attributes=attrs) as span:
            yield span
    except Exception:
        yield None
