import numpy as np
import pandas as pd
from rasterio.transform import from_origin

from biomass_model.features import snap_to_grid
from biomass_model.modeling import add_blocks, feature_columns

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
