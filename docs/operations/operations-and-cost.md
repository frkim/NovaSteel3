# NovaSteel — Operations and Cost

> **Status:** Implementation-ready v1.0
> **Date:** 2026-07-25
> **Authoritative source:** [`deployment-topology.md`](../architecture/deployment-topology.md) §5–§7 (capacity lifecycle, cost model, resilience) and [`solution-architecture.md`](../architecture/solution-architecture.md) §9 (resilience/observability) govern this document. [`demo-runbook.md`](../demo/demo-runbook.md) governs the presentation-day procedure; this document operationalizes its reset/recovery steps as engineering runbooks and adds the ongoing (non-demo-day) operational posture.
> **Owning todo:** `implementation-pack`
> **Companions:** [`implementation-guide.md`](../implementation/implementation-guide.md), [`api-contracts.md`](../implementation/api-contracts.md)

## 0. Scope

This document governs cloud and non-production operations **after** tenant
deployment; it does not claim that those cloud resources already exist. The
local deterministic demo, reset, and fallback posture are implemented and
validated now; Fabric/Azure operational SLOs, the 01:00 capacity lifecycle, and
incident procedures apply after their tenant-specific gates are cleared. It does
not restate architecture decisions; it operationalizes them.

---

## 1. Environments and operational ownership

| Environment | Purpose | Operational owner | Capacity lifecycle policy |
|---|---|---|---|
| `dev` | Developer integration, contract tests | Engineering leads | Pause when unused; no business dependency |
| `test` | Security/integration/performance/release validation | Platform Admin + QA | Scheduled pause permitted after test drain |
| `demo` | Repeatable 15-minute defense and rehearsal | Platform Ops (presenter's supporting engineer) | F2 initial/F4 measurement fallback; 01:00 daily lifecycle check (§5) |
| `prod` | Pilot and production operations (post-gate) | Platform SRE | No automated pause; capacity/SLO decisions made after pilot measurement (§9) |

No environment's on-call rotation, runbook, or automation may reach across the `demo`/`prod` boundary — this mirrors the hard isolation rule in `deployment-topology.md` §2.1.

---

## 2. Observability architecture

### 2.1 Signal-to-store mapping

| Layer | Signals (see `implementation-guide.md` §13 for the emission contract) | Store | Primary consumer |
|---|---|---|---|
| Gateway/relay | `source_id`, sequence, queue depth, oldest buffered event, connection state, event-time lag, duplicate count, publish retry count | Log Analytics (custom logs) + Application Insights metrics | Platform SRE, on-call |
| Eventstream/KQL | input/output rate, failures, ingestion/query latency, materialized-view health, quarantine rate, freshness | Fabric RTI dashboard + Log Analytics export | Data platform team, demo presenter (readiness check) |
| Lakehouse/pipeline | bronze→silver→gold reconciliation, contract pass rate, late/invalid record count, pipeline duration, freshness | Fabric monitoring + Purview lineage | Data platform team |
| Capacity | CU/utilization/throttling/cost, pause/resume transitions, active jobs, F SKU, budget alerts | Fabric Capacity Metrics app + Azure Cost Management | Platform Ops, FinOps |
| Models | input/model version, latency, confidence distribution, drift, prediction-vs-outcome, evaluation result | MLflow (Fabric Data Science) + Application Insights | Data Scientist / RAI board |
| Foundry/STT | model deployment, tool-call outcome, safety-filter result, quota/429 retry, evaluation, transcript status (redacted) | Application Insights + Foundry evaluation logs | AI/agent workstream owner |
| Application | OpenTelemetry traces, request/error/latency, SSE reconnects, authorization denials, correlation ID | Application Insights (APM) | On-call engineer |
| Security | Entra sign-in/audit, Key Vault access, Fabric/Power BI activity, Purview, Sentinel detections, capacity ARM activity | Microsoft Sentinel (central Log Analytics workspace) | Security engineer, IR commander |

Every signal carries `correlation_id`; the append-only audit table (`api-contracts.md` §9) is the cross-domain join point for a specific decision's full lineage.

### 2.2 Dashboards required at go-live

1. **Platform Ops health board** — capacity state/CU, ingestion freshness/lag, quarantine rate, SSE reconnect rate, error-budget burn (per §3).
2. **RTI operational dashboard** (Fabric-native) — current signal, alert, gateway health, data freshness — this is the operational awareness surface, never a substitute for the semantic/KPI reporting layer (`solution-architecture.md` §3.1 row "RTI visual").
3. **Model quality dashboard** — drift, confidence distribution, prediction-vs-outcome reconciliation per model.
4. **Security/audit dashboard** (Sentinel) — the six minimum analytics rules from `security-governance-and-threat-model.md` §9, reviewed weekly.
5. **Cost dashboard** — Capacity Metrics + Azure Cost Management budget burn-down, reviewed against §8's cost model.

---

## 3. Service Level Objectives (SLOs)

The platform is monitoring and decision support, **not** hard real-time control (`solution-architecture.md` §9.1). SLOs below define operational awareness targets, not safety-critical guarantees, and are explicitly measured rather than assumed.

| SLO | Target | Measurement window | Notes |
|---|---|---|---|
| `bff-api` availability | 99.5% (non-prod pilot target; re-baseline after pilot load test) | 30-day rolling | Excludes planned capacity-pause windows in `dev`/`test`/`demo` |
| `bff-api` p95 latency (read routes) | < 800 ms | 7-day rolling | Measured server-side, excludes client network |
| SSE alert delivery latency | < 5 s from KQL event to client-visible alert | Per-incident | Matches `dashboard-specification.md` AC-P1-3 |
| Data freshness (KQL hot path) | < 5 s during active ingestion | Continuous | Matches `demo-runbook.md` cue sheet expectation |
| Bronze→silver→gold reconciliation | 100% row-count reconciliation or explicit quarantine reason for every discrepancy | Per pipeline run | No silent data loss tolerated — a reconciliation gap with no quarantine record is a Sev-2 incident (§7) |
| RUL model scoring cadence (pilot) | Daily | Per plant/asset | Near-real-time scoring is a measured future enhancement, not an MVP SLO (`solution-architecture.md` §4.2) |
| Energy optimizer response | Cached/signed fallback within 5 s if solver has not returned | Per request | Matches `demo-runbook.md` "never leave a solver spinner visible for more than 5 seconds" |
| Foundry/Speech availability | Best-effort; failure never blocks knowledge-capture workflow | Continuous | Queue-and-retry per `solution-architecture.md` §9.1 |
| Capacity resume readiness | < 10 minutes from GUI request to `Running` (demo F2/F4) | Per request | Includes ARM LRO + readiness checklist (§5.4); re-measure per SKU |
| Demo reset (soft) | < 5 minutes | Per rehearsal | Matches `demo-runbook.md` go/no-go checklist |
| Demo hard recovery | < 20 minutes | Per incident | Includes new `run_id`, reload, replay, re-verify |

**Error budgets** are tracked per SLO on a rolling window; a burned error budget triggers a change-freeze on the affected component until root cause is addressed (standard SRE practice), reviewed at the weekly platform sync.

### 3.1 What is explicitly not an SLO

- No sub-second control-loop latency guarantee exists anywhere in this platform; "real-time" means promptly visible for operational awareness (`solution-architecture.md` §9.1).
- No automatic cross-region failover RTO/RPO is promised until a specific recovery design is tested (§9 of this document).
- No Fabric capacity performance number (query latency at a given CU) is guaranteed pre-measurement; F2→F4 is a measured decision, not an SLO commitment (§8).

---

## 4. Alerting

| Condition | Severity | Notification target | Source |
|---|---|---|---|
| `bff-api` error-rate > 5% over 5 minutes | Sev-2 | On-call (PagerDuty/Teams incident channel) | Application Insights alert rule |
| Data freshness stale > 60 s during expected active ingestion | Sev-2 | Data platform on-call | Fabric RTI + Log Analytics alert |
| Quarantine rate > 2% of ingested events over 15 minutes | Sev-2 | Data platform on-call | Fabric pipeline monitoring |
| Capacity ARM operation failure (resume/suspend) | Sev-2 | Platform Ops | `capacity-operator` (`bff-api`) + Logic App |
| Capacity budget alert threshold reached | Sev-3 | FinOps + Platform Admin | Azure Cost Management budget alert |
| Energy-dispatch agent tool call without matching human-approval audit event | Sev-1 | Security on-call + RAI board | Sentinel analytics rule (`security-governance-and-threat-model.md` §9) |
| Key Vault secret access outside expected managed identity | Sev-2 | Security on-call | Sentinel analytics rule |
| Anomalous OneLake export volume from Confidential/Highly Confidential item | Sev-2 | Security on-call + DPO | Sentinel analytics rule |
| Model drift or failed 21-day-warning evaluation | Sev-3 (triggers RAI review, not silent redeploy) | Data Scientist + RAI board | MLflow evaluation job |
| 01:00 lifecycle check `SKIPPED_BUSY` more than 3 consecutive days | Sev-4 (investigate why capacity never drains) | Platform Ops | Logic App run history |

Alert routing must never page a demo presenter mid-rehearsal for a non-blocking Sev-3/4 condition; only Sev-1/2 conditions interrupt an active demo/rehearsal window (cross-reference `demo-runbook.md` §8 failure-handling table).

---

## 5. Fabric capacity lifecycle runbook (01:00 daily pause + GUI startup)

This is the operational runbook for the mechanism specified in `deployment-topology.md` §5 and exposed as HTTP in `api-contracts.md` §8. It exists so an on-call engineer can execute or troubleshoot the lifecycle without re-deriving it from the architecture.

### 5.1 Daily 01:00 Europe/Luxembourg lifecycle check — operational procedure

**Scope:** `dev`, `test`, `demo` only. **Production is hard-denied** by environment tag and resource-ID allow-list at two independent layers (the Logic App's own precondition check and `bff-api`'s policy layer) — this is deliberate defense in depth, not redundant code.

Runbook steps (matching `deployment-topology.md` §5.3):

1. **01:00 Europe/Luxembourg, every day** (tested across DST transitions — the Logic App's time-zone mapping, not a naive UTC offset, drives the trigger), the Logic App workflow fires.
2. It reads the target capacity's ARM state and records a correlation ID for the whole run.
3. It verifies the capacity is on the non-production allow-list and that the current time is outside any approved demo/rehearsal window (a calendar/config check, not a guess).
4. It calls the internal `POST /internal/v1/platform/capacity/lifecycle-check` endpoint (`api-contracts.md` §8.5), which asks: is the simulator stopped? Has Event Hubs/relay drained or is a replay checkpoint recorded? Is no protected rehearsal active? Is no pipeline/notebook/semantic-model refresh in a critical phase?
5. **If any precondition fails:** log `SKIPPED_BUSY`, notify the Platform Ops Teams channel, and leave the capacity running. **This is the expected, safe outcome on any day with an active rehearsal** — it must never be treated as a bug to "fix" by forcing the pause.
6. **If safe:** submit `POST .../capacities/{capacityName}/suspend?api-version=2023-11-01`.
7. Treat the `202 Accepted` response as asynchronous; poll the `Location`/`Azure-AsyncOperation` URL respecting `Retry-After`. Do not report success until a terminal state is returned.
8. Persist to the audit log/Log Analytics: actor (`LogicApp:daily-0100`), policy version, precondition evidence, start/end state, ARM operation ID, duration, and result. Alert on failure without a retry storm (i.e., a single retry with backoff, then escalate to Sev-2, not an infinite loop).

### 5.2 On-call response to a 01:00 failure

| Symptom | Action |
|---|---|
| `SKIPPED_BUSY` for one night | No action; expected behavior if a rehearsal or refresh was active |
| `SKIPPED_BUSY` for 3+ consecutive nights | Investigate why the capacity never drains — likely a stuck simulator process, an orphaned pipeline, or a misconfigured rehearsal-window calendar (Sev-4, §4) |
| ARM `suspend` returns a terminal failure | Escalate Sev-2; do not retry blindly — check Fabric service health and capacity-level active operations first; capacity remains available (fails safe) |
| Logic App itself fails to trigger (schedule misfire) | Check DST-transition mapping and Logic App run history; this is a config/deployment defect, not a data-plane incident |

### 5.3 Optional 01:00 resume policy

An organization may deploy a separately approved 01:00 **resume** policy for a specific scheduled event (e.g., "always warm before the 09:00 team's day starts"), using the identical allow-list, ARM polling, readiness check, cost approval, and audit trail as the pause policy. The default remains pause-only, because an automatic resume defeats the cost-control and attendance-based justification for turning capacity on. **Neither pause nor resume automation is ever enabled for `prod`.**

### 5.4 GUI start request and readiness procedure — operational walkthrough

This operationalizes `deployment-topology.md` §5.4 and the HTTP contract in `api-contracts.md` §8.2–§8.4:

1. Operator (holding `Platform.Capacity.Manage`) opens the Platform Ops panel, sees the read-only status pill (visible to everyone), and — because they are outside Demo Mode and hold the role — sees the real "Request start" control.
2. Operator enters a reason (e.g., "Rehearsal for 14:00 defense") and submits. The client calls `POST /v1/platform/capacity/start-requests`; it never calls ARM directly.
3. `bff-api` validates role, environment/capacity allow-list, no conflicting transition, and current state `Paused`; logs actor/reason; calls ARM `resume` via `mi-ns-capacity-demo`.
4. UI polls `GET /v1/platform/capacity/operations/{operationId}` (SSE `capacity.transition` events also fire) and shows `Resuming` — a `202`/`InProgress` response is never presented as "started."
5. On ARM success, `bff-api` runs the readiness checklist: Fabric workspace available, Eventstream/Eventhouse query succeeds, Lakehouse/semantic model reachable, required application APIs healthy, budget not breached, and the demo simulator remains **paused** (it must not auto-start a scenario).
6. Only after every readiness check is green does the UI mark capacity `Running`. The presenter then deliberately starts the simulator/replay — capacity resume never auto-starts a live scenario.
7. If readiness fails, the simulator stays stopped, the UI shows the correlation ID/log link, and the operator switches to the cached/offline demo fallback (`demo-runbook.md` §6) rather than retrying live in front of an audience.

### 5.5 Orderly shutdown procedure (operational checklist)

1. Pause the simulator/accelerated clock; block new demo requests.
2. Stop publishers; wait for in-flight batches to drain or record an explicit replay checkpoint.
3. Preserve the run manifest, scenario seed, health report, capacity metrics, and audit records — never delete evidence to "reset."
4. Confirm no presentation/rehearsal window, active critical-phase data refresh, or approved consumer operation is running.
5. Request pause through the BFF/Logic App for the non-production capacity only; poll the ARM operation to completion.
6. Remove temporary grants, close presenter sessions, verify no publisher connection remains open.

A paused Fabric capacity makes everything assigned to it unavailable — this procedure is therefore never executed while a live demo, RTI ingest, reporting consumer, scheduled pipeline, or production monitoring function still needs the capacity (`deployment-topology.md` §5.5).

---

## 6. Incident response runbooks

### 6.1 Severity matrix (restated from `security-governance-and-threat-model.md` §10.1 as an operations-facing quick reference)

| Severity | Example | Initial response SLA |
|---|---|---|
| Sev-1 | Confirmed breach of Highly Confidential data, OT control-system compromise, energy agent executing an unauthorized scheduling action | 15 min triage, IR commander engaged |
| Sev-2 | Compromised credential/managed identity, Key Vault anomalous access, high-severity Defender for IoT alert, ARM capacity operation failure with capacity stuck in an unknown state | 1 hour |
| Sev-3 | Failed Conditional Access bypass attempt, repeated blocked prompt-injection attempts, quarantine-rate spike | 4 hours |
| Sev-4 | Policy drift, expired non-critical certificate, repeated `SKIPPED_BUSY` | Next business day |

### 6.2 General incident process

1. **Detect** — Sentinel analytics rule, Defender for IoT alert, or an operational SLO breach (§3–§4) fires and auto-creates an incident with linked entities.
2. **Triage & contain** — on-call confirms severity; for Sev-1/2, disable the affected identity, revoke OneLake security-role access, and (for OT incidents) coordinate with the OT/ICS Engineer to isolate the affected network zone without disrupting furnace safety-instrumented systems.
3. **Eradicate & recover** — rotate affected secrets/keys, re-image compromised compute, re-issue managed-identity federated credentials if federation trust was implicated.
4. **Notify** — DPO assesses GDPR Article 33/34 obligations; if personal data (including interview audio/transcripts) is implicated, notify the competent supervisory authority within 72 hours and affected data subjects without undue delay where high risk exists.
5. **Post-incident review** — root-cause logged; the STRIDE table and abuse-case table (`security-governance-and-threat-model.md` §17–§18) are updated if a new attack path is revealed; the security acceptance gates (§21 of the same document) are updated if the gap should have been caught pre-release.

### 6.3 Platform-specific runbooks

#### 6.3.1 "Live stream stopped / no live events" (operational, non-security)

1. Check `ingest-relay` health signal (event-time lag, connection state) in Application Insights.
2. If Event Hubs is healthy but Eventstream is not consuming, check Fabric service health and the Custom Endpoint publisher identity's token validity.
3. If unresolved within the SLA in §3, switch the affected demo/rehearsal to local deterministic replay (`implementation-guide.md` §5) and open a Sev-2/3 per the actual root cause once identified.
4. Never restart the simulator repeatedly against a live audience-facing session; use the pre-created fallback state instead (`demo-runbook.md` §4 minute-by-minute proof points).

#### 6.3.2 "Capacity stuck in `Resuming`/`Draining`"

1. Poll `GET /v1/platform/capacity/operations/{operationId}` for the ARM long-running-operation status directly.
2. If ARM reports a terminal failure, follow §5.2's row for ARM failures.
3. If ARM reports success but the readiness checklist keeps failing, check each readiness component individually (Fabric workspace, Eventstream/Eventhouse query, Lakehouse/semantic-model reachability, application health, budget) rather than re-submitting the resume operation blindly.
4. Escalate to Sev-2 if stuck beyond twice the measured SLO in §3.

#### 6.3.3 "Quarantine rate spike"

1. Query `ingest_quarantine_hot`/`quarantine_event` for the dominant `quarantine_reason`.
2. `SCHEMA_INVALID` spike → check for an unreviewed schema/contract change upstream (simulator or real gateway); this is a contract-test gap, escalate to the owning service team.
3. `UNKNOWN_ASSET` spike → check `dim_asset`/`dim_plant` reference-data freshness in silver.
4. `LATE_BEYOND_POLICY` spike → check gateway/relay buffering and network path health.
5. Never silently repair a quarantined record; fix the upstream cause and let the record remain queryable as evidence, per `solution-architecture.md` §3.3.

#### 6.3.4 "Agent tool call without matching approval" (Sev-1 security path)

1. Immediately treat as a potential control-boundary breach, not a UI bug — this exact condition is the platform's highest-severity automated detection (`security-governance-and-threat-model.md` §9 minimum analytics rules).
2. IR commander engaged within 15 minutes; disable the implicated agent identity's tool-calling capability pending investigation.
3. Confirm from the audit trail (`api-contracts.md` §9) whether any downstream write actually occurred; if so, this becomes a Sev-1 regardless of whether the write reached a real system, because the architecture guarantees no such write should be possible (ADR-006/ADR-007).
4. Full STRIDE/abuse-case review before the agent's tool scope is re-enabled.

---

## 7. Demo reset procedures (engineering-owned runbook)

These restate `demo-runbook.md` §9 as an engineering runbook with explicit tooling references, so the supporting platform engineer (not only the presenter) can execute them.

### 7.1 Soft reset between rehearsals (target: < 5 minutes, per §3 SLO)

1. Pause the accelerated clock (simulator control API/CLI).
2. Stop publishers cleanly; wait for in-flight batches to drain.
3. Set scenario to `demo-full`, root seed `240725`, simulated start time to the manifest value.
4. Clear only the synthetic run's hot cache, alert state, demo work-order link, interview session, and UI selections — never touch preloaded historical partitions or the fallback-pack artifacts.
5. Restore model responses and optimizer outputs from the matching manifest (the cached/signed fixtures from `implementation-guide.md` §6.2 `SIM-006`).
6. Reset alert to `ARMED`, stream to `PAUSED`, persona to Plant Manager.
7. Run for 30 seconds; verify sequence, event count, expected checksum, freshness, and synthetic labels.
8. Pause and mark control state `READY`.

### 7.2 Hard recovery (target: < 20 minutes, per §3 SLO)

Use when the run is contaminated, sequence state is unknown, or scenario outputs do not reconcile:

1. Stop the simulator and disconnect its publisher.
2. Record the failed `run_id`; do **not** delete evidence until after diagnosis — this is both an engineering and an audit requirement.
3. Create a new `run_id` and isolated synthetic namespace.
4. Reload the signed reference snapshot and historical scenario data.
5. Reset sink checkpoints/deduplication state for the new namespace only — never for a shared or production checkpoint store.
6. Replay the manifest and re-run contract, physical, and scenario assertions (`api-contracts.md` §11.3).
7. Refresh the semantic model and verify the cue sheet (`demo-runbook.md` §5).
8. Reopen the seven presenter tabs, test fallback files, and return to `READY`.

**Absolute rule:** never truncate a shared or production table, clear a shared event stream, or reuse a production secret as part of any reset — this applies to both soft and hard reset paths without exception.

### 7.3 Post-demo checklist

- Pause and stop the simulator.
- Save the run manifest, timestamps, and demo health report as release evidence.
- Delete ad hoc microphone recordings unless retention was explicitly approved; retain only the approved synthetic artifact.
- Close sessions, remove temporary access grants, confirm no publisher remains active.
- Record any fallback used during the session and schedule a rehearsal of that specific failed chapter before the next presentation.

### 7.4 Go/no-go checklist (engineering sign-off before presenter go-ahead)

Proceed only when: all displayed data is labeled synthetic; deterministic manifests and expected cues validate; the live stream and at least two fallback levels work; alert/optimizer/quality/knowledge cached results are available; microphone/audio and privacy messaging are tested; no production credentials or data are visible; reset completes within the §3 SLO; the presenter can finish the story entirely offline. If any synthetic-data boundary, privacy control, or safety disclaimer is missing, the demo is **no-go** — this is a hard gate, not a judgment call left to the presenter alone.

---

## 8. Cost assumptions and controls

### 8.1 Cost model (restated as an operational control table from `deployment-topology.md` §6)

| Cost driver | Control | Decision gate |
|---|---|---|
| Fabric capacity CU consumption | F2 initial demo, bounded stream rate, scheduled notebooks, safe non-production pause, Capacity Metrics review | F4 only on measured contention; production SKU chosen after a pilot load test |
| Power BI licenses | Pro/PPU/trial for all consumers below F64 | Never buy F64 solely to avoid per-user licensing |
| OneLake/KQL/Activator retained data | Explicit retention/cache settings; quarantine and raw-telemetry lifecycle; storage budget | Reviewed after each rehearsal/pilot; a paused capacity does **not** erase storage cost |
| Spark/autoscale | Off by default; batch windows and measured notebook duration | Enabled only with a named owner, budget, and workload evidence |
| Foundry model/token and Speech usage | Smallest suitable approved model, transcript/upload quotas, budget alarms, cached demo responses | Re-evaluated after actual usage and a regional quota check |
| Event Hubs and relay | Partition/retention sized from observed throughput; store-and-forward rather than overprovisioning | Test peak/recovery replay, then reserve/scale only where justified |
| Logs/Sentinel | Classification-aware sampling/retention; no raw audio/prompt payload logging | Confirmed jointly against the security retention policy and budget |
| DR | Reproducible infrastructure/artifacts first; cold/warm West Europe only after a justified RTO/RPO | Never pay for an untested duplicate capacity |

### 8.2 Explicit non-claims

**Exact regional currency price is intentionally not stated anywhere in this document** because it is offer-, currency-, and date-specific (`deployment-topology.md` §6). Any budget figure quoted to stakeholders must be pulled live from the official Azure/Fabric pricing pages and calculator for Sweden Central at the time of the quote, not copied from this or any other design document.

### 8.3 Required cost controls at go-live

1. **Azure budgets and cost alerts** on every resource group, tagged `costCenter` and `expiry` (the `expiry` tag is mandatory for every `demo` resource, per `deployment-topology.md` §3.1).
2. **Fabric Capacity Metrics app** reviewed weekly by Platform Ops; CU utilization and throttling trends feed the F2→F4 decision.
3. **Capacity overage disabled by default** for the demo environment; any limited exception has a named owner and an explicit expiry date recorded in the same budget system.
4. **FinOps review cadence:** weekly during active rehearsal/pilot phases, monthly thereafter, cross-checked against the SLO/error-budget review in §3.

### 8.4 F2 → F4 decision procedure

1. Run the scripted 15-minute demo (and at least one stress rehearsal with concurrent pipeline/notebook activity) on F2.
2. Capture Capacity Metrics CU utilization, throttling events, and query/report latency during the run.
3. If throttling or latency measurably degrades the presenter experience (subjective threshold: any fallback-ladder trigger attributable to capacity contention rather than a genuine fault), escalate to F4 with the same budget/owner sign-off as any other cost-driver change (§8.1 row 1).
4. F4 is never selected merely to obtain a Power BI licensing side-effect — that decision is independently governed by the Pro/PPU/trial rule in §8.1 row 2, per `solution-architecture.md` §2 reconciliation table.

---

## 9. Resilience, DR posture, and production caveats

### 9.1 Availability posture (operational summary of `deployment-topology.md` §7)

| Layer | Primary resilience mechanism | Degraded-mode operational response |
|---|---|---|
| OT telemetry | DMZ store-and-forward + Event Hubs replay, sequence/idempotency | Freshness/gap made visible; never interpolate operational truth to hide a gap |
| Fabric hot path | Eventstream dual destination (KQL + bronze); replay from buffer/bronze | Cached semantic data/RTI screenshot for demo; production incident runbook (§6) for pilot/prod |
| Lakehouse data | Immutable bronze, reconciled silver/gold, source-controlled transforms | Restore/reprocess from retained bronze/source extracts — never hand-patch gold |
| Application/AI | Stateless BFF/workers, health probes, retry/backoff, queue/replay semantics | Manual/cached recommendation and text-based knowledge workflow |
| Foundry/Speech | Human review independent of model availability | Queue consented capture; manual transcript/draft; no auto-publish |
| Demo | Deterministic local replay, cached interactive assets, recording, static proof pack | First working fallback level is explicitly announced as replay/cached (§7) |
| Region | Sweden Central primary; reproducible infrastructure/definitions | West Europe recovery only after approved data/restoration validation (§9.2) |

### 9.2 Recovery principles (do not weaken these when writing a future DR plan)

1. **No untested automatic cross-region Fabric failover.** Sweden Central's documented Power BI BCDR caveat means RTO/RPO cannot be promised until a specific recovery design is exercised end to end.
2. **Infrastructure and definitions are recoverable from source control/IaC.** Fabric item automation is validated per item type (`implementation-guide.md` §9.2); any non-exportable state has a documented manual rebuild procedure, not an assumption that "it will just come back."
3. **Bronze/replay data is the recovery source.** Reprocessing from bronze is preferred over manual silver/gold correction; audit facts are retained as evidence and are never deleted to "reset" a production run.
4. **Demonstration resilience is local-first.** The demo must finish even if Fabric, Foundry, Speech, market data, or the network is unavailable — this is why local demo mode (`implementation-guide.md` §5) is a first-class build requirement, not an afterthought.
5. **Production recovery needs explicit service targets before go-live.** Business, OT, DPO, security, and platform owners must jointly agree RTO/RPO per data domain and test a restore in an EU recovery location before any production onboarding sign-off (§10).

### 9.3 Production caveats this operations document must never relax

These restate `implementation-guide.md` §15 from an operations lens — they are the boundaries an on-call engineer must never "fix around" under incident pressure:

1. **No automated production capacity pause/resume ever exists.** Under no incident-response pressure does an on-call engineer add the production capacity ID to the 01:00 Logic App's allow-list "just for tonight." A capacity-cost emergency in production is handled through the standard change-management process (`deployment-topology.md` §5.2, "production capacity lifecycle" row), not this document's automation.
2. **No incident response action ever writes to a PLC, safety interlock, furnace, or production setpoint**, regardless of how compelling the automated fix appears. Any proposal to do so is itself immediately a Sev-1-adjacent governance escalation requiring security/legal/OT/RAI review (ADR-007), not an on-call judgment call.
3. **Energy/quality "approve" actions remain simulated/shadow in Phase 0/1.** An on-call engineer must never manually flip a database flag to make an approval "real" as an incident workaround; that is a data-integrity and governance violation, not a fix.
4. **Foundry Data Zone (EU) processing is not a single-region guarantee.** If a legal/DPO requirement for Sweden-Central-only processing is later confirmed, this is a configuration change to a regional deployment (`implementation-guide.md` §15 item 5) executed through the standard release process, not an operational hotfix.
5. **Demo/production data, identity, and workspace isolation is never bridged**, even temporarily, to unblock an incident. If a demo rehearsal genuinely needs production-realistic data, that requirement is redirected to the synthetic-data workstream (`synthetic-data-and-simulators.md`), not solved by a one-off cross-environment shortcut.

### 9.4 Pre-production gate checklist (operations sign-off)

Before any non-synthetic pilot/production traffic is onboarded, operations must confirm (mirroring `deployment-topology.md` §9 "Before non-synthetic pilot/production"):

- [ ] Target Fabric/Foundry/Speech regional availability, quota, deployment type, and private-network support rechecked at deployment time (not assumed from this document's date).
- [ ] DPO approved DPIA, lawful basis, consent/erasure workflow, retention, and any West Europe recovery copy.
- [ ] Legal confirmed EU AI Act classification and production human-oversight evidence requirements.
- [ ] OT/ICS owner signed off the DMZ protocol/egress design; no cloud-to-OT control path exists.
- [ ] Custom Endpoint Contributor blast-radius test, Fabric tenant switches, and query-adapter identity test passed.
- [ ] Capacity, Power BI license, cost budget, performance, recovery, and incident-response tests passed (§3, §8, §9 of this document).
- [ ] Security release gates (identity, protected feeds, threat model, logging, data labels, agent tools, supply chain — `security-governance-and-threat-model.md` §21) passed.

---

## 10. Weekly/monthly operational cadence

| Cadence | Activity | Owner |
|---|---|---|
| Daily | Review 01:00 Logic App run result; triage any Sev-1/2 overnight alerts | Platform on-call |
| Weekly | Capacity Metrics review (§8.3); Sentinel detection review (`security-governance-and-threat-model.md` §9); SLO/error-budget review (§3) | Platform Ops + Security engineer |
| Weekly (during active rehearsal/pilot) | FinOps budget review | FinOps + Platform Admin |
| Monthly | OneLake security-role and workspace-role audit via the Secure tab (`security-governance-and-threat-model.md` §2.3); PIM activation review | Platform Admin + Compliance |
| Per model release | Drift/evaluation review; RAI board sign-off before promotion | Data Scientist + RAI board |
| Per rehearsal | Demo go/no-go checklist (§7.4) | Platform Ops + presenter |
| Quarterly (post-pilot) | DR restore test in an EU recovery location | Platform SRE + DPO |

---

## 11. Cross-reference index

| Operations concern | Primary section here | Authoritative architecture source |
|---|---|---|
| Observability signal set | §2 | `solution-architecture.md` §9.2 |
| SLOs | §3 | `solution-architecture.md` §9.1; `deployment-topology.md` §5 |
| Capacity lifecycle (01:00 pause, GUI start) | §5 | `deployment-topology.md` §5 |
| Incident response | §6 | `security-governance-and-threat-model.md` §10, §17–§18 |
| Demo reset | §7 | `demo-runbook.md` §9–§10 |
| Cost model | §8 | `deployment-topology.md` §6 |
| Resilience/DR/production caveats | §9 | `deployment-topology.md` §7; `solution-architecture.md` §9.1 |
