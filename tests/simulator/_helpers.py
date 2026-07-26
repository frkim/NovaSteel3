"""Shared test helpers for the simulator test suite.

Keeps scratch output strictly inside the repository (never the OS temp
directory) by rooting all temporary run directories under
``tests/simulator/.tmp``, which is removed after each test.
"""
from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

TESTS_SIMULATOR_DIR = Path(__file__).resolve().parent
SCRATCH_ROOT = TESTS_SIMULATOR_DIR / ".tmp"


@contextmanager
def scratch_dir(prefix: str = "run-"):
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix=prefix, dir=SCRATCH_ROOT))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
