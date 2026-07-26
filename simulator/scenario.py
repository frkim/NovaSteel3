"""Scenario manifest loading/validation ("scenario compiler", docs 6.2 step 1).

Manifests are plain JSON (stdlib ``json``) rather than YAML, to avoid a
non-stdlib dependency; the schema matches the structure described in
``docs/data/synthetic-data-and-simulators.md`` sections 6 and 8.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_DIR = Path(__file__).parent / "manifests"

REQUIRED_FIELDS = [
    "scenario_id", "root_seed", "plant_id", "primary_asset_id", "start_time",
    "window_hours", "sample_interval_seconds", "campaign", "energy", "quality", "anomalies",
]


class ManifestError(ValueError):
    pass


@dataclass
class ScenarioManifest:
    raw: dict

    @property
    def scenario_id(self) -> str:
        return self.raw["scenario_id"]

    @property
    def root_seed(self) -> int:
        return int(self.raw["root_seed"])

    @property
    def plant_id(self) -> str:
        return self.raw["plant_id"]

    @property
    def primary_asset_id(self) -> str:
        return self.raw["primary_asset_id"]

    @property
    def start_time(self) -> datetime:
        raw = self.raw["start_time"].replace("Z", "+00:00")
        return datetime.fromisoformat(raw).astimezone(timezone.utc)

    def window_hours(self, fast: bool) -> float:
        if fast and "fast_window_hours" in self.raw:
            return float(self.raw["fast_window_hours"])
        return float(self.raw["window_hours"])

    def sample_interval_seconds(self, fast: bool) -> int:
        if fast and "fast_sample_interval_seconds" in self.raw:
            return int(self.raw["fast_sample_interval_seconds"])
        return int(self.raw["sample_interval_seconds"])

    @property
    def hearth_sectors(self) -> list[str]:
        return self.raw.get("hearth_sectors", ["07"])

    @property
    def campaign(self) -> dict:
        return self.raw["campaign"]

    @property
    def energy(self) -> dict:
        return self.raw["energy"]

    @property
    def quality(self) -> dict:
        return self.raw["quality"]

    @property
    def edge(self) -> dict:
        return self.raw.get("edge", {})

    @property
    def anomalies(self) -> list[dict]:
        return self.raw.get("anomalies", [])

    @property
    def expected_assertions(self) -> dict:
        return self.raw.get("expected_assertions", {})

    def quality_latent_hours(self, fast: bool) -> float:
        key = "fast_latent_hours" if fast and "fast_latent_hours" in self.quality else "latent_hours"
        return float(self.quality.get(key, 12.0))

    def quality_full_drift_hours(self, fast: bool) -> float:
        key = "fast_full_drift_hours" if fast and "fast_full_drift_hours" in self.quality else "full_drift_hours"
        return float(self.quality.get(key, 36.0))

    def thickness_at_eval_mm(self, sector: str) -> float:
        table = self.campaign["thickness_at_eval_mm"]
        return float(table.get(sector, table["default"]))

    def degradation_rate(self, sector: str) -> float:
        table = self.campaign["degradation_rate_mm_per_day"]
        return float(table.get(sector, table["default"]))

    def validate(self) -> None:
        missing = [f for f in REQUIRED_FIELDS if f not in self.raw]
        if missing:
            raise ManifestError(f"scenario manifest missing required fields: {missing}")
        if self.raw["window_hours"] <= 0:
            raise ManifestError("window_hours must be > 0")
        if self.raw["sample_interval_seconds"] <= 0:
            raise ManifestError("sample_interval_seconds must be > 0")
        for anomaly in self.anomalies:
            for req in ("anomaly_id", "type", "start_hours", "end_hours"):
                if req not in anomaly:
                    raise ManifestError(f"anomaly missing required field {req!r}: {anomaly}")
            if anomaly["end_hours"] < anomaly["start_hours"]:
                raise ManifestError(f"anomaly end_hours before start_hours: {anomaly}")


def load_manifest(scenario_id_or_path: str) -> ScenarioManifest:
    candidate = Path(scenario_id_or_path)
    if candidate.suffix == ".json" and candidate.exists():
        path = candidate
    else:
        path = MANIFEST_DIR / f"{scenario_id_or_path}.json"
    if not path.exists():
        available = sorted(p.stem for p in MANIFEST_DIR.glob("*.json"))
        raise ManifestError(f"unknown scenario {scenario_id_or_path!r}; available: {available}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    manifest = ScenarioManifest(raw)
    manifest.validate()
    return manifest


def list_scenarios() -> list[str]:
    return sorted(p.stem for p in MANIFEST_DIR.glob("*.json"))
