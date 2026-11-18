from datetime import datetime

import numpy as np

from biomass_model.datasets.dem import tile_name, tiles_for_bbox
from biomass_model.datasets.gedi import parse_granule_time, quality_mask


def test_tile_name_hemispheres():
    assert tile_name(-7, -61).endswith("S07_00_W061_00_DEM/Copernicus_DSM_COG_10_S07_00_W061_00_DEM.tif")
    assert "N00_00_E010_00_DEM" in tile_name(0, 10)


def test_tiles_for_bbox():
    tiles = tiles_for_bbox(-60.55, -7.0, -60.35, -6.8)
    assert len(tiles) == 1
    assert "S07_00_W061_00_DEM" in tiles[0]


def test_parse_granule_time():
    dt = parse_granule_time("GEDI04_A_2019124145322_O02217_04_T04152_02_002_02_V002")
    assert dt == datetime(2019, 5, 4, 14, 53, 22)


def test_quality_mask():
    agbd = np.array([100.0, -9999.0, 50.0, 20.0, 30.0])
    l2 = np.array([1, 1, 0, 1, 1], dtype="uint8")
    l4 = np.array([1, 1, 1, 0, 1], dtype="uint8")
    sens = np.array([0.95, 0.95, 0.95, 0.95, 0.5])
    mask = quality_mask(agbd, l2, l4, sens)
    assert mask.tolist() == [True, False, False, False, False]
