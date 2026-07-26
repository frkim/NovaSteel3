"""Configuration-driven adapter factory with graceful degradation.

When BFF_STORAGE_TABLE_ENDPOINT is set, durable Azure Table Storage adapters
are used; otherwise, the in-memory adapters are selected — matching today's
behaviour for the offline demo and all existing tests.
"""

from __future__ import annotations

import logging
import os

from .base import AuditStorePort, IdempotencyStorePort
from .local_audit import InMemoryAuditStore
from .local_idempotency import InMemoryIdempotencyStore

logger = logging.getLogger(__name__)


def create_audit_store() -> AuditStorePort:
    """Create the appropriate audit store based on environment configuration."""
    endpoint = os.getenv("BFF_STORAGE_TABLE_ENDPOINT", "").strip()
    table_name = os.getenv("BFF_AUDIT_TABLE_NAME", "bffauditlog").strip()

    if endpoint:
        try:
            from .azure_audit import AzureTableAuditStore

            store = AzureTableAuditStore(
                table_endpoint=endpoint, table_name=table_name
            )
            logger.info(
                "Audit store: Azure Table Storage (%s/%s)", endpoint, table_name
            )
            return store
        except Exception as exc:
            logger.warning(
                "Failed to initialize Azure audit store, falling back to in-memory: %s",
                exc,
            )

    logger.info("Audit store: in-memory (no BFF_STORAGE_TABLE_ENDPOINT configured)")
    return InMemoryAuditStore()


def create_idempotency_store() -> IdempotencyStorePort:
    """Create the appropriate idempotency store based on environment configuration."""
    endpoint = os.getenv("BFF_STORAGE_TABLE_ENDPOINT", "").strip()
    table_name = os.getenv("BFF_IDEMPOTENCY_TABLE_NAME", "bffidempotency").strip()

    if endpoint:
        try:
            from .azure_idempotency import AzureTableIdempotencyStore

            store = AzureTableIdempotencyStore(
                table_endpoint=endpoint, table_name=table_name
            )
            logger.info(
                "Idempotency store: Azure Table Storage (%s/%s)",
                endpoint,
                table_name,
            )
            return store
        except Exception as exc:
            logger.warning(
                "Failed to initialize Azure idempotency store, "
                "falling back to in-memory: %s",
                exc,
            )

    logger.info(
        "Idempotency store: in-memory (no BFF_STORAGE_TABLE_ENDPOINT configured)"
    )
    return InMemoryIdempotencyStore()
