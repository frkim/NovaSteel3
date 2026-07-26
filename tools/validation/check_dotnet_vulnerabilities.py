#!/usr/bin/env python3
"""Fail when `dotnet package list --vulnerable --format json` reports a CVE."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def find_vulnerabilities(value: Any, path: str = "") -> list[tuple[str, dict[str, Any]]]:
    findings: list[tuple[str, dict[str, Any]]] = []
    if isinstance(value, dict):
        vulnerabilities = value.get("vulnerabilities")
        if isinstance(vulnerabilities, list):
            for vulnerability in vulnerabilities:
                if isinstance(vulnerability, dict):
                    findings.append((path, vulnerability))
        for key, child in value.items():
            findings.extend(find_vulnerabilities(child, f"{path}.{key}" if path else key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_vulnerabilities(child, f"{path}[{index}]"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="dotnet JSON output.")
    args = parser.parse_args()

    report = json.loads(args.input.read_text(encoding="utf-8"))
    findings = find_vulnerabilities(report)
    if not findings:
        print("No vulnerable NuGet packages reported.")
        return 0

    print("Vulnerable NuGet packages reported:", file=sys.stderr)
    for path, vulnerability in findings:
        advisory = vulnerability.get("advisoryurl") or vulnerability.get("advisoryUrl") or "unknown"
        severity = vulnerability.get("severity") or "unknown"
        print(f"  {path}: {severity} {advisory}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
