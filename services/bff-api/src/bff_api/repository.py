"""Local file-backed query adapter for deterministic simulator datasets."""

from __future__ import annotations

import json
import hashlib
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .config import Settings


_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_FIXTURE = _ROOT / "services" / "bff-api" / "fixtures" / "demo-full"


@dataclass
class DemoRepository:
    """Normalizes simulator envelopes into the BFF's local read projections."""

    datasets: dict[str, list[dict[str, Any]]]
    manifest: dict[str, Any]
    source: str
    alerts: dict[str, dict[str, Any]] = field(default_factory=dict)
    workorders: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def load(cls, settings: Settings) -> "DemoRepository":
        candidates: list[Path] = []
        if settings.demo_data_directory:
            configured = Path(settings.demo_data_directory)
            candidates.append(
                configured if configured.is_absolute() else _ROOT / configured
            )
        candidates.append(_DEFAULT_FIXTURE)
        for candidate in candidates:
            if (candidate / "manifest.json").is_file():
                _verify_checksums(candidate)
                datasets = {
                    path.stem: _read_ndjson(path)
                    for path in candidate.glob("*.ndjson")
                }
                manifest = json.loads(
                    (candidate / "manifest.json").read_text(encoding="utf-8")
                )
                cls._ensure_local_safe(datasets)
                repository = cls(
                    datasets=datasets,
                    manifest=manifest,
                    source=f"simulator-fixture:{candidate.name}",
                )
                repository._hydrate_mutable_projections()
                return repository
        repository = cls(
            datasets=_fallback_datasets(),
            manifest=_fallback_manifest(),
            source="built-in-fallback",
        )
        repository._hydrate_mutable_projections()
        return repository

    @staticmethod
    def _ensure_local_safe(datasets: Mapping[str, Iterable[Mapping[str, Any]]]) -> None:
        for records in datasets.values():
            for record in records:
                if "data_classification" not in record:
                    continue
                if (
                    record.get("data_classification") != "SYNTHETIC"
                    or record.get("privacy_label") != "DEMO-NONPERSONAL"
                    or (
                        record.get("plant_id") is not None
                        and not str(record["plant_id"]).startswith("NS-DEMO-")
                    )
                ):
                    raise ValueError(
                        "Local demo data must be explicitly SYNTHETIC, DEMO-NONPERSONAL, "
                        "and in an NS-DEMO-* namespace."
                    )

    @property
    def site(self) -> str:
        return str(self.manifest.get("plant_id", "NS-DEMO-LUX-01"))

    @property
    def summary_metrics(self) -> dict[str, Any]:
        return dict(self.manifest.get("summary", {}))

    def telemetry_rows(self) -> list[dict[str, Any]]:
        rows = []
        for record in self.datasets.get("telemetry", []):
            payload = record.get("payload", {})
            rows.append(
                {
                    "eventId": record.get("event_id"),
                    "eventTs": record.get("event_ts"),
                    "site": record.get("plant_id"),
                    "assetId": record.get("asset_id"),
                    "sensorId": payload.get("sensor_id"),
                    "signalCode": payload.get("signal_code"),
                    "value": payload.get("value"),
                    "unit": payload.get("unit"),
                    "quality": payload.get("quality"),
                    "uncertainty": payload.get("uncertainty"),
                    "scenarioId": record.get("scenario_id"),
                    "sourceRef": f"event:{record.get('event_id')}",
                    "synthetic": True,
                }
            )
        return rows

    def raw_telemetry(self, asset_id: str) -> list[dict[str, Any]]:
        return [
            record
            for record in self.datasets.get("telemetry", [])
            if record.get("asset_id") == asset_id
        ]

    def energy_rows(self) -> list[dict[str, Any]]:
        rows = []
        for record in self.datasets.get("energy_interval", []):
            payload = record.get("payload", {})
            rows.append(
                {
                    "eventId": record.get("event_id"),
                    "eventTs": record.get("event_ts"),
                    "site": record.get("plant_id"),
                    "assetId": record.get("asset_id"),
                    "intervalStart": payload.get("interval_start"),
                    "intervalEnd": payload.get("interval_end"),
                    "priceEurMwh": payload.get("price"),
                    "demandMw": payload.get("demand"),
                    "baselineDemandMw": payload.get("baseline_demand_mw"),
                    "consumptionMwh": payload.get("consumption_mwh"),
                    "carbonIntensityKgCo2eMwh": payload.get(
                        "grid_carbon_intensity_kgco2e_per_mwh"
                    ),
                    "meterId": payload.get("meter_id"),
                    "scenario": payload.get("scenario"),
                    "sourceRef": f"event:{record.get('event_id')}",
                }
            )
        return rows

    def raw_energy(self, site: str) -> list[dict[str, Any]]:
        return [
            record
            for record in self.datasets.get("energy_interval", [])
            if record.get("plant_id") == site
        ]

    def raw_heat_batches(self, site: str) -> list[dict[str, Any]]:
        return [
            record
            for record in self.datasets.get("heat_batch", [])
            if record.get("plant_id") == site
        ]

    def quality_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for record in self.datasets.get("quality_measurement", []):
            payload = record.get("payload", {})
            batch_id = _public_batch_id(str(payload.get("material_id", "")))
            bias = float(payload.get("coiling_temperature_bias_c", 0.0))
            risk = min(0.95, round(0.11 + abs(bias) * 0.028, 3))
            rows.append(
                {
                    "batchId": batch_id,
                    "sourceBatchId": payload.get("material_id"),
                    "site": record.get("plant_id"),
                    "assetId": record.get("asset_id"),
                    "heatId": payload.get("heat_id"),
                    "grade": payload.get("grade_code"),
                    "sampleId": payload.get("sample_id"),
                    "characteristic": payload.get("characteristic_code"),
                    "value": payload.get("value"),
                    "unit": payload.get("unit"),
                    "lowerSpecLimit": payload.get("lower_spec_limit"),
                    "upperSpecLimit": payload.get("upper_spec_limit"),
                    "resultStatus": payload.get("result_status"),
                    "carbonEquivalent": payload.get("carbon_equivalent"),
                    "coilingTempBiasC": bias,
                    "riskScore": risk,
                    "eventTs": record.get("event_ts"),
                    "sourceRef": f"event:{record.get('event_id')}",
                }
            )
        return rows

    def quality_batch(self, batch_id: str) -> dict[str, Any] | None:
        return next(
            (row for row in self.quality_rows() if row["batchId"] == batch_id),
            None,
        )

    def genealogy(self, batch_id: str) -> dict[str, Any] | None:
        batch = self.quality_batch(batch_id)
        if batch is None:
            return None
        return {
            "batchId": batch["batchId"],
            "site": batch["site"],
            "chain": {
                "rawMaterialLots": [f"LOT-FE-{batch['heatId'][-4:]}"],
                "heat": batch["heatId"],
                "ladleTreatment": f"LADLE-{batch['heatId'][-4:]}",
                "slab": f"SLAB-{batch['heatId'][-4:]}",
                "reheating": {
                    "assetId": "LUX-RHF-01",
                    "operation": f"REHEAT-{batch['heatId'][-4:]}",
                },
                "coil": batch["batchId"],
                "sample": batch["sampleId"],
                "testResult": {
                    "characteristic": batch["characteristic"],
                    "value": batch["value"],
                    "unit": batch["unit"],
                    "resultStatus": batch["resultStatus"],
                },
                "shipment": f"SHIP-DEMO-{batch['batchId'][-3:]}",
            },
            "synthetic": True,
            "sourceRefs": [batch["sourceRef"]],
        }

    def furnaces(self) -> list[dict[str, Any]]:
        return [
            {
                "assetId": "LUX-BF-01",
                "site": self.site,
                "assetType": "BLAST_FURNACE",
                "componentId": "HEARTH-SECTOR-07",
                "health": "HIGH_RISK",
                "synthetic": True,
            },
            {
                "assetId": "LUX-RHF-01",
                "site": self.site,
                "assetType": "REHEAT_FURNACE",
                "componentId": "RHF-ZONE-03",
                "health": "WATCH",
                "synthetic": True,
            },
        ]

    def asset_site(self, asset_id: str) -> str | None:
        for asset in self.furnaces():
            if asset["assetId"] == asset_id:
                return str(asset["site"])
        for row in self.quality_rows():
            if row["assetId"] == asset_id:
                return str(row["site"])
        return None

    def lining_component(self, asset_id: str) -> str | None:
        if asset_id == "LUX-BF-01":
            return "HEARTH-SECTOR-07"
        return None

    def alerts_rows(self) -> list[dict[str, Any]]:
        return [deepcopy(row) for row in self.alerts.values()]

    def set_alert_workorder(self, asset_id: str, work_order_id: str) -> None:
        for alert in self.alerts.values():
            if alert["assetId"] == asset_id:
                alert["status"] = "WORK_ORDER_LINKED"
                alert["workOrderId"] = work_order_id
                alert["updatedAt"] = alert["createdAt"]

    def workorder(self, work_order_id: str) -> dict[str, Any] | None:
        record = self.workorders.get(work_order_id)
        return deepcopy(record) if record else None

    def create_workorder(
        self, *, asset_id: str, title: str, reason: str, actor: str
    ) -> dict[str, Any]:
        work_order_id = (
            "WO-DEMO-LUX-1042"
            if asset_id == "LUX-BF-01" and "WO-DEMO-LUX-1042" not in self.workorders
            else f"WO-DEMO-{asset_id.replace('-', '')}-{len(self.workorders) + 1000}"
        )
        record = {
            "workOrderId": work_order_id,
            "site": self.asset_site(asset_id) or self.site,
            "assetId": asset_id,
            "title": title,
            "reason": reason,
            "status": "PLANNED_INSPECTION",
            "synthetic": True,
            "createdBy": actor,
            "sourceRefs": ["alert:HEARTH-SECTOR-07"],
        }
        self.workorders[work_order_id] = record
        self.set_alert_workorder(asset_id, work_order_id)
        return deepcopy(record)

    def command_summary(self, site: str) -> dict[str, Any]:
        metrics = self.summary_metrics
        energy = self.energy_rows()
        quality = self.quality_rows()
        total_consumption = sum(float(row["consumptionMwh"] or 0) for row in energy)
        scope2 = sum(
            float(row["consumptionMwh"] or 0)
            * float(row["carbonIntensityKgCo2eMwh"] or 0)
            for row in energy
        )
        return {
            "site": site,
            "syntheticBanner": "Synthetic demo data — not for operational control",
            "freshness": {
                "energy": {"asOf": _latest(energy, "eventTs"), "stale": False},
                "furnace": {"asOf": _latest(self.telemetry_rows(), "eventTs"), "stale": False},
                "quality": {"asOf": _latest(quality, "eventTs"), "stale": False},
            },
            "kpis": {
                "plannedTonnage": metrics.get("energy_tonnage_before", 960.0),
                "energyConsumptionMwh": round(total_consumption, 2),
                "energyDispatchSavingsTargetPct": 10.4,
                "scope2KgCo2e": round(scope2, 2),
                "qualityPredictedFirstPassYieldPct": round(
                    float(metrics.get("quality_predicted_yield_before", 0.88)) * 100,
                    1,
                ),
                "liningRulDaysP50": metrics.get("lining_rul_p50_days", 21.0),
                "openAlerts": sum(
                    1 for alert in self.alerts.values() if alert["status"] != "CLOSED"
                ),
            },
            "scenario": {
                "id": self.manifest.get("scenario_id", "demo-full"),
                "seed": self.manifest.get("root_seed", 240725),
                "source": self.source,
            },
        }

    def sustainability_summary(self, site: str) -> dict[str, Any]:
        energy = self.energy_rows()
        total_mwh = sum(float(row["consumptionMwh"] or 0) for row in energy)
        scope2 = sum(
            float(row["consumptionMwh"] or 0)
            * float(row["carbonIntensityKgCo2eMwh"] or 0)
            for row in energy
        )
        tonnage = float(self.summary_metrics.get("energy_tonnage_before", 960.0))
        return {
            "site": site,
            "energyConsumptionMwh": round(total_mwh, 2),
            "scope1KgCo2e": round(tonnage * 1425, 2),
            "scope2KgCo2e": round(scope2, 2),
            "etsAllowancePriceEurTonne": 86.0,
            "modeledDispatchCo2ReductionPct": 8.7,
            "synthetic": True,
            "dataClassification": "SYNTHETIC",
        }

    def emissions_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "site": self.site,
                "eventTs": row["intervalStart"],
                "scope2KgCo2e": round(
                    float(row["consumptionMwh"] or 0)
                    * float(row["carbonIntensityKgCo2eMwh"] or 0),
                    2,
                ),
                "consumptionMwh": row["consumptionMwh"],
                "carbonIntensityKgCo2eMwh": row["carbonIntensityKgCo2eMwh"],
                "sourceRef": row["sourceRef"],
            }
            for row in self.energy_rows()
        ]

    def _hydrate_mutable_projections(self) -> None:
        for record in self.datasets.get("alarm_event", []):
            payload = record.get("payload", {})
            alert_id = str(payload.get("alert_id", record.get("event_id")))
            self.alerts[alert_id] = {
                "alertId": alert_id,
                "site": record.get("plant_id", self.site),
                "assetId": record.get("asset_id"),
                "componentId": payload.get("component_id"),
                "severity": payload.get("severity"),
                "status": payload.get("status"),
                "message": payload.get("message"),
                "confidence": payload.get("confidence"),
                "createdAt": record.get("event_ts"),
                "updatedAt": payload.get("transitioned_at", record.get("event_ts")),
                "sourceRef": f"event:{record.get('event_id')}",
                "correlationId": record.get("correlation_id"),
            }
        for record in self.datasets.get("maintenance_event", []):
            work_order_id = str(record.get("work_order_id"))
            self.workorders[work_order_id] = {
                "workOrderId": work_order_id,
                "site": self.site,
                "assetId": record.get("asset_id"),
                "title": f"Synthetic {record.get('failure_mode', 'inspection')}",
                "reason": record.get("notes"),
                "status": "COMPLETED" if record.get("completed_ts") else "PLANNED_INSPECTION",
                "synthetic": True,
                "createdBy": "SYSTEM",
                "detectedAt": record.get("detected_ts"),
            }


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _verify_checksums(directory: Path) -> None:
    """Reject a tampered generated/fallback pack before serving it locally."""
    checksum_path = directory / "checksums.json"
    if not checksum_path.is_file():
        raise ValueError(
            f"Generated local demo fixture '{directory}' is missing checksums.json."
        )
    declared = json.loads(checksum_path.read_text(encoding="utf-8"))
    for filename, expected in declared.items():
        path = directory / filename
        contents = path.read_bytes()
        if (
            len(contents) != expected.get("bytes")
            or hashlib.sha256(contents).hexdigest() != expected.get("sha256")
        ):
            raise ValueError(f"Checksum verification failed for local demo fixture '{filename}'.")


def _public_batch_id(raw: str) -> str:
    """Keep the documented demo coil identifier stable across generated snapshots."""
    return raw.replace("260610", "260725")


def _latest(rows: list[Mapping[str, Any]], field: str) -> str | None:
    values = [str(row[field]) for row in rows if row.get(field)]
    return max(values) if values else None


def _fallback_manifest() -> dict[str, Any]:
    return {
        "scenario_id": "demo-full",
        "root_seed": 240725,
        "plant_id": "NS-DEMO-LUX-01",
        "summary": {
            "energy_tonnage_before": 960.0,
            "quality_predicted_yield_before": 0.88,
            "quality_predicted_yield_after": 0.95,
            "lining_rul_p50_days": 21.0,
        },
    }


def _fallback_datasets() -> dict[str, list[dict[str, Any]]]:
    common = {
        "plant_id": "NS-DEMO-LUX-01",
        "data_classification": "SYNTHETIC",
        "privacy_label": "DEMO-NONPERSONAL",
        "event_ts": "2026-07-25T08:30:00Z",
    }
    return {
        "telemetry": [
            {
                **common,
                "event_id": "fallback-telemetry-07",
                "asset_id": "LUX-BF-01",
                "payload": {
                    "sensor_id": "LUX-BF-01-HERE-H07",
                    "signal_code": "hearth_refractory_estimate",
                    "value": 363.0,
                    "unit": "mm",
                    "quality": "GOOD",
                },
            }
        ],
        "energy_interval": [
            {
                **common,
                "event_id": "fallback-energy-01",
                "asset_id": "LUX-UTIL-01",
                "payload": {
                    "interval_start": "2026-07-25T08:30:00Z",
                    "interval_end": "2026-07-25T08:45:00Z",
                    "price": 280.0,
                    "demand": 40.0,
                    "baseline_demand_mw": 46.0,
                    "consumption_mwh": 10.0,
                    "grid_carbon_intensity_kgco2e_per_mwh": 220.0,
                    "meter_id": "LUX-UTIL-01-ELEC-01",
                    "scenario": "demo-full",
                },
            }
        ],
        "heat_batch": [
            {
                **common,
                "event_id": "fallback-batch-01",
                "asset_id": "LUX-RHF-01",
                "payload": {
                    "operation_id": "REHEAT-BATCH-00",
                    "planned_ts": "2026-07-25T08:30:00Z",
                    "urgent": False,
                    "grade_code": "NS-AUTO-DP780",
                    "material_id": "COIL-LUX-260725-017",
                },
            }
        ],
        "quality_measurement": [
            {
                **common,
                "event_id": "fallback-quality-017",
                "asset_id": "LUX-HSM-01",
                "payload": {
                    "material_id": "COIL-LUX-260725-017",
                    "heat_id": "H-LUX-260725-0042",
                    "grade_code": "NS-AUTO-DP780",
                    "sample_id": "LAB-260725-0091",
                    "characteristic_code": "tensile_strength",
                    "value": 801.2,
                    "unit": "MPa",
                    "lower_spec_limit": 780.0,
                    "upper_spec_limit": 930.0,
                    "result_status": "PASS",
                    "carbon_equivalent": 0.33,
                    "coiling_temperature_bias_c": 18.0,
                },
            }
        ],
        "alarm_event": [
            {
                **common,
                "event_id": "fallback-alert-07",
                "asset_id": "LUX-BF-01",
                "payload": {
                    "alert_id": "ALERT-HEARTH-SECTOR-07",
                    "component_id": "HEARTH-SECTOR-07",
                    "severity": "CRITICAL",
                    "status": "OPEN",
                    "message": "Synthetic 21-day lining warning.",
                    "confidence": 0.87,
                },
            }
        ],
        "maintenance_event": [],
    }
