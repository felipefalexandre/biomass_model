import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Point

from biomass_model.observation_features import build_observation_features


def _write_raster(path, values, names=None):
    values = np.asarray(values, dtype="float32")
    if values.ndim == 2:
        values = values[None, :, :]
    profile = dict(
        driver="GTiff", width=values.shape[2], height=values.shape[1],
        count=values.shape[0], dtype="float32", crs="EPSG:4326",
        transform=from_origin(-50.0, -9.9, 0.01, 0.01), nodata=np.nan,
    )
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(values)
        for i, name in enumerate(names or [f"band{i}" for i in range(1, len(values) + 1)], 1):
            dst.set_band_description(i, name)


def _observation(lon, lat, agb=20.0):
    return pd.DataFrame([{
        "observation_id": "test:1",
        "source": "test",
        "source_version": "1",
        "observation_type": "field",
        "reference_date": "2012-09-01",
        "geometry_wkt": Point(lon, lat).wkt,
        "crs": "EPSG:4326",
        "lon": lon,
        "lat": lat,
        "location_accuracy_m": 10,
        "support_area_ha": 1.0,
        "biome": "Cerrado",
        "fitofisionomia": "Cerrado sensu stricto",
        "fitofisionomia_group": "savanna",
        "mapbiomas_class": 4,
        "agb_mg_ha": agb,
        "agb_uncertainty_mg_ha": 2.0,
        "uncertainty_type": "se",
        "method": "field",
        "allometric_equation": "",
        "quality_flags": "",
        "license": "CC BY",
        "citation": "test",
        "model_status": "validation",
        "notes": "",
    }])


def test_build_observation_features_with_landsat_and_history(tmp_path):
    optical = tmp_path / "fields" / "site_001"
    optical.mkdir(parents=True)
    bands = np.zeros((7, 10, 10), dtype="float32")
    bands[0] = 0.1  # blue
    bands[1] = 0.1  # green
    bands[2] = 0.1  # red
    bands[3] = 0.4  # nir
    bands[4] = 0.2  # swir16
    bands[5] = 0.2  # swir22
    bands[6] = 5.0  # nobs
    _write_raster(optical / "landsat_2012.tif", bands,
                  ["blue", "green", "red", "nir08", "swir16", "swir22", "nobs"])
    _write_raster(optical / "dem.tif", np.full((1, 10, 10), 1000.0), ["elev"])

    mb = tmp_path / "mapbiomas"
    mb.mkdir()
    for year in range(2004, 2013):
        _write_raster(mb / f"mapbiomas_col11_{year}.tif",
                      np.full((1, 10, 10), 3.0), ["class"])

    obs = _observation(-49.95, -9.95)
    out = tmp_path / "features.csv"
    summary = build_observation_features(
        obs, out,
        optical_dir=tmp_path / "fields",
        optical_pattern="site_{site_int:03d}/landsat_{year}.tif",
        dem_dir=tmp_path / "fields",
        dem_pattern="site_{site_int:03d}/dem.tif",
        mapbiomas_dir=mb,
        history=True,
        history_start=2004,
        history_end=2018,
    )
    table = pd.read_csv(out)
    assert summary["rows_out"] == 1
    assert np.isfinite(table.loc[0, "ls_ndvi"])
    assert np.isclose(table.loc[0, "ls_ndvi"], (0.4 - 0.1) / (0.4 + 0.1))
    assert np.isfinite(table.loc[0, "elev"])
    assert table.loc[0, "mapbiomas_class"] == 3
    assert table.loc[0, "mb_history_years"] == 8
    assert table.loc[0, "mb_domain_years"] == 8
    assert not bool(table.loc[0, "feature_na"])
