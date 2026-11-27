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
                                 max_items=args.max_items, dem_half=args.dem_half)
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


def _cmd_annual_map(args: argparse.Namespace) -> int:
    from .inference.map import predict_map

    if args.resolution == 30:
        from .inference.map import predict_map_30m
        info = predict_map_30m(args.model, args.s2, args.dem, args.era5,
                               args.mapbiomas_dir, args.year, args.out,
                               training_csv=args.training_csv, residual_csv=args.residuals)
    else:
        info = predict_map(args.model, args.s2, args.dem, args.era5, args.mapbiomas_dir,
                           args.year, args.out, block=args.block)
    print(json.dumps(info, indent=2))
    return 0


def _cmd_map_intervals(args: argparse.Namespace) -> int:
    from .inference.map import add_intervals

    print(json.dumps(add_intervals(args.map, args.residuals, args.out), indent=2))
    return 0


def _cmd_mrv_check(args: argparse.Namespace) -> int:
    from .mrv import check_predictions

    result = check_predictions(args.csv, args.out, value_col=args.value_col,
                               class_col=args.class_col, aoa_col=args.aoa_col)
    print(json.dumps(result, indent=2))
    return 0


def _cmd_polygon_stats(args: argparse.Namespace) -> int:
    from .polygon import polygon_stats

    result = polygon_stats(args.csv, args.out, filter_col=args.filter_col,
                            filter_value=args.filter_value, value_col=args.value_col,
                            class_col=args.class_col, block_px=args.block_px,
                            n_boot=args.n_boot)
    print(json.dumps(result, indent=2))
    return 0


def _load_inventory_frame(args: argparse.Namespace):
    from .inventory.adapters import (
        load_ceda_manaus,
        load_gedi_l4a,
        load_ifn_panel,
        load_ornl_directory,
        load_plos2018,
    )

    if args.source == "plos2018":
        return load_plos2018(args.path, usage=args.usage)
    if args.source == "ifn":
        return load_ifn_panel(args.path, equation=args.equation, usage=args.usage,
                              max_rows=args.max_rows)
    if args.source == "ornl":
        return load_ornl_directory(args.path, usage=args.usage, coords_path=args.coords,
                                   limit=args.limit)
    if args.source == "gedi":
        return load_gedi_l4a(args.path, usage=args.usage, max_rows=args.max_rows)
    if args.source == "ceda":
        return load_ceda_manaus(args.path, usage=args.usage)
    raise ValueError(f"fonte desconhecida: {args.source}")


def _cmd_inventory(args: argparse.Namespace) -> int:
    from .inventory.schema import validate_observations, write_observations

    frame = _load_inventory_frame(args)
    report = validate_observations(frame)
    out = write_observations(frame, args.out)
    summary = {
        "source": args.source,
        "rows": int(len(frame)),
        "out": str(out),
        "errors": report["errors"],
        "warnings": report["warnings"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def _cmd_inventory_store(args: argparse.Namespace) -> int:
    from .inventory.store import ObservationStore

    frame = _load_inventory_frame(args)
    store = ObservationStore(args.store)
    license = str(frame["license"].dropna().iloc[0]) if len(frame) and frame["license"].notna().any() else ""
    result = store.ingest(frame, source_path=args.path, license=license,
                          notes=args.notes, force=args.force)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _cmd_ifn_enrich(args: argparse.Namespace) -> int:
    from .enrich_ifn import build_ifn_enrichment

    report = build_ifn_enrichment(
        args.panel, args.uf_dir, args.correspondence, args.out_dir,
        equation=args.equation, usage=args.usage,
        spatial_support=args.spatial_support,
        municipalities_path=args.municipalities,
        ibge_vegetation_path=args.ibge_vegetation,
        mapbiomas_pattern=args.mapbiomas_pattern,
        mapbiomas_correspondence_path=args.mapbiomas_correspondence,
        ibge_version=args.ibge_version,
        max_units=args.max_units,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def _cmd_ifn_validate(args: argparse.Namespace) -> int:
    from .enrich_ifn import validate_correspondence

    report = validate_correspondence(
        args.points, args.ibge_vegetation, args.correspondence, args.out_dir,
        tipologia_col=args.tipologia_col, source_col=args.source_col,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def _cmd_ifn_export(args: argparse.Namespace) -> int:
    from .enrich_ifn import export_ifn_spatial

    report = export_ifn_spatial(args.enriched, args.out, crs=args.crs)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def _cmd_target_consolidate(args: argparse.Namespace) -> int:
    from .targets import consolidate_target

    biomes = (
        [b.strip() for b in args.biomes.split(",") if b.strip()]
        if args.biomes else None
    )
    report = consolidate_target(
        args.gpkg, args.out_csv,
        gpkg_path=args.out_gpkg, manifest_path=args.manifest,
        source=args.source, source_version=args.source_version,
        plausibility_max=args.max_plausible, biomes=biomes,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def _cmd_features_catalog(args: argparse.Namespace) -> int:
    from .feature_catalog import load_catalog, select_features, summarize

    groups = (
        [g.strip() for g in args.groups.split(",") if g.strip()]
        if args.groups else None
    )
    catalog = load_catalog(args.catalog)
    selected = select_features(
        catalog, groups=groups, max_priority=args.max_priority,
        include_experimental=args.include_experimental,
    )
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        selected.to_csv(out, index=False, encoding="utf-8")
    print(json.dumps(summarize(
        catalog, selected, include_experimental=args.include_experimental,
    ), indent=2, ensure_ascii=False))
    return 0


def _cmd_target_observations(args: argparse.Namespace) -> int:
    import pandas as pd

    from .target_observations import (
        sample_target, target_to_observations, write_observations,
    )

    target = pd.read_csv(args.target_csv)
    if args.sample:
        by = tuple(b.strip() for b in args.by.split(",") if b.strip())
        target = sample_target(
            target, args.sample, tier=args.tier, seed=args.seed,
            min_per_stratum=args.min_per_stratum, by=by,
        )
    observations = target_to_observations(target)
    report = write_observations(
        observations, args.out, report_path=args.manifest,
        params={
            "target_csv": args.target_csv,
            "sample": args.sample,
            "tier": args.tier,
            "seed": args.seed,
            "min_per_stratum": args.min_per_stratum,
            "by": args.by,
        },
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def _cmd_features_observations(args: argparse.Namespace) -> int:
    from .observation_features import build_observation_features

    result = build_observation_features(
        args.observations, args.out,
        optical_dir=args.optical_dir, optical_pattern=args.optical_pattern,
        optical_path=args.optical_path, dem_dir=args.dem_dir,
        dem_pattern=args.dem_pattern, dem_path=args.dem_path,
        era5_path=args.era5, mapbiomas_dir=args.mapbiomas_dir,
        half_m=args.half_m, history=not args.no_history,
        history_start=args.history_start, history_end=args.history_end,
        fallback_year=args.fallback_year, max_rows=args.max_rows,
        fitofisionomia_vector=args.fitofisionomia_vector,
        fitofisionomia_attribute=args.fitofisionomia_attribute,
    )
    print(json.dumps({k: v for k, v in result.items() if k != "features"},
                     indent=2, ensure_ascii=False))
    return 0


def _cmd_train_field(args: argparse.Namespace) -> int:
    from .training.field import train_field_model

    result = train_field_model(
        args.csv, args.out_dir, target=args.target,
        block_size_m=args.block_size_m, buffer_m=args.buffer_m,
        n_estimators=args.trees, min_samples_leaf=args.min_samples_leaf,
        min_test=args.min_test, max_folds=args.max_folds, seed=args.seed,
        conformal_coverage=args.conformal_coverage,
        algorithm=args.algorithm,
        use_categoricals=not args.no_categoricals,
        domain_classes=tuple(int(x.strip()) for x in args.domain_classes.split(",") if x.strip()),
    )
    print(json.dumps({k: v for k, v in result.items()
                      if k not in {"features", "importance", "by_fold"}},
                     indent=2, ensure_ascii=False))
    return 0


def _cmd_predict_field(args: argparse.Namespace) -> int:
    from .training.inference import predict_field_model

    result = predict_field_model(args.model, args.csv, args.out, target_col=args.target)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _cmd_model_register(args: argparse.Namespace) -> int:
    from .model_registry import register_model

    result = register_model(args.metrics, args.registry, model_id=args.model_id,
                            family=args.family, status=args.status, notes=args.notes)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _cmd_model_list(args: argparse.Namespace) -> int:
    from .model_registry import list_models

    table = list_models(args.registry, family=args.family)
    print(table.to_json(orient="records", indent=2, force_ascii=False))
    return 0


def _cmd_model_compare(args: argparse.Namespace) -> int:
    from .model_registry import compare_models

    table = compare_models(args.registry, metric=args.metric, family=args.family)
    print(table.to_json(orient="records", indent=2, force_ascii=False))
    return 0


def _cmd_model_promote(args: argparse.Namespace) -> int:
    from .model_registry import promote_model

    result = promote_model(args.registry, args.model_id, reason=args.reason)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _cmd_fitofisionomia_reconcile(args: argparse.Namespace) -> int:
    from .stratification import compare_fitofisionomia_mapbiomas

    classes = tuple(int(x.strip()) for x in args.classes.split(",") if x.strip())
    result = compare_fitofisionomia_mapbiomas(
        args.fit_raster, args.mapbiomas_raster, args.codes,
        mapbiomas_classes=classes, out_csv=args.out,
    )
    print(json.dumps({k: v for k, v in result.items() if k != "rows"},
                     indent=2, ensure_ascii=False))
    return 0


def _cmd_fitofisionomia_reclassify(args: argparse.Namespace) -> int:
    from .stratification import reclassify_code_table

    result = reclassify_code_table(args.codes, args.out)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _cmd_fitofisionomia(args: argparse.Namespace) -> int:
    from .stratification import rasterize_fitofisionomia

    result = rasterize_fitofisionomia(
        args.vector, args.template, args.out, attribute=args.attribute,
        all_touched=args.all_touched,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _cmd_polygon(args: argparse.Namespace) -> int:
    from .aggregation.polygon import polygon_raster_stats

    domain = tuple(int(x.strip()) for x in args.domain_classes.split(",") if x.strip())
    result = polygon_raster_stats(
        args.raster,
        args.input,
        value_band=args.value_band,
        class_band=args.class_band,
        fitofisionomia_band=args.fitofisionomia_band,
        aoa_band=args.aoa_band,
        class_raster=args.class_raster,
        fitofisionomia_raster=args.fitofisionomia_raster,
        aoa_raster=args.aoa_raster,
        domain_classes=domain,
        require_domain=not args.allow_outside_domain,
        require_aoa=args.require_aoa,
        block_size_m=args.block_size_m,
        chunk_rows=args.chunk_rows,
        n_boot=args.n_boot,
        fitofisionomia_codes=args.fitofisionomia_codes,
        fitofisionomia_groups=(tuple(x.strip() for x in args.fitofisionomia_groups.split(",")
                                     if x.strip())
                               if args.fitofisionomia_groups else None),
        year=args.year,
        out=args.out,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
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


def _cmd_s2_annual(args: argparse.Namespace) -> int:
    from .datasets.s2 import fetch_annual

    result = fetch_annual(args.lon, args.lat, args.year, args.out,
                          size=args.size, max_items=args.max_items,
                          max_cloud=args.max_cloud)
    print(json.dumps({k: v for k, v in result.items() if k != "items"}, indent=2))
    return 0


def _cmd_ceda(args: argparse.Namespace) -> int:
    from .datasets.ceda import fetch_ceda_manaus

    result = fetch_ceda_manaus(args.out_dir, download=not args.no_download)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _cmd_ornl_plots(args: argparse.Namespace) -> int:
    from .datasets.ornl import fetch_ornl_plot_companions

    result = fetch_ornl_plot_companions(args.out_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _cmd_ornl_coords(args: argparse.Namespace) -> int:
    from .datasets.ornl import build_ornl_site_coords

    result = build_ornl_site_coords(args.plots_dir, args.out)
    print(json.dumps({k: v for k, v in result.items() if k != "rows"},
                     indent=2, ensure_ascii=False))
    return 0


def _cmd_ibge(args: argparse.Namespace) -> int:
    from .datasets.ibge import fetch_ibge_vegetacao

    result = fetch_ibge_vegetacao(
        args.out_dir,
        version=args.version,
        include_points=args.include_points,
        include_tables=not args.no_tables,
        download=not args.no_download,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
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

    s2a = sub.add_parser("s2-annual", help="composto anual S2 + fenologia")
    s2a.add_argument("--lon", type=float, required=True)
    s2a.add_argument("--lat", type=float, required=True)
    s2a.add_argument("--year", type=int, required=True)
    s2a.add_argument("--out", required=True)
    s2a.add_argument("--size", type=int, default=1600)
    s2a.add_argument("--max-items", type=int, default=30)
    s2a.add_argument("--max-cloud", type=float, default=40.0)
    s2a.set_defaults(func=_cmd_s2_annual)

    ceda = sub.add_parser("ceda-manaus", help="parcelas AGB CEDA/NCEO Manaus 2014")
    ceda.add_argument("--out-dir", required=True)
    ceda.add_argument("--no-download", action="store_true")
    ceda.set_defaults(func=_cmd_ceda)

    oplots = sub.add_parser("ornl-plots", help="baixa shapefiles de transectos do ORNL")
    oplots.add_argument("--out-dir", required=True)
    oplots.set_defaults(func=_cmd_ornl_plots)

    ocoords = sub.add_parser("ornl-coords", help="extrai centroides de sitios ORNL")
    ocoords.add_argument("--plots-dir", required=True)
    ocoords.add_argument("--out", required=True)
    ocoords.set_defaults(func=_cmd_ornl_coords)

    ibge = sub.add_parser("ibge-vegetacao", help="vegetacao IBGE 1:250.000 (areas/tabelas)")
    ibge.add_argument("--out-dir", required=True)
    ibge.add_argument("--version", default="2026")
    ibge.add_argument("--include-points", action="store_true")
    ibge.add_argument("--no-tables", action="store_true")
    ibge.add_argument("--no-download", action="store_true")
    ibge.set_defaults(func=_cmd_ibge)

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

    pst = sub.add_parser("polygon-stats", help="estoque e IC por poligono")
    pst.add_argument("--csv", required=True)
    pst.add_argument("--out", default=None)
    pst.add_argument("--filter-col", default=None)
    pst.add_argument("--filter-value", default=None)
    pst.add_argument("--value-col", default="pred")
    pst.add_argument("--class-col", default="mapbiomas_class")
    pst.add_argument("--block-px", type=int, default=5)
    pst.add_argument("--n-boot", type=int, default=400)
    pst.set_defaults(func=_cmd_polygon_stats)

    mrv = sub.add_parser("mrv-check", help="QA/MRV de uma tabela de predicoes")
    mrv.add_argument("--csv", required=True)
    mrv.add_argument("--out", default=None)
    mrv.add_argument("--value-col", default="pred")
    mrv.add_argument("--class-col", default="mapbiomas_class")
    mrv.add_argument("--aoa-col", default="aoa_inside")
    mrv.set_defaults(func=_cmd_mrv_check)

    inv = sub.add_parser("inventory", help="ingere inventario/observacao no esquema canonico")
    inv.add_argument("--source", choices=["plos2018", "ifn", "ornl", "gedi", "ceda"],
                     required=True)
    inv.add_argument("--path", required=True)
    inv.add_argument("--out", required=True)
    inv.add_argument("--usage", default="validation",
                     choices=["training", "calibration", "validation", "benchmark", "excluded"])
    inv.add_argument("--equation", default="AGB_Chave")
    inv.add_argument("--coords", default=None, help="CSV de coordenadas por sitio (ORNL)")
    inv.add_argument("--limit", type=int, default=None)
    inv.add_argument("--max-rows", type=int, default=None)
    inv.set_defaults(func=_cmd_inventory)

    invs = sub.add_parser("inventory-store", help="ingere no store canonico idempotente")
    invs.add_argument("--source", choices=["plos2018", "ifn", "ornl", "gedi", "ceda"],
                      required=True)
    invs.add_argument("--path", required=True)
    invs.add_argument("--store", required=True)
    invs.add_argument("--usage", default="validation",
                      choices=["training", "calibration", "validation", "benchmark", "excluded"])
    invs.add_argument("--equation", default="AGB_Chave")
    invs.add_argument("--coords", default=None)
    invs.add_argument("--limit", type=int, default=None)
    invs.add_argument("--max-rows", type=int, default=None)
    invs.add_argument("--notes", default="")
    invs.add_argument("--force", action="store_true")
    invs.set_defaults(func=_cmd_inventory_store)

    ien = sub.add_parser(
        "ifn-enrich",
        help="enriquece o painel IFN com correspondencia IBGE e territorio")
    ien.add_argument("--panel", required=True,
                     help="CSV/GPKG do Painel de Biomassa e Carbono")
    ien.add_argument("--uf-dir", required=True,
                     help="diretorio com os ua_<UF>.csv oficiais")
    ien.add_argument("--correspondence", required=True,
                     help="data/reference/ifn_correspondencia_ibge.csv")
    ien.add_argument("--out-dir", required=True)
    ien.add_argument("--equation", default="AGB_Chave")
    ien.add_argument("--usage", default="validation",
                     choices=["training", "calibration", "validation",
                              "benchmark", "excluded"])
    ien.add_argument("--spatial-support", default="footprint",
                     choices=["footprint", "municipio"],
                     help="pegada documentada do conglomerado (padrao) ou municipio")
    ien.add_argument("--municipalities", default=None,
                     help="malha municipal IBGE (shp/gpkg)")
    ien.add_argument("--ibge-vegetation", default=None,
                     help="vege_area.shp do IBGE 1:250.000")
    ien.add_argument("--mapbiomas-pattern", default=None,
                     help="padrao com {year}, ex.: .../mapbiomas_col11_{year}.tif")
    ien.add_argument("--mapbiomas-correspondence", default=None,
                     help="data/reference/ibge_legenda1_para_mapbiomas.csv")
    ien.add_argument("--ibge-version", default="2025-01-01")
    ien.add_argument("--max-units", type=int, default=None)
    ien.set_defaults(func=_cmd_ifn_enrich)

    iva = sub.add_parser(
        "ifn-validate",
        help="valida a correspondencia tematica contra o IBGE no ponto")
    iva.add_argument("--points", required=True)
    iva.add_argument("--ibge-vegetation", required=True)
    iva.add_argument("--correspondence", required=True)
    iva.add_argument("--out-dir", required=True)
    iva.add_argument("--tipologia-col", default="tipologia")
    iva.add_argument("--source-col", default="fonte")
    iva.set_defaults(func=_cmd_ifn_validate)

    iex = sub.add_parser(
        "ifn-export",
        help="exporta pontos e pegadas do IFN enriquecido em GeoPackage")
    iex.add_argument("--enriched", required=True,
                     help="ifn_enriquecido.csv (com lon/lat)")
    iex.add_argument("--out", required=True, help="arquivo .gpkg")
    iex.add_argument("--crs", default="EPSG:4326")
    iex.set_defaults(func=_cmd_ifn_export)

    tgt = sub.add_parser(
        "target-consolidate",
        help="consolida 1 target por UA (Tier A pixel + Tier B celula)")
    tgt.add_argument("--gpkg", required=True,
                     help="ifn_candidatos_espaciais.gpkg")
    tgt.add_argument("--out-csv", required=True, help="tabela de target (.csv)")
    tgt.add_argument("--out-gpkg", default=None,
                     help="opcional: pontos do target (.gpkg)")
    tgt.add_argument("--manifest", default=None,
                     help="opcional: manifesto JSON com hashes e contagens")
    tgt.add_argument("--source", default="IFN/SFB")
    tgt.add_argument("--source-version", default="painel_biomassa_carbono_2025")
    tgt.add_argument("--max-plausible", type=float, default=500.0,
                     help="limite de plausibilidade da mediana (Mg/ha)")
    tgt.add_argument("--biomes", default=None,
                     help="filtro opcional, ex.: 'Amazonia,Cerrado'")
    tgt.set_defaults(func=_cmd_target_consolidate)

    fcat = sub.add_parser(
        "features-catalog",
        help="valida o catalogo de features e calcula o feature_set_hash")
    fcat.add_argument("--catalog", default="data/reference/features_biomassa.csv")
    fcat.add_argument("--groups", default=None,
                      help="grupos separados por virgula, ex.: 'Optico S2,SAR S1'")
    fcat.add_argument("--max-priority", type=int, default=None)
    fcat.add_argument("--include-experimental", action="store_true",
                      help="inclui permitida_experimental (SOC); exige ablacao")
    fcat.add_argument("--out", default=None,
                      help="opcional: CSV do conjunto selecionado")
    fcat.set_defaults(func=_cmd_features_catalog)

    tobs = sub.add_parser(
        "target-observations",
        help="converte o target por UA em observacoes canonicas (e amostra)")
    tobs.add_argument("--target-csv", required=True)
    tobs.add_argument("--out", required=True)
    tobs.add_argument("--manifest", default=None)
    tobs.add_argument("--tier", default=None,
                      help="filtro de tier, ex.: B (Tier B = ~1,1 km)")
    tobs.add_argument("--sample", type=int, default=None,
                      help="tamanho da amostra estratificada")
    tobs.add_argument("--seed", type=int, default=42)
    tobs.add_argument("--min-per-stratum", type=int, default=1)
    tobs.add_argument("--by", default="bioma,fitofisionomia_group",
                      help="colunas de estrato para a amostra")
    tobs.set_defaults(func=_cmd_target_observations)

    pfield = sub.add_parser("predict-field", help="prediz AGB com modelo campo-first")
    pfield.add_argument("--model", required=True)
    pfield.add_argument("--csv", required=True)
    pfield.add_argument("--out", default=None)
    pfield.add_argument("--target", default="agb_mg_ha")
    pfield.set_defaults(func=_cmd_predict_field)

    mreg = sub.add_parser("model-register", help="registra um modelo no champion/challenger")
    mreg.add_argument("--metrics", required=True)
    mreg.add_argument("--registry", required=True)
    mreg.add_argument("--model-id", default=None)
    mreg.add_argument("--family", default="field_first")
    mreg.add_argument("--status", choices=["challenger", "champion", "retired"],
                      default="challenger")
    mreg.add_argument("--notes", default="")
    mreg.set_defaults(func=_cmd_model_register)

    mlist = sub.add_parser("model-list", help="lista modelos registrados")
    mlist.add_argument("--registry", required=True)
    mlist.add_argument("--family", default=None)
    mlist.set_defaults(func=_cmd_model_list)

    mcomp = sub.add_parser("model-compare", help="compara modelos por metrica")
    mcomp.add_argument("--registry", required=True)
    mcomp.add_argument("--metric", default="rmse")
    mcomp.add_argument("--family", default=None)
    mcomp.set_defaults(func=_cmd_model_compare)

    mprom = sub.add_parser("model-promote", help="promove um challenger a champion")
    mprom.add_argument("--registry", required=True)
    mprom.add_argument("--model-id", required=True)
    mprom.add_argument("--reason", default="")
    mprom.set_defaults(func=_cmd_model_promote)

    fit = sub.add_parser("fitofisionomia", help="rasteriza fitofisionomia na grade de um raster")
    fit.add_argument("--vector", required=True)
    fit.add_argument("--template", required=True)
    fit.add_argument("--out", required=True)
    fit.add_argument("--attribute", default="legenda_2")
    fit.add_argument("--all-touched", action="store_true")
    fit.set_defaults(func=_cmd_fitofisionomia)

    frec = sub.add_parser("fitofisionomia-reconcile",
                          help="cruza fitofisionomia IBGE com classes MapBiomas")
    frec.add_argument("--fit-raster", required=True)
    frec.add_argument("--mapbiomas-raster", required=True)
    frec.add_argument("--codes", required=True)
    frec.add_argument("--classes", default="3,4")
    frec.add_argument("--out", default=None)
    frec.set_defaults(func=_cmd_fitofisionomia_reconcile)

    frecl = sub.add_parser("fitofisionomia-reclassify",
                           help="atualiza grupos do JSON de fitofisionomia")
    frecl.add_argument("--codes", required=True)
    frecl.add_argument("--out", default=None)
    frecl.set_defaults(func=_cmd_fitofisionomia_reclassify)

    fobs = sub.add_parser("features-observations", help="features para observacoes canonicas")
    fobs.add_argument("--observations", required=True)
    fobs.add_argument("--out", required=True)
    fobs.add_argument("--optical-dir", default=None)
    fobs.add_argument("--optical-pattern", default=None)
    fobs.add_argument("--optical-path", default=None)
    fobs.add_argument("--dem-dir", default=None)
    fobs.add_argument("--dem-pattern", default=None)
    fobs.add_argument("--dem-path", default=None)
    fobs.add_argument("--era5", default=None)
    fobs.add_argument("--mapbiomas-dir", default=None)
    fobs.add_argument("--half-m", type=float, default=500.0)
    fobs.add_argument("--no-history", action="store_true")
    fobs.add_argument("--history-start", type=int, default=2004)
    fobs.add_argument("--history-end", type=int, default=2018)
    fobs.add_argument("--fallback-year", type=int, default=None)
    fobs.add_argument("--max-rows", type=int, default=None)
    fobs.add_argument("--fitofisionomia-vector", default=None)
    fobs.add_argument("--fitofisionomia-attribute", default="legenda_2")
    fobs.set_defaults(func=_cmd_features_observations)

    tfield = sub.add_parser("train-field", help="RandomForest campo-first com bloco+buffer")
    tfield.add_argument("--csv", required=True)
    tfield.add_argument("--out-dir", required=True)
    tfield.add_argument("--target", default="agb_mg_ha")
    tfield.add_argument("--block-size-m", type=float, default=100000.0)
    tfield.add_argument("--buffer-m", type=float, default=25000.0)
    tfield.add_argument("--trees", type=int, default=400)
    tfield.add_argument("--min-samples-leaf", type=int, default=3)
    tfield.add_argument("--min-test", type=int, default=3)
    tfield.add_argument("--max-folds", type=int, default=50)
    tfield.add_argument("--conformal-coverage", type=float, default=0.90)
    tfield.add_argument("--algorithm", default="rf",
                        choices=["rf", "extra_trees", "gradient_boosting",
                                 "hist_gradient_boosting", "ridge"])
    tfield.add_argument("--seed", type=int, default=42)
    tfield.add_argument("--no-categoricals", action="store_true")
    tfield.add_argument("--domain-classes", default="3,4")
    tfield.set_defaults(func=_cmd_train_field)

    poly = sub.add_parser("polygon", help="estoque e incerteza por poligono (Produto C)")
    poly.add_argument("--input", required=True, help="GeoJSON/GPKG/SHP")
    poly.add_argument("--raster", required=True, help="mapa de AGB em CRS projetado")
    poly.add_argument("--year", type=int, default=None)
    poly.add_argument("--value-band", type=int, default=1)
    poly.add_argument("--class-band", type=int, default=None)
    poly.add_argument("--class-raster", default=None)
    poly.add_argument("--fitofisionomia-band", type=int, default=None)
    poly.add_argument("--fitofisionomia-raster", default=None)
    poly.add_argument("--fitofisionomia-codes", default=None)
    poly.add_argument("--fitofisionomia-groups", default=None,
                      help="grupos elegiveis, ex.: forest,savanna,campestre")
    poly.add_argument("--aoa-raster", default=None)
    poly.add_argument("--aoa-band", type=int, default=None)
    poly.add_argument("--domain-classes", default="3,4")
    poly.add_argument("--allow-outside-domain", action="store_true")
    poly.add_argument("--require-aoa", action="store_true")
    poly.add_argument("--block-size-m", type=float, default=5000.0)
    poly.add_argument("--chunk-rows", type=int, default=2048)
    poly.add_argument("--n-boot", type=int, default=400)
    poly.add_argument("--out", default=None)
    poly.set_defaults(func=_cmd_polygon)

    amap = sub.add_parser("annual-map", help="mapa anual de AGB por pixel (prototipo)")
    amap.add_argument("--model", required=True)
    amap.add_argument("--s2", required=True)
    amap.add_argument("--dem", required=True)
    amap.add_argument("--era5", required=True)
    amap.add_argument("--mapbiomas-dir", required=True)
    amap.add_argument("--year", type=int, required=True)
    amap.add_argument("--out", required=True)
    amap.add_argument("--block", type=int, default=100)
    amap.add_argument("--resolution", type=int, default=30)
    amap.add_argument("--training-csv", default=None)
    amap.add_argument("--residuals", default=None)
    amap.set_defaults(func=_cmd_annual_map)

    mint = sub.add_parser("map-intervals", help="adiciona IC90 a um mapa por pixel")
    mint.add_argument("--map", required=True)
    mint.add_argument("--residuals", required=True)
    mint.add_argument("--out", required=True)
    mint.set_defaults(func=_cmd_map_intervals)

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
    lss.add_argument("--dem-half", type=float, default=0.02)
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
