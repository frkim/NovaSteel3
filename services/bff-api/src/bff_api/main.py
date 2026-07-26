"""FastAPI application factory for the NovaSteel BFF foundation."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import Settings
from .contracts import (
    ErrorCode,
    ErrorEnvelope,
    HealthStatus,
    MetaData,
    MetaEnvelope,
    utc_now,
)
from .errors import ApiError
from .routes import register_routes
from .services import BffServices
from .telemetry import configure_logging, configure_telemetry, inject_correlation_to_trace

configure_logging()
configure_telemetry("novasteel-bff-api")

logger = logging.getLogger(__name__)
CORRELATION_ID_HEADER = "X-Correlation-ID"


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", str(uuid.uuid4()))


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: ErrorCode,
    message: str,
    retryable: bool = False,
) -> JSONResponse:
    envelope = ErrorEnvelope(
        code=code,
        message=message,
        correlation_id=_correlation_id(request),
        retryable=retryable,
    )
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(by_alias=True, mode="json"),
        headers={CORRELATION_ID_HEADER: _correlation_id(request)},
    )


def create_app(
    settings: Settings | None = None, services: BffServices | None = None
) -> FastAPI:
    """Create a configured BFF with local adapters or explicit cloud boundaries."""

    runtime_settings = settings or Settings.from_environment()
    app = FastAPI(
        title="NovaSteel BFF API",
        version="1.0.0",
        description=(
            "Synthetic-demo-safe BFF routes with server-side authorization, "
            "auditable advisory analytics, and no OT control path."
        ),
    )
    app.state.settings = runtime_settings
    app.state.services = services or BffServices.create(runtime_settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime_settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            CORRELATION_ID_HEADER,
            "X-Demo-User",
            "X-Demo-Roles",
            "X-Demo-Plants",
            "X-Demo-Display-Name",
            "X-Demo-Locale",
        ],
        expose_headers=[CORRELATION_ID_HEADER],
    )

    @app.middleware("http")
    async def add_correlation_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[JSONResponse]],
    ) -> JSONResponse:
        candidate = request.headers.get(CORRELATION_ID_HEADER, "").strip()
        request.state.correlation_id = candidate if candidate else str(uuid.uuid4())
        # Map correlation ID onto the active W3C trace context
        inject_correlation_to_trace(request.state.correlation_id)
        response = await call_next(request)
        if CORRELATION_ID_HEADER not in response.headers:
            response.headers[CORRELATION_ID_HEADER] = request.state.correlation_id
        return response

    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return _error_response(
            request,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            retryable=exc.retryable,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else {}
        location = ".".join(str(item) for item in first_error.get("loc", []))
        message = first_error.get("msg", "Request validation failed.")
        if location:
            message = f"{location}: {message}"
        return _error_response(
            request,
            status_code=400,
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        if exc.status_code == 404:
            code = ErrorCode.NOT_FOUND
        elif exc.status_code == 401:
            code = ErrorCode.INVALID_TOKEN
        elif exc.status_code == 403:
            code = ErrorCode.FORBIDDEN_ROLE
        else:
            code = ErrorCode.VALIDATION_ERROR
        return _error_response(
            request,
            status_code=exc.status_code,
            code=code,
            message=str(exc.detail),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled BFF error",
            extra={"correlation_id": _correlation_id(request)},
            exc_info=exc,
        )
        return _error_response(
            request,
            status_code=500,
            code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred.",
            retryable=True,
        )

    @app.get("/health/live", response_model=HealthStatus, tags=["Health"])
    async def health_live(request: Request) -> HealthStatus:
        return HealthStatus(
            status="ok",
            service=runtime_settings.service_name,
            correlation_id=_correlation_id(request),
        )

    @app.get("/health/ready", response_model=HealthStatus, tags=["Health"])
    async def health_ready(request: Request) -> HealthStatus:
        return HealthStatus(
            status="ok",
            service=runtime_settings.service_name,
            correlation_id=_correlation_id(request),
        )

    @app.get("/v1/meta", response_model=MetaEnvelope, tags=["Bootstrap"])
    async def api_meta(request: Request) -> MetaEnvelope:
        return MetaEnvelope(
            data=MetaData(
                api_version=runtime_settings.api_version,
                service=runtime_settings.service_name,
                environment=runtime_settings.environment,
                demo_mode=runtime_settings.is_demo_mode,
                auth_mode=runtime_settings.auth_mode,
                data_namespace=runtime_settings.data_namespace,
                bridge_contract_version="1.0",
            ),
            as_of=utc_now(),
            correlation_id=_correlation_id(request),
        )

    register_routes(app)
    return app


app = create_app()
