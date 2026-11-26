"""Candidatos espaciais IFN: pixels/células com AGB atribuível (docs/60 §14).

Ideia: a pegada documentada (Cruz de Malta) é comparada com o MapBiomas do ano
e com o IBGE. Só recebe valor de AGB a unidade em que a classe é homogênea e
compatível com a fitofisionomia medida:

- **pixel** (precisão da coordenada >= 3 casas, incerteza <= ~56 m): pixels de
  30 m inteiramente dentro da pegada e da classe compatível;
- **célula** (precisão = 2 casas, célula de ~1,1 km): a célula inteira precisa
  ser homogênea (>= 95%) na classe compatível; a AGB é atribuída à célula, não
  a pixels individuais, porque a posição exata da pegada dentro dela é
  desconhecida.

Premissas declaradas em cada feição: homogeneidade da classe, representatividade
da AGB (0,4/0,8 ha) para a unidade atribuída e posição compatível com a
precisão da coordenada. Nada é interpolado nem reconstruído.

Uso:
  python tools/ifn_spatial_candidates.py \
    --enriched data/processed/ifn_enrich_footprint/ifn_enriquecido.csv \
    --panel data/raw/inventarios/sfb/dadosbiomassa_painel.csv \
    --correspondence data/reference/ifn_correspondencia_ibge.csv \
    --ibge-crosswalk data/reference/ibge_legenda1_para_mapbiomas.csv \
    --mapbiomas-pattern ".../mapbiomas_col11_{year}.tif" \
    --ibge-vegetation <vege_area.shp> \
    --out-gpkg data/processed/ifn_enrich_footprint/ifn_candidatos_espaciais.gpkg
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio import features
from rasterio.windows import Window, from_bounds
from shapely.geometry import box

from biomass_model.enrich_ifn import (
    MAPBIOMAS_CLASSES,
    _pixel_area_rows,
    compile_correspondence,
    compile_mapbiomas_correspondence,
    ifn_footprint,
    load_correspondence,
    load_mapbiomas_correspondence,
    mapbiomas_compatible_classes,
    match_category,
)

TIPOLOGIA = "tipologia_da_vegetacao"
USO = "classe_uso_da_terra"


def _panel_class_table(panel: str | Path) -> pd.DataFrame:
    """Área por tipologia e distribuição de AGB entre equações, por UA."""
    df = pd.read_csv(
        panel, sep=";", encoding="utf-8-sig", encoding_errors="replace",
        usecols=["ua", USO, TIPOLOGIA, "equacoes", "area_ha",
                 "agb_media_kg_por_ha"], low_memory=False)
    df = df.fillna("")
    for col in ("ua", USO, TIPOLOGIA, "equacoes"):
        df[col] = df[col].astype(str).str.strip()

    def _num(series):
        text = series.astype(str).str.strip()
        has_comma = text.str.contains(",", regex=False)
        text = text.where(
            ~has_comma,
            text.str.replace(".", "", regex=False).str.replace(
                ",", ".", regex=False))
        return pd.to_numeric(text, errors="coerce")

    df["area_ha"] = _num(df["area_ha"])
    df["agb"] = _num(df["agb_media_kg_por_ha"]) / 1000.0

    rows = []
    for (ua, tip), sub in df.groupby(["ua", TIPOLOGIA]):
        area = float(sub["area_ha"].max()) if sub["area_ha"].notna().any() else np.nan
        agb = sub["agb"].dropna()
        rows.append({
            "ua": ua, "tipologia": tip,
            "classes_uso": "|".join(sorted({c for c in sub[USO] if c})),
            "area_ha": area,
            "agb_min": float(agb.min()) if len(agb) else np.nan,
            "agb_mediana": float(agb.median()) if len(agb) else np.nan,
            "agb_max": float(agb.max()) if len(agb) else np.nan,
            "n_equacoes": int(sub["equacoes"].nunique()),
            "n_linhas": int(len(sub)),
        })
    per_tip = pd.DataFrame(rows)
    total = per_tip.groupby("ua")["area_ha"].apply(
        lambda s: float(pd.to_numeric(s, errors="coerce").sum()))
    per_tip["area_total_ua"] = per_tip["ua"].map(total)
    per_tip["share_tipologia"] = per_tip["area_ha"] / per_tip["area_total_ua"]
    return per_tip


def _unit_stats(geom, src, *, fractional: bool) -> dict:
    """Composição MapBiomas na unidade (fração de área ou contagem)."""
    out = {"classes": {}, "pixels": [], "total": 0.0}
    if src is None:
        return out
    win = from_bounds(*geom.bounds, transform=src.transform)
    row0 = max(0, int(np.floor(win.row_off)))
    col0 = max(0, int(np.floor(win.col_off)))
    row1 = min(src.height, int(np.ceil(win.row_off + win.height)))
    col1 = min(src.width, int(np.ceil(win.col_off + win.width)))
    height, width = row1 - row0, col1 - col0
    if height <= 0 or width <= 0:
        return out
    for off in range(0, height, 256):
        nrows = min(256, height - off)
        window = Window(col0, row0 + off, width, nrows)
        arr = src.read(1, window=window)
        if arr.size == 0:
            continue
        tr = src.window_transform(window)
        mask = features.geometry_mask(
            [geom], out_shape=arr.shape, transform=tr,
            all_touched=True, invert=True)
        if not mask.any():
            continue
        rr, cc = np.nonzero(mask)
        classes = arr[rr, cc].astype("int64")
        if not fractional:
            for cls, cnt in zip(*np.unique(classes, return_counts=True)):
                if cls <= 0:
                    continue
                out["classes"][int(cls)] = out["classes"].get(int(cls), 0) + int(cnt)
                out["total"] += int(cnt)
            continue
        rows = np.arange(nrows, dtype="float64") + off
        area_row = _pixel_area_rows(tr, rows)
        base = abs(tr.a * tr.e)
        for k in range(len(rr)):
            left = tr.c + cc[k] * tr.a
            top = tr.f + rr[k] * tr.e
            px = box(left, top + tr.e, left + tr.a, top)
            inter = px.intersection(geom)
            frac = inter.area / base if not inter.is_empty else 0.0
            if frac <= 0:
                continue
            cls = int(classes[k])
            if cls <= 0:
                continue
            area = float(area_row[rr[k]]) * frac
            out["classes"][cls] = out["classes"].get(cls, 0.0) + area
            out["total"] += area
            from shapely.geometry import Point
            center = Point(left + tr.a / 2.0, top + tr.e / 2.0)
            out["pixels"].append({
                "geometry": px, "classe": cls, "fracao": float(frac),
                "centro_dentro": bool(center.within(geom)),
            })
    return out


def _load_ibge(path: str | Path):
    ibge = gpd.read_file(path, columns=["legenda_1", "leg_sup"])
    if ibge.crs is None:
        ibge = ibge.set_crs("EPSG:4674")
    ibge = ibge.to_crs("EPSG:4326")
    ibge = ibge[ibge["leg_sup"].astype(str).str.startswith("Vegetação Natural")]
    ibge = ibge[ibge["legenda_1"].notna()].copy()
    ibge["legenda_1"] = ibge["legenda_1"].astype(str).str.strip()
    return ibge


def _ibge_stats(geom, ibge) -> dict:
    out = {"classes": {}, "total": 0.0}
    idx = ibge.sindex.query(geom, predicate="intersects")
    for _, row in ibge.iloc[list(idx)].iterrows():
        inter = row.geometry.intersection(geom)
        if inter.is_empty:
            continue
        area = float(inter.area)
        name = str(row["legenda_1"])
        out["classes"][name] = out["classes"].get(name, 0.0) + area
        out["total"] += area
    return out


def _share(stats: dict, codes) -> float:
    if not stats["total"]:
        return float("nan")
    compat = sum(v for k, v in stats["classes"].items() if k in set(codes))
    return compat / stats["total"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--enriched", required=True)
    ap.add_argument("--panel", required=True)
    ap.add_argument("--correspondence", required=True)
    ap.add_argument("--ibge-crosswalk", required=True)
    ap.add_argument("--mapbiomas-pattern", required=True)
    ap.add_argument("--ibge-vegetation", required=True)
    ap.add_argument("--out-gpkg", required=True)
    ap.add_argument("--min-share-tipologia", type=float, default=0.95)
    ap.add_argument("--min-share-mapbiomas", type=float, default=0.90)
    ap.add_argument("--min-share-celula", type=float, default=0.95)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    corr = compile_correspondence(load_correspondence(args.correspondence))
    mb_corr = compile_mapbiomas_correspondence(
        load_mapbiomas_correspondence(args.ibge_crosswalk))
    enriched = pd.read_csv(args.enriched)
    if args.limit:
        enriched = enriched.head(args.limit)
    per_tip = _panel_class_table(args.panel)
    per_tip = per_tip.sort_values("area_ha", ascending=False)
    dominant = per_tip.drop_duplicates("ua", keep="first").set_index("ua")
    ibge = _load_ibge(args.ibge_vegetation)

    sources: dict[int, rasterio.DatasetReader] = {}

    def get_src(year: int):
        if year not in sources:
            path = Path(str(args.mapbiomas_pattern).format(year=year))
            if not path.exists():
                return None
            sources[year] = rasterio.open(path)
        return sources[year]

    rows, pixel_rows, cell_rows = [], [], []
    try:
        for _, rec in enriched.iterrows():
            ua = str(rec["ua"])
            base = {
                "ua": ua, "ano": rec.get("ano"), "bioma": rec.get("bioma"),
                "uf": rec.get("uf"), "municipio": rec.get("municipio"),
                "tipologia": rec.get("tipologias_ifn", ""),
                "fitofisionomia": rec.get("tip_fitofisionomia_ibge", ""),
                "agb_mg_ha": rec.get("agb_mg_ha"),
                "precisao_decimais": rec.get("suporte_precisao_decimais"),
                "incerteza_max_m": rec.get("suporte_incerteza_max_m"),
            }
            fp = None
            if pd.notna(rec.get("lon")) and pd.notna(rec.get("lat")):
                fp = ifn_footprint(float(rec["lon"]), float(rec["lat"]),
                                   str(rec.get("bioma", "")), None)
            base["geometry"] = fp["geometry"] if fp else None
            base["area_pegada_ha"] = fp["area_ha"] if fp else np.nan

            def reject(reason, extra=None):
                row = {**base, "caso": "nao", "motivo": reason}
                if extra:
                    row.update(extra)
                rows.append(row)

            if fp is None:
                reject("sem_coordenada")
                continue
            if pd.isna(rec.get("ano")):
                reject("sem_ano_de_campo")
                continue
            if ua not in dominant.index:
                reject("sem_tabela_de_classes")
                continue
            dom = dominant.loc[ua]
            base.update({
                "tipologia_dominante": dom["tipologia"],
                "share_tipologia": round(float(dom["share_tipologia"]), 4)
                if pd.notna(dom["share_tipologia"]) else np.nan,
                "classes_uso_tipologia": dom["classes_uso"],
                "agb_min": dom["agb_min"], "agb_mediana": dom["agb_mediana"],
                "agb_max": dom["agb_max"], "n_equacoes": dom["n_equacoes"],
                "area_tipologia_ha": dom["area_ha"],
            })
            if pd.isna(dom["share_tipologia"]) or \
                    float(dom["share_tipologia"]) < args.min_share_tipologia:
                reject("tipologia_nao_dominante")
                continue
            if "|" in str(dom["classes_uso"]):
                reject("classe_de_uso_ambigua")
                continue
            match = match_category(dom["tipologia"], TIPOLOGIA, corr)
            if match["vinculo"] != "univoco" or not match["classe_ibge"]:
                reject(f"correspondencia_{match['vinculo']}")
                continue
            codes = mapbiomas_compatible_classes(
                mb_corr, match["classe_ibge"], str(rec.get("bioma", "")))
            if not codes:
                reject("sem_classe_mapbiomas_compativel")
                continue
            base["ibge_classe"] = match["classe_ibge"]
            base["mapbiomas_compativeis"] = "|".join(str(c) for c in codes)

            # plausibilidade da AGB (a matriz de equações tem extremos)
            agb_med = dom["agb_mediana"]
            agb_min = dom["agb_min"]
            agb_max = dom["agb_max"]
            spread = (float(agb_max) / float(agb_min)
                      if pd.notna(agb_min) and float(agb_min) > 0 else np.nan)
            base["spread_razao"] = round(spread, 1) if pd.notna(spread) else np.nan
            if pd.isna(agb_med) or float(agb_med) <= 0 or float(agb_med) > 500:
                reject("agb_implausivel")
                continue

            precision = int(rec["suporte_precisao_decimais"]) \
                if pd.notna(rec.get("suporte_precisao_decimais")) else 0
            year = int(rec["ano"])
            src = get_src(year)
            if src is None:
                reject("sem_raster_do_ano")
                continue

            if precision >= 3:
                stats = _unit_stats(fp["geometry"], src, fractional=True)
                if not stats["total"]:
                    reject("sem_dado_mapbiomas")
                    continue
                share = _share(stats, codes)
                base["mb_share_compativel"] = round(share, 4)
                base["mb_classe_dominante"] = max(
                    stats["classes"], key=stats["classes"].get)
                if share < args.min_share_mapbiomas:
                    reject("mapbiomas_incompativel")
                    continue
                px = [p for p in stats["pixels"]
                      if p["classe"] in set(codes) and p["centro_dentro"]]
                if not px:
                    reject("sem_pixel_inteiro_compativel")
                    continue
                ib = _ibge_stats(fp["geometry"], ibge)
                base["ibge_share_compativel"] = (
                    round(_share(ib, [match["classe_ibge"]]), 4)
                    if ib["total"] else np.nan)
                base["ibge_classe_dominante"] = (
                    max(ib["classes"], key=ib["classes"].get)
                    if ib["classes"] else "")
                base.update({"caso": "pixel", "motivo": ""})
                rows.append(base)
                for p in px:
                    pixel_rows.append({
                        "ua": ua, "ano": year,
                        "fitofisionomia": match["classe_ibge"],
                        "tipologia": dom["tipologia"],
                        "classe_mapbiomas": p["classe"],
                        "classe_mapbiomas_nome": MAPBIOMAS_CLASSES.get(
                            p["classe"], ""),
                        "agb_min_mg_ha": dom["agb_min"],
                        "agb_mediana_mg_ha": dom["agb_mediana"],
                        "agb_max_mg_ha": dom["agb_max"],
                        "n_equacoes": dom["n_equacoes"],
                        "precisao_decimais": precision,
                        "fracao_coberta": round(p["fracao"], 4),
                        "spread_razao": base["spread_razao"],
                        "agb_plausivel": True,
                        "mb_share_compativel": base["mb_share_compativel"],
                        "ibge_share_compativel": base.get(
                            "ibge_share_compativel"),
                        "hipotese": "classe_homogenea_e_centro_do_pixel_na_"
                                    "pegada; AGB medida em 0,4/0,8 ha",
                        "geometry": p["geometry"],
                    })
            elif precision == 2:
                cell = box(float(rec["lon"]) - 0.005, float(rec["lat"]) - 0.005,
                           float(rec["lon"]) + 0.005, float(rec["lat"]) + 0.005)
                stats = _unit_stats(cell, src, fractional=False)
                if not stats["total"]:
                    reject("sem_dado_mapbiomas")
                    continue
                share = _share(stats, codes)
                base["mb_share_compativel"] = round(share, 4)
                base["mb_classe_dominante"] = max(
                    stats["classes"], key=stats["classes"].get)
                if share < args.min_share_celula:
                    reject("celula_nao_homogenea")
                    continue
                ib = _ibge_stats(cell, ibge)
                base.update({
                    "ibge_share_compativel": (
                        round(_share(ib, [match["classe_ibge"]]), 4)
                        if ib["total"] else np.nan),
                    "ibge_classe_dominante": (
                        max(ib["classes"], key=ib["classes"].get)
                        if ib["classes"] else ""),
                    "caso": "celula", "motivo": "", "geometry": cell,
                })
                rows.append(base)
                cell_rows.append({
                    "ua": ua, "ano": year,
                    "fitofisionomia": match["classe_ibge"],
                    "tipologia": dom["tipologia"],
                    "classe_mapbiomas": base["mb_classe_dominante"],
                    "classe_mapbiomas_nome": MAPBIOMAS_CLASSES.get(
                        base["mb_classe_dominante"], ""),
                    "agb_min_mg_ha": dom["agb_min"],
                    "agb_mediana_mg_ha": dom["agb_mediana"],
                    "agb_max_mg_ha": dom["agb_max"],
                    "n_equacoes": dom["n_equacoes"],
                    "area_celula_km2": round(
                        (cell.bounds[2] - cell.bounds[0]) * 111.320
                        * np.cos(np.radians(
                            (cell.bounds[1] + cell.bounds[3]) / 2.0))
                        * (cell.bounds[3] - cell.bounds[1]) * 110.574, 4),
                    "spread_razao": base["spread_razao"],
                    "agb_plausivel": True,
                    "mb_share_compativel": base["mb_share_compativel"],
                    "ibge_share_compativel": base.get(
                        "ibge_share_compativel"),
                    "hipotese": "celula_1km_homogenea; posicao da pegada "
                                "incerta dentro da celula",
                    "geometry": cell,
                })
            else:
                reject("precisao_insuficiente")
    finally:
        for ds in sources.values():
            ds.close()

    out = Path(args.out_gpkg)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    cruz = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    cruz.to_file(out, layer="cruz_avaliada", driver="GPKG")
    if pixel_rows:
        gpd.GeoDataFrame(pixel_rows, geometry="geometry",
                         crs="EPSG:4326").to_file(
            out, layer="pixels_confirmados", driver="GPKG")
    if cell_rows:
        gpd.GeoDataFrame(cell_rows, geometry="geometry",
                         crs="EPSG:4326").to_file(
            out, layer="celulas_confirmadas", driver="GPKG")

    summary = {
        "out": str(out),
        "uas_avaliadas": int(len(cruz)),
        "caso_pixel": int((cruz["caso"] == "pixel").sum()),
        "caso_celula": int((cruz["caso"] == "celula").sum()),
        "nao_elegivel": int((cruz["caso"] == "nao").sum()),
        "pixels_confirmados": int(len(pixel_rows)),
        "celulas_confirmadas": int(len(cell_rows)),
        "motivos": cruz.loc[cruz["caso"] == "nao", "motivo"]
        .value_counts().to_dict(),
        "por_fitofisionomia_pixel": (pd.DataFrame(pixel_rows)
                                     .groupby("fitofisionomia").size()
                                     .to_dict() if pixel_rows else {}),
        "por_fitofisionomia_celula": (pd.DataFrame(cell_rows)
                                      .groupby("fitofisionomia").size()
                                      .to_dict() if cell_rows else {}),
        "premissas": [
            "classe homogenea na unidade de atribuicao (pegada ou celula)",
            "AGB medida em 0,4/0,8 ha representa a unidade atribuida",
            "posicao compativel com a precisao da coordenada publicada",
            "IBGE usado apenas como confirmacao (sem dimensao temporal)",
        ],
    }
    (out.parent / "ifn_candidatos_espaciais_resumo.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
