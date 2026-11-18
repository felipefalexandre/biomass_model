"""GEDI L4A: busca (CMR), download e extracao de footprints.

Le HDF5 com o driver HDF5 do GDAL (rasterio), evitando a dependencia de h5py.
Filtro padrao: l2_quality_flag==1, l4_quality_flag==1, agbd>=0 e
0.9 <= sensitivity <= 1.01. O degrade_flag e mantido e reportado, nao usado
como filtro rigido na v1 (ver ADR-0012).
"""

from __future__ import annotations

import re
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
import rasterio
from rasterio.errors import NotGeoreferencedWarning

warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)

from ..credentials import require_earthdata
from ..manifest import build_manifest, write_manifest

VERSIONS = {
    "V2_1": "GEDI_L4A_AGB_Density_V2_1_2056",
    "V3": "GEDI_L4A_AGB_Density_V3_2508",
}
BEAMS = ["BEAM0000", "BEAM0001", "BEAM0010", "BEAM0011",
         "BEAM0101", "BEAM0110", "BEAM1000", "BEAM1011"]
VARS = [
    "agbd", "agbd_se", "agbd_pi_lower", "agbd_pi_upper",
    "l2_quality_flag", "l4_quality_flag", "degrade_flag",
    "sensitivity", "solar_elevation",
    "lat_lowestmode", "lon_lowestmode", "elev_lowestmode",
    "shot_number", "beam",
]
LICENSE = "NASA (aberto, atribuicao)"
ACCOUNT = "Earthdata Login + token + app LP DAAC autorizada"
SOURCE = "https://doi.org/10.5067/GEDI/GEDI04_A.002"


def parse_granule_time(native_id: str) -> datetime:
    """Extrai data/hora do nome GEDI04_A_YYYYDDDHHMMSS_O...."""
    match = re.search(r"_(\d{4})(\d{3})(\d{2})(\d{2})(\d{2})_O", native_id)
    if not match:
        raise ValueError(f"nome de granulo GEDI inesperado: {native_id}")
    year, doy, hour, minute, second = (int(x) for x in match.groups())
    return datetime(year, 1, 1) + timedelta(days=doy - 1, hours=hour, minutes=minute, seconds=second)


def quality_mask(
    agbd: np.ndarray,
    l2_quality_flag: np.ndarray,
    l4_quality_flag: np.ndarray,
    sensitivity: np.ndarray,
    min_sensitivity: float = 0.9,
    max_sensitivity: float = 1.01,
) -> np.ndarray:
    return (
        (l2_quality_flag == 1)
        & (l4_quality_flag == 1)
        & (agbd >= 0)
        & np.isfinite(agbd)
        & (sensitivity >= min_sensitivity)
        & (sensitivity <= max_sensitivity)
    )


def _read_var(path: str | Path, beam: str, var: str) -> np.ndarray:
    uri = 'HDF5:"{}"://{}/{}'.format(Path(path).as_posix(), beam, var)
    with rasterio.open(uri) as ds:
        return ds.read(1).ravel()


def extract_granule(
    path: str | Path,
    bbox: tuple[float, float, float, float],
    min_sensitivity: float = 0.9,
) -> dict[str, np.ndarray]:
    """Le um granulo e devolve arrays filtrados dentro do bbox.

    bbox = (west, south, east, north) em EPSG:4326.
    """
    west, south, east, north = bbox
    arrays: dict[str, list[np.ndarray]] = {}
    for beam in BEAMS:
        try:
            cols = {var: _read_var(path, beam, var) for var in VARS}
        except Exception:
            continue
        for var, values in cols.items():
            arrays.setdefault(var, []).append(values)
    if not arrays:
        raise RuntimeError(f"nenhuma variavel legivel em {path}")

    data = {var: np.concatenate(values) for var, values in arrays.items()}
    inside = (
        (data["lon_lowestmode"] >= west)
        & (data["lon_lowestmode"] <= east)
        & (data["lat_lowestmode"] >= south)
        & (data["lat_lowestmode"] <= north)
    )
    keep = inside & quality_mask(
        data["agbd"], data["l2_quality_flag"], data["l4_quality_flag"],
        data["sensitivity"], min_sensitivity=min_sensitivity,
    )
    out = {var: values[keep] for var, values in data.items()}
    out["granule"] = np.array([Path(path).stem] * int(keep.sum()))
    return out


def search_granules(
    bbox: tuple[float, float, float, float],
    start: str,
    end: str,
    version: str = "V2_1",
    count: int = -1,
) -> list[Any]:
    import earthaccess

    require_earthdata()
    earthaccess.login(strategy="environment")
    return earthaccess.search_data(
        short_name=VERSIONS[version],
        bounding_box=bbox,
        temporal=(start, end),
        count=count,
    )


def fetch_gedi(
    bbox: tuple[float, float, float, float],
    start: str,
    end: str,
    out_csv: str | Path,
    work_dir: str | Path,
    version: str = "V2_1",
    max_granules: int | None = None,
    min_sensitivity: float = 0.9,
    manifest: bool = True,
) -> dict[str, Any]:
    import earthaccess

    granules = search_granules(bbox, start, end, version=version)
    if max_granules is not None:
        granules = granules[:max_granules]
    if not granules:
        raise RuntimeError("nenhum granulo GEDI encontrado")

    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    files = earthaccess.download(granules, str(work))

    frames = []
    for file in files:
        try:
            data = extract_granule(file, bbox, min_sensitivity=min_sensitivity)
        except Exception as exc:
            print(f"aviso: {Path(file).name}: {exc}")
            continue
        frame = pd.DataFrame({k: v for k, v in data.items()})
        if frame.empty:
            continue
        frame["granule_time"] = parse_granule_time(Path(file).stem).isoformat()
        frames.append(frame)

    if not frames:
        raise RuntimeError("nenhum footprint valido apos o filtro de qualidade")

    table = pd.concat(frames, ignore_index=True)
    table["degrade_zero"] = table["degrade_flag"] == 0
    table = table.sort_values(["granule_time", "shot_number"]).reset_index(drop=True)

    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False)

    summary = {
        "rows": int(len(table)),
        "granules_downloaded": len(files),
        "granules_used": int(table["granule"].nunique()),
        "agbd_median": float(table["agbd"].median()),
        "degrade_zero_fraction": float(table["degrade_zero"].mean()),
        "path": str(out_path),
    }
    if manifest:
        write_manifest(
            build_manifest(
                "gedi",
                {"bbox": bbox, "start": start, "end": end, "version": version,
                 "max_granules": max_granules, "min_sensitivity": min_sensitivity,
                 **summary},
                [out_path],
                license=LICENSE,
                account=ACCOUNT,
                source=SOURCE,
                notes="HDF5 lidos no diretorio de trabalho; checksums no manifesto de download",
            )
        )
    return summary
