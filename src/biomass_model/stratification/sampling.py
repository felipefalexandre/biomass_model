"""Amostragem de fitofisionomia IBGE em pontos (sem inventar correspondência)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def sample_fitofisionomia_vector(
    vector_path: str | Path,
    lon: np.ndarray,
    lat: np.ndarray,
    *,
    attribute: str = "legenda_2",
    bbox_pad: float = 0.05,
) -> pd.DataFrame:
    """Retorna fitofisionomia IBGE para cada ponto, usando interseção espacial.

    Pontos fora de qualquer polígono ficam vazios; não há preenchimento por vizinho.
    """
    import geopandas as gpd
    from shapely.geometry import Point

    from . import classify_fitofisionomia

    lon = np.asarray(lon, dtype="float64")
    lat = np.asarray(lat, dtype="float64")
    if len(lon) != len(lat):
        raise ValueError("lon e lat com tamanhos diferentes")
    out = pd.DataFrame({
        "ibge_fitofisionomia": "",
        "ibge_group": "",
        "ibge_mapbiomas_class": np.nan,
        "ibge_area_km2": np.nan,
    }, index=range(len(lon)))
    valid = np.isfinite(lon) & np.isfinite(lat)
    if not valid.any():
        return out

    bbox = (
        float(np.nanmin(lon) - bbox_pad), float(np.nanmin(lat) - bbox_pad),
        float(np.nanmax(lon) + bbox_pad), float(np.nanmax(lat) + bbox_pad),
    )
    gdf = gpd.read_file(vector_path, bbox=bbox)
    if gdf.empty:
        return out
    if attribute not in gdf.columns:
        raise KeyError(f"atributo {attribute!r} ausente na camada")
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    points = gpd.GeoDataFrame(
        {"_idx": np.flatnonzero(valid)},
        geometry=[Point(x, y) for x, y in zip(lon[valid], lat[valid])],
        crs="EPSG:4326",
    ).to_crs(gdf.crs)

    area_col = "ar_poli_km" if "ar_poli_km" in gdf.columns else None
    cols = ["geometry", attribute] + ([area_col] if area_col else [])
    joined = gpd.sjoin(points, gdf[cols], how="left", predicate="intersects")
    if joined.empty:
        return out
    joined = joined.sort_values(
        [area_col] if area_col else [attribute], ascending=False
    ).drop_duplicates("_idx", keep="first")

    for _, row in joined.iterrows():
        idx = int(row["_idx"])
        label = row.get(attribute)
        if pd.isna(label):
            continue
        mapped = classify_fitofisionomia(str(label))
        out.loc[idx, "ibge_fitofisionomia"] = str(label)
        out.loc[idx, "ibge_group"] = mapped["fitofisionomia_group"]
        out.loc[idx, "ibge_mapbiomas_class"] = mapped["mapbiomas_class"]
        if area_col:
            out.loc[idx, "ibge_area_km2"] = row.get(area_col)
    return out
