"""Top-level generation orchestrator (docs section 6.2 generator architecture).

Wires the scenario manifest, deterministic clock, process-state models,
observation model, anomaly controller, and edge gateway together to
produce every dataset for one run: telemetry, energy_interval,
quality_measurement, heat_batch, maintenance_event, operator_knowledge,
model_inference, and the truth ledger.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from simulator import GENERATOR_VERSION, config
from simulator.anomalies import AnomalyController
from simulator.checksum import write_checksums
from simulator.clock import iso
from simulator.determinism import child_random, config_checksum
from simulator.edge import EdgeGateway
from simulator.envelope import build_envelope
from simulator.observation import SensorFaultState, observe
from simulator.process import energy as energy_model
from simulator.process import furnace as furnace_model
from simulator.process import knowledge as knowledge_model
from simulator.process import maintenance as maintenance_model
from simulator.process import quality as quality_model
from simulator.process import rolling as rolling_model
from simulator.scenario import ScenarioManifest
from simulator.truth_ledger import TruthLedger, TruthRecord, lining_state_for_rul
from simulator.writer import write_dataset

DATASET_NAMES = [
    "telemetry", "energy_interval", "quality_measurement", "heat_batch",
    "maintenance_event", "alarm_event", "operator_knowledge", "model_inference", "truth_ledger",
]


@dataclass
class RunResult:
    manifest: ScenarioManifest
    out_dir: Path
    fast: bool
    fmt: str
    datasets: dict = field(default_factory=dict)
    summary: dict = field(default_factory=dict)
    file_paths: dict = field(default_factory=dict)
    run_manifest_path: Path | None = None
    checksums: dict = field(default_factory=dict)


def _correlation_id(manifest: ScenarioManifest) -> str:
    return f"run-{manifest.scenario_id}-{manifest.root_seed}"


def _source_id(plant_id: str) -> str:
    suffix = plant_id.replace("NS-DEMO-", "").replace("-01", "").lower()
    return f"edge-{suffix}-01"


def generate_run(manifest: ScenarioManifest, *, out_dir: Path, fast: bool = False,
                  fmt: str = "ndjson") -> RunResult:
    manifest.validate()
    root_seed = manifest.root_seed
    scenario_id = manifest.scenario_id
    plant_id = manifest.plant_id
    start_time = manifest.start_time
    window_hours = manifest.window_hours(fast)
    interval_seconds = manifest.sample_interval_seconds(fast)
    correlation_id = _correlation_id(manifest)
    source_id = _source_id(plant_id)
    anomaly_controller = AnomalyController.from_manifest(manifest.anomalies)

    gateway_rng = child_random(root_seed, scenario_id, plant_id, source_id, "edge-gateway")
    gateway = EdgeGateway(source_id, gateway_rng, outage_spec=manifest.edge)

    truth_ledger = TruthLedger()

    telemetry = _generate_furnace_telemetry(
        manifest, window_hours, interval_seconds, anomaly_controller, gateway,
        correlation_id, source_id, truth_ledger,
    )
    telemetry += _generate_rolling_telemetry(
        manifest, window_hours, interval_seconds, anomaly_controller, gateway,
        correlation_id, source_id, fast,
    )
    energy_interval, energy_summary = _generate_energy_dataset(
        manifest, anomaly_controller, gateway, correlation_id, source_id,
    )
    heat_batch = _generate_heat_batch_dataset(manifest, energy_summary, correlation_id, source_id)
    quality_measurement, quality_summary = _generate_quality_dataset(
        manifest, window_hours, gateway, correlation_id, source_id, fast,
    )
    model_inference, lining_summary = _generate_model_inference(
        manifest, window_hours, gateway, correlation_id, source_id,
    )
    maintenance_event = _generate_maintenance_dataset(manifest, window_hours, lining_summary, start_time)
    alarm_event = _generate_alarm_dataset(manifest, window_hours, lining_summary, start_time, gateway,
                                          correlation_id, source_id)
    operator_knowledge = _generate_operator_knowledge_dataset(manifest, start_time)

    _finalize_truth_ledger(truth_ledger, manifest, window_hours, lining_summary, quality_summary,
                            energy_summary, start_time)

    datasets = {
        "telemetry": telemetry,
        "energy_interval": energy_interval,
        "quality_measurement": quality_measurement,
        "heat_batch": heat_batch,
        "maintenance_event": maintenance_event,
        "alarm_event": alarm_event,
        "operator_knowledge": operator_knowledge,
        "model_inference": model_inference,
        "truth_ledger": truth_ledger.as_dicts(),
    }

    summary = {
        "scenario_id": scenario_id,
        "root_seed": root_seed,
        "window_hours": window_hours,
        "sample_interval_seconds": interval_seconds,
        "fast": fast,
        **lining_summary,
        **{k: v for k, v in energy_summary.items() if not k.startswith("_")},
        **quality_summary,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    file_paths = {}
    for name, records in datasets.items():
        path = write_dataset(out_dir, name, records, fmt=fmt if name != "truth_ledger" else "ndjson")
        file_paths[name] = path

    run_manifest = {
        "scenario_id": scenario_id,
        "root_seed": root_seed,
        "generator_version": GENERATOR_VERSION,
        "child_seed_derivation_version": 1,
        "config_checksum": config_checksum(manifest.raw),
        "clock_mode": "accelerated",
        "fast": fast,
        "start_time": iso(start_time),
        "window_hours": window_hours,
        "sample_interval_seconds": interval_seconds,
        "row_counts": {name: len(records) for name, records in datasets.items()},
        "min_max_event_ts": _min_max_event_ts(telemetry),
        "summary": summary,
        "data_classification": config.DATA_CLASSIFICATION,
        "privacy_label": config.PRIVACY_LABEL,
    }
    run_manifest_path = out_dir / "manifest.json"
    run_manifest_path.write_text(json.dumps(run_manifest, indent=2, sort_keys=True), encoding="utf-8")

    filenames = [p.name for p in file_paths.values()] + ["manifest.json"]
    write_checksums(out_dir, filenames)
    checksums = json.loads((out_dir / "checksums.json").read_text(encoding="utf-8"))

    return RunResult(manifest=manifest, out_dir=out_dir, fast=fast, fmt=fmt, datasets=datasets,
                      summary=summary, file_paths=file_paths, run_manifest_path=run_manifest_path,
                      checksums=checksums)


def _min_max_event_ts(telemetry: list[dict]) -> dict:
    if not telemetry:
        return {"min": None, "max": None}
    timestamps = sorted(t["event_ts"] for t in telemetry)
    return {"min": timestamps[0], "max": timestamps[-1]}


def _generate_furnace_telemetry(manifest, window_hours, interval_seconds, anomaly_controller,
                                 gateway, correlation_id, source_id, truth_ledger) -> list[dict]:
    plant_id = manifest.plant_id
    asset_id = "LUX-BF-01"
    start_time = manifest.start_time
    step_hours = interval_seconds / 3600.0
    steps = max(int(window_hours / step_hours), 1)

    ambient_rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id, "ambient")
    records: list[dict] = []
    fault_states: dict[str, SensorFaultState] = {}

    for sector in manifest.hearth_sectors:
        sector_rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id, f"sector-{sector}")
        degraded = anomaly_controller.is_active("lining_degradation", 0.0, target=sector) or \
            anomaly_controller.is_active("lining_degradation", window_hours, target=sector)
        target_delta_c = 0.0
        if degraded:
            spec = next(s for s in anomaly_controller.specs if s.anomaly_type == "lining_degradation" and s.target == sector)
            target_delta_c = float(spec.params.get("target_delta_c", 22.0))

        min_safe = manifest.campaign["min_safe_thickness_mm"]
        thickness_at_eval = manifest.thickness_at_eval_mm(sector)
        degradation_rate = manifest.degradation_rate(sector)

        base_shell = ambient_rng.uniform(120.0, 140.0)
        base_inlet = ambient_rng.uniform(25.0, 29.0)
        base_flow = ambient_rng.uniform(180.0, 220.0)
        base_delta_t = ambient_rng.uniform(6.0, 9.0)
        inner_temp_c = 1180.0

        for step in range(steps + 1):
            elapsed_hours = step * step_hours
            hours_before_eval = window_hours - elapsed_hours
            elapsed_fraction = elapsed_hours / max(window_hours, 1e-9)

            thickness_mm = furnace_model.hidden_thickness_mm(
                thickness_at_eval_mm=thickness_at_eval,
                degradation_rate_mm_per_day=degradation_rate,
                hours_before_eval=hours_before_eval,
            )
            excursion_c = furnace_model.sector_shell_excursion_c(
                elapsed_fraction=elapsed_fraction, target_delta_c=target_delta_c, rng=sector_rng,
            ) if degraded else 0.0
            efficiency_loss = 0.35 if degraded else 0.0

            shell_temp = base_shell + excursion_c + sector_rng.gauss(0.0, 1.0)
            cooling_inlet = base_inlet + sector_rng.gauss(0.0, 0.4)
            cooling_flow = base_flow + sector_rng.gauss(0.0, 4.0)
            delta_t = furnace_model.cooling_delta_t(
                base_delta_t_c=base_delta_t, excursion_c=excursion_c, efficiency_loss_fraction=efficiency_loss,
            )
            cooling_outlet = cooling_inlet + max(delta_t, 0.1)
            heat_flux = furnace_model.heat_flux_kw_m2(flow_m3h=cooling_flow, delta_t_c=cooling_outlet - cooling_inlet)

            event_ts = start_time + timedelta(hours=elapsed_hours)
            values = {
                "hearth_shell_temperature": (shell_temp, "Cel"),
                "cooling_water_inlet_temperature": (cooling_inlet, "Cel"),
                "cooling_water_outlet_temperature": (cooling_outlet, "Cel"),
                "cooling_water_flow": (cooling_flow, "m3/h"),
                "local_heat_flux": (heat_flux, "kW/m2"),
                "hearth_refractory_estimate": (thickness_mm, "mm"),
            }
            for signal_code, (true_value, unit) in values.items():
                sensor_id = f"LUX-BF-01-{signal_code.upper()[:4]}-H{sector}"
                fault_key = f"{sensor_id}"
                fault_state = fault_states.setdefault(fault_key, SensorFaultState())
                signal_rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id,
                                           f"{signal_code}-{sector}-{step}")
                registry = config.SIGNAL_REGISTRY[signal_code]
                if signal_code == "hearth_refractory_estimate":
                    # Bounded model noise on the 15-min inference (docs 3.2), not raw
                    # sensor noise, so the underlying monotonic trend stays checkable.
                    noise_std = 0.3
                    quantization = 0.5
                else:
                    noise_std = max((registry.high - registry.low) * 0.002, 0.01)
                    quantization = 0.1
                obs = observe(true_value=true_value, rng=signal_rng, noise_std=noise_std,
                              quantization=quantization, fault_state=fault_state)
                sample_period_ms = interval_seconds * 1000
                ingest_ts = event_ts + timedelta(milliseconds=gateway.jitter_ms())
                envelope = build_envelope(
                    schema_name="novasteel.telemetry.v1", event_ts=event_ts, ingest_ts=ingest_ts,
                    sequence=gateway.next_sequence(), source_id=source_id, plant_id=plant_id,
                    asset_id=asset_id, scenario_id=manifest.scenario_id, correlation_id=correlation_id,
                    seed=manifest.root_seed, rng=signal_rng,
                    payload={
                        "type": config.telemetry_event_type(signal_code),
                        "sensor_id": sensor_id,
                        "signal_code": signal_code,
                        "value": obs.value,
                        "unit": unit,
                        "quality": obs.quality,
                        "uncertainty": obs.uncertainty,
                        "sample_period_ms": sample_period_ms,
                        "hearth_sector": sector,
                    },
                )
                records.append(envelope)

    return records


def _generate_rolling_telemetry(manifest, window_hours, interval_seconds, anomaly_controller,
                                 gateway, correlation_id, source_id, fast=False) -> list[dict]:
    plant_id = manifest.plant_id
    asset_id = "LUX-HSM-01"
    start_time = manifest.start_time
    step_hours = interval_seconds / 3600.0
    steps = max(int(window_hours / step_hours), 1)
    stride = max(steps // 12, 1)  # one coil pass roughly every `stride` steps

    quality_cfg = manifest.quality
    drift_active = quality_cfg.get("drift_active", False)
    latent_hours = manifest.quality_latent_hours(fast)
    full_drift_hours = manifest.quality_full_drift_hours(fast)

    records: list[dict] = []
    for step in range(0, steps + 1, stride):
        elapsed_hours = step * step_hours
        event_ts = start_time + timedelta(hours=elapsed_hours)
        pass_rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id, f"coil-{step}")

        drift = quality_model.drift_state_at(elapsed_hours, latent_hours=latent_hours,
                                             full_drift_hours=full_drift_hours) if drift_active else \
            quality_model.DriftState(0.0, 0.0, 0.0, 0.0)

        # Slab entry speed at the roughing mill is slow; conserving mass
        # through to ~1.8mm at the finishing train needs a small entry speed
        # so downstream stands stay within the 0.2-22 m/s signal range.
        base_speed = pass_rng.uniform(0.08, 0.14)
        slab_thickness = pass_rng.uniform(210.0, 230.0)
        stands = rolling_model.chain_stands(base_speed_m_s=base_speed, slab_thickness_mm=slab_thickness,
                                             width_mm=1250.0, rng=pass_rng)
        for stand in stands:
            ingest_ts = event_ts + timedelta(milliseconds=gateway.jitter_ms())
            signal_rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id,
                                       f"stand-{stand.stand_id}-{step}")
            for signal_code, value, unit in [
                ("stand_motor_current", stand.stand_motor_current_a, "A"),
                ("rolling_force", stand.rolling_force_mn * (1.0 + drift.force_imbalance_pct / 100.0), "MW"),
                ("strip_speed", stand.strip_speed_m_s, "m/s"),
            ]:
                envelope = build_envelope(
                    schema_name="novasteel.telemetry.v1", event_ts=event_ts, ingest_ts=ingest_ts,
                    sequence=gateway.next_sequence(), source_id=source_id, plant_id=plant_id,
                    asset_id=asset_id, scenario_id=manifest.scenario_id, correlation_id=correlation_id,
                    seed=manifest.root_seed, rng=signal_rng,
                    payload={
                        "type": config.telemetry_event_type(signal_code),
                        "sensor_id": f"{asset_id}-{stand.stand_id}",
                        "signal_code": signal_code,
                        "value": round(value, 3),
                        "unit": unit,
                        "quality": "GOOD",
                        "uncertainty": 0.5,
                        "sample_period_ms": interval_seconds * 1000,
                        "stand_id": stand.stand_id,
                        "entry_thickness_mm": round(stand.entry_thickness_mm, 3),
                        "exit_thickness_mm": round(stand.exit_thickness_mm, 3),
                    },
                )
                records.append(envelope)

        coiling_temp = 620.0 + drift.coiling_temp_bias_c + pass_rng.uniform(-3.0, 3.0)
        ingest_ts = event_ts + timedelta(milliseconds=gateway.jitter_ms())
        signal_rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id, f"coiling-temp-{step}")
        envelope = build_envelope(
            schema_name="novasteel.telemetry.v1", event_ts=event_ts, ingest_ts=ingest_ts,
            sequence=gateway.next_sequence(), source_id=source_id, plant_id=plant_id,
            asset_id=asset_id, scenario_id=manifest.scenario_id, correlation_id=correlation_id,
            seed=manifest.root_seed, rng=signal_rng,
            payload={
                "type": config.telemetry_event_type("coiling_temperature"),
                "sensor_id": f"{asset_id}-COIL-TC-01",
                "signal_code": "coiling_temperature",
                "value": round(coiling_temp, 2),
                "unit": "Cel",
                "quality": "GOOD",
                "uncertainty": 1.0,
                "sample_period_ms": interval_seconds * 1000,
            },
        )
        records.append(envelope)
    return records


def _generate_energy_dataset(manifest, anomaly_controller, gateway, correlation_id, source_id):
    plant_id = manifest.plant_id
    # Dispatch to the EAF-specific generator for the Belgium melt shop.
    if plant_id == "NS-DEMO-BE-01":
        return _generate_eaf_energy_dataset(manifest, anomaly_controller, gateway, correlation_id, source_id)
    asset_id = "LUX-UTIL-01"
    start_time = manifest.start_time
    energy_cfg = manifest.energy
    price_rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id, "price")
    prices = energy_model.baseline_price_curve(price_rng)

    spike_active = any(s.anomaly_type == "price_spike" for s in anomaly_controller.specs)
    spike_start_interval = spike_end_interval = None
    if spike_active:
        spike = next(s for s in anomaly_controller.specs if s.anomaly_type == "price_spike")
        spike_start_interval = int(float(spike.start_hours) * 4)
        spike_end_interval = int(float(spike.end_hours) * 4)
        prices = energy_model.apply_scarcity_spike(
            prices, spike_start_interval=spike_start_interval, spike_end_interval=spike_end_interval,
            spike_price=float(spike.params.get("spike_price_eur_mwh", 280.0)),
        )

    batch_rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id, "batches")
    num_batches = energy_cfg.get("num_batches", 6)
    urgent_index = energy_cfg.get("urgent_batch_index", -1)
    base_load_mw = energy_cfg.get("base_load_mw", 40.0)
    spread = 96 // max(num_batches, 1)
    batches = [
        energy_model.ReheatBatch(
            batch_id=f"BATCH-{i:02d}",
            planned_interval=min(i * spread + batch_rng.randint(0, 3), 95),
            duration_intervals=batch_rng.randint(2, 4),
            demand_mw=batch_rng.uniform(6.0, 14.0),
            urgent=(i == urgent_index),
        )
        for i in range(num_batches)
    ]

    baseline_cost = energy_model.schedule_cost(batches, prices, base_load_mw)
    optimized_batches, diagnostics = (batches, {"shifted_batches": 0, "hard_constraint_violations": 0})
    if spike_active:
        optimized_batches, diagnostics = energy_model.optimize_schedule(
            batches, prices, spike_start_interval, spike_end_interval,
        )
    optimized_cost = energy_model.schedule_cost(optimized_batches, prices, base_load_mw)
    baseline_profile = energy_model.demand_profile(batches, base_load_mw)
    optimized_profile = energy_model.demand_profile(optimized_batches, base_load_mw)

    records = []
    for i, price in enumerate(prices):
        interval_start = start_time + timedelta(minutes=15 * i)
        interval_end = interval_start + timedelta(minutes=15)
        signal_rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id, f"interval-{i}")
        ingest_ts = interval_start + timedelta(milliseconds=gateway.jitter_ms())
        demand_mw = optimized_profile[i]
        is_spike_interval = spike_active and spike_start_interval <= i < spike_end_interval
        carbon_intensity = signal_rng.uniform(90.0, 220.0) + (signal_rng.uniform(50.0, 150.0) if is_spike_interval else 0.0)
        envelope = build_envelope(
            schema_name="novasteel.energy-interval.v1", event_ts=interval_start, ingest_ts=ingest_ts,
            sequence=gateway.next_sequence(), source_id=source_id, plant_id=plant_id, asset_id=asset_id,
            scenario_id=manifest.scenario_id, correlation_id=correlation_id, seed=manifest.root_seed,
            rng=signal_rng,
            payload={
                "type": "energy.interval",
                "meter_id": f"{asset_id}-ELEC-01",
                "interval_start": iso(interval_start),
                "interval_end": iso(interval_end),
                "price": price,
                "price_unit": "EUR/MWh",
                "demand": round(demand_mw, 2),
                "demand_unit": "MW",
                "consumption_mwh": round(demand_mw * 0.25, 4),
                "grid_carbon_intensity_kgco2e_per_mwh": round(carbon_intensity, 1),
                "baseline_demand_mw": round(baseline_profile[i], 2),
                "scenario": manifest.scenario_id,
            },
        )
        records.append(envelope)

    spike_slice = slice(spike_start_interval, spike_end_interval) if spike_active else slice(0, 0)
    peak_during_spike_before = max(baseline_profile[spike_slice], default=0.0)
    peak_during_spike_after = max(optimized_profile[spike_slice], default=0.0)

    summary = {
        "energy_baseline_cost_eur": round(baseline_cost, 2),
        "energy_optimized_cost_eur": round(optimized_cost, 2),
        "energy_tonnage_before": energy_model.planned_tonnage(batches),
        "energy_tonnage_after": energy_model.planned_tonnage(optimized_batches),
        "energy_hard_constraint_violations": diagnostics["hard_constraint_violations"],
        "energy_shifted_batches": diagnostics["shifted_batches"],
        "energy_peak_demand_before_mw": round(max(baseline_profile), 2),
        "energy_peak_demand_after_mw": round(max(optimized_profile), 2),
        "energy_peak_demand_during_spike_before_mw": round(peak_during_spike_before, 2),
        "energy_peak_demand_during_spike_after_mw": round(peak_during_spike_after, 2),
        "energy_schedule_optimality_gap": round(
            (optimized_cost - baseline_cost) / baseline_cost if baseline_cost else 0.0, 6),
        "_batches": batches,
        "_optimized_batches": optimized_batches,
    }
    return records, summary


def _generate_eaf_energy_dataset(manifest, anomaly_controller, gateway, correlation_id, source_id):
    """Generate energy interval and EAF heat batch data for the Belgium melt shop (NS-DEMO-BE-01).

    Mirrors the structure of the Luxembourg energy dataset but uses EafHeat
    batches with physically defensible EAF parameters (80–150 MW, 45–60 min
    tap-to-tap, 100–140 t per heat, 6 h shift deferral window).
    """
    plant_id = manifest.plant_id
    asset_id = "BE-UTIL-01"
    start_time = manifest.start_time
    energy_cfg = manifest.energy
    price_rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id, "price")
    prices = energy_model.baseline_price_curve(price_rng)

    spike_active = any(s.anomaly_type == "price_spike" for s in anomaly_controller.specs)
    spike_start_interval = spike_end_interval = None
    if spike_active:
        spike = next(s for s in anomaly_controller.specs if s.anomaly_type == "price_spike")
        spike_start_interval = int(float(spike.start_hours) * 4)
        spike_end_interval = int(float(spike.end_hours) * 4)
        prices = energy_model.apply_scarcity_spike(
            prices, spike_start_interval=spike_start_interval, spike_end_interval=spike_end_interval,
            spike_price=float(spike.params.get("spike_price_eur_mwh", 280.0)),
        )

    batch_rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, "BE-EAF-01", "batches")
    num_batches = energy_cfg.get("num_batches", 6)
    urgent_index = energy_cfg.get("urgent_batch_index", -1)
    base_load_mw = energy_cfg.get("base_load_mw", 15.0)
    spread = 96 // max(num_batches, 1)
    batches = [
        energy_model.EafHeat(
            batch_id=f"EAF-HEAT-{i:02d}",
            planned_interval=min(i * spread + batch_rng.randint(0, 3), 95),
            duration_intervals=batch_rng.randint(3, 4),  # 45–60 min tap-to-tap
            demand_mw=round(batch_rng.uniform(80.0, 150.0), 1),  # typical EAF arc power
            tonnage=round(batch_rng.uniform(100.0, 140.0), 1),  # liquid steel per tap
            urgent=(i == urgent_index),
        )
        for i in range(num_batches)
    ]

    baseline_cost = energy_model.schedule_cost(batches, prices, base_load_mw)
    optimized_batches, diagnostics = (batches, {"shifted_batches": 0, "hard_constraint_violations": 0})
    if spike_active:
        optimized_batches, diagnostics = energy_model.optimize_schedule(
            batches, prices, spike_start_interval, spike_end_interval,
        )
    optimized_cost = energy_model.schedule_cost(optimized_batches, prices, base_load_mw)
    baseline_profile = energy_model.demand_profile(batches, base_load_mw)
    optimized_profile = energy_model.demand_profile(optimized_batches, base_load_mw)

    records = []
    for i, price in enumerate(prices):
        interval_start = start_time + timedelta(minutes=15 * i)
        interval_end = interval_start + timedelta(minutes=15)
        signal_rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id, f"interval-{i}")
        ingest_ts = interval_start + timedelta(milliseconds=gateway.jitter_ms())
        demand_mw = optimized_profile[i]
        is_spike_interval = spike_active and spike_start_interval <= i < spike_end_interval
        carbon_intensity = signal_rng.uniform(90.0, 220.0) + (signal_rng.uniform(50.0, 150.0) if is_spike_interval else 0.0)
        envelope = build_envelope(
            schema_name="novasteel.energy-interval.v1", event_ts=interval_start, ingest_ts=ingest_ts,
            sequence=gateway.next_sequence(), source_id=source_id, plant_id=plant_id, asset_id=asset_id,
            scenario_id=manifest.scenario_id, correlation_id=correlation_id, seed=manifest.root_seed,
            rng=signal_rng,
            payload={
                "type": "energy.interval",
                "meter_id": f"{asset_id}-ELEC-01",
                "interval_start": iso(interval_start),
                "interval_end": iso(interval_end),
                "price": price,
                "price_unit": "EUR/MWh",
                "demand": round(demand_mw, 2),
                "demand_unit": "MW",
                "consumption_mwh": round(demand_mw * 0.25, 4),
                "grid_carbon_intensity_kgco2e_per_mwh": round(carbon_intensity, 1),
                "baseline_demand_mw": round(baseline_profile[i], 2),
                "scenario": manifest.scenario_id,
            },
        )
        records.append(envelope)

    spike_slice = slice(spike_start_interval, spike_end_interval) if spike_active else slice(0, 0)
    peak_during_spike_before = max(baseline_profile[spike_slice], default=0.0)
    peak_during_spike_after = max(optimized_profile[spike_slice], default=0.0)

    summary = {
        "energy_baseline_cost_eur": round(baseline_cost, 2),
        "energy_optimized_cost_eur": round(optimized_cost, 2),
        "energy_tonnage_before": energy_model.planned_tonnage(batches),
        "energy_tonnage_after": energy_model.planned_tonnage(optimized_batches),
        "energy_hard_constraint_violations": diagnostics["hard_constraint_violations"],
        "energy_shifted_batches": diagnostics["shifted_batches"],
        "energy_peak_demand_before_mw": round(max(baseline_profile), 2),
        "energy_peak_demand_after_mw": round(max(optimized_profile), 2),
        "energy_peak_demand_during_spike_before_mw": round(peak_during_spike_before, 2),
        "energy_peak_demand_during_spike_after_mw": round(peak_during_spike_after, 2),
        "energy_schedule_optimality_gap": round(
            (optimized_cost - baseline_cost) / baseline_cost if baseline_cost else 0.0, 6),
        "_batches": batches,
        "_optimized_batches": optimized_batches,
    }
    return records, summary


def _generate_heat_batch_dataset(manifest, energy_summary, correlation_id, source_id) -> list[dict]:
    plant_id = manifest.plant_id
    start_time = manifest.start_time
    records = []
    grade_codes = list(config.GRADES)

    # Dispatch based on plant: EAF heats for Belgium, reheat batches for Luxembourg.
    if plant_id == "NS-DEMO-BE-01":
        rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, "BE-EAF-01", "heat-batch")
        for i, batch in enumerate(energy_summary.get("_batches", [])):
            heat_id = f"H-BE-{start_time:%y%m%d}-{i:04d}"
            planned_ts = start_time + timedelta(minutes=15 * batch.planned_interval)
            energy_mwh = round(batch.demand_mw * batch.duration_intervals * 0.25, 2)
            envelope = build_envelope(
                schema_name="novasteel.heat-batch.v1", event_ts=planned_ts, ingest_ts=planned_ts,
                sequence=i + 1, source_id=source_id, plant_id=plant_id, asset_id="BE-EAF-01",
                scenario_id=manifest.scenario_id, correlation_id=correlation_id, seed=manifest.root_seed,
                rng=rng,
                payload={
                    "material_id": f"BILLET-BE-{start_time:%y%m%d}-{i:03d}",
                    "heat_id": heat_id,
                    "operation_id": f"EAF-{batch.batch_id}",
                    "grade_code": rng.choice(grade_codes),
                    "planned_ts": iso(planned_ts),
                    "urgent": batch.urgent,
                    "tonnage": batch.tonnage,
                    "energyMwh": energy_mwh,
                },
            )
            records.append(envelope)
        return records

    rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, "LUX-CC-01", "heat-batch")
    for i, batch in enumerate(energy_summary.get("_batches", [])):
        heat_id = f"H-LUX-{start_time:%y%m%d}-{i:04d}"
        planned_ts = start_time + timedelta(minutes=15 * batch.planned_interval)
        envelope = build_envelope(
            schema_name="novasteel.heat-batch.v1", event_ts=planned_ts, ingest_ts=planned_ts,
            sequence=i + 1, source_id=source_id, plant_id=plant_id, asset_id="LUX-RHF-01",
            scenario_id=manifest.scenario_id, correlation_id=correlation_id, seed=manifest.root_seed,
            rng=rng,
            payload={
                "material_id": f"COIL-LUX-{start_time:%y%m%d}-{i:03d}",
                "heat_id": heat_id,
                "operation_id": f"REHEAT-{batch.batch_id}",
                "grade_code": rng.choice(grade_codes),
                "planned_ts": iso(planned_ts),
                "urgent": batch.urgent,
            },
        )
        records.append(envelope)
    return records


def _generate_quality_dataset(manifest, window_hours, gateway, correlation_id, source_id, fast=False):
    plant_id = manifest.plant_id
    asset_id = "LUX-HSM-01"
    start_time = manifest.start_time
    quality_cfg = manifest.quality
    drift_active = quality_cfg.get("drift_active", False)
    latent_hours = manifest.quality_latent_hours(fast)
    full_drift_hours = manifest.quality_full_drift_hours(fast)
    warning_lead_hours = quality_cfg.get("warning_lead_hours", 2.0)

    rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id, "quality-samples")
    num_samples = 20
    step_hours = window_hours / num_samples

    records = []
    first_off_spec_ts = None
    yield_before = quality_model.predicted_first_pass_yield(0.0)
    yield_after = yield_before

    for i in range(num_samples):
        elapsed_hours = i * step_hours
        event_ts = start_time + timedelta(hours=elapsed_hours)
        drift = quality_model.drift_state_at(elapsed_hours, latent_hours=latent_hours,
                                              full_drift_hours=full_drift_hours) if drift_active else \
            quality_model.DriftState(0.0, 0.0, 0.0, 0.0)

        ceq = quality_model.carbon_equivalent(0.08 + drift.carbon_equivalent_shift_pct, 1.4)
        tensile = 830.0 - drift.coiling_temp_bias_c * 0.8 + rng.uniform(-6, 6)
        off_spec = rng.random() < drift.off_spec_probability
        result_status = "FAIL" if off_spec else "PASS"
        if off_spec and first_off_spec_ts is None:
            first_off_spec_ts = event_ts

        ingest_ts = event_ts + timedelta(milliseconds=gateway.jitter_ms())
        envelope = build_envelope(
            schema_name="novasteel.quality-measurement.v1", event_ts=event_ts, ingest_ts=ingest_ts,
            sequence=gateway.next_sequence(), source_id=source_id, plant_id=plant_id, asset_id=asset_id,
            scenario_id=manifest.scenario_id, correlation_id=correlation_id, seed=manifest.root_seed,
            rng=rng,
            payload={
                "type": "quality.measurement",
                "material_id": f"COIL-LUX-{start_time:%y%m%d}-{i:03d}",
                "heat_id": f"H-LUX-{start_time:%y%m%d}-{i:04d}",
                "grade_code": "NS-AUTO-DP780",
                "sample_id": f"LAB-{start_time:%y%m%d}-{i:04d}",
                "characteristic_code": "tensile_strength",
                "value": round(tensile, 1),
                "unit": "MPa",
                "lower_spec_limit": 780.0,
                "upper_spec_limit": 930.0,
                "measurement_method": "SYNTHETIC-LAB-TENSILE",
                "result_status": result_status,
                "carbon_equivalent": ceq,
                "coiling_temperature_bias_c": round(drift.coiling_temp_bias_c, 2),
            },
        )
        records.append(envelope)

        if elapsed_hours >= full_drift_hours:
            yield_before = quality_model.predicted_first_pass_yield(drift.off_spec_probability)

    yield_after = quality_model.predicted_first_pass_yield(0.0)

    warning_ts = start_time + timedelta(hours=max(latent_hours - warning_lead_hours, 0.0)) if drift_active else None

    summary = {
        "quality_drift_active": drift_active,
        "quality_warning_ts": iso(warning_ts) if warning_ts else None,
        "quality_first_off_spec_ts": iso(first_off_spec_ts) if first_off_spec_ts else None,
        "quality_predicted_yield_before": yield_before,
        "quality_predicted_yield_after": yield_after,
    }
    return records, summary


def _generate_model_inference(manifest, window_hours, gateway, correlation_id, source_id):
    plant_id = manifest.plant_id
    asset_id = "LUX-BF-01"
    start_time = manifest.start_time
    eval_ts = start_time + timedelta(hours=window_hours)
    rng = child_random(manifest.root_seed, manifest.scenario_id, plant_id, asset_id, "model-inference")

    records = []
    lining_summary = {}
    for sector in manifest.hearth_sectors:
        min_safe = manifest.campaign["min_safe_thickness_mm"]
        thickness_at_eval = manifest.thickness_at_eval_mm(sector)
        degradation_rate = manifest.degradation_rate(sector)
        rul_p50 = furnace_model.remaining_useful_life_days(thickness_at_eval, min_safe, degradation_rate)
        p10, p90 = furnace_model.rul_confidence_band(rul_p50)
        risk = furnace_model.risk_score(rul_p50)
        severity = furnace_model.severity_for_rul(rul_p50)
        component_id = f"HEARTH-SECTOR-{sector}"

        ingest_ts = eval_ts + timedelta(milliseconds=gateway.jitter_ms())
        envelope = build_envelope(
            schema_name="novasteel.model-inference.v1", event_ts=eval_ts, ingest_ts=ingest_ts,
            sequence=gateway.next_sequence(), source_id=source_id, plant_id=plant_id, asset_id=asset_id,
            scenario_id=manifest.scenario_id, correlation_id=correlation_id, seed=manifest.root_seed,
            rng=rng,
            payload={
                "type": "model.inference",
                "inference_id": f"INF-LUX-BF01-{eval_ts:%Y%m%dT%H%M}Z-{sector}",
                "model_id": "lining-rul-piml",
                "model_version": "1.3.0-demo",
                "feature_snapshot_ts": iso(eval_ts),
                "component_id": component_id,
                "prediction": {
                    "remaining_useful_life_days_p50": round(rul_p50, 2),
                    "remaining_useful_life_days_p10": p10,
                    "remaining_useful_life_days_p90": p90,
                    "estimated_minimum_lining_mm": manifest.campaign["min_safe_thickness_mm"],
                    "risk_score": risk,
                    "severity": severity,
                },
                "top_factors": [
                    {"feature": "heat_flux_6h_slope", "contribution": 0.29},
                    {"feature": "sector_to_ring_temp_delta", "contribution": 0.24},
                    {"feature": "cooling_efficiency_residual", "contribution": 0.18},
                ],
                "label": lining_state_for_rul(rul_p50),
            },
        )
        records.append(envelope)

        if sector == config.DEGRADED_SECTOR or sector == manifest.expected_assertions.get("component_id", "").split("-")[-1]:
            lining_summary = {
                "lining_rul_p50_days": round(rul_p50, 2),
                "lining_rul_p10_days": p10,
                "lining_rul_p90_days": p90,
                "lining_risk_score": risk,
                "lining_component_id": component_id,
                "lining_state": lining_state_for_rul(rul_p50),
            }
    if not lining_summary:
        # Fall back to the primary sector if no explicit target matched (e.g. healthy baseline).
        sector = manifest.hearth_sectors[0]
        thickness_at_eval = manifest.thickness_at_eval_mm(sector)
        rul_p50 = furnace_model.remaining_useful_life_days(
            thickness_at_eval, manifest.campaign["min_safe_thickness_mm"], manifest.degradation_rate(sector))
        p10, p90 = furnace_model.rul_confidence_band(rul_p50)
        lining_summary = {
            "lining_rul_p50_days": round(rul_p50, 2),
            "lining_rul_p10_days": p10,
            "lining_rul_p90_days": p90,
            "lining_risk_score": furnace_model.risk_score(rul_p50),
            "lining_component_id": f"HEARTH-SECTOR-{sector}",
            "lining_state": lining_state_for_rul(rul_p50),
        }
    return records, lining_summary


def _generate_maintenance_dataset(manifest, window_hours, lining_summary, start_time) -> list[dict]:
    records = []
    rng = child_random(manifest.root_seed, manifest.scenario_id, manifest.plant_id, "LUX-BF-01", "maintenance")
    if lining_summary.get("lining_state") in {"watch", "degraded", "critical"}:
        detected_ts = start_time + timedelta(hours=window_hours * 0.6)
        sector = lining_summary["lining_component_id"].split("-")[-1]
        records.append(maintenance_model.build_maintenance_event(
            work_order_id=f"WO-DEMO-LUX-{start_time:%y%m%d}-{sector}", asset_id="LUX-BF-01",
            failure_mode="refractory_wear", detected_ts=detected_ts, sector=sector, rng=rng,
        ))
    if manifest.quality.get("drift_active"):
        detected_ts = start_time + timedelta(hours=min(window_hours * 0.8, window_hours))
        records.append(maintenance_model.build_maintenance_event(
            work_order_id=f"WO-DEMO-HSM-{start_time:%y%m%d}", asset_id="LUX-HSM-01",
            failure_mode="burner_imbalance", detected_ts=detected_ts, sector=None, rng=rng,
        ))
    return records


_SEVERITY_TO_ALARM = {"HIGH": "CRITICAL", "MEDIUM": "WARNING", "LOW": "INFO"}


def _generate_alarm_dataset(manifest, window_hours, lining_summary, start_time, gateway,
                             correlation_id, source_id) -> list[dict]:
    """Alert lifecycle event for the lining prediction (docs section 4.4):
    ``OPEN -> ACKNOWLEDGED -> WORK_ORDER_LINKED -> MITIGATED -> CLOSED``.
    Only ``watch``/``degraded``/``critical`` lining states raise an alert;
    a healthy baseline run raises none.
    """
    severity = _SEVERITY_TO_ALARM.get(
        furnace_model.severity_for_rul(lining_summary["lining_rul_p50_days"]), "INFO")
    if lining_summary.get("lining_state") not in {"watch", "degraded", "critical"}:
        return []

    rng = child_random(manifest.root_seed, manifest.scenario_id, manifest.plant_id,
                        lining_summary["lining_component_id"], "alarm")
    event_ts = start_time + timedelta(hours=window_hours)
    ingest_ts = event_ts + timedelta(milliseconds=gateway.jitter_ms())
    envelope = build_envelope(
        schema_name="novasteel.alarm.v1", event_ts=event_ts, ingest_ts=ingest_ts,
        sequence=gateway.next_sequence(), source_id=source_id, plant_id=manifest.plant_id,
        asset_id="LUX-BF-01", scenario_id=manifest.scenario_id, correlation_id=correlation_id,
        seed=manifest.root_seed, rng=rng,
        payload={
            "type": "alarm.event",
            "alert_id": f"ALERT-{lining_summary['lining_component_id']}-{start_time:%y%m%d}",
            "component_id": lining_summary["lining_component_id"],
            "severity": severity,
            "status": "OPEN",
            "message": f"Demo synthetic warning: {lining_summary['lining_component_id']} predicted "
                       f"RUL P50 {lining_summary['lining_rul_p50_days']} days "
                       f"(risk {lining_summary['lining_risk_score']}).",
            "reason": "lining_rul_below_21d_threshold",
            "actor_type": "SYSTEM",
            "transitioned_at": iso(event_ts),
            "confidence": lining_summary["lining_risk_score"],
            "linked_inference_component_id": lining_summary["lining_component_id"],
        },
    )
    return [envelope]


def _generate_operator_knowledge_dataset(manifest, start_time) -> list[dict]:
    rng = child_random(manifest.root_seed, manifest.scenario_id, manifest.plant_id, "knowledge", "session")
    sector = manifest.hearth_sectors[-1] if manifest.hearth_sectors else "07"
    interview_id = f"IVW-DEMO-{manifest.scenario_id}"
    session = knowledge_model.build_interview_session(
        interview_id=interview_id, plant_id=manifest.plant_id, operator_id="OP-DEMO-014",
        role="Furnace Operator", scenario_id=manifest.scenario_id, start_ts=start_time, rng=rng,
    )
    segments = knowledge_model.build_knowledge_segments(
        interview_id=interview_id, start_ts=start_time, sector=sector, rng=rng,
    )
    return [session] + segments


def _finalize_truth_ledger(truth_ledger, manifest, window_hours, lining_summary, quality_summary,
                            energy_summary, start_time) -> None:
    eval_ts = iso(start_time + timedelta(hours=window_hours))
    rul_p50 = lining_summary["lining_rul_p50_days"]
    anomaly_id = manifest.anomalies[0]["anomaly_id"] if manifest.anomalies else None
    truth_ledger.add(TruthRecord(
        record_ts=eval_ts,
        plant_id=manifest.plant_id,
        asset_id="LUX-BF-01",
        component_id=lining_summary["lining_component_id"],
        lining_state=lining_summary["lining_state"],
        rul_days=rul_p50,
        failure_within_21d=1 if rul_p50 <= 21 else 0,
        sensor_fault_type="none",
        quality_outcome="rework" if quality_summary.get("quality_first_off_spec_ts") else "pass",
        quality_drift_active=bool(quality_summary.get("quality_drift_active")),
        energy_schedule_optimality_gap=energy_summary.get("energy_schedule_optimality_gap", 0.0),
        anomaly_id=anomaly_id,
    ))
