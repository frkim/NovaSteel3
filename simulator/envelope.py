"""Canonical event envelope construction (docs section 4).

Every event emitted by the simulator wraps a ``payload`` in the common
envelope shown in section 4.1 of the specification. ``event_id`` values are
UUIDv7 (time-ordered) but are generated deterministically from the
scenario's derived random stream rather than from wall-clock entropy, so
that repeated runs with the same seed produce byte-identical event IDs.
"""
from __future__ import annotations

import random
from datetime import datetime

from simulator import GENERATOR_VERSION, config
from simulator.clock import iso


def deterministic_uuid7(rng: random.Random, event_ts: datetime) -> str:
    """Build a UUIDv7-shaped identifier from a deterministic RNG stream.

    Layout (RFC 9562): 48-bit big-endian Unix millisecond timestamp,
    4-bit version (0b0111), 12 random bits, 2-bit variant (0b10), 62
    random bits. All "random" bits are drawn from ``rng`` so the value is
    fully reproducible for a given seed and sequence position.
    """
    millis = int(event_ts.timestamp() * 1000) & ((1 << 48) - 1)
    rand_a = rng.getrandbits(12)
    rand_b = rng.getrandbits(62)

    time_hi = millis
    version_and_rand_a = (0x7 << 12) | rand_a
    variant_and_rand_b = (0b10 << 62) | rand_b

    as_int = (time_hi << 80) | (version_and_rand_a << 64) | variant_and_rand_b
    hex_str = f"{as_int:032x}"
    return (
        f"{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}-"
        f"{hex_str[16:20]}-{hex_str[20:32]}"
    )


def build_envelope(*, schema_name: str, event_ts: datetime, ingest_ts: datetime,
                    sequence: int, source_id: str, plant_id: str, asset_id: str,
                    scenario_id: str, correlation_id: str, seed: int, payload: dict,
                    rng: random.Random, schema_version: int = 1) -> dict:
    """Build one canonical event envelope (docs 4.1)."""
    return {
        "schema_name": schema_name,
        "schema_version": schema_version,
        "event_id": deterministic_uuid7(rng, event_ts),
        "event_ts": iso(event_ts),
        "ingest_ts": iso(ingest_ts),
        "sequence": sequence,
        "source_id": source_id,
        "plant_id": plant_id,
        "asset_id": asset_id,
        "scenario_id": scenario_id,
        "correlation_id": correlation_id,
        "data_classification": config.DATA_CLASSIFICATION,
        "privacy_label": config.PRIVACY_LABEL,
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "payload": payload,
    }
