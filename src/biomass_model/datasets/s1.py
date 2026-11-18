"""Sentinel-1 RTC (Microsoft Planetary Computer, sem conta).

Usa a colecao `sentinel-1-rtc`; os assets sao COGs e precisam de SAS assinado
(`planetary_computer.sign`). Composicao por mediana em potencia linear e
conversao para dB.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import planetary_computer
import rasterio
from pyproj import Transformer
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.windows import Window, from_bounds

from ..manifest import build_manifest, write_manifest

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "sentinel-1-rtc"
LICENSE = "Copernicus Sentinel-1 / ASF (atribuicao)"
ACCOUNT = "nenhuma (MPC assina o acesso)"


def search_items(lon: float, lat: float, start: str, end: str, size: int = 1600,
                 max_items: int = 20) -> list[Any]:
    half_deg = size * 10 / 111_000 / 2
    bbox = [lon - half_deg, lat - half_deg, lon + half_deg, lat + half_deg]
    catalog = Client.open(STAC_URL)
    search = catalog.search(collections=[COLLECTION], bbox=bbox,
                            datetime=f"{start}/{end}", max_items=max_items)
    items = [it for it in search.items() if {"vv", "vh"} <= set(it.assets)]
    items.sort(key=lambda it: it.datetime or "")
    return items


def _read_asset(ds: rasterio.DatasetReader, bounds: tuple, size: int) -> np.ndarray:
    win = from_bounds(*bounds, transform=ds.transform).round()
    data = ds.read(1, window=win, out_shape=(size, size),
                   resampling=Resampling.bilinear).astype("float32")
    return data


def fetch_s1(
    lon: float,
    lat: float,
    start: str,
    end: str,
    out: str | Path,
    size: int = 1600,
    max_items: int = 8,
    manifest: bool = True,
) -> dict[str, Any]:
    items = search_items(lon, lat, start, end, size=size)
    if not items:
        raise RuntimeError("nenhuma cena Sentinel-1 RTC encontrada")
    items = items[:max_items]
    signed = [planetary_computer.sign(it) for it in items]

    with rasterio.open(signed[0].assets["vv"].href) as ref:
        to_crs = Transformer.from_crs("EPSG:4326", ref.crs, always_xy=True)
        x, y = to_crs.transform(lon, lat)
        half = size // 2
        col = min(max(int((x - ref.transform.c) / ref.transform.a), half), ref.width - half - 1)
        row = min(max(int((y - ref.transform.f) / ref.transform.e), half), ref.height - half - 1)
        win = Window(col - half, row - half, size, size)
        bounds = ref.window_bounds(win)
        crs = ref.crs
        transform = ref.window_transform(win)

    def stack(name):
        out_layers = []
        for item in signed:
            with rasterio.open(item.assets[name].href) as ds:
                out_layers.append(_read_asset(ds, bounds, size))
        arr = np.stack(out_layers)
        arr[~np.isfinite(arr) | (arr <= 0)] = np.nan
        return arr

    vv = stack("vv")
    vh = stack("vh")
    vv_med = np.nanmedian(vv, axis=0)
    vh_med = np.nanmedian(vh, axis=0)
    nobs = np.isfinite(vv).sum(axis=0).astype("float32")
    with np.errstate(divide="ignore", invalid="ignore"):
        vv_db = 10.0 * np.log10(vv_med)
        vh_db = 10.0 * np.log10(vh_med)
        ratio_db = vh_db - vv_db
        rvi = 4.0 * vh_med / (vv_med + vh_med)

    layers = [vv_db, vh_db, ratio_db, rvi, nobs]
    names = ["vv_db", "vh_db", "vh_vv_db", "rvi", "nobs"]
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff", "width": size, "height": size, "count": len(layers),
        "dtype": "float32", "crs": crs, "transform": transform,
        "compress": "deflate", "predictor": 3, "tiled": True,
        "blockxsize": 512, "blockysize": 512, "nodata": np.nan,
    }
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(np.stack(layers).astype("float32"))
        for i, name in enumerate(names, start=1):
            dst.set_band_description(i, name)

    meta = {
        "lon": lon, "lat": lat, "start": start, "end": end, "size_px": size,
        "crs": str(crs), "items": [it.id for it in items], "n_items": len(items),
        "orbit_state": items[0].properties.get("sat:orbit_state"),
        "bands": names, "source": items[0].assets["vv"].href,
        "median_nobs": float(np.nanmedian(nobs)),
    }
    meta_path = out_path.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    if manifest:
        write_manifest(build_manifest(
            "s1", {"lon": lon, "lat": lat, "start": start, "end": end,
                   "size": size, "max_items": max_items, "items": meta["items"]},
            [out_path, meta_path], license=LICENSE, account=ACCOUNT,
            source="https://planetarycomputer.microsoft.com/dataset/sentinel-1-rtc",
        ))
    return {"path": str(out_path), "meta": str(meta_path), **meta}
