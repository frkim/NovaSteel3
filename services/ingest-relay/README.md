# NovaSteel ingest relay

The relay validates canonical envelopes before publishing them to an Eventstream
publisher port. It keeps invalid/conflicting duplicate records in an explicit
quarantine projection and never exposes a user-facing API or curated-data path.
## Layout

```
services/ingest-relay/
├── src/ingest_relay/
│   ├── relay.py         # envelope validation, dedup, quarantine projection
│   └── telemetry.py     # OpenTelemetry setup + ingest counters, JSON logging
├── Dockerfile           # non-root image, protected feed only
└── requirements.txt     # pinned dependencies
```

## Observability

`telemetry.py` configures Azure Monitor OpenTelemetry when
`APPLICATIONINSIGHTS_CONNECTION_STRING` is present and degrades to a silent
no-op otherwise, so the relay runs unchanged offline. It emits accepted,
rejected and quarantined envelope counters and honours
`NOVASTEEL_LOG_FORMAT=json` for structured stdout logging with correlation IDs.

## Container image

The `Dockerfile` installs exclusively from
`packagefeedproxy.microsoft.io/pypi/simple`, runs as a non-root user, and is
built by the `ci-build-services.yml` workflow. No public registry is contacted
at build or run time.
