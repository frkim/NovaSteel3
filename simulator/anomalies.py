"""Named, time-bounded anomaly injection (docs section 8, 8.4).

The anomaly controller resolves, for a given simulated timestamp, which
process- or sensor-layer anomalies from the scenario manifest are
currently active, and returns their parameters so the process/observation
models can apply them consistently. All active anomalies are also written
to the truth ledger with their exact interval, per the
``anomaly_id`` truth label (docs section 9.1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AnomalySpec:
    anomaly_id: str
    anomaly_type: str
    layer: str  # "process" | "sensor" | "transport" | "contract" | "business" | "edge"
    target: str  # asset_id, sensor_id, or signal_code depending on type
    start_hours: float
    end_hours: float
    params: dict = field(default_factory=dict)

    def active_at(self, elapsed_hours: float) -> bool:
        return self.start_hours <= elapsed_hours < self.end_hours


class AnomalyController:
    def __init__(self, specs: list[AnomalySpec]):
        self.specs = specs

    def active(self, elapsed_hours: float, target: str | None = None) -> list[AnomalySpec]:
        return [
            s for s in self.specs
            if s.active_at(elapsed_hours) and (target is None or s.target == target)
        ]

    def is_active(self, anomaly_type: str, elapsed_hours: float, target: str | None = None) -> bool:
        return any(
            s.anomaly_type == anomaly_type and s.active_at(elapsed_hours)
            and (target is None or s.target == target)
            for s in self.specs
        )

    @classmethod
    def from_manifest(cls, anomaly_dicts: list[dict]) -> "AnomalyController":
        specs = [
            AnomalySpec(
                anomaly_id=d["anomaly_id"],
                anomaly_type=d["type"],
                layer=d.get("layer", "process"),
                target=d.get("target", ""),
                start_hours=float(d.get("start_hours", 0.0)),
                end_hours=float(d.get("end_hours", 1e9)),
                params=d.get("params", {}),
            )
            for d in anomaly_dicts
        ]
        return cls(specs)
