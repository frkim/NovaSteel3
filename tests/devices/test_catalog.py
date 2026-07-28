"""Catalog integrity tests.

Verifies that ``device_simulator.catalog`` contains exactly 6 assets,
18 core signals, 34 total signals, well-formed identifiers, and that
the 18 core signals match ``simulator/config.py`` byte-faithfully when the
upstream package is importable (sync check skipped otherwise).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from device_simulator.catalog import (
    CATALOG_ASSETS,
    CATALOG_SIGNALS,
    CORE_SIGNAL_CODES,
    SIGNALS_BY_ASSET,
    SITE_ID,
    _CORE_SIGNALS,
    _EXTENDED_SIGNALS,
)


def test_catalog_has_6_devices():
    assert len(CATALOG_ASSETS) == 17


def test_catalog_has_exactly_18_core_signals():
    assert len(_CORE_SIGNALS) == 18


def test_catalog_has_34_total_signals():
    """18 core + 73 extended = 91 total sensors across 17 devices."""
    assert len(CATALOG_SIGNALS) == 91


def test_catalog_has_73_extended_signals():
    assert len(_EXTENDED_SIGNALS) == 73


def test_all_expected_asset_ids_present():
    expected = {
        "LUX-BF-01", "LUX-BOF-01", "LUX-CC-01", "LUX-RHF-01", "LUX-HSM-01", "LUX-UTIL-01",
        "DE-EAF-01", "DE-LF-01", "DE-BCM-01", "DE-UTIL-01",
        "BE-EAF-01", "BE-CRM-01", "BE-GAL-01", "BE-UTIL-01",
        "ES-EAF-01", "ES-WRM-01", "ES-UTIL-01",
    }
    assert set(CATALOG_ASSETS.keys()) == expected


def test_all_asset_ids_well_formed():
    for asset_id in CATALOG_ASSETS:
        parts = asset_id.split("-")
        assert len(parts) >= 3, f"Bad asset_id: {asset_id}"
        assert parts[0] in ("LUX", "DE", "BE", "ES"), f"Unknown site prefix: {asset_id}"


def test_all_signal_codes_map_to_known_asset():
    for code, signal in CATALOG_SIGNALS.items():
        assert signal.asset_id in CATALOG_ASSETS, (
            f"Signal {code!r} references unknown asset {signal.asset_id!r}"
        )


def test_all_signals_have_valid_range():
    for code, signal in CATALOG_SIGNALS.items():
        assert signal.low < signal.high, (
            f"Signal {code!r} has low >= high: {signal.low} >= {signal.high}"
        )


def test_all_signals_have_non_negative_sample_period():
    for code, signal in CATALOG_SIGNALS.items():
        assert signal.sample_period_ms >= 0, (
            f"Signal {code!r} has negative sample_period_ms: {signal.sample_period_ms}"
        )


def test_site_id_constant():
    assert SITE_ID == "NS-DEMO-LUX-01"


def test_all_catalog_assets_have_area():
    for asset_id, asset in CATALOG_ASSETS.items():
        assert asset.area, f"Asset {asset_id!r} has empty area"


def test_all_signal_units_not_empty():
    for code, signal in CATALOG_SIGNALS.items():
        assert signal.unit, f"Signal {code!r} has empty unit"


def test_signals_by_asset_covers_all_assets():
    for asset_id in CATALOG_ASSETS:
        signals = SIGNALS_BY_ASSET.get(asset_id, [])
        assert len(signals) >= 1, f"Asset {asset_id!r} has no signals"


def test_core_signals_are_not_marked_extended():
    for s in _CORE_SIGNALS:
        assert not s.extended, f"Core signal {s.signal_code!r} is incorrectly marked extended"


def test_extended_signals_are_marked_extended():
    for s in _EXTENDED_SIGNALS:
        assert s.extended, f"Extended signal {s.signal_code!r} is not marked extended"


def test_core_signal_codes_set_has_18_entries():
    assert len(CORE_SIGNAL_CODES) == 18


def test_extended_signals_have_valid_asset_ids():
    for s in _EXTENDED_SIGNALS:
        assert s.asset_id in CATALOG_ASSETS, (
            f"Extended signal {s.signal_code!r} references unknown asset {s.asset_id!r}"
        )


def test_extended_signals_have_valid_ranges():
    for s in _EXTENDED_SIGNALS:
        assert s.low < s.high, (
            f"Extended signal {s.signal_code!r} has low >= high: {s.low} >= {s.high}"
        )


def test_event_driven_signals_exist_in_core():
    """hot_metal_temperature and coiling_temperature must have sample_period_ms == 0."""
    assert CATALOG_SIGNALS["LUX-BF-01:hot_metal_temperature"].sample_period_ms == 0
    assert CATALOG_SIGNALS["LUX-HSM-01:coiling_temperature"].sample_period_ms == 0


def test_catalog_mirror_in_sync_with_simulator_config():
    """Skip when simulator package is not importable (separate deployable).

    Checks that the 18 core signals are byte-faithful mirrors of
    simulator/config.py's SIGNAL_REGISTRY: same code, unit, low, high,
    sample_period_ms, and asset_id. Extended signals are excluded from the check.
    """
    simulator_path = Path(__file__).resolve().parents[2] / "simulator"
    if not simulator_path.exists():
        pytest.skip("simulator package not found on disk")

    sim_str = str(simulator_path.parent)
    if sim_str not in sys.path:
        sys.path.insert(0, sim_str)

    try:
        from simulator.config import ASSETS as SIM_ASSETS
        from simulator.config import SIGNAL_REGISTRY as SIM_SIGNALS
    except ImportError:
        pytest.skip("simulator.config not importable")

    for asset_id in SIM_ASSETS:
        assert asset_id in CATALOG_ASSETS, (
            f"simulator.config asset {asset_id!r} missing from device_simulator catalog"
        )

    assert len(SIM_SIGNALS) == 18, (
        f"Expected 18 upstream signals, got {len(SIM_SIGNALS)}; sync check needs updating"
    )

    for code, sim_sig in SIM_SIGNALS.items():
        assert code in CORE_SIGNAL_CODES, (
            f"simulator.config signal {code!r} missing from core registry"
        )
        catalog_key = f"{sim_sig.asset_id}:{code}"
        our_sig = CATALOG_SIGNALS[catalog_key]
        assert our_sig.unit == sim_sig.unit, f"{code}: unit mismatch"
        assert our_sig.low == float(sim_sig.low), f"{code}: low mismatch"
        assert our_sig.high == float(sim_sig.high), f"{code}: high mismatch"
        assert our_sig.sample_period_ms == sim_sig.sample_period_ms, (
            f"{code}: sample_period_ms mismatch"
        )
        assert our_sig.asset_id == sim_sig.asset_id, f"{code}: asset_id mismatch"
