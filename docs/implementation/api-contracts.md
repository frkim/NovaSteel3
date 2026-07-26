# NovaSteel — API Contracts

> **Status:** Implementation-ready v1.0
> **Date:** 2026-07-25
> **Authoritative source:** [`solution-architecture.md`](../architecture/solution-architecture.md) §5.3 and §7 define the binding API shape; [`deployment-topology.md`](../architecture/deployment-topology.md) §5 defines the capacity lifecycle state machine this document exposes as HTTP. The UX table/query semantics come from `docs/ux/dashboard-specification.md` §13 (`TBL-STD`). Where this document adds detail (exact field names, HTTP verbs, status codes) it is a **non-breaking refinement**, not a new decision; any conflict is resolved in favor of the architecture document.
> **Owning todo:** `implementation-pack`
> **Companions:** [`implementation-guide.md`](implementation-guide.md), [`../operations/operations-and-cost.md`](../operations/operations-and-cost.md)

## 0. Conventions used throughout this document

- All HTTP APIs are versioned under `/v1`, JSON-only, TLS-only, and require a valid Entra ID access token (`Authorization: Bearer <token>`), per `solution-architecture.md` §5.3.
- The canonical machine-readable contract lives at `contracts/openapi/bff-api-v1.yaml` (OpenAPI 3.1). This document is the human-readable companion; the OpenAPI file is what generated clients and contract tests consume. If this document and the OpenAPI file ever disagree, the OpenAPI file is corrected to match this document (or vice versa) in the same PR — they must never silently drift.
- Every response includes `correlationId` (a ULID/UUID string) and, where the payload represents a point-in-time read, `asOf` (UTC ISO 8601).
- Every mutating request (`POST`/`PATCH`/`PUT`/`DELETE`) requires an `Idempotency-Key` header (§7).
- Every response uses the shared error envelope (§3) on failure.
- Dates/times are UTC ISO 8601 everywhere on the wire; plant-local time is a presentation-only derived field, never a stored or transmitted value (`synthetic-data-and-simulators.md` §1).

---

## 1. Authentication and authorization

### 1.1 Token model

- The browser (`portal-shell`) acquires a short-lived Entra user access token via MSAL, scoped to the `bff-api` app registration. `analytics-mfe` never stores a raw token; it receives a token reference through the host interop bridge and the actual bearer value is attached to outbound calls by the shell's token broker (`solution-architecture.md` §5.1).
- `bff-api` validates `iss`, `aud`, signature, and expiry on every request using standard JWKS-based validation; it never accepts a self-issued or symmetric-key token.
- Service-to-service calls (`bff-api` → Fabric/Foundry/Speech, workers → Fabric) use managed identities, never a forwarded user token and never an API key, per the identity matrix in `solution-architecture.md` §8.1.

### 1.2 App roles (restated from `implementation-guide.md` §4.1 for contract completeness)

| Role value | Grants |
|---|---|
| `Operator.Read` | Read-only, plant-scoped |
| `ProcessEngineer.Contribute` | Read/contribute, quality+process, assigned plant(s) |
| `EnergyPlanner.Approve` | Read energy; only role for `POST /v1/energy/recommendations/{id}:approve` |
| `MaintenanceEngineer.Read` | Read furnace/prediction routes |
| `DataScientist.ML` | Read/write training-data routes only |
| `PlatformAdmin` | Administrative actions outside this API's user surface (via PIM) |
| `Compliance.Auditor` | Read-only `/v1/audit/decisions` and lineage |
| `Platform.Capacity.Manage` | Only role for `/v1/platform/capacity/{start,pause}-requests` |
| `Knowledge.Publisher` | Only role for `/v1/knowledge/procedures/{id}:approve` |

Canonical business personas map to these stable authorization values rather than inventing UI-only role names: Furnace Operator maps to `Operator.Read`; Quality Engineer maps to `ProcessEngineer.Contribute`; Energy Manager maps to `EnergyPlanner.Approve`; Maintenance/Reliability Engineer maps to `MaintenanceEngineer.Read`; Knowledge Engineer/Admin maps to `Knowledge.Publisher`; Sustainability Officer and Executive receive scoped read/audit projections; Plant Manager receives a plant-scoped union of required read/approval policies. `PlatformAdmin` and `Platform.Capacity.Manage` are restricted supporting roles, not persona-tab authorization shortcuts.

A request lacking the required role for a route receives `403` with `code: "FORBIDDEN_ROLE"` (§3). A request with a valid token but no plant-scope match for the requested resource receives `403` with `code: "FORBIDDEN_SCOPE"`. Both are distinguished so client telemetry and support triage can tell "wrong role" from "wrong plant" without exposing exactly which plants exist to an unauthorized caller — the response body never enumerates the caller's actual permitted scope in an error path, only in `/v1/me` (§4.1).

### 1.3 Demo Mode and token separation

Demo Mode (`portal-shell`'s `demoMode` context flag) never changes which token is used for authentication; it changes only the visual/behavioral surface (simulated capacity control, synthetic banners). The demo (`NS-DEMO-*`) environment uses an entirely separate Entra app registration with no role assignment reaching production scope, so a Demo Mode toggle in the UI is not itself a security boundary — the boundary is the environment's app registration and Fabric workspace isolation (`solution-architecture.md` §2 row "Demo capacity control").

For the offline local deterministic implementation only, the BFF uses explicit
test stubs `X-Demo-User`, `X-Demo-Roles`, and `X-Demo-Plants`; it accepts only
documented app-role values and `NS-DEMO-*` plant scope. The headers are not
accepted outside `DEMO_MODE=local`. Non-demo startup fails closed until an
organization-provided Entra/JWKS validator boundary verifies signature, issuer,
audience, expiry, and not-before.

---

## 2. Common response envelopes

### 2.1 List envelope

Every collection-returning `GET` uses this exact shape:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "size": 50,
  "asOf": "2026-07-25T08:15:10Z",
  "correlationId": "01J9Z8Q3K5F8E2X6R7T4V0M1N2"
}
```

- `page` is 1-based. `size` default `50`, max `200` (larger result sets must page, not request an unbounded size).
- `total` is the total matching row count **after** filters, **before** pagination — required so `TBL-STD` (§5) can render "X of Y" correctly.
- Sparse/large exports use the export endpoints in §5.5 rather than requesting `size=total` in one call.

### 2.2 AI-derived value envelope

Every route returning a model-produced prediction or recommendation uses this exact shape (`solution-architecture.md` §5.3):

```json
{
  "value": 19.65,
  "unit": "d",
  "confidence": { "p10": 18.69, "p50": 19.65, "p90": 20.61 },
  "modelVersion": "lining-rul-piml:1.3.0-demo",
  "scoredAt": "2026-07-25T08:30:00Z",
  "drivers": [{ "name": "heat_flux_6h_slope", "contribution": 0.29 }],
  "sourceRefs": ["event:...", "procedure:..."]
}
```

- `value`/`unit`/`confidence.p50` are always internally consistent (`p10 <= p50 <= p90`); a violating response is a scoring-worker bug, not an acceptable edge case, and is caught by `BE-005`'s contract test (`implementation-guide.md` §6.3).
- `modelVersion` is the exact registered model-registry version string (e.g. `lining-rul-piml:1.3.0-demo`), never `"latest"` — reproducibility requires pinning the version that produced this specific value.
- `drivers` is ordered by `|contribution|` descending; `sourceRefs` are opaque URIs resolvable by `/v1/audit/decisions` (§9) for lineage drill-down.

### 2.3 Single-resource envelope

A single-resource `GET`/`POST`/`PATCH` response wraps the resource under `data`, alongside `asOf` and `correlationId`:

```json
{
  "data": { "id": "wo-demo-lux-1042", "status": "OPEN" },
  "asOf": "2026-07-25T08:15:10Z",
  "correlationId": "01J9Z8Q3K5F8E2X6R7T4V0M1N2"
}
```

---

## 3. Error model

Every non-2xx response uses this exact shape, per `solution-architecture.md` §5.3:

```json
{
  "code": "FORBIDDEN_SCOPE",
  "message": "You do not have access to the requested plant.",
  "correlationId": "01J9Z8Q3K5F8E2X6R7T4V0M1N2",
  "retryable": false
}
```

### 3.1 Standard error codes

| `code` | HTTP status | `retryable` | Meaning |
|---|---|---|---|
| `INVALID_TOKEN` | 401 | false | Missing/expired/malformed Entra token |
| `FORBIDDEN_ROLE` | 403 | false | Valid token, missing required app role |
| `FORBIDDEN_SCOPE` | 403 | false | Valid role, resource outside the caller's plant/persona scope |
| `NOT_FOUND` | 404 | false | Resource does not exist or is outside caller visibility (identical body for both, to avoid existence leakage) |
| `VALIDATION_ERROR` | 400 | false | Request body/query failed schema or business-rule validation; `message` includes the first failing field |
| `IDEMPOTENCY_KEY_REQUIRED` | 400 | false | Mutating request missing `Idempotency-Key` |
| `IDEMPOTENCY_CONFLICT` | 409 | false | Same `Idempotency-Key` reused with a different request body |
| `STALE_APPROVAL` | 409 | false | Approval targets a recommendation/version that has since changed or expired |
| `DUPLICATE_APPROVAL` | 409 | false | Recommendation already has a terminal decision recorded |
| `RATE_LIMITED` | 429 | true | Caller exceeded the route's rate limit; `Retry-After` header present |
| `UPSTREAM_UNAVAILABLE` | 503 | true | A dependency (Fabric query adapter, Foundry, Speech, ARM) is unavailable; caller should retry or fall back |
| `UPSTREAM_STALE` | 200 (payload flagged, not an error status) | n/a | Data returned is served from cache/last-known-good; see `freshness` field (§2.1 extension per route) |
| `CAPACITY_STATE_CONFLICT` | 409 | false | Capacity lifecycle request conflicts with current state (§8) |
| `POLICY_DENIED` | 403 | false | Request is well-formed and authorized by role, but denied by an explicit business/security policy (e.g., allow-list, budget cap, Demo Mode restriction) |
| `INTERNAL_ERROR` | 500 | true | Unhandled server fault; logged with `correlationId` for support triage |

A `503 UPSTREAM_UNAVAILABLE` response is the trigger for the frontend to move to the next fallback-ladder level, per `solution-architecture.md` §9.1; it is never presented to a demo audience as a raw stack trace (`demo-runbook.md` §8).

---

## 4. Route catalog

This restates and completes the route table in `solution-architecture.md` §5.3 with method, request shape, and response shape sufficient to author `contracts/openapi/bff-api-v1.yaml` without further interpretation.

### 4.1 Identity and shell bootstrap

**`GET /v1/me`** — any authenticated user.

Response `data`:

```json
{
  "userId": "u-...",
  "displayName": "Synthetic Operator",
  "roles": ["Operator.Read", "MaintenanceEngineer.Read"],
  "plantScope": ["NS-DEMO-LUX-01"],
  "personas": ["PlantManager", "MaintenanceReliabilityEngineer"],
  "locale": "en-LU",
  "permittedActions": ["furnace.viewForecast", "workorder.createSynthetic"]
}
```

`permittedActions` is a derived, UI-consumable capability list — it is a convenience projection of `roles` + `plantScope`, never an independent authorization source; `bff-api` re-checks role/scope on every subsequent call regardless of what this list said (§1.2).

### 4.2 Command Center

**`GET /v1/command-center/summary?site={siteCode|all}`** — persona-scoped reader.

Response `data`: gold/KQL-backed summary object with per-domain freshness timestamps (energy, CO₂, furnace health, quality, open alerts count), matching the Plant Manager Command Center cockpit in `dashboard-specification.md` §9. Contains no raw personal data at any scope.

### 4.3 Real-time alerts (SSE)

**`GET /v1/realtime/alerts`** (Server-Sent Events) — authorized user. See §6 for the full event contract.

### 4.4 Furnace lining forecast

**`GET /v1/furnaces/{assetId}/lining-forecast`** — assigned plant reader (`MaintenanceEngineer.Read` or higher).

Response `data` is the AI-derived value envelope (§2.2) with `unit: "d"` and an additional `assetId`, `riskLevel` (`LOW|MEDIUM|HIGH`), and `auditRef` linking to `/v1/audit/decisions`.

### 4.5 Energy dispatch

**`POST /v1/energy/schedules:simulate`** — `EnergyPlanner.Approve` or the simulator role.

Request body: `{ "site": "NS-DEMO-LUX-01", "horizonHours": 48, "scenario": "evening-scarcity", "constraints": { ... } }`.

Response `data`: `{ "baseline": {"peakDemandMw": 56.0, ...}, "optimized": {"peakDemandMw": 51.58, ...}, "constraintReport": [{"constraint": "min_soak_time", "status": "SATISFIED"}], "savings": {"costPct": 7.25, "costEur": 2688.7, "peakPct": -7.89, "co2Pct": 3.29, "co2KgBaseline": 169268.99, "co2KgOptimized": 163705.39, "rawFlexibleCostPct": 21.74, "rawFlexibleCo2Pct": 31.71} }`. This route **never** writes an operational schedule; it always returns a proposal (`solution-architecture.md` §5.3). `rawFlexibleCostPct`/`rawFlexibleCo2Pct` report savings over only the movable reheat load (transparency); headlines use whole-dispatch basis (`costPct`/`co2Pct`).

**`POST /v1/energy/recommendations/{id}:approve`** — `EnergyPlanner.Approve` + policy gate.

Request body: `{ "reason": "Evening scarcity peak avoidance", "approvalContext": {"reviewedConstraints": true} }`. Requires `Idempotency-Key`. Phase 0/1 response is always a simulated/shadow state (`{"status": "SIMULATED_APPROVED"}`); Phase 2 additionally validates a separately approved write connector before ever returning `{"status": "COMMITTED"}` — no code path may skip this distinction (`implementation-guide.md` §15 item 3).

**`POST /v1/energy/recommendations/{id}:reject`** — `EnergyPlanner.Approve`.

Request body requires a `reasonCode` from a closed enum (`FR-ENE-05` in `solution-requirements.md` §8.1): `PRODUCTION_CONFLICT | RISK_TOO_HIGH | DATA_QUALITY_CONCERN | OTHER`; `OTHER` requires a free-text `reasonNote`.

### 4.6 Quality

**`GET /v1/quality/batches?site=&grade=&page=&size=&sort=&q=`** — quality-scoped reader. Returns the list envelope (§2.1) filtered by plant/product permission; supports the `TBL-STD` query semantics in §5.

**`GET /v1/quality/batches/{batchId}/genealogy`** — quality-scoped reader. Returns the full genealogy chain (`raw material lots → heat → ladle treatment → slab/billet → reheating → coil/bar → sample → test result → shipment`) per `synthetic-data-and-simulators.md` §3.5.

**`POST /v1/quality/what-if`** — `ProcessEngineer.Contribute`. Request: `{ "batchId": "...", "adjustments": {"coilingTempDeltaC": -8} }`. Response: predicted-vs-current yield delta using the AI-derived value envelope (§2.2); never writes a recipe/setpoint (`solution-architecture.md` §4.2).

### 4.7 Knowledge capture

**`POST /v1/knowledge/interviews`** — knowledge workflow role and recorded consent. Request: `{ "operatorRef": "OP-DEMO-014", "language": "en", "consent": {"granted": true, "scope": "knowledge-capture", "retentionDays": 30} }`. Creates a consent-bound session; response `data.sessionId` is used by the STT/orchestration flow in §10.

**`GET /v1/knowledge/procedures?q=&status=&page=&size=`** — any authenticated user with knowledge-read access. List envelope; `status` filters `DRAFT|IN_REVIEW|APPROVED|REJECTED`.

**`POST /v1/knowledge/procedures/{id}:approve`** — `Knowledge.Publisher` only. Publishes a reviewed immutable version and triggers a derived-index update; a `DRAFT` or `IN_REVIEW` procedure is never independently reachable through general retrieval before this call succeeds (`solution-architecture.md` §4.3 item 6).

**`GET /v1/knowledge/search?q=`** — search-first entry point backed by the derived retrieval index of **approved** procedures only (§5.5 documents the search-specific ranking/highlighting behavior).

### 4.8 Audit

**`GET /v1/audit/decisions?domain=&entityId=&from=&to=&page=&size=`** — `Compliance.Auditor` or the resource's authorized owner. Returns an append-only, export-audited record with model/input/decision/outcome lineage; every field is read-only at the API level — there is no `PATCH`/`DELETE` route for this resource anywhere in the contract.

### 4.9 Platform capacity

See §8 for the full capacity lifecycle contract (`GET /v1/platform/capacity`, `POST /v1/platform/capacity/start-requests`, `POST /v1/platform/capacity/pause-requests`).

### 4.9.1 Additive operational projections

The canonical OpenAPI also exposes additive, read-only projections used by the
local deterministic dashboard and table views: `GET /v1/dashboard/kpis`,
`GET /v1/telemetry`, `GET /v1/furnaces`,
`GET /v1/furnaces/{assetId}/telemetry`, `GET /v1/energy/intervals`,
`GET /v1/energy/recommendations`, `GET /v1/sustainability/summary`, and
`GET /v1/sustainability/emissions`. Collection routes use the same TBL-STD
query semantics in §5; they are advisory/read-only and plant-scoped.

### 4.10 Route summary table

| Route | Method | Auth | Mutating | Idempotency-Key required |
|---|---|---|---|---|
| `/v1/me` | GET | any | no | no |
| `/v1/command-center/summary` | GET | persona reader | no | no |
| `/v1/dashboard/kpis` | GET | persona reader | no | no |
| `/v1/telemetry` | GET | persona reader | no | no |
| `/v1/realtime/alerts` | GET (SSE) | authorized user | no | no |
| `/v1/furnaces` | GET | furnace reader | no | no |
| `/v1/furnaces/{assetId}/telemetry` | GET | furnace reader | no | no |
| `/v1/furnaces/{assetId}/lining-forecast` | GET | `MaintenanceEngineer.Read`+ | no | no |
| `/v1/energy/intervals` | GET | `EnergyPlanner.Approve` | no | no |
| `/v1/energy/recommendations` | GET | `EnergyPlanner.Approve` | no | no |
| `/v1/energy/schedules:simulate` | POST | `EnergyPlanner.Approve` or simulator | no (proposal only) | no |
| `/v1/energy/recommendations/{id}:approve` | POST | `EnergyPlanner.Approve` | yes | **yes** |
| `/v1/energy/recommendations/{id}:reject` | POST | `EnergyPlanner.Approve` | yes | **yes** |
| `/v1/quality/batches` | GET | quality reader | no | no |
| `/v1/quality/batches/{batchId}/genealogy` | GET | quality reader | no | no |
| `/v1/quality/what-if` | POST | `ProcessEngineer.Contribute` | no (simulation only) | no |
| `/v1/sustainability/summary` | GET | persona reader | no | no |
| `/v1/sustainability/emissions` | GET | persona reader | no | no |
| `/v1/knowledge/interviews` | POST | knowledge role + consent | yes | **yes** |
| `/v1/knowledge/procedures` | GET | knowledge read | no | no |
| `/v1/knowledge/procedures/{id}:approve` | POST | `Knowledge.Publisher` | yes | **yes** |
| `/v1/knowledge/search` | GET | any authenticated | no | no |
| `/v1/audit/decisions` | GET | `Compliance.Auditor`/owner | no | no |
| `/v1/platform/capacity` | GET | any authenticated | no | no |
| `/v1/platform/capacity/start-requests` | POST | `Platform.Capacity.Manage` | yes | **yes** |
| `/v1/platform/capacity/pause-requests` | POST | `Platform.Capacity.Manage` | yes | **yes** |
| `/v1/workorders` | POST | `MaintenanceEngineer.Read`+ (create) | yes | **yes** |
| `/v1/workorders/{id}` | GET | assigned plant reader | no | no |

`/v1/workorders` is included here because the demo runbook (`demo-runbook.md` minute 06:00–07:00) requires creating/linking a synthetic work order from an alert; it was implicit in the architecture's alert-acknowledgment flow and is made explicit here for contract completeness.

---

## 5. Search/filter/table query semantics (`TBL-STD`)

This section is the binding HTTP-query contract for every list endpoint, implementing the `TBL-STD` standard defined in `dashboard-specification.md` §13 exactly, so `analytics-mfe`'s shared `DataTable` component can bind to any list route with one adapter.

### 5.1 Query parameters (every list route accepts this exact set)

| Parameter | Type | Behavior |
|---|---|---|
| `page` | integer, 1-based | Default `1` |
| `size` | integer | Default `50`; max `200`; values above max return `400 VALIDATION_ERROR` |
| `sort` | string, `field:asc|desc`, repeatable for multi-column | Default sort is declared per route (e.g., alerts default to `severity:desc,time:desc`); `Shift`+click multi-sort in the UI serializes to repeated `sort` params in URL order |
| `q` | string | Global text search: OR-matches across all searchable columns for that route, case-insensitive, substring match; combines with any `col:value` filters via AND |
| `col:value` (per-column, e.g., `site:NS-DEMO-LUX-01`) | string | Per-column header search: matches only the named column; **type-appropriate** matching per §5.2; multiple distinct `col:value` pairs AND together; repeating the same `col` with different values ORs within that column (multi-select semantics) |
| `from` / `to` | ISO 8601 | Date-range filter on the route's primary time field |
| `site` | string or `all` | Plant/site scope filter; still subject to the caller's authorized `plantScope` (§4.1) — a caller cannot widen scope by omitting this parameter |

### 5.2 Type-appropriate column filtering

| Column type | `col:value` semantics |
|---|---|
| Text | Substring, case-insensitive `contains` match (`message:cooling` matches "Cooling circuit anomaly") |
| Numeric | Range via `col:min..max` (`riskScore:0.7..1.0`); a bare `col:value` on a numeric column is an exact-match shorthand |
| Enum | Multi-select via repeated `col` params (`status:OPEN&status:ACKED`) — OR within the column |
| Date | Range via `col:from..to` in ISO 8601 |

### 5.3 Response shape

List routes return the list envelope (§2.1). `total` reflects rows matching all active filters and `q`, before `page`/`size` windowing — this is what lets the UI render "Showing 1–50 of 3,412" and the "no match for filters" empty state (`dashboard-specification.md` §15 `STATE-EMPTY`) correctly distinguish "no data yet" from "no match."

### 5.4 Sorting contract

- `sort` values must reference a column declared as sortable in the route's OpenAPI schema; an unsortable-column reference returns `400 VALIDATION_ERROR`.
- Multi-column sort is applied in the order the `sort` parameters appear.
- Every route declares a stable default sort so identical queries are reproducible across page loads (required for the demo's deterministic-replay guarantee, `implementation-guide.md` §6.2 `SIM-001`).

### 5.5 Export

**`GET /v1/{resource}:export?format=csv|xlsx|pdf&...same filters as the list route`** — available only on routes marked exportable in `dashboard-specification.md` §13.2 (alerts, furnace units, energy schedule, quality batches/defects, sustainability/audit ledger, site scorecard, capacity transitions, procedures). Export honors the exact same `q`/`col:value`/`sort`/`from`/`to` filters as the on-screen table at request time — it is not a snapshot of a different query. Export is never available on a route carrying Highly Confidential raw content (e.g., raw interview audio) without an explicit separate DLP-reviewed capability, per `security-governance-and-threat-model.md` §7.

### 5.6 Global search route

**`GET /v1/search?q=&types=`** — the shell-level global search (`dashboard-specification.md` §9.5, `S-18`). Returns results grouped by entity type (`alert`, `furnace-unit`, `batch`, `procedure`, `workorder`, ...), each group paginated independently, using the same `q` substring/case-insensitive semantics as §5.1. This is a fan-out convenience over the domain-specific search/list routes, not a separate search index with different ranking rules than `/v1/knowledge/search` for the knowledge-domain group.

---

## 6. WebSocket/SSE events

The architecture specifies SSE (not raw WebSocket) as the real-time transport, with reconnect/poll fallback (`solution-architecture.md` §5.3 route table, row `/v1/realtime/alerts`). This section fixes the exact event framing.

### 6.1 Transport

`GET /v1/realtime/alerts` is a standard SSE stream (`Content-Type: text/event-stream`), authenticated by the same Entra bearer token as any other route (sent once at connection time; SSE has no per-message auth). The connection is kept alive with a `:heartbeat` comment every 15 seconds.

### 6.2 Event types

| SSE `event:` name | Payload | Meaning |
|---|---|---|
| `alert.created` | `{ "alertId", "severity", "site", "assetId", "message", "confidence", "createdAt" }` | New alert raised |
| `alert.updated` | `{ "alertId", "status", "updatedAt" }` | Status transition (e.g., `OPEN → ACKED`) |
| `capacity.transition` | `{ "capacityId", "fromState", "toState", "actor", "correlationId" }` | Capacity lifecycle state change (§8) |
| `freshness.changed` | `{ "domain", "asOf", "stale": true|false }` | Data-freshness signal for a dashboard domain |
| `heartbeat` | none (comment frame) | Keep-alive; absence for >45s is the client's cue to treat the connection as dead |

Every data-bearing event includes a `correlationId` so it can be joined to `/v1/audit/decisions` where applicable.

### 6.3 Reconnect and poll fallback contract

- The client uses the standard SSE `Last-Event-ID` header to resume from its last received event ID on reconnect; the server replays any buffered events newer than that ID from a short (5-minute) in-memory/Redis-backed replay buffer, then resumes live streaming.
- If SSE is unavailable (proxy incompatibility, `503`, or repeated reconnect failure), the client falls back to polling `GET /v1/realtime/alerts:poll?since={lastEventId}` on a 5-second interval; this poll route returns the same event objects as a JSON array `{ "events": [...], "asOf": "..." }` and is a first-class, permanently supported route, not a deprecated stopgap — `solution-architecture.md` §5.3 explicitly requires "reconnect/poll fallback exposes stale state."
- Both transports expose a `stale` flag once the underlying KQL/Fabric source itself reports degraded freshness (`freshness.changed` event / poll response `stale: true`); the frontend renders the `FreshnessBadge` component (`dashboard-specification.md` §9) from this flag, never inferring staleness client-side from elapsed time alone.

### 6.4 Backpressure and rate limits

The server caps outbound event rate per connection at 20 events/second with coalescing (multiple `freshness.changed` events for the same domain within 250ms are merged to the latest); a client exceeding its own processing capacity should rely on the poll fallback rather than the server silently dropping events.

---

## 7. Versioning and idempotency

### 7.1 API versioning

- The path prefix `/v1` is the only version marker; a breaking change ships as `/v2` with both versions live during a documented deprecation window, never an in-place breaking change to `/v1`.
- Additive fields (new optional response properties) do not require a version bump; consumers must tolerate unknown fields (`solution-architecture.md` §3.3 "Consumers tolerate additive fields within a major version").
- Event schemas (`contracts/events`) follow the same rule: additive fields within a `schemaVersion` major number are tolerated; a removal or semantic change requires a new major `schemaVersion`.

### 7.2 Idempotency

- Every mutating route listed with **yes** in §4.10's Idempotency-Key column requires an `Idempotency-Key: <client-generated-UUID>` header.
- `bff-api` stores `(route, idempotencyKey) → (requestHash, responseSnapshot, status)` for 24 hours.
- A repeated request with the same key and an **identical** request body returns the original response (replayed, not re-executed) with the original status code — this is what prevents a double-click "approve" from creating two audit events.
- A repeated request with the same key and a **different** request body returns `409 IDEMPOTENCY_CONFLICT` — the client must generate a new key for a genuinely different request.
- A mutating request without the header returns `400 IDEMPOTENCY_KEY_REQUIRED` before any business logic executes.
- Every successful mutating request emits exactly one append-only audit event (§9), keyed by the same `Idempotency-Key` so a replayed response can be proven not to have duplicated the audit trail.

### 7.3 Optimistic concurrency for approvals

`POST /v1/energy/recommendations/{id}:approve` and `POST /v1/knowledge/procedures/{id}:approve` additionally require the caller to have read the resource's current `version` (returned by the corresponding `GET`) and echo it back as `{"expectedVersion": N}` in the request body. A mismatch (someone else already approved/rejected, or the recommendation was superseded by a fresher model run) returns `409 STALE_APPROVAL`, never a silent overwrite.

---

## 8. Fabric capacity lifecycle: request/status API (full HTTP contract)

This is the HTTP-facing contract implementing the ARM-wrapping behavior fixed in `implementation-guide.md` §7 and the state machine in `deployment-topology.md` §5.1.

### 8.1 `GET /v1/platform/capacity`

Any authenticated user. Read-only; cached safely (`solution-architecture.md` §5.3).

Response `data`:

```json
{
  "capacityId": "cap-novasteel-demo-sc",
  "environment": "demo",
  "state": "Paused",
  "sku": "F2",
  "demoModeSimulated": true,
  "lastTransition": { "toState": "Paused", "at": "2026-07-25T01:00:12Z", "actor": "LogicApp:daily-0100" },
  "stale": false
}
```

If the capacity's real state cannot be determined (ARM unavailable), `state` is the last known value, `stale: true`, and the route still returns `200` — this is a read route, so it degrades to cached/stale rather than erroring, per `solution-architecture.md` §5.3 ("Read-only lifecycle state; cached safely and marked stale if unknown").

### 8.2 `POST /v1/platform/capacity/start-requests`

`Platform.Capacity.Manage` only; requires `Idempotency-Key`.

Request:

```json
{ "capacityId": "cap-novasteel-demo-sc", "reason": "Rehearsal for 14:00 defense session" }
```

Behavior (`deployment-topology.md` §5.4):

1. Validate role, environment/capacity allow-list (never a production capacity ID), no conflicting in-flight transition, and current state is `Paused`. Any failure returns `409 CAPACITY_STATE_CONFLICT` or `403 POLICY_DENIED` as appropriate — never silently queues a second request.
2. If Demo Mode is active for the caller's session, return immediately with `{"status": "SIMULATED", "state": "Running"}` and perform no ARM call at all — Demo Mode is always simulated (`solution-architecture.md` §2 row "Demo capacity control").
3. Outside Demo Mode, log the actor/reason, call ARM `resume?api-version=2023-11-01` via `mi-ns-capacity-demo`, and respond `202`-equivalent as `{"status": "ACCEPTED", "state": "Resuming", "operationId": "..."}`.
4. The client polls `GET /v1/platform/capacity/operations/{operationId}` (below) until `state` reaches `Running` or `Failed`.

### 8.3 `POST /v1/platform/capacity/pause-requests`

Same shape as §8.2, targeting `suspend`. Additionally runs the drain-check precondition (simulator stopped, Event Hubs/relay drained or checkpointed, no protected rehearsal window active, no pipeline/notebook/refresh in a critical phase) before calling ARM; a failed precondition returns `409 CAPACITY_STATE_CONFLICT` with `message` naming the failing precondition, and the capacity is left running (`deployment-topology.md` §5.3 step 4).

### 8.4 `GET /v1/platform/capacity/operations/{operationId}`

Polls the underlying ARM long-running operation. Response:

```json
{ "operationId": "...", "state": "Resuming", "armStatus": "InProgress", "startedAt": "...", "correlationId": "..." }
```

Terminal states are `Running`, `Paused`, or `Failed`. The client (and the internal readiness-check logic in `bff-api`) must not treat `202`/`InProgress` as success — only a terminal `Running` (after the readiness checklist in `deployment-topology.md` §5.4 step 5 passes) is reported as usable capacity.

### 8.5 Daily 01:00 lifecycle check (system-triggered, no public route)

The Logic App does not call the public BFF routes above; it calls a dedicated internal operations endpoint, not exposed through the public API surface or documented for external clients:

**`POST /internal/v1/platform/capacity/lifecycle-check`** (Logic-App-triggered, its own dedicated managed identity, network-restricted to the Logic App's outbound identity) — implements `deployment-topology.md` §5.3 steps 1–7 exactly: reads capacity state, verifies allow-list and time window, asks whether the simulator is stopped/Event Hubs drained/no protected rehearsal/no critical refresh, and either logs `SKIPPED_BUSY` (capacity left running) or submits the ARM suspend operation and polls to terminal state, persisting the full evidence record described there. This route is documented here only so implementers do not duplicate its logic inside the public `pause-requests` route — they are deliberately separate code paths with separate identities.

### 8.6 Capacity state values

`Paused | ResumeRequested | Resuming | ReadinessCheck | Running | DrainRequested | Draining | SuspendRequested | Failed` — exactly the state diagram in `deployment-topology.md` §5.1, no additional states invented at the API layer.

---

## 9. Audit and decision lineage contract

**`GET /v1/audit/decisions`** query parameters: `domain` (`energy|quality|furnace|knowledge|capacity`), `entityId`, `from`, `to`, plus the standard `TBL-STD` parameters (§5). Each row:

```json
{
  "auditId": "...",
  "domain": "furnace",
  "entityId": "LUX-BF-01",
  "correlationId": "...",
  "inputSnapshotRef": "silver:fact_telemetry@...",
  "modelVersion": "rul-model:2026.07.1",
  "output": { "value": 21.0, "unit": "d" },
  "humanAction": { "actor": "u-...", "decision": "ACKNOWLEDGED", "at": "..." },
  "outcome": null,
  "recordedAt": "..."
}
```

`outcome` is populated asynchronously once the real-world result is known (e.g., an actual reline date, a realized energy saving) and is itself an append (new row referencing the original `auditId`), never an in-place mutation of the original row — the audit table is append-only through the BFF end to end (`solution-architecture.md` §9.2).

---

## 10. Foundry Agent Service and Speech-to-Text contracts

### 10.1 Energy agent (Foundry) — tool contract

The energy agent's only callable tools are a restricted OpenAPI subset exposed by `bff-api`, matching `solution-architecture.md` §4.3 item 7:

| Tool name | Maps to route | Write capability |
|---|---|---|
| `read_energy_context` | `GET /v1/command-center/summary`, `GET /v1/energy/*` reads | Read-only |
| `forecast_demand` | Internal forecast function (not separately public) | Read-only |
| `simulate_schedule` | `POST /v1/energy/schedules:simulate` | Proposal only, no write |
| `propose_recommendation` | Creates a recommendation record for human review | Write to a **pending** recommendation only, never to an approved/committed state |

A separate, independently policy-gated **commit** capability exists only as `POST /v1/energy/recommendations/{id}:approve`, which is **not** in the agent's tool list at all — the agent cannot call it under any prompt, because approval requires the `EnergyPlanner.Approve` human role token, not the agent's own tool identity (`solution-architecture.md` ADR-006/ADR-007). The agent's tool-calling identity is a separate Foundry project/agent identity (`solution-architecture.md` §8.1), distinct from any user token, and every tool call is logged with full input/output for forensic replay (`security-governance-and-threat-model.md` §12.3).

### 10.2 Knowledge-capture agent — tool contract

| Tool name | Maps to route | Notes |
|---|---|---|
| `search_approved_procedures` | `GET /v1/knowledge/search` | Restricted to **approved** procedures only; never queries drafts |
| `write_draft_procedure` | Internal draft-write function, surfaced to the Knowledge Engineer via `GET /v1/knowledge/procedures?status=DRAFT` | Writes a `DRAFT` record only; cannot transition status |

Publishing (`POST /v1/knowledge/procedures/{id}:approve`) is exclusively a `Knowledge.Publisher`-role human action, never an agent tool call, matching `solution-architecture.md` §4.3 item 6 ("It cannot publish").

### 10.3 Speech Fast Transcription contract

**Internal flow** (not directly browser-callable; mediated by `knowledge-orchestrator` and exposed to the browser only through `/v1/knowledge/interviews`):

1. `POST /v1/knowledge/interviews` creates a consent-bound session (§4.7) and returns `sessionId`.
2. `knowledge-orchestrator` submits the recorded/streamed audio to Azure Speech **Fast Transcription** using the session's language/consent metadata, in Sweden Central.
3. Transcription result is stored classified `Highly Confidential` until de-identified/approved (`solution-architecture.md` §4.3 item 5), keyed to `sessionId`.
4. `GET /v1/knowledge/interviews/{sessionId}/transcript` — knowledge workflow role only — returns the transcript with `speakerLabels`, `confidence`, and segment timestamps once available; returns `202`-style `{"status": "PROCESSING"}` while transcription is in flight (polled, not SSE, since this is a bounded one-shot operation rather than a continuous stream).
5. The extraction step separates `observation`, `recommended_check`, `rationale`, and `safety_boundary` fields with source-segment citations, per `demo-runbook.md` §7, and is written as a `DRAFT` procedure via the knowledge agent's `write_draft_procedure` tool (§10.2) — never auto-published.

### 10.4 Foundry/Speech error handling

A `503 UPSTREAM_UNAVAILABLE` from either Foundry or Speech never blocks procedure approval or knowledge-capture entirely: the orchestrator queues the consented capture and offers a manual text-entry fallback path for the transcript, consistent with `solution-architecture.md` §9.1 ("do not block procedure approval; queue capture, use text/manual approved capture workflow").

---

## 11. Simulator contracts

The simulator is a first-class publisher against the same event contract real OT ingestion uses (`solution-architecture.md` §4.1.1), not a separate mocked shape. This section fixes the wire contract; `implementation-guide.md` §6.2 fixes the build tasks that implement it.

### 11.1 Event envelope (all simulator output, cloud or local)

```json
{
  "event_id": "018f2f6e-6b2a-7c31-9b1a-2f7e6a9c1d3e",
  "event_ts": "2026-07-25T08:00:00.125Z",
  "ingest_ts": "2026-07-25T08:00:00.410Z",
  "source_id": "LUX-BF-01-TC-H07-03",
  "asset_id": "LUX-BF-01",
  "plant_id": "NS-DEMO-LUX-01",
  "sequence": 48213,
  "correlation_id": "01J9Z8Q3K5F8E2X6R7T4V0M1N2",
  "schema_name": "novasteel.telemetry.v1",
  "schema_version": 1,
  "data_classification": "SYNTHETIC",
  "privacy_label": "DEMO-NONPERSONAL",
  "scenario_id": "demo-full",
  "seed": 240725,
  "generator_version": "novasteel-sim/1.0.0",
  "payload": { "type": "telemetry.furnace.thermal", "signal": "hearth_shell_temp_c", "value": 142.7 }
}
```

`event_id` is UUIDv7 (time-ordered, per `solution-architecture.md` §3.3). `payload.type` is a closed, versioned enum per dataset (`telemetry.furnace.thermal`, `telemetry.rolling.mill`, `energy.interval`, `quality.measurement`, `maintenance.event`, `alarm.event`, `model.inference`) — each with its own JSON Schema under `contracts/events`.

### 11.2 Manifest contract

A seeded JSON scenario manifest (`simulator/manifests/*.json`) carries
`scenario_id`, `root_seed`, `start_time`, plant/asset scope, anomaly
configuration, and expected assertions. Each generated run writes its own
`manifest.json`, truth ledger, and `checksums.json`; two runs of the same
scenario must produce byte-identical event sequences and truth-ledger checksum
(`implementation-guide.md` §6.2 `SIM-001` acceptance criterion). Checksum
validation rejects a tampered generated run—this is the deterministic-replay
guarantee the whole demo relies on.

### 11.3 Validation gate (contract + physics + scenario)

A run is not marked presentable unless all three validator classes pass:

1. **Contract validator** — every event conforms to its `contracts/events` schema; any failure is written to the quarantine dataset (`ingest_quarantine_hot` / `quarantine_event`), never silently dropped or repaired (`solution-architecture.md` §3.3).
2. **Physics validator** — documented signal relationships hold (e.g., mass conservation within 0.8% across rolling stands, cooling-water ΔT tracking heat flux) per `synthetic-data-and-simulators.md` §3.2/§3.3.
3. **Scenario validator** — the run's cue values match the manifest's expected values within documented tolerance (e.g., RUL P50 = 21.0 ± tolerance, risk ≥ 0.80) per `demo-runbook.md` §5.

### 11.4 Publish targets

- **Cloud**: the simulator (as an Azure Container Apps Job under `mi-ns-demo-simulator`) publishes directly to the isolated demo Eventstream Custom Endpoint using Entra managed identity — no SAS key, no direct database write.
- **Local**: the same generator writes NDJSON/Parquet files consumed by `bff-api` in `DEMO_MODE=local` (`implementation-guide.md` §5), with byte-identical event content to the cloud path — only the transport differs.

### 11.5 Quarantine contract

A quarantined record retains the original payload plus a `quarantine_reason` from a closed enum (`SCHEMA_INVALID | UNKNOWN_ASSET | LATE_BEYOND_POLICY | DUPLICATE_CONFLICT | INVALID_UNIT`) and is queryable (not deleted), matching `solution-architecture.md` §3.3's quarantine rule.

---

## 12. Cross-reference index

| Contract concern | Primary section here | Authoritative architecture source |
|---|---|---|
| Route catalog | §4 | `solution-architecture.md` §5.3 |
| Table/query semantics | §5 | `dashboard-specification.md` §13 |
| SSE events | §6 | `solution-architecture.md` §5.3 |
| Versioning/idempotency | §7 | `solution-architecture.md` §5.3 |
| Capacity lifecycle API | §8 | `deployment-topology.md` §5 |
| Audit lineage | §9 | `solution-architecture.md` §9.2 |
| Foundry/STT contracts | §10 | `solution-architecture.md` §4.2–4.3 |
| Simulator contracts | §11 | `solution-architecture.md` §4.1.1; `synthetic-data-and-simulators.md` |
