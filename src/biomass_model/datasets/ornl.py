"""ORNL Sustainable Landscapes Brazil: AGB/ha por sítio (DDLS fator 10).

Estimador: para cada transecto de 500 m, densidade = Σ AGB_i / area_i; a área de inclusão
por fuste é 2·L·(DBH/10) (L=500 m, DBH em cm → largura em m). O valor do sítio é a média
entre transectos; a incerteza é o erro padrão entre transectos (não entre árvores).
"""

from __future__ import annotations

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
