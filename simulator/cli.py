"""NovaSteel simulator command-line interface.

Subcommands
-----------
list-scenarios   List available scenario manifests.
generate         Generate one scenario's datasets to a local output directory.
demo             One-command fast full-demo generation (alias for
                 ``generate --scenario demo-full --fast``).
publish          Paced live publish of a generated dataset to an HTTP sink.
generate-reference  Emit the reference (dimension) data the medallion
                 bronze-to-silver notebook resolves every event against.
validate         Run contract/physics/scenario-assertion validators against a run.
checksum         Recompute/verify a run's checksums.json.
reset            Delete a run's generated output (never touches manifests).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from simulator.checksum import verify_checksums, write_checksums
from simulator.generator import DATASET_NAMES, generate_run
from simulator.reset import reset_run_directory
from simulator.scenario import list_scenarios, load_manifest
from simulator.sink_http import publish_ndjson
from simulator import contract_projection as proj
from simulator.analytics import (
    generate_analytical_run,
    list_analytical_scenarios,
    load_analytical_manifest,
)
from simulator.fabric_operational import export_operational_pack
from simulator.reference_data import export_reference_data
from simulator.validators import contract_schema as contract_schema_validator
from simulator.validators.contract import validate_envelopes
from simulator.validators.gold_contract import validate_analytical_run
from simulator.validators.physics import validate_furnace_physics
from simulator.validators.scenario_assertions import validate_scenario
from simulator.writer import read_ndjson

DEFAULT_OUT_ROOT = Path("output")
_REPO_ROOT = Path(__file__).resolve().parents[1]


def _default_out_dir(scenario_id: str) -> Path:
    return DEFAULT_OUT_ROOT / scenario_id


def cmd_list_scenarios(args: argparse.Namespace) -> int:
    for scenario_id in list_scenarios():
        manifest = load_manifest(scenario_id)
        print(f"{scenario_id}\tseed={manifest.root_seed}\t{manifest.raw.get('description', '')}")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.scenario)
    out_dir = Path(args.out) if args.out else _default_out_dir(manifest.scenario_id)
    result = generate_run(manifest, out_dir=out_dir, fast=args.fast, fmt=args.format)
    print(f"Generated scenario {manifest.scenario_id!r} (seed={manifest.root_seed}) into {out_dir}")
    run_manifest = json.loads(result.run_manifest_path.read_text(encoding="utf-8"))
    for name, count in run_manifest["row_counts"].items():
        print(f"  {name}: {count} rows")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    args.scenario = "demo-full"
    args.fast = True
    args.out = args.out or str(DEFAULT_OUT_ROOT / "demo")
    return cmd_generate(args)


def cmd_list_analytical_scenarios(args: argparse.Namespace) -> int:
    for scenario_id in list_analytical_scenarios():
        scenario = load_analytical_manifest(scenario_id)
        print(f"{scenario_id}\tseed={scenario.root_seed}\t{scenario.raw.get('description', '')}")
    return 0


def cmd_generate_analytics(args: argparse.Namespace) -> int:
    scenario = load_analytical_manifest(args.scenario)
    out_dir = Path(args.out) if args.out else _default_out_dir(scenario.scenario_id)
    result = generate_analytical_run(scenario, out_dir=out_dir, fast=args.fast, parquet=args.parquet)
    print(f"Generated analytical scenario {scenario.scenario_id!r} (seed={scenario.root_seed}) "
          f"into {out_dir}")
    for name, rows in result.datasets.items():
        print(f"  {name}: {len(rows)} rows")
    k = result.measured_kpis
    print("Measured KPIs (computed from rows):")
    print(f"  energy per ton reduction:   {k['energy_intensity_reduction'] * 100:.2f}%")
    print(f"  specific CO2 reduction:     {k['co2_intensity_reduction'] * 100:.2f}%")
    print(f"  high-grade yield gain:      {k['high_grade_yield_gain_pp'] * 100:.2f} pts")
    print(f"  lining advance warning:     {k['lining_warning_days']} days")
    return 0


def cmd_generate_operational(args: argparse.Namespace) -> int:
    pack_dir = Path(args.pack)
    out_dir = Path(args.out) if args.out else _default_out_dir("operational-envelopes")
    result = export_operational_pack(pack_dir, out_dir)
    print(f"Exported operational envelope tables from {pack_dir} into {out_dir}")
    for name, count in result["row_counts"].items():
        print(f"  {name}: {count} rows")
    return 0


def cmd_generate_reference(args: argparse.Namespace) -> int:
    out_dir = Path(args.out) if args.out else DEFAULT_OUT_ROOT / "reference-data"
    result = export_reference_data(out_dir)
    print(f"Generated reference (dimension) data into {out_dir}")
    for name in result.row_counts:
        print(f"  {name}: {result.row_counts[name]} rows")
    return 0


def cmd_validate_analytics(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"no analytical run manifest found at {manifest_path}", file=sys.stderr)
        return 2
    ok, reports = validate_analytical_run(run_dir)
    for name, report in reports.items():
        print(f"{name} validator: {'PASS' if report.ok else 'FAIL'} ({report.checked} checks)")
        for err in report.errors[:20]:
            print(f"  - {err}")
    if not args.skip_checksum:
        checksum_ok, problems = verify_checksums(run_dir)
        ok = ok and checksum_ok
        print(f"checksum validator: {'PASS' if checksum_ok else 'FAIL'}")
        for problem in problems[:20]:
            print(f"  - {problem}")
    return 0 if ok else 1


def cmd_publish(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    total_events = 0
    for dataset in args.datasets:
        path = run_dir / f"{dataset}.ndjson"
        if not path.exists():
            print(f"skipping {dataset}: {path} not found (generate with --format ndjson first)")
            continue
        result = publish_ndjson(
            path, sink_url=args.sink_url, batch_size=args.batch_size,
            rate_events_per_second=args.rate, token_env=args.token_env,
            replay_duplicate_fraction=args.replay_duplicate_fraction,
        )
        total_events += result.events_sent
        print(f"published {dataset}: {result.events_sent} events in {result.batches_sent} batches "
              f"({result.duplicates_replayed} duplicates replayed)")
    print(f"total events published: {total_events}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"no run manifest found at {manifest_path}", file=sys.stderr)
        return 2
    run_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenario_manifest = load_manifest(run_manifest["scenario_id"])

    telemetry_path = run_dir / "telemetry.ndjson"
    telemetry = read_ndjson(telemetry_path) if telemetry_path.exists() else []

    ok = True
    if not args.only or "contract" in args.only:
        contract_report = validate_envelopes(telemetry)
        ok = ok and contract_report.ok
        print(f"contract validator: {'PASS' if contract_report.ok else 'FAIL'} "
              f"({contract_report.checked_records} records checked)")
        for err in contract_report.errors[:20]:
            print(f"  - {err}")

    if not args.only or "physics" in args.only:
        physics_report = validate_furnace_physics(telemetry)
        ok = ok and physics_report.ok
        print(f"physics validator: {'PASS' if physics_report.ok else 'FAIL'}")
        for err in physics_report.errors[:20]:
            print(f"  - {err}")

    if not args.only or "scenario" in args.only:
        scenario_report = validate_scenario(run_manifest.get("summary", {}), scenario_manifest.expected_assertions)
        ok = ok and scenario_report.ok
        print(f"scenario assertion validator: {'PASS' if scenario_report.ok else 'FAIL'}")
        for err in scenario_report.errors[:20]:
            print(f"  - {err}")

    if not args.only or "checksum" in args.only:
        checksum_ok, problems = verify_checksums(run_dir)
        ok = ok and checksum_ok
        print(f"checksum validator: {'PASS' if checksum_ok else 'FAIL'}")
        for problem in problems[:20]:
            print(f"  - {problem}")

    if not args.only or "contract-schema" in args.only:
        if not contract_schema_validator.contracts_available():
            print("contracts/events schema validator: SKIPPED (contracts/events not found in this checkout)")
        else:
            dataset_schema_projection = [
                ("telemetry", "telemetry.v1.schema.json", proj.project_telemetry),
                ("energy_interval", "energy-interval.v1.schema.json", proj.project_energy_interval),
                ("quality_measurement", "quality-measurement.v1.schema.json", proj.project_quality_measurement),
                ("model_inference", "model-inference.v1.schema.json", proj.project_model_inference),
                ("alarm_event", "alarm.v1.schema.json", proj.project_alarm),
            ]
            contract_schema_ok = True
            for dataset_name, schema_filename, project_fn in dataset_schema_projection:
                if contract_schema_validator.payload_schema_is_restrictive(schema_filename):
                    print(f"contracts/events schema validator [{dataset_name}]: SKIPPED "
                          f"({schema_filename} is still the pre-correction restrictive shape per the "
                          "2026-07-25 application-foundation coordination; rerun once the additive schema lands)")
                    continue
                dataset_path = run_dir / f"{dataset_name}.ndjson"
                records = read_ndjson(dataset_path) if dataset_path.exists() else []
                errors = []
                for record in records:
                    report = contract_schema_validator.validate_against_schema(project_fn(record), schema_filename)
                    errors.extend(report.errors)
                dataset_ok = len(errors) == 0
                contract_schema_ok = contract_schema_ok and dataset_ok
                print(f"contracts/events schema validator [{dataset_name}]: {'PASS' if dataset_ok else 'FAIL'} "
                      f"({len(records)} records checked against contracts/events/{schema_filename})")
                for err in errors[:20]:
                    print(f"  - {err}")
            ok = ok and contract_schema_ok

    return 0 if ok else 1


def cmd_checksum(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    if args.verify:
        ok, problems = verify_checksums(run_dir)
        print("checksums OK" if ok else "checksums MISMATCH")
        for problem in problems:
            print(f"  - {problem}")
        return 0 if ok else 1
    filenames = [p.name for p in run_dir.glob("*") if p.name != "checksums.json"]
    write_checksums(run_dir, filenames)
    print(f"wrote {run_dir / 'checksums.json'}")
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    removed = reset_run_directory(out_dir)
    print(f"reset {out_dir}: removed {len(removed)} item(s)")
    for name in removed:
        print(f"  - {name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="simulator", description="NovaSteel synthetic captor/sensor simulator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list-scenarios", help="List available scenario manifests")
    p_list.set_defaults(func=cmd_list_scenarios)

    p_gen = sub.add_parser("generate", help="Generate one scenario's datasets")
    p_gen.add_argument("--scenario", required=True, help="Scenario id (see list-scenarios)")
    p_gen.add_argument("--out", default=None, help="Output directory (default output/<scenario_id>)")
    p_gen.add_argument("--fast", action="store_true", help="Use the scenario's fast/demo window and sampling")
    p_gen.add_argument("--format", choices=["ndjson", "csv", "json"], default="ndjson")
    p_gen.set_defaults(func=cmd_generate)

    p_demo = sub.add_parser("demo", help="One-command fast full-demo generation")
    p_demo.add_argument("--out", default=None)
    p_demo.add_argument("--format", choices=["ndjson", "csv", "json"], default="ndjson")
    p_demo.set_defaults(func=cmd_demo)

    p_list_an = sub.add_parser("list-analytical-scenarios",
                               help="List available multi-month analytical (gold) scenarios")
    p_list_an.set_defaults(func=cmd_list_analytical_scenarios)

    p_gen_an = sub.add_parser("generate-analytics",
                              help="Generate a multi-month analytical gold-fact dataset")
    p_gen_an.add_argument("--scenario", required=True, help="Analytical scenario id")
    p_gen_an.add_argument("--out", default=None, help="Output directory (default output/<scenario_id>)")
    p_gen_an.add_argument("--fast", action="store_true", help="Use the scenario's short fast window")
    p_gen_an.add_argument("--parquet", action="store_true",
                          help="Also write Parquet alongside the canonical CSV (needs pyarrow)")
    p_gen_an.set_defaults(func=cmd_generate_analytics)

    p_val_an = sub.add_parser("validate-analytics",
                              help="Validate an analytical gold run (contract/guardrails/KPIs/checksums)")
    p_val_an.add_argument("--run-dir", required=True)
    p_val_an.add_argument("--skip-checksum", action="store_true")
    p_val_an.set_defaults(func=cmd_validate_analytics)

    p_gen_op = sub.add_parser("generate-operational",
                              help="Reshape the committed simulator pack into Fabric operational "
                                   "envelope tables (the BFF's Lakehouse read layer)")
    p_gen_op.add_argument("--pack", default=str(_REPO_ROOT / "services" / "bff-api" / "fixtures" / "demo-full"),
                          help="Source simulator pack directory (default: the committed demo-full pack)")
    p_gen_op.add_argument("--out", default=None,
                          help="Output directory (default output/operational-envelopes)")
    p_gen_op.set_defaults(func=cmd_generate_operational)

    p_gen_ref = sub.add_parser("generate-reference",
                               help="Generate the reference (dimension) data the medallion "
                                    "bronze-to-silver notebook resolves every event against")
    p_gen_ref.add_argument("--out", default=None,
                           help="Output directory (default output/reference-data)")
    p_gen_ref.set_defaults(func=cmd_generate_reference)

    p_pub = sub.add_parser("publish", help="Paced publish of a generated run to an HTTP sink")
    p_pub.add_argument("--run-dir", required=True)
    p_pub.add_argument("--sink-url", required=True, help="Eventstream Custom Endpoint / local BFF ingestion URL")
    p_pub.add_argument("--datasets", nargs="+", default=DATASET_NAMES)
    p_pub.add_argument("--batch-size", type=int, default=1)
    p_pub.add_argument("--rate", type=float, default=20.0, help="Events per second (paced publishing)")
    p_pub.add_argument("--token-env", default=None, help="Env var holding a bearer token (never hard-coded)")
    p_pub.add_argument("--replay-duplicate-fraction", type=float, default=0.0)
    p_pub.set_defaults(func=cmd_publish)

    p_val = sub.add_parser("validate", help="Run contract/physics/scenario/checksum validators")
    p_val.add_argument("--run-dir", required=True)
    p_val.add_argument("--only", nargs="+",
                        choices=["contract", "physics", "scenario", "checksum", "contract-schema"],
                        default=None)
    p_val.set_defaults(func=cmd_validate)

    p_chk = sub.add_parser("checksum", help="Write or verify a run's checksums.json")
    p_chk.add_argument("--run-dir", required=True)
    p_chk.add_argument("--verify", action="store_true")
    p_chk.set_defaults(func=cmd_checksum)

    p_reset = sub.add_parser("reset", help="Delete a run's generated output directory")
    p_reset.add_argument("--out", required=True)
    p_reset.set_defaults(func=cmd_reset)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
