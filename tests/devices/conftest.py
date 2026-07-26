"""Shared pytest fixtures for device-simulator tests.

Adds the service ``src`` directory to ``sys.path`` so tests import the package
without an install step. Everything runs offline with no external dependencies.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SERVICE = Path(__file__).resolve().parents[2] / "services" / "device-simulator"
_SRC = _SERVICE / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
