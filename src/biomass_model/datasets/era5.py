"""ERA5-Land mensal via CDS API. Requer `~/.cdsapirc`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..credentials import CDSAPIRC
from ..manifest import build_manifest, write_manifest

VARIABLES = [
    "2m_temperature",
    "total_precipitation",
    "potential_evaporation",
    "surface_solar_radiation_downwards",
    "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2",
    "volumetric_soil_water_layer_3",
    "volumetric_soil_water_layer_4",
]
LICENSE = "Copernicus C3S"
ACCOUNT = "conta CDS + chave em ~/.cdsapirc"


def fetch_era5(
    lon: float,
    lat: float,
    start_year: int,
    end_year: int,
    out: str | Path,
    pad: float = 0.1,
    manifest: bool = True,
) -> dict[str, Any]:
    import cdsapi

    if not CDSAPIRC.exists():
        raise RuntimeError(f"CDS nao configurado: crie {CDSAPIRC} (ver docs/32)")

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    request = {
        "product_type": ["monthly_averaged_reanalysis"],
        "variable": VARIABLES,
        "year": [str(y) for y in range(start_year, end_year + 1)],
        "month": [f"{m:02d}" for m in range(1, 13)],
        "time": "00:00",
        "area": [lat + pad, lon - pad, lat - pad, lon + pad],
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    cdsapi.Client().retrieve("reanalysis-era5-land-monthly-means", request, str(out_path))

    if manifest:
        write_manifest(
            build_manifest(
                "era5",
                {"lon": lon, "lat": lat, "start_year": start_year, "end_year": end_year,
                 "pad": pad, "variables": VARIABLES},
                [out_path],
                license=LICENSE,
                account=ACCOUNT,
                source="https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-monthly-means",
            )
        )
    return {"path": str(out_path), "bytes": out_path.stat().st_size, "request": request}
