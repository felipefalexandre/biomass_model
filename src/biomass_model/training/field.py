"""Treinamento com referência de campo e validação espacial com buffer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..observation_features import FEATURE_PREFIXES
from ..validation.spatial import assign_spatial_blocks, spatial_block_folds


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    y_true = np.asarray(y_true, dtype="float64")
    y_pred = np.asarray(y_pred, dtype="float64")
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true, y_pred = y_true[mask], y_pred[mask]
    if len(y_true) == 0:
        return {"n": 0}
    bias = float(np.mean(y_pred - y_true))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    medae = float(np.median(np.abs(y_pred - y_true)))
    mean_y = float(np.mean(y_true))
    r2 = float(r2_score(y_true, y_pred)) if len(y_true) >= 2 else None
    r2_after_bias = float(r2_score(y_true, y_pred - bias)) if len(y_true) >= 2 else None
    return {
        "n": int(len(y_true)),
        "r2": r2,
        "rmse": rmse,
        "mae": mae,
        "medae": medae,
        "bias": bias,
        "rmse_relative": rmse / mean_y if mean_y > 0 else None,
        "mae_relative": mae / mean_y if mean_y > 0 else None,
        "r2_after_bias": r2_after_bias,
    }


def _feature_columns(df: pd.DataFrame) -> list[str]:
    cols = [c for c in df.columns if c.startswith(FEATURE_PREFIXES) and not c.endswith("_valid")]
    cols += [c for c in ("elev", "slope", "aspect") if c in df.columns]
    cols += [c for c in df.columns if c.startswith("cat_")]
    return cols


def _encode_categoricals(
    df: pd.DataFrame,
    columns: tuple[str, ...] = ("fitofisionomia_group", "biome"),
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    out = df.copy()
    levels: dict[str, list[str]] = {}
    for col in columns:
        if col not in out.columns:
            continue
        values = out[col].fillna("unknown").astype(str)
        categories = sorted(values.unique())
        levels[col] = categories
        for category in categories:
            out[f"cat_{col}_{category}"] = (values == category).astype("float64")
    return out, levels


def _baseline_predictions(
    train: pd.DataFrame,
    test: pd.DataFrame,
    target: str,
    group_cols: tuple[str, ...] = ("fitofisionomia_group", "biome"),
) -> np.ndarray:
    global_mean = float(train[target].mean())
    group_col = next((c for c in group_cols if c in train.columns and c in test.columns), None)
    if group_col is None:
        return np.full(len(test), global_mean)
    means = train.groupby(group_col)[target].mean()
    pred = test[group_col].map(means).astype("float64")
    return pred.fillna(global_mean).to_numpy()


def _group_folds(
    df: pd.DataFrame,
    X: np.ndarray,
    y: np.ndarray,
    *,
    block_size_m: float,
    buffer_m: float,
    max_folds: int,
) -> list[dict[str, Any]]:
    from sklearn.model_selection import GroupKFold

    blocks = assign_spatial_blocks(df, block_size_m=block_size_m)["block_id"]
    n_groups = int(blocks.nunique())
    if n_groups < 2:
        raise ValueError("apenas um bloco espacial; validação honesta impossível")
    splitter = GroupKFold(n_splits=min(max_folds, n_groups))
    folds = []
    for i, (train_idx, test_idx) in enumerate(splitter.split(X, y, groups=blocks)):
        folds.append({
            "fold": i, "block_id": "groupkfold", "train_idx": train_idx,
            "test_idx": test_idx, "n_train": len(train_idx), "n_test": len(test_idx),
            "block_size_m": block_size_m, "buffer_m": buffer_m,
        })
    return folds


def train_field_model(
    csv_path: str | Path,
    out_dir: str | Path,
    *,
    target: str = "agb_mg_ha",
    block_size_m: float = 100_000.0,
    buffer_m: float = 25_000.0,
    n_estimators: int = 400,
    min_samples_leaf: int = 3,
    min_test: int = 3,
    max_folds: int = 50,
    seed: int = 42,
    use_categoricals: bool = True,
    domain_classes: tuple[int, ...] | None = (3, 4),
) -> dict[str, Any]:
    """Treina RandomForest campo-first com validação espacial em blocos e buffer."""
    from sklearn.ensemble import RandomForestRegressor

    df = pd.read_csv(csv_path).reset_index(drop=True)
    if target not in df.columns and "agbd" in df.columns:
        target = "agbd"
    if target not in df.columns:
        raise KeyError(f"alvo {target!r} ausente")
    if "feature_na" in df.columns:
        dropped_na = int(df["feature_na"].astype(bool).sum())
        df = df[~df["feature_na"].astype(bool)].reset_index(drop=True)
    else:
        dropped_na = 0
    df = df[np.isfinite(df[target]) & (df[target] >= 0)].reset_index(drop=True)
    dropped_domain = 0
    if domain_classes and "mapbiomas_class" in df.columns:
        keep = df["mapbiomas_class"].isin(list(domain_classes))
        dropped_domain = int((~keep).sum())
        df = df[keep].reset_index(drop=True)
    if len(df) < 10:
        raise ValueError("amostra insuficiente para treinamento campo-first")

    if use_categoricals:
        df, categorical_levels = _encode_categoricals(df)
    else:
        categorical_levels = {}
    features = _feature_columns(df)
    if not features:
        raise ValueError("nenhuma feature disponível na tabela")
    X = df[features].to_numpy(dtype="float64")
    y = df[target].to_numpy(dtype="float64")
    if not np.isfinite(X).all():
        raise ValueError("features contêm NaN/inf; remova via feature_na ou impute explicitamente")

    cv_warning = None
    try:
        folds = spatial_block_folds(
            df, block_size_m=block_size_m, buffer_m=buffer_m, min_test=min_test,
        )
        cv_mode = "spatial_block_buffer"
        coverage = sum(f["n_test"] for f in folds) / max(len(df), 1)
        if coverage < 0.3 and min_test > 1:
            folds = spatial_block_folds(
                df, block_size_m=block_size_m, buffer_m=buffer_m, min_test=1,
            )
            cv_mode = "spatial_block_buffer_loo"
            cv_warning = f"min_test reduzido para 1 (cobertura inicial {coverage:.2f})"
        n_before = len(folds)
        if n_before > max_folds:
            folds = _group_folds(
                df, X, y, block_size_m=block_size_m, buffer_m=buffer_m,
                max_folds=max_folds,
            )
            cv_mode = "groupkfold_no_buffer"
            msg = f"{n_before} folds excedem max_folds={max_folds}"
            cv_warning = f"{cv_warning}; {msg}" if cv_warning else msg
    except ValueError as exc:
        folds = _group_folds(
            df, X, y, block_size_m=block_size_m, buffer_m=buffer_m,
            max_folds=max_folds,
        )
        cv_mode = "groupkfold_no_buffer"
        cv_warning = str(exc)

    oof = np.full(len(df), np.nan)
    baseline_oof = np.full(len(df), np.nan)
    fold_rows = []
    for fold in folds:
        train_idx = np.asarray(fold["train_idx"], dtype=int)
        test_idx = np.asarray(fold["test_idx"], dtype=int)
        model = RandomForestRegressor(
            n_estimators=n_estimators, min_samples_leaf=min_samples_leaf,
            n_jobs=-1, random_state=seed,
        )
        model.fit(X[train_idx], y[train_idx])
        pred = model.predict(X[test_idx])
        oof[test_idx] = pred
        baseline_oof[test_idx] = _baseline_predictions(
            df.iloc[train_idx], df.iloc[test_idx], target,
        )
        metrics = _metrics(y[test_idx], pred)
        metrics.update({"fold": int(fold["fold"]), "block_id": str(fold["block_id"]),
                        "n_train": int(fold["n_train"]), "n_test": int(fold["n_test"])})
        fold_rows.append(metrics)

    mask = np.isfinite(oof)
    overall = _metrics(y[mask], oof[mask])
    baseline = _metrics(y[mask], baseline_oof[mask])
    by_group = []
    for col in ("fitofisionomia_group", "biome", "source"):
        if col not in df.columns:
            continue
        for value in sorted(df[col].dropna().astype(str).unique()):
            sub = mask & (df[col].astype(str) == value).to_numpy()
            if sub.sum() >= 3:
                row = _metrics(y[sub], oof[sub])
                row[col] = value
                by_group.append(row)

    final_model = RandomForestRegressor(
        n_estimators=n_estimators, min_samples_leaf=min_samples_leaf,
        n_jobs=-1, random_state=seed,
    )
    final_model.fit(X, y)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    import joblib

    bundle = {
        "model": final_model,
        "features": features,
        "categorical_levels": categorical_levels,
        "target": target,
        "metadata": {
            "csv": str(csv_path),
            "cv_mode": cv_mode,
            "block_size_m": block_size_m,
            "buffer_m": buffer_m,
            "max_folds": max_folds,
            "n": int(len(df)),
            "n_features": len(features),
            "dropped_feature_na": dropped_na,
            "dropped_outside_domain": dropped_domain,
            "domain_classes": list(domain_classes) if domain_classes else None,
            "field_first": True,
        },
    }
    joblib.dump(bundle, out.with_suffix(".joblib"))

    pred = df[["observation_id", "source", "lon", "lat", target,
               "fitofisionomia_group", "biome"]].copy()
    pred["pred"] = oof
    pred["baseline"] = baseline_oof
    pred["residual"] = pred["pred"] - pred[target]
    pred.to_csv(out.with_suffix(".predictions.csv"), index=False, encoding="utf-8")

    result = {
        "csv": str(csv_path),
        "target": target,
        "n": int(len(df)),
        "features": features,
        "n_features": len(features),
        "dropped_feature_na": dropped_na,
        "dropped_outside_domain": dropped_domain,
        "domain_classes": list(domain_classes) if domain_classes else None,
        "cv_mode": cv_mode,
        "cv_warning": cv_warning,
        "block_size_m": block_size_m,
        "buffer_m": buffer_m,
        "max_folds": max_folds,
        "overall": overall,
        "baseline": baseline,
        "by_fold": fold_rows,
        "by_group": by_group,
        "importance": sorted(
            zip(features, (float(v) for v in final_model.feature_importances_)),
            key=lambda kv: kv[1], reverse=True,
        ),
        "limitations": [
            "Validação espacial por blocos com buffer; não substitui validação de campo independente.",
            "Campo disponível pode ser antigo, esparso e com coordenadas imprecisas.",
            "Modelo não inclui erro de referência nem alometria na incerteza.",
        ],
    }
    out.with_suffix(".metrics.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return result
