"""Verify the BFF fallback ladder and prove no external network dependency.

Levels demonstrated (runbook section 6.1):
  * Local deterministic replay  -> committed simulator fixture
  * Cached interactive          -> alternate generated snapshot directory
  * Static/built-in fallback     -> in-code fallback datasets (all fixtures gone)
  * Integrity gate               -> tampered pack is rejected before serving

A socket guard blocks every non-loopback TCP connect for the whole run, so any
hidden outbound call would raise instead of silently succeeding.
"""
from __future__ import annotations

import shutil
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "bff-api" / "src"))
SCRATCH = Path(__file__).resolve().parent / "scratch"
SCRATCH.mkdir(parents=True, exist_ok=True)

# ---- Network guard: forbid any non-loopback connection for this process. ----
_LOOPBACK = {"127.0.0.1", "::1", "localhost"}
_real_connect = socket.socket.connect
_blocked: list[str] = []


def _guarded_connect(self, address):  # type: ignore[no-untyped-def]
    host = address[0] if isinstance(address, tuple) else str(address)
    if host not in _LOOPBACK:
        _blocked.append(str(address))
        raise OSError(f"BLOCKED non-loopback connect to {address}")
    return _real_connect(self, address)


socket.socket.connect = _guarded_connect  # type: ignore[assignment]

from bff_api.config import Settings, DemoMode  # noqa: E402
from bff_api import repository as repo_mod  # noqa: E402
from bff_api.repository import (  # noqa: E402
    DemoRepository,
    _fallback_datasets,
    _fallback_manifest,
)


def demo_settings(data_dir: str = "") -> Settings:
    return Settings(
        service_name="novasteel-bff-api",
        api_version="v1",
        environment="demo",
        demo_mode=DemoMode.LOCAL,
        data_namespace="NS-DEMO-LUX-01",
        cors_origins=("http://localhost:5000",),
        auth_mode="demo",
        demo_data_directory=data_dir,
    )


results: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    results.append((label, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))


# Level 1: committed simulator fixture (default local deterministic replay).
r1 = DemoRepository.load(demo_settings())
check("Level 1 local deterministic fixture loads", r1.source.startswith("simulator-fixture:"), r1.source)
check("Level 1 serves RUL P50 21.0 evidence",
      r1.summary_metrics.get("lining_rul_p50_days") == 21.0, str(r1.summary_metrics.get("lining_rul_p50_days")))
check("Level 1 furnace inventory present", any(f["assetId"] == "LUX-BF-01" for f in r1.furnaces()), "")

# Level 2: alternate cached snapshot directory (cached interactive).
genA = ROOT / "artifacts" / "demo-validation" / "scenario" / "genA"
r2 = DemoRepository.load(demo_settings(str(genA)))
check("Level 2 cached snapshot directory loads", "genA" in r2.source, r2.source)
check("Level 2 telemetry rows served", len(r2.telemetry_rows()) > 0, f"{len(r2.telemetry_rows())} rows")

# Level 3: built-in in-code fallback (simulate ALL fixtures missing).
missing = SCRATCH / "does-not-exist"
orig_default = repo_mod._DEFAULT_FIXTURE
try:
    repo_mod._DEFAULT_FIXTURE = missing  # type: ignore[attr-defined]
    r3 = DemoRepository.load(demo_settings(str(missing)))
finally:
    repo_mod._DEFAULT_FIXTURE = orig_default  # type: ignore[attr-defined]
check("Level 3 built-in fallback engages when packs are gone",
      r3.source == "built-in-fallback", r3.source)
check("Level 3 fallback still serves deterministic RUL 21.0 + tonnage 960",
      r3.summary_metrics.get("lining_rul_p50_days") == 21.0
      and r3.summary_metrics.get("energy_tonnage_before") == 960.0, "")
check("Built-in fallback datasets are non-empty", len(_fallback_datasets()) > 0 and bool(_fallback_manifest()), "")

# Integrity gate: a tampered pack must be rejected, not served.
tmp = SCRATCH / "tampered"
if tmp.exists():
    shutil.rmtree(tmp)
shutil.copytree(ROOT / "services" / "bff-api" / "fixtures" / "demo-full", tmp)
tele = tmp / "telemetry.ndjson"
tele.write_text(tele.read_text(encoding="utf-8") + '{"tampered":true}\n', encoding="utf-8")
rejected = False
try:
    DemoRepository.load(demo_settings(str(tmp)))
except ValueError as exc:
    rejected = "Checksum" in str(exc) or "checksum" in str(exc)
check("Integrity gate rejects a tampered fixture", rejected, "checksum mismatch raised")

# Exercise service-layer scoring/optimization under the network guard.
from bff_api.services import BffServices  # noqa: E402

svc = BffServices.create(demo_settings())
fc = svc.lining_forecast(asset_id="LUX-BF-01", correlation_id="net-guard")
check("Scoring worker runs fully offline (no network)", fc["value"] == 21.0, f"p50={fc['value']}")
sim = svc.simulate_energy(site="NS-DEMO-LUX-01", horizon_hours=24, scenario="evening-scarcity",
                          constraints={}, correlation_id="net-guard", actor="net-guard")
check("Optimizer runs fully offline (no network)",
      sim["hardConstraintViolations"] == 0 and sim["baseline"]["tonnage"] == sim["optimized"]["tonnage"], "")

check("No non-loopback network connection was attempted during the demo path",
      len(_blocked) == 0, f"blocked={_blocked}")

shutil.rmtree(SCRATCH, ignore_errors=True)

passed = sum(1 for _, ok, _ in results if ok)
print(f"\n==== fallback ladder + no-network: {passed}/{len(results)} checks passed ====")
sys.exit(0 if passed == len(results) else 1)
