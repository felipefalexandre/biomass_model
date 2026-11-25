import pandas as pd

from biomass_model.validation.spatial import assign_spatial_blocks, spatial_block_folds


def _points():
    rows = []
    for i, (lon, lat) in enumerate([
        (-50.0, -15.0), (-49.9, -15.0), (-49.8, -15.0),
        (-47.0, -15.0), (-46.9, -15.0), (-46.8, -15.0),
        (-44.0, -15.0), (-43.9, -15.0), (-43.8, -15.0),
    ]):
        rows.append({"id": i, "lon": lon, "lat": lat})
    return pd.DataFrame(rows)


def test_assign_spatial_blocks_adds_ids():
    out = assign_spatial_blocks(_points(), block_size_m=100_000)
    assert {"block_x", "block_y", "block_id", "_x_m", "_y_m"} <= set(out.columns)
    assert out["block_id"].nunique() >= 2


def test_spatial_block_folds_remove_buffer():
    folds = spatial_block_folds(_points(), block_size_m=100_000, buffer_m=25_000, min_test=3)
    assert len(folds) >= 2
    for fold in folds:
        assert fold["n_train"] > 0
        assert fold["n_test"] >= 3
        assert not set(fold["train_idx"]) & set(fold["test_idx"])
