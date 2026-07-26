# Event contracts

Schemas use JSON Schema Draft 2020-12 and are versioned in their filenames and
`schema_name` values. `event_id` is the producer idempotency key. Synthetic
events must carry a demo namespace, scenario, seed, and generator version.

Telemetry payloads use the data specification's `sensor_id`, `signal_code`,
`quality`, `uncertainty`, and `sample_period_ms` fields, alongside the
closed `payload.type` required by the API contract. Model-inference and alarm
payloads retain the documented evidence and lifecycle fields.

`energy-interval.v1` and `quality-measurement.v1` own their corresponding
`energy.interval` and `quality.measurement` payload types; they are not
telemetry payload variants.

Consumers must tolerate additive fields in v1. Removing or changing field
semantics requires a new major schema.
