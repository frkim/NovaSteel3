"""Deterministic waveform generation for device-simulator sensors.

Produces a pure function of ``(sensor_id, tick, seed, scenario,
active_incidents)`` → ``(value, quality, clamped)``. Two calls with identical
arguments always return identical results. No mutable state is used or
modified. Child seeds follow the project-wide SHA-256 derivation from
``simulator/determinism.py``.

See ``docs/data/synthetic-data-and-simulators.md`` section 6.1.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any


def _derive_sensor_seed(sensor_id: str, seed: int, scenario: str) -> int:
    """SHA-256 child seed for one (sensor_id, seed, scenario) triple."""
    key = f"{seed}|{scenario}|{sensor_id}"
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def _waveform_params(sensor_id: str, seed: int, scenario: str) -> tuple[float, float, float, float, float]:
    """Return stable waveform parameters derived from the sensor identity.

    Returns ``(freq1, phase1, freq2, phase2, blend)`` — all deterministic.
    """
    s = _derive_sensor_seed(sensor_id, seed, scenario)
    digest = hashlib.sha256(s.to_bytes(8, "big")).digest()

    def _frac(offset: int) -> float:
        return int.from_bytes(digest[offset : offset + 2], "big") / 65535.0

    freq1 = 0.3 + _frac(0) * 1.4
    phase1 = _frac(2) * 2 * math.pi
    freq2 = 0.5 + _frac(4) * 2.0
    phase2 = _frac(6) * 2 * math.pi
    blend = 0.3 + _frac(8) * 0.4
    return freq1, phase1, freq2, phase2, blend


def _base_value(sensor_id: str, tick: int, seed: int, scenario: str,
                low: float, high: float) -> float:
    """Smooth sinusoidal base in ``[low, high]``, deterministic per tick."""
    freq1, phase1, freq2, phase2, blend = _waveform_params(sensor_id, seed, scenario)
    t = tick * 0.02
    wave = blend * math.sin(freq1 * t + phase1) + (1 - blend) * math.cos(freq2 * t + phase2)
    # wave in approx [-1, 1]; map to [low, high] using 85% of the full range
    mid = (low + high) / 2.0
    half = (high - low) / 2.0 * 0.85
    return mid + half * wave


def _noise_value(sensor_id: str, tick: int, seed: int, low: float, high: float) -> float:
    """Tick-local pseudo-noise, deterministic per (sensor_id, tick, seed)."""
    key = f"{sensor_id}|{tick}|{seed}"
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    raw = int.from_bytes(digest[:4], "big") / (2**32 - 1)
    noise_amp = (high - low) * 0.025
    return (raw - 0.5) * 2 * noise_amp


_DEGRADING_FURNACE_SIGNALS: frozenset[str] = frozenset(
    {"local_heat_flux", "hearth_refractory_estimate", "hearth_shell_temperature"}
)
_COOLING_WATER_SIGNALS: frozenset[str] = frozenset(
    {"cooling_water_flow", "cooling_water_outlet_temperature"}
)
_ENERGY_SPIKE_SIGNALS: frozenset[str] = frozenset({"site_active_power", "spot_price"})
_QUALITY_DRIFT_SIGNALS: frozenset[str] = frozenset(
    {"slab_width_deviation", "mould_level", "coiling_temperature"}
)


def _apply_incident(
    incident_id: str,
    progress: float,
    signal_code: str,
    device_id: str,
    sensor_id: str,
    inc_device: str,
    inc_sensor: str | None,
    value: float,
    low: float,
    high: float,
) -> tuple[float, str]:
    """Apply one incident's effect to a raw value. Returns ``(value, quality)``."""
    affected = False
    if incident_id == "degrading-furnace":
        affected = inc_device == device_id and signal_code in _DEGRADING_FURNACE_SIGNALS
    elif incident_id == "cooling-water-loss":
        affected = inc_device == device_id and signal_code in _COOLING_WATER_SIGNALS
    elif incident_id in ("sensor-drift", "sensor-dropout"):
        affected = inc_sensor == sensor_id
    elif incident_id == "energy-price-spike":
        affected = inc_device == device_id and signal_code in _ENERGY_SPIKE_SIGNALS
    elif incident_id == "quality-drift":
        affected = inc_device == device_id and signal_code in _QUALITY_DRIFT_SIGNALS
    elif incident_id == "edge-outage-recovery":
        affected = inc_device == device_id

    if not affected:
        return value, "good"

    span = high - low

    if incident_id == "degrading-furnace":
        if signal_code == "local_heat_flux":
            value += span * 0.45 * progress
        elif signal_code == "hearth_refractory_estimate":
            value -= span * 0.35 * progress
        elif signal_code == "hearth_shell_temperature":
            value += span * 0.28 * progress

    elif incident_id == "cooling-water-loss":
        if signal_code == "cooling_water_flow":
            value = low + max(0.0, value - low) * (1.0 - 0.92 * progress)
        elif signal_code == "cooling_water_outlet_temperature":
            value += span * 0.55 * progress

    elif incident_id == "sensor-drift":
        value += span * 0.22 * progress

    elif incident_id == "sensor-dropout":
        return value, "bad"

    elif incident_id == "energy-price-spike":
        spike_factor = math.sin(math.pi * progress)
        if signal_code == "spot_price":
            value += span * 0.30 * spike_factor
        elif signal_code == "site_active_power":
            value += span * 0.20 * spike_factor

    elif incident_id == "quality-drift":
        drift = span * 0.20 * progress
        value += drift

    elif incident_id == "edge-outage-recovery":
        if progress < 0.5:
            return value, "bad"

    return value, "good"


def generate_value(
    sensor_id: str,
    device_id: str,
    signal_code: str,
    tick: int,
    seed: int,
    scenario: str,
    low: float,
    high: float,
    active_incidents: list[dict[str, Any]],
) -> tuple[float | None, str, bool]:
    """Generate one sensor reading deterministically.

    Parameters
    ----------
    sensor_id:
        Full sensor identifier (``"{deviceId}:{signalCode}"``).
    device_id:
        Parent device/asset identifier.
    signal_code:
        Signal code string from the catalog.
    tick:
        Zero-based tick index for the current engine step.
    seed:
        Global integer seed for this simulation run.
    scenario:
        Scenario name string (used in child-seed derivation).
    low, high:
        Physical plausibility bounds from the catalog.
    active_incidents:
        List of active incident dicts (keys: incidentId, deviceId, sensorId,
        progress). Only incidents relevant to this sensor are applied.

    Returns
    -------
    (value, quality, clamped)
        ``value`` is ``None`` only when the engine decides not to write a
        sample (kept for API consistency; the engine currently always returns
        a float).
    """
    value = _base_value(sensor_id, tick, seed, scenario, low, high)
    value += _noise_value(sensor_id, tick, seed, low, high)

    quality = "good"
    for incident in active_incidents:
        value, q = _apply_incident(
            incident_id=incident["incidentId"],
            progress=incident["progress"],
            signal_code=signal_code,
            device_id=device_id,
            sensor_id=sensor_id,
            inc_device=incident["deviceId"],
            inc_sensor=incident.get("sensorId"),
            value=value,
            low=low,
            high=high,
        )
        if q != "good":
            quality = q

    clamped = False
    if value < low:
        value = low
        clamped = True
    elif value > high:
        value = high
        clamped = True

    return value, quality, clamped
