"""Estratificação fitofisionômica: IBGE, MapBiomas e crosswalk (ADR-0029)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

DEFAULT_CROSSWALK = Path("data/reference/fitofisionomias_crosswalk.csv")

GROUP_BY_MAPBIOMAS = {
    2: "campestre",
    3: "forest",
    4: "savanna",
    6: "flooded_forest",
}


def normalize_name(value: Any) -> str:
    import re
    import unicodedata

    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_agb_range(value: Any) -> tuple[float, float]:
    text = str(value)
    parts = text.replace(",", ".").split("-")
    if len(parts) != 2:
        return (np.nan, np.nan)
    try:
        return (float(parts[0]), float(parts[1]))
    except ValueError:
        return (np.nan, np.nan)


def load_crosswalk(path: str | Path = DEFAULT_CROSSWALK) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8")
    df = df.copy()
    df["_key"] = df["fitofisionomia_ibge"].map(normalize_name)
    ranges = df["faixa_agbd_indicativa_mg_ha"].map(parse_agb_range)
    df["agbd_low_mg_ha"] = [r[0] for r in ranges]
    df["agbd_high_mg_ha"] = [r[1] for r in ranges]
    df["mapbiomas_codigo"] = pd.to_numeric(df["mapbiomas_codigo"], errors="coerce")
    return df


def _fallback_group(name: str) -> str:
    key = normalize_name(name)
    if any(token in key for token in ("campo", "vereda", "palmeiral", "estepe")):
        return "campestre"
    if any(token in key for token in ("savana", "cerrado")):
        return "savanna"
    if any(token in key for token in ("floresta", "mata", "campinarana", "bambu")):
        return "forest"
    return "unknown"


def classify_fitofisionomia(
    name: Any,
    biome: str | None = None,
    crosswalk: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Mapeia um nome IBGE/tipologia para nome canônico, grupo e classe MapBiomas."""
    table = load_crosswalk() if crosswalk is None else crosswalk
    key = normalize_name(name)
    if not key:
        return {
            "fitofisionomia": "",
            "fitofisionomia_group": "unknown",
            "mapbiomas_class": np.nan,
            "source_match": False,
        }

    subset = table
    if biome:
        norm_biome = normalize_name(biome)
        candidate = table[table["bioma"].map(normalize_name) == norm_biome]
        if len(candidate):
            subset = candidate

    exact = subset[subset["_key"] == key]
    if len(exact):
        row = exact.iloc[0]
        code = row.get("mapbiomas_codigo")
        return {
            "fitofisionomia": str(row["fitofisionomia_ibge"]),
            "fitofisionomia_group": GROUP_BY_MAPBIOMAS.get(int(code), _fallback_group(key))
            if pd.notna(code) else _fallback_group(key),
            "mapbiomas_class": float(code) if pd.notna(code) else np.nan,
            "source_match": True,
        }

    contains = subset[subset["_key"].map(lambda k: k in key or key in k)]
    if len(contains):
        row = contains.iloc[0]
        code = row.get("mapbiomas_codigo")
        return {
            "fitofisionomia": str(row["fitofisionomia_ibge"]),
            "fitofisionomia_group": GROUP_BY_MAPBIOMAS.get(int(code), _fallback_group(key))
            if pd.notna(code) else _fallback_group(key),
            "mapbiomas_class": float(code) if pd.notna(code) else np.nan,
            "source_match": False,
        }

    return {
        "fitofisionomia": str(name).strip(),
        "fitofisionomia_group": _fallback_group(key),
        "mapbiomas_class": np.nan,
        "source_match": False,
    }


def apply_crosswalk(
    df: pd.DataFrame,
    column: str,
    *,
    biome_column: str | None = "biome",
    crosswalk: pd.DataFrame | None = None,
) -> pd.DataFrame:
    table = load_crosswalk() if crosswalk is None else crosswalk
    out = df.copy()
    rows = []
    for _, row in out.iterrows():
        biome = row[biome_column] if biome_column and biome_column in out.columns else None
        rows.append(classify_fitofisionomia(row[column], biome=biome, crosswalk=table))
    mapped = pd.DataFrame(rows, index=out.index)
    for col in ("fitofisionomia", "fitofisionomia_group", "mapbiomas_class"):
        out[col] = mapped[col]
    return out


def rasterize_fitofisionomia(
    vector_path: str | Path,
    template_path: str | Path,
    out_path: str | Path,
    *,
    attribute: str,
    all_touched: bool = False,
) -> dict[str, Any]:
    """Rasteriza uma camada vetorial de fitofisionomia na grade de um raster de referência."""
    import json

    import geopandas as gpd
    import rasterio
    from rasterio.features import rasterize
    from shapely.validation import make_valid

    with rasterio.open(template_path) as template:
        profile = template.profile.copy()
        transform = template.transform
        crs = template.crs
        height, width = template.height, template.width
        bounds = template.bounds
    bbox_tuple = (bounds.left, bounds.bottom, bounds.right, bounds.top)

    if isinstance(vector_path, gpd.GeoDataFrame):
        gdf = vector_path.copy()
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")
        gdf = gdf.to_crs(crs)
        from shapely.geometry import box as _box

        gdf = gdf[gdf.geometry.intersects(_box(*bbox_tuple))]
    else:
        import pyogrio
        from pyproj import Transformer

        info = pyogrio.read_info(str(vector_path))
        vector_crs = info.get("crs")
        read_bbox = bbox_tuple
        if vector_crs:
            transformer = Transformer.from_crs(crs, vector_crs, always_xy=True)
            xs, ys = transformer.transform(
                [bounds.left, bounds.right, bounds.left, bounds.right],
                [bounds.bottom, bounds.bottom, bounds.top, bounds.top],
            )
            read_bbox = (min(xs), min(ys), max(xs), max(ys))
        gdf = gpd.read_file(vector_path, bbox=read_bbox)
        if gdf.crs is None:
            gdf = gdf.set_crs(vector_crs or "EPSG:4326")
        gdf = gdf.to_crs(crs)
    if gdf.empty:
        raise ValueError("camada de fitofisionomia vazia na extensão do template")
    if attribute not in gdf.columns:
        raise KeyError(f"atributo {attribute!r} ausente na camada")

    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    gdf["geometry"] = gdf.geometry.map(
        lambda g: g if g.is_valid else make_valid(g)
    )

    labels = sorted({str(v) for v in gdf[attribute].dropna().unique()})
    code_by_label = {label: i + 1 for i, label in enumerate(labels)}
    shapes = (
        (geom, code_by_label[str(label)])
        for geom, label in zip(gdf.geometry, gdf[attribute])
        if pd.notna(label)
    )
    codes = rasterize(
        shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=all_touched,
        dtype="int32",
    )

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    profile.update(dtype="int32", count=1, nodata=0, compress="deflate")
    with rasterio.open(out, "w", **profile) as dst:
        dst.write(codes, 1)
        dst.set_band_description(1, "fitofisionomia_code")

    code_items = []
    crosswalk_table = load_crosswalk()
    for label, code in code_by_label.items():
        mapped = classify_fitofisionomia(label, crosswalk=crosswalk_table)
        code_items.append({
            "code": code,
            "label": label,
            "group": mapped["fitofisionomia_group"],
            "mapbiomas_class": None if pd.isna(mapped["mapbiomas_class"])
            else float(mapped["mapbiomas_class"]),
        })
    code_table = {
        "attribute": attribute,
        "source": str(vector_path),
        "template": str(template_path),
        "codes": code_items,
    }
    out.with_suffix(".json").write_text(
        json.dumps(code_table, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return {"out": str(out), "n_classes": len(labels), "codes": code_by_label}
