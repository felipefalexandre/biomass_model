"""Baseline de AGB com validacao por blocos espaciais (ADR-0006)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

METRICS = ("r2", "rmse", "mae", "bias")


def feature_columns(df: pd.DataFrame) -> list[str]:
    cols = [c for c in df.columns if c.startswith(("s2_", "s1_", "ls_", "era5_")) and not c.endswith("_valid")]
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
    if "box" in d:
        out["box"] = grouped["box"].first()
    for col in ("lon", "lat", "pixel_lon", "pixel_lat"):
        if col in d:
            out[col] = grouped[col].mean()
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


def run_field_baseline(
    csv_path: str | Path,
    out_dir: str | Path,
    *,
    block_deg: float = 1.0,
    n_splits: int = 5,
    n_estimators: int = 400,
    seed: int = 42,
) -> dict[str, Any]:
    """Baseline em sitios de campo; blocos espaciais de ~1 grau."""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import GroupKFold, KFold

    df = pd.read_csv(csv_path)
    df = df[~df["feature_na"].astype(bool)] if "feature_na" in df else df
    df = df[np.isfinite(df["agb_mg_ha"])].reset_index(drop=True)
    df["block_id"] = (np.floor(df["lon"] / block_deg).astype(int).astype(str) + "_"
                      + np.floor(df["lat"] / block_deg).astype(int).astype(str))

    feats = feature_columns(df)
    X = df[feats].to_numpy(dtype="float64")
    y = df["agb_mg_ha"].to_numpy(dtype="float64")
    groups = df["block_id"].to_numpy()
    n_groups = len(np.unique(groups))
    splitter = GroupKFold(n_splits=n_splits) if n_groups >= n_splits else KFold(
        n_splits=n_splits, shuffle=True, random_state=seed)

    oof = np.full(len(y), np.nan)
    per_fold = []
    for i, (train_idx, test_idx) in enumerate(splitter.split(X, y, groups)):
        model = RandomForestRegressor(n_estimators=n_estimators, min_samples_leaf=2,
                                      n_jobs=-1, random_state=seed)
        model.fit(X[train_idx], y[train_idx])
        pred = model.predict(X[test_idx])
        oof[test_idx] = pred
        fold = _metrics(y[test_idx], pred)
        fold["fold"] = i
        per_fold.append(fold)

    model = RandomForestRegressor(n_estimators=n_estimators, min_samples_leaf=2,
                                  n_jobs=-1, random_state=seed)
    model.fit(X, y)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    df_out = df[["site", "lon", "lat", "block_id"]].copy()
    df_out["agb_mg_ha"] = y
    df_out["pred"] = oof
    df_out.to_csv(out.with_suffix(".predictions.csv"), index=False)

    result = {
        "csv": str(csv_path),
        "n": int(len(df)),
        "groups": int(n_groups),
        "features": feats,
        "cv": {"overall": _metrics(y, oof), "per_fold": per_fold},
        "importance": sorted(zip(feats, (float(v) for v in model.feature_importances_)),
                             key=lambda kv: kv[1], reverse=True),
    }
    (out.with_suffix(".metrics.json")).write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    import joblib
    joblib.dump(model, out.with_suffix(".joblib"))
    return result


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
    group_col: str | None = None,
    log_target: bool = False,
) -> dict[str, Any]:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import GroupKFold

    df = pd.read_csv(csv_path)
    df = df[~df["feature_na"].astype(bool)] if "feature_na" in df else df
    df = df[np.isfinite(df["agbd"]) & (df["agbd"] >= 0) & (df["agbd"] <= max_agbd)]
    if cell_px:
        df = aggregate_cells(df, cell_px, min_shots=min_shots)
    if group_col:
        df = df.dropna(subset=[group_col])
    df = add_blocks(df, block_px=block_px).reset_index(drop=True)

    feats = feature_columns(df)
    X = df[feats].to_numpy(dtype="float64")
    y = df["agbd"].to_numpy(dtype="float64")
    y_fit = np.log1p(y) if log_target else y
    groups = (df[group_col] if group_col else df["block_id"]).to_numpy()
    if group_col:
        df["block_id"] = df[group_col].astype(str)

    folds = list(GroupKFold(n_splits=n_splits).split(X, y, groups))
    oof = np.full(len(y), np.nan)
    per_fold = []
    for i, (train_idx, test_idx) in enumerate(folds):
        model = RandomForestRegressor(
            n_estimators=n_estimators, min_samples_leaf=3, n_jobs=-1,
            random_state=seed, oob_score=False,
        )
        model.fit(X[train_idx], y_fit[train_idx])
        pred = model.predict(X[test_idx])
        if log_target:
            pred = np.clip(np.expm1(pred), 0, None)
        oof[test_idx] = pred
        fold = _metrics(y[test_idx], pred)
        fold["fold"] = i
        per_fold.append(fold)

    model = RandomForestRegressor(
        n_estimators=n_estimators, min_samples_leaf=3, n_jobs=-1, random_state=seed,
    )
    model.fit(X, y_fit)

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
        "log_target": bool(log_target),
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


def run_region_cv(
    csv_path: str | Path,
    out_dir: str | Path,
    *,
    calib_frac: float = 0.0,
    n_calib: int | None = None,
    calib_mode: str = "random",
    group_col: str = "box",
    cell_px: int | None = None,
    min_shots: int = 3,
    n_estimators: int = 400,
    seed: int = 42,
    max_agbd: float = 1000.0,
) -> dict[str, Any]:
    """Leave-one-region-out com calibracao local opcional.

    Para cada regiao retida, treina nas demais e em uma amostra da regiao alvo
    (calib_frac ou n_calib), testando no restante. Mede o custo/beneficio de
    poucos dados locais para adaptar o modelo.
    """
    from sklearn.ensemble import RandomForestRegressor

    df = pd.read_csv(csv_path)
    df = df[~df["feature_na"].astype(bool)] if "feature_na" in df else df
    df = df[np.isfinite(df["agbd"]) & (df["agbd"] >= 0) & (df["agbd"] <= max_agbd)]
    if cell_px:
        df = aggregate_cells(df, cell_px, min_shots=min_shots)
    feats = feature_columns(df)
    rng = np.random.default_rng(seed)

    oof = np.full(len(df), np.nan)
    per_box, calib_sizes = [], {}
    for box in sorted(df[group_col].unique()):
        target = df[group_col].to_numpy() == box
        idx_target = np.flatnonzero(target)
        k = n_calib if n_calib is not None else int(round(calib_frac * len(idx_target)))
        k = min(k, max(0, len(idx_target) - 30))
        if k and calib_mode == "center" and {"pixel_row", "pixel_col"} <= set(df.columns):
            sub = df.iloc[idx_target]
            cr = sub["pixel_row"].median(); cc = sub["pixel_col"].median()
            dist = (sub["pixel_row"] - cr) ** 2 + (sub["pixel_col"] - cc) ** 2
            calib = sub.index.to_numpy()[np.argsort(dist.to_numpy())[:k]]
        elif k and calib_mode == "south" and "pixel_lat" in df.columns:
            order = idx_target[np.argsort(df.iloc[idx_target]["pixel_lat"].to_numpy())]
            calib = order[:k]
        elif k:
            calib = rng.choice(idx_target, size=k, replace=False)
        else:
            calib = np.array([], dtype=int)
        train_idx = np.flatnonzero(~target)
        train_idx = np.concatenate([train_idx, calib])
        test_idx = np.setdiff1d(idx_target, calib)
        model = RandomForestRegressor(n_estimators=n_estimators, min_samples_leaf=3,
                                      n_jobs=-1, random_state=seed)
        model.fit(df.iloc[train_idx][feats].to_numpy(dtype="float64"),
                  df.iloc[train_idx]["agbd"].to_numpy(dtype="float64"))
        pred = model.predict(df.iloc[test_idx][feats].to_numpy(dtype="float64"))
        oof[test_idx] = pred
        m = _metrics(df.iloc[test_idx]["agbd"].to_numpy(dtype="float64"), pred)
        m["box"] = box
        m["n_calib"] = int(k)
        per_box.append(m)
        calib_sizes[box] = int(k)

    mask = np.isfinite(oof)
    overall = _metrics(df.loc[mask, "agbd"].to_numpy(dtype="float64"), oof[mask])
    result = {
        "csv": str(csv_path), "n": int(mask.sum()), "features": feats,
        "calib_frac": calib_frac, "n_calib": n_calib, "calib_mode": calib_mode,
        "cell_px": cell_px,
        "calib_sizes": calib_sizes,
        "overall": overall, "per_box": per_box,
    }
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out.with_suffix(".metrics.json")).write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    loc_cols = [c for c in ("lon", "lat", "pixel_lon", "pixel_lat", group_col, "agbd") if c in df.columns]
    pred_cols = df.loc[mask, loc_cols].copy()
    pred_cols["pred"] = oof[mask]
    pred_cols.to_csv(out.with_suffix(".predictions.csv"), index=False)
    return result


def run_region_conformal(
    csv_path: str | Path,
    out_dir: str | Path,
    *,
    calib_frac: float = 0.1,
    conformal_frac: float = 0.1,
    coverage: float = 0.9,
    group_col: str = "box",
    cell_px: int | None = None,
    min_shots: int = 3,
    n_estimators: int = 400,
    seed: int = 42,
    max_agbd: float = 1000.0,
) -> dict[str, Any]:
    """Leave-one-region-out com calibracao e intervalo conformal (split).

    A regiao retida e dividida em calibracao (treino), conformal (residuos) e teste.
    Reporta cobertura e largura media do intervalo por regiao.
    """
    from sklearn.ensemble import RandomForestRegressor

    df = pd.read_csv(csv_path)
    df = df[~df["feature_na"].astype(bool)] if "feature_na" in df else df
    df = df[np.isfinite(df["agbd"]) & (df["agbd"] >= 0) & (df["agbd"] <= max_agbd)]
    if cell_px:
        df = aggregate_cells(df, cell_px, min_shots=min_shots)
    feats = feature_columns(df)
    rng = np.random.default_rng(seed)

    rows, per_box = [], []
    for box in sorted(df[group_col].unique()):
        target = df[group_col].to_numpy() == box
        idx_target = np.flatnonzero(target)
        n_cal = int(round(calib_frac * len(idx_target)))
        n_conf = int(round(conformal_frac * len(idx_target)))
        n_cal = min(n_cal, max(0, len(idx_target) - n_conf - 30))
        shuffled = rng.permutation(idx_target)
        calib = shuffled[:n_cal]
        conf = shuffled[n_cal:n_cal + n_conf]
        test = shuffled[n_cal + n_conf:]
        train_idx = np.concatenate([np.flatnonzero(~target), calib])

        model = RandomForestRegressor(n_estimators=n_estimators, min_samples_leaf=3,
                                      n_jobs=-1, random_state=seed)
        model.fit(df.iloc[train_idx][feats].to_numpy(dtype="float64"),
                  df.iloc[train_idx]["agbd"].to_numpy(dtype="float64"))
        pred_conf = model.predict(df.iloc[conf][feats].to_numpy(dtype="float64"))
        resid = np.abs(df.iloc[conf]["agbd"].to_numpy(dtype="float64") - pred_conf)
        q = float(np.quantile(resid, coverage)) if len(resid) else float("nan")
        pred = model.predict(df.iloc[test][feats].to_numpy(dtype="float64"))
        y = df.iloc[test]["agbd"].to_numpy(dtype="float64")
        inside = np.abs(y - pred) <= q
        m = _metrics(y, pred)
        m.update({"box": box, "n_calib": int(len(calib)), "n_conformal": int(len(conf)),
                  "q90": q, "coverage90": float(inside.mean()),
                  "width90": float(2 * q)})
        per_box.append(m)
        loc_cols = [c for c in ("lon", "lat", "pixel_lon", "pixel_lat", group_col, "agbd") if c in df.columns]
        block = df.iloc[test][loc_cols].copy()
        block["pred"] = pred
        block["lo"] = pred - q
        block["hi"] = pred + q
        rows.append(block)

    preds = pd.concat(rows, ignore_index=True)
    all_y = preds["agbd"].to_numpy(dtype="float64")
    all_pred = preds["pred"].to_numpy(dtype="float64")
    all_inside = (all_y >= preds["lo"].to_numpy()) & (all_y <= preds["hi"].to_numpy())
    overall = _metrics(all_y, all_pred)
    overall.update({"coverage90": float(all_inside.mean()),
                    "width90": float((preds["hi"] - preds["lo"]).mean())})
    result = {
        "csv": str(csv_path), "n": int(len(preds)), "features": feats,
        "calib_frac": calib_frac, "conformal_frac": conformal_frac,
        "cell_px": cell_px, "overall": overall, "per_box": per_box,
    }
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out.with_suffix(".metrics.json")).write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    preds.to_csv(out.with_suffix(".predictions.csv"), index=False)
    return result
