"""Extracao de features nos footprints, sobre a grade do MapBiomas.

Os pontos GEDI sao primeiro encaixados no centro do pixel de ~30 m do MapBiomas
(ADR-0013); todas as camadas sao amostradas nesse ponto. S2 e DEM usam
interpolacao bilinear; classe usa vizinho mais proximo.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.windows import Window

S2_BANDS = ["blue", "green", "red", "nir", "swir16", "swir22", "ndvi", "ndmi", "nirv", "scl"]
ERA5_VARS = {
    "t2m": "t2m",
    "tp": "tp",
    "pev": "pev",
    "ssrd": "ssrd",
    "swvl1": "swvl1",
    "swvl2": "swvl2",
    "swvl3": "swvl3",
    "swvl4": "swvl4",
}


def snap_to_grid(lon: np.ndarray, lat: np.ndarray, transform) -> tuple[np.ndarray, np.ndarray]:
    """Indices de linha/coluna e centro do pixel que contem cada ponto."""
    cols = np.floor((np.asarray(lon) - transform.c) / transform.a).astype("int64")
    rows = np.floor((np.asarray(lat) - transform.f) / transform.e).astype("int64")
    lon_c = transform.c + (cols + 0.5) * transform.a
    lat_c = transform.f + (rows + 0.5) * transform.e
    return rows, cols, lon_c, lat_c


def _coords_in_crs(lon: np.ndarray, lat: np.ndarray, crs) -> list[tuple[float, float]]:
    if str(crs) == "EPSG:4326":
        return list(zip(lon, lat))
    tr = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    x, y = tr.transform(lon, lat)
    return list(zip(x, y))


def sample_raster(
    path: str | Path,
    lon: np.ndarray,
    lat: np.ndarray,
    indexes: Sequence[int] | None = None,
    resampling: Resampling = Resampling.bilinear,
    max_pixels: int = 4_000_000,
) -> np.ndarray:
    """Amostra bandas em lon/lat (EPSG:4326). Retorna matriz (n_pontos, n_bandas).

    Bilinear e calculado em memoria para rasters pequenos (pilotos); para rasters
    grandes cai para vizinho mais proximo. Categoricas exigem `nearest`.
    """
    with rasterio.open(path) as ds:
        coords = _coords_in_crs(lon, lat, ds.crs)
        idx = list(indexes) if indexes else list(range(1, ds.count + 1))
        nodata = ds.nodata
        if ds.width * ds.height > max_pixels or resampling == Resampling.nearest:
            values = np.array(list(ds.sample(coords, indexes=idx)), dtype="float64")
        else:
            data = ds.read(idx)
            transform = ds.transform
            x = np.array([c[0] for c in coords])
            y = np.array([c[1] for c in coords])
            col = (x - transform.c) / transform.a - 0.5
            row = (y - transform.f) / transform.e - 0.5
            c0 = np.clip(np.floor(col).astype(int), 0, ds.width - 2)
            r0 = np.clip(np.floor(row).astype(int), 0, ds.height - 2)
            tx = np.clip(col - np.floor(col), 0, 1)
            ty = np.clip(row - np.floor(row), 0, 1)
            a = data[:, r0, c0]
            b = data[:, r0, c0 + 1]
            c = data[:, r0 + 1, c0]
            d = data[:, r0 + 1, c0 + 1]
            values = ((1 - tx) * (1 - ty) * a + tx * (1 - ty) * b
                      + (1 - tx) * ty * c + tx * ty * d).T
    if nodata is not None:
        values[values == nodata] = np.nan
    return values


def terrain_features(dem_path: str | Path, lon: np.ndarray, lat: np.ndarray) -> pd.DataFrame:
    """Elevacao, declividade e aspecto na grade do DEM."""
    with rasterio.open(dem_path) as ds:
        dem = ds.read(1).astype("float64")
        transform = ds.transform
        nodata = ds.nodata
        lat0 = transform.f + dem.shape[0] / 2 * transform.e
        res_deg = abs(transform.a)
        dy = res_deg * 111_320.0
        dx = res_deg * 111_320.0 * np.cos(np.deg2rad(lat0))
        gy, gx = np.gradient(dem, dy, dx)
        slope = np.degrees(np.arctan(np.hypot(gx, gy)))
        aspect = (np.degrees(np.arctan2(-gx, gy)) + 360.0) % 360.0

    cols = np.floor((lon - transform.c) / transform.a).astype(int)
    rows = np.floor((lat - transform.f) / transform.e).astype(int)
    rows = np.clip(rows, 0, dem.shape[0] - 1)
    cols = np.clip(cols, 0, dem.shape[1] - 1)
    elev = dem[rows, cols]
    out = pd.DataFrame({
        "elev": elev,
        "slope": slope[rows, cols],
        "aspect": aspect[rows, cols],
    })
    out.loc[(elev == nodata) | ~np.isfinite(elev), ["elev", "slope", "aspect"]] = np.nan
    return out


def load_era5(path: str | Path) -> dict:
    from netCDF4 import Dataset, num2date

    ds = Dataset(str(path))
    time_name = "valid_time" if "valid_time" in ds.variables else "time"
    times = num2date(ds[time_name][:], ds[time_name].units, only_use_cftime_datetimes=False)
    data = {
        "times": pd.to_datetime([t.isoformat() for t in times]),
        "lat": np.asarray(ds["latitude"][:]),
        "lon": np.asarray(ds["longitude"][:]),
    }
    for name in ERA5_VARS.values():
        data[name] = np.asarray(ds[name][:], dtype="float64")
    ds.close()
    return data


def era5_features(era5: dict, lon: np.ndarray, lat: np.ndarray, dates: pd.Series) -> pd.DataFrame:
    """Valores mensais no mes do footprint + climatologia 2019-2024."""
    ilat = np.abs(era5["lat"][None, :] - np.asarray(lat)[:, None]).argmin(axis=1)
    ilon = np.abs(era5["lon"][None, :] - np.asarray(lon)[:, None]).argmin(axis=1)
    months = pd.to_datetime(dates).dt.month.to_numpy() - 1
    years = pd.to_datetime(dates).dt.year.to_numpy()
    time_index = np.array([
        np.where((era5["times"].year == y) & (era5["times"].month == m + 1))[0][0]
        for y, m in zip(years, months)
    ])

    def take(name):
        return era5[name][time_index, ilat, ilon]

    out = pd.DataFrame({
        "era5_t2m_c": take("t2m") - 273.15,
        "era5_tp_mm_day": take("tp") * 1000.0,
        "era5_pev_mm_day": take("pev") * 1000.0,
        "era5_ssrd_mj_m2_day": take("ssrd") / 1e6,
        "era5_swvl1": take("swvl1"),
        "era5_swvl2": take("swvl2"),
        "era5_swvl3": take("swvl3"),
        "era5_swvl4": take("swvl4"),
    })

    span = (era5["times"].year >= 2019) & (era5["times"].year <= 2024)
    clim_t2m = era5["t2m"][span].mean(axis=0) - 273.15
    clim_tp = era5["tp"][span].mean(axis=0) * 365.25 * 1000.0
    clim_ssrd = era5["ssrd"][span].mean(axis=0) / 1e6
    clim_swvl = era5["swvl1"][span].mean(axis=0)
    out["era5_t2m_clim"] = clim_t2m[ilat, ilon]
    out["era5_precip_annual_mm"] = clim_tp[ilat, ilon]
    out["era5_ssrd_clim"] = clim_ssrd[ilat, ilon]
    out["era5_swvl1_clim"] = clim_swvl[ilat, ilon]
    return out


def mapbiomas_class(raster_dir: str | Path, year: int, lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    path = Path(raster_dir) / f"mapbiomas_col11_{year}.tif"
    values = sample_raster(path, lon, lat, indexes=[1], resampling=Resampling.nearest)
    return values[:, 0].astype("int16")


def window_mean(
    path: str | Path,
    lon: float,
    lat: float,
    half_m: float = 500.0,
    indexes: Sequence[int] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Media de bandas numa janela de ~1 km em torno do ponto.

    Retorna (medias, contagem de pixels validos por banda).
    """
    with rasterio.open(path) as ds:
        x, y = _coords_in_crs(np.array([lon]), np.array([lat]), ds.crs)[0]
        px_x, px_y = abs(ds.transform.a), abs(ds.transform.e)
        if ds.crs.is_geographic:
            mx = px_x * 111_320.0 * np.cos(np.deg2rad(lat))
            my = px_y * 110_574.0
        else:
            mx, my = px_x, px_y
        hx = max(1, int(round(half_m / mx)))
        hy = max(1, int(round(half_m / my)))
        col, row = (~ds.transform) @ (x, y)
        win = Window(int(col) - hx, int(row) - hy, 2 * hx + 1, 2 * hy + 1)
        arr = ds.read(indexes or list(range(1, ds.count + 1)),
                      window=win, boundless=True, masked=True).astype("float64")
        flat = arr.reshape(arr.shape[0], -1)
        means = np.ma.mean(flat, axis=1).filled(np.nan)
        counts = (~np.ma.getmaskarray(flat)).sum(axis=1)
    return means, counts


def window_slope_mean(dem_path: str | Path, lon: float, lat: float,
                      half_m: float = 500.0) -> float:
    with rasterio.open(dem_path) as ds:
        x, y = _coords_in_crs(np.array([lon]), np.array([lat]), ds.crs)[0]
        res_deg = abs(ds.transform.a)
        hx = max(2, int(round(half_m / (res_deg * 111_320.0))))
        col, row = (~ds.transform) @ (x, y)
        win = Window(int(col) - hx, int(row) - hx, 2 * hx + 1, 2 * hx + 1)
        dem = ds.read(1, window=win, boundless=True, masked=True).astype("float64")
    dem = np.ma.filled(dem, np.nan)
    dy = res_deg * 111_320.0
    dx = res_deg * 111_320.0 * np.cos(np.deg2rad(lat))
    gy, gx = np.gradient(dem, dy, dx)
    return float(np.nanmean(np.degrees(np.arctan(np.hypot(gx, gy)))))


SCL_BAD = {0, 1, 3, 8, 9, 10, 11}


def window_valid_fraction(
    path: str | Path,
    lon: float,
    lat: float,
    index: int,
    bad_values: Iterable[int],
    half_m: float = 500.0,
) -> float:
    with rasterio.open(path) as ds:
        x, y = _coords_in_crs(np.array([lon]), np.array([lat]), ds.crs)[0]
        px_x, px_y = abs(ds.transform.a), abs(ds.transform.e)
        if ds.crs.is_geographic:
            mx = px_x * 111_320.0 * np.cos(np.deg2rad(lat))
            my = px_y * 110_574.0
        else:
            mx, my = px_x, px_y
        hx = max(1, int(round(half_m / mx)))
        hy = max(1, int(round(half_m / my)))
        col, row = (~ds.transform) @ (x, y)
        win = Window(int(col) - hx, int(row) - hy, 2 * hx + 1, 2 * hy + 1)
        values = ds.read(index, window=win, boundless=True, masked=True)
    values = np.ma.filled(values, -1).astype("int64")
    return float(np.mean(~np.isin(values, list(bad_values))))


def build_field_table(
    sites_csv: str | Path,
    work_root: str | Path,
    era5_path: str | Path,
    mapbiomas_dir: str | Path,
    out_csv: str | Path,
    *,
    bioma: str = "Cerrado",
    half_m: float = 500.0,
    domain_classes: Iterable[int] = (3, 4),
) -> dict:
    sites = pd.read_csv(sites_csv)
    sites = sites[(sites["bioma"] == bioma)].dropna(subset=["lon", "lat", "agb_mg_ha"])
    era5 = load_era5(era5_path)
    root = Path(work_root)

    rows = []
    for _, site in sites.iterrows():
        folder = root / f"site_{int(site['site']):03d}"
        s2_path, dem_path = folder / "s2.tif", folder / "dem.tif"
        if not s2_path.exists() or not dem_path.exists():
            continue
        with rasterio.open(s2_path) as ds:
            names = ds.descriptions or tuple(S2_BANDS[: ds.count])
        means, counts = window_mean(s2_path, site["lon"], site["lat"], half_m=half_m)
        scl_idx = names.index("scl") + 1
        valid_fraction = window_valid_fraction(
            s2_path, site["lon"], site["lat"], scl_idx, SCL_BAD, half_m=half_m)
        elev_mean, _ = window_mean(dem_path, site["lon"], site["lat"],
                                    half_m=half_m, indexes=[1])
        slope_mean = window_slope_mean(dem_path, site["lon"], site["lat"], half_m=half_m)
        klass = int(mapbiomas_class(mapbiomas_dir, 2024,
                                    np.array([site["lon"]]), np.array([site["lat"]]))[0])

        row = {"site": int(site["site"]), "nome": site.get("nome"), "uf": site.get("uf"),
               "lon": site["lon"], "lat": site["lat"],
               "agb_mg_ha": float(site["agb_mg_ha"]),
               "agb_lo95": site.get("agb_lo95"), "agb_hi95": site.get("agb_hi95"),
               "mapbiomas_class": klass, "elev": float(elev_mean[0]),
               "slope": slope_mean}
        for i, name in enumerate(names):
            if name == "scl":
                continue
            row[f"s2_{name}"] = float(means[i])
        row["s2_valid_fraction"] = valid_fraction
        clim = era5_features(era5, np.array([site["lon"]]), np.array([site["lat"]]),
                             pd.Series(["2022-07-01"]))
        for col in ("era5_t2m_clim", "era5_precip_annual_mm", "era5_ssrd_clim", "era5_swvl1_clim"):
            row[col] = float(clim[col].iloc[0])
        rows.append(row)

    table = pd.DataFrame(rows)
    table = table[table["mapbiomas_class"].isin(list(domain_classes))].reset_index(drop=True)
    table["feature_na"] = table[[c for c in table if c.startswith(("s2_", "era5_"))]
                                + ["elev", "slope"]].isna().any(axis=1)
    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False)
    summary = {"sites_in": int(len(sites)), "rows": int(len(table)),
               "in_domain": int(len(table)), "classes": table["mapbiomas_class"].value_counts().to_dict(),
               "path": str(out_path)}
    out_path.with_suffix(".summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def build_training_table(
    gedi_csv: str | Path,
    s2_path: str | Path,
    dem_path: str | Path,
    era5_path: str | Path,
    mapbiomas_dir: str | Path,
    out_csv: str | Path,
    bioma: str,
    domain_classes: Iterable[int] = (3, 4),
) -> dict:
    gedi = pd.read_csv(gedi_csv)
    with rasterio.open(Path(mapbiomas_dir) / "mapbiomas_col11_2024.tif") as ds:
        transform = ds.transform
    rows, cols, lon_c, lat_c = snap_to_grid(gedi["lon_lowestmode"].to_numpy(),
                                            gedi["lat_lowestmode"].to_numpy(), transform)

    years = pd.to_datetime(gedi["granule_time"]).dt.year.to_numpy()
    classes = np.full(len(gedi), -1, dtype="int16")
    for year in np.unique(years):
        mask = years == year
        classes[mask] = mapbiomas_class(mapbiomas_dir, int(year), lon_c[mask], lat_c[mask])

    keep = np.isin(classes, list(domain_classes))
    keep &= np.isfinite(gedi["agbd"].to_numpy())

    table = gedi.loc[keep].reset_index(drop=True)
    lon_c, lat_c = lon_c[keep], lat_c[keep]
    table["pixel_row"] = rows[keep]
    table["pixel_col"] = cols[keep]
    table["pixel_lon"] = lon_c
    table["pixel_lat"] = lat_c
    table["mapbiomas_class"] = classes[keep]

    s2 = sample_raster(s2_path, lon_c, lat_c)
    with rasterio.open(s2_path) as ds:
        names = ds.descriptions or tuple(S2_BANDS[: ds.count])
    for i, name in enumerate(names):
        table[f"s2_{name}"] = s2[:, i]
    if "scl" in names:
        table["s2_valid"] = ~np.isin(table["s2_scl"].to_numpy(), [0, 1, 3, 8, 9, 10, 11])
        table = table.drop(columns=["s2_scl"])
    elif "nobs" in names:
        table["s2_valid"] = table["s2_nobs"] >= 3

    table = pd.concat([table, terrain_features(dem_path, lon_c, lat_c)], axis=1)
    table = pd.concat([table, era5_features(load_era5(era5_path), lon_c, lat_c,
                                            pd.to_datetime(table["granule_time"]))], axis=1)
    table["bioma"] = bioma

    feature_cols = [c for c in table.columns if c.startswith(("s2_", "era5_"))] + ["elev", "slope", "aspect"]
    table["feature_na"] = table[feature_cols].isna().any(axis=1)

    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False)

    summary = {
        "rows_in": int(len(gedi)),
        "rows_in_domain": int(keep.sum()),
        "rows_na_features": int(table["feature_na"].sum()),
        "classes": {int(k): int(v) for k, v in table["mapbiomas_class"].value_counts().items()},
        "agbd_median": float(table["agbd"].median()),
        "path": str(out_path),
    }
    out_path.with_suffix(".summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary
