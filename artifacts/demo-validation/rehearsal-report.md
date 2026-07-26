# NovaSteel 15-Minute Oral-Defense Demo — Rehearsal Report

> **Result:** ✅ **GO (local deterministic mode)** — every demo moment reproduced live over real HTTP; 1 issue found and fixed.
> **Date:** 2026-07-25 · **Mode:** local deterministic (`DEMO_MODE=local`), **no cloud resources deployed**
> **Owner:** todo `demo-validation` · **Runbook:** [docs/demo/demo-runbook.md](../../docs/demo/demo-runbook.md) · **Plan:** [docs/presentation/oral-defense-and-slide-plan.md](../../docs/presentation/oral-defense-and-slide-plan.md)
> **Evidence root:** `artifacts/demo-validation/` (http · logs · scenario · screenshots)

---

## 1. Executive summary

The comprehensive solution was rehearsed end to end as the runbook's 15-minute
live demo, driven against a locally running BFF and the built portal/analytics
UI, using only the deterministic synthetic scenario `demo-full` (root seed
`240725`). Results:

| Area | Result |
|---|---|
| Six demo moments (DM-1…DM-6) + telemetry/alert, audit, capacity | **66/66 live HTTP checks passed** |
| Runbook cue sheet (§5) values | **All matched exactly** (RUL 21.0 / 16.8 / 27.5, risk 0.87 HIGH; 280 EUR/MWh peak; tonnage 960=960, 0 violations; yield 88%→95%; WO-DEMO-LUX-1042) |
| Table search / filter / sort / pagination | **10 live API checks + 11 component tests** pass |
| Determinism (generate ×2, reset, API re-run) | **Byte-for-byte identical**; domain payloads identical across BFF restarts |
| Fallback ladder + no external network | **12/12 checks** (3 levels + integrity gate + socket guard) |
| PowerPoint | **PASS** — 26 slides, 714 runs, 0 placeholders, aligns to all demo transitions |
| Startup / shutdown scripts | **Validated** (`npm run run:bff`, `dotnet run`, `Stop-Process -Id`) |
| Backend latency per moment | **< 0.1 s each** (total 0.23 s) — far inside the runbook's 10 s ceiling |
| Issues found | **1** — BFF CORS allowlist missing the portal origin → **fixed** in owning code, re-verified, no regression |

---

## 2. Environment and toolchain

| Component | Value |
|---|---|
| OS | Windows (PowerShell) |
| Python (BFF/simulator venv) | 3.13.14 — `services/bff-api/.venv` |
| Node / npm | v22.19.0 / 10.9.3 |
| .NET SDK | 10.0.302 |
| BFF | FastAPI 0.139.2 + uvicorn, `127.0.0.1:8080` |
| Portal shell | Blazor WASM, `http://localhost:5266` (https `7075`) |
| Data | `services/bff-api/fixtures/demo-full` (seed 240725), namespace `NS-DEMO-LUX-01` |

The working tree is not a git checkout (`.git` absent); no commit hash is
available. Simulator has **no third-party dependencies** (pure stdlib).

---

## 3. Startup / shutdown / reset (validated)

**Startup — BFF (documented `npm run run:bff`):**
```
> uvicorn bff_api.main:app --port 8080   (DEMO_MODE=local, PYTHONPATH set)
Application startup complete → /health/ready = 200
/v1/meta → demoMode:true, authMode:demo, dataNamespace:NS-DEMO-LUX-01
```
Log: `logs/bff_run3.log`.

**Startup — UI (documented build + `dotnet run`):**
```
npm run build:analytics   → wwwroot/analytics-mfe/analytics-mfe.js (1.68 MB), .css
dotnet restore … --configfile NuGet.Config ; npm run build:portal   → 0 warnings, 0 errors
dotnet run --project apps/portal-shell/PortalShell.csproj --launch-profile http → http://localhost:5266
```
Served-asset probes (all 200): `/`, `/appsettings.json` (BFF `http://localhost:8080`),
`/_framework/blazor.webassembly.js`, `/analytics-mfe/analytics-mfe.js`, `/analytics-mfe/analytics-mfe.css`.
Logs: `logs/build_analytics.log`, `logs/portal_build.log`, `logs/portal_run.log`;
served page saved to `screenshots/portal-served-index.html`.
(`/_framework/blazor.boot.json` returns 404 by design — .NET 10 moved boot config into the import map.)

**Shutdown:** `Stop-Process -Id <pid>` on the listener of port 8080 / 5266
(exercised three times during restarts; port confirmed free after each).

**Soft reset / re-run:** restarting the BFF clears in-memory alert/work-order/
recommendation/interview state to `READY`; the simulator `reset` subcommand
deletes only a generated run directory and never touches manifests or the
committed fixture (verified — see §7).

---

## 4. Minute-by-minute walkthrough (six demo moments)

Each runbook moment was reproduced by calling the exact BFF endpoints the UI
uses, with the correct persona (RBAC) header, asserting the runbook cue values.
Backend latency is the measured HTTP time; the 15-minute budget is narration.

| Runbook window | Moment | Endpoints exercised (persona) | Cue verified | Backend |
|---|---|---|---|---|
| 00:00–02:00 | **DM-1** Command center + persona switch + Fabric framing | `/v1/me` ×7 personas, `/v1/command-center/summary`, `/v1/dashboard/kpis` (Exec) | 7 distinct personas; 7 KPIs; synthetic banner; freshness green | 0.036 s |
| (stream) | Live/historical telemetry + armed alert | `/v1/telemetry`, `/v1/furnaces/{id}/telemetry`, `/v1/realtime/alerts` (SSE), `:poll` | 2110 telemetry rows, default `eventTs desc`; SSE stream opens | 0.022 s |
| 04:30–07:00 | **DM-3** Furnace RUL 21-day + uncertainty + work order | `/v1/furnaces`, `/v1/furnaces/LUX-BF-01/lining-forecast`, `POST /v1/workorders` (Reliability) | **P50 21.0 d, P10 16.8 < 21 < P90 27.5, risk 0.87 HIGH**; `WO-DEMO-LUX-1042` PLANNED_INSPECTION | 0.016 s |
| 02:00–04:30 | **DM-2** Energy dispatch (equal tonnage, zero violations) | `/v1/energy/intervals`, `POST /v1/energy/schedules:simulate`, `…:approve` (Energy) | **280 EUR/MWh peak; tonnage 960=960; 0 hard violations; cost −9.94% (8–13%); peak −5.16%**; urgent batch fixed; shadow-approved | 0.014 s |
| 07:00–09:30 | **DM-4** Quality genealogy + what-if + yield | `/v1/quality/batches`, `/…/{id}/genealogy`, `POST /v1/quality/what-if` (Quality) | `COIL-LUX-260725-017` full lineage (lot→heat→ladle→slab→reheat→coil→sample→shipment); **yield 88.0%→95.0%**, `operationalWrite=false` | 0.011 s |
| 12:00–13:00 | **DM-6** Sustainability / CO₂ / ETS | `/v1/sustainability/summary`, `/v1/sustainability/emissions` (Exec) | scope1/scope2 CO₂; **ETS allowance 86 EUR/tonne**; modeled dispatch CO₂ −8.7%; 96 emission rows | 0.006 s |
| 09:30–12:00 | **DM-5** Operator interview / STT / Foundry knowledge | `POST /v1/knowledge/interviews`, `/…/transcript`, `/v1/knowledge/procedures?status=`, `…:approve`, `/v1/knowledge/search` (Knowledge) | consent recorded; Foundry **DRAFT** produced (cannot self-publish); IN_REVIEW queue; KE approval→**APPROVED**; STT transcript with confidence + speaker segments | 0.020 s |
| 13:00–14:00 | Audit evidence (append-only) | `/v1/audit/decisions`, `?domain=energy` (Exec/Auditor) | 7 append-only records; energy approval traced; actor+correlation+timestamp linked | 0.005 s |
| lifecycle | Capacity start / status / pause (simulated) | `/v1/platform/capacity`, `…/start-requests`, `…/operations/{id}`, `…/pause-requests` (Platform) | start `SIMULATED`, operation retrievable, pause `SIMULATED` | 0.013 s |
| — | Server-side authorization boundaries | Operator→energy (403), no-auth (401), non-`NS-DEMO` scope (401) | all rejected as expected | 0.005 s |

**Total backend wall-clock across all moments: 0.23 s** — every screen is ready
well within the runbook's "do not wait more than 10 seconds" rule.
Driver: `drive_demo.py`; per-response evidence: `http/*.json`; summary:
`http/_summary.json`; on-screen render: `screenshots/dashboard-snapshot.md`.

---

## 5. Tables — search / filter / sort / pagination

**Live API semantics (TBL-STD)** — 10 checks on `/v1/telemetry` (2110 rows):
enum filter (`quality=GOOD`), text-contains filter (`signalCode=hearth` → 582),
numeric range (`value=100..150` → 280), global `q=hearth` search, `sort=value:asc`
(verified ascending), disjoint pagination with stable total, ISO date range
(`from/to`), invalid sort → **400**, `size>200` → **400**, and cross-entity
`/v1/search?q=LUX` (5 groups). Evidence: `http/tables_*.json`.

**Component tests** (`npm run test:frontend`, 28/28 pass): `tableProcessing.test.ts`
(7 — numeric asc/desc sort, per-column AND, global OR, stable multi-column sort)
and `DataTable.test.tsx` (4 — default desc render, header-click re-sort, global
search box, per-column header search). Log: `logs/frontend_tests.log`.

---

## 6. Determinism and reset

- **Generate ×2:** two independent `simulator demo` runs (`genA`, `genB`) are
  **byte-for-byte identical** across all nine `.ndjson` datasets (SHA-256 compare
  empty). Logs: `logs/sim_genA.log`, `sim_genB.log`; hashes: `scenario/genA-hashes.txt`, `genB-hashes.txt`.
- **Fixture parity:** a fresh generation is **identical to the committed fixture**
  `services/bff-api/fixtures/demo-full`.
- **Validators:** contract, physics, scenario-assertion, checksum, and
  `contracts/events` JSON-schema validators all **PASS** (2110 telemetry + all
  datasets). Log: `logs/sim_validate_genA.log`.
- **Reset:** `simulator reset` removed only the 11 generated items, preserved the
  directory, left the 5 manifests untouched, and the committed fixture still
  verifies (`checksums OK`). Log: `logs/sim_reset_genB.log`.
- **API re-run determinism:** after a full BFF restart (state reset), a second
  driver run produced **identical domain payloads** for every deterministic
  endpoint (same `REC-EB7A0DEDE29F`, RUL 21.0/16.8/27.5/0.87, cost −9.94%,
  tonnage 960=960). Log: `logs/rerun_determinism.log`.

---

## 7. Fallback ladder and offline (no-network) posture

Verified by `verify_fallback.py` under a process-wide socket guard that blocks
every non-loopback TCP connect (12/12 checks — `logs/verify_fallback.log`):

1. **Level 1 — local deterministic replay:** committed simulator fixture loads
   (`simulator-fixture:demo-full`), serves RUL 21.0 + furnace inventory.
2. **Level 2 — cached interactive:** an alternate generated snapshot directory
   loads and serves 2110 telemetry rows.
3. **Level 3 — built-in static fallback:** with all fixtures removed, the BFF
   engages its in-code `built-in-fallback` datasets and still serves the
   deterministic RUL 21.0 / tonnage 960 headline evidence.
4. **Integrity gate:** a tampered fixture (extra line) is **rejected** by the
   SHA-256/byte-count check before being served.
5. **Offline compute:** the scoring worker (RUL) and optimizer (dispatch) run
   fully in-process; **zero non-loopback connections** were attempted across the
   entire demo path. The BFF binds `127.0.0.1` only and reads local files only.

The `http/*.json` responses captured here (alert, lining forecast, optimizer
result, genealogy, what-if, transcript, procedure draft, audit) constitute the
runbook §6.2 static proof pack for the recorded/proof-pack fallback levels.

**Operational fallback instructions (presenter, per runbook §6.1):** use the
first working level and say "replay" / "cached result":
(1) live cloud → (2) `npm run run:bff` local deterministic replay → (3) cached
`http/*.json` responses / `screenshots/dashboard-snapshot.md` → (4) recorded
flow → (5) `docs/presentation/NovaSteel-Oral-Defense.pptx` static proof + JSON.
Never spend more than 10 s diagnosing on stage.

---

## 8. PowerPoint alignment

`validate_pptx.py` → **PASS**: 26 slides, 714 text runs, no placeholder/TODO
findings (`http/presentation_validation.json`). Structure: 19 content slides →
**slide 20 "DEMO HANDOFF"** (the 30:00 transition) → 6 FAQ backup slides. The
four "AI DEEP DIVE" slides (12–15) pre-load the demo's four AI capabilities so
the live demo confirms rather than introduces. A keyword scan confirms the deck
pre-loads **every** demo transition (DM-1…DM-6, audit/traceability, the
synthetic honesty contract, the demo handoff, and the 14/22/21/8 targets).
Logs: `logs/pptx_validate.log`, `logs/pptx_alignment.log`, `logs/pptx_titles.log`.

---

## 9. Issue found and fixed

**CORS allowlist did not include the portal shell origin (browser-demo blocker).**

- **Symptom:** Following the documented startup exactly, the Blazor shell serves
  at `http://localhost:5266` (its `launchSettings.json` http profile; https
  `7075`) and calls the BFF at `:8080`, but the BFF default
  `BFF_CORS_ORIGINS` was `http://localhost:5000,http://localhost:5173`. A CORS
  preflight from `5266` returned **400**, so every browser→BFF call in the live
  demo would have failed.
- **Fix (owning code):** added the portal origins to the BFF default allowlist —
  `services/bff-api/src/bff_api/config.py` now defaults to
  `http://localhost:5266,https://localhost:7075,http://localhost:5000,http://localhost:5173`;
  documented in `services/bff-api/README.md`.
- **Verification:** preflight from `5266` and `7075` now returns **200** with the
  matching `Access-Control-Allow-Origin`; a disallowed origin still returns
  **400** (allowlist remains restrictive). No regression — BFF unit tests
  **11/11**, demo driver **66/66** after the change (tests build CORS origins
  explicitly, so the default change touches no test expectation).

---

## 10. Remaining cloud-only gates (out of scope for local demo)

These require a target Azure tenant and cannot be proven in local deterministic
mode (aligned with `docs/validation-report.md` §"Remaining production gates"):

1. Fabric F-SKU/quota provisioning and measurement (Sweden Central).
2. Eventstream Custom Endpoint managed-identity publishing, isolated Contributor
   role, tenant switch, permitted network path.
3. Foundry model/deployment type, Agent Service tool set/quota, Speech features
   (incl. **live STT**), and private-network behavior in the tenant.
4. Fabric query adapter's Entra / item-level authorization behavior.
5. DPO/Legal: lawful basis, DPIA, retention/deletion, EU AI Act classification.
6. OT vendor/site approval for each DMZ protocol, source, rate, ownership boundary.
7. Market-data licensing/freshness; any Phase 2 CMMS/scheduling connector.
8. Fallback ladder **Level 1 (live cloud)**: Fabric stream, semantic model, model
   endpoints, live STT — cloud-only; Levels 2–5 validated locally here.

---

## 11. Tooling limitations (documented, not blockers)

- **Full-browser click-through (Playwright)** is not installed and cannot be
  added offline under the approved-feed policy. The browser path was instead
  validated by: served-HTML/asset probes (200), the **CORS preflight fix**, and
  **28 DOM render/component tests** (DataTable, AnalyticsDashboard command-center
  banner + RUL uncertainty band). Pixel screenshots must be captured from the
  presenter's browser on demo day; `screenshots/dashboard-snapshot.md` renders
  the on-screen values from live data as an interim proof.

---

## 12. Evidence index (`artifacts/demo-validation/`)

- `drive_demo.py` — live HTTP demo driver (66 checks) · `http/_summary.json`
- `verify_fallback.py` — fallback ladder + no-network guard (12 checks)
- `http/*.json` — per-moment BFF responses (DM-1…DM-6, audit, capacity, tables) + run-1 snapshot in `http_run1/`
- `scenario/genA`, `genB`, `*-hashes.txt` — determinism generations + SHA-256 sets
- `screenshots/portal-served-index.html`, `screenshots/dashboard-snapshot.md`
- `logs/` — BFF, builds, portal serve, frontend/BFF tests, simulator gen/validate/reset, determinism, pptx, fallback

**Conclusion:** the platform runs the full 15-minute oral-defense demo in local
deterministic mode with all six moments, tables, audit, capacity, determinism,
offline fallback, and slide alignment verified; the single CORS defect was fixed
in owning code and re-verified. **GO for local rehearsal.**
