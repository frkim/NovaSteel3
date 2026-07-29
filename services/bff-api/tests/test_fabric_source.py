"""Tests for the Fabric Lakehouse read path and its fixture fallback.

No network is touched: the ``FabricQueryClient`` port is driven by an in-memory
fake, exactly mirroring how ``capacity.py`` is unit-tested through
``ArmCapacityClient``.
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from bff_api.config import ConfigurationError, DemoMode, Settings
from bff_api.fabric_source import (
    FabricLakehouseSource,
    FabricUnavailableError,
    KNOWN_DATASETS,
)
from bff_api.main import create_app
from bff_api.repository import DemoRepository


_TABLE_RE = re.compile(r"FROM \[[^\]]+\]\.\[[^\]]+\]\.\[(?P<table>[^\]]+)\]")


class FakeFabricClient:
    """In-memory stand-in for the Fabric SQL analytics endpoint."""

    def __init__(
        self,
        tables: dict[str, list[dict]],
        *,
        fail_tables: set[str] | None = None,
    ) -> None:
        self._tables = tables
        self._fail_tables = fail_tables or set()

    def query(self, statement: str) -> list[dict]:
        match = _TABLE_RE.search(statement)
        table = match.group("table") if match else ""
        if table in self._fail_tables:
            raise RuntimeError("CapacityNotActive")
        return list(self._tables.get(table, []))


def _synthetic_record(event_id: str, *, plant_id: str = "NS-DEMO-LUX-01") -> dict:
    return {
        "event_id": event_id,
        "event_ts": "2026-06-10T08:30:00.000Z",
        "plant_id": plant_id,
        "asset_id": "LUX-BF-01",
        "data_classification": "SYNTHETIC",
        "privacy_label": "DEMO-NONPERSONAL",
        # payload stored as JSON text to exercise envelope reconstruction.
        "payload": '{"sensor_id": "LUX-BF-01-H07", "signal_code": "temp", "value": 1450.0, "unit": "C"}',
    }


def _fabric_tables() -> dict[str, list[dict]]:
    tables = {name: [] for name in KNOWN_DATASETS}
    tables["telemetry"] = [
        _synthetic_record("fabric-telemetry-1"),
        _synthetic_record("fabric-telemetry-2"),
    ]
    return tables


def _settings(**overrides) -> Settings:
    base = dict(
        service_name="test-bff",
        api_version="v1",
        environment="demo",
        demo_mode=DemoMode.LOCAL,
        data_namespace="NS-DEMO-LUX-01",
        cors_origins=("http://localhost:5173",),
        auth_mode="demo",
        demo_clock_rebase=False,
    )
    base.update(overrides)
    return Settings(**base)


def _source(tables=None, *, fail_tables=None) -> FabricLakehouseSource:
    client = FakeFabricClient(
        tables if tables is not None else _fabric_tables(),
        fail_tables=fail_tables,
    )
    return FabricLakehouseSource(client=client, lakehouse="lh_novasteelv3_core")


# --- Fabric source directly ------------------------------------------------


def test_fabric_source_returns_rows_and_synthesizes_manifest() -> None:
    datasets, manifest = _source().load()

    assert [r["event_id"] for r in datasets["telemetry"]] == [
        "fabric-telemetry-1",
        "fabric-telemetry-2",
    ]
    # payload JSON text is reconstructed into a nested dict.
    assert datasets["telemetry"][0]["payload"]["signal_code"] == "temp"
    assert manifest["plant_id"] == "NS-DEMO-LUX-01"
    assert manifest["min_max_event_ts"]["max"] == "2026-06-10T08:30:00.000Z"


def test_fabric_source_prefers_manifest_table_when_present() -> None:
    tables = _fabric_tables()
    tables["manifest"] = [
        {"envelope": '{"scenario_id": "demo-full", "plant_id": "NS-DEMO-LUX-01", "summary": {"lining_rul_p50_days": 21.0}}'}
    ]
    _datasets, manifest = _source(tables).load()

    assert manifest["summary"]["lining_rul_p50_days"] == 21.0


def test_fabric_source_wraps_capacity_errors_as_soft_failure() -> None:
    source = _source(fail_tables={"telemetry"})

    with pytest.raises(FabricUnavailableError):
        source.load()


# --- Repository wiring -----------------------------------------------------


def test_repository_load_reports_fabric_provenance() -> None:
    repository = DemoRepository.load(
        _settings(data_source="fabric"), fabric_source=_source()
    )

    assert repository.source == "fabric-lakehouse:lh_novasteelv3_core"
    assert len(repository.telemetry_rows()) == 2


def test_repository_falls_back_to_fixtures_when_fabric_unavailable() -> None:
    repository = DemoRepository.load(
        _settings(data_source="fabric"),
        fabric_source=_source(fail_tables={"telemetry"}),
    )

    assert repository.source.startswith("fabric-fallback:simulator-fixture:")
    # The committed fixture pack is substantial, proving a real fallback.
    assert len(repository.telemetry_rows()) > 100


def test_fabric_rows_that_are_not_synthetic_are_rejected_loudly() -> None:
    tables = _fabric_tables()
    tampered = _synthetic_record("fabric-telemetry-bad")
    tampered["data_classification"] = "REAL"
    tables["telemetry"] = [tampered]

    with pytest.raises(ValueError, match="SYNTHETIC"):
        DemoRepository.load(
            _settings(data_source="fabric"), fabric_source=_source(tables)
        )


def test_fabric_rows_outside_demo_namespace_are_rejected_loudly() -> None:
    tables = _fabric_tables()
    tables["telemetry"] = [
        _synthetic_record("fabric-telemetry-prod", plant_id="NS-PROD-LUX-01")
    ]

    with pytest.raises(ValueError, match="NS-DEMO"):
        DemoRepository.load(
            _settings(data_source="fabric"), fabric_source=_source(tables)
        )


# --- Config validation -----------------------------------------------------


def test_settings_rejects_unknown_data_source() -> None:
    with pytest.raises(ConfigurationError, match="BFF_DATA_SOURCE"):
        _settings(data_source="warehouse")


def test_from_environment_rejects_unknown_data_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BFF_DATA_SOURCE", "warehouse")

    with pytest.raises(ConfigurationError, match="BFF_DATA_SOURCE"):
        Settings.from_environment()


def test_from_environment_reads_fabric_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BFF_DATA_SOURCE", "fabric")
    monkeypatch.setenv("BFF_FABRIC_LAKEHOUSE", "lh_novasteelv3_core")

    settings = Settings.from_environment()

    assert settings.data_source == "fabric"
    assert settings.fabric_lakehouse == "lh_novasteelv3_core"
    assert settings.fabric_workspace == "NovaSteelV3-Demo"


def test_from_environment_rejects_non_integer_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BFF_FABRIC_QUERY_TIMEOUT_SECONDS", "soon")

    with pytest.raises(ConfigurationError, match="TIMEOUT"):
        Settings.from_environment()


# --- App startup / meta endpoint ------------------------------------------


def test_app_starts_and_meta_tells_truth_when_fabric_unreachable() -> None:
    # data_source=fabric with no endpoint: the real client fails fast, the app
    # must fall back to fixtures rather than crash, and say so on /v1/meta.
    settings = _settings(data_source="fabric", fabric_sql_endpoint="")
    client = TestClient(create_app(settings))

    response = client.get("/v1/meta")

    assert response.status_code == 200
    data_source = response.json()["data"]["dataSource"]
    assert data_source.startswith("fabric-fallback:simulator-fixture:")


def test_meta_reports_fixture_source_by_default() -> None:
    client = TestClient(create_app(_settings()))

    data_source = client.get("/v1/meta").json()["data"]["dataSource"]

    assert data_source == "simulator-fixture:demo-full"
