"""Sensor observation model (docs section 6.2, 7).

Turns a hidden *true* process value into an observed telemetry value by
layering calibration bias, quantization, heteroscedastic noise, and
realistic missingness/quality flags. Sensor-layer anomalies (bias, freeze,
dropout, spike, drift) are applied here; process-layer anomalies are
applied upstream in the process models.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Observation:
    value: float
    quality: str
    uncertainty: float
    substituted: bool = False


class SensorFaultState:
    """Per-sensor mutable state needed for stateful faults (freeze, drift)."""

    def __init__(self) -> None:
        self.frozen_value: float | None = None
        self.drift_accumulator: float = 0.0


def observe(*, true_value: float, rng, noise_std: float, quantization: float = 0.01,
            fault_type: str = "none", fault_state: SensorFaultState | None = None,
            fault_magnitude: float = 0.0, dropout_probability: float = 0.0005) -> Observation:
    """Apply the observation model to one hidden true value.

    ``fault_type`` is one of ``none``, ``bias``, ``freeze``, ``dropout``,
    ``spike``, ``drift`` (docs section 9.1 ``sensor_fault_type`` label).
    """
    fault_state = fault_state or SensorFaultState()

    # Heteroscedastic noise: larger absolute values get proportionally more noise.
    noise = rng.gauss(0.0, noise_std * (1.0 + abs(true_value) * 1e-4))
    observed = true_value + noise

    quality = "GOOD"
    uncertainty = round(abs(noise_std), 4)
    substituted = False

    if fault_type == "bias":
        observed += fault_magnitude
        quality = "UNCERTAIN"
    elif fault_type == "freeze":
        if fault_state.frozen_value is None:
            fault_state.frozen_value = observed
        observed = fault_state.frozen_value
        quality = "STALE"
    elif fault_type == "spike":
        if rng.random() < 0.05:
            observed += fault_magnitude * rng.choice([-1, 1])
            quality = "UNCERTAIN"
    elif fault_type == "drift":
        fault_state.drift_accumulator += fault_magnitude
        observed += fault_state.drift_accumulator
        quality = "UNCERTAIN"
    elif fault_type == "dropout":
        if rng.random() < max(dropout_probability, 0.2):
            quality = "BAD"
            substituted = True

    if fault_type != "dropout" and rng.random() < dropout_probability:
        quality = "SUBSTITUTED"
        substituted = True

    if quantization > 0:
        observed = round(observed / quantization) * quantization

    return Observation(round(observed, 4), quality, uncertainty, substituted)
