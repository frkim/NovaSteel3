"""Gold analytical-dataset validators (contract conformance, guardrails,
determinism, and honest KPI assertions).

This module validates the output of ``simulator/analytics.py`` against:

* **Contract conformance** -- every emitted table is validated against
  ``contracts/data/gold.v2.json`` (contract v2, natural keys): it must be
  declared there, its column set and order must equal the contract's declared
  columns, the generator's idempotency key must equal the contract's
  ``idempotencyKey``, and both the ``primaryKey`` and ``idempotencyKey`` must be
  unique across the produced rows. The contract is the single source of truth --
  ``EXPECTED_COLUMNS`` and the key lists are derived from it, so contract, tables
  and validator cannot silently drift.
* **Guardrail provenance** -- the run manifest carries
  ``data_classification=SYNTHETIC``, ``privacy_label=DEMO-NONPERSONAL``,
  ``generator_version``, ``scenario_id`` and ``seed``; every ``plant_id`` is
  ``NS-DEMO-`` prefixed; audit actor identifiers are ``OP-DEMO-`` synthetic
  ids and no names/emails leak.
* **Headline KPIs recomputed from rows** -- energy per ton, specific CO2,
  high-grade first-pass yield and the furnace-lining advance warning are all
  recomputed here directly from the emitted rows (never read from the
  summary) and checked against the manifest targets/tolerances. The lining
  warning check also proves internal consistency: the alert fires exactly at
  ``rul_days_p50 == warning_days`` with ``risk_score >= 0.80`` and *no* row
  with ``rul_days_p50 > target`` carries an alert -- so a "High = 7-20 days"
  style contradiction is impossible.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

_CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "data" / "gold.v2.json"


def _load_gold_contract() -> dict | None:
    if not _CONTRACT_PATH.exists():
        return None
    return json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))


_CONTRACT = _load_gold_contract()
_CONTRACT_TABLES = {t["name"]: t for t in (_CONTRACT["tables"] if _CONTRACT else [])}

# Derived from contracts/data/gold.v2.json (the single source of truth) rather
# than hand-maintained here, so the contract, the produced tables and this
# validator can never silently drift. Column order matches the declared column
# order, which is also the produced CSV order and the deployed Delta DDL order.
EXPECTED_COLUMNS = {
    name: [c["name"] for c in spec.get("columns", [])]
    for name, spec in _CONTRACT_TABLES.items()
}
CONTRACT_PRIMARY_KEYS = {name: spec["primaryKey"] for name, spec in _CONTRACT_TABLES.items()}
CONTRACT_IDEMPOTENCY_KEYS = {name: spec["idempotencyKey"] for name, spec in _CONTRACT_TABLES.items()}


@dataclass
class GoldReport:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    checked: int = 0

    def add(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False


def _gold_contract_tables() -> set[str] | None:
    if _CONTRACT is None:
        return None
    return set(_CONTRACT_TABLES)


def _unique_key_error(rows: list, keycols: list) -> dict | None:
    seen: set[tuple] = set()
    for row in rows:
        key = tuple(row.get(k) for k in keycols)
        if key in seen:
            return dict(zip(keycols, key))
        seen.add(key)
    return None


def validate_gold_contract(datasets: dict, idempotency_keys: dict) -> GoldReport:
    """Assert the produced tables against contracts/data/gold.v2.json.

    This is a genuine contract test: it reads the binding contract file and,
    for every produced table, checks (1) the table is declared in the contract,
    (2) its column set and order equal the contract's declared columns, (3) the
    generator's idempotency key equals the contract's ``idempotencyKey`` (so the
    two cannot drift), (4) the contract's ``primaryKey``/``idempotencyKey``
    columns all exist, and (5) both the primary key and the idempotency key are
    unique across the produced rows (honouring the declared grain).
    """
    report = GoldReport()
    if _CONTRACT is None:
        report.checked += 1
        report.add(f"contract file not found at {_CONTRACT_PATH}")
        return report
    version = _CONTRACT.get("contractVersion")
    for name, rows in datasets.items():
        report.checked += 1
        spec = _CONTRACT_TABLES.get(name)
        if spec is None:
            report.add(f"{name}: not declared in contracts/data/gold.v2.json (v{version})")
            continue
        expected = [c["name"] for c in spec.get("columns", [])]
        if not expected:
            report.add(f"{name}: contract declares no columns to validate against")
            continue

        for row in rows:
            actual = list(row.keys())
            if actual != expected:
                report.add(f"{name}: column set/order mismatch vs contract v{version}: "
                           f"{actual} != {expected}")
                break

        primary_key = list(spec.get("primaryKey", []))
        contract_idem = list(spec.get("idempotencyKey", []))

        generator_idem = idempotency_keys.get(name)
        if generator_idem is not None and list(generator_idem) != contract_idem:
            report.add(f"{name}: generator idempotency key {list(generator_idem)} "
                       f"!= contract idempotencyKey {contract_idem}")

        for label, keycols in (("primaryKey", primary_key), ("idempotencyKey", contract_idem)):
            missing = [c for c in keycols if c not in expected]
            if missing:
                report.add(f"{name}: contract {label} columns {missing} are not declared columns")
                continue
            duplicate = _unique_key_error(rows, keycols)
            if duplicate is not None:
                report.add(f"{name}: duplicate {label} {duplicate}")
    return report


def validate_guardrails(run_manifest: dict, datasets: dict) -> GoldReport:
    report = GoldReport()
    required = {
        "data_classification": "SYNTHETIC",
        "privacy_label": "DEMO-NONPERSONAL",
    }
    for field_name, expected in required.items():
        report.checked += 1
        if run_manifest.get(field_name) != expected:
            report.add(f"manifest {field_name}={run_manifest.get(field_name)!r} != {expected!r}")
    for field_name in ("generator_version", "scenario_id", "seed"):
        report.checked += 1
        if not run_manifest.get(field_name) and run_manifest.get(field_name) != 0:
            report.add(f"manifest missing guardrail field {field_name!r}")

    for name, rows in datasets.items():
        report.checked += 1
        for row in rows:
            plant_id = row.get("plant_id")
            if plant_id is not None and not str(plant_id).startswith("NS-DEMO-"):
                report.add(f"{name}: plant_id {plant_id!r} is not NS-DEMO- prefixed")
                break
        # Furnace rows must carry per-row synthetic provenance.
        if name == "fact_furnace_rul":
            for row in rows:
                if row.get("scenario_id") != run_manifest.get("scenario_id"):
                    report.add(f"{name}: scenario_id provenance missing/incorrect")
                    break

    # No names/emails may leak in the audit correlation/actor fields.
    for row in datasets.get("fact_ai_decision_audit", []):
        blob = json.dumps(row)
        if _EMAIL_RE.search(blob):
            report.add("fact_ai_decision_audit: an email-like string leaked into an audit record")
            break
        corr = str(row.get("correlation_id", ""))
        if "OP-" in corr:
            actor = corr.split("OP-")[-1]
            if not actor.startswith("DEMO-"):
                report.add(f"fact_ai_decision_audit: operator id not OP-DEMO- synthetic ({corr})")
                break
    return report


def _weighted_intensity(rows, num_field, rollout_iso):
    b_num = b_den = a_num = a_den = 0.0
    for r in rows:
        if r["date_key"] < rollout_iso:
            b_num += float(r[num_field]); b_den += float(r["crude_steel_tons"])
        else:
            a_num += float(r[num_field]); a_den += float(r["crude_steel_tons"])
    before = b_num / b_den if b_den else 0.0
    after = a_num / a_den if a_den else 0.0
    reduction = 1.0 - after / before if before else 0.0
    return before, after, reduction


def _high_grade_yield(rows, rollout_iso):
    b_num = b_den = a_num = a_den = 0.0
    for r in rows:
        high = r["high_grade_flag"]
        high = high in (True, "true", "True", "1")
        if not high:
            continue
        if r["date_key"] < rollout_iso:
            b_num += float(r["first_pass_good_tons"]); b_den += float(r["attempted_tons"])
        else:
            a_num += float(r["first_pass_good_tons"]); a_den += float(r["attempted_tons"])
    before = b_num / b_den if b_den else 0.0
    after = a_num / a_den if a_den else 0.0
    return before, after, after - before


def validate_kpis(datasets: dict, targets: dict, tolerances: dict, rollout_iso: str,
                  primary_asset_id: str) -> GoldReport:
    """Recompute every headline KPI directly from the rows and check it against
    the manifest target within tolerance."""
    report = GoldReport()

    _, _, energy_reduction = _weighted_intensity(datasets["fact_energy_daily"], "energy_gj", rollout_iso)
    _, _, co2_reduction = _weighted_intensity(datasets["fact_emissions_daily"], "total_co2e_t", rollout_iso)
    _, _, yield_gain = _high_grade_yield(datasets["fact_quality_yield"], rollout_iso)

    checks = [
        ("energy_intensity_reduction", energy_reduction),
        ("co2_intensity_reduction", co2_reduction),
        ("high_grade_yield_gain_pp", yield_gain),
    ]
    for key, measured in checks:
        target = float(targets[key])
        tol = float(tolerances.get(key, 0.01))
        report.checked += 1
        if abs(measured - target) > tol:
            report.add(f"{key}: measured {measured:.4f} not within {tol} of target {target}")

    # Furnace-lining advance warning, recomputed from the primary campaign rows.
    target_days = int(targets["lining_warning_days"])
    tol_days = int(tolerances.get("lining_warning_days", 0))
    alert_rows = [r for r in datasets["fact_furnace_rul"]
                  if r["asset_id"] == primary_asset_id and r["alert_issued_at"]]
    report.checked += 1
    if not alert_rows:
        report.add("no furnace-lining alert row found for the primary asset")
    else:
        first = min(alert_rows, key=lambda r: r["scored_date"])
        scored = date.fromisoformat(first["scored_date"])
        predicted = date.fromisoformat(first["predicted_failure_date"])
        warning_days = (predicted - scored).days
        if abs(warning_days - target_days) > tol_days:
            report.add(f"lining_warning_days: measured {warning_days} != target {target_days}")
        p50 = float(first["rul_days_p50"])
        if int(round(p50)) != warning_days:
            report.add(f"lining alert p50 {p50} inconsistent with advance warning {warning_days}")
        if float(first["risk_score"]) < 0.80:
            report.add(f"lining alert risk_score {first['risk_score']} < 0.80 threshold")
    # Threshold consistency: no row above target may carry an alert.
    for r in datasets["fact_furnace_rul"]:
        if r["alert_issued_at"] and float(r["rul_days_p50"]) > target_days:
            report.add(f"furnace alert fired at p50={r['rul_days_p50']} > target {target_days} "
                       "(a 'High band' contradiction)")
            break
    return report


def validate_analytical_run(run_dir: Path) -> tuple[bool, dict]:
    """Load a persisted analytical run directory and validate everything.

    Returns ``(ok, reports)`` where ``reports`` maps a validator name to its
    ``GoldReport``.
    """
    from simulator.analytics import GOLD_TABLES

    manifest_path = run_dir / "manifest.json"
    run_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    datasets = {name: _read_csv(run_dir / f"{name}.csv") for name in GOLD_TABLES
                if (run_dir / f"{name}.csv").exists()}

    idempotency_keys = run_manifest.get("idempotency_keys", {})
    measured = run_manifest.get("measured_kpis", {})
    summary = run_manifest.get("summary", {})
    targets = summary.get("kpi_targets", {})
    tolerances = summary.get("kpi_tolerances", {})
    rollout_iso = measured.get("rollout_date") or run_manifest.get("rollout_date")
    primary_asset = measured.get("lining_primary_asset_id", "LUX-BF-01")

    reports = {
        "contract": validate_gold_contract(datasets, idempotency_keys),
        "guardrails": validate_guardrails(run_manifest, datasets),
        "kpi": validate_kpis(datasets, targets, tolerances, rollout_iso, primary_asset),
    }
    ok = all(r.ok for r in reports.values())
    return ok, reports


def _read_csv(path: Path) -> list[dict]:
    import csv
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))
