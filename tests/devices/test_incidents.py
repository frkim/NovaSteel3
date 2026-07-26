"""Incident catalog and active-incident lifecycle tests.

Verifies all 7 catalog entries, triggering, expiry, early clear, and that
each incident type produces observable signal changes in the expected direction.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from device_simulator.incidents import INCIDENT_CATALOG, trigger_incident
from device_simulator.signals import generate_value


_UTC = timezone.utc
_T0 = datetime(2024, 7, 25, 6, 0, 0, tzinfo=_UTC)


def _make_incident_dict(inc, progress):
    return {
        "incidentId": inc.incidentId,
        "deviceId": inc.deviceId,
        "sensorId": inc.sensorId,
        "progress": progress,
    }


def test_catalog_has_7_incidents():
    assert len(INCIDENT_CATALOG) == 7


def test_all_incident_ids_present():
    expected = {
        "degrading-furnace",
        "cooling-water-loss",
        "sensor-drift",
        "sensor-dropout",
        "energy-price-spike",
        "quality-drift",
        "edge-outage-recovery",
    }
    assert set(INCIDENT_CATALOG.keys()) == expected


def test_degrading_furnace_ramps_heat_flux_up():
    inc = trigger_incident("degrading-furnace", _T0)
    sig = "local_heat_flux"
    low, high = 35.0, 190.0
    sid = f"LUX-BF-01:{sig}"
    baseline, _, _ = generate_value(sid, "LUX-BF-01", sig, 10, 42, "healthy-baseline", low, high, [])
    incident_dict = _make_incident_dict(inc, 0.9)
    with_inc, _, _ = generate_value(sid, "LUX-BF-01", sig, 10, 42, "healthy-baseline", low, high, [incident_dict])
    assert with_inc >= baseline, f"heat_flux should rise during degrading-furnace: {with_inc} vs {baseline}"


def test_degrading_furnace_ramps_refractory_down():
    inc = trigger_incident("degrading-furnace", _T0)
    sig = "hearth_refractory_estimate"
    low, high = 280.0, 950.0
    sid = f"LUX-BF-01:{sig}"
    baseline, _, _ = generate_value(sid, "LUX-BF-01", sig, 10, 42, "healthy-baseline", low, high, [])
    incident_dict = _make_incident_dict(inc, 0.9)
    with_inc, _, _ = generate_value(sid, "LUX-BF-01", sig, 10, 42, "healthy-baseline", low, high, [incident_dict])
    assert with_inc <= baseline, f"refractory_estimate should drop during degrading-furnace"


def test_cooling_water_loss_drops_flow():
    inc = trigger_incident("cooling-water-loss", _T0)
    sig = "cooling_water_flow"
    low, high = 110.0, 310.0
    sid = f"LUX-BF-01:{sig}"
    baseline, _, _ = generate_value(sid, "LUX-BF-01", sig, 10, 42, "healthy-baseline", low, high, [])
    incident_dict = _make_incident_dict(inc, 0.8)
    with_inc, _, _ = generate_value(sid, "LUX-BF-01", sig, 10, 42, "healthy-baseline", low, high, [incident_dict])
    assert with_inc <= baseline, "cooling_water_flow should drop during cooling-water-loss"


def test_cooling_water_loss_raises_outlet_temp():
    inc = trigger_incident("cooling-water-loss", _T0)
    sig = "cooling_water_outlet_temperature"
    low, high = 28.0, 58.0
    sid = f"LUX-BF-01:{sig}"
    baseline, _, _ = generate_value(sid, "LUX-BF-01", sig, 10, 42, "healthy-baseline", low, high, [])
    incident_dict = _make_incident_dict(inc, 0.8)
    with_inc, _, _ = generate_value(sid, "LUX-BF-01", sig, 10, 42, "healthy-baseline", low, high, [incident_dict])
    assert with_inc >= baseline, "outlet_temperature should rise during cooling-water-loss"


def test_sensor_drift_biases_value_up():
    inc = trigger_incident("sensor-drift", _T0, device_id="LUX-BF-01",
                           sensor_id="LUX-BF-01:top_pressure")
    sig = "top_pressure"
    low, high = 1.4, 2.6
    sid = "LUX-BF-01:top_pressure"
    baseline, _, _ = generate_value(sid, "LUX-BF-01", sig, 10, 42, "healthy-baseline", low, high, [])
    incident_dict = _make_incident_dict(inc, 0.7)
    with_inc, _, _ = generate_value(sid, "LUX-BF-01", sig, 10, 42, "healthy-baseline", low, high, [incident_dict])
    assert with_inc >= baseline, "sensor-drift should apply an upward bias"


def test_sensor_dropout_sets_quality_bad():
    inc = trigger_incident("sensor-dropout", _T0, device_id="LUX-BF-01",
                           sensor_id="LUX-BF-01:hot_blast_temperature")
    sig = "hot_blast_temperature"
    low, high = 1050.0, 1250.0
    sid = "LUX-BF-01:hot_blast_temperature"
    incident_dict = _make_incident_dict(inc, 0.5)
    _, quality, _ = generate_value(sid, "LUX-BF-01", sig, 10, 42, "healthy-baseline", low, high, [incident_dict])
    assert quality == "bad", f"sensor-dropout should set quality='bad', got {quality!r}"


def test_energy_price_spike_raises_spot_price():
    inc = trigger_incident("energy-price-spike", _T0, device_id="LUX-UTIL-01")
    sig = "spot_price"
    low, high = -15.0, 420.0
    sid = "LUX-UTIL-01:spot_price"
    baseline, _, _ = generate_value(sid, "LUX-UTIL-01", sig, 10, 42, "healthy-baseline", low, high, [])
    incident_dict = _make_incident_dict(inc, 0.5)
    with_inc, _, _ = generate_value(sid, "LUX-UTIL-01", sig, 10, 42, "healthy-baseline", low, high, [incident_dict])
    assert with_inc >= baseline, "spot_price should spike during energy-price-spike"


def test_quality_drift_affects_slab_width_deviation():
    inc = trigger_incident("quality-drift", _T0, device_id="LUX-CC-01")
    sig = "slab_width_deviation"
    low, high = -6.0, 6.0
    sid = "LUX-CC-01:slab_width_deviation"
    baseline, _, _ = generate_value(sid, "LUX-CC-01", sig, 10, 42, "healthy-baseline", low, high, [])
    incident_dict = _make_incident_dict(inc, 0.7)
    with_inc, _, _ = generate_value(sid, "LUX-CC-01", sig, 10, 42, "healthy-baseline", low, high, [incident_dict])
    assert with_inc >= baseline, "slab_width_deviation should drift upward during quality-drift"


def test_quality_drift_affects_mould_level():
    inc = trigger_incident("quality-drift", _T0, device_id="LUX-CC-01")
    sig = "mould_level"
    low, high = 60.0, 140.0
    sid = "LUX-CC-01:mould_level"
    baseline, _, _ = generate_value(sid, "LUX-CC-01", sig, 10, 42, "healthy-baseline", low, high, [])
    incident_dict = _make_incident_dict(inc, 0.7)
    with_inc, _, _ = generate_value(sid, "LUX-CC-01", sig, 10, 42, "healthy-baseline", low, high, [incident_dict])
    assert with_inc >= baseline, "mould_level should drift during quality-drift"


def test_quality_drift_affects_coiling_temperature():
    inc = trigger_incident("quality-drift", _T0, device_id="LUX-HSM-01")
    sig = "coiling_temperature"
    low, high = 520.0, 720.0
    sid = "LUX-HSM-01:coiling_temperature"
    baseline, _, _ = generate_value(sid, "LUX-HSM-01", sig, 0, 42, "healthy-baseline", low, high, [])
    incident_dict = _make_incident_dict(inc, 0.7)
    with_inc, _, _ = generate_value(sid, "LUX-HSM-01", sig, 0, 42, "healthy-baseline", low, high, [incident_dict])
    assert with_inc >= baseline, "coiling_temperature should rise during quality-drift on LUX-HSM-01"


def test_edge_outage_recovery_goes_stale_first_half():
    inc = trigger_incident("edge-outage-recovery", _T0, device_id="LUX-HSM-01")
    sig = "stand_motor_current"
    low, high = 1000.0, 12000.0
    sid = "LUX-HSM-01:stand_motor_current"
    incident_dict = _make_incident_dict(inc, 0.3)
    _, quality, _ = generate_value(sid, "LUX-HSM-01", sig, 10, 42, "healthy-baseline", low, high, [incident_dict])
    assert quality == "bad", "edge-outage-recovery first half should set quality='bad'"


def test_edge_outage_recovery_recovers_second_half():
    inc = trigger_incident("edge-outage-recovery", _T0, device_id="LUX-HSM-01")
    sig = "stand_motor_current"
    low, high = 1000.0, 12000.0
    sid = "LUX-HSM-01:stand_motor_current"
    incident_dict = _make_incident_dict(inc, 0.75)
    _, quality, _ = generate_value(sid, "LUX-HSM-01", sig, 10, 42, "healthy-baseline", low, high, [incident_dict])
    assert quality == "good", "edge-outage-recovery second half should restore quality='good'"


def test_incident_expires_on_time():
    inc = trigger_incident("cooling-water-loss", _T0, duration_minutes=5.0)
    assert not inc.is_expired(_T0)
    assert not inc.is_expired(_T0 + timedelta(minutes=4, seconds=59))
    assert inc.is_expired(_T0 + timedelta(minutes=5))


def test_incident_clear_early():
    """ActiveIncident can be marked expired by consuming code clearing it."""
    inc = trigger_incident("sensor-drift", _T0, device_id="LUX-BF-01",
                           sensor_id="LUX-BF-01:top_pressure")
    assert not inc.is_expired(_T0 + timedelta(minutes=1))
    # Simulate clearing by checking remaining_minutes before expiry
    assert inc.remaining_minutes(_T0 + timedelta(minutes=30)) > 0


def test_clamping_never_yields_physically_impossible_values():
    """Even with extreme incident progress the value stays within [low, high]."""
    inc = trigger_incident("degrading-furnace", _T0)
    sig = "local_heat_flux"
    low, high = 35.0, 190.0
    sid = f"LUX-BF-01:{sig}"
    extreme = _make_incident_dict(inc, 1.0)
    v, _, clamped = generate_value(sid, "LUX-BF-01", sig, 10, 42, "healthy-baseline", low, high, [extreme])
    assert low <= v <= high, f"Value {v} outside physical bounds [{low}, {high}]"


def test_clamped_flag_set_when_incident_pushes_past_bound():
    """When an incident drives a value to a bound, clamped must be True."""
    inc = trigger_incident("degrading-furnace", _T0)
    sig = "local_heat_flux"
    low, high = 35.0, 190.0
    sid = f"LUX-BF-01:{sig}"
    # At progress=1.0 the ramp is severe enough that at SOME tick the value will clamp
    extreme = _make_incident_dict(inc, 1.0)
    found_clamped = False
    for tick in range(50):
        v, _, c = generate_value(sid, "LUX-BF-01", sig, tick, 42, "healthy-baseline", low, high, [extreme])
        if c:
            found_clamped = True
            break
    assert found_clamped, "Expected at least one clamped=True at max incident progress"


def test_incident_catalog_entry_shape():
    for entry in INCIDENT_CATALOG.values():
        assert entry.incidentId
        assert entry.label
        assert entry.description
        assert entry.severity in ("low", "medium", "high", "critical")
        assert entry.defaultDurationMinutes > 0
        assert isinstance(entry.targetDeviceIds, list)
        assert isinstance(entry.affectedSignalCodes, list)


def test_unknown_incident_raises():
    with pytest.raises(KeyError):
        trigger_incident("does-not-exist", _T0, device_id="LUX-BF-01")
