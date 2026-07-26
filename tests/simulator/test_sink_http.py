"""Paced HTTP-sink publishing tests (docs section 7, 11): batching, pacing,
retry, and deterministic duplicate replay against an injected post
function (no real network access needed)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulator.generator import generate_run
from simulator.scenario import load_manifest
from simulator.sink_http import publish_ndjson

from _helpers import scratch_dir


class FakeSink:
    def __init__(self, fail_first_n: int = 0):
        self.batches: list[list[dict]] = []
        self.fail_first_n = fail_first_n
        self._calls = 0

    def post(self, url: str, batch: list[dict], token: str | None) -> None:
        self._calls += 1
        if self._calls <= self.fail_first_n:
            import urllib.error
            raise urllib.error.URLError("simulated transient failure")
        self.batches.append(batch)


class SinkPublishTests(unittest.TestCase):
    def setUp(self):
        self._sleep_calls = []

    def _fake_sleep(self, seconds: float) -> None:
        self._sleep_calls.append(seconds)

    def test_publish_sends_every_event_in_order(self):
        manifest = load_manifest("healthy-baseline")
        with scratch_dir("sink-") as out_dir:
            result = generate_run(manifest, out_dir=out_dir, fast=True)
            path = result.file_paths["telemetry"]

            sink = FakeSink()
            publish_result = publish_ndjson(
                path, sink_url="https://example.invalid/ingest", batch_size=10,
                rate_events_per_second=1_000_000, sleep_fn=self._fake_sleep, post_fn=sink.post,
            )

            total_sent = sum(len(b) for b in sink.batches)
            self.assertEqual(total_sent, len(result.datasets["telemetry"]))
            self.assertEqual(publish_result.events_sent, len(result.datasets["telemetry"]))
            flattened = [r["event_id"] for b in sink.batches for r in b]
            self.assertEqual(flattened, [r["event_id"] for r in result.datasets["telemetry"]])

    def test_publish_retries_transient_failures(self):
        manifest = load_manifest("healthy-baseline")
        with scratch_dir("sink-retry-") as out_dir:
            result = generate_run(manifest, out_dir=out_dir, fast=True)
            path = result.file_paths["telemetry"]

            sink = FakeSink(fail_first_n=2)
            publish_result = publish_ndjson(
                path, sink_url="https://example.invalid/ingest", batch_size=5,
                rate_events_per_second=1_000_000, sleep_fn=self._fake_sleep, post_fn=sink.post,
                max_retries=5,
            )
            self.assertEqual(publish_result.events_sent, len(result.datasets["telemetry"]))

    def test_publish_can_replay_duplicates_for_idempotency_testing(self):
        manifest = load_manifest("healthy-baseline")
        with scratch_dir("sink-dup-") as out_dir:
            result = generate_run(manifest, out_dir=out_dir, fast=True)
            path = result.file_paths["telemetry"]

            sink = FakeSink()
            publish_result = publish_ndjson(
                path, sink_url="https://example.invalid/ingest", batch_size=1,
                rate_events_per_second=1_000_000, sleep_fn=self._fake_sleep, post_fn=sink.post,
                replay_duplicate_fraction=0.5,
            )
            self.assertGreater(publish_result.duplicates_replayed, 0)
            total_batches_sent = len(sink.batches)
            self.assertEqual(total_batches_sent, publish_result.batches_sent + publish_result.duplicates_replayed)


if __name__ == "__main__":
    unittest.main()
