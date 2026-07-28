"""Local file-backed query adapter for deterministic simulator datasets."""

from __future__ import annotations

import json
import hashlib
import re
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .config import Settings


_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_FIXTURE = _ROOT / "services" / "bff-api" / "fixtures" / "demo-full"
_ISO_INSTANT_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})T"
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
    r"(?P<fraction>\.\d{1,6})?(?P<tz>Z|[+-]\d{2}:\d{2})$"
)
_DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_COMPACT_INSTANT_RE = re.compile(
    r"(?<!\d)(?P<stamp>\d{8}T\d{4}(?:\d{2})?Z)(?!\d)"
)


@dataclass
class DemoRepository:
    """Normalizes simulator envelopes into the BFF's local read projections."""

    datasets: dict[str, list[dict[str, Any]]]
    manifest: dict[str, Any]
    source: str
    alerts: dict[str, dict[str, Any]] = field(default_factory=dict)
    workorders: dict[str, dict[str, Any]] = field(default_factory=dict)
    demo_clock_shift_days: int = 0

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
                shift_days = 0
                if settings.demo_clock_rebase:
                    datasets, manifest, shift_days = _rebase_demo_clock(
                        datasets, manifest
                    )
                repository = cls(
                    datasets=datasets,
                    manifest=manifest,
                    source=f"simulator-fixture:{candidate.name}",
                    demo_clock_shift_days=shift_days,
                )
                repository._hydrate_mutable_projections()
                return repository
        datasets = _fallback_datasets()
        manifest = _fallback_manifest()
        shift_days = 0
        if settings.demo_clock_rebase:
            datasets, manifest, shift_days = _rebase_demo_clock(datasets, manifest)
        repository = cls(
            datasets=datasets,
            manifest=manifest,
            source="built-in-fallback",
            demo_clock_shift_days=shift_days,
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
        # Deterministic site-specific scaling so each site shows different figures.
        factor = _site_factor(site)
        return {
            "site": site,
            "syntheticBanner": "Synthetic demo data — not for operational control",
            "freshness": {
                "energy": {"asOf": _latest(energy, "eventTs"), "stale": False},
                "furnace": {"asOf": _latest(self.telemetry_rows(), "eventTs"), "stale": False},
                "quality": {"asOf": _latest(quality, "eventTs"), "stale": False},
            },
            "kpis": {
                "plannedTonnage": round(metrics.get("energy_tonnage_before", 960.0) * factor, 1),
                "energyConsumptionMwh": round(total_consumption * factor, 2),
                "energyDispatchSavingsTargetPct": 10.4,
                "scope2KgCo2e": round(scope2 * factor, 2),
                "qualityPredictedFirstPassYieldPct": round(
                    float(metrics.get("quality_predicted_yield_before", 0.88)) * 100
                    - _site_yield_offset(site),
                    1,
                ),
                "liningRulDaysP50": round(
                    metrics.get("lining_rul_p50_days", 21.0) * factor, 0
                ),
                "openAlerts": sum(
                    1
                    for alert in self.alerts.values()
                    if alert["status"] != "CLOSED"
                    and (site == "all" or alert.get("site") == site)
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
        factor = _site_factor(site)
        return {
            "site": site,
            "energyConsumptionMwh": round(total_mwh * factor, 2),
            "scope1KgCo2e": round(tonnage * 1425 * factor, 2),
            "scope2KgCo2e": round(scope2 * factor, 2),
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
        self._hydrate_supplementary_alerts()

    def _hydrate_supplementary_alerts(self) -> None:
        """Add the deterministic Warning/Info alert deck the demo triages.

        The generated scenario only raises the single critical lining alarm. The
        Command Center needs a realistic severity mix across all four sites, so
        this deck is layered on top without touching the checksum-verified pack.
        """
        anchor = _anchor_timestamp(self.manifest)
        for entry in _SUPPLEMENTARY_ALERTS:
            alert_id = str(entry["alertId"])
            if alert_id in self.alerts:
                continue
            created_at = _shift_hours(anchor, -int(entry["offsetHours"]))
            self.alerts[alert_id] = {
                "alertId": alert_id,
                "site": entry["site"],
                "assetId": entry["assetId"],
                "componentId": entry["componentId"],
                "severity": entry["severity"],
                "status": entry["status"],
                "message": entry["message"],
                "confidence": entry["confidence"],
                "createdAt": created_at,
                "updatedAt": created_at,
                "sourceRef": f"demo:supplementary-alert:{alert_id}",
                "correlationId": f"demo-alert-deck-{self.manifest.get('root_seed', 240725)}",
            }


_SUPPLEMENTARY_ALERTS: tuple[dict[str, Any], ...] = (
    {
        "alertId": "ALERT-ENERGY-SCARCITY-1830",
        "site": "NS-DEMO-LUX-01",
        "assetId": "LUX-UTIL-01",
        "componentId": "GRID",
        "severity": "WARNING",
        "status": "OPEN",
        "message": "Evening scarcity spike to 280 EUR/MWh forecast for 18:30-19:00.",
        "confidence": 0.74,
        "offsetHours": 6,
    },
    {
        "alertId": "ALERT-ETS-ALLOWANCE-Q3",
        "site": "NS-DEMO-LUX-01",
        "assetId": "LUX-SITE-01",
        "componentId": "ETS-LEDGER",
        "severity": "WARNING",
        "status": "OPEN",
        "message": "Q3 EU ETS allowance headroom down to 6.2% at current emission intensity.",
        "confidence": 0.71,
        "offsetHours": 9,
    },
    {
        "alertId": "ALERT-STOVE-04-DOME-TEMP",
        "site": "NS-DEMO-LUX-01",
        "assetId": "LUX-BF-01",
        "componentId": "STOVE-04",
        "severity": "WARNING",
        "status": "OPEN",
        "message": "Hot blast stove 04 dome temperature 24 C below setpoint over three cycles.",
        "confidence": 0.66,
        "offsetHours": 12,
    },
    {
        "alertId": "ALERT-SENSOR-DRIFT-TC-114",
        "site": "NS-DEMO-LUX-01",
        "assetId": "LUX-BF-01",
        "componentId": "TC-114",
        "severity": "WARNING",
        "status": "ACKNOWLEDGED",
        "message": "Thermocouple TC-114 drifting 1.8 C/h against neighbouring sensors; calibration due.",
        "confidence": 0.63,
        "offsetHours": 15,
    },
    {
        "alertId": "ALERT-LADLE-12-CYCLE-COUNT",
        "site": "NS-DEMO-LUX-01",
        "assetId": "LUX-BOF-01",
        "componentId": "LADLE-12",
        "severity": "INFO",
        "status": "OPEN",
        "message": "Ladle 12 reached 88 of 110 refractory heats; schedule relining window.",
        "confidence": 0.58,
        "offsetHours": 18,
    },
    {
        "alertId": "ALERT-PPA-WIND-SURPLUS",
        "site": "NS-DEMO-LUX-01",
        "assetId": "LUX-UTIL-01",
        "componentId": "PPA-WIND",
        "severity": "INFO",
        "status": "OPEN",
        "message": "Wind PPA surplus 12 MWh forecast 02:00-05:00; candidate window for reheat pre-charge.",
        "confidence": 0.61,
        "offsetHours": 21,
    },
    {
        "alertId": "ALERT-KNOWLEDGE-REVIEW-QUEUE",
        "site": "NS-DEMO-LUX-01",
        "assetId": "LUX-SITE-01",
        "componentId": "KNOWLEDGE-HUB",
        "severity": "INFO",
        "status": "OPEN",
        "message": "Three captured procedures awaiting expert review beyond the 5-day SLA.",
        "confidence": 0.55,
        "offsetHours": 24,
    },
    {
        "alertId": "ALERT-DE-CASTER-MOULD-LEVEL",
        "site": "NS-DEMO-DE-01",
        "assetId": "DE-CC-01",
        "componentId": "MOULD-LEVEL-02",
        "severity": "WARNING",
        "status": "OPEN",
        "message": "Caster 01 mould level oscillation above 4.5 mm band on two consecutive sequences.",
        "confidence": 0.69,
        "offsetHours": 7,
    },
    {
        "alertId": "ALERT-DE-SCRAP-MIX-COST",
        "site": "NS-DEMO-DE-01",
        "assetId": "DE-EAF-01",
        "componentId": "CHARGE-MIX",
        "severity": "INFO",
        "status": "OPEN",
        "message": "Scrap charge mix 3.1% above least-cost recipe; alternative bundle available.",
        "confidence": 0.57,
        "offsetHours": 16,
    },
    {
        "alertId": "ALERT-BE-ROLL-FORCE-TREND",
        "site": "NS-DEMO-BE-01",
        "assetId": "BE-HSM-01",
        "componentId": "STAND-F4",
        "severity": "WARNING",
        "status": "OPEN",
        "message": "Stand F4 roll force trending 5.8% high for NS-AUTO-DP780; check work-roll wear.",
        "confidence": 0.64,
        "offsetHours": 10,
    },
    {
        "alertId": "ALERT-BE-COIL-COOLING-BANK",
        "site": "NS-DEMO-BE-01",
        "assetId": "BE-HSM-01",
        "componentId": "COOLING-BANK-03",
        "severity": "INFO",
        "status": "OPEN",
        "message": "Cooling bank 03 nozzle flow 6% below nominal; routine descaling proposed.",
        "confidence": 0.53,
        "offsetHours": 20,
    },
    {
        "alertId": "ALERT-ES-REHEAT-AIR-RATIO",
        "site": "NS-DEMO-ES-01",
        "assetId": "ES-RHF-01",
        "componentId": "BURNER-ZONE-02",
        "severity": "WARNING",
        "status": "OPEN",
        "message": "Reheat furnace zone 02 air/fuel ratio rich by 4%; ~180 kWh/h avoidable loss.",
        "confidence": 0.67,
        "offsetHours": 11,
    },
    {
        "alertId": "ALERT-ES-BILLET-YIELD-WATCH",
        "site": "NS-DEMO-ES-01",
        "assetId": "ES-BM-01",
        "componentId": "BILLET-LINE",
        "severity": "INFO",
        "status": "OPEN",
        "message": "Billet line yield 0.9 pt under weekly plan; no action required yet.",
        "confidence": 0.51,
        "offsetHours": 22,
    },
)


def _site_factor(site: str) -> float:
    """Deterministic per-site scaling factor so KPIs visibly differ between sites."""
    factors = {
        "NS-DEMO-LUX-01": 1.0,
        "NS-DEMO-DE-01": 0.72,
        "NS-DEMO-BE-01": 0.38,
        "NS-DEMO-ES-01": 0.55,
    }
    return factors.get(site, 1.0)


def _site_yield_offset(site: str) -> float:
    """Offset to first-pass yield % so each site looks different."""
    offsets = {
        "NS-DEMO-LUX-01": 0.0,
        "NS-DEMO-DE-01": 2.3,
        "NS-DEMO-BE-01": -1.4,
        "NS-DEMO-ES-01": 3.8,
    }
    return offsets.get(site, 0.0)


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


def _rebase_demo_clock(
    datasets: dict[str, list[dict[str, Any]]],
    manifest: dict[str, Any],
    *,
    now: datetime | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any], int]:
    anchor = _parse_iso_instant(_anchor_timestamp(manifest))
    if anchor is None:
        return datasets, manifest, 0

    now_utc = now or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    shift_days = int(
        (now_utc.astimezone(timezone.utc) - anchor.astimezone(timezone.utc))
        // timedelta(days=1)
    )
    if shift_days <= 0:
        return datasets, manifest, 0

    shifted_datasets = {
        name: [_rebase_value(record, shift_days) for record in records]
        for name, records in datasets.items()
    }
    shifted_manifest = _rebase_value(manifest, shift_days)
    return shifted_datasets, shifted_manifest, shift_days


def _rebase_value(value: Any, shift_days: int, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            item_key: _rebase_value(item_value, shift_days, str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_rebase_value(item, shift_days, key) for item in value]
    if not isinstance(value, str):
        return value

    shifted = _shift_timestamp_string(value, shift_days)
    if shifted != value:
        return shifted
    if key is not None and _is_identifier_field(key):
        return _shift_compact_identifier_timestamps(value, shift_days)
    return value


def _shift_timestamp_string(value: str, shift_days: int) -> str:
    instant_match = _ISO_INSTANT_RE.match(value)
    if instant_match:
        parsed = _parse_iso_instant(value)
        if parsed is None:
            return value
        shifted = parsed + timedelta(days=shift_days)
        fraction = instant_match.group("fraction") or ""
        if fraction:
            digits = len(fraction) - 1
            fraction = f".{shifted.microsecond:06d}"[: digits + 1]
        return (
            f"{shifted:%Y-%m-%dT%H:%M:%S}"
            f"{fraction}{instant_match.group('tz')}"
        )

    if _DATE_ONLY_RE.match(value):
        try:
            return (date.fromisoformat(value) + timedelta(days=shift_days)).isoformat()
        except ValueError:
            return value
    return value


def _parse_iso_instant(value: str) -> datetime | None:
    if not _ISO_INSTANT_RE.match(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _is_identifier_field(key: str) -> bool:
    normalized = key.lower()
    return normalized == "id" or normalized.endswith("_id") or normalized.endswith("id")


def _shift_compact_identifier_timestamps(value: str, shift_days: int) -> str:
    def replace(match: re.Match[str]) -> str:
        stamp = match.group("stamp")
        fmt = "%Y%m%dT%H%M%SZ" if len(stamp) == 16 else "%Y%m%dT%H%MZ"
        try:
            parsed = datetime.strptime(stamp, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            return stamp
        shifted = parsed + timedelta(days=shift_days)
        return shifted.strftime(fmt)

    return _COMPACT_INSTANT_RE.sub(replace, value)


def _public_batch_id(raw: str) -> str:
    """Keep the documented demo coil identifier stable across generated snapshots."""
    return raw.replace("260610", "260725")


def _anchor_timestamp(manifest: Mapping[str, Any]) -> str:
    """Latest event timestamp in the pack; the supplementary deck hangs off it."""
    window = manifest.get("min_max_event_ts") or {}
    raw = window.get("max") if isinstance(window, Mapping) else None
    return str(raw) if raw else "2026-06-11T00:00:00Z"


def _shift_hours(timestamp: str, hours: int) -> str:
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return timestamp
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    shifted = parsed + timedelta(hours=hours)
    return shifted.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _latest(rows: list[Mapping[str, Any]], field: str) -> str | None:
    values = [str(row[field]) for row in rows if row.get(field)]
    return max(values) if values else None


def _fallback_manifest() -> dict[str, Any]:
    return {
        "scenario_id": "demo-full",
        "root_seed": 240725,
        "plant_id": "NS-DEMO-LUX-01",
        "start_time": "2026-07-25T08:30:00Z",
        "end_time": "2026-07-25T08:30:00Z",
        "min_max_event_ts": {
            "min": "2026-07-25T08:30:00Z",
            "max": "2026-07-25T08:30:00Z",
        },
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
