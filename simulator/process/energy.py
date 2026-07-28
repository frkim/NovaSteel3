"""Energy market and dispatch-optimization model (docs section 3.4, 8.2).

Generates a deterministic 15-minute day-ahead spot-price profile and a
simple, auditable "optimizer" that shifts a small number of eligible
reheat batches away from a scarcity interval. This is intentionally a
transparent, rule-based stand-in for a real optimizer: it only needs to
demonstrate the documented acceptance behavior (lower cost, equal
tonnage, zero hard-constraint violations), not be a production scheduler.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

INTERVALS_PER_DAY = 96  # 15-minute intervals

# Union type for any flexible batch (ReheatBatch or EafHeat).
FlexibleBatch = Union["ReheatBatch", "EafHeat"]


def baseline_price_curve(rng, *, low: float = 55.0, high: float = 115.0) -> list[float]:
    """Smooth diurnal day-ahead price profile in EUR/MWh (baseline-summer)."""
    import math

    prices = []
    for i in range(INTERVALS_PER_DAY):
        hour = i / 4.0
        diurnal = (math.sin((hour - 6.0) / 24.0 * 2 * math.pi) + 1.0) / 2.0
        price = low + (high - low) * diurnal + rng.uniform(-3.0, 3.0)
        prices.append(round(max(low - 5.0, min(price, high + 5.0)), 2))
    return prices


def apply_scarcity_spike(prices: list[float], *, spike_start_interval: int,
                          spike_end_interval: int, spike_price: float = 280.0) -> list[float]:
    """Evening-scarcity style price spike (docs 8.2: one deterministic
    scarcity interval raising spot price to 280 EUR/MWh)."""
    spiked = list(prices)
    for i in range(spike_start_interval, spike_end_interval):
        if 0 <= i < len(spiked):
            spiked[i] = spike_price
    return spiked


@dataclass
class ReheatBatch:
    batch_id: str
    planned_interval: int
    duration_intervals: int
    demand_mw: float
    urgent: bool = False
    max_shift_intervals: int = 12


@dataclass
class EafHeat:
    """A single EAF tap (heat) as a schedulable flexible load.

    EAF heats are genuinely deferrable within a shift window because the
    furnace is idle between taps — unlike reheat batches which are coupled to
    the rolling schedule.  max_shift_intervals is therefore wider (up to 24
    slots = 6 h) reflecting a full production shift.
    """
    batch_id: str
    planned_interval: int
    duration_intervals: int  # 3–4 slots (45–60 min tap-to-tap)
    demand_mw: float         # 80–150 MW per heat
    tonnage: float           # 100–140 t liquid steel per tap
    urgent: bool = False
    max_shift_intervals: int = 24  # 6 h — full shift deferral window


def demand_profile(batches: list[FlexibleBatch], base_load_mw: float = 40.0) -> list[float]:
    profile = [base_load_mw] * INTERVALS_PER_DAY
    for batch in batches:
        for i in range(batch.planned_interval, batch.planned_interval + batch.duration_intervals):
            if 0 <= i < INTERVALS_PER_DAY:
                profile[i] += batch.demand_mw
    return profile


def optimize_schedule(batches: list[FlexibleBatch], prices: list[float],
                       spike_start_interval: int, spike_end_interval: int) -> tuple[list[FlexibleBatch], dict]:
    """Shift eligible (non-urgent) batches whose planned window overlaps the
    scarcity interval to the cheapest nearby slot within their
    ``max_shift_intervals`` hold-time limit.

    Returns the optimized batch list and a diagnostics dict including the
    number of shifted batches and whether any hard constraint (hold-time
    or urgent-batch immutability) was violated.
    """
    optimized: list[FlexibleBatch] = []
    shifted = 0
    violations = 0
    for batch in batches:
        overlaps_spike = any(
            spike_start_interval <= i < spike_end_interval
            for i in range(batch.planned_interval, batch.planned_interval + batch.duration_intervals)
        )
        if batch.urgent or not overlaps_spike:
            optimized.append(batch)
            continue

        best_interval = batch.planned_interval
        best_cost = _batch_cost(batch, prices, batch.planned_interval)
        for shift in range(-batch.max_shift_intervals, batch.max_shift_intervals + 1):
            candidate = batch.planned_interval + shift
            if candidate < 0 or candidate + batch.duration_intervals > INTERVALS_PER_DAY:
                continue
            candidate_overlaps = any(
                spike_start_interval <= i < spike_end_interval
                for i in range(candidate, candidate + batch.duration_intervals)
            )
            if candidate_overlaps:
                continue
            cost = _batch_cost(batch, prices, candidate)
            if cost < best_cost:
                best_cost = cost
                best_interval = candidate

        if best_interval != batch.planned_interval:
            shifted += 1
            if abs(best_interval - batch.planned_interval) > batch.max_shift_intervals:
                violations += 1

        # Reconstruct the batch at the new interval preserving its type.
        if isinstance(batch, EafHeat):
            optimized.append(EafHeat(batch.batch_id, best_interval, batch.duration_intervals,
                                     batch.demand_mw, batch.tonnage, batch.urgent, batch.max_shift_intervals))
        else:
            optimized.append(ReheatBatch(batch.batch_id, best_interval, batch.duration_intervals,
                                          batch.demand_mw, batch.urgent, batch.max_shift_intervals))
    return optimized, {"shifted_batches": shifted, "hard_constraint_violations": violations}


def _batch_cost(batch: FlexibleBatch, prices: list[float], start_interval: int) -> float:
    cost = 0.0
    for i in range(start_interval, start_interval + batch.duration_intervals):
        if 0 <= i < len(prices):
            cost += batch.demand_mw * 0.25 * prices[i]
    return cost


def schedule_cost(batches: list[FlexibleBatch], prices: list[float], base_load_mw: float = 40.0) -> float:
    profile = demand_profile(batches, base_load_mw)
    return sum(mw * 0.25 * price for mw, price in zip(profile, prices))


def planned_tonnage(batches: list[FlexibleBatch], tonnes_per_batch: float = 120.0) -> float:
    """Total tonnage across all batches.

    For EafHeat instances the per-heat tonnage field is used directly;
    for ReheatBatch the fallback ``tonnes_per_batch`` is applied (backward-compatible).
    """
    total = 0.0
    for batch in batches:
        if isinstance(batch, EafHeat):
            total += batch.tonnage
        else:
            total += tonnes_per_batch
    return total
