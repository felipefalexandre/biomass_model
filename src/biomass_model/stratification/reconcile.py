"""Comparação espacial entre fitofisionomia IBGE e classes MapBiomas (ADR-0029)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import Resampling, reproject


def _read_on_grid(path: str | Path, ref: rasterio.DatasetReader) -> np.ndarray:
    with rasterio.open(path) as src:
        if (src.crs == ref.crs and src.transform == ref.transform
                and src.width == ref.width and src.height == ref.height):
            return src.read(1)
        dest = np.zeros((ref.height, ref.width), dtype=src.dtypes[0])
        reproject(
            source=rasterio.band(src, 1), destination=dest,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=ref.transform, dst_crs=ref.crs,
            resampling=Resampling.nearest,
        )
        return dest


def _code_table(path: str | Path) -> dict[int, dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        int(item["code"]): {
            "label": str(item.get("label", item["code"])),
            "group": str(item.get("group", "unknown")),
        }
        for item in data.get("codes", [])
    }


def compare_fitofisionomia_mapbiomas(
    fit_raster: str | Path,
    mapbiomas_raster: str | Path,
    codes_path: str | Path,
    *,
    mapbiomas_classes: Iterable[int] = (3, 4),
    out_csv: str | Path | None = None,
) -> dict[str, Any]:
    """Cruza fitofisionomia IBGE com classe MapBiomas na mesma grade."""
    with rasterio.open(fit_raster) as ref:
        fit = ref.read(1)
        mb = _read_on_grid(mapbiomas_raster, ref)
        pixel_area_ha = abs(ref.transform.a * ref.transform.e) / 10_000.0
        projected = not ref.crs.is_geographic
    if not projected:
        raise ValueError("fitofisionomia-reconcile exige raster projetado em metros")
    codes = _code_table(codes_path)
    mask = np.isin(mb, list(mapbiomas_classes)) & (fit > 0)
    rows = []
    for code in sorted({int(x) for x in np.unique(fit[mask])}):
        label = codes.get(code, {}).get("label", str(code))
        group = codes.get(code, {}).get("group", "unknown")
        for klass in sorted({int(x) for x in np.unique(mb[mask & (fit == code)])}):
            n = int(np.sum(mask & (fit == code) & (mb == klass)))
            rows.append({
                "fitofisionomia_code": code,
                "fitofisionomia_label": label,
                "fitofisionomia_group": group,
                "mapbiomas_class": klass,
                "n_pixels": n,
                "area_ha": n * pixel_area_ha,
            })
    table = pd.DataFrame(rows)
    if table.empty:
        raise ValueError("nenhuma interseção válida entre fitofisionomia e MapBiomas")

    total_ha = float(table["area_ha"].sum())
    by_group = (table.groupby("fitofisionomia_group", as_index=False)["area_ha"].sum()
                .sort_values("area_ha", ascending=False))
    by_group["fraction"] = by_group["area_ha"] / total_ha
    by_class = (table.groupby("mapbiomas_class", as_index=False)["area_ha"].sum()
                .sort_values("area_ha", ascending=False))
    by_class["fraction"] = by_class["area_ha"] / total_ha
    non_vegetation = by_group[by_group["fitofisionomia_group"].isin(
        ["anthropogenic", "water", "unknown"]
    )]["area_ha"].sum()

    if out_csv:
        out = Path(out_csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(out, index=False, encoding="utf-8")
    summary = {
        "fit_raster": str(fit_raster),
        "mapbiomas_raster": str(mapbiomas_raster),
        "mapbiomas_classes": list(mapbiomas_classes),
        "total_area_ha": total_ha,
        "n_pixels": int(table["n_pixels"].sum()),
        "by_group": by_group.to_dict(orient="records"),
        "by_mapbiomas_class": by_class.to_dict(orient="records"),
        "non_vegetation_area_ha": float(non_vegetation),
        "non_vegetation_fraction": float(non_vegetation / total_ha) if total_ha else None,
        "rows": table.to_dict(orient="records"),
        "out_csv": str(out_csv) if out_csv else None,
    }
    return summary
