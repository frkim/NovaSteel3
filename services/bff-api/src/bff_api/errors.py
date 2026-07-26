"""Typed errors that always serialize to the BFF error envelope."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import ErrorCode


@dataclass(slots=True)
class ApiError(Exception):
    """An expected error that the BFF may safely expose to clients."""

    status_code: int
    code: ErrorCode
    message: str
    retryable: bool = False
