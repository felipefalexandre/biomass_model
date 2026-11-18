"""Extrai Copernicus DEM GLO-30 (COG publico na AWS) para um ponto.

Sem autenticacao: le os tiles 1x1 grau via /vsicurl/ e recorta a janela.

Uso:
    python tools/fetch_dem_pilot.py --lon -60.45 --lat -6.9 --half 0.08 \
        --out E:/Mapbiomas/biomass/pilots/amazonia_dem30.tif
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import rasterio
from rasterio.merge import merge

BASE = "https://copernicus-dem-30m.s3.amazonaws.com"


def tile_name(lat: int, lon: int) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    stem = f"Copernicus_DSM_COG_10_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"
    return f"{BASE}/{stem}/{stem}.tif"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--half", type=float, default=0.08, help="meia-largura em graus")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    south, north = args.lat - args.half, args.lat + args.half
    west, east = args.lon - args.half, args.lon + args.half

    tiles = []
    for lat in range(math.floor(south), math.floor(north) + 1):
        for lon in range(math.floor(west), math.floor(east) + 1):
            tiles.append(tile_name(lat, lon))

    urls = [f"/vsicurl/{t}" for t in tiles]
    datasets = [rasterio.open(u) for u in urls]
    try:
        mosaic, transform = merge(datasets, bounds=(west, south, east, north))
        profile = {
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "count": 1,
            "dtype": mosaic.dtype,
            "crs": "EPSG:4326",
            "transform": transform,
            "compress": "deflate",
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
            "nodata": 0,
        }
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(out, "w", **profile) as dst:
            dst.write(mosaic)
        print(f"tiles={len(tiles)} -> {out} shape={mosaic.shape} ({out.stat().st_size/1e6:.1f} MB)")
    finally:
        for ds in datasets:
            ds.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
