"""Features para observações canônicas (campo, LiDAR, GEDI) em uma grade de referência.

O objetivo é desacoplar o treinamento da fonte de referência: a tabela canônica traz lon/lat,
data e AGB; este módulo extrai features ópticas, topográficas, climáticas e de histórico do
MapBiomas para cada observação. A resolução e o suporte são declarados pelo usuário.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rasterio

from .features import (
    era5_features,
    load_era5,
    mapbiomas_class,
    terrain_features,
    window_mean,
    window_slope_mean,
)
from .inventory.schema import normalize_observations

FEATURE_PREFIXES = ("s2_", "s1_", "ls_", "era5_", "mb_")
DEFAULT_OPTICAL_NAMES = ("blue", "green", "red", "nir08", "swir16", "swir22", "nobs")


def _site_key(row: pd.Series) -> str:
    obs_id = str(row.get("observation_id", ""))
    return obs_id.split(":")[-1] if ":" in obs_id else obs_id


def _site_int(site: str) -> int | None:
    try:
        return int(str(site).strip())
    except ValueError:
        return None


def _format_path(pattern: str | None, root: str | Path | None, row: pd.Series,
                 year: int | None) -> Path | None:
    if not pattern:
        return None
    site = _site_key(row)
    site_int = _site_int(site)
    values = {
        "site": site,
        "site_int": site_int if site_int is not None else 0,
        "year": year if year is not None else 0,
        "observation_id": str(row.get("observation_id", "")),
        "source": str(row.get("source", "")),
    }
    try:
        rendered = pattern.format(**values)
    except (KeyError, ValueError):
        return None
    path = Path(rendered)
    if root is not None and not path.is_absolute():
        path = Path(root) / path
    return path if path.exists() else None


def _year_from_row(row: pd.Series, fallback_year: int | None) -> int | None:
    for col in ("reference_date", "inventory_date", "year"):
        if col not in row or pd.isna(row[col]) or str(row[col]).strip() == "":
            continue
        ts = pd.to_datetime(row[col], errors="coerce")
        if not pd.isna(ts):
            return int(ts.year)
        try:
            return int(str(row[col])[:4])
        except ValueError:
            continue
    return fallback_year


def _optical_features(path: str | Path, lon: float, lat: float, *, prefix: str,
                      half_m: float) -> dict[str, float]:
    with rasterio.open(path) as ds:
        names = list(ds.descriptions or ())
        if not any(names):
            names = [f"band{i}" for i in range(1, ds.count + 1)]
    means, counts = window_mean(path, lon, lat, half_m=half_m)
    means = np.asarray(means, dtype="float64")
    counts = np.asarray(counts, dtype="float64")
    out: dict[str, float] = {}
    values: dict[str, float] = {}
    for name, value in zip(names, means):
        if name.lower() in {"scl", "valid_fraction"}:
            continue
        values[name.lower()] = float(value)
        out[f"{prefix}_{name.lower()}"] = float(value)
    if counts.size:
        out[f"{prefix}_valid_fraction"] = float(counts.min() / max(counts.max(), 1.0))

    def take(*candidates: str) -> float | None:
        for candidate in candidates:
            if candidate in values and np.isfinite(values[candidate]):
                return values[candidate]
        return None

    nir = take("nir", "nir08", "band5")
    red = take("red", "band3")
    blue = take("blue", "band2")
    swir16 = take("swir16", "band6")
    swir22 = take("swir22", "band7")
    with np.errstate(divide="ignore", invalid="ignore"):
        if nir is not None and red is not None and (nir + red) != 0:
            out[f"{prefix}_ndvi"] = (nir - red) / (nir + red)
        if nir is not None and swir16 is not None and (nir + swir16) != 0:
            out[f"{prefix}_ndmi"] = (nir - swir16) / (nir + swir16)
            out[f"{prefix}_ndii"] = (nir - swir16) / (nir + swir16)
        if nir is not None and swir22 is not None and (nir + swir22) != 0:
            out[f"{prefix}_nbr"] = (nir - swir22) / (nir + swir22)
        if None not in (nir, red, blue):
            denom = nir + 6 * red - 7.5 * blue + 1
            if denom != 0:
                out[f"{prefix}_evi"] = 2.5 * (nir - red) / denom
    return out


def _terrain_features(dem_path: str | Path, lon: float, lat: float, *, half_m: float) -> dict[str, float]:
    elev, _ = window_mean(dem_path, lon, lat, half_m=half_m, indexes=[1])
    slope = window_slope_mean(dem_path, lon, lat, half_m=half_m)
    aspect = float(terrain_features(dem_path, np.array([lon]), np.array([lat]))["aspect"].iloc[0])
    return {"elev": float(elev[0]), "slope": float(slope), "aspect": aspect}


def _era5_features(era5: dict, lon: float, lat: float, year: int | None) -> dict[str, float]:
    date = pd.Series([f"{year}-07-01"] if year else ["2022-07-01"])
    try:
        frame = era5_features(era5, np.array([lon]), np.array([lat]), date)
    except Exception:
        frame = era5_features(era5, np.array([lon]), np.array([lat]),
                              pd.Series(["2022-07-01"]))
    return {col: float(frame[col].iloc[0]) for col in frame.columns}


def _mapbiomas_features(
    mapbiomas_dir: str | Path,
    lon: np.ndarray,
    lat: np.ndarray,
    years: np.ndarray,
    *,
    history: bool,
    history_start: int,
    history_end: int,
) -> dict[str, np.ndarray]:
    n = len(years)
    current = np.full(n, np.nan, dtype="float64")
    domain_years = np.zeros(n, dtype="float64")
    forest_years = np.zeros(n, dtype="float64")
    savanna_years = np.zeros(n, dtype="float64")
    changes = np.zeros(n, dtype="float64")
    since_change = np.zeros(n, dtype="float64")
    history_n = np.zeros(n, dtype="float64")

    for year in sorted({int(y) for y in years if np.isfinite(y)}):
        idx = np.flatnonzero(years == year)
        try:
            current[idx] = mapbiomas_class(mapbiomas_dir, year, lon[idx], lat[idx])
        except Exception:
            continue
        if not history:
            continue
        end = min(history_end, year - 1)
        if end < history_start:
            continue
        series_years = list(range(history_start, end + 1))
        try:
            series = np.stack([
                mapbiomas_class(mapbiomas_dir, y, lon[idx], lat[idx])
                for y in series_years
            ])
        except Exception:
            continue
        in_domain = np.isin(series, [3, 4])
        domain_years[idx] = in_domain.sum(axis=0)
        forest_years[idx] = (series == 3).sum(axis=0)
        savanna_years[idx] = (series == 4).sum(axis=0)
        changes[idx] = (np.diff(series, axis=0) != 0).sum(axis=0)
        last = np.full(series.shape[1], -1)
        for i in range(1, len(series_years)):
            moved = series[i] != series[i - 1]
            last[moved] = i
        since_change[idx] = np.where(last >= 0, len(series_years) - 1 - last, len(series_years))
        history_n[idx] = len(series_years)

    return {
        "mapbiomas_class": current,
        "mb_domain_years": domain_years,
        "mb_forest_years": forest_years,
        "mb_savanna_years": savanna_years,
        "mb_changes": changes,
        "mb_years_since_change": since_change,
        "mb_history_years": history_n,
    }


def _feature_columns(df: pd.DataFrame) -> list[str]:
    cols = [c for c in df.columns if c.startswith(FEATURE_PREFIXES) and not c.endswith("_valid")]
    cols += [c for c in ("elev", "slope", "aspect") if c in df.columns]
    return cols


def build_observation_features(
    observations: str | Path | pd.DataFrame,
    out_csv: str | Path,
    *,
    optical_dir: str | Path | None = None,
    optical_pattern: str | None = None,
    optical_path: str | Path | None = None,
    dem_dir: str | Path | None = None,
    dem_pattern: str | None = None,
    dem_path: str | Path | None = None,
    era5_path: str | Path | None = None,
    mapbiomas_dir: str | Path | None = None,
    half_m: float = 500.0,
    history: bool = True,
    history_start: int = 2004,
    history_end: int = 2018,
    fallback_year: int | None = None,
    max_rows: int | None = None,
) -> dict[str, Any]:
    """Monta uma tabela de features para observações canônicas.

    `optical_pattern`/`dem_pattern` aceitam `{site}`, `{site_int}`, `{year}`,
    `{observation_id}` e `{source}`. Exemplo PLOS:
    `optical_pattern="site_{site_int:03d}/landsat_{year}.tif"`.
    """
    if isinstance(observations, pd.DataFrame):
        table = normalize_observations(observations)
    else:
        from .inventory.schema import read_observations

        table = read_observations(observations)
    if max_rows is not None:
        table = table.head(max_rows).copy()
    table = table[np.isfinite(table["lon"]) & np.isfinite(table["lat"])].reset_index(drop=True)
    table = table[np.isfinite(table["agb_mg_ha"])].reset_index(drop=True)
    if table.empty:
        raise ValueError("nenhuma observação com lon/lat/AGB válidos")

    years = np.array([_year_from_row(row, fallback_year) for _, row in table.iterrows()],
                     dtype="float64")
    era5 = load_era5(era5_path) if era5_path is not None else None
    mb = _mapbiomas_features(
        mapbiomas_dir, table["lon"].to_numpy(), table["lat"].to_numpy(), years,
        history=history, history_start=history_start, history_end=history_end,
    ) if mapbiomas_dir is not None else {}

    rows: list[dict[str, Any]] = []
    for i, row in table.iterrows():
        year = int(years[i]) if np.isfinite(years[i]) else None
        record: dict[str, Any] = {
            "observation_id": row["observation_id"],
            "source": row["source"],
            "source_version": row["source_version"],
            "observation_type": row["observation_type"],
            "reference_date": row["reference_date"],
            "year": year,
            "lon": float(row["lon"]),
            "lat": float(row["lat"]),
            "agb_mg_ha": float(row["agb_mg_ha"]),
            "agb_uncertainty_mg_ha": float(row["agb_uncertainty_mg_ha"])
            if np.isfinite(row["agb_uncertainty_mg_ha"]) else np.nan,
            "biome": row["biome"],
            "fitofisionomia": row["fitofisionomia"],
            "fitofisionomia_group": row["fitofisionomia_group"],
            "model_status": row["model_status"],
        }
        opt_path = _format_path(optical_pattern, optical_dir, row, year)
        if opt_path is None and optical_path is not None:
            opt_path = Path(optical_path)
        if opt_path is not None and Path(opt_path).exists():
            prefix = "ls" if "landsat" in Path(opt_path).name.lower() else "s2"
            try:
                record.update(_optical_features(opt_path, row["lon"], row["lat"],
                                                prefix=prefix, half_m=half_m))
            except Exception:
                pass

        d_path = _format_path(dem_pattern, dem_dir, row, year)
        if d_path is None and dem_path is not None:
            d_path = Path(dem_path)
        if d_path is not None and Path(d_path).exists():
            try:
                record.update(_terrain_features(d_path, row["lon"], row["lat"], half_m=half_m))
            except Exception:
                pass

        if era5 is not None:
            try:
                record.update(_era5_features(era5, row["lon"], row["lat"], year))
            except Exception:
                pass

        if mb:
            record["mapbiomas_class"] = float(mb["mapbiomas_class"][i])
            for key in ("mb_domain_years", "mb_forest_years", "mb_savanna_years",
                        "mb_changes", "mb_years_since_change", "mb_history_years"):
                record[key] = float(mb[key][i])
        rows.append(record)

    out = pd.DataFrame(rows)
    feat_cols = _feature_columns(out)
    out["feature_na"] = out[feat_cols].isna().any(axis=1)
    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False, encoding="utf-8")
    summary = {
        "rows_in": int(len(table)),
        "rows_out": int(len(out)),
        "features": feat_cols,
        "n_features": len(feat_cols),
        "rows_feature_na": int(out["feature_na"].sum()),
        "years": {int(y): int((years == y).sum()) for y in np.unique(years[np.isfinite(years)])},
        "path": str(out_path),
    }
    out_path.with_suffix(".summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary
