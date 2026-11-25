"""Adaptadores de inventários para o esquema canônico (ADR-0032).

Cada adaptador documenta a fonte, a licença, o método de obtenção da AGB e as limitações. Campos
desconhecidos permanecem vazios; não são preenchidos por suposição.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..stratification import classify_fitofisionomia
from .schema import merge_observations, normalize_observations

PLOS_CITATION = "Roitman et al. 2018, PLOS ONE, doi:10.1371/journal.pone.0196742"
IFN_CITATION = "SFB/IFN — Painel de Biomassa e Carbono"
ORNL_CITATION = "ORNL DAAC Sustainable Landscapes Brazil, doi:10.3334/ORNLDAAC/2007"
GEDI_CITATION = "GEDI L4A V2.1, doi:10.5067/GEDI/GEDI04_A.002"


def _point_wkt(lon: float, lat: float) -> str:
    if not (np.isfinite(lon) and np.isfinite(lat)):
        return ""
    return f"POINT ({lon:.8f} {lat:.8f})"


def _safe_float(value: Any) -> float:
    if value is None:
        return np.nan
    if isinstance(value, str):
        text = value.strip()
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        value = text
    try:
        out = float(value)
    except (TypeError, ValueError):
        return np.nan
    return out if np.isfinite(out) else np.nan


def _append_flag(flags: str, flag: str) -> str:
    parts = [p for p in str(flags).split(";") if p]
    if flag not in parts:
        parts.append(flag)
    return ";".join(parts)


def load_plos2018(
    path: str | Path,
    *,
    usage: str = "validation",
    include_outside_cerrado: bool = True,
) -> pd.DataFrame:
    """Carrega a tabela S3 do PLOS 2018 (AGB por sítio, Cerrado s.s.)."""
    df = pd.read_excel(path, sheet_name=0, usecols="A:M")
    site_number = pd.to_numeric(df["Site Number"], errors="coerce")
    df = df[site_number.notna()].copy()
    df["site_number"] = site_number[site_number.notna()].astype(int).to_numpy()

    lon = df["Longitude (decimal)"].map(_safe_float)
    lat = df["Latitude (decimal)"].map(_safe_float)
    agb = df["Biomass (ton ha-1)"].map(_safe_float)
    low = df["BiomassInferior  95% CIL (ton ha-1)"].map(_safe_float)
    high = df["BiomassSuperior 95% CIL (ton ha-1)"].map(_safe_float)
    half = (high - low) / 2.0

    rows = []
    for i, row in df.iterrows():
        biome = "Cerrado"
        eco = str(row.get("Ecoregion", "")).strip()
        state = str(row.get("State", "")).strip()
        flags = "site_level_agb;support_area_unknown;ci95_source"
        if eco:
            flags = _append_flag(flags, f"ecoregion_{re.sub(r'[^A-Za-z0-9]+', '_', eco).strip('_').lower()}")
        if not include_outside_cerrado and state in {"AM", "RR", "AC", "AP", "PA", "RO"}:
            continue
        mapped = classify_fitofisionomia("Cerrado sensu stricto", biome="Cerrado")
        rows.append({
            "observation_id": f"plos2018:{int(row['site_number'])}",
            "site": int(row["site_number"]),
            "source": "PLOS2018",
            "source_version": "Roitman2018",
            "observation_type": "field",
            "reference_date": row.get("Inventory date"),
            "geometry_wkt": _point_wkt(lon.loc[i], lat.loc[i]),
            "crs": "EPSG:4326",
            "lon": lon.loc[i],
            "lat": lat.loc[i],
            "location_accuracy_m": np.nan,
            "support_area_ha": np.nan,
            "biome": biome,
            "fitofisionomia": mapped["fitofisionomia"],
            "fitofisionomia_group": mapped["fitofisionomia_group"],
            "mapbiomas_class": mapped["mapbiomas_class"],
            "agb_mg_ha": agb.loc[i],
            "agb_uncertainty_mg_ha": half.loc[i],
            "uncertainty_type": "ci95_half_width",
            "method": "published_site_agb",
            "allometric_equation": "",
            "quality_flags": _append_flag(flags, "biome_assumed_cerrado"),
            "license": "CC BY",
            "citation": PLOS_CITATION,
            "model_status": usage,
            "notes": f"State={state}; Ecoregion={eco}; Reference={row.get('Reference', '')}",
        })

    return normalize_observations(pd.DataFrame(rows))


def load_ifn_panel(
    path: str | Path,
    *,
    equation: str | None = "AGB_Chave",
    usage: str = "validation",
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Carrega o Painel de Biomassa e Carbono do IFN/SFB.

    O painel traz múltiplas equações por unidade amostral. Por padrão escolhe `AGB_Chave`; quando
    a equação não existe para uma UA, usa a primeira linha disponível e sinaliza a limitação.
    """
    columns = [
        "bioma", "uf", "lon_pc", "lat_pc", "ua", "n_subunidades", "sanidade",
        "classe_uso_da_terra", "tipologia_da_vegetacao", "equacoes", "area_ha",
        "agb_media_kg_por_ha", "agb_variancia_por_ua",
    ]
    df = pd.read_csv(
        path,
        sep=";",
        encoding="utf-8",
        encoding_errors="replace",
        usecols=columns,
        nrows=max_rows,
        low_memory=False,
    )
    df = df.copy()
    for col in ("lon_pc", "lat_pc", "n_subunidades", "area_ha", "agb_media_kg_por_ha",
                "agb_variancia_por_ua"):
        df[col] = df[col].map(_safe_float)
    df["equacoes"] = df["equacoes"].astype(str).str.strip()
    df["ua"] = df["ua"].astype(str).str.strip()

    if equation:
        with_eq = df[df["equacoes"] == equation].drop_duplicates("ua", keep="first")
        missing = df[~df["ua"].isin(with_eq["ua"])].sort_values(["ua", "equacoes"])
        fallback = missing.drop_duplicates("ua", keep="first")
        selected = pd.concat([with_eq, fallback], ignore_index=True)
    else:
        selected = df.drop_duplicates("ua", keep="first")

    rows = []
    for _, row in selected.iterrows():
        n_sub = row["n_subunidades"]
        variance = row["agb_variancia_por_ua"]
        se_kg = math.sqrt(variance / n_sub) if (
            np.isfinite(variance) and variance > 0 and np.isfinite(n_sub) and n_sub > 1
        ) else np.nan
        mapped = classify_fitofisionomia(row["tipologia_da_vegetacao"], biome=row["bioma"])
        flags = "ifn_panel;coarse_coordinates;multiple_equations;reference_date_unknown"
        if not equation or row["equacoes"] != equation:
            flags = _append_flag(flags, "equation_fallback")
        if not np.isfinite(se_kg):
            flags = _append_flag(flags, "uncertainty_unavailable")
        rows.append({
            "observation_id": f"ifn:{row['ua']}:{row['equacoes']}",
            "site": str(row["ua"]),
            "source": "IFN_SFB",
            "source_version": "painel_biomassa_carbono",
            "observation_type": "field",
            "reference_date": "",
            "geometry_wkt": _point_wkt(row["lon_pc"], row["lat_pc"]),
            "crs": "EPSG:4326",
            "lon": row["lon_pc"],
            "lat": row["lat_pc"],
            "location_accuracy_m": 11000.0,
            "support_area_ha": row["area_ha"],
            "biome": str(row["bioma"]).strip(),
            "fitofisionomia": mapped["fitofisionomia"],
            "fitofisionomia_group": mapped["fitofisionomia_group"],
            "mapbiomas_class": mapped["mapbiomas_class"],
            "agb_mg_ha": row["agb_media_kg_por_ha"] / 1000.0,
            "agb_uncertainty_mg_ha": se_kg / 1000.0 if np.isfinite(se_kg) else np.nan,
            "uncertainty_type": "approx_se_from_subunit_variance",
            "method": "ifn_panel_equation",
            "allometric_equation": row["equacoes"],
            "quality_flags": flags,
            "license": "CC BY",
            "citation": IFN_CITATION,
            "model_status": usage,
            "notes": f"UF={row['uf']}; classe_uso={row['classe_uso_da_terra']}; "
                     f"sanidade={row['sanidade']}; n_subunidades={n_sub}",
        })

    return normalize_observations(pd.DataFrame(rows))


def _find_col(columns: list[str], *candidates: str) -> str | None:
    lower = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return None


def _ornl_suffixes(df: pd.DataFrame) -> list[str]:
    found = []
    for col in df.columns:
        match = re.match(r"(?i)^DBH[._]?(\d{2,4})$", str(col).strip())
        if match:
            found.append(match.group(1))
    return sorted(set(found), key=lambda s: int(s))


def _density_from_agb_dbh(
    df: pd.DataFrame,
    *,
    agb_col: str,
    dbh_col: str,
    transect_col: str,
    dead_col: str | None,
    line_m: float = 500.0,
) -> dict[str, Any]:
    agb = pd.to_numeric(df[agb_col], errors="coerce")
    dbh = pd.to_numeric(df[dbh_col], errors="coerce")
    area = 2.0 * line_m * (dbh / 10.0) / 10_000.0
    dead = df[dead_col].astype(str).str.upper() if dead_col else pd.Series("A", index=df.index)
    alive = ~dead.eq("D")
    work = pd.DataFrame({
        "transect": df[transect_col],
        "agb": agb,
        "area": area,
        "alive": alive,
    })
    work = work[np.isfinite(work["agb"]) & np.isfinite(work["area"]) & (work["area"] > 0)
                & work["alive"]]
    per = work.groupby("transect").apply(lambda g: float((g["agb"] / g["area"]).sum()))
    return {
        "density_mg_ha": float(per.mean()) if len(per) else np.nan,
        "se_mg_ha": float(per.std(ddof=1) / np.sqrt(len(per))) if len(per) > 1 else np.nan,
        "n_transects": int(len(per)),
        "n_trees": int(len(work)),
        "method": "ornl_agb_ddls",
    }


def _ornl_coords(path: str | Path | None) -> dict[str, tuple[float, float]]:
    if path is None:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    lon_col = _find_col(list(df.columns), "lon", "longitude")
    lat_col = _find_col(list(df.columns), "lat", "latitude")
    site_col = _find_col(list(df.columns), "site", "site_id")
    if not (lon_col and lat_col and site_col):
        return {}
    out = {}
    for _, row in df.iterrows():
        lon = _safe_float(row[lon_col])
        lat = _safe_float(row[lat_col])
        if np.isfinite(lon) and np.isfinite(lat):
            out[str(row[site_col]).strip()] = (lon, lat)
    return out


def load_ornl_site(
    path: str | Path,
    *,
    site: str | None = None,
    year: int | str | None = None,
    usage: str = "validation",
    coords_path: str | Path | None = None,
) -> pd.DataFrame:
    """Carrega um CSV do ORNL e calcula AGB/ha por sítio/ano quando possível."""
    from ..datasets.ornl import density_from_agb_area, density_from_measurements

    p = Path(path)
    try:
        df = pd.read_csv(p, encoding="latin-1")
    except UnicodeDecodeError:
        df = pd.read_csv(p, encoding="utf-8", encoding_errors="replace")

    site_name = site
    if site_name is None:
        area_col = _find_col(list(df.columns), "area", "site")
        if area_col and len(df):
            site_name = str(df[area_col].iloc[0]).strip()
        else:
            site_name = p.stem.split("_")[0]

    transect_col = _find_col(list(df.columns), "transect", "trans", "Transect", "plot",
                             "group_code")
    if transect_col is None:
        df["_transect"] = "T1"
        transect_col = "_transect"
    dead_any = _find_col(list(df.columns), "dead", "Dead")
    suffix = None
    year_label = ""

    if "AGB" in df.columns and "area_sampled" in df.columns:
        result = density_from_agb_area(df, transect_col=transect_col)
        method = "ornl_agb_area_sampled"
        allometry = ""
        flags = "ornl_ddls;support_area_derived"
    elif "AGB" in df.columns:
        dbh_plain = _find_col(list(df.columns), "DBH", "dbh")
        if dbh_plain:
            dbh_col = dbh_plain
        else:
            suffixes = _ornl_suffixes(df)
            if not suffixes:
                return pd.DataFrame()
            suffix = suffixes[-1]
            dbh_col = _find_col(list(df.columns), f"DBH_{suffix}", f"DBH.{suffix}")
        if not dbh_col:
            return pd.DataFrame()
        result = _density_from_agb_dbh(
            df, agb_col="AGB", dbh_col=dbh_col, transect_col=transect_col,
            dead_col=dead_any,
        )
        method = "ornl_agb_ddls"
        allometry = ""
        flags = "ornl_ddls;agb_provided;support_area_derived;year_approx"
        year_label = suffix or ""
    else:
        suffixes = _ornl_suffixes(df)
        if not suffixes:
            return pd.DataFrame()
        if year is not None:
            wanted = str(year)
            suffix = wanted if wanted in suffixes else (wanted[-2:] if wanted[-2:] in suffixes else None)
        if suffix is None:
            suffix = suffixes[-1]
        dbh_col = _find_col(list(df.columns), f"DBH_{suffix}", f"DBH.{suffix}")
        h_col = _find_col(list(df.columns), f"Htot_{suffix}", f"Htot.{suffix}")
        wsd_col = _find_col(list(df.columns), f"WSD_{suffix}", f"WSD.{suffix}")
        dead_col = _find_col(list(df.columns), f"dead_{suffix}", f"dead.{suffix}", f"Dead.{suffix}")
        type_col = _find_col(list(df.columns), f"type_{suffix}", f"type.{suffix}", "type")
        if not (dbh_col and h_col and wsd_col):
            return pd.DataFrame()

        work = pd.DataFrame({
            "transect": df[transect_col],
            f"DBH_{suffix}": df[dbh_col],
            f"Htot_{suffix}": df[h_col],
            f"WSD_{suffix}": df[wsd_col],
            f"dead_{suffix}": df[dead_col] if dead_col else "A",
            "type": df[type_col] if type_col else "O",
        })
        result = density_from_measurements(work, suffix)
        method = "ornl_ddls_chave2005"
        allometry = "Chave et al. 2005"
        flags = "ornl_ddls;palms_lianas_partial;support_area_derived;year_approx"
        year_label = suffix

    density = result.get("density_mg_ha", np.nan)
    if not np.isfinite(density):
        return pd.DataFrame()

    coords = _ornl_coords(coords_path)
    lon, lat = coords.get(str(site_name).strip(), (np.nan, np.nan))
    fit = classify_fitofisionomia("tropical forest", biome="Amazônia")
    date_col = _find_col(list(df.columns), "date", "Date")
    ref_date = ""
    if date_col is not None and len(df):
        candidate = df[date_col].dropna()
        if len(candidate):
            ref_date = str(candidate.iloc[0])
    if not ref_date and str(year_label).isdigit() and len(str(year_label)) == 4:
        ref_date = f"{year_label}-01-01"
    if np.isfinite(density) and density > 400:
        flags = _append_flag(flags, "agb_gt_400_check")

    row = {
        "observation_id": f"ornl:{p.stem}",
        "site": str(site_name),
        "source": "ORNL_SLB",
        "source_version": "ORNLDAAC_2007",
        "observation_type": "field",
        "reference_date": ref_date,
        "geometry_wkt": _point_wkt(lon, lat),
        "crs": "EPSG:4326",
        "lon": lon,
        "lat": lat,
        "location_accuracy_m": np.nan,
        "support_area_ha": np.nan,
        "biome": "Amazônia",
        "fitofisionomia": fit["fitofisionomia"],
        "fitofisionomia_group": fit["fitofisionomia_group"],
        "mapbiomas_class": fit["mapbiomas_class"],
        "agb_mg_ha": float(density),
        "agb_uncertainty_mg_ha": float(result.get("se_mg_ha", np.nan)),
        "uncertainty_type": "se_between_transects",
        "method": method,
        "allometric_equation": allometry,
        "quality_flags": flags,
        "license": "NASA open",
        "citation": ORNL_CITATION,
        "model_status": usage,
        "notes": f"file={p.name}; n_transects={result.get('n_transects')}; n_trees={result.get('n_trees')}",
    }
    return normalize_observations(pd.DataFrame([row]))


def load_ornl_directory(
    root: str | Path,
    *,
    usage: str = "validation",
    coords_path: str | Path | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    frames = []
    files = sorted(Path(root).glob("*nventory*.csv"))
    if limit is not None:
        files = files[:limit]
    for path in files:
        try:
            frame = load_ornl_site(path, usage=usage, coords_path=coords_path)
        except Exception:
            continue
        if len(frame):
            frames.append(frame)
    return merge_observations(frames)


def load_ceda_manaus(
    path: str | Path,
    *,
    usage: str = "validation",
) -> pd.DataFrame:
    """Carrega o shapefile CEDA/NCEO Manaus 2014 (23 parcelas de 100 x 60 m)."""
    import geopandas as gpd

    from ..datasets.ceda import CITATION as CEDA_CITATION
    from ..datasets.ceda import LICENSE as CEDA_LICENSE

    gdf = gpd.read_file(path)
    if gdf.empty:
        raise ValueError("shapefile CEDA vazio")
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:32720")
    metric = gdf.to_crs("EPSG:32720")
    geo = gdf.to_crs("EPSG:4326")
    rows = []
    for i, (_, row) in enumerate(gdf.iterrows()):
        lon = float(geo.geometry.iloc[i].centroid.x)
        lat = float(geo.geometry.iloc[i].centroid.y)
        area_ha = float(metric.geometry.iloc[i].area / 10_000.0)
        plot = str(row.get("Plot_ID", i))
        fit = classify_fitofisionomia("tropical forest", biome="Amazônia")
        rows.append({
            "observation_id": f"ceda:{plot}",
            "site": i + 1,
            "source": "CEDA_MANAUS",
            "source_version": "v1.0_2014",
            "observation_type": "field",
            "reference_date": "2014-01-01",
            "geometry_wkt": _point_wkt(lon, lat),
            "crs": "EPSG:4326",
            "lon": lon,
            "lat": lat,
            "location_accuracy_m": 30.0,
            "support_area_ha": area_ha,
            "biome": "Amazônia",
            "fitofisionomia": fit["fitofisionomia"],
            "fitofisionomia_group": fit["fitofisionomia_group"],
            "mapbiomas_class": fit["mapbiomas_class"],
            "agb_mg_ha": _safe_float(row.get("AGB")),
            "agb_uncertainty_mg_ha": np.nan,
            "uncertainty_type": "",
            "method": "ceda_plot_agb",
            "allometric_equation": "",
            "quality_flags": "ceda_manaus;plot_100x60m;agb_from_source;uncertainty_unavailable",
            "license": CEDA_LICENSE,
            "citation": CEDA_CITATION,
            "model_status": usage,
            "notes": f"n_trees={row.get('n')}; meanDBH={row.get('meanDBH')}; meanH={row.get('meanH')}",
        })
    return normalize_observations(pd.DataFrame(rows))


def load_gedi_l4a(
    path: str | Path,
    *,
    usage: str = "calibration",
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Converte footprints GEDI L4A em observações canônicas, preservando o erro do produto."""
    df = pd.read_csv(path, nrows=max_rows)
    if "agbd" not in df.columns:
        raise KeyError("CSV GEDI sem coluna agbd")
    n = len(df)
    lon = df["lon_lowestmode"].map(_safe_float) if "lon_lowestmode" in df else pd.Series(np.nan, index=df.index)
    lat = df["lat_lowestmode"].map(_safe_float) if "lat_lowestmode" in df else pd.Series(np.nan, index=df.index)
    agb = df["agbd"].map(_safe_float)
    se = df["agbd_se"].map(_safe_float) if "agbd_se" in df else pd.Series(np.nan, index=df.index)
    date = df["granule_time"] if "granule_time" in df else pd.Series("", index=df.index)
    shot = df["shot_number"].astype(str) if "shot_number" in df else pd.Series([str(i) for i in range(n)], index=df.index)
    granule = df["granule"].astype(str) if "granule" in df else pd.Series("", index=df.index)
    flags = "gedi_l4a_model;not_field_measurement"
    if "degrade_zero" in df:
        flags = _append_flag(flags, "degrade_flag_retained")
    rows = []
    for i in range(n):
        rows.append({
            "observation_id": f"gedi_l4a:{i}:{shot.iloc[i]}",
            "source": "GEDI_L4A",
            "source_version": "V2.1",
            "observation_type": "gedi_l4a",
            "reference_date": date.iloc[i],
            "geometry_wkt": _point_wkt(lon.iloc[i], lat.iloc[i]),
            "crs": "EPSG:4326",
            "lon": lon.iloc[i],
            "lat": lat.iloc[i],
            "location_accuracy_m": np.nan,
            "support_area_ha": 0.0625,
            "biome": "",
            "fitofisionomia": "",
            "fitofisionomia_group": "",
            "mapbiomas_class": np.nan,
            "agb_mg_ha": agb.iloc[i],
            "agb_uncertainty_mg_ha": se.iloc[i],
            "uncertainty_type": "gedi_l4a_se",
            "method": "gedi_l4a_model",
            "allometric_equation": "",
            "quality_flags": flags,
            "license": "NASA open",
            "citation": GEDI_CITATION,
            "model_status": usage,
            "notes": f"granule={granule.iloc[i]}",
        })
    return normalize_observations(pd.DataFrame(rows))
