"""Blocos espaciais com buffer para reduzir vazamento por autocorrelação."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pyproj import Transformer


def assign_spatial_blocks(
    df: pd.DataFrame,
    *,
    block_size_m: float = 100_000.0,
    x_col: str = "lon",
    y_col: str = "lat",
    crs_in: str = "EPSG:4326",
    crs_metric: str = "EPSG:5880",
) -> pd.DataFrame:
    out = df.copy()
    transformer = Transformer.from_crs(crs_in, crs_metric, always_xy=True)
    x, y = transformer.transform(out[x_col].to_numpy(), out[y_col].to_numpy())
    out["_x_m"] = np.asarray(x, dtype="float64")
    out["_y_m"] = np.asarray(y, dtype="float64")
    bx = np.floor(out["_x_m"] / block_size_m).astype("int64")
    by = np.floor(out["_y_m"] / block_size_m).astype("int64")
    out["block_x"] = bx
    out["block_y"] = by
    out["block_id"] = bx.astype(str) + "_" + by.astype(str)
    return out


def spatial_block_folds(
    df: pd.DataFrame,
    *,
    block_size_m: float = 100_000.0,
    buffer_m: float = 25_000.0,
    x_col: str = "lon",
    y_col: str = "lat",
    crs_in: str = "EPSG:4326",
    crs_metric: str = "EPSG:5880",
    min_test: int = 3,
) -> list[dict[str, Any]]:
    """Folds leave-one-block-out; exclui do treino pontos dentro do buffer do bloco teste."""
    data = assign_spatial_blocks(
        df, block_size_m=block_size_m, x_col=x_col, y_col=y_col,
        crs_in=crs_in, crs_metric=crs_metric,
    )
    folds: list[dict[str, Any]] = []
    for block_id, group in data.groupby("block_id", sort=True):
        test_idx = group.index.to_numpy()
        if len(test_idx) < min_test:
            continue
        xmin, xmax = group["_x_m"].min() - buffer_m, group["_x_m"].max() + buffer_m
        ymin, ymax = group["_y_m"].min() - buffer_m, group["_y_m"].max() + buffer_m
        in_buffer = (
            (data["_x_m"] >= xmin) & (data["_x_m"] <= xmax)
            & (data["_y_m"] >= ymin) & (data["_y_m"] <= ymax)
        )
        train_idx = data.index[~in_buffer].to_numpy()
        if len(train_idx) == 0:
            continue
        folds.append({
            "fold": len(folds),
            "block_id": block_id,
            "train_idx": train_idx,
            "test_idx": test_idx,
            "n_train": int(len(train_idx)),
            "n_test": int(len(test_idx)),
            "block_size_m": block_size_m,
            "buffer_m": buffer_m,
        })
    if not folds:
        raise ValueError("nenhum bloco com amostra suficiente para validação espacial")
    return folds
