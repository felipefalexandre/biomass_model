"""Landsat Collection 2 L2 (Microsoft Planetary Computer, sem conta).

Usado para alinhar a referencia de campo (inventarios antigos) ao sensor da epoca:
as parcelas do PLOS 2018 sao de 1988-2014, fora do periodo do Sentinel-2.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import planetary_computer
import rasterio
from pyproj import CRS, Transformer
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds

from ..manifest import build_manifest, write_manifest

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "landsat-c2-l2"
LICENSE = "USGS Landsat Collection 2 (aberto)"
ACCOUNT = "nenhuma (MPC assina o acesso)"
BANDS = ("blue", "green", "red", "nir08", "swir16", "swir22")
QA_BAD_MASK = 0b111111  # fill, dilated cloud, cirrus, cloud, shadow, snow

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def parse_inventory_date(value: Any) -> str | None:
    """Normaliza datas sujas do PLOS ('2010', 'Mar/Apr- 2008') para ISO."""
    import re

    s = str(value)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0)
    year = re.search(r"(19|20)\d{2}", s)
    if not year:
        return None
    months = re.findall(r"([A-Za-z]{3})", s)
    month = _MONTHS.get(months[-1].lower(), 7) if months else 7
    return f"{year.group(0)}-{month:02d}-01"


def target_grid(lon: float, lat: float, half_m: float = 500.0, res_m: float = 30.0):
    zone = int((lon + 180.0) // 6.0) + 1
    epsg = (32600 if lat >= 0 else 32700) + zone
    crs = CRS.from_epsg(epsg)
    x, y = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform(lon, lat)
    n = 2 * int(round(half_m / res_m)) + 1
    transform = from_origin(x - n * res_m / 2, y + n * res_m / 2, res_m, res_m)
    return crs, transform, n


def search_items(lon: float, lat: float, start: str, end: str,
                 pad_deg: float = 0.02, max_items: int = 40) -> list[Any]:
    catalog = Client.open(STAC_URL)
    search = catalog.search(
        collections=[COLLECTION],
        bbox=[lon - pad_deg, lat - pad_deg, lon + pad_deg, lat + pad_deg],
        datetime=f"{start}/{end}", max_items=max_items,
    )
    items = [it for it in search.items() if set(BANDS) <= set(it.assets) and "qa_pixel" in it.assets]
    items.sort(key=lambda it: it.properties.get("eo:cloud_cover", 100.0))
    return items


def _read_warped(item, asset: str, crs, transform, n: int, resampling) -> np.ndarray:
    with rasterio.open(item.assets[asset].href) as ds:
        b = transform_bounds(crs, ds.crs, *rasterio.transform.array_bounds(n, n, transform),
                             densify_pts=21)
        win = rasterio.windows.from_bounds(*b, transform=ds.transform).round()
        win = win.intersection(rasterio.windows.Window(0, 0, ds.width, ds.height))
        src = ds.read(1, window=win, boundless=True)
        dst = np.full((n, n), np.nan, dtype="float32")
        reproject(source=src, destination=dst,
                  src_transform=ds.window_transform(win), src_crs=ds.crs,
                  dst_transform=transform, dst_crs=crs,
                  src_nodata=0, dst_nodata=np.nan, resampling=resampling)
    return dst


def fetch_landsat_window(
    lon: float,
    lat: float,
    date: str,
    out: str | Path,
    *,
    half_m: float = 500.0,
    days: int = 45,
    max_items: int = 6,
    manifest: bool = True,
) -> dict[str, Any]:
    from datetime import date as _date, timedelta

    d = _date.fromisoformat(str(date)[:10])
    start = (d - timedelta(days=days)).isoformat()
    end = (d + timedelta(days=days)).isoformat()
    items = search_items(lon, lat, start, end)[:max_items]
    if not items:
        raise RuntimeError(f"sem Landsat C2 L2 em {start}..{end}")
    crs, transform, n = target_grid(lon, lat, half_m=half_m)

    sr, qa, use = [], [], []
    for it in items:
        sit = planetary_computer.sign(it)
        try:
            quality = _read_warped(sit, "qa_pixel", crs, transform, n, Resampling.nearest)
            stack = [_read_warped(sit, b, crs, transform, n, Resampling.bilinear) for b in BANDS]
        except Exception:
            continue
        reflected = []
        for arr in stack:
            refl = arr * 0.0000275 - 0.2
            refl[(refl < -0.2) | (refl > 1.6)] = np.nan
            reflected.append(refl)
        bad = np.isnan(quality) | ((np.nan_to_num(quality).astype("int32") & QA_BAD_MASK) != 0)
        good = np.isfinite(reflected[3]) & ~bad
        if good.mean() < 0.2:
            continue
        for arr in reflected:
            arr[bad] = np.nan
        sr.append(np.stack(reflected))
        qa.append(good)
        use.append(it.id)

    if not sr:
        raise RuntimeError("todas as cenas ficaram invalidas apos a mascara de nuvem")

    cube = np.stack(sr)  # (itens, bandas, n, n)
    nobs = np.sum(np.stack(qa), axis=0).astype("float32")
    med = np.nanmedian(cube, axis=0)
    layers = list(med) + [nobs]
    names = list(BANDS) + ["nobs"]

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff", "width": n, "height": n, "count": len(layers),
        "dtype": "float32", "crs": crs, "transform": transform,
        "compress": "deflate", "predictor": 3, "nodata": np.nan,
    }
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(np.stack(layers).astype("float32"))
        for i, name in enumerate(names, start=1):
            dst.set_band_description(i, name)

    meta = {
        "lon": lon, "lat": lat, "date": str(date), "window": [start, end],
        "half_m": half_m, "size_px": n, "res_m": 30, "crs": str(crs),
        "items": use, "n_items": len(use), "bands": names,
        "valid_fraction_median": float(np.nanmedian(nobs > 0)),
        "median_nobs": float(np.nanmedian(nobs)),
    }
    meta_path = out_path.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    if manifest:
        write_manifest(build_manifest(
            "landsat", {"lon": lon, "lat": lat, "date": str(date), "days": days,
                        "half_m": half_m, "items": use},
            [out_path, meta_path], license=LICENSE, account=ACCOUNT,
            source="https://planetarycomputer.microsoft.com/dataset/landsat-c2-l2",
        ))
    return {"path": str(out_path), "meta": str(meta_path), **meta}


def fetch_landsat_sites(
    sites_csv: str | Path,
    out_dir: str | Path,
    *,
    bioma: str = "Cerrado",
    years: tuple[int, int] = (2004, 2014),
    half_m: float = 500.0,
    days: int = 45,
    max_items: int = 6,
    manifest: bool = True,
) -> dict[str, Any]:
    import pandas as pd

    sites = pd.read_csv(sites_csv)
    sites = sites[(sites["bioma"] == bioma)].dropna(
        subset=["lon", "lat", "agb_mg_ha", "data_inventario"])
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    results, failures, skipped = [], [], []
    for _, site in sites.iterrows():
        sid = int(site["site"])
        iso = parse_inventory_date(site["data_inventario"])
        if iso is None:
            skipped.append({"site": sid, "reason": "data ilegivel",
                            "value": str(site["data_inventario"])})
            continue
        year = int(iso[:4])
        if not (years[0] <= year <= years[1]):
            skipped.append({"site": sid, "year": year,
                            "reason": "fora da janela Landsat/MapBiomas"})
            continue
        folder = root / f"site_{sid:03d}"
        folder.mkdir(parents=True, exist_ok=True)
        try:
            r = fetch_landsat_window(
                site["lon"], site["lat"], iso,
                folder / f"landsat_{year}.tif", half_m=half_m,
                days=days, max_items=max_items, manifest=False)
            results.append({"site": sid, "year": year, "path": r["path"],
                            "n_items": r["n_items"], "items": r["items"]})
        except Exception as exc:
            failures.append({"site": sid, "year": year, "error": str(exc)})

    summary = {"sites": len(results), "failures": failures,
               "skipped": len(skipped), "out_dir": str(root)}
    (root / "landsat_sites_summary.json").write_text(
        json.dumps({**summary, "skipped_detail": skipped}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    if manifest:
        write_manifest(build_manifest(
            "landsat_sites",
            {"sites_csv": str(sites_csv), "bioma": bioma, "years": list(years),
             "half_m": half_m, "days": days, "max_items": max_items, **summary},
            [r["path"] for r in results], license=LICENSE, account=ACCOUNT,
            notes="um GeoTIFF por sitio (mediana de cenas em +-45 dias do inventario)",
            hash_outputs=False,
        ))
    return summary
