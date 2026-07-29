#!/usr/bin/env python
"""Send NovaSteel synthetic envelopes to a Fabric Eventstream Custom Endpoint.

A Fabric Eventstream *Custom Endpoint* is an Event Hubs compatible ingress: it
authenticates with a Shared Access Signature (SAS), not a bearer token, so the
simulator's generic ``simulator publish`` HTTP sink (bearer POST, designed for a
BFF relay) cannot talk to it directly. This is the thin transport adapter that
carries the *same* simulator-generated NDJSON envelopes into the Custom Endpoint
over the Event Hubs REST ``/messages`` send API, using standard-library HTTP and
an HMAC-SHA256 SAS token only.

The connection details (namespace, entity, SAS key name/value) are read from the
git-ignored settings file written by ``Get-FabricEventstreamEndpoint.ps1`` or
from ``NS_EVENTSTREAM_*`` environment variables. No secret is ever committed.

Every event routes on its top-level ``schema_name`` field, exactly as the
Eventstream ``route-hot-schemas`` SQL operator expects.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_DATASETS = ["telemetry", "alarm_event", "model_inference"]


def build_sas_token(namespace: str, entity: str, key_name: str, key: str, ttl_seconds: int = 3600) -> str:
    """Build an Event Hubs Shared Access Signature token for the entity URI."""
    uri = f"https://{namespace}/{entity}".lower()
    encoded_uri = urllib.parse.quote_plus(uri)
    expiry = int(time.time()) + ttl_seconds
    to_sign = f"{encoded_uri}\n{expiry}".encode("utf-8")
    signature = base64.b64encode(
        hmac.new(key.encode("utf-8"), to_sign, hashlib.sha256).digest()
    )
    signature_encoded = urllib.parse.quote_plus(signature)
    return (
        f"SharedAccessSignature sr={encoded_uri}&sig={signature_encoded}"
        f"&se={expiry}&skn={key_name}"
    )


def load_settings(settings_file: Path | None) -> dict:
    """Resolve connection settings from env vars first, then the local file."""
    env = {
        "fullyQualifiedNamespace": os.environ.get("NS_EVENTSTREAM_NAMESPACE"),
        "eventHubName": os.environ.get("NS_EVENTSTREAM_ENTITY"),
        "sharedAccessKeyName": os.environ.get("NS_EVENTSTREAM_SAS_KEYNAME"),
        "sharedAccessKey": os.environ.get("NS_EVENTSTREAM_SAS_KEY"),
    }
    if all(env.values()):
        return env
    if settings_file and settings_file.exists():
        data = json.loads(settings_file.read_text(encoding="utf-8"))
        return {
            "fullyQualifiedNamespace": data["fullyQualifiedNamespace"],
            "eventHubName": data["eventHubName"],
            "sharedAccessKeyName": data["sharedAccessKeyName"],
            "sharedAccessKey": data["sharedAccessKey"],
        }
    raise SystemExit(
        "No connection settings found. Set NS_EVENTSTREAM_* env vars or run "
        "Get-FabricEventstreamEndpoint.ps1 to produce the local settings file, "
        "then pass --settings-file."
    )


def read_ndjson(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def send_event(namespace: str, entity: str, token: str, envelope: dict, timeout: float = 20.0) -> None:
    url = f"https://{namespace}/{entity}/messages?api-version=2014-01"
    body = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Authorization", token)
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response.read()


def send_with_retry(fn, *, max_retries: int = 4) -> int:
    attempt = 0
    while True:
        try:
            fn()
            return attempt
        except (urllib.error.URLError, OSError):
            attempt += 1
            if attempt > max_retries:
                raise
            time.sleep(min(2 ** attempt * 0.2, 3.0))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="Directory of generated <dataset>.ndjson files")
    parser.add_argument("--datasets", nargs="+", default=DEFAULT_DATASETS)
    parser.add_argument("--settings-file", default=None,
                        help="Git-ignored endpoint settings JSON (default: env vars)")
    parser.add_argument("--rate", type=float, default=20.0, help="Events per second (paced)")
    parser.add_argument("--max-events", type=int, default=0,
                        help="Cap total events sent (0 = no cap); keeps demo bursts cheap")
    parser.add_argument("--replay-duplicate-fraction", type=float, default=0.0)
    args = parser.parse_args(argv)

    settings_file = Path(args.settings_file) if args.settings_file else None
    settings = load_settings(settings_file)
    namespace = settings["fullyQualifiedNamespace"]
    entity = settings["eventHubName"]
    token = build_sas_token(namespace, entity, settings["sharedAccessKeyName"], settings["sharedAccessKey"])

    run_dir = Path(args.run_dir)
    interval = 1.0 / max(args.rate, 1e-6)
    total_sent = 0
    total_retries = 0
    total_dupes = 0

    for dataset in args.datasets:
        path = run_dir / f"{dataset}.ndjson"
        if not path.exists():
            print(f"skipping {dataset}: {path} not found")
            continue
        records = read_ndjson(path)
        sent = 0
        for index, envelope in enumerate(records):
            if args.max_events and total_sent >= args.max_events:
                break
            total_retries += send_with_retry(
                lambda: send_event(namespace, entity, token, envelope))
            sent += 1
            total_sent += 1
            if args.replay_duplicate_fraction > 0 and (
                index % max(int(1 / args.replay_duplicate_fraction), 1) == 0
            ):
                total_retries += send_with_retry(
                    lambda: send_event(namespace, entity, token, envelope))
                total_dupes += 1
            time.sleep(interval)
        print(f"sent {dataset}: {sent} events")
        if args.max_events and total_sent >= args.max_events:
            break

    print(f"total events sent: {total_sent} (retries={total_retries}, duplicates={total_dupes})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
