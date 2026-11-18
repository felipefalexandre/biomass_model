"""Janelas de features em sitios de campo (ex.: PLOS 2018 no Cerrado)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ..manifest import build_manifest, write_manifest
from .dem import fetch_dem
from .s2 import fetch_window


def fetch_site_windows(
    sites_csv: str | Path,
    out_dir: str | Path,
    start: str,
    end: str,
    *,
    bioma: str = "Cerrado",
    size: int = 400,
    dem_half: float = 0.02,
    max_cloud: float = 25.0,
    manifest: bool = True,
) -> dict[str, Any]:
    sites = pd.read_csv(sites_csv)
    sites = sites[sites["bioma"] == bioma].dropna(subset=["lon", "lat", "agb_mg_ha"])
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)

    results, failures = [], []
    for _, site in sites.iterrows():
        sid = int(site["site"])
        folder = root / f"site_{sid:03d}"
        folder.mkdir(parents=True, exist_ok=True)
        try:
            s2 = fetch_window(site["lon"], site["lat"], start, end,
                              folder / "s2.tif", size=size, max_cloud=max_cloud,
                              manifest=False)
            dem = fetch_dem(site["lon"], site["lat"], folder / "dem.tif",
                            half=dem_half, manifest=False)
            results.append({"site": sid, "s2": s2["path"], "dem": dem["path"],
                            "item_id": s2["item_id"], "cloud": s2["cloud_cover"]})
        except Exception as exc:
            failures.append({"site": sid, "error": str(exc)})

    summary = {"sites": len(results), "failures": failures, "out_dir": str(root)}
    if manifest:
        write_manifest(build_manifest(
            "sites_s2_dem",
            {"sites_csv": str(sites_csv), "bioma": bioma, "start": start, "end": end,
             "size": size, "max_cloud": max_cloud, **summary},
            [r["s2"] for r in results] + [r["dem"] for r in results],
            license="Copernicus (S2 e DEM)", account="nenhuma",
            notes="um manifesto agregado para todas as janelas",
            hash_outputs=False,
        ))
    return summary
