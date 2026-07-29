"""Offline Fabric operational round-trip test.

This is the linchpin of the two-layer Fabric data work: it proves the demo
tells the *same* story whether the application reads the committed fixture pack
or the Fabric Lakehouse. It takes the committed ``demo-full`` pack, shapes it
with the loader's row-shaping logic (``simulator.fabric_operational``), feeds
the resulting rows into ``bff_api.fabric_source.FabricLakehouseSource`` through
its ``FabricQueryClient`` port with an in-memory fake, and asserts the
reconstructed datasets + manifest are equivalent to what ``DemoRepository``
loads from the fixture pack directly -- same dataset keys, same record counts,
same envelopes, same manifest.

No Spark and no network are involved: the fake client stands in for the Fabric
SQL analytics endpoint, so this runs anywhere the unit tests run.
"""
from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
for source in (
    ROOT / "services" / "bff-api" / "src",
    ROOT,
):
    sys.path.insert(0, str(source))

from bff_api.config import Settings  # noqa: E402
from bff_api.fabric_source import KNOWN_DATASETS, FabricLakehouseSource  # noqa: E402
from bff_api.repository import DemoRepository  # noqa: E402

from simulator.fabric_operational import (  # noqa: E402
    MANIFEST_TABLE,
    OPERATIONAL_DATASETS,
    shape_dataset_rows,
    shape_pack,
)

PACK = ROOT / "services" / "bff-api" / "fixtures" / "demo-full"


class _FakeFabricClient:
    """In-memory stand-in for the Fabric SQL analytics endpoint.

    Answers ``SELECT * FROM [lakehouse].[dbo].[table]`` by returning the shaped
    rows for ``table`` (the last bracketed identifier in the statement).
    """

    def __init__(self, tables: Mapping[str, list[dict[str, Any]]]):
        self._tables = tables

    def query(self, statement: str) -> list[Mapping[str, Any]]:
        table = statement.rsplit("[", 1)[1].rstrip("]")
        return [dict(row) for row in self._tables.get(table, [])]


def _canonical_set(records: list[dict[str, Any]]) -> list[str]:
    return sorted(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in records)


@contextmanager
def _env(**overrides: str):
    saved = {k: os.environ.get(k) for k in overrides}
    try:
        for key, value in overrides.items():
            os.environ[key] = value
        yield
    finally:
        for key, previous in saved.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous


def _load_fixture_repo() -> DemoRepository:
    with _env(
        BFF_DATA_SOURCE="fixture",
        DEMO_CLOCK_REBASE="false",
        BFF_DEMO_DATA_DIRECTORY=str(PACK),
    ):
        settings = Settings.from_environment()
        return DemoRepository.load(settings)


def _load_via_fabric():
    tables = shape_pack(PACK)
    source = FabricLakehouseSource(client=_FakeFabricClient(tables),
                                   lakehouse="lh_novasteelv3_core")
    return source.load()


def test_operational_datasets_match_known_datasets() -> None:
    # The simulator's operational dataset list must equal what the BFF queries.
    assert tuple(OPERATIONAL_DATASETS) == tuple(KNOWN_DATASETS)


def test_shaped_rows_have_unique_idempotency_keys() -> None:
    tables = shape_pack(PACK)
    for name in OPERATIONAL_DATASETS:
        keys = [row["event_id"] for row in tables[name]]
        assert len(keys) == len(set(keys)), f"{name}: duplicate idempotency keys"


def test_fabric_round_trip_matches_fixture_repository() -> None:
    repo = _load_fixture_repo()
    datasets, manifest = _load_via_fabric()

    # Same dataset keys (the nine operational datasets).
    assert set(datasets) == set(KNOWN_DATASETS)
    assert set(datasets) == (set(repo.datasets) & set(KNOWN_DATASETS))

    # Same record counts and same envelopes, per dataset.
    for name in KNOWN_DATASETS:
        fixture_records = repo.datasets[name]
        fabric_records = datasets[name]
        assert len(fabric_records) == len(fixture_records), (
            f"{name}: {len(fabric_records)} via Fabric != {len(fixture_records)} from fixture")
        assert _canonical_set(fabric_records) == _canonical_set(fixture_records), (
            f"{name}: envelopes differ between Fabric round trip and fixture")

    # Same manifest (guardrail fields included).
    assert manifest == repo.manifest


def test_fabric_round_trip_preserves_guardrails() -> None:
    datasets, manifest = _load_via_fabric()
    assert manifest["data_classification"] == "SYNTHETIC"
    assert manifest["privacy_label"] == "DEMO-NONPERSONAL"
    for name in KNOWN_DATASETS:
        for record in datasets[name]:
            if "data_classification" in record:
                assert record["data_classification"] == "SYNTHETIC"
                assert record["privacy_label"] == "DEMO-NONPERSONAL"
            if record.get("plant_id") is not None:
                assert str(record["plant_id"]).startswith("NS-DEMO-")


def test_manifest_table_is_single_row() -> None:
    tables = shape_pack(PACK)
    assert len(tables[MANIFEST_TABLE]) == 1
    assert "envelope" in tables[MANIFEST_TABLE][0]
