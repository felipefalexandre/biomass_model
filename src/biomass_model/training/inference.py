"""Inferência com modelo campo-first salvo (bundle joblib)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..applicability import score_aoa
from .field import _metrics


def predict_field_model(
    model_path: str | Path,
    features: str | Path | pd.DataFrame,
    out: str | Path | None = None,
    *,
    target_col: str = "agb_mg_ha",
) -> dict[str, Any]:
    import joblib

    bundle = joblib.load(model_path)
    model = bundle["model"]
    feature_names = list(bundle["features"])
    levels = bundle.get("categorical_levels", {}) or {}
    df = pd.read_csv(features) if not isinstance(features, pd.DataFrame) else features.copy()
    if "feature_na" in df.columns:
        df = df[~df["feature_na"].astype(bool)].copy()
    for col, categories in levels.items():
        if col not in df.columns:
            continue
        values = df[col].fillna("unknown").astype(str)
        for category in categories:
            df[f"cat_{col}_{category}"] = (values == category).astype("float64")
    missing = [c for c in feature_names if c not in df.columns]
    if missing:
        raise KeyError(f"features ausentes para o modelo: {missing}")
    X = df[feature_names].to_numpy(dtype="float64")
    if not np.isfinite(X).all():
        raise ValueError("features de inferência contêm NaN/inf")
    pred = np.clip(model.predict(X), 0, None)
    aoa = bundle.get("aoa")
    aoa_distance = aoa_inside = None
    if aoa:
        aoa_distance, aoa_inside = score_aoa(aoa, X)

    cols = [c for c in ("observation_id", "site", "source", "lon", "lat", "biome",
                        "fitofisionomia", "fitofisionomia_group") if c in df.columns]
    result = df[cols].copy()
    result["pred"] = pred
    if aoa_distance is not None:
        result["aoa_distance"] = aoa_distance
        result["aoa_inside"] = aoa_inside
    if target_col in df.columns:
        result["observed"] = df[target_col].to_numpy(dtype="float64")
        result["residual"] = result["pred"] - result["observed"]
    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(out_path, index=False, encoding="utf-8")
    summary = {
        "model": str(model_path),
        "n": int(len(result)),
        "n_features": len(feature_names),
        "pred_mean": float(np.mean(pred)),
        "pred_min": float(np.min(pred)),
        "pred_max": float(np.max(pred)),
    }
    if aoa_inside is not None:
        summary["aoa_fraction"] = float(np.mean(aoa_inside))
        summary["aoa_threshold"] = float(aoa["threshold"])
    if target_col in df.columns:
        summary["metrics"] = _metrics(df[target_col].to_numpy(dtype="float64"), pred)
    if out:
        summary["out"] = str(out)
        Path(out).with_suffix(".json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return summary
