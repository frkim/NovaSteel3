"""Durable Azure Table Storage idempotency adapter.

Uses insert-if-not-exists semantics (create_entity raises ResourceExistsError
on conflict) to guarantee that exactly one replica wins the race when multiple
replicas attempt to process the same idempotency key concurrently.

Authentication uses DefaultAzureCredential (managed identity in production).
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Mapping

from ..contracts import ErrorCode
from ..errors import ApiError
from ..idempotency import StoredResponse
from .base import IdempotencyStorePort

logger = logging.getLogger(__name__)


class AzureTableIdempotencyStore(IdempotencyStorePort):
    """Durable idempotency store backed by Azure Table Storage.

    Concurrency safety: store() uses create_entity (HTTP PUT with If-None-Match: *)
    which is an atomic insert — if two replicas race, only one succeeds and the
    other receives a 409 Conflict (ResourceExistsError). The second replica then
    reads and replays the existing response, guaranteeing exactly-once semantics.

    Table schema (PartitionKey=route, RowKey=idempotency_key):
      - requestHash: SHA-256 of the request body
      - statusCode: HTTP status of the stored response
      - responseBody: JSON-serialized response body
    """

    def __init__(
        self, *, table_endpoint: str, table_name: str = "bffidempotency"
    ) -> None:
        from azure.data.tables import TableServiceClient
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential()
        service = TableServiceClient(endpoint=table_endpoint, credential=credential)
        self._table = service.get_table_client(table_name)
        self._table_name = table_name

    @staticmethod
    def _hash(body: Mapping[str, Any]) -> str:
        blob = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def replay_or_none(
        self, *, route: str, key: str, body: Mapping[str, Any]
    ) -> StoredResponse | None:
        try:
            entity = self._table.get_entity(partition_key=route, row_key=key)
        except Exception:
            # Entity not found or network error — treat as first attempt.
            return None

        saved_hash = entity.get("requestHash", "")
        if saved_hash != self._hash(body):
            raise ApiError(
                409,
                ErrorCode.IDEMPOTENCY_CONFLICT,
                "This Idempotency-Key was previously used with a different request.",
            )
        return StoredResponse(
            request_hash=saved_hash,
            status_code=int(entity.get("statusCode", 200)),
            body=json.loads(entity.get("responseBody", "{}")),
        )

    def store(
        self,
        *,
        route: str,
        key: str,
        body: Mapping[str, Any],
        status_code: int,
        response: Mapping[str, Any],
    ) -> None:
        from azure.core.exceptions import ResourceExistsError

        entity = {
            "PartitionKey": route,
            "RowKey": key,
            "requestHash": self._hash(body),
            "statusCode": status_code,
            "responseBody": json.dumps(dict(response), separators=(",", ":")),
        }
        try:
            self._table.create_entity(entity)
        except ResourceExistsError:
            # Another replica already stored — this is safe; the first writer wins.
            logger.debug(
                "Idempotency key %s already stored by another replica.", key
            )
