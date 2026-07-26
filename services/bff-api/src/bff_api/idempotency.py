"""In-memory idempotency boundary for all BFF mutations."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, Mapping

from .contracts import ErrorCode
from .errors import ApiError


@dataclass(frozen=True, slots=True)
class StoredResponse:
    request_hash: str
    status_code: int
    body: dict[str, Any]


class IdempotencyStore:
    """Stores a response snapshot per route/key for the local demo lifecycle."""

    def __init__(self) -> None:
        self._responses: dict[tuple[str, str], StoredResponse] = {}

    @staticmethod
    def require_key(value: str | None) -> str:
        if not value:
            raise ApiError(
                400,
                ErrorCode.IDEMPOTENCY_KEY_REQUIRED,
                "An Idempotency-Key header is required.",
            )
        try:
            uuid.UUID(value)
        except (TypeError, ValueError) as exc:
            raise ApiError(
                400,
                ErrorCode.VALIDATION_ERROR,
                "Idempotency-Key must be a UUID.",
            ) from exc
        return value

    def replay_or_none(
        self, *, route: str, key: str, body: Mapping[str, Any]
    ) -> StoredResponse | None:
        saved = self._responses.get((route, key))
        if saved is None:
            return None
        if saved.request_hash != self._hash(body):
            raise ApiError(
                409,
                ErrorCode.IDEMPOTENCY_CONFLICT,
                "This Idempotency-Key was previously used with a different request.",
            )
        return saved

    def store(
        self,
        *,
        route: str,
        key: str,
        body: Mapping[str, Any],
        status_code: int,
        response: Mapping[str, Any],
    ) -> None:
        self._responses[(route, key)] = StoredResponse(
            request_hash=self._hash(body),
            status_code=status_code,
            body=dict(response),
        )

    @staticmethod
    def _hash(body: Mapping[str, Any]) -> str:
        blob = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()
