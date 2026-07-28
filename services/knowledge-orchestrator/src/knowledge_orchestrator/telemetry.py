"""Fail-safe OpenTelemetry / Azure Monitor instrumentation for the knowledge orchestrator.

Activates only when APPLICATIONINSIGHTS_CONNECTION_STRING is present.
When absent (local/offline demo), all instrumentation is a no-op.
Import failures and exporter errors never crash or block startup.

Provides specialized span helpers for the critic loop and handoff protocol
to make the multi-agent flow legible in Application Insights, plus GenAI
instrumentation so hosted Foundry agent runs, model calls and retrievals land in
the same workspace as the rest of the service's traces.
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

# GenAI content capture is opt-in and defaults to off. When enabled, prompts and
# completions are attached to spans in Application Insights — for this service that
# means interview transcripts and operator questions, which is exactly the personal
# and process-sensitive content the erasure and residency controls exist to protect.
# Useful for a short debugging window; never a default.
ENV_CAPTURE_CONTENT = "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"


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

    _configure_genai_instrumentation()


def genai_content_capture_enabled() -> bool:
    """Whether prompt/completion content is attached to GenAI spans.

    Defaults to False. See :data:`ENV_CAPTURE_CONTENT` for why.
    """
    return os.getenv(ENV_CAPTURE_CONTENT, "").strip().lower() in ("true", "1", "yes")


def _configure_genai_instrumentation() -> None:
    """Turn on GenAI tracing for the Foundry SDKs.

    This is what makes Agent Service runs visible: with it enabled, each agent run,
    model call and tool invocation becomes a span carrying the model name, token
    counts, tool names and latency, correlated with the HTTP request that triggered
    it. The Foundry account's Application Insights connection covers server-side
    agent spans; this covers the client-side calls we make ourselves, so a single
    trace spans both.

    Content capture stays off unless explicitly enabled, so the spans carry shape and
    cost but not the text.
    """
    if not genai_content_capture_enabled():
        # Set explicitly rather than relying on the SDK default: this value is read at
        # instrumentation time and an inherited value from the host would silently
        # start recording prompts.
        os.environ.setdefault(ENV_CAPTURE_CONTENT, "false")

    try:
        from azure.ai.agents.telemetry import AIAgentsInstrumentor

        AIAgentsInstrumentor().instrument()
        logger.info(
            "GenAI agent instrumentation enabled (message content capture: %s).",
            "on" if genai_content_capture_enabled() else "off",
        )
    except ImportError:
        logger.debug(
            "azure-ai-agents telemetry not installed; hosted agent runs are still "
            "traced server-side via the Foundry Application Insights connection."
        )
    except Exception as exc:
        logger.warning("GenAI agent instrumentation failed: %s", exc)


@contextmanager
def agent_span(
    agent_name: str, operation: str = "invoke_agent", **attributes: Any
) -> Generator[Any, None, None]:
    """Create a GenAI span around an agent invocation.

    Attribute names follow the OpenTelemetry GenAI semantic conventions
    (``gen_ai.*``) so Application Insights and the Foundry portal recognise these
    spans as agent operations rather than generic dependencies, and correlate them
    with the server-side spans Agent Service emits for the same run.
    """
    if not _telemetry_active or _tracer is None:
        yield None
        return

    try:
        attrs: dict[str, Any] = {
            "gen_ai.operation.name": operation,
            "gen_ai.agent.name": agent_name,
            "gen_ai.system": "az.ai.agents",
        }
        for key, value in attributes.items():
            if value is None:
                continue
            attrs[f"gen_ai.{key}" if "." not in key else key] = value
        with _tracer.start_as_current_span(
            f"{operation} {agent_name}", attributes=attrs
        ) as span:
            yield span
    except Exception:
        yield None


@contextmanager
def retrieval_span(
    query_source: str, top_k: int, **attributes: Any
) -> Generator[Any, None, None]:
    """Create a span around a procedure retrieval.

    Records which backend served the query (AI Search vs the in-memory retriever) and
    how many chunks came back, so a drop in answer quality can be traced to a
    retrieval failure rather than being blamed on the model.
    """
    if not _telemetry_active or _tracer is None:
        yield None
        return

    try:
        attrs: dict[str, Any] = {
            "gen_ai.operation.name": "retrieve",
            "novasteel.retrieval.source": query_source,
            "novasteel.retrieval.top_k": top_k,
        }
        for key, value in attributes.items():
            if value is not None:
                attrs[f"novasteel.retrieval.{key}"] = value
        with _tracer.start_as_current_span(
            f"retrieve {query_source}", attributes=attrs
        ) as span:
            yield span
    except Exception:
        yield None


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
