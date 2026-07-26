# NovaSteel — Monitoring & Observability Evaluation

**Rubric owned:** *"Logging and metrics — Implements structured logging and relevant metrics."*
**Also feeds:** *"Performance and reliability — Performance optimization and reliability clearly addressed."*
**Evaluator:** Observability / SRE
**Date:** 2026-07-25

---

## 1. Executive verdict

| | Project A (`20260507 - NovaSteel\NovaSteel`) | Project B (`20260724 - Novasteel 3`) |
|---|---|---|
| Structured application logging | ❌ Essentially absent in Python; `print()` everywhere. C# simulator uses default `ILogger<T>` but never ships anywhere. | ⚠️ Only the `bff-api` uses `logging.getLogger` + `logger.exception(..., extra={"correlation_id": ...})`. Every other service (workers, relay, Blazor shell) has **zero** logger. |
| Correlation / tracing | ❌ 0 hits for `correlation_id\|trace_id` in `workloads/`, `libs/`, `platform/`. | ✅ First-class: `X-Correlation-ID` middleware, propagation into all responses, threaded into audit + adapters + SSE headers. |
| Health / readiness endpoints | ❌ Simulator only exposes `/api/status`. No `/health/live`, `/health/ready`. | ✅ `/health/live` and `/health/ready` in `bff-api/main.py`. |
| Azure Monitor **provisioned** in IaC | ✅ Log Analytics + App Insights + **action group + 2 KQL scheduled-query alerts** (freshness, model drift) + wired to Functions. | ✅ Log Analytics (workspace capping, prod=365d retention) + App Insights + **Microsoft Sentinel onboarding** + diagnosticSettings on 7 modules. |
| Azure Monitor **consumed** by app code | ⚠️ Only Azure Functions receives `APPLICATIONINSIGHTS_CONNECTION_STRING`. C# simulator does not. No `azure-monitor-*` or `OpenTelemetry` in any manifest. | ❌ App Insights connection string is **never** wired into any Container App and **no** service depends on `azure-monitor-opentelemetry`, `applicationinsights`, `Serilog`, or `OpenTelemetry`. Pure "provisioned but unconsumed". |
| Alert rules in IaC | ✅ 2 `scheduledQueryRules` + `actionGroup` in `monitoring-alerts.bicep`. | ❌ **Zero** `actionGroups`, `scheduledQueryRules`, or `metricAlerts` — alerts exist only as prose in `docs/operations/operations-and-cost.md`. |
| Fabric / RTI monitoring | ✅ Eventhouse quarantine table + 3 KQL Activator functions (`DetectTelemetryDropout`, `DetectLateArrival`, `DetectQualityDegradation`). | ✅ 8 dashboard KQL queries, RTI Activator rules JSON template (3 rules), Data-Quality notebook writing to Delta reconciliation table. |
| AI observability | ⚠️ Content-safety boolean flag on prediction records; no token usage, groundedness, drift metric. | ✅ `evaluation.py` scorecard (grounding coverage, injection block rate, citation validity); no token/latency metrics. |
| Audit trail (EU AI Act) | ⚠️ Immutable append-only tuple with runtime immutability guards. No hash chain. | ✅ **SHA-256 hash-chained** append-only audit with `_redact()` of `{audio, transcript, secret, token, key, prompt}` and `verify()` walk. |
| Metrics (counters / histograms / KPIs emitted) | ❌ None (KPIs computed as batch dataclasses; never emitted). | ❌ None (KPIs surfaced in responses only). |

**Bottom line:** Neither project ships production-grade telemetry, but **Project B wins the logging-and-metrics criterion decisively** on the strengths of correlation-ID discipline, health probes, hash-chained audit, Sentinel onboarding, and much broader `diagnosticSettings` fan-out. Project B's weakness is the *unconsumed* App Insights and complete absence of Azure alert rules in IaC — which Project A actually did provision. Project A's fatal weakness is that its Python decision code has no application logging at all; workloads emit information via `print()`.

Proposed scores (see §10):
- **Project A: 2 / 5** (Needs Improvement)
- **Project B: 3 / 5** (Satisfactory)

---

## 2. Observability capability matrix

| Capability | Project A evidence | Project B evidence | Winner |
|---|---|---|---|
| Structured JSON logging | *None found.* Only C# simulator uses `ILogger<T>` structured templates (`IotHubTelemetrySink.cs:105`). | `logger = logging.getLogger(__name__)` + `logger.exception("Unhandled BFF error", extra={"correlation_id": ...})` at `services/bff-api/src/bff_api/main.py:28,141-144`. Only one service though. | **B** (thin but present) |
| `logging.getLogger` count (Python, excluding venv) | **0** files (verified via `Select-String` over all `*.py`) | **1** file (`services/bff-api/src/bff_api/main.py`, 2 hits) | B |
| `print()` count in first-party Python | 15 files, up to 12 hits each (`workloads/p1_predictive_maintenance/run_p1_live.py`, `platform/scripts/validate_pillars_live.py:10 hits`, `platform/medallion/*.py`) | 15 files, mostly demo drivers & simulator CLI; production `services/` mostly clean (only `knowledge-orchestrator/evaluation.py:1` and `demo_local.py:15`) | B |
| `ILogger` / `Serilog` (.NET) | 4 files, ~14 hits (`SteelFactorySimulator/Services/FabricCapacityService.cs:6`, `Transport/IotHubTelemetrySink.cs:4`, `SimulationController.cs:2`, `SimulationHostedService.cs:2`) | **0** C# logger usage in `apps/portal-shell/` (Blazor WASM, `Program.cs` never calls `AddLogging`/AI) | A |
| Correlation-ID propagation | 0 hits for `correlation_id\|correlationId\|trace_id` in `workloads/`, `libs/`, `platform/` | 60+ hits across `services/bff-api/src/bff_api/{main,routes,services,audit,contracts,knowledge_adapter,repository}.py`. Middleware at `main.py:82-92`; header `X-Correlation-ID` roundtripped. | **B (huge margin)** |
| Distributed tracing (OpenTelemetry / W3C traceparent) | Not present anywhere. `pyproject.toml` has no `opentelemetry-*` deps. | Not present anywhere. `requirements.txt` has no `opentelemetry-*` or `azure-monitor-opentelemetry`. | Tie (both fail) |
| Custom application metrics (counters/histograms) | None emitted; KPI values calculated only for report tables (`platform/kpi/kpi_baseline.py`). | None emitted; KPI values surfaced via response payloads only (`services/bff-api/src/bff_api/repository.py:88`). | Tie (both fail) |
| Application Insights **provisioned** | `infrastructure/modules/monitoring.bicep:36-48` (workspace-based). | `infra/bicep/modules/monitoring.bicep:41-52` (workspace-based) + Sentinel onboarding `:54-58`. | **B** (Sentinel + capping + env-tiered retention) |
| App Insights connection string **consumed** by code | `functions.bicep:120-121` sets `APPLICATIONINSIGHTS_CONNECTION_STRING` on Function App env → auto-instrumented. No .NET/Python service pip/nuget uses it. | Provisioned in `monitoring.bicep`, exposed in `main.bicep:501`, but **never referenced in `containerapps.bicep` env** (see excerpt below) — App Insights is orphaned. | **A** (at least Functions ships) |
| Health / readiness endpoints | .NET simulator only has business `/api/status`; no `/health/live` or `/health/ready`. | `bff-api/main.py:154-168` exposes both `/health/live` and `/health/ready` returning `HealthStatus` with correlation ID. | **B** |
| Container App liveness/readiness probes | Not set in `container-apps.bicep`. | Not set in `containerapps.bicep`. | Tie (both fail) |
| Diagnostic Settings fan-out (LA workspace) | Only implicit via `logAnalyticsConfiguration` on Container Apps env (`container-apps.bicep:36-38`). No `diagnosticSettings` resource anywhere. | Explicit `diagnosticSettings` on **7 resources**: Container Apps env (`:60`), Event Hubs (`:141`, both `allLogs` + `AllMetrics`), Foundry+Speech (`:188,208`), Key Vault (`:103`), Logic App (`:166`), NSG (`:262`), Storage (`:146`). | **B (large margin)** |
| Log retention policy | Single `retentionInDays` (default 90). | Environment-tiered: `prod=365`, `dev/test/demo=30` (`parameters/prod.bicepparam:33`) with `logAnalyticsDailyQuotaGb` cost cap. | **B** |
| Alert rules in IaC | 2 KQL `scheduledQueryRules` (freshness, drift) + `actionGroup` with email receiver (`monitoring-alerts.bicep:39-126`). | **None**. `docs/operations/operations-and-cost.md §4` lists 10 alerts as *documentation*; no `Microsoft.Insights/*Alerts*` or `actionGroups` in any `.bicep`. | **A** |
| Microsoft Sentinel / SIEM onboarding | Not provisioned. | `Microsoft.SecurityInsights/onboardingStates@2024-03-01` in `monitoring.bicep:54-58` (togglable). | **B** |
| Fabric RTI / KQL monitoring | `platform/rti/eventhouse.kql` (bronze table + retention/caching + quarantine table); `activator-freshness.kql` (3 KQL functions: dropout, late arrival, quality burst). | `fabric/kql/dashboard-queries.kql` (8 named queries Q01–Q08 including freshness, alarms, gateway state, quarantine); `fabric/rti/activator-rules.template.json` (3 rules with recovery/suppression/forbiddenActions), `dashboard-spec.json` (multi-page RTI dashboard). | **B (broader + explicit forbiddenActions)** |
| Semantic-model / pipeline data-quality checks | `platform/medallion/data_quality.py` — inline assertions, raises `DataQualityError`. | `fabric/notebooks/ns-validate-data-quality.Notebook` writes `PASS/FAIL` rows to a Delta `pipeline_run_reconciliation` table with per-rule metric + threshold. | **B (persisted results)** |
| AI observability (prompt / groundedness / drift) | `workloads/content_safety.py` + `content_safety_passed` boolean in prediction audit record; model drift alert defined in Bicep KQL query. | `services/knowledge-orchestrator/src/knowledge_orchestrator/evaluation.py` runs a scorecard: prompt-injection block rate, extraction grounding, citation validity, safe-prompt success. | **B (broader scorecard) + A wins on drift alerting** |
| Token usage / cost tracking | Not implemented. | Not implemented. | Tie (both fail) |
| Audit log (EU AI Act §12 traceability) | `libs/novasteel_core/novasteel_core/audit.py` — `AuditLog(Sequence)` with `ImmutableAuditError` on any mutation. No hash chain. | `services/bff-api/src/bff_api/audit.py` — SHA-256 hash-chained (`previous_hash → record_hash`), `_redact()` of secret-like keys, `verify()` walks the chain. Duplicated in `services/knowledge-orchestrator/.../audit.py`. | **B** |

---

## 3. Logging quality — deep dive

### 3.1 Project A

**Python side (workloads, libs, platform).** A repository-wide `Select-String -Pattern "logging\.getLogger|structlog|import logging"` returns **zero matches** across every first-party Python file. The decision services never instantiate a logger. Operational visibility comes exclusively from `print(...)` scattered in "live" scripts, e.g.:

- `workloads/p1_predictive_maintenance/run_p1_live.py` — 12 `print()` calls (line-level narrative of an ML run).
- `platform/scripts/validate_pillars_live.py` — 10 `print()` calls.
- `platform/medallion/{bronze,silver,gold}_*.py` — 1–5 `print()` calls each.

There is no logger name, no severity, no correlation ID, no structured extras. This defeats any downstream KQL parsing in Log Analytics — every line becomes an unstructured `ContainerAppConsoleLogs_CL.Log_s` blob. Notably, the freshness alert in `monitoring-alerts.bicep:73` matches on `Log_s has "telemetry" or Log_s has "readings"` — a substring scan of unstructured console output. That works because the app produces no structured signals.

**.NET side (`apps/steel_factory_simulator`).** The simulator does the opposite: it uses the default `Microsoft.Extensions.Logging` `ILogger<T>` API properly, e.g.:

```csharp
// apps/.../Transport/IotHubTelemetrySink.cs:105
_logger.LogInformation(
    "Published {Count} synthetic simulator readings to IoT Hub as {MessageId}",
    _buffer.Count, payload.MessageId);
```

with 14 similar structured-template calls across `FabricCapacityService.cs`, `SimulationController.cs`, `SimulationHostedService.cs`. This is **good structured logging in isolation**, but:

- `Program.cs` never calls `builder.Logging.AddApplicationInsights(...)`, never adds OpenTelemetry, never adds Serilog.
- `SteelFactorySimulator.csproj` references only `Azure.Identity`, `Azure.Security.KeyVault.Secrets`, `Microsoft.Azure.Devices.Client` — no `Microsoft.ApplicationInsights.AspNetCore`, no `OpenTelemetry.*`, no `Serilog.*`.

Net effect: the structured template lives its whole life inside the process's stdout. Log Analytics receives only line-string ingest via Container Apps' native console log stream — parameters are baked into the message string, losing the `{Count}`/`{MessageId}` dimensions that would make them queryable.

**Correlation IDs & tracing.** Zero. `Select-String -Pattern "correlation_id|correlationId|trace_id|traceId"` returns zero hits under `workloads/`, `libs/`, and `platform/`. The simulator does propagate a `messageId` and `injectedScenario` into IoT Hub message properties (good for lineage), but nothing carries a W3C `traceparent` end-to-end.

**Health endpoints.** The simulator exposes `/api/status`, `/api/readings`, `/api/simulation/start|stop`. No `/health/live`, `/health/ready`, and no `WithStartupTimeout`/`AddHealthChecks()` — probes cannot distinguish "process alive" from "downstream IoT Hub reachable".

### 3.2 Project B

**Python side (`services/bff-api`).** Only `bff-api` uses the standard library logger, and it does so correctly:

```python
# services/bff-api/src/bff_api/main.py:28
logger = logging.getLogger(__name__)
CORRELATION_ID_HEADER = "X-Correlation-ID"
...
# :82-92 — middleware that generates/propagates the correlation id
@app.middleware("http")
async def add_correlation_id(request, call_next):
    candidate = request.headers.get(CORRELATION_ID_HEADER, "").strip()
    request.state.correlation_id = candidate if candidate else str(uuid.uuid4())
    response = await call_next(request)
    if CORRELATION_ID_HEADER not in response.headers:
        response.headers[CORRELATION_ID_HEADER] = request.state.correlation_id
    return response
...
# :141-145 — global exception handler carries correlation id in extras
logger.exception(
    "Unhandled BFF error",
    extra={"correlation_id": _correlation_id(request)},
    exc_info=exc,
)
```

`X-Correlation-ID` is also emitted in `expose_headers` (CORS), on every response, and on outbound SSE headers in `routes.py:91`. The `AppendOnlyAudit.append(...)` stores it as a top-level field. That's exemplary discipline for one service.

**Everywhere else the discipline evaporates.** `optimizer-worker`, `scoring-worker`, `ingest-relay` are single-line `requirements.txt` ("uses the Python standard library only") with **no logging framework and no `import logging` in any source file**. `knowledge-orchestrator/src/knowledge_orchestrator/*.py` uses one `print()` in `evaluation.py` for scorecard output. `apps/portal-shell/Program.cs` (Blazor WASM) makes no `builder.Logging` calls and has no `Microsoft.ApplicationInsights.AspNetCore` reference; the client has no telemetry at all.

**Log-configuration format.** `bff-api` does not install a JSON formatter (e.g., `python-json-logger`) — the `extra={"correlation_id": ...}` is written by whatever handler `logging.basicConfig()` defaults to at import time, which by default drops `extra` fields. Without a configured `JsonFormatter` or `structlog`, the `correlation_id` in `extra` is lost from stdout unless a caller sets up an explicit handler. **This is a real bug**: the design intent is good, but the runtime output does not actually persist the correlation ID unless the operator supplies a custom `logging.config.dictConfig`.

**Health endpoints.** `bff-api/main.py:154-168` defines `/health/live` and `/health/ready` returning a `HealthStatus` model with `service`, `status`, `correlation_id`. Both return the same payload — no downstream dependency check is performed for readiness, so this is really two liveness probes labelled differently. Nonetheless, they exist and are addressable by a Container App `probes` block — which is *not* configured (see gaps §8).

**Correlation ID.** Threaded through 8 modules; propagated into audit records (`audit.py:23,80,96`), replay routes (`routes.py:933`), knowledge adapter (`knowledge_adapter.py:46,54,98,107`). This is the strongest observability primitive in either codebase.

---

## 4. Metrics and KPI instrumentation

Both projects fail to emit **any** first-party application metrics (counters, histograms, gauges). No `azure.monitor.opentelemetry.exporter.metrics`, no `prometheus_client`, no `applicationinsights.TelemetryClient.track_metric`, no `Meter.CreateCounter`.

### Project A

- `platform/kpi/kpi_baseline.py:81-120` implements `compute_baseline(records, site, as_of, months)` returning a `BaselineKpis(energy_mwh_per_ton, co2_kg_per_ton, cost_eur_per_ton, high_grade_yield)` dataclass. The value is **calculated for reporting**, not emitted as an OTel/AI metric. `improvement_vs_baseline(...)` at `:123-127` is a helper for the Power BI mart, not a metric hook.
- `workloads/p1_predictive_maintenance/decision_service.py` records `confidence`, `remaining_useful_life_days_p10/p50/p90` **inside** an `AuditRecord`, but the confidence value that the model-drift alert (`monitoring-alerts.bicep:109`) queries (`P1Predictions_CL | summarize AvgConfidence = avg(...)`) never ships as a metric — it depends on the confidence appearing in a console line the LA agent later parses. Nothing writes to `P1Predictions_CL` explicitly.

### Project B

- `services/bff-api/src/bff_api/repository.py:88-330` exposes `summary_metrics` (energyTonnage, quality yield, lining_rul_p50_days) via HTTP responses only. No metric emission.
- Fabric-side: `fabric/notebooks/ns-validate-data-quality.Notebook/notebook-content.py:40-172` writes a metric row `(RUN_ID, date, table_name, rule_id, status, evaluated_rows, failed_rows, metric, threshold, ts)` per DQ rule to Delta — this **is** persisted metric telemetry but lives in OneLake, not Log Analytics.
- KQL `dashboard-queries.kql` computes `fn_data_freshness`, `fn_active_alarms`, `fn_gateway_status`, `fn_latest_model_scores`, `fn_quarantine_rate(15m)` — these are query-time metrics against a Fabric Eventhouse (RTI), not App Insights `customMetrics`.

**Neither project instruments business KPIs as first-class metrics that would light up an Application Insights dashboard or trigger a metric alert.** Both rely on downstream KQL scanning of console logs (Project A) or ad-hoc semantic-model refresh (Project B). That is a shared weakness the grader must acknowledge.

---

## 5. Azure Monitor / App Insights — provisioned vs consumed

### Provisioned (IaC)

| | Project A | Project B |
|---|---|---|
| Log Analytics workspace | `monitoring.bicep:21-34` | `monitoring.bicep:24-39` with workspace capping + env retention (`parameters/prod.bicepparam:33 = 365d`) |
| App Insights (workspace-based) | `monitoring.bicep:36-48` | `monitoring.bicep:41-52` |
| Sentinel onboarding | ❌ | `monitoring.bicep:54-58` (`Microsoft.SecurityInsights/onboardingStates`) |
| Action group | ✅ `monitoring-alerts.bicep:39-54` (email receiver) | ❌ |
| Scheduled-query alerts | ✅ `monitoring-alerts.bicep:58-90` (telemetry freshness), `:94-126` (P1 model drift) | ❌ |
| Metric alerts | ❌ | ❌ |
| `diagnosticSettings` resources | 0 (Container Apps env consumes LA via native `logAnalyticsConfiguration`, not through a `diagnosticSettings` resource) | 7 explicit resources: Container Apps env, Event Hubs (allLogs + AllMetrics), Foundry, Speech, Key Vault, Logic App, NSG, Storage |
| Daily ingestion cap | ❌ | ✅ `dailyQuotaGb` param, `dev/test/demo=5`, `prod=-1` |

### Consumed (application code)

| | Project A | Project B |
|---|---|---|
| App Insights connection string wired to Container Apps | ❌ (`container-apps.bicep` sends console logs to LA workspace, no AI connection string env var) | ❌ `containerapps.bicep:122-135` sets only `NOVASTEEL_ENVIRONMENT`, `NOVASTEEL_KEY_VAULT_URI`, `NOVASTEEL_PLACEHOLDER` — no AI conn string on any of the 5 services |
| App Insights connection string wired to Functions | ✅ `functions.bicep:120-121` `APPLICATIONINSIGHTS_CONNECTION_STRING` | N/A (no Functions) |
| Python `azure-monitor-opentelemetry` / `applicationinsights` package | ❌ (not in `pyproject.toml`) | ❌ (not in any of 5 `pyproject.toml` / `requirements.txt`) |
| .NET `Microsoft.ApplicationInsights.AspNetCore` package | ❌ (not in `SteelFactorySimulator.csproj`) | ❌ (not in `PortalShell.csproj`) |
| OpenTelemetry SDK / exporter | ❌ | ❌ |
| Serilog | ❌ | ❌ |

**Consequence:** In Project B, App Insights receives nothing except whatever the Container Apps runtime auto-forwards (which is not APM data). Custom traces, dependencies, exceptions, and custom metrics are not surfaced. Project A gets some auto-instrumentation on its Functions plane, but nothing on its .NET simulator or Python workloads.

---

## 6. AI observability & audit trail

### AI observability

- **Project A.** `workloads/content_safety.py` calls the Azure Content Safety REST API and returns a pass/fail flag that is written into `PredictionAudit.content_safety_passed` (see `workloads/p4_knowledge_capture/assistant.py:105`). The KQL model-drift alert (`monitoring-alerts.bicep:109`) is defined on `P1Predictions_CL`. No token counts, no latency histograms, no groundedness scorer.
- **Project B.** `services/knowledge-orchestrator/src/knowledge_orchestrator/evaluation.py:80-90` runs an offline evaluation report producing a `pass_rate` scorecard over four kinds: injection detection, extraction grounding, citation validity, and safe-prompt behaviour. `prompt_defense.py` scans for jailbreak/exfiltration patterns (`:70`). Consent state machine + `withdraw_consent` handler (`orchestrator.py:326-346`) is a GDPR-Art-17 primitive. No token/latency/cost telemetry.

Winner: **B** for the scorecard; **A** for actually alerting on model drift.

### Audit trail (EU AI Act traceability)

- **Project A** — `libs/novasteel_core/novasteel_core/audit.py`:
  - `AuditLog(Sequence[AuditRecord])` with `ImmutableAuditError` on `__setitem__`, `__delitem__`, `clear`, `pop`, `remove`, `replace`.
  - Deep-copies on append.
  - **No hash chain, no per-record signature, no redaction of sensitive fields, no `verify()` method.**
- **Project B** — `services/bff-api/src/bff_api/audit.py`:
  - `AppendOnlyAudit.append(...)` computes `record_hash = sha256(json.dumps(payload, sort_keys=True))` chained through `previous_hash` starting at genesis hash `"0"*64`.
  - `_redact(...)` blanks values for keys in `{"audio", "transcript", "token", "secret", "key", "prompt"}` — matches EU AI Act §12 & GDPR non-persistence expectations.
  - `verify()` re-walks the chain and returns `False` on tamper.
  - `correlation_id` is a first-class field.
  - Duplicated in `services/knowledge-orchestrator/src/knowledge_orchestrator/audit.py` (also hash-chained + redacted).

Winner: **B (unambiguous).**

---

## 7. Fabric / data-platform observability

| | Project A | Project B |
|---|---|---|
| Eventhouse / KQL schema | `platform/rti/eventhouse.kql` — `TelemetryRaw` (with `Origin`, `SourceId`), `TelemetryQuarantine` with retention/caching policies | Referenced via `fabric/kql/dashboard-queries.kql` (Q01–Q08) — assumes `mv_telemetry_1m`, `ingest_quarantine_hot`, and functions `fn_data_freshness`, `fn_active_alarms`, `fn_gateway_status`, `fn_latest_model_scores`, `fn_quarantine_rate`. The KQL definition of those functions is not co-located; the dashboard depends on them being deployed. |
| Activator / real-time rules | `platform/rti/activator-freshness.kql` — 3 KQL functions | `fabric/rti/activator-rules.template.json` — 3 rules with `recovery`, `suppressionMinutes`, and an explicit `forbiddenActions` block (PLC write, setpoint change, capacity pause/resume) — good defense in depth |
| Dashboard spec | Not present as machine-readable spec | `fabric/rti/dashboard-spec.json` — visuals, thresholds (green ≤5s, red >60s) |
| Data-quality checks | `platform/medallion/data_quality.py` — inline `raise DataQualityError` | `fabric/notebooks/ns-validate-data-quality.Notebook` — writes `PASS/FAIL/evaluated_rows/failed_rows/metric/threshold` to a Delta `pipeline_run_reconciliation` table, queryable over time |
| Capacity monitoring | Not exposed | Documented dashboards required at go-live (§2.2 of `operations-and-cost.md`), lifecycle Logic App audits its own runs; capacity metrics documented but not provisioned in Bicep beyond `budget.bicep` |
| Semantic model refresh monitoring | Not implemented | Not explicit in code |

Winner: **B slightly**, mainly for persisted DQ results + `forbiddenActions` list + dashboard spec. **A slightly** for actually co-locating the KQL function definitions rather than referring to them.

---

## 8. Gaps per project

### Project A — gaps
1. **Python codebase has no logger.** Zero `logging.getLogger` in `workloads/`, `libs/`, `platform/`. Everything is `print()` — unstructured, unfilterable, unlevelled. No level, no timestamp, no correlation.
2. **No correlation IDs anywhere in the Python codebase.** No end-to-end traceability from simulator → Fabric → workload — the audit `AuditRecord.audit_id` is per-decision, not per-request.
3. **No health / readiness endpoints.** The .NET simulator only exposes `/api/status`; Container App probes cannot distinguish liveness from readiness. Not defined in `container-apps.bicep` either.
4. **App Insights unused by the .NET simulator.** Structured `ILogger` templates lose their parameters at the stdout boundary. No `AddApplicationInsightsTelemetry()`, no OpenTelemetry, no Serilog sink.
5. **Audit log lacks a hash chain and redaction.** Immutable-in-memory is not tamper-evident.
6. **No `diagnosticSettings` resources on Key Vault, Storage, Event Hubs, IoT Hub.** Diagnostic logs from Azure control-plane are not shipped to LA (they'd default to disabled).
7. **No environment-tiered retention** (single `retentionInDays=90` for all envs — exceeds spec for dev/test cost and undershoots prod compliance if any real data lands).
8. **Freshness alert queries `ContainerAppConsoleLogs_CL.Log_s has "telemetry"`** — a substring scan that will fire (or miss) based on unstructured print output. Brittle.
9. **No Sentinel onboarding.** The freshness/drift alerts fire an email but there is no SIEM correlation, no incident, no analytics rule.
10. **No token/latency/cost metrics** for the P4 GenAI knowledge workload.

### Project B — gaps
1. **App Insights is provisioned but consumed by nothing.** `containerapps.bicep:122-135` does not set `APPLICATIONINSIGHTS_CONNECTION_STRING`. No service has `azure-monitor-opentelemetry`, `applicationinsights`, `Serilog`, or `Microsoft.ApplicationInsights.*`. This is the single biggest gap: the AI resource cost is paid but yields no telemetry.
2. **No alert rules in IaC.** The comprehensive `docs/operations/operations-and-cost.md §4` table lists 10 alerts (BFF error-rate, freshness, quarantine, capacity failure, budget, agent-without-approval, Key Vault anomaly, OneLake export, drift, lifecycle skip) but **none** exist as `Microsoft.Insights/scheduledQueryRules` or `metricAlerts` in the Bicep. Documentation-as-alert-rule is not alerting.
3. **Only `bff-api` uses `logging.getLogger`.** `optimizer-worker`, `scoring-worker`, `ingest-relay`, `knowledge-orchestrator` all lack a logger instance. Blazor `portal-shell` has no `AddApplicationInsights` and no `Serilog`.
4. **`bff-api` uses stdlib `logging` without a JSON formatter** — the `extra={"correlation_id": ...}` payload is silently dropped by the default handler. Design correct, runtime wrong.
5. **Container App probes not configured.** `/health/live` and `/health/ready` exist in code but `containerapps.bicep` template `probes` block is missing.
6. **No token/latency/cost metrics** on the Foundry/Speech knowledge orchestrator; the evaluation scorecard runs offline over fixtures, not against live prompts.
7. **KQL dashboard depends on `fn_data_freshness`, `fn_active_alarms`, ...** functions that are not defined in `fabric/kql/`. Deployment risk.
8. **No custom application metrics** anywhere (counters/histograms/summaries).
9. **No OpenTelemetry** — the whole "Application: OpenTelemetry traces" row in `operations-and-cost.md §2.1` is aspirational.

---

## 9. Score justification — "Logging and metrics"

| Score | Meaning | Project A | Project B |
|---|---|---|---|
| 5 | Excellent — structured JSON logs, correlation propagated, custom metrics, dashboards, alerts, drift | | |
| 4 | Good — structured logs + correlation + some custom metrics + alerts | | |
| 3 | Satisfactory — structured logging in main service, correlation, health, alerting in IaC or documented | | ✅ |
| 2 | Needs improvement — sparse or unstructured logging, no correlation, provisioned but unconsumed | ✅ | |
| 1 | Poor — none of the above | | |

### Project A — proposed **2 / 5**
- (+) Actual alert rules & action group in IaC (freshness + drift) — the only project doing this.
- (+) C# simulator uses `ILogger<T>` with structured templates.
- (+) Immutable audit log with runtime guards.
- (+) Fabric RTI KQL for staleness/lateness/quality burst.
- (–) Zero application logger in Python — `print()` only.
- (–) Zero correlation IDs anywhere in the Python codebase.
- (–) No health/readiness endpoints.
- (–) App Insights consumed only on Functions; simulator and workloads emit nothing to AI.
- (–) Audit not hash-chained; no redaction of secrets from records.

The alerting/IaC strength is real but does not offset the absence of application-level structured logging and correlation. A jury that "greps the code" will see zero logger usage and downgrade.

### Project B — proposed **3 / 5**
- (+) Exemplary correlation-ID propagation across BFF, adapters, audit, SSE responses.
- (+) Health-live / health-ready endpoints.
- (+) SHA-256 hash-chained, redacting, verifiable audit log — best-in-class in either repo.
- (+) Sentinel onboarding, tenant-aware retention, ingestion cap, diagnostic settings fan-out to 7 resources.
- (+) AI evaluation scorecard (injection, grounding, citation, safe prompt).
- (+) Fabric DQ notebook persists per-rule PASS/FAIL to Delta.
- (–) App Insights is provisioned but not wired to any Container App and no service has an AI/OTel SDK dependency.
- (–) Only 1 of 5 services actually uses `logging.getLogger`.
- (–) Zero alert rules in IaC (10 alerts documented, 0 provisioned).
- (–) `bff-api` uses default `logging.basicConfig` — `extra={"correlation_id"}` is not persisted by default handlers, negating the correlation propagation for stdout consumers.
- (–) No custom metrics emitted (counters/histograms).

The BFF-quality signal + Sentinel + retention tiering + hash-chained audit put B firmly ahead of A. But the failure to consume App Insights and to provision alerts prevents a "Good (4)". A generous jury might award 3.5.

**Recommended jury scores: A = 2, B = 3.** If the jury weights *provisioned alerts* very heavily, B and A both slide by 1 into (1, 2). If the jury weights *correlation & audit* heavily, B could reach 4 and A stays at 2.

---

## 10. Top 5 observability fixes

### Project A — top 5
1. **Add a Python logger to every workload and script.** Replace `print()` with `logging.getLogger(__name__)` and configure `logging.config.dictConfig` with a JSON formatter that emits `timestamp`, `severity`, `logger`, `correlation_id`, `run_id`, `pillar` fields. This alone converts every existing string into a queryable Log Analytics row.
2. **Introduce a `correlation_id` context (contextvars) that threads through `medallion → workloads → audit`** and is picked up by the JSON formatter. Also propagate `X-Correlation-ID` on the .NET simulator's outbound IoT Hub messages via a message property so bronze rows carry the ID.
3. **Wire `APPLICATIONINSIGHTS_CONNECTION_STRING` into the .NET simulator** (`SteelFactorySimulator.csproj` add `Microsoft.ApplicationInsights.AspNetCore`, `Program.cs` `builder.Services.AddApplicationInsightsTelemetry()`) so structured `ILogger` templates ship as `traces` with typed dimensions, and add `builder.Logging.AddOpenTelemetry()` for cross-service traces.
4. **Add `/health/live` and `/health/ready` endpoints** to the simulator + a `probes` block on `container-apps-simulator.bicep`; readiness should verify IoT Hub connection string acquisition (`FabricCapacityService` succeed once).
5. **Hash-chain the audit log** (`libs/novasteel_core/novasteel_core/audit.py`) — add `previous_hash`, `record_hash = sha256(...)`, `verify()`, and a `_redact()` step for GDPR/AI-Act §12 evidence.

### Project B — top 5
1. **Wire `APPLICATIONINSIGHTS_CONNECTION_STRING` into every Container App** in `containerapps.bicep` env, add `azure-monitor-opentelemetry==1.6.*` to each service's `requirements.txt`, and initialize it once (`azure.monitor.opentelemetry.configure_azure_monitor()`) at each service's `main.py`. This turns the currently-orphaned App Insights into an actual APM.
2. **Convert `docs/operations/operations-and-cost.md §4` into `Microsoft.Insights/scheduledQueryRules` + `actionGroups` in `infra/bicep/modules/alerts.bicep`.** At minimum: BFF error-rate, telemetry freshness, quarantine rate, capacity ARM failure, budget, KV anomaly, model drift, agent-without-approval. Currently zero alerts are provisioned.
3. **Configure a JSON logging formatter** for `bff-api` (`python-json-logger` or `structlog`) so `extra={"correlation_id": ...}` actually reaches stdout and Log Analytics — right now the intent is destroyed by the default handler. Also add the same logger + middleware pattern to `optimizer-worker`, `scoring-worker`, `ingest-relay`, `knowledge-orchestrator`.
4. **Configure Container App `probes`** in `containerapps.bicep` to actually call `/health/live` (liveness) and `/health/ready` (readiness) — and make `/health/ready` verify at least one downstream dependency (e.g., KV secret fetch), otherwise it is a second liveness probe.
5. **Emit business KPIs as OTel metrics** — `energy_mwh_per_ton` (gauge), `co2_kg_per_ton` (gauge), `lining_rul_p50_days` (histogram), `foundry_prompt_tokens` (counter), `injection_scanner_flagged_total` (counter), `audit_chain_verified` (gauge). Once the App Insights connection is live (fix #1), these will populate Metrics Explorer and enable metric-based alerts far cheaper than KQL scheduled queries.
