"""Determinism validator (docs section 6.1).

Given the same scenario manifest and seed, two independent generation
runs must match by primary key and numeric value (within floating-point
tolerance). This module compares two ``RunResult``s (or their persisted
``checksums.json``/dataset files) and reports any divergence.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DeterminismReport:
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False


def compare_checksums(checksums_a: dict, checksums_b: dict) -> DeterminismReport:
    report = DeterminismReport()
    keys_a, keys_b = set(checksums_a), set(checksums_b)
    if keys_a != keys_b:
        report.add(f"file sets differ: only-in-a={keys_a - keys_b}, only-in-b={keys_b - keys_a}")
    for name in sorted(keys_a & keys_b):
        sha_a = checksums_a[name].get("sha256")
        sha_b = checksums_b[name].get("sha256")
        if sha_a != sha_b:
            report.add(f"checksum mismatch for {name}: {sha_a} != {sha_b}")
    return report


def compare_datasets(records_a: list[dict], records_b: list[dict], *, dataset_name: str,
                      key_field: str = "event_id") -> DeterminismReport:
    """Compare two runs of the same dataset record-by-record (used when a
    byte-identical file comparison is too strict, e.g. across formats)."""
    report = DeterminismReport()
    if len(records_a) != len(records_b):
        report.add(f"{dataset_name}: row count differs {len(records_a)} != {len(records_b)}")
        return report
    for i, (a, b) in enumerate(zip(records_a, records_b)):
        if a != b:
            report.add(f"{dataset_name}[{i}]: record differs: {a} != {b}")
    return report
