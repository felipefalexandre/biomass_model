"""Intervalos conformais para modelos de campo com validação por folds espaciais.

O modo `cross_conformal` usa, para cada fold, os resíduos absolutos dos outros folds como
conjunto de calibração. É uma aproximação honesta para OOF espacial; não substitui a propagação
de erro de referência, alometria e amostragem.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def conformal_quantile(residuals: np.ndarray, coverage: float = 0.90) -> float:
    values = np.abs(np.asarray(residuals, dtype="float64"))
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return float("nan")
    return float(np.quantile(values, coverage))


def cross_conformal(
    predictions: pd.DataFrame,
    *,
    target_col: str = "agb_mg_ha",
    pred_col: str = "pred",
    fold_col: str = "fold",
    coverage: float = 0.90,
    group_cols: tuple[str, ...] = ("fitofisionomia_group", "biome", "source"),
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Adiciona lo/hi por fold e calcula cobertura e largura empíricas."""
    df = predictions.copy()
    if fold_col not in df.columns:
        raise KeyError(f"coluna de fold {fold_col!r} ausente")
    if pred_col not in df.columns or target_col not in df.columns:
        raise KeyError("predições precisam de pred e alvo")
    df["residual"] = df[pred_col] - df[target_col]
    df["lo"] = np.nan
    df["hi"] = np.nan
    df["conformal_q"] = np.nan

    by_fold = []
    for fold in sorted(df[fold_col].dropna().unique()):
        test = df[fold_col] == fold
        calib = ~test
        q = conformal_quantile(df.loc[calib, "residual"].to_numpy(), coverage)
        df.loc[test, "lo"] = df.loc[test, pred_col] - q
        df.loc[test, "hi"] = df.loc[test, pred_col] + q
        df.loc[test, "conformal_q"] = q
        y = df.loc[test, target_col].to_numpy(dtype="float64")
        lo = df.loc[test, "lo"].to_numpy(dtype="float64")
        hi = df.loc[test, "hi"].to_numpy(dtype="float64")
        inside = (y >= lo) & (y <= hi)
        by_fold.append({
            "fold": int(fold),
            "n": int(test.sum()),
            "q": q,
            "coverage": float(np.mean(inside)) if len(inside) else None,
            "width": float(np.mean(hi - lo)) if len(hi) else None,
        })

    y = df[target_col].to_numpy(dtype="float64")
    lo = df["lo"].to_numpy(dtype="float64")
    hi = df["hi"].to_numpy(dtype="float64")
    valid = np.isfinite(y) & np.isfinite(lo) & np.isfinite(hi)
    inside = (y >= lo) & (y <= hi)
    overall = {
        "coverage_nominal": coverage,
        "coverage": float(inside[valid].mean()) if valid.any() else None,
        "width": float(np.mean((hi - lo)[valid])) if valid.any() else None,
        "n": int(valid.sum()),
    }
    by_group = []
    for col in group_cols:
        if col not in df.columns:
            continue
        for value in sorted(df[col].dropna().astype(str).unique()):
            mask = valid & (df[col].astype(str) == value).to_numpy()
            if mask.sum() < 3:
                continue
            by_group.append({
                col: value,
                "n": int(mask.sum()),
                "coverage": float(inside[mask].mean()),
                "width": float(np.mean((hi - lo)[mask])),
            })
    summary = {
        "overall": overall,
        "by_fold": by_fold,
        "by_group": by_group,
        "note": "Cobertura empírica dos resíduos OOF; não inclui erro de referência/alometria.",
    }
    return df, summary
