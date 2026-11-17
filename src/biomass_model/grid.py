"""Contratos de grade para o pipeline de biomassa.

Todas as camadas empilhadas devem compartilhar CRS, transform, largura, altura e
nodata. Este modulo fornece a verificacao minima para falhar cedo em caso de
desalinhamento, evitando erros silenciosos de pareamento pixel a pixel.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.windows import Window


@dataclass(frozen=True)
class RasterGrid:
    crs: str
    transform: Affine
    width: int
    height: int
    nodata: float | None = None

    @classmethod
    def from_raster(cls, path) -> "RasterGrid":
        with rasterio.open(path) as ds:
            return cls(
                crs=str(ds.crs),
                transform=ds.transform,
                width=ds.width,
                height=ds.height,
                nodata=ds.nodata,
            )

    def assert_compatible(self, other: "RasterGrid", name: str = "raster") -> None:
        if self.crs != other.crs:
            raise ValueError(f"{name}: CRS divergente ({other.crs} != {self.crs})")
        if (self.width, self.height) != (other.width, other.height):
            raise ValueError(
                f"{name}: dimensoes divergentes "
                f"({other.width}x{other.height} != {self.width}x{self.height})"
            )
        if self.transform != other.transform:
            raise ValueError(f"{name}: transform divergente")

    def window(self, row_off: int, col_off: int, height: int, width: int) -> Window:
        return Window(col_off, row_off, width, height)

    def row_pixel_area_m2(self, row_start: int, row_stop: int, radius_earth_m: float = 6_378_137.0):
        """Area de cada linha de pixel (m2) considerando a latitude central da linha."""
        res = abs(self.transform.e)
        lon_scale = 2.0 * np.pi * radius_earth_m / 360.0 * res
        lat = self.transform.f + (np.arange(row_start, row_stop) + 0.5) * self.transform.e
        lat_scale = 2.0 * np.pi * radius_earth_m / 360.0 * res
        return np.abs(lon_scale * lat_scale * np.cos(np.deg2rad(lat)))
