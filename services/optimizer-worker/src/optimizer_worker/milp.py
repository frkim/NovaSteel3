"""MILP energy-dispatch solver (PuLP/CBC) for the NovaSteel optimizer worker.

Formulates batch load-shifting as a mixed-integer program: choose each
non-urgent batch's start slot to minimize weighted (energy cost + CO₂),
subject to capacity, shift, and hold constraints.  Returns the same dict
shape expected by the BFF contract (via service.py's Strategy switch).

The solver is imported lazily — the heuristic path never requires PuLP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


class SolverUnavailableError(RuntimeError):
    """Raised when PuLP/CBC is not installed or cannot solve."""


@dataclass(frozen=True, slots=True)
class _SlotInfo:
    index: int
    price: float
    carbon: float  # kgCO2e/MWh
    demand: float
    baseline_demand: float


@dataclass(frozen=True, slots=True)
class _BatchInfo:
    batch_id: str
    planned_slot: int
    urgent: bool
    grade: str
    tonnage: float
    energy_mwh: float


def solve_milp(
    *,
    intervals: Sequence[_SlotInfo],
    batches: Sequence[_BatchInfo],
    max_shift_slots: int,
    max_concurrent: int,
    max_hold_minutes: int,
    min_soak_minutes: int,
    co2_weight: float = 1.0,
    cost_weight: float = 1.0,
) -> list[int]:
    """Solve the placement MILP; return chosen slot indices (one per batch, same order).

    Raises SolverUnavailableError if PuLP/CBC is unavailable or the problem is infeasible.
    """
    try:
        import pulp  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SolverUnavailableError(
            "PuLP is required for the MILP solver (pip install pulp)"
        ) from exc

    n_slots = len(intervals)
    n_batches = len(batches)

    prob = pulp.LpProblem("novasteel_energy_dispatch", pulp.LpMinimize)

    # Decision variables: x[b, s] = 1 if batch b is assigned to slot s.
    x: dict[tuple[int, int], Any] = {}
    feasible_slots: list[list[int]] = []

    for b_idx, batch in enumerate(batches):
        if batch.urgent:
            # Urgent batches are pinned to their planned slot.
            slots = [batch.planned_slot]
        else:
            lo = max(0, batch.planned_slot - max_shift_slots)
            hi = min(n_slots - 1, batch.planned_slot + max_shift_slots)
            slots = [
                s for s in range(lo, hi + 1)
                if abs(s - batch.planned_slot) * 15 <= max_hold_minutes
            ]
        if not slots:
            raise SolverUnavailableError(
                f"No feasible slot exists for batch {batch.batch_id}."
            )
        feasible_slots.append(slots)
        for s in slots:
            x[(b_idx, s)] = pulp.LpVariable(f"x_{b_idx}_{s}", cat="Binary")

    # Constraint 1: each batch starts exactly once.
    for b_idx in range(n_batches):
        prob += (
            pulp.lpSum(x[(b_idx, s)] for s in feasible_slots[b_idx]) == 1,
            f"assign_{b_idx}",
        )

    # Constraint 2: at most max_concurrent batches per slot.
    for s in range(n_slots):
        occupying = [
            x[(b_idx, s)]
            for b_idx in range(n_batches)
            if s in feasible_slots[b_idx]
        ]
        if occupying:
            prob += (
                pulp.lpSum(occupying) <= max_concurrent,
                f"capacity_{s}",
            )

    # Objective: minimize weighted (CO₂ + cost) with deterministic tie-break.
    # Tie-break term: tiny penalty proportional to distance from planned slot
    # and slot index to ensure unique optimum (determinism).
    epsilon = 1e-6
    obj_terms = []
    for b_idx, batch in enumerate(batches):
        for s in feasible_slots[b_idx]:
            slot_info = intervals[s]
            primary = (
                co2_weight * batch.energy_mwh * slot_info.carbon
                + cost_weight * batch.energy_mwh * slot_info.price
            )
            tie_break = epsilon * (abs(s - batch.planned_slot) + epsilon * s)
            obj_terms.append((primary + tie_break) * x[(b_idx, s)])

    prob += pulp.lpSum(obj_terms)

    # Solve with CBC, deterministic settings.
    solver = pulp.PULP_CBC_CMD(msg=False, threads=1)
    prob.solve(solver)

    if pulp.LpStatus[prob.status] != "Optimal":
        raise SolverUnavailableError(
            f"MILP not solved to optimality: {pulp.LpStatus[prob.status]}"
        )

    # Extract assignments with canonical ordering for determinism.
    assignments: list[int] = [0] * n_batches
    for b_idx in range(n_batches):
        for s in feasible_slots[b_idx]:
            val = pulp.value(x[(b_idx, s)])
            if val is not None and val > 0.5:
                assignments[b_idx] = s
                break

    return assignments
