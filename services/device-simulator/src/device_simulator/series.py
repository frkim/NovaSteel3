"""Time-series window parsing, downsampling, normalisation, and statistics.

All functions are pure (no side effects). ``points`` throughout this module
are dicts with keys ``t`` (ISO-8601 string), ``v`` (float), ``q`` (quality
string).

See ``docs/data/synthetic-data-and-simulators.md`` section 7 and the frozen
``series`` response shape in ``views.py``.
"""

from __future__ import annotations

import math


_WINDOW_ALIASES: dict[str, int] = {
    "15m": 15 * 60,
    "1h": 60 * 60,
    "8h": 8 * 60 * 60,
    "24h": 24 * 60 * 60,
}


def parse_window(window: str) -> int:
    """Parse a window string into seconds.

    Accepted formats: ``"15m"``, ``"1h"``, ``"8h"``, ``"24h"``, or an integer
    string (interpreted as seconds).

    Raises ``ValueError`` for unrecognised formats.
    """
    if window in _WINDOW_ALIASES:
        return _WINDOW_ALIASES[window]
    try:
        return int(window)
    except (ValueError, TypeError):
        raise ValueError(
            f"Unrecognised window {window!r}. "
            f"Expected one of {sorted(_WINDOW_ALIASES)} or an integer (seconds)."
        )


def downsample(points: list[dict], target_count: int) -> list[dict]:
    """Return exactly ``target_count`` evenly-spaced points from ``points``.

    Uses index-based even spacing (not time-based). If ``len(points) <=
    target_count`` the original list is returned unchanged. If ``points`` is
    empty or ``target_count <= 0`` an empty list is returned.
    """
    n = len(points)
    if target_count <= 0 or n == 0:
        return []
    if n <= target_count:
        return list(points)

    step = n / target_count
    return [points[int(i * step)] for i in range(target_count)]


def normalize_points(points: list[dict], low: float, high: float) -> list[dict]:
    """Map ``v`` values linearly into ``[0, 1]`` using catalog ``[low, high]``.

    Returns a new list of dicts with the same ``t`` key and normalised ``v``.
    Values outside ``[low, high]`` are clamped.
    """
    span = high - low
    result = []
    for p in points:
        raw = p["v"]
        if span == 0.0:
            nv = 0.5
        else:
            nv = max(0.0, min(1.0, (raw - low) / span))
        result.append({"t": p["t"], "v": nv})
    return result


def compute_stats(points: list[dict]) -> dict:
    """Compute min/max/mean/stdDev/last over the ``v`` field of ``points``.

    Returns a dict with float values (all ``None`` when ``points`` is empty).
    """
    values = [p["v"] for p in points if p.get("v") is not None]
    if not values:
        return {"min": None, "max": None, "mean": None, "stdDev": None, "last": None}

    n = len(values)
    mn = min(values)
    mx = max(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std_dev = math.sqrt(variance)
    last = values[-1]
    return {"min": mn, "max": mx, "mean": mean, "stdDev": std_dev, "last": last}
