import numpy as np
import pytest
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from biomass_model.grid import RasterGrid


def _make_raster(width=8, height=6, res=0.01, nodata=0):
    transform = from_origin(-50.0, -10.0, res, res)
    mem = MemoryFile()
    ds = mem.open(
        driver="GTiff",
        width=width,
        height=height,
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=transform,
        nodata=nodata,
    )
    ds.write(np.zeros((height, width), dtype="uint8"), 1)
    ds.close()
    return mem


def test_from_raster_reads_grid():
    mem = _make_raster()
    with mem.open() as ds:
        grid = RasterGrid.from_raster(ds.name)
    assert grid.width == 8
    assert grid.height == 6
    assert grid.crs == "EPSG:4326"
    assert grid.nodata == 0


def test_assert_compatible_accepts_same_grid():
    mem_a = _make_raster()
    mem_b = _make_raster()
    with mem_a.open() as a, mem_b.open() as b:
        RasterGrid.from_raster(a.name).assert_compatible(RasterGrid.from_raster(b.name))


def test_assert_compatible_rejects_shape():
    mem_a = _make_raster()
    mem_b = _make_raster(width=9)
    with mem_a.open() as a, mem_b.open() as b:
        with pytest.raises(ValueError, match="dimensoes"):
            RasterGrid.from_raster(a.name).assert_compatible(RasterGrid.from_raster(b.name))


def test_assert_compatible_rejects_crs():
    mem_a = _make_raster()
    mem_b = _make_raster()
    with mem_a.open() as a, mem_b.open() as b:
        grid_b = RasterGrid(
            crs="EPSG:4674",
            transform=RasterGrid.from_raster(b.name).transform,
            width=RasterGrid.from_raster(b.name).width,
            height=RasterGrid.from_raster(b.name).height,
            nodata=0,
        )
        with pytest.raises(ValueError, match="CRS"):
            RasterGrid.from_raster(a.name).assert_compatible(grid_b)


def test_row_pixel_area_decreases_toward_poles():
    mem = _make_raster()
    with mem.open() as ds:
        grid = RasterGrid.from_raster(ds.name)
    areas = grid.row_pixel_area_m2(0, grid.height)
    assert np.all(areas > 0)
    assert np.all(np.diff(areas) < 0)
