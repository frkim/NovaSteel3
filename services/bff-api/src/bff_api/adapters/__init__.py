"""Hexagonal adapters for audit and idempotency stores.

Only the in-memory (local) adapters are imported eagerly; the Azure adapters are
imported on demand so the package has zero cloud dependencies for tests/the demo.
"""

from .base import AuditStorePort, IdempotencyStorePort
from .local_audit import InMemoryAuditStore
from .local_idempotency import InMemoryIdempotencyStore

__all__ = [
    "AuditStorePort",
    "IdempotencyStorePort",
    "InMemoryAuditStore",
    "InMemoryIdempotencyStore",
]
