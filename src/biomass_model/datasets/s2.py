"""Sentinel-2 L2A: janela geografica via STAC publico + COGs na AWS.

Nao exige conta. A janela e recortada em torno de um ponto; a cena escolhida
e a de menor cobertura de nuvem no periodo.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from pyproj import Transformer
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.windows import Window, from_bounds

from ..manifest import build_manifest, write_manifest

STAC_URL = "https://earth-search.aws.element84.com/v1"
COLLECTION = "sentinel-2-l2a"
BANDS = ["blue", "green", "red", "nir", "swir16", "swir22"]
SCL_BAD = {0, 1, 3, 8, 9, 10, 11}
LICENSE = "Copernicus Sentinel data policy (atribuicao)"
ACCOUNT = "nenhuma"


def search_items(
    lon: float,
    lat: float,
    start: str,
    end: str,
    size: int = 1600,
    max_cloud: float = 20.0,
    max_items: int = 50,
) -> list[Any]:
    half_deg = size * 10 / 111_000 / 2
    bbox = [lon - half_deg, lat - half_deg, lon + half_deg, lat + half_deg]
    catalog = Client.open(STAC_URL)
    search = catalog.search(
        collections=[COLLECTION],
        bbox=bbox,
        datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": max_cloud}},
        max_items=max_items,
    )
    items = list(search.items())
    items.sort(key=lambda it: it.properties.get("eo:cloud_cover", 100.0))
    return items


def _read_band(ds: rasterio.DatasetReader, bounds: tuple, size: int, resampling: Resampling) -> np.ndarray:
    win = from_bounds(*bounds, transform=ds.transform).round()
    data = ds.read(1, window=win, out_shape=(size, size), resampling=resampling)
    return data.astype("float32")


def fetch_window(
    lon: float,
    lat: float,
    start: str,
    end: str,
    out: str | Path,
    size: int = 1600,
    max_cloud: float = 20.0,
    manifest: bool = True,
) -> dict[str, Any]:
    items = search_items(lon, lat, start, end, size=size, max_cloud=max_cloud)
    if not items:
        raise RuntimeError("nenhuma cena Sentinel-2 encontrada no periodo/limite de nuvem")
    item = items[0]

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(item.assets["red"].href) as ref:
        to_crs = Transformer.from_crs("EPSG:4326", ref.crs, always_xy=True)
        x, y = to_crs.transform(lon, lat)
        half = size // 2
        col = min(max(int((x - ref.transform.c) / ref.transform.a), half), ref.width - half - 1)
        row = min(max(int((y - ref.transform.f) / ref.transform.e), half), ref.height - half - 1)
        win = Window(col - half, row - half, size, size)
        bounds = ref.window_bounds(win)
        crs = ref.crs
        transform = ref.window_transform(win)

    layers: list[np.ndarray] = []
    descriptions: list[str] = []
    for name in BANDS:
        with rasterio.open(item.assets[name].href) as ds:
            layers.append(_read_band(ds, bounds, size, Resampling.bilinear))
        descriptions.append(name)

    blue, green, red, nir, swir16, swir22 = layers
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = np.where(nir + red > 0, (nir - red) / (nir + red), np.nan)
        ndmi = np.where(nir + swir16 > 0, (nir - swir16) / (nir + swir16), np.nan)
    nirv = ndvi * nir
    layers += [ndvi.astype("float32"), ndmi.astype("float32"), nirv.astype("float32")]
    descriptions += ["ndvi", "ndmi", "nirv"]

    with rasterio.open(item.assets["scl"].href) as ds:
        scl = _read_band(ds, bounds, size, Resampling.nearest).astype("uint8")
    layers.append(scl.astype("float32"))
    descriptions.append("scl")

    profile = {
        "driver": "GTiff",
        "width": size,
        "height": size,
        "count": len(layers),
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "compress": "deflate",
        "predictor": 3,
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "nodata": np.nan,
    }
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(np.stack(layers).astype("float32"))
        for i, name in enumerate(descriptions, start=1):
            dst.set_band_description(i, name)

    valid = ~np.isin(scl, list(SCL_BAD))
    meta = {
        "item_id": item.id,
        "datetime": item.datetime.isoformat() if item.datetime else None,
        "cloud_cover": item.properties.get("eo:cloud_cover"),
        "tile": item.id.split("_")[1],
        "center_lon": lon,
        "center_lat": lat,
        "size_px": size,
        "crs": str(crs),
        "valid_fraction": float(valid.mean()),
        "bands": descriptions,
        "source": item.assets["red"].href,
        "candidates": [{"id": it.id, "cloud": it.properties.get("eo:cloud_cover")} for it in items[:10]],
    }
    meta_path = out_path.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    if manifest:
        write_manifest(
            build_manifest(
                "s2",
                {"lon": lon, "lat": lat, "start": start, "end": end, "size": size,
                 "max_cloud": max_cloud, "item_id": item.id},
                [out_path, meta_path],
                license=LICENSE,
                account=ACCOUNT,
                source=item.assets["red"].href,
            )
        )
    return {"path": str(out_path), "meta": str(meta_path), **meta}
