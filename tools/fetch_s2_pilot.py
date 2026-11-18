"""Extrai uma janela Sentinel-2 L2A (COG publico na AWS) em torno de um ponto.

Nao requer conta: usa o STAC earth-search e le apenas a janela necessaria via
/vsicurl/. Salva um GeoTIFF com reflectancia e indices + metadados JSON.

Uso:
    python tools/fetch_s2_pilot.py --lon -60.45 --lat -6.9 \
        --start 2024-07-01 --end 2024-09-30 \
        --out E:/Mapbiomas/biomass/pilots/amazonia_s2_2024.tif
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from pystac_client import Client
from rasterio.enums import Resampling
from pyproj import Transformer
from rasterio.windows import Window, from_bounds

STAC = "https://earth-search.aws.element84.com/v1"
BANDS = ["blue", "green", "red", "nir", "swir16", "swir22"]
SCL_BAD = {0, 1, 3, 8, 9, 10, 11}


def read_band(ds, bounds, size: int, resampling: Resampling) -> np.ndarray:
    win = from_bounds(*bounds, transform=ds.transform).round()
    data = ds.read(1, window=win, out_shape=(size, size), resampling=resampling)
    return data.astype("float32")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--size", type=int, default=1600, help="pixels de 10 m")
    parser.add_argument("--max-cloud", type=float, default=20.0)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    half_deg = args.size * 10 / 111_000 / 2
    bbox = [args.lon - half_deg, args.lat - half_deg, args.lon + half_deg, args.lat + half_deg]

    catalog = Client.open(STAC)
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=f"{args.start}/{args.end}",
        query={"eo:cloud_cover": {"lt": args.max_cloud}},
        max_items=50,
    )
    items = list(search.items())
    if not items:
        raise SystemExit("nenhuma cena encontrada no periodo/limite de nuvem")
    items.sort(key=lambda it: it.properties.get("eo:cloud_cover", 100))
    item = items[0]
    print(f"cena: {item.id} {item.datetime} nuvem={item.properties.get('eo:cloud_cover'):.2f}%")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(item.assets["red"].href) as ref:
        to_crs = Transformer.from_crs("EPSG:4326", ref.crs, always_xy=True)
        x, y = to_crs.transform(args.lon, args.lat)
        half = args.size // 2
        col = min(max(int((x - ref.transform.c) / ref.transform.a), half), ref.width - half - 1)
        row = min(max(int((y - ref.transform.f) / ref.transform.e), half), ref.height - half - 1)
        win = Window(col - half, row - half, args.size, args.size)
        bounds = ref.window_bounds(win)
        crs = ref.crs
        transform = ref.window_transform(win)

    layers: list[np.ndarray] = []
    descriptions: list[str] = []
    for name in BANDS:
        with rasterio.open(item.assets[name].href) as ds:
            resampling = Resampling.nearest if name == "scl" else Resampling.bilinear
            layers.append(read_band(ds, bounds, args.size, resampling))
        descriptions.append(name)

    blue, green, red, nir, swir16, swir22 = layers
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = np.where(nir + red > 0, (nir - red) / (nir + red), np.nan)
        ndmi = np.where(nir + swir16 > 0, (nir - swir16) / (nir + swir16), np.nan)
    nirv = ndvi * nir
    layers += [ndvi.astype("float32"), ndmi.astype("float32"), nirv.astype("float32")]
    descriptions += ["ndvi", "ndmi", "nirv"]

    with rasterio.open(item.assets["scl"].href) as ds:
        scl = read_band(ds, bounds, args.size, Resampling.nearest).astype("uint8")
    layers.append(scl.astype("float32"))
    descriptions.append("scl")

    profile = {
        "driver": "GTiff",
        "width": args.size,
        "height": args.size,
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
        "center_lon": args.lon,
        "center_lat": args.lat,
        "size_px": args.size,
        "crs": str(crs),
        "valid_fraction": float(valid.mean()),
        "bands": descriptions,
        "source": item.assets["red"].href,
        "candidates": [{"id": it.id, "cloud": it.properties.get("eo:cloud_cover")} for it in items[:10]],
    }
    meta_path = out_path.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"valido={valid.mean():.3f} -> {out_path} ({out_path.stat().st_size/1e6:.1f} MB)")
    print(f"meta -> {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
