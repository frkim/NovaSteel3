"""Quality and genealogy model with latent multivariate drift (docs 3.5, 8.3).

Drift is latent for the first ``latent_hours`` of the window, then the
(simulated) monitoring model raises an early warning, and only later do
laboratory samples actually go off-spec. This ordering -- warning strictly
before the first off-spec result -- is exactly the acceptance assertion for
seed 240728 (docs section 10.3).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DriftState:
    coiling_temp_bias_c: float
    carbon_equivalent_shift_pct: float
    force_imbalance_pct: float
    off_spec_probability: float


def drift_state_at(elapsed_hours: float, *, latent_hours: float = 12.0,
                    full_drift_hours: float = 36.0,
                    max_temp_bias_c: float = 18.0,
                    max_ceq_shift_pct: float = 0.035,
                    max_force_imbalance_pct: float = 7.0) -> DriftState:
    if elapsed_hours <= latent_hours:
        return DriftState(0.0, 0.0, 0.0, 0.0)
    progressed = min((elapsed_hours - latent_hours) / max(full_drift_hours - latent_hours, 1e-6), 1.0)
    temp_bias = 8.0 + (max_temp_bias_c - 8.0) * progressed
    ceq_shift = 0.015 + (max_ceq_shift_pct - 0.015) * progressed
    force_imbalance = 3.0 + (max_force_imbalance_pct - 3.0) * progressed
    # Off-spec probability only becomes material well after drift onset,
    # matching "visible off-target samples only later" (docs 3.5).
    off_spec_probability = max(0.0, (progressed - 0.5) * 2) * 0.35
    return DriftState(temp_bias, ceq_shift, force_imbalance, off_spec_probability)


def predicted_first_pass_yield(off_spec_probability: float, *, baseline_yield: float = 0.95,
                                floor_yield: float = 0.75) -> float:
    return round(max(0.0, baseline_yield - off_spec_probability * (baseline_yield - floor_yield)), 4)


def carbon_equivalent(c_pct: float, mn_pct: float, cr_pct: float = 0.0, mo_pct: float = 0.0,
                       v_pct: float = 0.0, ni_pct: float = 0.0, cu_pct: float = 0.0) -> float:
    """IIW carbon-equivalent formula, derived (never sampled independently)
    per docs section 3.5/9.2."""
    return round(
        c_pct + mn_pct / 6.0 + (cr_pct + mo_pct + v_pct) / 5.0 + (ni_pct + cu_pct) / 15.0,
        4,
    )
