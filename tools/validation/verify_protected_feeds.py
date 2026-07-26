#!/usr/bin/env python3
"""Fail executable repository content that bypasses protected package feeds.

Markdown is deliberately excluded: policy documents may name prohibited public
endpoints to explain why they are blocked. Comments in executable files are
also ignored so an adjacent explanatory comment does not create a false
positive.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


BLOCKED_ENDPOINTS = (
    "pypi" + ".org/simple",
    "files" + ".pythonhosted.org",
    "api" + ".nuget.org",
    "nuget" + ".org/api/v2",
)

SKIPPED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "artifacts",
    "bin",
    "node_modules",
    "obj",
}

EXECUTABLE_SUFFIXES = {
    ".bicep",
    ".bicepparam",
    ".bat",
    ".cjs",
    ".cmd",
    ".config",
    ".conf",
    ".cs",
    ".csproj",
    ".fs",
    ".fsproj",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".mjs",
    ".nupkg",
    ".nuspec",
    ".pkgproj",
    ".props",
    ".ps1",
    ".psm1",
    ".py",
    ".pyproject",
    ".sh",
    ".targets",
    ".toml",
    ".ts",
    ".tsx",
    ".xml",
    ".yaml",
    ".yml",
}

SPECIAL_FILENAMES = {
    ".npmrc",
    "dockerfile",
    "nuget.config",
    "pip.conf",
}


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    endpoint: str
    content: str


def is_executable_config(path: Path) -> bool:
    name = path.name.lower()
    if path.suffix.lower() in {".md", ".rst"}:
        return False
    if name.startswith("dockerfile") or name in SPECIAL_FILENAMES:
        return True
    if name.startswith("requirements") and path.suffix.lower() == ".txt":
        return True
    return path.suffix.lower() in EXECUTABLE_SUFFIXES


def iter_scannable_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.lower() in SKIPPED_DIRECTORIES for part in path.relative_to(root).parts):
            continue
        if is_executable_config(path):
            yield path


def active_lines(path: Path) -> list[tuple[int, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    lines: list[tuple[int, str]] = []
    in_xml_comment = False
    for number, line in enumerate(text.splitlines(), start=1):
        candidate = line
        if in_xml_comment:
            if "-->" in candidate:
                candidate = candidate.split("-->", 1)[1]
                in_xml_comment = False
            else:
                continue
        if "<!--" in candidate:
            before, after = candidate.split("<!--", 1)
            if "-->" in after:
                candidate = before + after.split("-->", 1)[1]
            else:
                candidate = before
                in_xml_comment = True

        stripped = candidate.lstrip()
        if not stripped or stripped.startswith(("#", ";", "//", "*", "REM ")):
            continue
        lines.append((number, candidate))
    return lines


def scan(root: Path) -> tuple[int, list[Violation]]:
    checked_files = 0
    violations: list[Violation] = []
    for path in iter_scannable_files(root):
        checked_files += 1
        for line_number, content in active_lines(path):
            lower_content = content.lower()
            for endpoint in BLOCKED_ENDPOINTS:
                if endpoint in lower_content:
                    violations.append(
                        Violation(
                            file=path.relative_to(root).as_posix(),
                            line=line_number,
                            endpoint=endpoint,
                            content=content.strip(),
                        )
                    )
    return checked_files, violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root to scan.",
    )
    parser.add_argument("--json", dest="json_path", type=Path, help="Write a JSON report.")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"Repository root does not exist: {root}")

    checked_files, violations = scan(root)
    report = {
        "status": "PASS" if not violations else "FAIL",
        "checkedAtUtc": datetime.now(UTC).isoformat(),
        "checkedFiles": checked_files,
        "blockedEndpointCount": len(BLOCKED_ENDPOINTS),
        "violations": [asdict(violation) for violation in violations],
    }
    if args.json_path:
        output = args.json_path if args.json_path.is_absolute() else root / args.json_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if violations:
        print("Protected-feed policy violations:", file=sys.stderr)
        for violation in violations:
            print(
                f"  {violation.file}:{violation.line}: prohibited {violation.endpoint}",
                file=sys.stderr,
            )
        return 1

    print(f"Protected-feed scan passed ({checked_files} executable/configuration files checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
