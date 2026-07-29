"""Operational envelope -> Fabric Lakehouse table shaping (the *application*
read layer).

This is the second of the two analytical/operational layers that live in
``lh_novasteelv3_core``:

* The eight ``fact_*`` gold tables (see ``simulator/analytics.py``) feed the
  semantic model / Power BI / KPI trends.
* The nine **operational envelope** tables shaped here feed the *application*:
  the BFF reads them when ``BFF_DATA_SOURCE=fabric`` via
  ``services/bff-api/src/bff_api/fabric_source.py`` and reshapes them back into
  exactly the ``datasets`` structure :class:`DemoRepository` already consumes.

The source of truth for the operational layer is the committed simulator pack
``services/bff-api/fixtures/demo-full/`` (nine NDJSON envelope streams plus
``manifest.json``). This module reshapes those envelopes into loader-ready rows
and the loader (``fabric/notebooks/ns-load-operational-envelopes.Notebook``)
writes them as Delta tables named exactly after the datasets.

Row shape -- why the *JSON-document* column, not a flat row
-----------------------------------------------------------
``bff_api.fabric_source._reconstruct_envelope`` supports two shapes: a flat row
(every envelope field is its own column, ``payload`` carried as JSON text), or a
single column carrying the **whole envelope as a JSON document**. These
envelopes carry a nested, per-schema-typed ``payload`` object (thermal telemetry,
energy intervals, heat batches, ...), so a flat row would need a different,
lossy column set per dataset and would drop or coerce nested typed fields. The
JSON-document shape is a *lossless* round trip: we store the entire envelope as
a string in the ``envelope`` column, and the BFF gets back byte-for-byte the
same dict via ``json.loads``. That also keeps the guardrail fields
(``data_classification``/``privacy_label``/``plant_id``) intact so
``fabric_source._ensure_fabric_safe`` passes rather than tripping on a lossy
round trip.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from simulator import GENERATOR_VERSION, config
from simulator.checksum import write_checksums
from simulator.writer import read_ndjson, write_ndjson

# The nine NDJSON dataset stems the fixture pack ships. This MUST equal
# bff_api.fabric_source.KNOWN_DATASETS (asserted by the round-trip test); it is
# duplicated here so the simulator package has no dependency on the BFF.
OPERATIONAL_DATASETS: tuple[str, ...] = (
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

MANIFEST_TABLE = "manifest"
EVENT_ID_COLUMN = "event_id"
ENVELOPE_COLUMN = "envelope"

# Idempotency: operational envelope rows are keyed on event_id (mirrors the gold
# tables' per-table idempotency keys); the single-row manifest table is
# overwritten wholesale on each load. A few datasets (maintenance_event,
# operator_knowledge, truth_ledger) carry no event_id -- and their natural ids
# (work_order_id / interview_id / anomaly_id) are not row-unique -- so the row
# key falls back to a content hash of the envelope, with an occurrence counter
# to keep byte-identical rows distinct. The key is only used for the loader
# MERGE: the BFF reconstructs the record from the ``envelope`` column and
# ignores this column entirely.
OPERATIONAL_IDEMPOTENCY_KEY = EVENT_ID_COLUMN


class OperationalPackError(ValueError):
    pass


def _canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _base_key(env: dict, envelope_json: str) -> str:
    event_id = env.get("event_id")
    if event_id:
        return str(event_id)
    return "sha256:" + hashlib.sha256(envelope_json.encode("utf-8")).hexdigest()[:32]


def shape_dataset_rows(envelopes: list[dict]) -> list[dict]:
    """Shape envelope records into ``{event_id, envelope}`` rows.

    The ``event_id`` column carries a stable, unique idempotency key: the
    envelope's ``event_id`` when present, else a content hash; a per-key
    occurrence counter keeps any byte-identical rows distinct so no record is
    ever dropped.
    """
    rows: list[dict] = []
    counts: dict[str, int] = {}
    for env in envelopes:
        envelope_json = _canonical(env)
        base = _base_key(env, envelope_json)
        n = counts.get(base, 0)
        counts[base] = n + 1
        key = base if n == 0 else f"{base}#{n}"
        rows.append({EVENT_ID_COLUMN: key, ENVELOPE_COLUMN: envelope_json})
    return rows


def shape_manifest_rows(manifest: dict) -> list[dict]:
    """Shape the demo manifest into the single-row ``manifest`` table."""
    return [{ENVELOPE_COLUMN: _canonical(manifest)}]


def shape_pack(pack_dir: Path) -> dict[str, list[dict]]:
    """Read the committed pack and return ``{table_name: rows}`` in memory.

    Includes every operational dataset present in the pack plus the ``manifest``
    table. No disk output; used directly by the offline round-trip test.
    """
    pack_dir = Path(pack_dir)
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.exists():
        raise OperationalPackError(f"no manifest.json under {pack_dir}")
    tables: dict[str, list[dict]] = {}
    for name in OPERATIONAL_DATASETS:
        ndjson_path = pack_dir / f"{name}.ndjson"
        if not ndjson_path.exists():
            continue
        tables[name] = shape_dataset_rows(read_ndjson(ndjson_path))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tables[MANIFEST_TABLE] = shape_manifest_rows(manifest)
    return tables


def export_operational_pack(pack_dir: Path, out_dir: Path) -> dict:
    """Reshape the committed pack into loader-ready NDJSON table files.

    Writes ``<table>.ndjson`` for every operational dataset plus
    ``manifest.ndjson``, then a ``checksums.json`` so the upload is verifiable.
    Deterministic: NDJSON is written with sorted keys and stable separators.
    """
    pack_dir = Path(pack_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tables = shape_pack(pack_dir)
    filenames: list[str] = []
    row_counts: dict[str, int] = {}
    for name, rows in tables.items():
        path = out_dir / f"{name}.ndjson"
        write_ndjson(path, rows)
        filenames.append(path.name)
        row_counts[name] = len(rows)

    export_manifest = {
        "kind": "operational-envelopes",
        "source_pack": str(pack_dir).replace("\\", "/"),
        "generator_version": GENERATOR_VERSION,
        "data_classification": config.DATA_CLASSIFICATION,
        "privacy_label": config.PRIVACY_LABEL,
        "datasets": list(OPERATIONAL_DATASETS),
        "manifest_table": MANIFEST_TABLE,
        "idempotency_key": OPERATIONAL_IDEMPOTENCY_KEY,
        "row_counts": row_counts,
        "envelope_column": ENVELOPE_COLUMN,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    export_manifest_path = out_dir / "export-manifest.json"
    export_manifest_path.write_text(json.dumps(export_manifest, indent=2, sort_keys=True),
                                    encoding="utf-8", newline="\n")
    filenames.append(export_manifest_path.name)

    write_checksums(out_dir, filenames)
    return {"out_dir": out_dir, "row_counts": row_counts, "tables": tables,
            "export_manifest": export_manifest}
