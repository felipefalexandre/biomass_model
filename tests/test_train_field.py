import json

import numpy as np
import pandas as pd

from biomass_model.training.field import train_field_model


def _feature_table():
    rng = np.random.default_rng(42)
    rows = []
    centers = [(-50.0, -15.0), (-47.0, -15.0), (-44.0, -15.0)]
    for block, (lon0, lat0) in enumerate(centers):
        for i in range(10):
            lon = lon0 + rng.normal(0, 0.03)
            lat = lat0 + rng.normal(0, 0.03)
            ndvi = 0.5 + 0.1 * block + rng.normal(0, 0.01)
            elev = 500 + 50 * block + rng.normal(0, 5)
            agb = 10 + 100 * ndvi + 0.02 * elev + rng.normal(0, 1)
            rows.append({
                "observation_id": f"test:{block}:{i}",
                "source": "test",
                "lon": lon,
                "lat": lat,
                "agb_mg_ha": agb,
                "ls_ndvi": ndvi,
                "elev": elev,
                "fitofisionomia_group": "savanna",
                "biome": "Cerrado",
                "feature_na": False,
            })
    return pd.DataFrame(rows)


def test_train_field_model_spatial_buffer(tmp_path):
    csv = tmp_path / "features.csv"
    _feature_table().to_csv(csv, index=False)
    out_dir = tmp_path / "model"
    result = train_field_model(
        csv, out_dir, block_size_m=100_000, buffer_m=20_000,
        n_estimators=50, min_samples_leaf=1, min_test=3, use_categoricals=False,
    )
    assert result["n"] == 30
    assert result["cv_mode"] in {"spatial_block_buffer", "groupkfold_no_buffer"}
    assert "ls_ndvi" in result["features"]
    assert result["overall"]["n"] == 30
    assert "uncertainty" in result
    assert result["uncertainty"]["overall"]["n"] == 30
    assert np.isfinite(result["overall"]["rmse"])
    assert (tmp_path / "model.joblib").exists()
    assert (tmp_path / "model.metrics.json").exists()
    predictions = pd.read_csv(tmp_path / "model.predictions.csv")
    assert len(predictions) == 30
    assert "pred" in predictions.columns
    payload = json.loads((tmp_path / "model.metrics.json").read_text(encoding="utf-8"))
    assert payload["target"] == "agb_mg_ha"


def test_train_field_model_ridge(tmp_path):
    csv = tmp_path / "features.csv"
    _feature_table().to_csv(csv, index=False)
    result = train_field_model(
        csv, tmp_path / "ridge", block_size_m=100_000, buffer_m=20_000,
        n_estimators=50, min_samples_leaf=1, min_test=3,
        use_categoricals=False, algorithm="ridge",
    )
    assert result["algorithm"] == "ridge"
    assert result["overall"]["n"] == 30
    assert (tmp_path / "ridge.joblib").exists()
