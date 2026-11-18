"""Baixa ERA5-Land (medias mensais) para um ponto, via CDS API.

Requer `~/.cdsapirc` configurado (ver docs/19). Salva NetCDF em disco local.

Uso:
    python tools/fetch_era5_land.py --lon -60.45 --lat -6.9 \
        --start-year 2018 --end-year 2025 \
        --out E:/Mapbiomas/biomass/pilots/amazonia_era5land_2018_2025.nc
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cdsapi

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--pad", type=float, default=0.1, help="graus de margem")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    request = {
        "product_type": ["monthly_averaged_reanalysis"],
        "variable": VARIABLES,
        "year": [str(y) for y in range(args.start_year, args.end_year + 1)],
        "month": [f"{m:02d}" for m in range(1, 13)],
        "time": "00:00",
        "area": [
            args.lat + args.pad,
            args.lon - args.pad,
            args.lat - args.pad,
            args.lon + args.pad,
        ],
        "data_format": "netcdf",
        "download_format": "unarchived",
    }

    client = cdsapi.Client()
    client.retrieve("reanalysis-era5-land-monthly-means", request, str(out))
    print(f"OK {out} ({out.stat().st_size/1e3:.1f} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
