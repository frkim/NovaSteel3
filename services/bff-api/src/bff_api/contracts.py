"""Wire models shared by the foundation routes and error handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for API envelopes."""

    return datetime.now(UTC)


class WireModel(BaseModel):
    """Use the contract's camel-case JSON names while retaining Python naming."""

    model_config = ConfigDict(populate_by_name=True)


class ErrorCode(StrEnum):
    INVALID_TOKEN = "INVALID_TOKEN"
    FORBIDDEN_ROLE = "FORBIDDEN_ROLE"
    FORBIDDEN_SCOPE = "FORBIDDEN_SCOPE"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    IDEMPOTENCY_KEY_REQUIRED = "IDEMPOTENCY_KEY_REQUIRED"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    STALE_APPROVAL = "STALE_APPROVAL"
    DUPLICATE_APPROVAL = "DUPLICATE_APPROVAL"
    RATE_LIMITED = "RATE_LIMITED"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    CAPACITY_STATE_CONFLICT = "CAPACITY_STATE_CONFLICT"
    ERASURE_STATE_CONFLICT = "ERASURE_STATE_CONFLICT"
    SIMULATOR_STATE_CONFLICT = "SIMULATOR_STATE_CONFLICT"
    POLICY_DENIED = "POLICY_DENIED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorEnvelope(WireModel):
    code: ErrorCode
    message: str
    correlation_id: str = Field(alias="correlationId")
    retryable: bool


class HealthStatus(WireModel):
    status: str
    service: str
    correlation_id: str = Field(alias="correlationId")


class MetaData(WireModel):
    api_version: str = Field(alias="apiVersion")
    service: str
    environment: str
    demo_mode: bool = Field(alias="demoMode")
    demo_clock_shift_days: int = Field(alias="demoClockShiftDays")
    auth_mode: str = Field(alias="authMode")
    data_namespace: str = Field(alias="dataNamespace")
    data_source: str = Field(alias="dataSource")
    bridge_contract_version: str = Field(alias="bridgeContractVersion")


class MetaEnvelope(WireModel):
    data: MetaData
    as_of: datetime = Field(alias="asOf")
    correlation_id: str = Field(alias="correlationId")


class DataEnvelope(WireModel):
    data: dict[str, Any]
    as_of: datetime = Field(alias="asOf")
    correlation_id: str = Field(alias="correlationId")
