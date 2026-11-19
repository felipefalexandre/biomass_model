"""Sentinel-2 L2A: janela geografica via STAC publico + COGs na AWS.

Nao exige conta. A janela e recortada em torno de um ponto; a cena escolhida
e a de menor cobertura de nuvem no periodo.
"""

from __future__ import annotations

import json
import warnings
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


def _window_for_items(items, lon: float, lat: float, size: int):
    with rasterio.open(items[0].assets["red"].href) as ref:
        to_crs = Transformer.from_crs("EPSG:4326", ref.crs, always_xy=True)
        x, y = to_crs.transform(lon, lat)
        half = size // 2
        col = min(max(int((x - ref.transform.c) / ref.transform.a), half), ref.width - half - 1)
        row = min(max(int((y - ref.transform.f) / ref.transform.e), half), ref.height - half - 1)
        win = Window(col - half, row - half, size, size)
        return win, ref.window_bounds(win), ref.crs, ref.window_transform(win)


def fetch_composite(
    lon: float,
    lat: float,
    start: str,
    end: str,
    out: str | Path,
    size: int = 1600,
    max_items: int = 10,
    max_cloud: float = 30.0,
    manifest: bool = True,
) -> dict[str, Any]:
    """Mediana multi-data de S2 (bandas e indices) na janela do piloto."""
    items = search_items(lon, lat, start, end, size=size, max_cloud=max_cloud)
    if not items:
        raise RuntimeError("nenhuma cena Sentinel-2 encontrada")
    tile = items[0].id.split("_")[1]
    items = [it for it in items if it.id.split("_")[1] == tile][:max_items]
    _, bounds, crs, transform = _window_for_items(items, lon, lat, size)

    def stack(name, resampling=Resampling.bilinear):
        layers = []
        for item in items:
            with rasterio.open(item.assets[name].href) as ds:
                layers.append(_read_band(ds, bounds, size, resampling))
        return np.stack(layers)

    scl = stack("scl", Resampling.nearest)
    valid = ~np.isin(scl.astype("uint8"), list(SCL_BAD))

    def masked_median(arr):
        arr = arr.astype("float32").copy()
        arr[~valid] = np.nan
        return np.nanmedian(arr, axis=0)

    nir = stack("nir")
    red = stack("red")
    swir16 = stack("swir16")
    med_nir, med_red = masked_median(nir), masked_median(red)
    med_green = masked_median(stack("green"))
    med_blue = masked_median(stack("blue"))
    med_swir16 = masked_median(swir16)
    med_swir22 = masked_median(stack("swir22"))

    def scene_index(stack_a, stack_b):
        with np.errstate(divide="ignore", invalid="ignore"):
            idx = np.where(stack_a + stack_b > 0, (stack_a - stack_b) / (stack_a + stack_b), np.nan)
        idx[~valid] = np.nan
        return np.nanmedian(idx, axis=0)

    ndvi = scene_index(nir, red)
    ndmi = scene_index(nir, swir16)
    nirv = ndvi * med_nir
    nobs = valid.sum(axis=0).astype("float32")

    layers = [med_blue, med_green, med_red, med_nir, med_swir16, med_swir22,
              ndvi, ndmi, nirv, nobs]
    names = ["blue", "green", "red", "nir", "swir16", "swir22", "ndvi", "ndmi", "nirv", "nobs"]

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
        "tile": tile, "crs": str(crs), "items": [it.id for it in items],
        "n_items": len(items), "bands": names, "source": items[0].assets["red"].href,
        "median_nobs": float(np.nanmedian(nobs)),
    }
    meta_path = out_path.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    if manifest:
        write_manifest(build_manifest(
            "s2_composite",
            {"lon": lon, "lat": lat, "start": start, "end": end, "size": size,
             "max_items": max_items, "max_cloud": max_cloud, "items": meta["items"]},
            [out_path, meta_path], license=LICENSE, account=ACCOUNT,
            source=items[0].assets["red"].href,
        ))
    return {"path": str(out_path), "meta": str(meta_path), **meta}


def fetch_annual(
    lon: float,
    lat: float,
    year: int,
    out: str | Path,
    size: int = 1600,
    max_items: int = 30,
    max_cloud: float = 40.0,
    manifest: bool = True,
) -> dict[str, Any]:
    """Composito anual com metricas fenologicas (S2) para o ano year.

    Bandas: medianas e indices, percentis de NDVI, amplitude sazonal, NBR/NDII,
    fracao valida e numero de observacoes. Usado no modelo anual (ADR-0021).
    """
    start, end = f"{year}-01-01", f"{year}-12-31"
    items = search_items(lon, lat, start, end, size=size, max_cloud=max_cloud)
    if not items:
        raise RuntimeError(f"nenhuma cena S2 em {year}")
    tile = items[0].id.split("_")[1]
    items = [it for it in items if it.id.split("_")[1] == tile][:max_items]
    _, bounds, crs, transform = _window_for_items(items, lon, lat, size)

    def stack(name, resampling=Resampling.bilinear):
        layers = []
        for item in items:
            with rasterio.open(item.assets[name].href) as ds:
                layers.append(_read_band(ds, bounds, size, resampling))
        return np.stack(layers)

    scl = stack("scl", Resampling.nearest)
    valid = ~np.isin(scl.astype("uint8"), list(SCL_BAD))
    n_scenes = len(items)

    def masked_median(arr):
        arr = arr.astype("float32").copy()
        arr[~valid] = np.nan
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return np.nanmedian(arr, axis=0)

    nir, red = stack("nir"), stack("red")
    swir16, swir22 = stack("swir16"), stack("swir22")
    blue, green = stack("blue"), stack("green")
    med = {k: masked_median(v) for k, v in
           (("blue", blue), ("green", green), ("red", red), ("nir", nir),
            ("swir16", swir16), ("swir22", swir22))}

    def scene_index(a, b):
        with np.errstate(divide="ignore", invalid="ignore"):
            idx = np.where(a + b > 0, (a - b) / (a + b), np.nan)
        idx[~valid] = np.nan
        return idx

    ndvi_scenes = scene_index(nir, red)
    ndmi_scenes = scene_index(nir, swir16)
    nbr_scenes = scene_index(nir, swir22)
    ndii_scenes = scene_index(nir, swir16)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        ndvi = np.nanmedian(ndvi_scenes, axis=0)
        ndmi = np.nanmedian(ndmi_scenes, axis=0)
        nbr = np.nanmedian(nbr_scenes, axis=0)
        ndii = np.nanmedian(ndii_scenes, axis=0)
        ndvi_p10 = np.nanpercentile(ndvi_scenes, 10, axis=0)
        ndvi_p90 = np.nanpercentile(ndvi_scenes, 90, axis=0)
    ndvi_amp = ndvi_p90 - ndvi_p10
    nirv = ndvi * med["nir"]
    nobs = valid.sum(axis=0).astype("float32")
    valid_fraction = (nobs / n_scenes).astype("float32")

    layers = [med["blue"], med["green"], med["red"], med["nir"], med["swir16"],
              med["swir22"], ndvi, ndmi, nirv, nbr, ndii, ndvi_p10, ndvi_p90,
              ndvi_amp, nobs, valid_fraction]
    names = ["blue", "green", "red", "nir", "swir16", "swir22", "ndvi",
             "ndmi", "nirv", "nbr", "ndii", "ndvi_p10", "ndvi_p90",
             "ndvi_amp", "nobs", "valid_fraction"]

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

    meta = {"lon": lon, "lat": lat, "year": year, "size_px": size, "tile": tile,
            "crs": str(crs), "items": [it.id for it in items], "n_items": len(items),
            "bands": names, "source": items[0].assets["red"].href,
            "median_nobs": float(np.nanmedian(nobs))}
    meta_path = out_path.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    if manifest:
        write_manifest(build_manifest(
            "s2_annual",
            {"lon": lon, "lat": lat, "year": year, "size": size,
             "max_items": max_items, "max_cloud": max_cloud, "items": meta["items"]},
            [out_path, meta_path], license=LICENSE, account=ACCOUNT,
            source=items[0].assets["red"].href,
        ))
    return {"path": str(out_path), "meta": str(meta_path), **meta}
