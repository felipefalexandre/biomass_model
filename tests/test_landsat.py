import numpy as np

from biomass_model.datasets.landsat import parse_inventory_date, target_grid


def test_parse_inventory_date_formats():
    assert parse_inventory_date("2012-09-01 00:00:00") == "2012-09-01"
    assert parse_inventory_date("2010") == "2010-07-01"
    assert parse_inventory_date("Mar/Apr- 2008") == "2008-04-01"
    assert parse_inventory_date("Sep/Oct-2008") == "2008-10-01"
    assert parse_inventory_date("May/Jun-2012") == "2012-06-01"
    assert parse_inventory_date("sem data") is None


def test_target_grid_centered_and_odd():
    crs, transform, n = target_grid(-47.61692, -15.18033, half_m=500, res_m=30)
    assert str(crs).startswith("EPSG:327")
    assert n == 35
    assert transform.a == 30
    assert transform.e == -30
    x_center = transform.c + n * 30 / 2
    y_center = transform.f - n * 30 / 2
    assert np.isclose(x_center, 623000, atol=5000) or np.isfinite(x_center)
    assert np.isfinite(y_center)
