"""CLI de aquisicao de dados: `python -m biomass_model.cli <comando>`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import catalog, credentials


def _cmd_list(_: argparse.Namespace) -> int:
    status = credentials.status()
    for spec in catalog.DATASETS:
        print(f"{spec.id:10s} {spec.name:38s} conta: {spec.account}")
        print(f"           doc: {spec.doc}")
    print("\nCredenciais:")
    print(json.dumps(status, indent=2, ensure_ascii=False))
    return 0


def _cmd_s2(args: argparse.Namespace) -> int:
    from .datasets.s2 import fetch_window

    result = fetch_window(
        args.lon, args.lat, args.start, args.end, args.out,
        size=args.size, max_cloud=args.max_cloud,
    )
    print(json.dumps({k: v for k, v in result.items() if k not in {"candidates", "bands"}}, indent=2))
    return 0


def _cmd_dem(args: argparse.Namespace) -> int:
    from .datasets.dem import fetch_dem

    print(json.dumps(fetch_dem(args.lon, args.lat, args.out, half=args.half), indent=2))
    return 0


def _cmd_era5(args: argparse.Namespace) -> int:
    from .datasets.era5 import fetch_era5

    result = fetch_era5(args.lon, args.lat, args.start_year, args.end_year, args.out, pad=args.pad)
    print(json.dumps({k: v for k, v in result.items() if k != "request"}, indent=2))
    return 0


def _cmd_gedi(args: argparse.Namespace) -> int:
    from .datasets.gedi import fetch_gedi

    bbox = (args.west, args.south, args.east, args.north)
    result = fetch_gedi(
        bbox, args.start, args.end, args.out, args.work_dir,
        version=args.version, max_granules=args.max_granules,
        min_sensitivity=args.min_sensitivity,
    )
    print(json.dumps(result, indent=2))
    return 0


def _cmd_train_table(args: argparse.Namespace) -> int:
    from .features import build_training_table

    summary = build_training_table(
        args.gedi, args.s2, args.dem, args.era5, args.mapbiomas_dir, args.out,
        bioma=args.bioma,
    )
    print(json.dumps(summary, indent=2))
    return 0


def _cmd_baseline(args: argparse.Namespace) -> int:
    from .modeling import run_baseline

    result = run_baseline(args.csv, args.out_dir, n_splits=args.folds,
                          block_px=args.block_px, n_estimators=args.trees)
    print(json.dumps({k: v for k, v in result.items() if k != "importance"}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="biomass", description="Aquisicao de dados abertos")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="lista datasets e status das credenciais").set_defaults(func=_cmd_list)

    s2 = sub.add_parser("s2", help="janela Sentinel-2 L2A")
    s2.add_argument("--lon", type=float, required=True)
    s2.add_argument("--lat", type=float, required=True)
    s2.add_argument("--start", required=True)
    s2.add_argument("--end", required=True)
    s2.add_argument("--out", required=True)
    s2.add_argument("--size", type=int, default=1600)
    s2.add_argument("--max-cloud", type=float, default=20.0)
    s2.set_defaults(func=_cmd_s2)

    dem = sub.add_parser("dem", help="DEM Copernicus GLO-30")
    dem.add_argument("--lon", type=float, required=True)
    dem.add_argument("--lat", type=float, required=True)
    dem.add_argument("--out", required=True)
    dem.add_argument("--half", type=float, default=0.08)
    dem.set_defaults(func=_cmd_dem)

    era5 = sub.add_parser("era5", help="ERA5-Land mensal")
    era5.add_argument("--lon", type=float, required=True)
    era5.add_argument("--lat", type=float, required=True)
    era5.add_argument("--start-year", type=int, required=True)
    era5.add_argument("--end-year", type=int, required=True)
    era5.add_argument("--out", required=True)
    era5.add_argument("--pad", type=float, default=0.1)
    era5.set_defaults(func=_cmd_era5)

    gedi = sub.add_parser("gedi", help="GEDI L4A: footprints validos no bbox")
    gedi.add_argument("--west", type=float, required=True)
    gedi.add_argument("--south", type=float, required=True)
    gedi.add_argument("--east", type=float, required=True)
    gedi.add_argument("--north", type=float, required=True)
    gedi.add_argument("--start", required=True)
    gedi.add_argument("--end", required=True)
    gedi.add_argument("--out", required=True)
    gedi.add_argument("--work-dir", required=True)
    gedi.add_argument("--version", choices=["V2_1", "V3"], default="V2_1")
    gedi.add_argument("--max-granules", type=int, default=None)
    gedi.add_argument("--min-sensitivity", type=float, default=0.9)
    gedi.set_defaults(func=_cmd_gedi)

    table = sub.add_parser("train-table", help="tabela de treino (GEDI x features)")
    table.add_argument("--gedi", required=True)
    table.add_argument("--s2", required=True)
    table.add_argument("--dem", required=True)
    table.add_argument("--era5", required=True)
    table.add_argument("--mapbiomas-dir", required=True)
    table.add_argument("--out", required=True)
    table.add_argument("--bioma", choices=["amazonia", "cerrado"], required=True)
    table.set_defaults(func=_cmd_train_table)

    baseline = sub.add_parser("baseline", help="RandomForest com CV por blocos espaciais")
    baseline.add_argument("--csv", required=True)
    baseline.add_argument("--out-dir", required=True)
    baseline.add_argument("--folds", type=int, default=5)
    baseline.add_argument("--block-px", type=int, default=167)
    baseline.add_argument("--trees", type=int, default=400)
    baseline.set_defaults(func=_cmd_baseline)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
