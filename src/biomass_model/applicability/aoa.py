"""AOA por distância ao treino em features padronizadas (Meyer & Pebesma, 2021)."""

from __future__ import annotations

from typing import Any

import numpy as np


def fit_aoa(X: np.ndarray, *, quantile: float = 0.95) -> dict[str, Any]:
    from sklearn.neighbors import NearestNeighbors

    values = np.asarray(X, dtype="float64")
    mean = np.nanmean(values, axis=0)
    sd = np.nanstd(values, axis=0)
    sd[~np.isfinite(sd) | (sd == 0)] = 1.0
    Z = (values - mean) / sd
    nn = NearestNeighbors(n_neighbors=2).fit(Z)
    distances = nn.kneighbors(Z, return_distance=True)[0][:, 1]
    threshold = float(np.quantile(distances, quantile))
    return {
        "mean": mean,
        "sd": sd,
        "threshold": threshold,
        "quantile": quantile,
        "reference": Z,
        "n_reference": int(len(Z)),
    }


def score_aoa(aoa: dict[str, Any], X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    from sklearn.neighbors import NearestNeighbors

    values = np.asarray(X, dtype="float64")
    Z = (values - aoa["mean"]) / aoa["sd"]
    nn = NearestNeighbors(n_neighbors=1).fit(aoa["reference"])
    distances = nn.kneighbors(Z, return_distance=True)[0][:, 0]
    return distances, distances <= float(aoa["threshold"])
