from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from bff_api.config import DemoMode, Settings
from bff_api.repository import (
    _DEFAULT_FIXTURE,
    _parse_iso_instant,
    _rebase_demo_clock,
    _shift_compact_identifier_timestamps,
    _shift_timestamp_string,
    _verify_checksums,
    DemoRepository,
)


def _settings(*, demo_clock_rebase: bool = True) -> Settings:
    return Settings(
        service_name="test-bff",
        api_version="v1",
        environment="demo",
        demo_mode=DemoMode.LOCAL,
        data_namespace="NS-DEMO-LUX-01",
        cors_origins=("http://localhost:5173",),
        auth_mode="demo",
        demo_clock_rebase=demo_clock_rebase,
    )


def test_rebase_uses_whole_day_floor_and_keeps_newest_event_recent() -> None:
    datasets = {"telemetry": [{"event_ts": "2026-06-11T00:00:00.000Z"}]}
    manifest = {
        "start_time": "2026-06-10T00:00:00.000Z",
        "min_max_event_ts": {
            "min": "2026-06-10T00:00:00.000Z",
            "max": "2026-06-11T00:00:00.000Z",
        },
    }
    now = datetime(2026, 7, 28, 11, 33, 51, tzinfo=timezone.utc)

    shifted_datasets, shifted_manifest, shift_days = _rebase_demo_clock(
        datasets, manifest, now=now
    )

    assert shift_days == 47
    assert shifted_datasets["telemetry"][0]["event_ts"] == "2026-07-28T00:00:00.000Z"
    max_event_ts = _parse_iso_instant(shifted_manifest["min_max_event_ts"]["max"])
    assert max_event_ts is not None
    assert timedelta(0) <= now - max_event_ts <= timedelta(hours=24)


def test_rebase_preserves_timestamp_formats() -> None:
    assert (
        _shift_timestamp_string("2026-06-10T01:02:03.123Z", 2)
        == "2026-06-12T01:02:03.123Z"
    )
    assert (
        _shift_timestamp_string("2026-06-10T01:02:03.123456+02:00", 2)
        == "2026-06-12T01:02:03.123456+02:00"
    )
    assert _shift_timestamp_string("2026-06-10", 2) == "2026-06-12"


def test_rebase_does_nothing_when_anchor_is_current_or_future() -> None:
    datasets = {"telemetry": [{"event_ts": "2026-06-11T00:00:00.000Z"}]}
    manifest = {
        "min_max_event_ts": {
            "min": "2026-06-11T00:00:00.000Z",
            "max": "2026-06-11T00:00:00.000Z",
        },
    }

    assert _rebase_demo_clock(
        datasets, manifest, now=datetime(2026, 6, 11, 23, tzinfo=timezone.utc)
    )[2] == 0
    assert _rebase_demo_clock(
        datasets, manifest, now=datetime(2026, 6, 10, 23, tzinfo=timezone.utc)
    )[2] == 0


def test_rebase_recurses_payloads_and_identifier_compact_timestamps() -> None:
    datasets = {
        "model_inference": [
            {
                "event_ts": "2026-06-11T00:00:00.000Z",
                "correlation_id": "run-demo-full-240725",
                "payload": {
                    "feature_snapshot_ts": "2026-06-11T00:00:00.000Z",
                    "inference_id": "INF-LUX-BF01-20260611T0000Z-07",
                    "windows": [{"start": "2026-06-10"}],
                },
            }
        ]
    }
    manifest = {
        "start_time": "2026-06-10T00:00:00.000Z",
        "summary": {"quality_warning_ts": "2026-06-10T04:00:00.000Z"},
        "min_max_event_ts": {
            "min": "2026-06-10T00:00:00.000Z",
            "max": "2026-06-11T00:00:00.000Z",
        },
    }

    shifted_datasets, shifted_manifest, shift_days = _rebase_demo_clock(
        datasets,
        manifest,
        now=datetime(2026, 6, 13, 1, tzinfo=timezone.utc),
    )

    assert shift_days == 2
    record = shifted_datasets["model_inference"][0]
    assert record["event_ts"] == "2026-06-13T00:00:00.000Z"
    assert record["correlation_id"] == "run-demo-full-240725"
    assert record["payload"]["feature_snapshot_ts"] == "2026-06-13T00:00:00.000Z"
    assert record["payload"]["inference_id"] == "INF-LUX-BF01-20260613T0000Z-07"
    assert record["payload"]["windows"][0]["start"] == "2026-06-12"
    assert shifted_manifest["summary"]["quality_warning_ts"] == "2026-06-12T04:00:00.000Z"


def test_compact_identifier_preserves_minutes_or_seconds_shape() -> None:
    assert (
        _shift_compact_identifier_timestamps("INF-20260611T0000Z", 1)
        == "INF-20260612T0000Z"
    )
    assert (
        _shift_compact_identifier_timestamps("INF-20260611T000001Z", 1)
        == "INF-20260612T000001Z"
    )


def test_loading_rebased_fixture_keeps_fixture_bytes_and_checksums_valid() -> None:
    before = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in _DEFAULT_FIXTURE.iterdir()
        if path.is_file()
    }

    repository = DemoRepository.load(_settings(demo_clock_rebase=True))

    after = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in _DEFAULT_FIXTURE.iterdir()
        if path.is_file()
    }
    _verify_checksums(_DEFAULT_FIXTURE)
    assert after == before
    assert repository.demo_clock_shift_days >= 0


def test_rebase_can_be_disabled_for_pinned_fixture_timestamps() -> None:
    repository = DemoRepository.load(_settings(demo_clock_rebase=False))

    assert repository.demo_clock_shift_days == 0
    assert repository.manifest["min_max_event_ts"]["max"] == "2026-06-11T00:00:00.000Z"
