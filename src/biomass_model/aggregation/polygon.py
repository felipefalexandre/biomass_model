"""Estatísticas de AGB por polígono com área real de interseção.

O raster deve estar em CRS projetado (metros). A área de cada célula é a área geométrica no CRS;
células de borda usam a interseção entre a célula e o polígono. A incerteza agregada é estimada
por block bootstrap espacial, não por erro padrão ingênuo de pixels.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import Window
from shapely.geometry import box
from shapely.ops import unary_union
from shapely.validation import make_valid


def _read_polygon(polygon: str | Path | Any) -> tuple[Any, Any]:
    import geopandas as gpd

    if isinstance(polygon, gpd.GeoDataFrame):
        gdf = polygon.copy()
    else:
        gdf = gpd.read_file(polygon)
    if gdf.empty:
        raise ValueError("polígono vazio")
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    geoms = []
    for geom in gdf.geometry:
        if geom is None or geom.is_empty:
            continue
        geoms.append(geom if geom.is_valid else make_valid(geom))
    if not geoms:
        raise ValueError("polígono sem geometria válida")
    return unary_union(geoms), gdf.crs


def _cell_polygon(transform: Any, row: int, col: int) -> Any:
    x0 = transform.c + col * transform.a
    x1 = x0 + transform.a
    y0 = transform.f + row * transform.e
    y1 = y0 + transform.e
    return box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not mask.any():
        return float("nan")
    v = values[mask]
    w = weights[mask]
    order = np.argsort(v)
    v, w = v[order], w[order]
    cumulative = np.cumsum(w)
    half = cumulative[-1] / 2.0
    idx = int(np.searchsorted(cumulative, half, side="left"))
    idx = min(idx, len(v) - 1)
    if idx == 0:
        return float(v[0])
    prev_cum = cumulative[idx - 1]
    span = cumulative[idx] - prev_cum
    if span <= 0:
        return float(v[idx])
    fraction = (half - prev_cum) / span
    return float(v[idx - 1] + fraction * (v[idx] - v[idx - 1]))


def _block_sums(
    values: np.ndarray,
    areas_ha: np.ndarray,
    block_ids: np.ndarray,
) -> pd.DataFrame:
    df = pd.DataFrame({"v": values * areas_ha, "a": areas_ha, "block": block_ids})
    out = df.groupby("block", sort=False)[["v", "a"]].sum()
    return out


def _bootstrap(
    block_sums: pd.DataFrame,
    total_area_ha: float,
    *,
    n_boot: int,
    seed: int,
) -> dict[str, Any]:
    if len(block_sums) < 2:
        return {"ci90_mean": [None, None], "ci90_total_mg": [None, None],
                "n_boot": 0, "n_blocks": int(len(block_sums))}
    rng = np.random.default_rng(seed)
    v = block_sums["v"].to_numpy(dtype="float64")
    a = block_sums["a"].to_numpy(dtype="float64")
    means = np.empty(n_boot, dtype="float64")
    totals = np.empty(n_boot, dtype="float64")
    for i in range(n_boot):
        pick = rng.integers(0, len(v), size=len(v))
        sampled_a = a[pick].sum()
        mean = v[pick].sum() / sampled_a if sampled_a > 0 else np.nan
        means[i] = mean
        totals[i] = mean * total_area_ha if np.isfinite(mean) else np.nan
    lo_m, hi_m = np.nanquantile(means, [0.05, 0.95])
    lo_t, hi_t = np.nanquantile(totals, [0.05, 0.95])
    return {
        "ci90_mean": [float(lo_m), float(hi_m)],
        "ci90_total_mg": [float(lo_t), float(hi_t)],
        "n_boot": int(n_boot),
        "n_blocks": int(len(block_sums)),
    }


def _summarize(
    values: np.ndarray,
    areas_ha: np.ndarray,
    block_ids: np.ndarray,
    *,
    n_boot: int,
    seed: int,
) -> dict[str, Any]:
    mask = np.isfinite(values) & np.isfinite(areas_ha) & (areas_ha > 0)
    values = values[mask]
    areas = areas_ha[mask]
    blocks = block_ids[mask]
    if len(values) == 0:
        return {"n_cells": 0}
    total_area = float(areas.sum())
    total_mg = float((values * areas).sum())
    mean = total_mg / total_area if total_area > 0 else float("nan")
    median = _weighted_median(values, areas)
    sums = _block_sums(values, areas, blocks)
    boot = _bootstrap(sums, total_area, n_boot=n_boot, seed=seed)
    return {
        "n_cells": int(len(values)),
        "n_blocks": int(len(sums)),
        "area_ha": total_area,
        "mean_agbd_mg_ha": float(mean),
        "median_agbd_mg_ha": float(median),
        "total_mg": total_mg,
        "total_tg": float(total_mg / 1e6),
        **boot,
    }


def _group_stats(
    values: np.ndarray,
    areas_ha: np.ndarray,
    block_ids: np.ndarray,
    groups: np.ndarray,
    *,
    n_boot: int,
    seed: int,
    labels: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    out = []
    for code in sorted({int(g) for g in groups if np.isfinite(g)}):
        mask = groups == code
        stats = _summarize(values[mask], areas_ha[mask], block_ids[mask],
                           n_boot=n_boot, seed=seed)
        stats["code"] = code
        stats["label"] = (labels or {}).get(code, str(code))
        out.append(stats)
    return out


def _load_code_table(path: str | Path | None) -> dict[int, str]:
    if path is None:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {int(item["code"]): str(item["label"]) for item in data.get("codes", [])}


def _load_code_groups(path: str | Path | None) -> dict[int, str]:
    if path is None:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {int(item["code"]): str(item.get("group", "")) for item in data.get("codes", [])}


def polygon_raster_stats(
    raster_path: str | Path,
    polygon: str | Path | Any,
    *,
    value_band: int = 1,
    class_band: int | None = None,
    fitofisionomia_band: int | None = None,
    aoa_band: int | None = None,
    class_raster: str | Path | None = None,
    fitofisionomia_raster: str | Path | None = None,
    aoa_raster: str | Path | None = None,
    domain_classes: Iterable[int] = (3, 4),
    require_domain: bool = True,
    require_aoa: bool = False,
    block_size_m: float = 5000.0,
    chunk_rows: int = 2048,
    n_boot: int = 400,
    seed: int = 42,
    fitofisionomia_codes: str | Path | None = None,
    fitofisionomia_groups: Iterable[str] | None = None,
    year: int | None = None,
    out: str | Path | None = None,
) -> dict[str, Any]:
    """Calcula média, mediana, estoque e IC para um polígono sobre um raster de AGB."""
    geom, geom_crs = _read_polygon(polygon)
    with rasterio.open(raster_path) as src:
        if src.crs is None:
            raise ValueError("raster sem CRS")
        if src.crs.is_geographic:
            raise ValueError(
                "polygon_raster_stats exige raster em CRS projetado (metros); "
                "reprojete o mapa antes da agregação"
            )
        if not (src.transform.b == 0 and src.transform.d == 0):
            raise ValueError("raster rotacionado não suportado")
        raster_crs = src.crs
        aux = {}
        for name, path in (("class", class_raster), ("fitofisionomia", fitofisionomia_raster),
                           ("aoa", aoa_raster)):
            if path is None:
                continue
            ds = rasterio.open(path)
            if (ds.crs != src.crs or ds.transform != src.transform
                    or ds.width != src.width or ds.height != src.height):
                ds.close()
                raise ValueError(f"raster auxiliar {name} não está alinhado ao raster de AGB")
            aux[name] = ds
        geom_r = geom
        if geom_crs != raster_crs:
            import geopandas as gpd

            geom_r = gpd.GeoSeries([geom], crs=geom_crs).to_crs(raster_crs).iloc[0]

        window = rasterio.windows.from_bounds(*geom_r.bounds, transform=src.transform)
        col_off = max(0, int(np.floor(window.col_off)))
        row_off = max(0, int(np.floor(window.row_off)))
        col_end = min(src.width, int(np.ceil(window.col_off + window.width)))
        row_end = min(src.height, int(np.ceil(window.row_off + window.height)))
        if col_end <= col_off or row_end <= row_off:
            raise ValueError("polígono fora da extensão do raster")

        cell_area_m2 = abs(src.transform.a * src.transform.e)
        cell_area_ha = cell_area_m2 / 10000.0
        block_cells = max(1, int(round(block_size_m / max(abs(src.transform.a), abs(src.transform.e)))))

        values_parts: list[np.ndarray] = []
        areas_parts: list[np.ndarray] = []
        blocks_parts: list[np.ndarray] = []
        class_parts: list[np.ndarray] = []
        fit_parts: list[np.ndarray] = []
        aoa_parts: list[np.ndarray] = []
        polygon_area_ha = float(geom_r.area / 10000.0)

        for start_row in range(row_off, row_end, chunk_rows):
            height = min(chunk_rows, row_end - start_row)
            width = col_end - col_off
            win = Window(col_off, start_row, width, height)
            bands = [value_band]
            for band, raster in ((class_band, class_raster),
                                 (fitofisionomia_band, fitofisionomia_raster),
                                 (aoa_band, aoa_raster)):
                if band is not None and raster is None and band not in bands:
                    bands.append(band)
            array = src.read(bands, window=win, masked=True).astype("float64")
            data = {band: array[i].filled(np.nan) for i, band in enumerate(bands)}
            value = data[value_band]
            transform = src.window_transform(win)
            shape = (height, width)
            inside = geometry_mask([geom_r], out_shape=shape, transform=transform,
                                   invert=True, all_touched=False)
            boundary = geometry_mask([geom_r.boundary], out_shape=shape, transform=transform,
                                     invert=True, all_touched=True)
            valid = inside & np.isfinite(value)

            def aux_array(name, band):
                if name in aux:
                    return aux[name].read(1, window=win, masked=True).astype("float64").filled(np.nan)
                if band is not None:
                    return data[band]
                return np.full(shape, np.nan)

            klass = aux_array("class", class_band)
            if (class_band is not None or class_raster is not None) and require_domain:
                valid &= np.isin(klass, list(domain_classes))
            fitofisionomia = aux_array("fitofisionomia", fitofisionomia_band)
            aoa = aux_array("aoa", aoa_band)
            if (aoa_band is not None or aoa_raster is not None) and require_aoa:
                valid &= aoa > 0.5

            rows, cols = np.nonzero(valid & ~boundary)
            if len(rows):
                global_rows = start_row + rows
                global_cols = col_off + cols
                block_ids = (global_rows // block_cells).astype("int64") * 10_000_000 + (
                    global_cols // block_cells
                )
                values_parts.append(value[rows, cols])
                areas_parts.append(np.full(len(rows), cell_area_ha, dtype="float64"))
                blocks_parts.append(block_ids)
                class_parts.append(klass[rows, cols])
                if fitofisionomia_band is not None or fitofisionomia_raster is not None:
                    fit_parts.append(fitofisionomia[rows, cols])
                if aoa_band is not None or aoa_raster is not None:
                    aoa_parts.append(aoa[rows, cols])

            rows, cols = np.nonzero(valid & boundary)
            for r, c in zip(rows.tolist(), cols.tolist()):
                cell = _cell_polygon(transform, r, c)
                intersection = cell.intersection(geom_r)
                if intersection.is_empty:
                    continue
                area_ha = float(intersection.area / 10000.0)
                if area_ha <= 0:
                    continue
                global_row = start_row + r
                global_col = col_off + c
                block_id = (global_row // block_cells) * 10_000_000 + (global_col // block_cells)
                values_parts.append(np.array([value[r, c]], dtype="float64"))
                areas_parts.append(np.array([area_ha], dtype="float64"))
                blocks_parts.append(np.array([block_id], dtype="int64"))
                class_parts.append(np.array([klass[r, c]], dtype="float64"))
                if fitofisionomia_band is not None or fitofisionomia_raster is not None:
                    fit_parts.append(np.array([fitofisionomia[r, c]], dtype="float64"))
                if aoa_band is not None or aoa_raster is not None:
                    aoa_parts.append(np.array([aoa[r, c]], dtype="float64"))

    for ds in aux.values():
        ds.close()

    if not values_parts:
        raise ValueError("nenhuma célula válida no polígono após os filtros")

    values = np.concatenate(values_parts)
    areas_ha = np.concatenate(areas_parts)
    block_ids = np.concatenate(blocks_parts)
    classes = np.concatenate(class_parts) if class_parts else np.full(len(values), np.nan)
    fits = np.concatenate(fit_parts) if fit_parts else np.full(len(values), np.nan)
    aoa = np.concatenate(aoa_parts) if aoa_parts else np.full(len(values), np.nan)

    if fitofisionomia_groups and (fitofisionomia_band is not None or fitofisionomia_raster is not None):
        groups_map = _load_code_groups(fitofisionomia_codes)
        fit_groups = np.array([
            groups_map.get(int(code), "") if np.isfinite(code) else "" for code in fits
        ])
        keep = np.isin(fit_groups, list(fitofisionomia_groups))
        values, areas_ha, block_ids = values[keep], areas_ha[keep], block_ids[keep]
        classes, fits, aoa = classes[keep], fits[keep], aoa[keep]
        if len(values) == 0:
            raise ValueError("nenhuma célula válida após o filtro de grupos fitofisionômicos")

    overall = _summarize(values, areas_ha, block_ids, n_boot=n_boot, seed=seed)
    aoa_fraction = float(
        (areas_ha[aoa > 0.5].sum() / areas_ha.sum())
        if (aoa_band is not None or aoa_raster is not None) and areas_ha.sum() > 0
        else np.nan
    )
    by_class = _group_stats(values, areas_ha, block_ids, classes,
                            n_boot=n_boot, seed=seed) \
        if (class_band is not None or class_raster is not None) else []
    fit_labels = _load_code_table(fitofisionomia_codes)
    by_fit = _group_stats(values, areas_ha, block_ids, fits,
                          n_boot=n_boot, seed=seed, labels=fit_labels) \
        if (fitofisionomia_band is not None or fitofisionomia_raster is not None) else []

    result = {
        "raster": str(raster_path),
        "year": year,
        "polygon_crs": str(geom_crs),
        "raster_crs": str(raster_crs),
        "polygon_area_ha": polygon_area_ha,
        "area_analyzed_ha": float(overall.get("area_ha", np.nan)),
        "area_excluded_ha": float(max(0.0, polygon_area_ha - overall.get("area_ha", np.nan))),
        "mean_agbd_mg_ha": overall.get("mean_agbd_mg_ha"),
        "median_agbd_mg_ha": overall.get("median_agbd_mg_ha"),
        "total_mg": overall.get("total_mg"),
        "total_tg": overall.get("total_tg"),
        "ci90_mean": overall.get("ci90_mean"),
        "ci90_total_mg": overall.get("ci90_total_mg"),
        "n_cells": overall.get("n_cells"),
        "n_blocks": overall.get("n_blocks"),
        "aoa_fraction": aoa_fraction,
        "by_class": by_class,
        "by_fitofisionomia": by_fit,
        "value_band": value_band,
        "class_band": class_band,
        "fitofisionomia_band": fitofisionomia_band,
        "aoa_band": aoa_band,
        "fitofisionomia_groups": list(fitofisionomia_groups) if fitofisionomia_groups else None,
        "domain_classes": list(domain_classes),
        "block_size_m": block_size_m,
        "n_boot": n_boot,
        "limitations": [
            "IC do total cobre variabilidade espacial das predições (block bootstrap), "
            "não erro de referência, alometria ou calibração.",
            "Área elegível depende da máscara de domínio/AOA do raster.",
        ],
    }
    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result
