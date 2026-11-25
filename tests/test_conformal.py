import numpy as np
import pandas as pd

from biomass_model.uncertainty.conformal import conformal_quantile, cross_conformal


def test_conformal_quantile():
    assert np.isclose(conformal_quantile([1, -2, 3], 0.90), np.quantile([1, 2, 3], 0.90))


def test_cross_conformal_adds_intervals_and_coverage():
    rows = []
    for fold in (0, 1):
        for i in range(5):
            y = 10.0 + i
            pred = y + (1.0 if i % 2 else -1.0)
            rows.append({"fold": fold, "agb_mg_ha": y, "pred": pred,
                         "fitofisionomia_group": "savanna", "biome": "Cerrado"})
    df, summary = cross_conformal(pd.DataFrame(rows), coverage=0.8)
    assert {"lo", "hi", "conformal_q"} <= set(df.columns)
    assert summary["overall"]["n"] == 10
    assert 0 <= summary["overall"]["coverage"] <= 1
    assert summary["overall"]["width"] >= 0
