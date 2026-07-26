"""Scenario acceptance-threshold validator (docs section 10.3).

Checks the specific, named assertions the specification requires for each
demo scenario seed:

- seed 240726 (``lining-degradation-21d``): 21-day P50 warning for
  ``HEARTH-SECTOR-07`` with P10 < P50 < P90 and risk >= 0.80.
- seed 240727 (``energy-price-spike``): optimized schedule costs less than
  baseline with equal planned tonnage and zero hard-constraint violations.
- seed 240728 (``quality-drift``): the quality warning precedes the first
  off-spec result and the recommended correction improves predicted
  first-pass yield.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AssertionReport:
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False


def validate_lining_assertions(summary: dict, expected: dict) -> AssertionReport:
    report = AssertionReport()
    p50 = summary.get("lining_rul_p50_days")
    p10 = summary.get("lining_rul_p10_days")
    p90 = summary.get("lining_rul_p90_days")
    risk = summary.get("lining_risk_score")

    if p50 is None or p10 is None or p90 is None or risk is None:
        report.add("lining prediction summary is incomplete")
        return report

    lo = expected.get("rul_p50_days_min")
    hi = expected.get("rul_p50_days_max")
    if lo is not None and p50 < lo:
        report.add(f"RUL P50 {p50} below minimum expected {lo}")
    if hi is not None and p50 > hi:
        report.add(f"RUL P50 {p50} above maximum expected {hi}")
    if not (p10 < p50 < p90):
        report.add(f"confidence band ordering violated: p10={p10} p50={p50} p90={p90}")
    risk_min = expected.get("risk_score_min")
    if risk_min is not None and risk < risk_min:
        report.add(f"risk_score {risk} below minimum expected {risk_min}")
    expected_component = expected.get("component_id")
    if expected_component and summary.get("lining_component_id") != expected_component:
        report.add(f"component_id {summary.get('lining_component_id')} != expected {expected_component}")
    return report


def validate_energy_assertions(summary: dict, expected: dict) -> AssertionReport:
    report = AssertionReport()
    baseline_cost = summary.get("energy_baseline_cost_eur")
    optimized_cost = summary.get("energy_optimized_cost_eur")
    if baseline_cost is None or optimized_cost is None:
        report.add("energy cost summary is incomplete")
        return report

    if expected.get("optimized_cost_lower_than_baseline") and not (optimized_cost < baseline_cost):
        report.add(f"optimized cost {optimized_cost} is not lower than baseline {baseline_cost}")
    if expected.get("tonnage_equal"):
        before = summary.get("energy_tonnage_before")
        after = summary.get("energy_tonnage_after")
        if before != after:
            report.add(f"planned tonnage changed: before={before} after={after}")
    max_violations = expected.get("max_hard_constraint_violations")
    if max_violations is not None:
        violations = summary.get("energy_hard_constraint_violations", 0)
        if violations > max_violations:
            report.add(f"hard constraint violations {violations} exceed max {max_violations}")
    return report


def validate_quality_assertions(summary: dict, expected: dict) -> AssertionReport:
    report = AssertionReport()
    warning_ts = summary.get("quality_warning_ts")
    off_spec_ts = summary.get("quality_first_off_spec_ts")

    if expected.get("warning_before_first_off_spec"):
        if warning_ts is None:
            report.add("no quality warning timestamp recorded")
        elif off_spec_ts is not None and warning_ts >= off_spec_ts:
            report.add(f"quality warning {warning_ts} does not precede first off-spec {off_spec_ts}")

    yield_before = summary.get("quality_predicted_yield_before")
    yield_after = summary.get("quality_predicted_yield_after")
    max_before = expected.get("predicted_yield_before_max")
    min_after = expected.get("predicted_yield_after_min")
    if max_before is not None and yield_before is not None and yield_before > max_before:
        report.add(f"predicted yield before correction {yield_before} exceeds max {max_before}")
    if min_after is not None and yield_after is not None and yield_after < min_after:
        report.add(f"predicted yield after correction {yield_after} below min {min_after}")
    if yield_before is not None and yield_after is not None and yield_after <= yield_before:
        report.add(f"correction did not improve predicted yield: before={yield_before} after={yield_after}")
    return report


def validate_scenario(summary: dict, expected: dict) -> AssertionReport:
    """Run whichever scenario-specific assertions apply based on the keys
    present in ``expected`` (a manifest's ``expected_assertions``)."""
    report = AssertionReport()
    for sub_report in [
        validate_lining_assertions(summary, expected) if "rul_p50_days_min" in expected else None,
        validate_energy_assertions(summary, expected) if "optimized_cost_lower_than_baseline" in expected else None,
        validate_quality_assertions(summary, expected) if "warning_before_first_off_spec" in expected else None,
    ]:
        if sub_report is None:
            continue
        if not sub_report.ok:
            report.ok = False
            report.errors.extend(sub_report.errors)
    return report
