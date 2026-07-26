"""Deterministic seed derivation (docs section 6.1).

Child seeds are derived with
``SHA-256(root_seed | scenario_id | plant_id | asset_id | signal_code)``,
using the first 64 bits as an unsigned integer. This avoids
process-dependent language hash functions (Python's built-in ``hash()`` is
salted per-process for strings) so the same manifest always yields the same
numeric stream on any machine.
"""
from __future__ import annotations

import hashlib
import random

CHILD_SEED_DERIVATION_VERSION = 1


def derive_child_seed(root_seed: int, scenario_id: str, plant_id: str = "",
                       asset_id: str = "", signal_code: str = "") -> int:
    """Derive a stable 64-bit unsigned child seed for one (scenario, plant,
    asset, signal) tuple."""
    key = "|".join(str(part) for part in (root_seed, scenario_id, plant_id, asset_id, signal_code))
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def child_random(root_seed: int, scenario_id: str, plant_id: str = "",
                  asset_id: str = "", signal_code: str = "") -> random.Random:
    """Return a ``random.Random`` seeded with the derived child seed."""
    return random.Random(derive_child_seed(root_seed, scenario_id, plant_id, asset_id, signal_code))


def config_checksum(manifest_dict: dict) -> str:
    """Stable configuration checksum for a scenario manifest (docs 6.1/10.3).

    Uses ``json.dumps(..., sort_keys=True)`` so field order never affects
    the checksum; this is recorded in the run manifest for reproducibility
    audits.
    """
    import json

    canonical = json.dumps(manifest_dict, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
