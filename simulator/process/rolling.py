"""Hot-rolling mill process model (docs section 3.3).

Implements the correlated relationships called out in the specification:
motor current/power rising with rolling force and strip speed, thickness
decreasing through successive stands, and mass-flow conservation within a
documented tolerance.
"""
from __future__ import annotations

from dataclasses import dataclass

STAND_IDS = ["R1", "R2", "F1", "F2", "F3", "F4", "F5", "F6", "F7"]

# Target exit thickness per stand (mm), monotonically decreasing (docs 3.3).
STAND_EXIT_THICKNESS_MM = {
    "R1": 60.0,
    "R2": 32.0,
    "F1": 18.0,
    "F2": 11.0,
    "F3": 7.0,
    "F4": 4.6,
    "F5": 3.2,
    "F6": 2.3,
    "F7": 1.8,
}


@dataclass
class StandObservation:
    stand_id: str
    entry_thickness_mm: float
    exit_thickness_mm: float
    strip_speed_m_s: float
    rolling_force_mn: float
    stand_motor_current_a: float


def mass_flow_kg_s(width_mm: float, thickness_mm: float, speed_m_s: float,
                    density_kg_m3: float = 7850.0) -> float:
    """Steel mass flow rate (kg/s) through one stand cross-section."""
    area_m2 = (width_mm / 1000.0) * (thickness_mm / 1000.0)
    return area_m2 * speed_m_s * density_kg_m3


def stand_observation(*, stand_id: str, entry_thickness_mm: float,
                       volumetric_flow_m2_s: float, width_mm: float, rng) -> StandObservation:
    """Build one stand observation given a conserved volumetric flow
    (``width_m * thickness_m * speed_m_s``), so successive stands respect
    mass conservation by construction (docs 3.3/10.2), before a small
    realistic noise term is layered on top.
    """
    exit_mm = STAND_EXIT_THICKNESS_MM[stand_id]
    reduction = max(entry_thickness_mm - exit_mm, 0.1)
    force_mn = 4.0 + 0.9 * reduction + rng.uniform(-0.4, 0.4)
    force_mn = max(4.0, min(force_mn, 38.0))

    width_m = width_mm / 1000.0
    exit_m = exit_mm / 1000.0
    ideal_speed_m_s = volumetric_flow_m2_s / (width_m * exit_m)
    speed_m_s = ideal_speed_m_s * (1.0 + rng.uniform(-0.002, 0.002))
    speed_m_s = max(0.2, min(speed_m_s, 22.0))

    current_a = 1000.0 + 260.0 * force_mn * (speed_m_s / 5.0) + rng.uniform(-30, 30)
    current_a = max(1000.0, min(current_a, 12000.0))
    return StandObservation(stand_id, entry_thickness_mm, exit_mm, speed_m_s, force_mn, current_a)


def chain_stands(*, base_speed_m_s: float, slab_thickness_mm: float, width_mm: float,
                  rng) -> list[StandObservation]:
    """Roll a slab through all stands, conserving volumetric flow."""
    width_m = width_mm / 1000.0
    slab_thickness_m = slab_thickness_mm / 1000.0
    volumetric_flow_m2_s = width_m * slab_thickness_m * base_speed_m_s

    observations: list[StandObservation] = []
    entry_thickness_mm = slab_thickness_mm
    for stand_id in STAND_IDS:
        obs = stand_observation(stand_id=stand_id, entry_thickness_mm=entry_thickness_mm,
                                 volumetric_flow_m2_s=volumetric_flow_m2_s, width_mm=width_mm,
                                 rng=rng)
        observations.append(obs)
        entry_thickness_mm = obs.exit_thickness_mm
    return observations


def mass_balance_residual_fraction(entry: StandObservation, exit_: StandObservation,
                                    width_mm: float = 1250.0) -> float:
    """Fractional mass-flow imbalance between two successive stands.

    Docs section 10.2 requires rolling mass balance within +/-0.8%.
    """
    m_in = mass_flow_kg_s(width_mm, entry.exit_thickness_mm, entry.strip_speed_m_s)
    m_out = mass_flow_kg_s(width_mm, exit_.exit_thickness_mm, exit_.strip_speed_m_s)
    if m_in <= 1e-9:
        return 0.0
    return (m_out - m_in) / m_in
