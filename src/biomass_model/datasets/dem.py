"""Copernicus DEM GLO-30 (COGs publicos na AWS), sem autenticacao."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import rasterio
from rasterio.merge import merge

from ..manifest import build_manifest, write_manifest

BASE = "https://copernicus-dem-30m.s3.amazonaws.com"
LICENSE = "Copernicus DEM (aberto, atribuicao)"
ACCOUNT = "nenhuma"


def tile_name(lat: int, lon: int) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    stem = f"Copernicus_DSM_COG_10_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"
    return f"{BASE}/{stem}/{stem}.tif"


def tiles_for_bbox(west: float, south: float, east: float, north: float) -> list[str]:
    tiles: list[str] = []
    for lat in range(math.floor(south), math.floor(north) + 1):
        for lon in range(math.floor(west), math.floor(east) + 1):
            tiles.append(tile_name(lat, lon))
    return tiles


def fetch_dem(
    lon: float,
    lat: float,
    out: str | Path,
    half: float = 0.08,
    manifest: bool = True,
) -> dict[str, Any]:
    south, north = lat - half, lat + half
    west, east = lon - half, lon + half
    urls = [f"/vsicurl/{t}" for t in tiles_for_bbox(west, south, east, north)]
    datasets = [rasterio.open(u) for u in urls]
    try:
        mosaic, transform = merge(datasets, bounds=(west, south, east, north))
    finally:
        for ds in datasets:
            ds.close()

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
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
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(mosaic)

    if manifest:
        write_manifest(
            build_manifest(
                "dem",
                {"lon": lon, "lat": lat, "half_deg": half},
                [out_path],
                license=LICENSE,
                account=ACCOUNT,
                source=";".join(urls),
            )
        )
    return {"path": str(out_path), "tiles": urls, "shape": list(mosaic.shape)}
