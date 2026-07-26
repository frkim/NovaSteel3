# NovaSteel optimizer worker

The worker provides a deterministic, constraint-aware energy-dispatch proposal.
It validates hard production constraints, keeps planned tonnage unchanged, and
returns a proposal only. It has no operational schedule-write capability.

## Model

Dispatch is solved as a mixed-integer program with PuLP and the bundled CBC
solver (`milp.py`): binary start-slot variables, an assign-exactly-once
constraint per batch, a per-slot concurrency capacity limit, and a weighted
CO₂-plus-cost objective. A small epsilon term breaks ties toward the earliest
slot and the solver runs single-threaded, so a given input always yields the
same schedule. If the solver is unavailable the worker falls back to a
deterministic heuristic strategy and reports which strategy produced the
result.

Savings are reported on a **whole-dispatch** basis — the non-flexible base load
is included in both the baseline and optimized figures for cost and CO₂ alike,
so neither metric is flattered by excluding load the optimizer cannot move.
Peak reduction is derived from per-slot load profiles built from the solver's
own placements, so it responds to the schedule rather than restating an input.
The movable-load-only view is exposed additively as `rawFlexibleCostPct` and
`rawFlexibleCo2Pct` for transparency; it is not the headline.

## Dependencies

Requires `pulp` (pinned in `requirements.txt`). Install dependencies only from
`https://packagefeedproxy.microsoft.io/pypi/simple`.
