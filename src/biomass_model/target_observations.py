"""Converte o target consolidado em observacoes canonicas e amostra estratificada.

O target por UA (`targets.py`) e uma tabela de analise; o extrator de features
(`observation_features.py`) consome o esquema canonico de observacoes. Este
modulo faz a ponte sem duplicar logica:

- `target_to_observations`: mapeia UA -> observacao (campo, licenca, data,
  incerteza de equacao e flags de suporte);
- `sample_target`: amostra estratificada reproduzivel por bioma/grupo/tier;
- o Tier A (pixel 30 m) entra como `validation`; o Tier B como `training`,
  coerente com o plano de dois estagios (docs/62).

Nao inventa data: quando so o ano e conhecido, usa 1 de janeiro e registra
`reference_date_year_only` em `quality_flags`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
from shapely.geometry import Point

from .inventory.schema import normalize_observations
from .stratification import classify_fitofisionomia

CITATION = "SFB. Painel de Biomassa e Carbono (IFN), CC BY."
LICENSE = "CC BY"


def _fitofisionomia_group(name: Any, mapbiomas_class: Any) -> str:
    try:
        code = int(mapbiomas_class) if pd.notna(mapbiomas_class) else None
    except (TypeError, ValueError):
        code = None
    try:
        mapped = classify_fitofisionomia(str(name), code)
        return str(mapped.get("fitofisionomia_group") or "unknown")
    except Exception:
        return "unknown"


def _location_accuracy_m(precision: Any) -> float:
    """Meia-celula da coordenada publicada (556,6 m para 2 casas)."""
    try:
        decimals = int(precision)
    except (TypeError, ValueError):
        return float("nan")
    return 55660.0 / (10 ** max(decimals, 0))


def target_to_observations(target: pd.DataFrame | str | Path) -> pd.DataFrame:
    """Converte a tabela de target (1 linha por UA) no esquema canonico."""
    if not isinstance(target, pd.DataFrame):
        target = pd.read_csv(target)
    required = {"ua", "lon", "lat", "ano", "agb_mg_ha", "bioma", "fitofisionomia"}
    missing = sorted(required - set(target.columns))
    if missing:
        raise ValueError(f"target sem colunas obrigatorias: {missing}")

    rows: list[dict[str, Any]] = []
    for row in target.itertuples(index=False):
        year = int(row.ano) if pd.notna(row.ano) else None
        reference_date = f"{year}-01-01" if year else ""
        tier = str(getattr(row, "tier", "") or "")
        support = str(getattr(row, "suporte", "") or "")
        agb = float(row.agb_mg_ha)
        agb_min = float(getattr(row, "agb_min_mg_ha", np.nan))
        agb_max = float(getattr(row, "agb_max_mg_ha", np.nan))
        half_range = (
            (agb_max - agb_min) / 2.0
            if np.isfinite(agb_min) and np.isfinite(agb_max) else np.nan
        )
        flags = [f"target_tier_{tier}", f"suporte_{support}"]
        if year:
            flags.append("reference_date_year_only")
        spread = getattr(row, "spread_razao", np.nan)
        if pd.notna(spread):
            flags.append(f"spread_razao_{float(spread):.1f}")
        rows.append({
            "observation_id": f"target:{row.ua}",
            "site": str(row.ua),
            "source": str(getattr(row, "source", "IFN/SFB")),
            "source_version": str(getattr(row, "source_version", "")),
            "observation_type": "field",
            "reference_date": reference_date,
            "geometry_wkt": Point(float(row.lon), float(row.lat)).wkt,
            "crs": "EPSG:4326",
            "lon": float(row.lon),
            "lat": float(row.lat),
            "location_accuracy_m": _location_accuracy_m(
                getattr(row, "precisao_decimais", np.nan)
            ),
            "support_area_ha": float(getattr(row, "area_pegada_ha", np.nan)),
            "biome": str(row.bioma),
            "fitofisionomia": str(row.fitofisionomia),
            "fitofisionomia_group": _fitofisionomia_group(
                row.fitofisionomia, getattr(row, "classe_mapbiomas", np.nan)
            ),
            "mapbiomas_class": getattr(row, "classe_mapbiomas", np.nan),
            "agb_mg_ha": agb,
            "agb_uncertainty_mg_ha": half_range,
            "uncertainty_type": "half_range_equations",
            "method": "ifn_painel_biomassa_carbono",
            "allometric_equation": "AGB_Chave (SFB)",
            "quality_flags": ";".join(flags),
            "license": LICENSE,
            "citation": CITATION,
            "model_status": "validation" if tier == "A" else "training",
            "notes": f"target consolidado; tier={tier}; suporte={support}",
        })
    return normalize_observations(pd.DataFrame(rows))


def sample_target(
    target: pd.DataFrame,
    n: int,
    *,
    tier: str | None = None,
    by: Sequence[str] = ("bioma", "fitofisionomia_group"),
    seed: int = 42,
    min_per_stratum: int = 1,
) -> pd.DataFrame:
    """Amostra estratificada reproduzivel, com alocacao proporcional."""
    frame = target.copy()
    if tier:
        wanted = {t.strip().upper() for t in str(tier).split(",") if t.strip()}
        frame = frame[frame["tier"].astype(str).str.upper().isin(wanted)].copy()
    if frame.empty:
        raise ValueError("filtro de tier nao deixou nenhuma UA")
    if "fitofisionomia_group" not in frame.columns and "fitofisionomia" in frame.columns:
        classes = frame["classe_mapbiomas"] if "classe_mapbiomas" in frame else [None] * len(frame)
        frame["fitofisionomia_group"] = [
            _fitofisionomia_group(name, code)
            for name, code in zip(frame["fitofisionomia"], classes)
        ]
    keys = [c for c in by if c in frame.columns]
    if not keys:
        keys = ["bioma"]
    frame["_stratum"] = frame[keys].astype(str).agg(" | ".join, axis=1)
    sizes = frame.groupby("_stratum").size()
    total = int(sizes.sum())
    if n >= total:
        return frame.drop(columns="_stratum").sample(frac=1.0, random_state=seed)

    raw = sizes / total * n
    alloc = np.floor(raw).astype(int).clip(lower=min_per_stratum)
    fractions = (raw - np.floor(raw)).sort_values(ascending=False)
    order = list(fractions.index)
    while int(alloc.sum()) < n:
        for key in order:
            if int(alloc.sum()) >= n:
                break
            if alloc[key] < sizes[key]:
                alloc[key] += 1
    while int(alloc.sum()) > n:
        candidates = alloc[alloc > min_per_stratum].sort_values(ascending=False)
        if candidates.empty:
            break
        alloc[candidates.index[0]] -= 1

    rng = np.random.default_rng(seed)
    parts = []
    for key, group in frame.groupby("_stratum"):
        take = min(int(alloc.get(key, min_per_stratum)), len(group))
        idx = rng.choice(group.index.to_numpy(), size=take, replace=False)
        parts.append(frame.loc[idx])
    sampled = pd.concat(parts, ignore_index=True)
    return sampled.drop(columns="_stratum").sample(frac=1.0, random_state=seed)


def write_observations(
    observations: pd.DataFrame,
    out_csv: str | Path,
    *,
    report_path: str | Path | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    observations.to_csv(out_csv, index=False, encoding="utf-8")
    digest = hashlib.sha256(out_csv.read_bytes()).hexdigest()
    report = {
        "rows": int(len(observations)),
        "path": str(out_csv),
        "sha256": digest,
        "by_tier": {},
        "by_biome": {
            str(k): int(v) for k, v in observations["biome"].value_counts().items()
        },
        "by_fitofisionomia_group": {
            str(k): int(v)
            for k, v in observations["fitofisionomia_group"].value_counts().items()
        },
        "by_model_status": {
            str(k): int(v)
            for k, v in observations["model_status"].value_counts().items()
        },
        "params": params or {},
    }
    if "quality_flags" in observations:
        tiers = observations["quality_flags"].astype(str).str.extract(
            r"target_tier_([A-Z])", expand=False
        )
        report["by_tier"] = {str(k): int(v) for k, v in tiers.value_counts().items()}
    if report_path is not None:
        Path(report_path).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        report["manifest"] = str(report_path)
    return report
