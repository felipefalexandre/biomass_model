"""Agregação de predições por polígono (produto de estoque) e incerteza por blocos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _block_ids(df: pd.DataFrame, block_px: int = 5) -> pd.Series:
    return (df["pixel_row"] // block_px).astype(str) + "_" + (df["pixel_col"] // block_px).astype(str)


def polygon_stats(
    csv_path: str | Path,
    out: str | Path | None = None,
    *,
    filter_col: str | None = None,
    filter_value: str | None = None,
    value_col: str = "pred",
    class_col: str | None = "mapbiomas_class",
    area_ha_per_row: float = 100.0,
    block_px: int = 5,
    n_boot: int = 400,
    seed: int = 42,
) -> dict[str, Any]:
    """Estatísticas de estoque para um subconjunto (polígono) de células.

    `area_ha_per_row` assume 1 km² por linha (100 ha). A incerteza é um block
    bootstrap sobre blocos de `block_px` células (~5 km), preservando correlação
    espacial; não é o erro padrão ingênuo de pixels.
    """
    df = pd.read_csv(csv_path)
    if filter_col and filter_value is not None:
        df = df[df[filter_col].astype(str) == str(filter_value)]
    df = df[np.isfinite(df[value_col])].reset_index(drop=True)
    if df.empty:
        raise ValueError("nenhuma célula no polígono/filtro")
    if "pixel_row" not in df or "pixel_col" not in df:
        raise ValueError("predições precisam de pixel_row/pixel_col para o bootstrap espacial")

    area_ha = len(df) * area_ha_per_row
    mean = float(df[value_col].mean())
    total = mean * area_ha

    df["_block"] = _block_ids(df, block_px)
    rng = np.random.default_rng(seed)
    blocks = df["_block"].unique()
    totals = []
    for _ in range(n_boot):
        pick = rng.choice(blocks, size=len(blocks), replace=True)
        sample = pd.concat([df[df["_block"] == b] for b in pick], ignore_index=True)
        totals.append(float(sample[value_col].mean() * area_ha))
    lo, hi = np.quantile(totals, [0.05, 0.95])

    by_class = []
    if class_col and class_col in df.columns:
        for klass, g in df.groupby(class_col):
            by_class.append({
                "class": int(klass),
                "n_cells": int(len(g)),
                "area_fraction": float(len(g) / len(df)),
                "mean_agbd": float(g[value_col].mean()),
                "area_ha": float(len(g) * area_ha_per_row),
                "total_mg": float(g[value_col].mean() * len(g) * area_ha_per_row),
            })

    result = {
        "csv": str(csv_path), "filter": {filter_col: filter_value} if filter_col else None,
        "n_cells": int(len(df)), "area_ha": float(area_ha),
        "mean_agbd": mean, "total_mg": float(total),
        "total_tg": float(total / 1e6),
        "ci90_total_mg": [float(lo), float(hi)],
        "ci90_relative": float((hi - lo) / 2 / total) if total else None,
        "by_class": by_class,
        "value_col": value_col, "area_ha_per_row": area_ha_per_row,
        "n_blocks": int(df["_block"].nunique()),
    }
    if out:
        Path(out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result
