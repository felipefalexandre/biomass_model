"""Mapa anual de AGB por pixel (protótipo 1 km a partir de features anuais S2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling

from ..features import (S2_BANDS, era5_features, load_era5, mapbiomas_class,
                        terrain_features)


def _block_mean(arr: np.ndarray, nb: int, block: int) -> np.ndarray:
    """Média de blocos block×block; ignora NaN; usa o canto superior esquerdo."""
    out = np.full((nb, nb), np.nan, dtype="float32")
    for i in range(nb):
        for j in range(nb):
            win = arr[i * block:(i + 1) * block, j * block:(j + 1) * block]
            if np.isfinite(win).any():
                out[i, j] = np.nanmean(win)
    return out


def _mb_history(mapbiomas_dir: Path, lon: np.ndarray, lat: np.ndarray,
                start: int = 2004, end: int = 2018) -> dict[str, np.ndarray]:
    years = list(range(start, end + 1))
    series = np.stack([mapbiomas_class(mapbiomas_dir, y, lon, lat) for y in years])
    in_dom = np.isin(series, [3, 4])
    changes = (np.diff(series, axis=0) != 0).sum(axis=0)
    last = np.full(series.shape[1], -1)
    for i in range(1, len(years)):
        moved = series[i] != series[i - 1]
        last[moved] = i
    since = np.where(last >= 0, len(years) - 1 - last, len(years))
    out = {
        "mb_domain_years": in_dom.sum(axis=0).astype("float32"),
        "mb_forest_years": (series == 3).sum(axis=0).astype("float32"),
        "mb_savanna_years": (series == 4).sum(axis=0).astype("float32"),
        "mb_changes": changes.astype("float32"),
        "mb_years_since_change": since.astype("float32"),
    }
    for y in (2004, 2010, 2014, 2018):
        out[f"mb_class_{y}"] = series[years.index(y)].astype("float32")
    return out


def build_cell_features(annual_tif: str | Path, dem_tif: str | Path,
                        era5_nc: str | Path, mapbiomas_dir: str | Path,
                        year: int, block: int = 33) -> tuple[pd.DataFrame, dict[str, Any]]:
    with rasterio.open(annual_tif) as ds:
        nb = ds.width // block
        names = ds.descriptions or tuple(S2_BANDS[: ds.count])
        arrays = ds.read(out_shape=(ds.count, ds.height, ds.width))
        transform, crs = ds.transform, ds.crs
        cols, rows = np.meshgrid(np.arange(nb), np.arange(nb))
        xs = transform.c + (cols * block + block / 2) * transform.a
        ys = transform.f + (rows * block + block / 2) * transform.e
        to_wgs = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        lon, lat = to_wgs.transform(xs.ravel(), ys.ravel())

    data: dict[str, np.ndarray] = {}
    for i, name in enumerate(names):
        data[f"s2_{name}"] = _block_mean(arrays[i].astype("float32"), nb, block).ravel()

    cells = pd.DataFrame({"lon": lon, "lat": lat})
    cells = pd.concat([cells, terrain_features(dem_tif, lon, lat)], axis=1)
    era5 = load_era5(era5_nc)
    cells = pd.concat([cells, era5_features(era5, lon, lat,
                                            pd.Series([f"{year}-07-01"] * len(lon)))], axis=1)
    for k, v in _mb_history(Path(mapbiomas_dir), lon, lat).items():
        cells[k] = v
    cells["mapbiomas_class"] = mapbiomas_class(mapbiomas_dir, year, lon, lat)
    for i, name in enumerate(names):
        cells[f"s2_{name}"] = data[f"s2_{name}"]
    cells["_nb"] = nb
    return cells, {"nb": nb, "crs": str(crs), "transform": transform,
                   "cell_size_m": abs(transform.a) * block}


def predict_map(model_path: str | Path, annual_tif: str | Path, dem_tif: str | Path,
                era5_nc: str | Path, mapbiomas_dir: str | Path, year: int,
                out: str | Path, block: int = 33) -> dict[str, Any]:
    import joblib

    bundle = joblib.load(model_path)
    if isinstance(bundle, dict):
        model, feats = bundle["model"], bundle["features"]
    else:
        model, feats = bundle, list(bundle.feature_names_in_)
    cells, meta = build_cell_features(annual_tif, dem_tif, era5_nc, mapbiomas_dir,
                                      year, block=block)
    X = cells.reindex(columns=feats).to_numpy(dtype="float64")
    pred = np.clip(model.predict(X), 0, 600)
    valid = cells["mapbiomas_class"].isin([3, 4]).to_numpy()
    if "s2_valid_fraction" in cells:
        valid = valid & (cells["s2_valid_fraction"].to_numpy() > 0.3)
    pred = np.where(valid, pred, np.nan)

    nb = int(meta["nb"])
    profile = {
        "driver": "GTiff", "width": nb, "height": nb, "count": 3,
        "dtype": "float32", "crs": meta["crs"], "transform": meta["transform"],
        "compress": "deflate", "predictor": 3, "nodata": np.nan,
    }
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(pred.reshape(nb, nb).astype("float32"), 1)
        dst.write(valid.reshape(nb, nb).astype("float32"), 2)
        dst.write(cells["s2_valid_fraction"].to_numpy().reshape(nb, nb).astype("float32"), 3)
        dst.set_band_description(1, "agbd_mg_ha")
        dst.set_band_description(2, "domain_mask")
        dst.set_band_description(3, "s2_valid_fraction")

    info = {
        "year": year, "resolution_m": meta["cell_size_m"], "n_cells": int(nb * nb),
        "n_valid": int(np.isfinite(pred).sum()),
        "agbd_mean": float(np.nanmean(pred)), "agbd_min": float(np.nanmin(pred)),
        "agbd_max": float(np.nanmax(pred)), "out": str(out_path),
        "model": str(model_path), "features": len(feats),
        "note": "protótipo: sem IC/AOA; treinar e validar antes de uso MRV",
    }
    out_path.with_suffix(".json").write_text(json.dumps(info, indent=2, ensure_ascii=False),
                                             encoding="utf-8")
    return info
