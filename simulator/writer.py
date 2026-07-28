"""Local NDJSON/CSV/JSON dataset writer.

Writes one file per dataset into a run output directory. NDJSON is the
default (matches the streaming event shape 1:1); CSV flattens the
envelope's ``payload`` sub-object for spreadsheet-friendly review; JSON
writes a single pretty-printed array, useful for small reference/lookup
datasets (e.g. the run manifest itself).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


def _flatten(record: dict) -> dict:
    flat = {k: v for k, v in record.items() if k != "payload"}
    payload = record.get("payload")
    if isinstance(payload, dict):
        for k, v in payload.items():
            flat[f"payload_{k}"] = v
    return flat


def write_ndjson(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            fh.write("\n")


def write_csv(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        path.write_text("", encoding="utf-8", newline="\n")
        return
    flat_records = [_flatten(r) for r in records]
    fieldnames: list[str] = []
    for r in flat_records:
        for k in r:
            if k not in fieldnames:
                fieldnames.append(k)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in flat_records:
            writer.writerow(r)


def write_json(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(records, indent=2, sort_keys=True))


def write_dataset(out_dir: Path, dataset_name: str, records: list[dict], fmt: str = "ndjson") -> Path:
    ext = {"ndjson": "ndjson", "csv": "csv", "json": "json"}[fmt]
    path = out_dir / f"{dataset_name}.{ext}"
    if fmt == "ndjson":
        write_ndjson(path, records)
    elif fmt == "csv":
        write_csv(path, records)
    else:
        write_json(path, records)
    return path


def read_ndjson(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
