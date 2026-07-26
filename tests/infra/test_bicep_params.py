"""Every environment .bicepparam file must compile against main.bicep via `az bicep build-params`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import AZ_CLI_AVAILABLE, ENVIRONMENTS, _az_bicep_build_params

pytestmark = pytest.mark.skipif(
    not AZ_CLI_AVAILABLE, reason="az CLI (with the bicep extension) is not installed"
)


def test_one_bicepparam_file_per_environment(bicepparam_files: list[Path]) -> None:
    names = {f.stem for f in bicepparam_files}
    assert names == set(ENVIRONMENTS), (
        f"expected exactly one .bicepparam per environment {ENVIRONMENTS}, found {sorted(names)}"
    )


def test_every_bicepparam_file_builds_clean(bicepparam_files: list[Path]) -> None:
    failures = []
    for f in bicepparam_files:
        result = _az_bicep_build_params(f)
        if result.returncode != 0:
            failures.append((f, result.stdout + result.stderr))
    if failures:
        details = "\n\n".join(f"{f}:\n{out}" for f, out in failures)
        pytest.fail(f"{len(failures)} .bicepparam file(s) failed to build:\n\n{details}")
