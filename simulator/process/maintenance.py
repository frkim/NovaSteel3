"""Maintenance/reliability event generation (docs section 3.6)."""
from __future__ import annotations

from datetime import datetime, timedelta

from simulator import config


def build_maintenance_event(*, work_order_id: str, asset_id: str, failure_mode: str,
                             detected_ts: datetime, sector: str | None, rng) -> dict:
    ack_delay_min = rng.uniform(5, 25)
    plan_delay_min = ack_delay_min + rng.uniform(30, 180)
    start_delay_min = plan_delay_min + rng.uniform(60, 720)
    complete_delay_min = start_delay_min + rng.uniform(30, 240)

    template = rng.choice(config.MAINTENANCE_NOTE_TEMPLATES)
    note = template.format(sector=sector or "N/A", asset=asset_id)

    return {
        "work_order_id": work_order_id,
        "asset_id": asset_id,
        "component_id": f"HEARTH-SECTOR-{sector}" if sector else asset_id,
        "failure_mode": failure_mode,
        "detected_ts": _iso(detected_ts),
        "acknowledged_ts": _iso(detected_ts + timedelta(minutes=ack_delay_min)),
        "planned_ts": _iso(detected_ts + timedelta(minutes=plan_delay_min)),
        "started_ts": _iso(detected_ts + timedelta(minutes=start_delay_min)),
        "completed_ts": _iso(detected_ts + timedelta(minutes=complete_delay_min)),
        "labor_hours": round(rng.uniform(1.0, 8.0), 1),
        "downtime_minutes": round(complete_delay_min - start_delay_min, 1),
        "notes": note,
        "data_classification": config.DATA_CLASSIFICATION,
        "privacy_label": config.PRIVACY_LABEL,
    }


def _iso(dt: datetime) -> str:
    from simulator.clock import iso

    return iso(dt)
