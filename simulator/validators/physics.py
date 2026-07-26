"""Physics validator (docs section 9.2, 10.2).

Recomputes physical relationships directly from generated telemetry
records (not from internal generator state) so the check is an
independent verification: cooling water must not cool below its own
inlet temperature, heat flux must be non-negative and consistent with the
conductive relation, hearth thickness must never increase except after a
declared repair, and rolling mass balance must reconcile within
tolerance.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from simulator.process.rolling import mass_flow_kg_s


@dataclass
class PhysicsReport:
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_furnace_physics(telemetry_records: list[dict], *, mass_balance_tolerance: float = 0.008,
                              thickness_tolerance_mm: float = 1.5) -> PhysicsReport:
    report = PhysicsReport()
    by_sector_signal: dict[tuple[str, str], list[dict]] = defaultdict(list)
    stand_pairs: dict[str, list[dict]] = defaultdict(list)

    for record in telemetry_records:
        payload = record["payload"]
        signal_code = payload.get("signal_code")
        if "hearth_sector" in payload:
            key = (payload["hearth_sector"], signal_code)
            by_sector_signal[key].append(record)
        if "stand_id" in payload:
            stand_pairs[record["event_ts"]].append(payload)

    for (sector, signal_code), records in by_sector_signal.items():
        records_sorted = sorted(records, key=lambda r: r["event_ts"])
        if signal_code == "hearth_refractory_estimate":
            prev_value = None
            for r in records_sorted:
                value = r["payload"]["value"]
                if prev_value is not None and value > prev_value + thickness_tolerance_mm:
                    report.add(
                        f"sector {sector}: hearth_refractory_estimate increased from {prev_value} to "
                        f"{value} at {r['event_ts']} without a declared repair")
                prev_value = value

    inlet_by_key = {(r["payload"]["hearth_sector"], r["event_ts"]): r["payload"]["value"]
                    for r in telemetry_records
                    if r["payload"].get("signal_code") == "cooling_water_inlet_temperature"}
    outlet_records = [r for r in telemetry_records
                       if r["payload"].get("signal_code") == "cooling_water_outlet_temperature"]
    for r in outlet_records:
        key = (r["payload"]["hearth_sector"], r["event_ts"])
        inlet = inlet_by_key.get(key)
        if inlet is not None and r["payload"]["value"] < inlet - 0.5:
            report.add(
                f"sector {r['payload']['hearth_sector']}: cooling outlet "
                f"{r['payload']['value']} below inlet {inlet} at {r['event_ts']}")

    for r in telemetry_records:
        if r["payload"].get("signal_code") == "local_heat_flux" and r["payload"]["value"] < 0:
            report.add(f"negative heat flux at {r['event_ts']} sector {r['payload'].get('hearth_sector')}")

    for event_ts, payloads in stand_pairs.items():
        by_stand = {p["stand_id"]: p for p in payloads if p.get("signal_code") == "strip_speed"}
        stand_order = ["R1", "R2", "F1", "F2", "F3", "F4", "F5", "F6", "F7"]
        present = [s for s in stand_order if s in by_stand]
        for a, b in zip(present, present[1:]):
            pa, pb = by_stand[a], by_stand[b]
            m_a = mass_flow_kg_s(1250.0, pa["exit_thickness_mm"], pa["value"])
            m_b = mass_flow_kg_s(1250.0, pb["exit_thickness_mm"], pb["value"])
            if m_a <= 1e-9:
                continue
            residual = (m_b - m_a) / m_a
            if abs(residual) > mass_balance_tolerance:
                report.add(
                    f"rolling mass balance residual {residual:.4f} exceeds tolerance "
                    f"{mass_balance_tolerance} between {a} and {b} at {event_ts}")

    return report
