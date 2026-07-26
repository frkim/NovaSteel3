# `device_simulator` — NovaSteel Live Device Simulator

Deterministic live device simulator runtime for the NovaSteel synthetic
industrial-steel decision-support demo. Mirrors the sensor estate described in
`docs/data/synthetic-data-and-simulators.md` and serves JSON payloads consumed
by the BFF and Analytics MFE.

## Purpose

Provides a FastAPI micro-service (and importable library) that:
- Streams realistic sensor waveforms for all 6 demo assets and 34 signals.
- Enforces **strong determinism**: `seed + scenario + tick_count → byte-identical output`.
- Supports 7 injectable incidents with time-varying, clamped effects.
- Exposes 6 demo scenarios pre-armed with incident sequences (`demo-full`,
  `edge-outage-recovery`, `energy-price-spike`, `healthy-baseline`,
  `lining-degradation-21d`, `quality-drift`).

## Module map

| Module | Responsibility |
|---|---|
| `catalog.py` | Frozen asset + signal registry (mirror of `simulator/config.py`; superset) |
| `registry.py` | `Device` / `Sensor` dataclasses built from the catalog |
| `signals.py` | Pure deterministic waveform generation per sensor per tick |
| `incidents.py` | Incident catalog + active-incident lifecycle |
| `engine.py` | `DeviceSimulatorEngine` — state machine, ring buffer, auto-advance |
| `series.py` | Window parsing, downsampling, normalisation, stats |
| `status.py` | Sensor status / trend / deviation derivation; device health score |
| `views.py` | **Frozen** JSON-serialisable dict shapes (contract with BFF/MFE) |
| `telemetry.py` | Structured logging + optional Azure Monitor OpenTelemetry bootstrap |
| `app.py` | FastAPI app exposing `/devices/…`, `/health/live`, `/health/ready` |

## Determinism guarantee

Given identical `(seed, scenario, tick_count)` the engine produces byte-for-byte
identical sensor values regardless of wall-clock time, Python process, or machine.
Child seeds are derived with `SHA-256(seed | scenario | sensorId)` using the first
64 bits, matching the project-wide derivation in `simulator/determinism.py`.
The simulated clock starts at `2024-07-25T06:00:00Z` and advances by
`tick_interval_seconds` per tick.

## Frozen response shapes

```
device       = {deviceId, site, area, description, status, sensorCount,
                activeIncidents, lastSampleAt, healthScore, uptimePct}
deviceDetail = device + {sensors: [sensor]}
sensor       = {sensorId, deviceId, signalCode, displayName, area, unit,
                low, high, samplePeriodMs, value, quality, status, trend,
                deviationPct, clamped, lastSampleAt}
series       = {sensorId, deviceId, displayName, unit, low, high, window,
                pointCount, points, normalizedPoints,
                stats: {min, max, mean, stdDev, last}}
incidentCatalogEntry = {incidentId, label, description, severity,
                        defaultDurationMinutes, targetDeviceIds,
                        affectedSignalCodes}
activeIncident = {activeIncidentId, incidentId, label, severity, deviceId,
                  sensorId, startedAt, endsAt, remainingMinutes, progress}
simulatorStatus = {state, scenario, seed, speedFactor, tickIntervalSeconds,
                   simulatedClock, elapsedHours, tickCount, deviceCount,
                   sensorCount, activeIncidents, availableScenarios,
                   availableIncidents, startedAt}
```

## Running standalone

```bash
# Using the project venv (already has fastapi/uvicorn):
PYTHONPATH=services/device-simulator/src \
  services/bff-api/.venv/Scripts/python.exe -m uvicorn \
  device_simulator.app:app --reload --port 8081

# Docker:
docker buildx build -t novasteelv3/device-simulator:dev --load services/device-simulator
docker run -p 8081:8080 novasteelv3/device-simulator:dev
```

## Running tests

```bash
cd 'D:\work\20260724 - Novasteel 3'
$env:PYTHONPATH = 'services\device-simulator\src'
services\bff-api\.venv\Scripts\python.exe -m pytest tests\devices -q
```
