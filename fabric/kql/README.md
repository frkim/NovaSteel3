# KQL operational assets

The deployable database definition is
`items/kql-ns-operations.KQLDatabase/DatabaseSchema.kql`. It creates the five
authoritative hot tables, JSON mappings, reusable functions, and materialized
views with idempotent KQL management commands.

`dashboard-queries.kql` is a read-only query pack for RTI/dashboard validation.
It contains no destructive command and can be run against an empty database.

Retention values are rendered from the environment parameter file:

- `telemetry_hot`: 90 days by default (furnace hot-history target).
- `alarm_hot`: 365 days.
- `gateway_health_hot`: 30 days.
- `model_inference_hot`: 90 days; durable history remains in Delta.
- `ingest_quarantine_hot`: 30 days; durable evidence remains in Lakehouse.

Changing a retention value is a data-governance/cost decision. The Lakehouse is
the governed long-term store; Eventhouse is the operational query layer.
