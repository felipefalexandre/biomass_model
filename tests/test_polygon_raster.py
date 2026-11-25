import json

import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from biomass_model.aggregation.polygon import polygon_raster_stats


def _raster(path):
    profile = dict(
        driver="GTiff", width=3, height=3, count=2, dtype="float32",
        crs="EPSG:3857", transform=from_origin(0, 90, 30, 30), nodata=np.nan,
    )
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.full((3, 3), 10.0, dtype="float32"), 1)
        dst.write(np.array([
            [3, 3, 4],
            [3, 3, 4],
            [3, 3, 4],
        ], dtype="float32"), 2)
        dst.set_band_description(1, "agbd_mg_ha")
        dst.set_band_description(2, "mapbiomas_class")


def _polygon(path, geometry):
    import geopandas as gpd

    gpd.GeoDataFrame({"id": [1]}, geometry=[geometry], crs="EPSG:3857").to_file(path)


def test_polygon_full_raster_area_and_total(tmp_path):
    raster = tmp_path / "map.tif"
    _raster(raster)
    vector = tmp_path / "poly.geojson"
    _polygon(vector, box(0, 0, 90, 90))
    result = polygon_raster_stats(raster, vector, class_band=2, n_boot=50)
    assert np.isclose(result["polygon_area_ha"], 0.81)
    assert np.isclose(result["area_analyzed_ha"], 0.81)
    assert np.isclose(result["mean_agbd_mg_ha"], 10.0)
    assert np.isclose(result["median_agbd_mg_ha"], 10.0)
    assert np.isclose(result["total_mg"], 8.1)
    assert result["n_cells"] == 9


def test_polygon_partial_cell_uses_real_intersection(tmp_path):
    raster = tmp_path / "map.tif"
    _raster(raster)
    vector = tmp_path / "poly.geojson"
    _polygon(vector, box(0, 0, 15, 15))
    result = polygon_raster_stats(raster, vector, n_boot=20)
    assert np.isclose(result["polygon_area_ha"], 0.0225)
    assert np.isclose(result["area_analyzed_ha"], 0.0225)
    assert np.isclose(result["total_mg"], 0.225)
    assert result["n_cells"] == 1


def test_polygon_domain_filter_and_by_class(tmp_path):
    raster = tmp_path / "map.tif"
    _raster(raster)
    vector = tmp_path / "poly.geojson"
    _polygon(vector, box(0, 0, 90, 90))
    result = polygon_raster_stats(
        raster, vector, class_band=2, domain_classes=(3,), n_boot=20,
    )
    assert np.isclose(result["area_analyzed_ha"], 0.54)
    assert np.isclose(result["total_mg"], 5.4)
    classes = {int(c["code"]): c for c in result["by_class"]}
    assert int(classes[3]["n_cells"]) == 6


def test_polygon_with_separate_class_and_fitofisionomia_rasters(tmp_path):
    raster = tmp_path / "map.tif"
    _raster(raster)
    class_raster = tmp_path / "class.tif"
    fit_raster = tmp_path / "fit.tif"
    profile = dict(driver="GTiff", width=3, height=3, count=1, dtype="float32",
                   crs="EPSG:3857", transform=from_origin(0, 90, 30, 30), nodata=0)
    with rasterio.open(class_raster, "w", **profile) as dst:
        dst.write(np.array([[3, 3, 4], [3, 3, 4], [3, 3, 4]], dtype="float32"), 1)
    with rasterio.open(fit_raster, "w", **profile) as dst:
        dst.write(np.array([[1, 1, 2], [1, 1, 2], [1, 1, 2]], dtype="float32"), 1)
    codes = tmp_path / "fit.json"
    codes.write_text(json.dumps({"codes": [{"code": 1, "label": "Savana Arborizada"},
                                             {"code": 2, "label": "Savana Parque"}]}),
                     encoding="utf-8")
    vector = tmp_path / "poly.geojson"
    _polygon(vector, box(0, 0, 90, 90))
    result = polygon_raster_stats(
        raster, vector, class_raster=class_raster, fitofisionomia_raster=fit_raster,
        fitofisionomia_codes=codes, n_boot=20,
    )
    assert np.isclose(result["area_analyzed_ha"], 0.81)
    assert {int(c["code"]) for c in result["by_class"]} == {3, 4}
    labels = {c["label"] for c in result["by_fitofisionomia"]}
    assert labels == {"Savana Arborizada", "Savana Parque"}
