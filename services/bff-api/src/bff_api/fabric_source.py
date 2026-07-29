"""Fabric Lakehouse SQL analytics read source for the BFF.

This module adds a *second* data source alongside the committed simulator
fixture pack. It reads the same simulator envelope records back out of the
Microsoft Fabric Lakehouse (via its SQL analytics endpoint) and reshapes them
into the exact ``datasets`` + ``manifest`` structure that :class:`DemoRepository`
already consumes, so every repository method and route keeps working unchanged.

Design notes:

* ``FabricQueryClient`` is a narrow *port* (Protocol) so the whole path is
  unit-testable with a fake and needs no network in tests. This mirrors the
  ``ArmCapacityClient`` port + ``ArmCapacityAdapter`` /
  ``UnconfiguredArmCapacityAdapter`` style in ``capacity.py``.
* Every Azure SDK / driver import is lazy (inside functions) so the base image
  can start without those packages installed, matching the
  ``knowledge_orchestrator`` adapters convention.
* A paused F2 capacity, an unreachable endpoint, or a misconfigured workspace is
  treated as a **soft failure** (:class:`FabricUnavailableError`) so the caller
  can fall back to the fixture pack. Non-synthetic or non-``NS-DEMO-`` rows are a
  **safety violation** and are rejected loudly (``ValueError``) — never a
  silent fallback.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Protocol

logger = logging.getLogger(__name__)

# Dataset names are the NDJSON file stems the fixture pack ships and the loader
# writes as Lakehouse tables.
KNOWN_DATASETS: tuple[str, ...] = (
    "telemetry",
    "energy_interval",
    "heat_batch",
    "quality_measurement",
    "model_inference",
    "alarm_event",
    "maintenance_event",
    "operator_knowledge",
    "truth_ledger",
)

# The loader stores the demo manifest as a single-row table; if it is absent the
# manifest is synthesized from the data itself.
MANIFEST_TABLE = "manifest"

# Columns a row may use to carry the full envelope as a JSON document. If none is
# present the row itself is treated as a flat envelope.
_ENVELOPE_DOCUMENT_COLUMNS: tuple[str, ...] = ("envelope", "record", "document", "value")

# Entra token scope for the Fabric SQL analytics endpoint (TDS front door shares
# the Azure SQL resource identifier).
FABRIC_SQL_SCOPE = "https://database.windows.net/.default"


class FabricSourceError(RuntimeError):
    """Base class for Fabric read-path failures."""


class FabricUnavailableError(FabricSourceError):
    """Fabric is paused, unreachable, or misconfigured — safe to fall back."""


class FabricQueryClient(Protocol):
    """Narrow port over the Fabric SQL analytics endpoint (read-only)."""

    def query(self, statement: str) -> list[Mapping[str, Any]]:
        """Execute a read-only statement and return rows as mappings."""


def _reconstruct_envelope(row: Mapping[str, Any]) -> dict[str, Any]:
    """Turn a returned SQL row back into a simulator envelope record.

    Tolerant of two loader shapes: a single column carrying the envelope JSON
    document, or a flat row whose ``payload`` column holds JSON text.
    """
    record = dict(row)
    for column in _ENVELOPE_DOCUMENT_COLUMNS:
        candidate = record.get(column)
        if isinstance(candidate, str) and candidate.strip():
            try:
                decoded = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(decoded, dict):
                return decoded
    payload = record.get("payload")
    if isinstance(payload, str) and payload.strip():
        try:
            record["payload"] = json.loads(payload)
        except json.JSONDecodeError:
            pass
    return record


def _ensure_fabric_safe(datasets: Mapping[str, Iterable[Mapping[str, Any]]]) -> None:
    """Reject non-synthetic / non-demo rows loudly (data-safety invariant)."""
    for records in datasets.values():
        for record in records:
            if "data_classification" not in record:
                continue
            if (
                record.get("data_classification") != "SYNTHETIC"
                or record.get("privacy_label") != "DEMO-NONPERSONAL"
                or (
                    record.get("plant_id") is not None
                    and not str(record["plant_id"]).startswith("NS-DEMO-")
                )
            ):
                raise ValueError(
                    "Fabric-sourced demo data must be explicitly SYNTHETIC, "
                    "DEMO-NONPERSONAL, and in an NS-DEMO-* namespace."
                )


def _latest_event_ts(datasets: Mapping[str, list[dict[str, Any]]]) -> tuple[str | None, str | None]:
    stamps = [
        str(record["event_ts"])
        for records in datasets.values()
        for record in records
        if record.get("event_ts")
    ]
    if not stamps:
        return None, None
    return min(stamps), max(stamps)


def _first_plant_id(datasets: Mapping[str, list[dict[str, Any]]]) -> str:
    for records in datasets.values():
        for record in records:
            plant_id = record.get("plant_id")
            if plant_id:
                return str(plant_id)
    return "NS-DEMO-LUX-01"


@dataclass
class FabricLakehouseSource:
    """Adapter that builds ``datasets`` + ``manifest`` from a Fabric Lakehouse.

    The heavy lifting (SQL + JSON reconstruction) sits behind the
    ``FabricQueryClient`` port, so tests inject a fake and no network is touched.
    """

    client: FabricQueryClient
    lakehouse: str
    datasets: tuple[str, ...] = KNOWN_DATASETS
    schema: str = "dbo"

    @property
    def provenance(self) -> str:
        return f"fabric-lakehouse:{self.lakehouse}"

    @classmethod
    def from_settings(cls, settings: Any) -> "FabricLakehouseSource":
        """Build a network-backed source from settings (lazy Azure import)."""
        client = _FabricSqlClient(
            endpoint=settings.fabric_sql_endpoint,
            lakehouse=settings.fabric_lakehouse,
            timeout_seconds=settings.fabric_query_timeout_seconds,
        )
        return cls(client=client, lakehouse=settings.fabric_lakehouse)

    def _qualify(self, table: str) -> str:
        return f"[{self.lakehouse}].[{self.schema}].[{table}]"

    def _statement(self, table: str) -> str:
        return f"SELECT * FROM {self._qualify(table)}"

    def load(self) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
        """Load datasets + manifest, or raise :class:`FabricUnavailableError`.

        Connectivity / capacity failures are wrapped as a soft failure. The
        synthetic-data safety check runs *after* the network section so its
        ``ValueError`` propagates loudly instead of masquerading as a fallback.
        """
        try:
            datasets: dict[str, list[dict[str, Any]]] = {}
            for name in self.datasets:
                rows = self.client.query(self._statement(name))
                datasets[name] = [_reconstruct_envelope(row) for row in rows]
            manifest = self._load_manifest(datasets)
        except FabricUnavailableError:
            raise
        except Exception as exc:  # capacity paused, driver missing, DNS, auth...
            raise FabricUnavailableError(
                f"Fabric Lakehouse '{self.lakehouse}' is unavailable: {exc}"
            ) from exc

        _ensure_fabric_safe(datasets)
        return datasets, manifest

    def _load_manifest(
        self, datasets: Mapping[str, list[dict[str, Any]]]
    ) -> dict[str, Any]:
        try:
            rows = self.client.query(self._statement(MANIFEST_TABLE))
        except Exception:
            rows = []
        for row in rows:
            manifest = _reconstruct_envelope(row)
            manifest.pop("payload", None)
            if manifest:
                return manifest
        return _synthesize_manifest(datasets)


def _synthesize_manifest(
    datasets: Mapping[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    """Build a minimal manifest when the Lakehouse has no manifest table."""
    minimum, maximum = _latest_event_ts(datasets)
    plant_id = _first_plant_id(datasets)
    return {
        "scenario_id": "demo-full",
        "plant_id": plant_id,
        "data_classification": "SYNTHETIC",
        "privacy_label": "DEMO-NONPERSONAL",
        "row_counts": {name: len(records) for name, records in datasets.items()},
        "min_max_event_ts": {"min": minimum, "max": maximum},
        "summary": {},
    }


@dataclass
class _FabricSqlClient:
    """Managed-identity SQL client for the Fabric analytics endpoint.

    All driver/SDK imports are lazy; nothing here runs (or is imported) unless a
    ``fabric`` data source is actually selected and queried.
    """

    endpoint: str
    lakehouse: str
    timeout_seconds: int = 30
    _connection: Any = field(default=None, init=False, repr=False)

    def query(self, statement: str) -> list[Mapping[str, Any]]:  # pragma: no cover - requires network
        connection = self._connect()
        cursor = connection.cursor()
        try:
            cursor.execute(statement)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def _connect(self) -> Any:  # pragma: no cover - requires network
        if self._connection is not None:
            return self._connection
        if not self.endpoint:
            raise FabricUnavailableError(
                "BFF_FABRIC_SQL_ENDPOINT is not configured."
            )
        import struct

        import pyodbc

        token = self._access_token()
        # SQL_COPT_SS_ACCESS_TOKEN = 1256; token is UTF-16-LE length-prefixed.
        encoded = token.encode("utf-16-le")
        token_struct = struct.pack(f"<I{len(encoded)}s", len(encoded), encoded)
        connection_string = (
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server={self.endpoint};"
            f"Database={self.lakehouse};"
            "Encrypt=yes;TrustServerCertificate=no;"
            f"Connection Timeout={self.timeout_seconds};"
        )
        self._connection = pyodbc.connect(
            connection_string,
            attrs_before={1256: token_struct},
            timeout=self.timeout_seconds,
        )
        return self._connection

    def _access_token(self) -> str:  # pragma: no cover - requires azure-identity
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential()
        return credential.get_token(FABRIC_SQL_SCOPE).token


__all__ = [
    "FabricLakehouseSource",
    "FabricQueryClient",
    "FabricSourceError",
    "FabricUnavailableError",
    "KNOWN_DATASETS",
]
