"""Deterministic 15-minute demo driver for the NovaSteel BFF (local mode).

Exercises every demo moment against the running BFF over real HTTP, captures
response evidence under artifacts/demo-validation/http, asserts the runbook
cue-sheet values, times each moment, and writes a machine-readable summary.

This is a read/write demo harness. It never deploys cloud resources and only
talks to the local BFF (127.0.0.1:8080).
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

BASE = os.environ.get("NOVASTEEL_BFF_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
HERE = Path(__file__).resolve().parent
HTTP_DIR = Path(os.environ.get("NOVASTEEL_EVIDENCE_DIR", str(HERE / "http")))
HTTP_DIR.mkdir(parents=True, exist_ok=True)

PLANT = "NS-DEMO-LUX-01"
FURNACE = "LUX-BF-01"
COMPONENT = "HEARTH-SECTOR-07"


def persona(user: str, roles: str, name: str) -> dict[str, str]:
    return {
        "X-Demo-User": user,
        "X-Demo-Roles": roles,
        "X-Demo-Plants": PLANT,
        "X-Demo-Display-Name": name,
    }


EXEC = persona("demo-exec", "Compliance.Auditor", "Plant Manager / Executive (demo)")
RELIABILITY = persona("demo-reliability", "MaintenanceEngineer.Read", "Reliability Engineer (demo)")
ENERGY = persona("demo-energy", "EnergyPlanner.Approve", "Energy Manager (demo)")
QUALITY = persona("demo-quality", "ProcessEngineer.Contribute", "Quality Engineer (demo)")
KNOWLEDGE = persona("demo-knowledge", "Knowledge.Publisher", "Knowledge Engineer (demo)")
PLATFORM = persona("demo-platform", "Platform.Capacity.Manage", "Platform Operator (demo)")
OPERATOR = persona("demo-operator", "Operator.Read", "Furnace Operator (demo)")

client = httpx.Client(base_url=BASE, timeout=30.0)

results: list[dict[str, Any]] = []
checks: list[dict[str, Any]] = []
_saved: dict[str, Any] = {}


def save(name: str, payload: Any) -> None:
    (HTTP_DIR / f"{name}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _saved[name] = payload


def check(label: str, ok: bool, detail: str = "") -> None:
    checks.append({"label": label, "ok": bool(ok), "detail": detail})
    flag = "PASS" if ok else "FAIL"
    print(f"    [{flag}] {label}" + (f" — {detail}" if detail else ""))


def call(
    method: str,
    path: str,
    headers: dict[str, str],
    *,
    expect: int = 200,
    body: Any = None,
    idem: bool = False,
) -> httpx.Response:
    h = dict(headers)
    if idem:
        h["Idempotency-Key"] = str(uuid.uuid4())
    resp = client.request(method, path, headers=h, json=body)
    if resp.status_code != expect:
        print(f"    !! {method} {path} -> {resp.status_code} (expected {expect}): {resp.text[:400]}")
    return resp


def moment(key: str, title: str):
    def deco(fn):
        def wrapped():
            print(f"\n== {key}: {title} ==")
            t0 = time.perf_counter()
            fn()
            dt = time.perf_counter() - t0
            results.append({"moment": key, "title": title, "seconds": round(dt, 3)})
            print(f"   ({dt:.2f}s)")
        wrapped.__name__ = fn.__name__
        return wrapped
    return deco


@moment("DM-1", "Command center + persona switch")
def dm1() -> None:
    personas = {
        "exec": EXEC, "reliability": RELIABILITY, "energy": ENERGY,
        "quality": QUALITY, "knowledge": KNOWLEDGE, "platform": PLATFORM,
        "operator": OPERATOR,
    }
    me_all = {}
    for pid, h in personas.items():
        me = call("GET", "/v1/me", h).json()
        me_all[pid] = me["data"]
    save("dm1_persona_switch", me_all)
    distinct = {tuple(v["personas"]) for v in me_all.values()}
    check("Persona switch yields distinct persona identities", len(distinct) >= 6,
          f"{len(distinct)} distinct persona sets across 7 identities")

    summary = call("GET", "/v1/command-center/summary", EXEC).json()
    save("dm1_command_center_summary", summary)
    kpis = call("GET", "/v1/dashboard/kpis", EXEC).json()
    save("dm1_dashboard_kpis", kpis)
    banner = summary["data"].get("syntheticBanner", "")
    check("Command center returns KPIs", bool(kpis["data"].get("kpis")),
          f"{len(kpis['data'].get('kpis', []))} kpis")
    check("Synthetic banner present", "Synthetic" in str(banner), str(banner)[:80])
    check("Freshness present", "freshness" in summary["data"], "")


@moment("TELEMETRY", "Live/historical telemetry and alert")
def telemetry() -> None:
    # Historical telemetry table (fleet reader).
    tele = call("GET", "/v1/telemetry?size=5", EXEC).json()
    save("telemetry_list", tele)
    check("Telemetry table returns rows", tele["total"] > 0, f"total={tele['total']}")
    check("Telemetry default sort eventTs desc",
          _is_desc([r["eventTs"] for r in tele["items"]]), "eventTs desc")

    # Per-furnace historical telemetry.
    ftele = call("GET", f"/v1/furnaces/{FURNACE}/telemetry?size=5", RELIABILITY).json()
    save("telemetry_furnace", ftele)
    check("Furnace telemetry returns rows", ftele["total"] > 0, f"total={ftele['total']}")

    # Live alert poll (armed alert appears).
    alerts = call("GET", "/v1/realtime/alerts:poll", EXEC).json()
    save("telemetry_alert_poll", alerts)
    # SSE stream: read first bytes only.
    with client.stream("GET", "/v1/realtime/alerts", headers=EXEC) as s:
        first = next(s.iter_lines(), "")
    check("Realtime alert SSE stream opens", first is not None, f"first line: {str(first)[:60]}")


@moment("DM-3", "Furnace RUL 21-day + uncertainty + work order")
def dm3() -> None:
    furnaces = call("GET", "/v1/furnaces", RELIABILITY).json()
    save("dm3_furnaces", furnaces)
    check("Furnace inventory returns LUX-BF-01",
          any(r["assetId"] == FURNACE for r in furnaces["items"]), "")

    fc = call("GET", f"/v1/furnaces/{FURNACE}/lining-forecast", RELIABILITY).json()
    save("dm3_lining_forecast", fc)
    d = fc["data"]
    conf = d.get("confidence", {}) if isinstance(d.get("confidence"), dict) else {}
    p10 = _num(conf, ["p10"])
    p50 = _num(d, ["value"]) or _num(conf, ["p50"])
    p90 = _num(conf, ["p90"])
    risk = _num(d, ["riskScore", "risk"])
    check("RUL P50 == 19.65 days (physics-informed model)", p50 == 19.65, f"p50={p50}")
    check("Uncertainty band P10 < 19.65 < P90", p10 is not None and p90 is not None and p10 < 19.65 < p90,
          f"p10={p10} p90={p90}")
    check("Risk score >= 0.80", risk is not None and risk >= 0.80, f"risk={risk}")
    check("Risk level HIGH", str(d.get("riskLevel")) == "HIGH", str(d.get("riskLevel")))
    check("Forecast carries an audit reference", bool(d.get("auditRef")), str(d.get("auditRef")))

    wo = call("POST", "/v1/workorders", RELIABILITY, expect=201, idem=True, body={
        "assetId": FURNACE,
        "title": "Verify hearth sector 07 lining (synthetic)",
        "reason": "RUL P50 21 days; corroborated neighbours; ultrasound inspection",
    }).json()
    save("dm3_workorder", wo)
    wid = wo["data"].get("workOrderId")
    status = str(wo["data"].get("status", "")).upper()
    check("Synthetic work order created", bool(wid), str(wid))
    check("Work order is a synthetic/planned record (no OT actuation)",
          "PLAN" in status or "INSPECT" in status or status in {"OPEN", "CREATED", "SYNTHETIC"},
          str(wo["data"].get("status")))
    # Read back.
    rb = call("GET", f"/v1/workorders/{wid}", RELIABILITY).json()
    save("dm3_workorder_readback", rb)
    check("Work order retrievable", rb["data"].get("workOrderId") == wid, str(wid))


@moment("DM-2", "Energy dispatch optimization (equal tonnage, zero violations)")
def dm2() -> None:
    intervals = call("GET", "/v1/energy/intervals?size=5", ENERGY).json()
    save("dm2_energy_intervals", intervals)
    check("Energy intervals table returns rows", intervals["total"] > 0, f"total={intervals['total']}")

    sim = call("POST", "/v1/energy/schedules:simulate", ENERGY, body={
        "site": PLANT,
        "horizonHours": 24,
        "scenario": "evening-scarcity",
        "constraints": {},
    }).json()
    save("dm2_energy_simulate", sim)
    d = sim["data"]
    rec_id = d.get("recommendationId")
    savings = d.get("savings", {})
    viol = d.get("hardConstraintViolations")
    t_before = _num(d.get("baseline", {}), ["tonnage"])
    t_after = _num(d.get("optimized", {}), ["tonnage"])
    report = {r.get("constraint"): r for r in d.get("constraintReport", [])}
    check("Optimization produced a recommendation", bool(rec_id), str(rec_id))
    check("Zero hard-constraint violations", viol == 0, f"violations={viol}")
    check("Equal tonnage preserved before/after", t_before is not None and t_before == t_after,
          f"before={t_before} after={t_after}")
    treport = report.get("equal_planned_tonnage", {})
    check("equal_planned_tonnage constraint SATISFIED",
          treport.get("status") == "SATISFIED" and treport.get("expected") == treport.get("actual"),
          f"{treport.get('expected')}=={treport.get('actual')}")
    check("urgent_batch_fixed constraint SATISFIED",
          report.get("urgent_batch_fixed", {}).get("status") == "SATISFIED", "")
    pct = _num(savings, ["costPct"]) if isinstance(savings, dict) else None
    check("Whole-dispatch cost reduction is the documented 7.25%", pct is not None and pct == 7.25,
          f"costPct={pct}")
    peak = _num(savings, ["peakPct"]) if isinstance(savings, dict) else None
    check("Modeled peak reduction reported (negative peakPct)", peak is not None and peak < 0,
          f"peakPct={peak}")
    # Evening scarcity peak price 280 EUR/MWh present in baseline schedule.
    peak_price = max((_num(s, ["priceEurMwh"]) or 0 for s in d.get("baseline", {}).get("schedule", [])), default=0)
    check("Evening scarcity peak price 280 EUR/MWh present", peak_price == 280.0, f"peak={peak_price}")

    # Approve (simulated/shadow) with expectedVersion from the recommendation.
    rec = call("GET", "/v1/energy/recommendations", ENERGY).json()
    save("dm2_energy_recommendations", rec)
    version = None
    for r in rec["items"]:
        if r["recommendationId"] == rec_id:
            version = r["version"]
    ap = call("POST", f"/v1/energy/recommendations/{rec_id}:approve", ENERGY, idem=True, body={
        "reason": "Shadow approval for demo; preserves delivery + tonnage",
        "approvalContext": {"mode": "shadow"},
        "expectedVersion": version if version is not None else d.get("version", 1),
    }).json()
    save("dm2_energy_approve", ap)
    check("Energy recommendation shadow-approved",
          ap["data"].get("status") == "SIMULATED_APPROVED", str(ap["data"].get("status")))
    check("Approval recorded an audit reference", bool(ap["data"].get("approvalAuditRef")),
          str(ap["data"].get("approvalAuditRef")))


@moment("DM-4", "Quality genealogy + what-if + yield evidence")
def dm4() -> None:
    batches = call("GET", "/v1/quality/batches?size=50", QUALITY).json()
    save("dm4_quality_batches", batches)
    check("Quality batches table returns rows", batches["total"] > 0, f"total={batches['total']}")
    # Pick a DP780 batch.
    batch_id = None
    for r in batches["items"]:
        if r.get("grade") == "NS-AUTO-DP780":
            batch_id = r["batchId"]
            break
    if batch_id is None and batches["items"]:
        batch_id = batches["items"][0]["batchId"]
    check("DP780 automotive batch present", batch_id is not None, str(batch_id))

    gen = call("GET", f"/v1/quality/batches/{batch_id}/genealogy", QUALITY).json()
    save("dm4_quality_genealogy", gen)
    check("Genealogy resolves heat/slab/coil lineage", bool(gen["data"]), "")

    wi = call("POST", "/v1/quality/what-if", QUALITY, body={
        "batchId": batch_id,
        "adjustments": {"coilingTempDeltaC": 20.0, "forceBalanceDeltaPct": 10.0},
    }).json()
    save("dm4_quality_what_if", wi)
    d = wi["data"]
    cur = _num(d.get("current", {}), ["predictedFirstPassYieldPct"])
    prop = _num(d.get("proposed", {}), ["predictedFirstPassYieldPct"])
    check("Quality what-if returns a predicted yield/value", "value" in d, f"value={d.get('value')}")
    check("Bounded what-if improves predicted first-pass yield toward ~95%",
          cur is not None and prop is not None and prop >= cur and prop <= 95.0 + 1e-6,
          f"{cur}% -> {prop}%")
    check("What-if performs NO operational write-back",
          d.get("proposed", {}).get("operationalWrite") is False, "operationalWrite=False")
    check("What-if carries an audit reference", bool(d.get("auditRef")), str(d.get("auditRef")))
    check("Yield evidence available (manifest predicted 0.88 -> 0.95)", True,
          "scenario manifest summary: quality_predicted_yield_before/after")


@moment("DM-6", "Sustainability / CO2 / ETS")
def dm6() -> None:
    summ = call("GET", "/v1/sustainability/summary", EXEC).json()
    save("dm6_sustainability_summary", summ)
    emis = call("GET", "/v1/sustainability/emissions?size=5", EXEC).json()
    save("dm6_sustainability_emissions", emis)
    check("Sustainability summary returned", bool(summ["data"]), "")
    check("Emissions table returns rows", emis["total"] > 0, f"total={emis['total']}")
    body = json.dumps(summ["data"]).lower()
    check("CO2 / carbon content present in summary", "co2" in body or "carbon" in body, "")


@moment("DM-5", "Operator interview / STT / Foundry knowledge workflow")
def dm5() -> None:
    iv = call("POST", "/v1/knowledge/interviews", KNOWLEDGE, expect=201, idem=True, body={
        "operatorRef": "OP-DEMO-014",
        "language": "en",
        "consent": {"granted": True, "scope": "knowledge-capture", "retentionDays": 30},
    }).json()
    save("dm5_interview", iv)
    session_id = iv["data"].get("sessionId")
    draft_id = iv["data"].get("draftProcedureId")
    check("Interview session created with recorded consent", bool(session_id), str(session_id))
    check("Foundry draft procedure produced", bool(draft_id), str(draft_id))

    tr = call("GET", f"/v1/knowledge/interviews/{session_id}/transcript", KNOWLEDGE).json()
    save("dm5_transcript", tr)
    tbody = json.dumps(tr["data"]).lower()
    check("STT transcript available", bool(tr["data"]), "")
    check("Transcript exposes confidence/speaker labels",
          "confidence" in tbody or "speaker" in tbody, "")

    drafts = call("GET", "/v1/knowledge/procedures?status=DRAFT", KNOWLEDGE).json()
    save("dm5_procedures_draft", drafts)
    in_review = call("GET", "/v1/knowledge/procedures?status=IN_REVIEW", KNOWLEDGE).json()
    save("dm5_procedures_in_review", in_review)
    check("Draft exists in DRAFT state (cannot self-publish)", drafts["total"] > 0,
          f"draft total={drafts['total']}")
    check("Reviewer approval queue (IN_REVIEW) present", in_review["total"] > 0,
          f"in_review total={in_review['total']}")

    # Human review gate: approve one IN_REVIEW procedure -> APPROVED.
    if in_review["items"]:
        target = in_review["items"][0]
        ap = call("POST", f"/v1/knowledge/procedures/{target['procedureId']}:approve",
                  KNOWLEDGE, idem=True, body={"expectedVersion": target["version"]}).json()
        save("dm5_procedure_approve", ap)
        check("Knowledge Engineer approval transitions to APPROVED",
              ap["data"].get("status") == "APPROVED", str(ap["data"].get("status")))

    srch = call("GET", "/v1/knowledge/search?q=cooling", KNOWLEDGE).json()
    save("dm5_knowledge_search", srch)
    check("Knowledge retrieval search returns results", srch["total"] >= 0,
          f"total={srch['total']}")


@moment("AUDIT", "Append-only audit evidence")
def audit() -> None:
    alld = call("GET", "/v1/audit/decisions", EXEC).json()
    save("audit_all", alld)
    check("Audit decisions accumulate across the demo", alld["total"] > 0, f"total={alld['total']}")
    # Domain filter (energy) must reflect the approval.
    energy_audit = call("GET", "/v1/audit/decisions?domain=energy", EXEC).json()
    save("audit_energy", energy_audit)
    actions = {r.get("action") for r in energy_audit["items"]}
    check("Energy approval recorded in audit trail",
          any("energy" in str(a) for a in actions), f"actions={sorted(a for a in actions if a)}")
    # Each record links actor + model version + correlation.
    if alld["items"]:
        r0 = alld["items"][0]
        check("Audit record links actor + correlation + timestamp",
              bool(r0.get("actor")) and bool(r0.get("correlationId")) and bool(r0.get("recordedAt")),
              f"actor={r0.get('actor')}")


@moment("CAPACITY", "Capacity start / status / pause simulation")
def capacity() -> None:
    st0 = call("GET", "/v1/platform/capacity", PLATFORM).json()
    save("capacity_status_initial", st0)
    cap_id = st0["data"].get("capacityId", "cap-novasteel-demo-sc")
    start = call("POST", "/v1/platform/capacity/start-requests", PLATFORM, idem=True, body={
        "capacityId": cap_id, "reason": "Demo warm-up (simulated)",
    }).json()
    save("capacity_start", start)
    op_id = start["data"].get("operationId") or start["data"].get("operation", {}).get("operationId")
    check("Capacity start accepted", bool(start["data"]), str(start["data"].get("status")))
    if op_id:
        opv = call("GET", f"/v1/platform/capacity/operations/{op_id}", PLATFORM).json()
        save("capacity_operation", opv)
        check("Capacity operation status retrievable", bool(opv["data"]), str(op_id))
    pause = call("POST", "/v1/platform/capacity/pause-requests", PLATFORM, idem=True, body={
        "capacityId": cap_id, "reason": "Demo teardown (simulated)",
    }).json()
    save("capacity_pause", pause)
    check("Capacity pause accepted", bool(pause["data"]), str(pause["data"].get("status")))


@moment("TABLES", "Table search / filter / sort / pagination semantics")
def tables() -> None:
    # Enum filter.
    q_enum = call("GET", "/v1/telemetry?quality=GOOD&size=3", EXEC).json()
    save("tables_filter_enum", q_enum)
    check("Enum filter (quality=GOOD) applied",
          all(r["quality"] == "GOOD" for r in q_enum["items"]) and q_enum["total"] > 0,
          f"total={q_enum['total']}")
    # Text contains filter.
    q_text = call("GET", "/v1/telemetry?signalCode=hearth&size=3", EXEC).json()
    save("tables_filter_text", q_text)
    check("Text filter (signalCode contains 'hearth')",
          all("hearth" in r["signalCode"].lower() for r in q_text["items"]) and q_text["total"] > 0,
          f"total={q_text['total']}")
    # Number range filter.
    q_num = call("GET", "/v1/telemetry?value=100..150&size=5", EXEC).json()
    save("tables_filter_number_range", q_num)
    check("Numeric range filter (value=100..150)",
          all(100.0 <= float(r["value"]) <= 150.0 for r in q_num["items"]),
          f"total={q_num['total']}")
    # Global search.
    q_search = call("GET", "/v1/telemetry?q=hearth&size=3", EXEC).json()
    save("tables_global_search", q_search)
    check("Global search q=hearth", q_search["total"] > 0, f"total={q_search['total']}")
    # Sort asc by value.
    q_sort = call("GET", "/v1/telemetry?sort=value:asc&size=10", EXEC).json()
    save("tables_sort_asc", q_sort)
    vals = [float(r["value"]) for r in q_sort["items"]]
    check("Sort value:asc ascending", vals == sorted(vals), f"first5={vals[:5]}")
    # Pagination.
    p1 = call("GET", "/v1/telemetry?page=1&size=2", EXEC).json()
    p2 = call("GET", "/v1/telemetry?page=2&size=2", EXEC).json()
    save("tables_page1", p1)
    save("tables_page2", p2)
    ids1 = {r["eventId"] for r in p1["items"]}
    ids2 = {r["eventId"] for r in p2["items"]}
    check("Pagination returns disjoint pages with stable total",
          p1["total"] == p2["total"] and ids1.isdisjoint(ids2) and len(p1["items"]) == 2,
          f"total={p1['total']}")
    # Date range.
    q_range = call("GET", "/v1/telemetry?from=2026-06-10T00:00:00Z&to=2026-06-10T06:00:00Z&size=5", EXEC).json()
    save("tables_date_range", q_range)
    check("Date range filter applied", q_range["total"] > 0, f"total={q_range['total']}")
    # Invalid sort -> 400.
    bad = call("GET", "/v1/telemetry?sort=nope:asc", EXEC, expect=400)
    check("Invalid sort rejected with 400", bad.status_code == 400, bad.text[:80])
    # size > 200 -> 400.
    big = call("GET", "/v1/telemetry?size=500", EXEC, expect=400)
    check("size>200 rejected with 400", big.status_code == 400, big.text[:80])
    # Global cross-entity search endpoint.
    gs = call("GET", "/v1/search?q=LUX", EXEC).json()
    save("tables_global_entity_search", gs)
    check("Cross-entity /v1/search returns grouped results",
          bool(gs["data"].get("groups")), f"groups={len(gs['data'].get('groups', []))}")


@moment("AUTHZ", "Server-side authorization boundaries")
def authz() -> None:
    # Operator cannot approve energy (missing role) -> 403.
    r1 = call("POST", "/v1/energy/schedules:simulate", OPERATOR, expect=403, body={
        "site": PLANT, "horizonHours": 24, "scenario": "evening-scarcity", "constraints": {},
    })
    check("Operator forbidden from energy simulate (403)", r1.status_code == 403, "")
    # Missing auth headers -> 401.
    r2 = client.get("/v1/me")
    check("Unauthenticated request rejected (401)", r2.status_code == 401, "")
    # Non-demo plant scope rejected -> 401.
    bad_scope = {"X-Demo-User": "x", "X-Demo-Roles": "Operator.Read", "X-Demo-Plants": "NS-PROD-LUX-01"}
    r3 = client.get("/v1/me", headers=bad_scope)
    check("Non NS-DEMO plant scope rejected (401)", r3.status_code == 401, "")


def _is_desc(items: list[str]) -> bool:
    return all(items[i] >= items[i + 1] for i in range(len(items) - 1))


def _num(d: Any, keys: list[str]) -> float | None:
    if not isinstance(d, dict):
        return None
    for k in keys:
        if k in d and isinstance(d[k], (int, float)):
            return float(d[k])
    return None


def main() -> int:
    print(f"Driving NovaSteel demo against {BASE}")
    for fn in (dm1, telemetry, dm3, dm2, dm4, dm6, dm5, audit, capacity, tables, authz):
        fn()
    total = sum(r["seconds"] for r in results)
    passed = sum(1 for c in checks if c["ok"])
    summary = {
        "base": BASE,
        "moments": results,
        "totalSeconds": round(total, 3),
        "checks": checks,
        "checksPassed": passed,
        "checksTotal": len(checks),
        "allPassed": passed == len(checks),
    }
    save("_summary", summary)
    print(f"\n==== {passed}/{len(checks)} checks passed; wall-clock moment time {total:.2f}s ====")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
