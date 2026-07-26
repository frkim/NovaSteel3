"""Executable validation-tool behavior that cannot be asserted by static review."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCANNER = ROOT / "tools" / "validation" / "verify_protected_feeds.py"


def _blocked_index() -> str:
    return "https://" + "pypi" + ".org/simple"


def test_protected_feed_scanner_rejects_code_but_allows_policy_prose() -> None:
    scratch_root = ROOT / "tests" / "simulator" / ".tmp"
    with tempfile.TemporaryDirectory(dir=scratch_root) as directory:
        temporary_root = Path(directory)
        executable = temporary_root / "install.ps1"
        executable.write_text(
            f'python -m pip install --index-url "{_blocked_index()}" example-package\n',
            encoding="utf-8",
        )
        report = temporary_root / "report.json"

        rejected = subprocess.run(
            [sys.executable, str(SCANNER), "--root", str(temporary_root), "--json", str(report)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert rejected.returncode == 1
        assert json.loads(report.read_text(encoding="utf-8"))["violations"]

        executable.unlink()
        report.unlink()
        policy = temporary_root / "docs" / "package-policy.md"
        policy.parent.mkdir()
        policy.write_text(
            f"The endpoint {_blocked_index()} is prohibited by policy.\n",
            encoding="utf-8",
        )
        allowed = subprocess.run(
            [sys.executable, str(SCANNER), "--root", str(temporary_root)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert allowed.returncode == 0, allowed.stderr
