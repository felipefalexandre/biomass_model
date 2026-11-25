"""ORNL Sustainable Landscapes Brazil: AGB/ha por sítio (DDLS fator 10).

Estimador: para cada transecto de 500 m, densidade = Σ AGB_i / area_i; a área de inclusão
por fuste é 2·L·(DBH/10) (L=500 m, DBH em cm → largura em m). O valor do sítio é a média
entre transectos; a incerteza é o erro padrão entre transectos (não entre árvores).
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _area_ha(dbh_cm: pd.Series, line_m: float = 500.0) -> pd.Series:
    width_m = dbh_cm / 10.0
    return 2.0 * line_m * width_m / 10_000.0


def density_from_agb_area(
    df: pd.DataFrame,
    *,
    agb_col: str = "AGB",
    area_col: str = "area_sampled",
    transect_col: str = "transect",
) -> dict[str, Any]:
    d = df.copy()
    for c in (agb_col, area_col):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d[np.isfinite(d[agb_col]) & np.isfinite(d[area_col]) & (d[area_col] > 0)]
    per = d.groupby(transect_col).apply(lambda g: float((g[agb_col] / g[area_col]).sum()))
    return {
        "density_mg_ha": float(per.mean()),
        "se_mg_ha": float(per.std(ddof=1) / np.sqrt(len(per))) if len(per) > 1 else np.nan,
        "n_transects": int(len(per)),
        "n_trees": int(len(d)),
        "per_transect": [float(x) for x in per.values],
        "method": "AGB_area_sampled",
    }


def _tree_agb(row: pd.Series, dbh: float, h: float, wsd: float) -> float:
    typ = str(row.get("type", "")).strip().upper()
    if typ in ("P", "PT"):
        return float(np.exp(0.9285 * np.log(dbh ** 2) + 5.7236) * 1.05001 / 1e3)
    if typ == "L":
        return float(np.exp(-1.484 + 2.657 * np.log(dbh)) / 1e3)
    if not (np.isfinite(wsd) and wsd > 0 and np.isfinite(h) and h > 0 and dbh > 0):
        return np.nan
    return float(0.0509 * wsd * dbh ** 2 * h / 1000.0)  # kg -> Mg


def density_from_measurements(
    df: pd.DataFrame,
    suffix: str,
    *,
    transect_col: str = "transect",
    line_m: float = 500.0,
) -> dict[str, Any]:
    """Calcula AGB por árvore (Chave 2005/palmeira/liana) e densidade por transecto."""
    dbh = pd.to_numeric(df[f"DBH_{suffix}"], errors="coerce")
    h = pd.to_numeric(df[f"Htot_{suffix}"], errors="coerce")
    wsd = pd.to_numeric(df[f"WSD_{suffix}"], errors="coerce")
    dead = df[f"dead_{suffix}"].astype(str).str.upper()
    alive = ~dead.eq("D")
    agb = df.apply(lambda r: _tree_agb(r, r[f"DBH_{suffix}"], r[f"Htot_{suffix}"],
                                       r[f"WSD_{suffix}"]), axis=1)
    d = pd.DataFrame({
        "transect": df[transect_col], "agb": agb, "dbh": dbh, "alive": alive,
        "type": df.get("type", "").astype(str).str.upper(),
    })
    d = d[np.isfinite(d["agb"]) & np.isfinite(d["dbh"]) & (d["dbh"] > 0) & d["alive"]]
    # palmeiras e lianas exigem alometria propria; excluidas nesta versao
    d = d[d["type"].eq("O")]
    d["area"] = _area_ha(d["dbh"], line_m=line_m)
    per = d.groupby("transect").apply(lambda g: float((g["agb"] / g["area"]).sum()))
    return {
        "density_mg_ha": float(per.mean()),
        "se_mg_ha": float(per.std(ddof=1) / np.sqrt(len(per))) if len(per) > 1 else np.nan,
        "n_transects": int(len(per)),
        "n_trees": int(len(d)),
        "per_transect": [float(x) for x in per.values],
        "method": "allometry_Chave2005_dbh10",
    }


def site_density(path: str | Path, *, line_m: float = 500.0) -> dict[str, Any] | None:
    p = Path(path)
    df = pd.read_csv(p, encoding="latin-1")
    if "AGB" in df.columns and "area_sampled" in df.columns:
        out = density_from_agb_area(df)
    elif "DBH_09" in df.columns:
        out = density_from_measurements(df, "09", line_m=line_m)
    else:
        return None
    out["site"] = p.stem
    return out


SHORT_NAME = "Forest_Inventory_Brazil_2007"
SOURCE = "https://doi.org/10.3334/ORNLDAAC/2007"
LICENSE = "NASA open data"


def fetch_ornl_plot_companions(
    out_dir: str | Path,
    *,
    manifest: bool = True,
) -> dict[str, Any]:
    """Baixa os shapefiles/plot companions do ORNL (coordenadas dos transectos)."""
    import earthaccess

    from ..credentials import require_earthdata
    from ..manifest import build_manifest, write_manifest

    require_earthdata()
    earthaccess.login(strategy="environment")
    results = earthaccess.search_data(short_name=SHORT_NAME, count=-1)
    selected = [
        g for g in results
        if any(link.endswith(".zip") and "inventory_plots" in link for link in g.data_links())
    ]
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    files = earthaccess.download(selected, str(root))
    summary = {
        "out_dir": str(root),
        "granules": len(selected),
        "files": len(files),
        "source": SOURCE,
        "license": LICENSE,
    }
    if manifest:
        write_manifest(build_manifest(
            "ornl_plot_companions",
            {"short_name": SHORT_NAME, "granules": len(selected)},
            [Path(f) for f in files], license=LICENSE, account="Earthdata token",
            source=SOURCE, notes="shapefiles de transectos por sitio/ano",
        ))
    return summary


def build_ornl_site_coords(
    plots_dir: str | Path,
    out_csv: str | Path,
) -> dict[str, Any]:
    """Extrai centroides de sitios a partir dos zips de transectos do ORNL."""
    import geopandas as gpd

    root = Path(plots_dir)
    out_dir = root / "extracted"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for z in sorted(root.glob("*.zip")):
        if z.name.endswith(".sha256"):
            continue
        match = re.match(r"^(.*?)_(\d{4})(?:_\d{4})?_inventory_plots", z.stem)
        if not match:
            continue
        site = match.group(1)
        target = out_dir / z.stem
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(z) as archive:
            archive.extractall(target)
        shapefiles = list(target.rglob("*.shp"))
        if not shapefiles:
            continue
        try:
            gdf = gpd.read_file(shapefiles[0])
        except Exception:
            continue
        if gdf.empty or gdf.crs is None:
            continue
        geo = gdf.to_crs("EPSG:4326")
        centroid = geo.geometry.union_all().centroid
        bounds = geo.total_bounds
        rows.append({
            "site": site,
            "lon": float(centroid.x),
            "lat": float(centroid.y),
            "lon_min": float(bounds[0]),
            "lon_max": float(bounds[2]),
            "lat_min": float(bounds[1]),
            "lat_max": float(bounds[3]),
            "n_vertices": 0,
            "source_file": z.name,
        })
    table = pd.DataFrame(rows)
    if table.empty:
        raise ValueError("nenhum shapefile valido nos zips ORNL")
    table = table.groupby("site", as_index=False).agg({
        "lon": "mean", "lat": "mean", "lon_min": "min", "lon_max": "max",
        "lat_min": "min", "lat_max": "max", "n_vertices": "sum",
        "source_file": "first",
    })
    out = Path(out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out, index=False, encoding="utf-8")
    return {"out": str(out), "sites": int(len(table)), "rows": table.to_dict(orient="records")}
