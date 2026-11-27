"""Mede a sobreposicao do Global Canopy Atlas (GCA) com as pegadas do IFN.

O GCA e LiDAR aerotransportado: nao entra como target nem feature (ADR-0022/0027).
Este utilitario quantifica onde ele pode servir como validacao estrutural.

Uso:
  python tools/gca_index_overlap.py \
    --gca-shp data/raw/gca/GCA_extended_public.shp \
    --pegadas data/processed/ifn_enrich_footprint/ifn_espacial.gpkg \
    --target-csv data/processed/target/target_uas_amazonia_cerrado.csv \
    --out-dir data/processed/gca
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gca-shp", required=True)
    ap.add_argument("--pegadas", required=True)
    ap.add_argument("--target-csv", default=None,
                    help="opcional: restringe as pegadas as UAs do target")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--bbox", default="-74,-34,-34,6",
                    help="oeste,sul,leste,norte")
    ap.add_argument("--encoding", default="latin1")
    args = ap.parse_args()

    west, south, east, north = (float(v) for v in args.bbox.split(","))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    gca = gpd.read_file(args.gca_shp, encoding=args.encoding)
    gca_br = gca[gca.intersects(box(west, south, east, north))].copy()
    peg = gpd.read_file(args.pegadas, layer="pegadas")
    if args.target_csv:
        target = pd.read_csv(args.target_csv, usecols=["ua"])
        peg = peg[peg["ua"].isin(set(target["ua"]))].copy()

    points = gpd.GeoDataFrame(
        peg[["ua", "bioma"]].copy(),
        geometry=peg.geometry.representative_point(), crs=peg.crs,
    )
    columns = ["IDunique", "biome", "realm", "access", "license",
               "minyear", "maxyear", "area_km2", "chm_mean", "chm_perc99",
               "geometry"]
    joined = gpd.sjoin(points, gca_br[columns], how="inner", predicate="within")

    intersection = gpd.overlay(
        peg[peg["ua"].isin(set(joined["ua"]))].to_crs(6933)[["ua", "geometry"]],
        gca_br[gca_br["IDunique"].isin(set(joined["IDunique"]))].to_crs(6933)[
            ["IDunique", "geometry"]],
        how="intersection", keep_geom_type=True,
    )
    intersection["area_ha"] = intersection.geometry.area / 10_000.0
    area_by_ua = intersection.groupby("ua")["area_ha"].sum()

    result = joined.drop(columns="geometry").merge(
        area_by_ua.rename("gca_area_ha"), left_on="ua", right_index=True, how="left"
    )
    result.to_csv(out_dir / "gca_sobreposicao_uas.csv", index=False,
                  encoding="utf-8")

    summary = {
        "gca_total": int(len(gca)),
        "gca_no_bbox": int(len(gca_br)),
        "gca_area_bbox_km2": float(gca_br["area_km2"].sum()),
        "gca_acesso": {str(k): int(v) for k, v in gca_br["access"].value_counts().items()},
        "gca_licencas": {str(k): int(v) for k, v in
                         gca_br["license"].value_counts().head(10).items()},
        "anos": [int(gca_br["minyear"].min()), int(gca_br["maxyear"].max())],
        "pegadas": int(len(peg)),
        "uas_com_sobreposicao": int(result["ua"].nunique()),
        "sobreposicao_por_bioma": {
            str(k): int(v) for k, v in result.groupby("bioma")["ua"].nunique().items()
        },
        "area_pegada_coberta_ha": float(area_by_ua.sum()),
        "output": str(out_dir / "gca_sobreposicao_uas.csv"),
    }
    (out_dir / "gca_sobreposicao_resumo.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
