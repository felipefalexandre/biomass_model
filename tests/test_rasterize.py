import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from biomass_model.stratification import rasterize_fitofisionomia


def test_rasterize_fitofisionomia(tmp_path):
    import geopandas as gpd

    template = tmp_path / "template.tif"
    profile = dict(driver="GTiff", width=2, height=2, count=1, dtype="float32",
                   crs="EPSG:3857", transform=from_origin(0, 60, 30, 30), nodata=0)
    with rasterio.open(template, "w", **profile) as dst:
        dst.write(np.zeros((2, 2), dtype="float32"), 1)

    vector = tmp_path / "fit.geojson"
    gpd.GeoDataFrame(
        {"fitofisionomia": ["Floresta", "Savana"]},
        geometry=[box(0, 30, 30, 60), box(30, 0, 60, 30)],
        crs="EPSG:3857",
    ).to_file(vector)

    out = tmp_path / "fit.tif"
    result = rasterize_fitofisionomia(vector, template, out, attribute="fitofisionomia")
    assert result["n_classes"] == 2
    with rasterio.open(out) as dst:
        arr = dst.read(1)
    assert arr.max() == 2
    assert (arr > 0).sum() == 2
