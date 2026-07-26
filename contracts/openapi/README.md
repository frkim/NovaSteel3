# BFF OpenAPI contracts

`bff-api-v1.yaml` is the machine-readable v1 source of truth. It includes the
public route catalog, shared response envelopes, typed error model, SSE/poll
surface, and idempotency requirements. Additive changes stay in v1; a breaking
change requires a new versioned OpenAPI document and `/v2` path prefix.
