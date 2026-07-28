"""Binding TBL-STD filtering, sorting, global search, and pagination semantics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from fastapi import Request

from .contracts import ErrorCode
from .errors import ApiError


def apply_table_query(
    *,
    request: Request,
    rows: list[dict[str, Any]],
    columns: Mapping[str, str],
    default_sort: tuple[str, ...],
    primary_time: str,
) -> tuple[list[dict[str, Any]], int, int, int]:
    """Apply the API contract's AND-across-column, OR-within-column semantics."""
    query = request.query_params
    page = _positive_int(query.get("page", "1"), "page")
    size = _positive_int(query.get("size", "50"), "size")
    if size > 200:
        raise ApiError(400, ErrorCode.VALIDATION_ERROR, "size must be at most 200.")

    filters = _column_filters(query.multi_items(), columns)
    filtered = list(rows)
    for column, values in filters.items():
        filtered = [
            row
            for row in filtered
            if any(_matches(row.get(column), value, columns[column]) for value in values)
        ]
    global_query = query.get("q", "").strip().lower()
    if global_query:
        searchable = tuple(columns)
        filtered = [
            row
            for row in filtered
            if any(global_query in str(row.get(column, "")).lower() for column in searchable)
        ]
    filtered = _date_range(filtered, query.get("from"), query.get("to"), primary_time)

    sorts = query.getlist("sort") or list(default_sort)
    for sort in reversed(sorts):
        column, direction = _parse_sort(sort, columns)
        filtered.sort(
            key=lambda row: _sort_value(row.get(column), columns[column]),
            reverse=direction == "desc",
        )
    total = len(filtered)
    start = (page - 1) * size
    return filtered[start : start + size], total, page, size


def _column_filters(
    entries: list[tuple[str, str]], columns: Mapping[str, str]
) -> dict[str, list[str]]:
    reserved = {"page", "size", "sort", "q", "from", "to", "types", "format"}
    filters: dict[str, list[str]] = {}
    for raw_key, raw_value in entries:
        key, value = raw_key, raw_value
        if raw_key == "filter":
            key, separator, value = raw_value.partition(":")
            if not separator:
                raise ApiError(
                    400,
                    ErrorCode.VALIDATION_ERROR,
                    "filter must use column:value syntax.",
                )
        elif ":" in raw_key and not raw_value:
            key, _, value = raw_key.partition(":")
        if key in reserved or key == "site":
            continue
        if key not in columns:
            continue
        filters.setdefault(key, []).append(value)
    return filters


def _matches(value: Any, expression: str, value_type: str) -> bool:
    if value is None:
        return False
    if value_type == "number":
        try:
            numeric = float(value)
            if ".." in expression:
                lower, upper = expression.split("..", 1)
                return float(lower) <= numeric <= float(upper)
            return numeric == float(expression)
        except ValueError as exc:
            raise ApiError(
                400, ErrorCode.VALIDATION_ERROR, f"Invalid numeric filter '{expression}'."
            ) from exc
    if value_type == "date":
        if ".." in expression:
            lower, upper = expression.split("..", 1)
            return lower <= str(value) <= upper
        return expression.lower() in str(value).lower()
    if value_type == "enum":
        return str(value).lower() == expression.lower()
    return expression.lower() in str(value).lower()


def _instant(value: str) -> datetime | None:
    """Parse an ISO-8601 instant, defaulting a missing offset to UTC."""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _date_range(
    rows: list[dict[str, Any]], start: str | None, end: str | None, field: str
) -> list[dict[str, Any]]:
    bounds: dict[str, datetime | None] = {"from": None, "to": None}
    for value, name in ((start, "from"), (end, "to")):
        if value:
            parsed = _instant(value)
            if parsed is None:
                raise ApiError(
                    400, ErrorCode.VALIDATION_ERROR, f"{name} must be an ISO-8601 timestamp."
                )
            bounds[name] = parsed

    lower, upper = bounds["from"], bounds["to"]
    if lower is None and upper is None:
        return rows

    kept: list[dict[str, Any]] = []
    for row in rows:
        raw = str(row.get(field, ""))
        # Compare instants, not strings: "…T00:00:00.000Z" sorts *below*
        # "…T00:00:00Z" lexicographically, which would silently drop rows that
        # carry milliseconds at an exact boundary.
        moment = _instant(raw) if raw else None
        if moment is None:
            if (not start or raw >= start) and (not end or raw <= end):
                kept.append(row)
            continue
        if lower is not None and moment < lower:
            continue
        if upper is not None and moment > upper:
            continue
        kept.append(row)
    return kept


def _parse_sort(value: str, columns: Mapping[str, str]) -> tuple[str, str]:
    column, separator, direction = value.partition(":")
    if (
        not separator
        or direction not in {"asc", "desc"}
        or column not in columns
    ):
        raise ApiError(
            400,
            ErrorCode.VALIDATION_ERROR,
            f"Invalid or unsortable column in sort '{value}'.",
        )
    return column, direction


def _sort_value(value: Any, value_type: str) -> Any:
    if value is None:
        return float("-inf") if value_type == "number" else ""
    return float(value) if value_type == "number" else str(value).lower()


def _positive_int(value: str, name: str) -> int:
    try:
        result = int(value)
    except ValueError as exc:
        raise ApiError(400, ErrorCode.VALIDATION_ERROR, f"{name} must be an integer.") from exc
    if result < 1:
        raise ApiError(400, ErrorCode.VALIDATION_ERROR, f"{name} must be at least 1.")
    return result
