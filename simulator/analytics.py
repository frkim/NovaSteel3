"""Analytical multi-month gold-fact generator (static/analytical data stream).

This is the *analytical* counterpart to the streaming event generator in
``simulator/generator.py``. Where that path emits 15-second canonical event
envelopes for a single short demo window, this path emits **gold-grain
star-schema facts** (``contracts/data/gold.v2.json``) at daily/shift grain
spanning roughly 24 months, so the NovaSteel platform can show a *programme*
trend instead of a single shift.

Design goals
------------
* **Deterministic / byte-reproducible.** Every value is drawn from a
  ``determinism.child_random`` stream seeded from the manifest ``root_seed``.
  Two runs of the same manifest produce byte-identical CSVs (verified by
  ``simulator/validators/gold_contract.py`` and the determinism tests).
* **Honest, computed-from-rows KPIs.** An explicit efficiency-programme
  ``rollout_date`` splits the window into a *before* and *after* period. The
  headline deltas (energy per ton -14%, specific CO2 -22%, high-grade
  first-pass yield +8pp, 21-day furnace-lining advance warning) are computed
  by aggregating the emitted rows -- never hard-coded into a summary. Risk
  thresholds are chosen so the 21-day warning genuinely falls out of the data
  (the alert fires exactly when ``rul_days_p50 <= 21`` and ``risk >= 0.80``,
  and those two conditions coincide at 21 days).
* **Loader-ready.** The emitted columns match, one-for-one, the deployed
  ``lh_novasteelv3_core`` Delta table DDL in
  ``fabric/notebooks/ns-initialize-lakehouses.Notebook`` so the loader can
  MERGE straight into the existing tables idempotently.

Guardrail provenance (``data_classification``, ``privacy_label``,
``generator_version``, ``scenario_id``, ``seed``, ``root_seed``,
``config_checksum``) is recorded in the run ``manifest.json`` for the whole
dataset; the two fact tables whose deployed schema carries ``scenario_id`` /
``seed`` columns (``fact_furnace_rul``) also carry them per row.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from simulator import GENERATOR_VERSION, config
from simulator.checksum import write_checksums
from simulator.determinism import child_random, config_checksum

ANALYTICAL_MANIFEST_DIR = Path(__file__).parent / "manifests" / "analytical"

# Gold fact tables emitted by this generator, in dependency order.
GOLD_TABLES = [
    "fact_production_shift",
    "fact_energy_daily",
    "fact_emissions_daily",
    "fact_quality_yield",
    "fact_furnace_rul",
    "fact_dispatch_recommendation",
    "fact_knowledge_procedure",
    "fact_ai_decision_audit",
]

# Idempotency keys per gold table (honours contracts/data/gold.v2.json grains,
# expressed with the natural-key columns of the deployed physical schema).
IDEMPOTENCY_KEYS = {
    "fact_production_shift": ["shift_id"],
    "fact_energy_daily": ["date_key", "plant_id"],
    "fact_emissions_daily": ["date_key", "plant_id"],
    "fact_quality_yield": ["date_key", "plant_id", "grade_code"],
    "fact_furnace_rul": ["inference_id"],
    "fact_dispatch_recommendation": ["recommendation_id"],
    "fact_knowledge_procedure": ["procedure_id", "version"],
    "fact_ai_decision_audit": ["audit_id"],
}

SHIFTS = ("A", "B", "C")
SHIFT_START_HOUR = {"A": 6, "B": 14, "C": 22}
ETS_ALLOWANCE_PRICE_EUR_PER_T = 82.0
FREE_ALLOCATION_T_PER_T = 1.50


class AnalyticalManifestError(ValueError):
    pass


@dataclass
class AnalyticalScenario:
    raw: dict

    @property
    def scenario_id(self) -> str:
        return self.raw["scenario_id"]

    @property
    def root_seed(self) -> int:
        return int(self.raw["root_seed"])

    @property
    def end_date(self) -> date:
        return date.fromisoformat(self.raw["end_date"])

    def months(self, fast: bool) -> int:
        return int(self.raw["fast_months"]) if fast else int(self.raw["months"])

    def start_date(self, fast: bool) -> date:
        # Approximate months as 30-day blocks so the window is fully data-driven
        # and identical on every platform.
        return self.end_date - timedelta(days=self.months(fast) * 30)

    def rollout_date(self, fast: bool) -> date:
        if fast:
            return self.start_date(fast) + timedelta(days=int(self.raw["fast_rollout_offset_days"]))
        return date.fromisoformat(self.raw["rollout_date"])

    @property
    def plants(self) -> list[str]:
        return list(self.raw["plants"])

    @property
    def grades(self) -> list[dict]:
        return list(self.raw["grades"])

    @property
    def plant_baselines(self) -> dict:
        return self.raw["plant_baselines"]

    @property
    def kpi_targets(self) -> dict:
        return self.raw["kpi_targets"]

    @property
    def kpi_tolerances(self) -> dict:
        return self.raw["kpi_tolerances"]

    @property
    def quality_yield(self) -> dict:
        return self.raw["quality_yield"]

    @property
    def furnace_campaigns(self) -> list[dict]:
        return list(self.raw["furnace_campaigns"])

    @property
    def dispatch(self) -> dict:
        return self.raw["dispatch"]

    @property
    def model_versions(self) -> dict:
        return self.raw["model_versions"]

    def validate(self) -> None:
        required = ["scenario_id", "root_seed", "end_date", "months", "rollout_date",
                    "plants", "grades", "plant_baselines", "kpi_targets", "quality_yield",
                    "furnace_campaigns", "dispatch", "model_versions"]
        missing = [f for f in required if f not in self.raw]
        if missing:
            raise AnalyticalManifestError(f"analytical manifest missing required fields: {missing}")
        for plant in self.plants:
            if plant not in self.plant_baselines:
                raise AnalyticalManifestError(f"plant {plant!r} has no baseline entry")
            if plant not in config.PLANTS:
                raise AnalyticalManifestError(f"plant {plant!r} is not a known synthetic plant")
        alloc = round(sum(g["allocation"] for g in self.grades), 6)
        if alloc != 1.0:
            raise AnalyticalManifestError(f"grade allocations must sum to 1.0, got {alloc}")


def load_analytical_manifest(scenario_id_or_path: str) -> AnalyticalScenario:
    candidate = Path(scenario_id_or_path)
    if candidate.suffix == ".json" and candidate.exists():
        path = candidate
    else:
        path = ANALYTICAL_MANIFEST_DIR / f"{scenario_id_or_path}.json"
    if not path.exists():
        available = sorted(p.stem for p in ANALYTICAL_MANIFEST_DIR.glob("*.json"))
        raise AnalyticalManifestError(
            f"unknown analytical scenario {scenario_id_or_path!r}; available: {available}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    scenario = AnalyticalScenario(raw)
    scenario.validate()
    return scenario


def list_analytical_scenarios() -> list[str]:
    if not ANALYTICAL_MANIFEST_DIR.exists():
        return []
    return sorted(p.stem for p in ANALYTICAL_MANIFEST_DIR.glob("*.json"))


@dataclass
class AnalyticalRunResult:
    scenario: AnalyticalScenario
    out_dir: Path
    fast: bool
    fmt: str
    datasets: dict = field(default_factory=dict)
    measured_kpis: dict = field(default_factory=dict)
    summary: dict = field(default_factory=dict)
    file_paths: dict = field(default_factory=dict)
    run_manifest_path: Path | None = None
    checksums: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Deterministic helpers                                                        #
# --------------------------------------------------------------------------- #

def _daterange(start: date, end_inclusive: date):
    day = start
    while day <= end_inclusive:
        yield day
        day += timedelta(days=1)


def _seasonal(day: date, phase: float) -> float:
    """Mean-zero seasonal wave keyed on day-of-year (integrates to ~0 over a
    full year, so it does not bias before/after period means)."""
    doy = day.timetuple().tm_yday
    return math.sin(2.0 * math.pi * (doy / 365.0) + phase)


def _iso_ts(day: date, hour: int = 6, minute: int = 0) -> str:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _content_hash(*parts) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:16]


def _improvement_factor(day: date, rollout: date, reduction: float) -> float:
    """1.0 before the rollout, (1 - reduction) on/after it -- the explicit
    before/after boundary the KPI deltas are computed against."""
    return (1.0 - reduction) if day >= rollout else 1.0


# --------------------------------------------------------------------------- #
# Fact generators                                                             #
# --------------------------------------------------------------------------- #

def _generate_production(scenario: AnalyticalScenario, start: date, end: date) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    daily_tons: dict[tuple[str, date], float] = {}
    calc_version = scenario.model_versions["production"]
    for plant_id in scenario.plants:
        base = scenario.plant_baselines[plant_id]
        rate = float(base["shift_rate_tph"])
        line_id = base["line_id"]
        for day in _daterange(start, end):
            season = _seasonal(day, phase=0.4)
            day_total = 0.0
            for shift in SHIFTS:
                rng = child_random(scenario.root_seed, scenario.scenario_id, plant_id,
                                    base["line_id"], f"prod-{day.isoformat()}-{shift}")
                planned_minutes = 480.0
                availability = 0.94 + 0.05 * rng.random()
                runtime_minutes = round(planned_minutes * availability, 1)
                performance = 0.95 + 0.05 * rng.random() + 0.01 * season
                ideal_rate_tph = round(rate, 2)
                total_tons = round(ideal_rate_tph * (runtime_minutes / 60.0) * performance, 2)
                good_fraction = 0.96 + 0.03 * rng.random()
                good_tons = round(total_tons * good_fraction, 2)
                total_orders = 6 + int(rng.random() * 5)
                on_time_orders = max(0, total_orders - (1 if rng.random() < 0.2 else 0))
                shift_start = datetime(day.year, day.month, day.day, SHIFT_START_HOUR[shift],
                                       tzinfo=timezone.utc)
                shift_id = f"{plant_id}:{shift_start.strftime('%Y%m%dT%H%M%SZ')}:{line_id}"
                rows.append({
                    "shift_id": shift_id,
                    "shift_date": day.isoformat(),
                    "plant_id": plant_id,
                    "line_id": line_id,
                    "planned_minutes": planned_minutes,
                    "runtime_minutes": runtime_minutes,
                    "ideal_rate_tph": ideal_rate_tph,
                    "total_tons": total_tons,
                    "good_tons": good_tons,
                    "crude_steel_tons": total_tons,
                    "on_time_orders": on_time_orders,
                    "total_orders": total_orders,
                    "calculation_version": calc_version,
                })
                day_total += total_tons
            daily_tons[(plant_id, day)] = round(day_total, 2)
    return rows, daily_tons


def _generate_energy(scenario: AnalyticalScenario, start: date, end: date,
                     daily_tons: dict) -> list[dict]:
    rows: list[dict] = []
    calc_version = scenario.model_versions["energy"]
    rollout = scenario.rollout_date(scenario._fast)
    reduction = float(scenario.kpi_targets["energy_intensity_reduction"])
    for plant_id in scenario.plants:
        base = scenario.plant_baselines[plant_id]
        sec0 = float(base["sec0_gj_per_t"])
        electric_fraction = float(base["electric_fraction"])
        for day in _daterange(start, end):
            tons = daily_tons[(plant_id, day)]
            rng = child_random(scenario.root_seed, scenario.scenario_id, plant_id, "energy",
                                day.isoformat())
            season = _seasonal(day, phase=1.1)
            # Seasonality lives in throughput/price, not in specific energy: SEC is
            # a relatively stable ratio, so the before/after reduction computed from
            # rows is not biased by the length of the comparison window.
            noise = 1.0 + 0.008 * (rng.random() - 0.5) * 2.0
            factor = _improvement_factor(day, rollout, reduction)
            intensity_gj_per_t = sec0 * factor * noise
            energy_gj = round(intensity_gj_per_t * tons, 2)
            baseline_energy_gj = round((sec0 * noise) * tons, 2)
            electricity_mwh = round(energy_gj * electric_fraction / 3.6, 2)
            spot_price = 68.0 + 22.0 * season + 8.0 * (rng.random() - 0.5)
            fuel_cost = energy_gj * (1.0 - electric_fraction) / 3.6 * 24.0
            energy_cost_eur = round(electricity_mwh * spot_price + fuel_cost, 2)
            baseline_cost_eur = round(
                (baseline_energy_gj * electric_fraction / 3.6) * spot_price
                + baseline_energy_gj * (1.0 - electric_fraction) / 3.6 * 24.0, 2)
            rows.append({
                "date_key": day.isoformat(),
                "plant_id": plant_id,
                "energy_gj": energy_gj,
                "electricity_mwh": electricity_mwh,
                "energy_cost_eur": energy_cost_eur,
                "baseline_energy_gj": baseline_energy_gj,
                "baseline_cost_eur": baseline_cost_eur,
                "crude_steel_tons": tons,
                "calculation_version": calc_version,
            })
    return rows


def _generate_emissions(scenario: AnalyticalScenario, start: date, end: date,
                        daily_tons: dict) -> list[dict]:
    rows: list[dict] = []
    calc_version = scenario.model_versions["emissions"]
    rollout = scenario.rollout_date(scenario._fast)
    reduction = float(scenario.kpi_targets["co2_intensity_reduction"])
    for plant_id in scenario.plants:
        base = scenario.plant_baselines[plant_id]
        co2_0 = float(base["co2_0_t_per_t"])
        scope1_fraction = float(base["scope1_fraction"])
        for day in _daterange(start, end):
            tons = daily_tons[(plant_id, day)]
            rng = child_random(scenario.root_seed, scenario.scenario_id, plant_id, "emissions",
                                day.isoformat())
            noise = 1.0 + 0.008 * (rng.random() - 0.5) * 2.0
            factor = _improvement_factor(day, rollout, reduction)
            specific_co2 = co2_0 * factor * noise
            total_co2e_t = round(specific_co2 * tons, 3)
            scope1 = round(total_co2e_t * scope1_fraction, 3)
            scope2 = round(total_co2e_t - scope1, 3)
            baseline_co2e_t = round((co2_0 * noise) * tons, 3)
            free_allocation_t = round(tons * FREE_ALLOCATION_T_PER_T, 3)
            ets_exposure = round(max(total_co2e_t - free_allocation_t, 0.0)
                                 * ETS_ALLOWANCE_PRICE_EUR_PER_T, 2)
            rows.append({
                "date_key": day.isoformat(),
                "plant_id": plant_id,
                "scope1_co2e_t": scope1,
                "scope2_co2e_t": scope2,
                "total_co2e_t": total_co2e_t,
                "baseline_co2e_t": baseline_co2e_t,
                "crude_steel_tons": tons,
                "free_allocation_t": free_allocation_t,
                "ets_allowance_price_eur_per_t": ETS_ALLOWANCE_PRICE_EUR_PER_T,
                "ets_exposure_eur": ets_exposure,
                "calculation_version": calc_version,
            })
    return rows


def _generate_quality(scenario: AnalyticalScenario, start: date, end: date,
                      daily_tons: dict) -> list[dict]:
    rows: list[dict] = []
    calc_version = scenario.model_versions["quality"]
    rollout = scenario.rollout_date(scenario._fast)
    qy = scenario.quality_yield
    fpy_before = float(qy["high_grade_fpy_before"])
    fpy_after = float(qy["high_grade_fpy_after"])
    fpy_low = float(qy["low_grade_fpy"])
    for plant_id in scenario.plants:
        for grade in scenario.grades:
            grade_code = grade["grade_code"]
            high = bool(grade["high_grade"])
            alloc = float(grade["allocation"])
            for day in _daterange(start, end):
                tons = daily_tons[(plant_id, day)]
                attempted = round(tons * alloc, 2)
                rng = child_random(scenario.root_seed, scenario.scenario_id, plant_id, grade_code,
                                    day.isoformat())
                if high:
                    base_fpy = fpy_after if day >= rollout else fpy_before
                else:
                    base_fpy = fpy_low
                fpy = base_fpy + 0.01 * (rng.random() - 0.5) * 2.0
                fpy = min(max(fpy, 0.0), 1.0)
                first_pass_good = round(attempted * fpy, 2)
                remainder = max(attempted - first_pass_good, 0.0)
                rework = round(remainder * 0.6, 2)
                downgrade = round(remainder * 0.3, 2)
                scrap = round(remainder - rework - downgrade, 2)
                defect_count = int(round(remainder / max(attempted, 1e-9) * 40))
                produced_units = 20 + int(rng.random() * 20)
                open_ncr = 1 if (not high and rng.random() < 0.05) or (high and day < rollout and rng.random() < 0.08) else 0
                rows.append({
                    "date_key": day.isoformat(),
                    "plant_id": plant_id,
                    "grade_code": grade_code,
                    "high_grade_flag": high,
                    "attempted_tons": attempted,
                    "first_pass_good_tons": first_pass_good,
                    "rework_tons": rework,
                    "downgrade_tons": downgrade,
                    "scrap_tons": scrap,
                    "defect_count": defect_count,
                    "produced_units": produced_units,
                    "open_ncr_count": open_ncr,
                    "calculation_version": calc_version,
                })
    return rows


def _generate_furnace_rul(scenario: AnalyticalScenario, start: date, end: date) -> list[dict]:
    """Daily RUL scoring for each furnace campaign.

    ``rul_days_p50`` is the integer number of days to the next scheduled
    reline. ``risk_score = clip(1 - p50/105, ...)`` so that ``risk >= 0.80``
    is reached *exactly* when ``p50 <= 21`` -- which makes the alert fire 21
    days before the predicted failure by construction, with no arithmetic
    contradiction (the cautionary "High = 7-20 days" band is deliberately
    avoided).
    """
    rows: list[dict] = []
    model_version = scenario.model_versions["furnace_rul"]
    for campaign in scenario.furnace_campaigns:
        asset_id = campaign["asset_id"]
        plant_id = campaign["plant_id"]
        component_id = campaign["component_id"]
        campaign_days = int(campaign["campaign_days"])
        demo_reline = date.fromisoformat(campaign["demonstration_reline_date"])
        # Anchor a chain of reline dates on the demonstration reline so the
        # whole window is covered; each reline is predicted 21 days out.
        relines: list[date] = []
        d = demo_reline
        while d >= start - timedelta(days=campaign_days):
            relines.append(d)
            d -= timedelta(days=campaign_days)
        d = demo_reline + timedelta(days=campaign_days)
        while d <= end + timedelta(days=campaign_days):
            relines.append(d)
            d += timedelta(days=campaign_days)
        relines.sort()
        for day in _daterange(start, end):
            next_reline = next((r for r in relines if r >= day), None)
            if next_reline is None:
                continue
            p50 = (next_reline - day).days
            if p50 < 1:
                # No forecast is issued on the reline day itself (remaining life
                # is zero); daily scoring covers every day strictly before it.
                continue
            rng = child_random(scenario.root_seed, scenario.scenario_id, plant_id, asset_id,
                                f"rul-{day.isoformat()}")
            risk = min(max(1.0 - p50 / 105.0, 0.02), 0.99)
            p10 = round(p50 * 0.80, 1)
            p90 = round(p50 * 1.31, 1)
            confidence = round(min(0.72 + (105 - min(p50, 105)) / 105.0 * 0.23, 0.97), 4)
            alert = p50 <= 21 and risk >= 0.80
            scored_at = _iso_ts(day, hour=6)
            inference_id = f"{asset_id}:{day.isoformat()}:{model_version}"
            top_factors = json.dumps([
                {"factor": "cooling_efficiency_loss", "contribution": round(0.4 + 0.1 * rng.random(), 3)},
                {"factor": "shell_temperature_trend", "contribution": round(0.3 + 0.1 * rng.random(), 3)},
            ], separators=(",", ":"))
            rows.append({
                "inference_id": inference_id,
                "scored_date": day.isoformat(),
                "scored_at": scored_at,
                "plant_id": plant_id,
                "asset_id": asset_id,
                "component_id": component_id,
                "rul_days_p10": p10,
                "rul_days_p50": float(p50),
                "rul_days_p90": p90,
                "risk_score": round(risk, 4),
                "confidence": confidence,
                "predicted_failure_date": next_reline.isoformat(),
                "alert_issued_at": scored_at if alert else None,
                "actual_reline_or_failure_at": _iso_ts(next_reline, hour=4) if alert else None,
                "unplanned_outage_flag": False,
                "model_version": model_version,
                "top_factors_json": top_factors,
                "scenario_id": scenario.scenario_id,
                "seed": scenario.root_seed,
            })
    return rows


def _generate_dispatch(scenario: AnalyticalScenario, start: date, end: date,
                       energy_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """One dispatch recommendation per plant-day plus its matching append-only
    audit record."""
    rows: list[dict] = []
    audit_rows: list[dict] = []
    model_version = scenario.model_versions["dispatch"]
    audit_version = scenario.model_versions["audit"]
    rollout = scenario.rollout_date(scenario._fast)
    disp = scenario.dispatch
    energy_by_key = {(r["plant_id"], r["date_key"]): r for r in energy_rows}
    for plant_id in scenario.plants:
        for day in _daterange(start, end):
            energy_row = energy_by_key[(plant_id, day.isoformat())]
            rng = child_random(scenario.root_seed, scenario.scenario_id, plant_id, "dispatch",
                                day.isoformat())
            after = day >= rollout
            saving = (disp["saving_after"] if after else disp["saving_before"]) * (0.9 + 0.2 * rng.random())
            baseline_cost = round(energy_row["energy_cost_eur"], 2)
            optimized_cost = round(baseline_cost * (1.0 - saving), 2)
            as_run_cost = round(optimized_cost + baseline_cost * 0.002 * rng.random(), 2)
            expected_avoid = round(baseline_cost - optimized_cost, 2)
            realized_avoid = round(baseline_cost - as_run_cost, 2)
            adoption = disp["adoption_after"] if after else disp["adoption_before"]
            status = "ACCEPTED" if rng.random() < adoption else "ISSUED"
            expected_co2 = round(expected_avoid / 65.0 * 0.35, 3)
            shiftable_mw = round(4.0 + 6.0 * rng.random(), 2)
            issued_at = _iso_ts(day, hour=5, minute=30)
            recommendation_id = f"{plant_id}:{day.isoformat()}:dispatch"
            correlation_id = f"corr-dispatch-{plant_id}-{day.isoformat()}"
            rows.append({
                "recommendation_id": recommendation_id,
                "recommendation_date": day.isoformat(),
                "issued_at": issued_at,
                "plant_id": plant_id,
                "status": status,
                "baseline_cost_eur": baseline_cost,
                "optimized_cost_eur": optimized_cost,
                "as_run_cost_eur": as_run_cost,
                "expected_cost_avoidance_eur": expected_avoid,
                "realized_cost_avoidance_eur": realized_avoid,
                "expected_co2_avoided_t": expected_co2,
                "shiftable_mw": shiftable_mw,
                "hard_constraint_violations": 0,
                "model_version": model_version,
                "correlation_id": correlation_id,
            })
            decided = status == "ACCEPTED"
            audit_rows.append({
                "audit_id": f"aud-dispatch-{plant_id}-{day.isoformat()}",
                "recorded_date": day.isoformat(),
                "recorded_at": issued_at,
                "domain": "energy",
                "entity_id": recommendation_id,
                "recommendation_status": status,
                "input_snapshot_ref": f"snap://energy/{plant_id}/{day.isoformat()}",
                "model_version": model_version,
                "confidence": round(0.8 + 0.15 * rng.random(), 4),
                "human_decision_at": _iso_ts(day, hour=7) if decided else None,
                "outcome_recorded_at": _iso_ts(day, hour=23) if decided else None,
                "complete_audit_flag": True,
                "correlation_id": correlation_id,
                "projection_version": audit_version,
            })
    return rows, audit_rows


def _furnace_audit_rows(scenario: AnalyticalScenario, furnace_rows: list[dict]) -> list[dict]:
    """Append-only audit evidence for each furnace-lining alert."""
    audit_version = scenario.model_versions["audit"]
    rows: list[dict] = []
    for r in furnace_rows:
        if not r["alert_issued_at"]:
            continue
        plant_id = r["plant_id"]
        asset_id = r["asset_id"]
        scored_date = r["scored_date"]
        rng = child_random(scenario.root_seed, scenario.scenario_id, plant_id, asset_id,
                            f"audit-{scored_date}")
        operator = f"OP-DEMO-{(int(rng.random() * 40) + 1):03d}"
        rows.append({
            "audit_id": f"aud-furnace-{asset_id}-{scored_date}",
            "recorded_date": scored_date,
            "recorded_at": r["alert_issued_at"],
            "domain": "maintenance",
            "entity_id": r["inference_id"],
            "recommendation_status": "ACCEPTED",
            "input_snapshot_ref": f"snap://furnace/{asset_id}/{scored_date}",
            "model_version": r["model_version"],
            "confidence": r["confidence"],
            "human_decision_at": _iso_ts(date.fromisoformat(scored_date), hour=8),
            "outcome_recorded_at": r["actual_reline_or_failure_at"],
            "complete_audit_flag": True,
            "correlation_id": f"corr-furnace-{asset_id}-{scored_date}-{operator}",
            "projection_version": audit_version,
        })
    return rows


def _generate_knowledge(scenario: AnalyticalScenario, start: date, end: date) -> list[dict]:
    """A small, immutable set of approved operator procedures with versions
    published across the programme."""
    templates = [
        ("PROC-LINING-INSPECT", "topic-furnace-lining", "LUX-BF-01", 3),
        ("PROC-ENERGY-DISPATCH", "topic-energy-dispatch", "LUX-UTIL-01", 2),
        ("PROC-QUALITY-COILING", "topic-quality-coiling", "LUX-HSM-01", 3),
        ("PROC-EAF-FLEX", "topic-eaf-flex", "BE-EAF-01", 2),
    ]
    rows: list[dict] = []
    span_days = (end - start).days
    for procedure_id, topic_id, equipment_id, versions in templates:
        for version in range(1, versions + 1):
            published = start + timedelta(days=int(span_days * version / (versions + 1)))
            rows.append({
                "procedure_id": procedure_id,
                "version": version,
                "topic_id": topic_id,
                "equipment_id": equipment_id,
                "review_status": "APPROVED",
                "approved_flag": True,
                "published_date": published.isoformat(),
                "source_citation_count": 3 + version,
                "content_hash": _content_hash(procedure_id, version, topic_id, equipment_id),
            })
    return rows


# --------------------------------------------------------------------------- #
# KPI measurement (computed from the emitted rows)                             #
# --------------------------------------------------------------------------- #

def _measure_kpis(scenario: AnalyticalScenario, energy_rows, emissions_rows, quality_rows,
                  furnace_rows, dispatch_rows) -> dict:
    rollout = scenario.rollout_date(scenario._fast).isoformat()

    def _intensity(rows, num_field):
        before_num = before_den = after_num = after_den = 0.0
        for r in rows:
            if r["date_key"] < rollout:
                before_num += r[num_field]
                before_den += r["crude_steel_tons"]
            else:
                after_num += r[num_field]
                after_den += r["crude_steel_tons"]
        before = before_num / before_den if before_den else 0.0
        after = after_num / after_den if after_den else 0.0
        reduction = 1.0 - after / before if before else 0.0
        return before, after, reduction

    e_before, e_after, e_reduction = _intensity(energy_rows, "energy_gj")
    c_before, c_after, c_reduction = _intensity(emissions_rows, "total_co2e_t")

    hg_before_num = hg_before_den = hg_after_num = hg_after_den = 0.0
    for r in quality_rows:
        if not r["high_grade_flag"]:
            continue
        if r["date_key"] < rollout:
            hg_before_num += r["first_pass_good_tons"]
            hg_before_den += r["attempted_tons"]
        else:
            hg_after_num += r["first_pass_good_tons"]
            hg_after_den += r["attempted_tons"]
    hg_before = hg_before_num / hg_before_den if hg_before_den else 0.0
    hg_after = hg_after_num / hg_after_den if hg_after_den else 0.0

    # Advance warning: first alert row of the primary furnace campaign.
    primary = next(c for c in scenario.furnace_campaigns if c.get("primary"))
    warning_days = None
    warn_scored = warn_predicted = None
    for r in sorted(furnace_rows, key=lambda x: (x["asset_id"], x["scored_date"])):
        if r["asset_id"] != primary["asset_id"] or not r["alert_issued_at"]:
            continue
        scored = date.fromisoformat(r["scored_date"])
        predicted = date.fromisoformat(r["predicted_failure_date"])
        warning_days = (predicted - scored).days
        warn_scored = r["scored_date"]
        warn_predicted = r["predicted_failure_date"]
        break

    after_disp = [r for r in dispatch_rows if r["recommendation_date"] >= rollout]
    dispatch_adoption_after = (
        sum(1 for r in after_disp if r["status"] == "ACCEPTED") / len(after_disp)
        if after_disp else 0.0)

    return {
        "rollout_date": rollout,
        "energy_intensity_before_gj_per_t": round(e_before, 4),
        "energy_intensity_after_gj_per_t": round(e_after, 4),
        "energy_intensity_reduction": round(e_reduction, 4),
        "co2_intensity_before_t_per_t": round(c_before, 4),
        "co2_intensity_after_t_per_t": round(c_after, 4),
        "co2_intensity_reduction": round(c_reduction, 4),
        "high_grade_fpy_before": round(hg_before, 4),
        "high_grade_fpy_after": round(hg_after, 4),
        "high_grade_yield_gain_pp": round(hg_after - hg_before, 4),
        "lining_warning_days": warning_days,
        "lining_warning_scored_date": warn_scored,
        "lining_warning_predicted_failure_date": warn_predicted,
        "lining_primary_asset_id": primary["asset_id"],
        "dispatch_adoption_after": round(dispatch_adoption_after, 4),
    }


# --------------------------------------------------------------------------- #
# CSV writing (deterministic, LF line endings, all-string, loader-friendly)   #
# --------------------------------------------------------------------------- #

def _fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        text = repr(round(value, 6))
        return text
    return str(value)


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8", newline="\n")
        return
    fieldnames = list(rows[0].keys())
    lines = [",".join(fieldnames)]
    for row in rows:
        cells = []
        for name in fieldnames:
            cell = _fmt(row.get(name))
            if any(ch in cell for ch in (",", '"', "\n")):
                cell = '"' + cell.replace('"', '""') + '"'
            cells.append(cell)
        lines.append(",".join(cells))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _write_parquet(path: Path, rows: list[dict]) -> bool:
    """Best-effort Parquet output (Fabric-idiomatic). Returns False if the
    optional ``pyarrow`` dependency is unavailable; CSV remains the canonical,
    checksummed format so determinism never depends on Parquet."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except Exception:
        return False
    if not rows:
        return False
    columns = {name: [row.get(name) for row in rows] for name in rows[0].keys()}
    table = pa.table(columns)
    pq.write_table(table, str(path))
    return True


# --------------------------------------------------------------------------- #
# Orchestration                                                               #
# --------------------------------------------------------------------------- #

def generate_analytical_run(scenario: AnalyticalScenario, *, out_dir: Path, fast: bool = False,
                            fmt: str = "csv", parquet: bool = False) -> AnalyticalRunResult:
    scenario.validate()
    scenario._fast = fast  # window selector threaded through the fact generators
    start = scenario.start_date(fast)
    end = scenario.end_date

    production_rows, daily_tons = _generate_production(scenario, start, end)
    energy_rows = _generate_energy(scenario, start, end, daily_tons)
    emissions_rows = _generate_emissions(scenario, start, end, daily_tons)
    quality_rows = _generate_quality(scenario, start, end, daily_tons)
    furnace_rows = _generate_furnace_rul(scenario, start, end)
    dispatch_rows, dispatch_audit = _generate_dispatch(scenario, start, end, energy_rows)
    furnace_audit = _furnace_audit_rows(scenario, furnace_rows)
    knowledge_rows = _generate_knowledge(scenario, start, end)
    audit_rows = sorted(dispatch_audit + furnace_audit, key=lambda r: r["audit_id"])

    datasets = {
        "fact_production_shift": production_rows,
        "fact_energy_daily": energy_rows,
        "fact_emissions_daily": emissions_rows,
        "fact_quality_yield": quality_rows,
        "fact_furnace_rul": furnace_rows,
        "fact_dispatch_recommendation": dispatch_rows,
        "fact_knowledge_procedure": knowledge_rows,
        "fact_ai_decision_audit": audit_rows,
    }

    measured = _measure_kpis(scenario, energy_rows, emissions_rows, quality_rows,
                             furnace_rows, dispatch_rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    file_paths: dict[str, Path] = {}
    for name in GOLD_TABLES:
        csv_path = out_dir / f"{name}.csv"
        _write_csv(csv_path, datasets[name])
        file_paths[name] = csv_path
        if parquet:
            _write_parquet(out_dir / f"{name}.parquet", datasets[name])

    summary = {
        "scenario_id": scenario.scenario_id,
        "root_seed": scenario.root_seed,
        "fast": fast,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "kpi_targets": scenario.kpi_targets,
        "kpi_tolerances": scenario.kpi_tolerances,
        "measured_kpis": measured,
    }

    run_manifest = {
        "scenario_id": scenario.scenario_id,
        "kind": "analytical-gold",
        "root_seed": scenario.root_seed,
        "seed": scenario.root_seed,
        "generator_version": GENERATOR_VERSION,
        "child_seed_derivation_version": 1,
        "config_checksum": config_checksum(scenario.raw),
        "fast": fast,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "rollout_date": scenario.rollout_date(fast).isoformat(),
        "data_classification": config.DATA_CLASSIFICATION,
        "privacy_label": config.PRIVACY_LABEL,
        "idempotency_keys": IDEMPOTENCY_KEYS,
        "row_counts": {name: len(datasets[name]) for name in GOLD_TABLES},
        "measured_kpis": measured,
        "summary": summary,
    }
    run_manifest_path = out_dir / "manifest.json"
    with run_manifest_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(run_manifest, indent=2, sort_keys=True))

    filenames = [p.name for p in file_paths.values()] + ["manifest.json"]
    write_checksums(out_dir, filenames)
    checksums = json.loads((out_dir / "checksums.json").read_text(encoding="utf-8"))

    return AnalyticalRunResult(scenario=scenario, out_dir=out_dir, fast=fast, fmt=fmt,
                               datasets=datasets, measured_kpis=measured, summary=summary,
                               file_paths=file_paths, run_manifest_path=run_manifest_path,
                               checksums=checksums)
