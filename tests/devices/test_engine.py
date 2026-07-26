"""DeviceSimulatorEngine state machine and determinism tests."""

from __future__ import annotations

import pytest

from device_simulator.engine import DeviceSimulatorEngine, IllegalTransitionError
from device_simulator.registry import SENSORS


def _make_engine(t: float = 0.0) -> tuple[DeviceSimulatorEngine, list]:
    """Create an engine with a controllable clock."""
    clock_values = [t]

    def clock():
        return clock_values[0]

    eng = DeviceSimulatorEngine(tick_interval_seconds=5.0, clock=clock)
    return eng, clock_values


def test_engine_initial_state_stopped():
    eng, _ = _make_engine()
    assert eng._state == "stopped"
    assert eng._tick_count == 0


def test_start_transitions_to_running():
    eng, _ = _make_engine()
    eng.start(scenario="healthy-baseline", seed=42)
    assert eng._state == "running"


def test_pause_transitions_to_paused():
    eng, _ = _make_engine()
    eng.start(seed=42)
    eng.pause()
    assert eng._state == "paused"


def test_resume_transitions_to_running():
    eng, _ = _make_engine()
    eng.start(seed=42)
    eng.pause()
    eng.resume()
    assert eng._state == "running"


def test_stop_transitions_to_stopped():
    eng, _ = _make_engine()
    eng.start(seed=42)
    eng.stop()
    assert eng._state == "stopped"


def test_reset_transitions_to_stopped():
    eng, _ = _make_engine()
    eng.start(seed=42)
    for _ in range(5):
        eng.tick()
    eng.reset()
    assert eng._state == "stopped"
    assert eng._tick_count == 0


def test_illegal_pause_when_stopped_raises():
    eng, _ = _make_engine()
    with pytest.raises(IllegalTransitionError):
        eng.pause()


def test_illegal_resume_when_stopped_raises():
    eng, _ = _make_engine()
    with pytest.raises(IllegalTransitionError):
        eng.resume()


def test_illegal_stop_when_already_stopped_raises():
    eng, _ = _make_engine()
    with pytest.raises(IllegalTransitionError):
        eng.stop()


def test_illegal_pause_when_paused_raises():
    eng, _ = _make_engine()
    eng.start(seed=42)
    eng.pause()
    with pytest.raises(IllegalTransitionError):
        eng.pause()


def test_determinism_two_engines_same_seed():
    eng_a, _ = _make_engine()
    eng_b, _ = _make_engine()
    eng_a.start(scenario="healthy-baseline", seed=12345)
    eng_b.start(scenario="healthy-baseline", seed=12345)
    for _ in range(10):
        eng_a.tick()
        eng_b.tick()
    for sid in SENSORS:
        buf_a = list(eng_a._buffers[sid])
        buf_b = list(eng_b._buffers[sid])
        assert buf_a == buf_b, f"Buffer mismatch for sensor {sid}"


def test_determinism_different_seeds_differ():
    eng_a, _ = _make_engine()
    eng_b, _ = _make_engine()
    eng_a.start(seed=111)
    eng_b.start(seed=999)
    for _ in range(5):
        eng_a.tick()
        eng_b.tick()
    # At least some sensor should differ
    any_different = any(
        list(eng_a._buffers[sid]) != list(eng_b._buffers[sid])
        for sid in SENSORS
    )
    assert any_different, "Different seeds should produce different sensor data"


def test_ring_buffer_never_exceeds_cap():
    eng, _ = _make_engine()
    eng.start(seed=1)
    for _ in range(1500):
        eng.tick()
    for sid in SENSORS:
        assert len(eng._buffers[sid]) <= 1440, (
            f"Buffer for {sid} exceeded cap: {len(eng._buffers[sid])}"
        )


def test_event_driven_signals_emit_at_reduced_cadence():
    """Sensors with sample_period_ms == 0 must emit only once per simulated hour
    (every 720 ticks at 5s/tick), not on every tick."""
    eng, _ = _make_engine()
    eng.start(seed=42)
    # Run 719 ticks — just before the first event emission after tick 0
    # Tick 0 emits (0 % 720 == 0), ticks 1..718 do NOT emit
    for _ in range(719):
        eng.tick()

    event_driven_sids = [
        sid for sid, s in SENSORS.items() if s.samplePeriodMs == 0
    ]
    assert event_driven_sids, "Expected at least two event-driven sensors"

    for sid in event_driven_sids:
        # Should have exactly 1 sample (from tick 0 only)
        assert len(eng._buffers[sid]) == 1, (
            f"Event-driven sensor {sid} should have 1 sample after 719 ticks, "
            f"got {len(eng._buffers[sid])}"
        )


def test_event_driven_sensors_not_flagged_stale_by_engine():
    """After running 100 ticks (8min 20s sim), event-driven sensors' status
    must not be 'stale' — sample_period_ms=0 disables the timing gate."""
    eng, _ = _make_engine()
    eng.start(seed=42)
    for _ in range(100):
        eng.tick()
    svs = eng.sensors(device_id="LUX-BF-01")
    hot_metal = next(s for s in svs if s["signalCode"] == "hot_metal_temperature")
    assert hot_metal["status"] != "stale", (
        "hot_metal_temperature (period=0) must not be 'stale' while running"
    )


def test_speed_factor_change():
    eng, _ = _make_engine()
    eng.start(seed=42)
    eng.set_speed(5.0)
    assert eng._speed_factor == 5.0


def test_scenario_change_requires_stopped():
    eng, _ = _make_engine()
    eng.start(seed=42)
    with pytest.raises(IllegalTransitionError):
        eng.set_scenario("quality-drift")


def test_scenario_change_when_stopped():
    eng, _ = _make_engine()
    eng.set_scenario("energy-price-spike")
    assert eng._scenario == "energy-price-spike"


def test_trigger_incident_returns_active_incident_view():
    eng, _ = _make_engine()
    eng.start(seed=42)
    result = eng.trigger_incident("degrading-furnace")
    assert "activeIncidentId" in result
    assert result["incidentId"] == "degrading-furnace"


def test_clear_incident_removes_it():
    eng, _ = _make_engine()
    eng.start(seed=42)
    result = eng.trigger_incident("degrading-furnace")
    aid = result["activeIncidentId"]
    eng.clear_incident(aid)
    status = eng.status()
    active_ids = [ai["activeIncidentId"] for ai in status["activeIncidents"]]
    assert aid not in active_ids


def test_clear_unknown_incident_raises():
    eng, _ = _make_engine()
    with pytest.raises(KeyError):
        eng.clear_incident("does-not-exist")


def test_auto_advance_catch_up():
    """Engine auto-advances ticks based on wall-clock delta."""
    eng, cv = _make_engine(t=0.0)
    eng.start(seed=42, speed_factor=1.0)
    assert eng._tick_count == 0
    # Advance wall clock by 50 seconds → 10 ticks at 5s/tick
    cv[0] = 50.0
    eng.status()
    assert eng._tick_count == 10
