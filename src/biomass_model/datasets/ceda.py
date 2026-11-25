"""CEDA/NCEO Manaus plots AGB 2014 (OGL, dados abertos).

Fonte: https://catalogue.ceda.ac.uk/uuid/c7aa24fb8d5c458daefdf0f4410ba830
Arquivo: shapefile de 23 parcelas de 100 x 60 m com AGB.
"""

from __future__ import annotations

import hashlib
import shutil
import urllib.request
from pathlib import Path
from typing import Any

from ..manifest import build_manifest, write_manifest

BASE_URL = "https://dap.ceda.ac.uk/neodc/nceo_biomass_maps/data/manaus/v1.0/2014/"
LICENSE = "Open Government Licence v3 (OGL)"
ACCOUNT = "nenhuma"
SOURCE = "https://catalogue.ceda.ac.uk/uuid/c7aa24fb8d5c458daefdf0f4410ba830"
CITATION = "Carreiras, J. (2025): NCEO Manaus plots AGB map 2014 v1.0. NERC EDS CEDA."
USER_AGENT = "biomass-model/0.1 (+https://github.com/felipefalexandre/biomass_model)"

FILES = [
    "00README_catalogue_and_licence.txt",
    "Manaus2014_Plots100x60m_AGB.dbf",
    "Manaus2014_Plots100x60m_AGB.prj",
    "Manaus2014_Plots100x60m_AGB.sbn",
    "Manaus2014_Plots100x60m_AGB.sbx",
    "Manaus2014_Plots100x60m_AGB.shp",
    "Manaus2014_Plots100x60m_AGB.shx",
]
SHAPEFILE = "Manaus2014_Plots100x60m_AGB.shp"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_ceda_manaus(
    out_dir: str | Path,
    *,
    download: bool = True,
    manifest: bool = True,
) -> dict[str, Any]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for name in FILES:
        target = root / name
        url = BASE_URL + name
        if target.exists() and target.stat().st_size > 0:
            downloaded.append({"path": str(target), "bytes": target.stat().st_size,
                               "sha256": _sha256(target), "url": url, "cached": True})
            continue
        if not download:
            raise FileNotFoundError(f"{target} ausente e download=False")
        tmp = target.with_suffix(target.suffix + ".part")
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=120) as response, tmp.open("wb") as fh:
            shutil.copyfileobj(response, fh)
        tmp.replace(target)
        downloaded.append({"path": str(target), "bytes": target.stat().st_size,
                           "sha256": _sha256(target), "url": url})

    summary = {
        "out_dir": str(root),
        "shapefile": str(root / SHAPEFILE),
        "downloaded": downloaded,
        "license": LICENSE,
        "citation": CITATION,
        "source": SOURCE,
    }
    if manifest:
        write_manifest(build_manifest(
            "ceda_manaus",
            {"files": FILES, "out_dir": str(root)},
            [Path(item["path"]) for item in downloaded],
            license=LICENSE, account=ACCOUNT, source=SOURCE,
            notes="shapefile de 23 parcelas 100x60m; AGB por parcela",
        ))
    return summary
