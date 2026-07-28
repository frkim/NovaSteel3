"""Manifest checksum utilities (docs section 6.1, 10.3).

Each generation run writes a manifest containing row counts, min/max event
times, and per-file checksums so that a run can be verified byte-for-byte
against a previous reference run (determinism) or against a demo rehearsal
(operational reset/checksum control).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_checksums(out_dir: Path, filenames: list[str]) -> dict:
    checksums = {}
    for name in filenames:
        path = out_dir / name
        if path.exists():
            checksums[name] = {
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
    return checksums


def write_checksums(out_dir: Path, filenames: list[str]) -> Path:
    checksums = compute_checksums(out_dir, filenames)
    path = out_dir / "checksums.json"
    # Newline translation would make an identical run produce different bytes on
    # Windows and Linux, and these digests are what the BFF verifies at load.
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(checksums, indent=2, sort_keys=True))
    return path


def verify_checksums(out_dir: Path, expected_path: Path | None = None) -> tuple[bool, list[str]]:
    """Recompute checksums for every file listed in ``checksums.json`` (or
    ``expected_path``) and report any mismatch."""
    expected_path = expected_path or (out_dir / "checksums.json")
    if not expected_path.exists():
        return False, [f"missing checksum manifest: {expected_path}"]
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    problems = []
    for name, meta in expected.items():
        path = out_dir / name
        if not path.exists():
            problems.append(f"missing file: {name}")
            continue
        actual = sha256_file(path)
        if actual != meta.get("sha256"):
            problems.append(f"checksum mismatch: {name}")
    return (len(problems) == 0), problems
