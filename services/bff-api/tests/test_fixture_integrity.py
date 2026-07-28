"""The committed fixture pack is SHA-256 verified at load; guard its bytes."""

from __future__ import annotations

import pytest

from bff_api.repository import _DEFAULT_FIXTURE, _verify_checksums


def test_committed_fixture_pack_passes_checksum_verification() -> None:
    _verify_checksums(_DEFAULT_FIXTURE)


@pytest.mark.parametrize(
    "name",
    sorted(path.name for path in _DEFAULT_FIXTURE.glob("*") if path.is_file()),
)
def test_fixture_files_are_lf_only(name: str) -> None:
    """A CRLF checkout silently breaks every digest and the BFF refuses to boot.

    `.gitattributes` pins the pack to LF; this fails loudly if that is undone.
    """
    assert b"\r" not in (_DEFAULT_FIXTURE / name).read_bytes()
