"""Baseline de AGB com validacao por blocos espaciais (ADR-0006)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

METRICS = ("r2", "rmse", "mae", "bias")


def feature_columns(df: pd.DataFrame) -> list[str]:
    cols = [c for c in df.columns if c.startswith(("s2_", "era5_"))]
    cols += [c for c in ("elev", "slope", "aspect") if c in df.columns]
    return cols


def add_blocks(df: pd.DataFrame, block_px: int = 167) -> pd.DataFrame:
    """Blocos de ~5 km (167 px de 30 m) para o CV espacial."""
    out = df.copy()
    out["block_row"] = out["pixel_row"] // block_px
    out["block_col"] = out["pixel_col"] // block_px
    out["block_id"] = out["block_row"].astype(str) + "_" + out["block_col"].astype(str)
    return out


def aggregate_cells(df: pd.DataFrame, cell_px: int, min_shots: int = 3) -> pd.DataFrame:
    """Agrega footprints em celulas (ex.: 33 px ~ 1 km); media das features e do alvo."""
    feats = feature_columns(df)
    d = df.copy()
    d["cell_row"] = d["pixel_row"] // cell_px
    d["cell_col"] = d["pixel_col"] // cell_px
    grouped = d.groupby(["cell_row", "cell_col"])
    out = grouped[feats].mean()
    out["agbd"] = grouped["agbd"].mean()
    out["n_shots"] = grouped.size()
    out["mapbiomas_class"] = grouped["mapbiomas_class"].agg(lambda s: int(s.mode().iat[0]))
    if "degrade_zero" in d:
        out["degrade_zero"] = grouped["degrade_zero"].mean() >= 0.5
    out = out[out["n_shots"] >= min_shots].reset_index()
    out["pixel_row"] = out["cell_row"] * cell_px
    out["pixel_col"] = out["cell_col"] * cell_px
    return out


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    return {
        "r2": float(r2_score(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "bias": float(np.mean(y_pred - y_true)),
        "n": int(len(y_true)),
    }


def run_baseline(
    csv_path: str | Path,
    out_dir: str | Path,
    *,
    n_splits: int = 5,
    block_px: int = 167,
    n_estimators: int = 400,
    seed: int = 42,
    max_agbd: float = 1000.0,
    cell_px: int | None = None,
    min_shots: int = 3,
) -> dict[str, Any]:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import GroupKFold

    df = pd.read_csv(csv_path)
    df = df[~df["feature_na"].astype(bool)] if "feature_na" in df else df
    df = df[np.isfinite(df["agbd"]) & (df["agbd"] >= 0) & (df["agbd"] <= max_agbd)]
    if cell_px:
        df = aggregate_cells(df, cell_px, min_shots=min_shots)
    df = add_blocks(df, block_px=block_px).reset_index(drop=True)

    feats = feature_columns(df)
    X = df[feats].to_numpy(dtype="float64")
    y = df["agbd"].to_numpy(dtype="float64")
    groups = df["block_id"].to_numpy()

    folds = list(GroupKFold(n_splits=n_splits).split(X, y, groups))
    oof = np.full(len(y), np.nan)
    per_fold = []
    for i, (train_idx, test_idx) in enumerate(folds):
        model = RandomForestRegressor(
            n_estimators=n_estimators, min_samples_leaf=3, n_jobs=-1,
            random_state=seed, oob_score=False,
        )
        model.fit(X[train_idx], y[train_idx])
        pred = model.predict(X[test_idx])
        oof[test_idx] = pred
        fold = _metrics(y[test_idx], pred)
        fold["fold"] = i
        per_fold.append(fold)

    model = RandomForestRegressor(
        n_estimators=n_estimators, min_samples_leaf=3, n_jobs=-1, random_state=seed,
    )
    model.fit(X, y)

    overall = _metrics(y, oof)
    by_class = {
        int(k): _metrics(y[df["mapbiomas_class"].to_numpy() == k], oof[df["mapbiomas_class"].to_numpy() == k])
        for k in sorted(df["mapbiomas_class"].unique())
    }
    dz = df["degrade_zero"].to_numpy(dtype=bool) if "degrade_zero" in df else np.ones(len(df), dtype=bool)
    strict = _metrics(y[dz], oof[dz])

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    keep_cols = [c for c in ("granule", "granule_time", "pixel_row", "pixel_col", "block_id",
                             "mapbiomas_class", "degrade_zero", "n_shots", "agbd") if c in df]
    df_out = df[keep_cols].copy()
    df_out["pred"] = oof
    df_out.to_csv(out.with_suffix(".predictions.csv"), index=False)

    result = {
        "csv": str(csv_path),
        "n": int(len(df)),
        "scale_px": int(cell_px) if cell_px else 1,
        "features": feats,
        "blocks": int(df["block_id"].nunique()),
        "cv": {"overall": overall, "per_fold": per_fold, "degrade_zero": strict},
        "by_class": by_class,
        "importance": sorted(
            zip(feats, (float(v) for v in model.feature_importances_)),
            key=lambda kv: kv[1], reverse=True,
        ),
    }
    (out.with_suffix(".metrics.json")).write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    import joblib
    joblib.dump(model, out.with_suffix(".joblib"))
    return result
