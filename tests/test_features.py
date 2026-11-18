import numpy as np
import pandas as pd
from rasterio.transform import from_origin

from biomass_model.features import snap_to_grid
from biomass_model.modeling import add_blocks, aggregate_cells, feature_columns

TRANSFORM = from_origin(-74.02073025380652, 5.405791885246045,
                        0.00026949458523585647, 0.00026949458523585647)


def test_snap_to_grid_returns_pixel_center():
    rows, cols, lon, lat = snap_to_grid(np.array([-60.45]), np.array([-6.90]), TRANSFORM)
    assert rows[0] >= 0 and cols[0] >= 0
    assert abs(lon[0] - (-60.45)) < 0.001
    assert abs(lat[0] - (-6.90)) < 0.001


def test_feature_columns_excludes_identifiers_and_target():
    df = pd.DataFrame({"agbd": [1], "s2_ndvi": [0.8], "era5_t2m_c": [25],
                       "elev": [100], "slope": [2], "aspect": [90], "shot_number": [1]})
    cols = feature_columns(df)
    assert "agbd" not in cols and "shot_number" not in cols
    assert {"s2_ndvi", "era5_t2m_c", "elev", "slope", "aspect"} <= set(cols)


def test_add_blocks_groups_nearby_pixels():
    df = pd.DataFrame({"pixel_row": [0, 5, 200], "pixel_col": [0, 5, 200]})
    out = add_blocks(df, block_px=167)
    assert out.loc[0, "block_id"] == out.loc[1, "block_id"]
    assert out.loc[2, "block_id"] != out.loc[0, "block_id"]


def test_aggregate_cells_averages_and_filters():
    df = pd.DataFrame({
        "pixel_row": [0, 1, 2, 200], "pixel_col": [0, 1, 2, 200],
        "s2_ndvi": [0.8, 0.9, 0.7, 0.6], "elev": [1.0, 2.0, 3.0, 4.0],
        "agbd": [10.0, 20.0, 30.0, 40.0], "mapbiomas_class": [3, 3, 3, 4],
        "degrade_zero": [True, True, False, True], "feature_na": [False] * 4,
    })
    out = aggregate_cells(df, cell_px=33, min_shots=2)
    assert len(out) == 1
    assert out.loc[0, "n_shots"] == 3
    assert abs(out.loc[0, "agbd"] - 20.0) < 1e-9
    assert out.loc[0, "mapbiomas_class"] == 3

