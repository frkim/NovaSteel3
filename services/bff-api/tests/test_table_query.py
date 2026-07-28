"""TBL-STD date-range semantics: boundary rows must not be lost to string compare."""

from __future__ import annotations

import pytest

from bff_api.errors import ApiError
from bff_api.table import _date_range

ROWS = [
    {"event_ts": "2026-07-27T23:59:59.500Z"},
    {"event_ts": "2026-07-28T00:00:00.000Z"},
    {"event_ts": "2026-07-28T06:15:00Z"},
    {"event_ts": "2026-07-29T00:00:00.000Z"},
]


def test_lower_bound_includes_fractional_second_row_at_the_exact_boundary() -> None:
    kept = _date_range(ROWS, "2026-07-28T00:00:00Z", None, "event_ts")

    assert [row["event_ts"] for row in kept] == [
        "2026-07-28T00:00:00.000Z",
        "2026-07-28T06:15:00Z",
        "2026-07-29T00:00:00.000Z",
    ]


def test_single_day_window_selects_that_day_only() -> None:
    kept = _date_range(ROWS, "2026-07-28T00:00:00Z", "2026-07-28T23:59:59Z", "event_ts")

    assert [row["event_ts"] for row in kept] == [
        "2026-07-28T00:00:00.000Z",
        "2026-07-28T06:15:00Z",
    ]


def test_offsets_are_normalised_before_comparison() -> None:
    rows = [{"event_ts": "2026-07-28T02:00:00+02:00"}]

    assert _date_range(rows, "2026-07-28T00:00:00Z", "2026-07-28T00:00:00Z", "event_ts") == rows


def test_unparseable_bound_is_rejected() -> None:
    with pytest.raises(ApiError):
        _date_range(ROWS, "not-a-timestamp", None, "event_ts")
