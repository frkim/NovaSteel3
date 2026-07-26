"""Truth ledger (docs section 6.2, 9.1).

Records the *hidden* simulator state and ground-truth labels that models
are trained/evaluated against, independent of anything a model might have
predicted. Labels must never leak from model output back into training
data (docs section 9.1).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TruthRecord:
    record_ts: str
    plant_id: str
    asset_id: str
    component_id: str
    lining_state: str
    rul_days: float
    failure_within_21d: int
    sensor_fault_type: str
    quality_outcome: str
    quality_drift_active: bool
    energy_schedule_optimality_gap: float
    anomaly_id: str | None

    def to_dict(self) -> dict:
        return {
            "record_ts": self.record_ts,
            "plant_id": self.plant_id,
            "asset_id": self.asset_id,
            "component_id": self.component_id,
            "lining_state": self.lining_state,
            "rul_days": self.rul_days,
            "failure_within_21d": self.failure_within_21d,
            "sensor_fault_type": self.sensor_fault_type,
            "quality_outcome": self.quality_outcome,
            "quality_drift_active": self.quality_drift_active,
            "energy_schedule_optimality_gap": self.energy_schedule_optimality_gap,
            "anomaly_id": self.anomaly_id,
        }


def lining_state_for_rul(rul_days: float) -> str:
    if rul_days <= 21:
        return "critical" if rul_days <= 7 else "degraded"
    if rul_days <= 45:
        return "watch"
    return "healthy"


class TruthLedger:
    def __init__(self) -> None:
        self.records: list[TruthRecord] = []

    def add(self, record: TruthRecord) -> None:
        self.records.append(record)

    def as_dicts(self) -> list[dict]:
        return [r.to_dict() for r in self.records]
