"""Esquema canônico de observações de biomassa (ADR-0032).

A tabela canônica separa o que é medição de campo, observação estrutural, estimativa GEDI e
produto global. Ela é deliberadamente conservadora: campos desconhecidos ficam vazios e são
descritos em `quality_flags`, em vez de inventados.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

OBSERVATION_COLUMNS = [
    "observation_id",
    "source",
    "source_version",
    "observation_type",
    "reference_date",
    "geometry_wkt",
    "crs",
    "lon",
    "lat",
    "location_accuracy_m",
    "support_area_ha",
    "biome",
    "fitofisionomia",
    "fitofisionomia_group",
    "mapbiomas_class",
    "agb_mg_ha",
    "agb_uncertainty_mg_ha",
    "uncertainty_type",
    "method",
    "allometric_equation",
    "quality_flags",
    "license",
    "citation",
    "model_status",
    "notes",
]

REQUIRED_COLUMNS = [
    "observation_id",
    "source",
    "source_version",
    "observation_type",
    "geometry_wkt",
    "crs",
    "agb_mg_ha",
    "license",
    "model_status",
]

VALID_OBSERVATION_TYPES = {
    "field",
    "lidar",
    "gedi_l4a",
    "global_product",
    "benchmark",
}

VALID_MODEL_STATUS = {
    "training",
    "calibration",
    "validation",
    "benchmark",
    "excluded",
}


def empty_observations() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="object") for c in OBSERVATION_COLUMNS})


def _as_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return str(value).strip()


def _as_float(value: Any) -> float:
    if value is None:
        return np.nan
    if isinstance(value, str):
        value = value.strip().replace(".", "").replace(",", ".") if "," in value else value.strip()
    try:
        out = float(value)
    except (TypeError, ValueError):
        return np.nan
    return out if np.isfinite(out) else np.nan


def _as_date(value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        ts = pd.Timestamp(value)
        return "" if pd.isna(ts) else ts.strftime("%Y-%m-%d")
    text = str(value).strip()
    if not text:
        return ""
    ts = pd.to_datetime(text, errors="coerce")
    if pd.isna(ts):
        return text
    return ts.strftime("%Y-%m-%d")


def normalize_observations(df: pd.DataFrame) -> pd.DataFrame:
    """Garante colunas, tipos e ordenação sem descartar registros inválidos."""
    out = df.copy()
    for col in OBSERVATION_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out = out[OBSERVATION_COLUMNS]

    for col in (
        "observation_id", "source", "source_version", "observation_type",
        "reference_date", "geometry_wkt", "crs", "biome", "fitofisionomia",
        "fitofisionomia_group", "uncertainty_type", "method", "allometric_equation",
        "quality_flags", "license", "citation", "model_status", "notes",
    ):
        out[col] = out[col].map(_as_text).astype("object")

    out["reference_date"] = out["reference_date"].map(_as_date)

    for col in ("lon", "lat", "location_accuracy_m", "support_area_ha", "agb_mg_ha",
                "agb_uncertainty_mg_ha", "mapbiomas_class"):
        out[col] = out[col].map(_as_float).astype("float64")

    out["lon"] = out["lon"].where(out["lon"].between(-180, 180))
    out["lat"] = out["lat"].where(out["lat"].between(-90, 90))
    return out.reset_index(drop=True)


def validate_observations(df: pd.DataFrame) -> dict[str, list[str]]:
    """Retorna erros e avisos; não altera a tabela."""
    errors: list[str] = []
    warnings: list[str] = []
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"colunas obrigatórias ausentes: {missing}")
        return {"errors": errors, "warnings": warnings}

    df = df.copy()
    for col in OBSERVATION_COLUMNS:
        if col not in df.columns:
            df[col] = "" if col not in {
                "lon", "lat", "location_accuracy_m", "support_area_ha", "agb_mg_ha",
                "agb_uncertainty_mg_ha", "mapbiomas_class",
            } else np.nan

    if df.empty:
        warnings.append("tabela vazia")
        return {"errors": errors, "warnings": warnings}

    ids = df["observation_id"].astype(str)
    blank_ids = int((ids.str.strip() == "").sum())
    if blank_ids:
        errors.append(f"{blank_ids} observações sem observation_id")
    dup = int(ids[ids.str.strip() != ""].duplicated().sum())
    if dup:
        errors.append(f"{dup} observation_id duplicados")

    types = set(df["observation_type"].astype(str).str.strip())
    bad_types = sorted(types - VALID_OBSERVATION_TYPES)
    if bad_types:
        warnings.append(f"tipos de observação não reconhecidos: {bad_types}")

    status = set(df["model_status"].astype(str).str.strip())
    bad_status = sorted(status - VALID_MODEL_STATUS)
    if bad_status:
        warnings.append(f"status de modelo não reconhecidos: {bad_status}")

    agb = pd.to_numeric(df["agb_mg_ha"], errors="coerce")
    bad_agb = int((~np.isfinite(agb)).sum())
    if bad_agb:
        errors.append(f"{bad_agb} registros sem AGB finita")
    negative = int((agb < 0).sum())
    if negative:
        errors.append(f"{negative} registros com AGB negativa")

    unc = pd.to_numeric(df["agb_uncertainty_mg_ha"], errors="coerce")
    negative_unc = int((unc < 0).sum())
    if negative_unc:
        errors.append(f"{negative_unc} registros com incerteza negativa")

    for col in ("support_area_ha", "location_accuracy_m"):
        vals = pd.to_numeric(df[col], errors="coerce")
        negative_vals = int((vals < 0).sum())
        if negative_vals:
            errors.append(f"{negative_vals} registros com {col} negativa")

    blank_geom = int((df["geometry_wkt"].astype(str).str.strip() == "").sum())
    if blank_geom:
        warnings.append(f"{blank_geom} registros sem geometria")

    try:
        from shapely import wkt

        invalid_geom = 0
        for value in df["geometry_wkt"].astype(str):
            if not value.strip():
                continue
            try:
                geom = wkt.loads(value)
                if geom.is_empty or not geom.is_valid:
                    invalid_geom += 1
            except Exception:
                invalid_geom += 1
        if invalid_geom:
            errors.append(f"{invalid_geom} geometrias inválidas ou vazias")
    except Exception:
        warnings.append("shapely indisponível; geometria não validada")

    return {"errors": errors, "warnings": warnings}


def write_observations(df: pd.DataFrame, path: str | Path) -> Path:
    """Escreve CSV, Parquet (se pyarrow) ou GeoPackage."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    table = normalize_observations(df)
    suffix = out.suffix.lower()

    if suffix == ".parquet":
        try:
            table.to_parquet(out, index=False)
        except ImportError as exc:
            raise RuntimeError(
                "Parquet requer pyarrow; instale pyarrow ou use .csv/.gpkg"
            ) from exc
        return out

    if suffix in {".gpkg", ".geojson", ".shp"}:
        from shapely import wkt

        import geopandas as gpd

        geometry = [wkt.loads(v) if str(v).strip() else None for v in table["geometry_wkt"]]
        crs_values = table["crs"].dropna().astype(str)
        crs = crs_values.iloc[0] if len(crs_values) and crs_values.iloc[0] else "EPSG:4326"
        gdf = gpd.GeoDataFrame(table.drop(columns=["geometry_wkt"]), geometry=geometry, crs=crs)
        driver = "GPKG" if suffix == ".gpkg" else "GeoJSON" if suffix == ".geojson" else "ESRI Shapefile"
        gdf.to_file(out, driver=driver)
        return out

    table.to_csv(out, index=False, encoding="utf-8")
    return out


def read_observations(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".parquet":
        table = pd.read_parquet(p)
    elif p.suffix.lower() in {".gpkg", ".geojson", ".shp"}:
        import geopandas as gpd

        gdf = gpd.read_file(p)
        table = pd.DataFrame(gdf.drop(columns=["geometry"]))
        table["geometry_wkt"] = gdf.geometry.apply(
            lambda g: "" if g is None else g.wkt
        )
        table["crs"] = str(gdf.crs) if gdf.crs else ""
    else:
        table = pd.read_csv(p)
    return normalize_observations(table)


def merge_observations(frames: list[pd.DataFrame]) -> pd.DataFrame:
    frames = [normalize_observations(f) for f in frames if f is not None and len(f)]
    if not frames:
        return empty_observations()
    out = pd.concat(frames, ignore_index=True)
    return normalize_observations(out)
