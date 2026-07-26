"""Paced live publishing to an HTTP sink (docs section 7, 11).

Compatible with a Fabric Eventstream **Custom Endpoint** (HTTPS POST,
bearer-token authenticated, no SAS key -- see
``docs/architecture/deployment-topology.md``) or a local BFF ingestion
stub used for development. The sink contract is intentionally simple and
generic: an HTTPS POST of one JSON array of canonical envelopes per batch,
``Content-Type: application/json``, and an optional bearer token read from
an environment variable (never hard-coded).

Only the Python standard library (``urllib.request``) is used.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from simulator.writer import read_ndjson


@dataclass
class PublishResult:
    events_sent: int
    batches_sent: int
    retries: int
    duplicates_replayed: int


def _post_batch(url: str, batch: list[dict], token: str | None, timeout: float = 10.0) -> None:
    body = json.dumps(batch, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response.read()


def publish_ndjson(path: Path, *, sink_url: str, batch_size: int = 1, rate_events_per_second: float = 20.0,
                    token_env: str | None = None, max_retries: int = 3,
                    replay_duplicate_fraction: float = 0.0,
                    sleep_fn: Callable[[float], None] = time.sleep,
                    post_fn: Callable[[str, list[dict], str | None], None] | None = None) -> PublishResult:
    """Paced publish of one NDJSON dataset file to an HTTP sink.

    ``rate_events_per_second`` paces wall-clock delivery (docs "paced live
    publishing"); ``replay_duplicate_fraction`` intentionally re-sends a
    fraction of already-sent events to exercise idempotent-sink handling
    (docs section 7 "deterministic duplicate replay").
    """
    post = post_fn or (lambda url, batch, token: _post_batch(url, batch, token))
    token = os.environ.get(token_env) if token_env else None

    records = read_ndjson(path)
    events_sent = 0
    batches_sent = 0
    retries = 0
    duplicates_replayed = 0

    interval_seconds = batch_size / max(rate_events_per_second, 1e-6)

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        _send_with_retry(post, sink_url, batch, token, max_retries, sleep_fn)
        events_sent += len(batch)
        batches_sent += 1

        if replay_duplicate_fraction > 0 and batch and (i // batch_size) % max(int(1 / replay_duplicate_fraction), 1) == 0:
            _send_with_retry(post, sink_url, batch, token, max_retries, sleep_fn)
            duplicates_replayed += len(batch)

        sleep_fn(interval_seconds)

    return PublishResult(events_sent, batches_sent, retries, duplicates_replayed)


def _send_with_retry(post, sink_url, batch, token, max_retries, sleep_fn) -> None:
    attempt = 0
    while True:
        try:
            post(sink_url, batch, token)
            return
        except (urllib.error.URLError, OSError):
            attempt += 1
            if attempt > max_retries:
                raise
            sleep_fn(min(2 ** attempt * 0.1, 2.0))
