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


def _cmd_s2_composite(args: argparse.Namespace) -> int:
    from .datasets.s2 import fetch_composite

    result = fetch_composite(
        args.lon, args.lat, args.start, args.end, args.out,
        size=args.size, max_items=args.max_items, max_cloud=args.max_cloud,
    )
    print(json.dumps({k: v for k, v in result.items() if k != "items"}, indent=2))
    return 0


def _cmd_era5_bbox(args: argparse.Namespace) -> int:
    from .datasets.era5 import fetch_era5_bbox

    print(json.dumps(fetch_era5_bbox(args.west, args.south, args.east, args.north,
                                     args.start_year, args.end_year, args.out), indent=2))
    return 0


def _cmd_sites_fetch(args: argparse.Namespace) -> int:
    from .datasets.sites import fetch_site_windows

    result = fetch_site_windows(
        args.csv, args.out_dir, args.start, args.end,
        bioma=args.bioma, size=args.size, max_cloud=args.max_cloud,
    )
    print(json.dumps(result, indent=2))
    return 0


def _cmd_field_table(args: argparse.Namespace) -> int:
    from .features import build_field_table

    print(json.dumps(build_field_table(
        args.sites, args.work_root, args.era5, args.mapbiomas_dir, args.out,
        bioma=args.bioma, half_m=args.half_m), indent=2))
    return 0


def _cmd_landsat(args: argparse.Namespace) -> int:
    from .datasets.landsat import fetch_landsat_window

    result = fetch_landsat_window(args.lon, args.lat, args.date, args.out,
                                  half_m=args.half_m, days=args.days,
                                  max_items=args.max_items)
    print(json.dumps({k: v for k, v in result.items() if k != "items"}, indent=2))
    return 0


def _cmd_landsat_sites(args: argparse.Namespace) -> int:
    from .datasets.landsat import fetch_landsat_sites

    result = fetch_landsat_sites(args.sites, args.out_dir, bioma=args.bioma,
                                 years=(args.year_start, args.year_end),
                                 half_m=args.half_m, days=args.days,
                                 max_items=args.max_items)
    print(json.dumps({k: v for k, v in result.items() if k != "failures"}, indent=2))
    return 0


def _cmd_landsat_field_table(args: argparse.Namespace) -> int:
    from .features import build_landsat_field_table

    print(json.dumps(build_landsat_field_table(
        args.sites, args.work_root, args.era5, args.mapbiomas_dir, args.out,
        bioma=args.bioma, half_m=args.half_m), indent=2))
    return 0


def _cmd_region_cv(args: argparse.Namespace) -> int:
    from .modeling import run_region_cv

    result = run_region_cv(args.csv, args.out_dir, calib_frac=args.calib_frac,
                           calib_mode=args.calib_mode, cell_px=args.cell_px)
    print(json.dumps({k: v for k, v in result.items() if k != "features"}, indent=2))
    return 0


def _cmd_region_conformal(args: argparse.Namespace) -> int:
    from .modeling import run_region_conformal

    result = run_region_conformal(args.csv, args.out_dir, calib_frac=args.calib_frac,
                                  conformal_frac=args.conformal_frac,
                                  cell_px=args.cell_px)
    print(json.dumps({k: v for k, v in result.items() if k != "features"}, indent=2))
    return 0


def _cmd_region_aoa(args: argparse.Namespace) -> int:
    from .modeling import run_region_aoa

    result = run_region_aoa(args.csv, args.out_dir, calib_frac=args.calib_frac,
                            cell_px=args.cell_px)
    print(json.dumps({k: v for k, v in result.items() if k != "features"}, indent=2))
    return 0


def _cmd_field_baseline(args: argparse.Namespace) -> int:
    from .modeling import run_field_baseline

    result = run_field_baseline(args.csv, args.out_dir, block_deg=args.block_deg,
                                n_estimators=args.trees)
    print(json.dumps({k: v for k, v in result.items() if k != "importance"}, indent=2))
    return 0


def _cmd_s1(args: argparse.Namespace) -> int:
    from .datasets.s1 import fetch_s1

    result = fetch_s1(args.lon, args.lat, args.start, args.end, args.out,
                      size=args.size, max_items=args.max_items)
    print(json.dumps({k: v for k, v in result.items() if k != "items"}, indent=2))
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
        bioma=args.bioma, s1_path=args.s1, history=args.history,
    )
    print(json.dumps(summary, indent=2))
    return 0


def _cmd_baseline(args: argparse.Namespace) -> int:
    from .modeling import run_baseline

    result = run_baseline(args.csv, args.out_dir, n_splits=args.folds,
                          block_px=args.block_px, n_estimators=args.trees,
                          cell_px=args.cell_px, min_shots=args.min_shots,
                          group_col=args.group_col)
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

    s2c = sub.add_parser("s2-composite", help="mediana multi-data de S2")
    s2c.add_argument("--lon", type=float, required=True)
    s2c.add_argument("--lat", type=float, required=True)
    s2c.add_argument("--start", required=True)
    s2c.add_argument("--end", required=True)
    s2c.add_argument("--out", required=True)
    s2c.add_argument("--size", type=int, default=1600)
    s2c.add_argument("--max-items", type=int, default=10)
    s2c.add_argument("--max-cloud", type=float, default=30.0)
    s2c.set_defaults(func=_cmd_s2_composite)

    s1 = sub.add_parser("s1", help="Sentinel-1 RTC (mediana, sem conta)")
    s1.add_argument("--lon", type=float, required=True)
    s1.add_argument("--lat", type=float, required=True)
    s1.add_argument("--start", required=True)
    s1.add_argument("--end", required=True)
    s1.add_argument("--out", required=True)
    s1.add_argument("--size", type=int, default=1600)
    s1.add_argument("--max-items", type=int, default=8)
    s1.set_defaults(func=_cmd_s1)

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

    era5b = sub.add_parser("era5-bbox", help="ERA5-Land mensal para um retangulo")
    era5b.add_argument("--west", type=float, required=True)
    era5b.add_argument("--south", type=float, required=True)
    era5b.add_argument("--east", type=float, required=True)
    era5b.add_argument("--north", type=float, required=True)
    era5b.add_argument("--start-year", type=int, required=True)
    era5b.add_argument("--end-year", type=int, required=True)
    era5b.add_argument("--out", required=True)
    era5b.set_defaults(func=_cmd_era5_bbox)

    sites = sub.add_parser("sites-fetch", help="janelas S2/DEM em sitios de campo")
    sites.add_argument("--csv", required=True)
    sites.add_argument("--out-dir", required=True)
    sites.add_argument("--start", required=True)
    sites.add_argument("--end", required=True)
    sites.add_argument("--bioma", default="Cerrado")
    sites.add_argument("--size", type=int, default=400)
    sites.add_argument("--max-cloud", type=float, default=25.0)
    sites.set_defaults(func=_cmd_sites_fetch)

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
    table.add_argument("--s1", default=None, help="opcional: composite Sentinel-1 RTC")
    table.add_argument("--history", action="store_true", help="features de historico MapBiomas")
    table.set_defaults(func=_cmd_train_table)

    baseline = sub.add_parser("baseline", help="RandomForest com CV por blocos espaciais")
    baseline.add_argument("--csv", required=True)
    baseline.add_argument("--out-dir", required=True)
    baseline.add_argument("--folds", type=int, default=5)
    baseline.add_argument("--block-px", type=int, default=167)
    baseline.add_argument("--trees", type=int, default=400)
    baseline.add_argument("--cell-px", type=int, default=None,
                          help="agrega footprints em celulas (33 px ~ 1 km)")
    baseline.add_argument("--min-shots", type=int, default=3)
    baseline.add_argument("--group-col", default=None, help="agrupa folds (ex.: box)")
    baseline.set_defaults(func=_cmd_baseline)

    ftable = sub.add_parser("field-table", help="tabela de features em sitios de campo")
    ftable.add_argument("--sites", required=True)
    ftable.add_argument("--work-root", required=True)
    ftable.add_argument("--era5", required=True)
    ftable.add_argument("--mapbiomas-dir", required=True)
    ftable.add_argument("--out", required=True)
    ftable.add_argument("--bioma", default="Cerrado")
    ftable.add_argument("--half-m", type=float, default=500.0)
    ftable.set_defaults(func=_cmd_field_table)

    fbase = sub.add_parser("field-baseline", help="RandomForest em sitios de campo")
    fbase.add_argument("--csv", required=True)
    fbase.add_argument("--out-dir", required=True)
    fbase.add_argument("--block-deg", type=float, default=1.0)
    fbase.add_argument("--trees", type=int, default=400)
    fbase.set_defaults(func=_cmd_field_baseline)

    rcv = sub.add_parser("region-cv", help="leave-one-region-out com calibracao local")
    rcv.add_argument("--csv", required=True)
    rcv.add_argument("--out-dir", required=True)
    rcv.add_argument("--calib-frac", type=float, default=0.0)
    rcv.add_argument("--calib-mode", choices=["random", "south", "center"], default="random")
    rcv.add_argument("--cell-px", type=int, default=None)
    rcv.set_defaults(func=_cmd_region_cv)

    rcf = sub.add_parser("region-conformal", help="intervalo conformal por regiao")
    rcf.add_argument("--csv", required=True)
    rcf.add_argument("--out-dir", required=True)
    rcf.add_argument("--calib-frac", type=float, default=0.1)
    rcf.add_argument("--conformal-frac", type=float, default=0.1)
    rcf.add_argument("--cell-px", type=int, default=None)
    rcf.set_defaults(func=_cmd_region_conformal)

    raoa = sub.add_parser("region-aoa", help="Area de Aplicabilidade por regiao")
    raoa.add_argument("--csv", required=True)
    raoa.add_argument("--out-dir", required=True)
    raoa.add_argument("--calib-frac", type=float, default=0.1)
    raoa.add_argument("--cell-px", type=int, default=None)
    raoa.set_defaults(func=_cmd_region_aoa)

    ls = sub.add_parser("landsat", help="janela Landsat C2 L2 em torno de uma data (MPC)")
    ls.add_argument("--lon", type=float, required=True)
    ls.add_argument("--lat", type=float, required=True)
    ls.add_argument("--date", required=True)
    ls.add_argument("--out", required=True)
    ls.add_argument("--half-m", type=float, default=500.0)
    ls.add_argument("--days", type=int, default=45)
    ls.add_argument("--max-items", type=int, default=6)
    ls.set_defaults(func=_cmd_landsat)

    lss = sub.add_parser("landsat-sites", help="janelas Landsat por sitio de campo")
    lss.add_argument("--sites", required=True)
    lss.add_argument("--out-dir", required=True)
    lss.add_argument("--bioma", default="Cerrado")
    lss.add_argument("--year-start", type=int, default=2004)
    lss.add_argument("--year-end", type=int, default=2014)
    lss.add_argument("--half-m", type=float, default=500.0)
    lss.add_argument("--days", type=int, default=45)
    lss.add_argument("--max-items", type=int, default=6)
    lss.set_defaults(func=_cmd_landsat_sites)

    lft = sub.add_parser("landsat-field-table", help="tabela de campo com Landsat na data")
    lft.add_argument("--sites", required=True)
    lft.add_argument("--work-root", required=True)
    lft.add_argument("--era5", required=True)
    lft.add_argument("--mapbiomas-dir", required=True)
    lft.add_argument("--out", required=True)
    lft.add_argument("--bioma", default="Cerrado")
    lft.add_argument("--half-m", type=float, default=500.0)
    lft.set_defaults(func=_cmd_landsat_field_table)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
