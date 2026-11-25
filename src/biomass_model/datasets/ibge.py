"""Aquisição da vegetação IBGE 1:250.000 (ADR-0029).

Fonte oficial: geoftp.ibge.gov.br, dados públicos. O download é feito por streaming, com hash
SHA-256 e manifesto; a extração é idempotente. O módulo não decide qual atributo usar como
fitofisionomia; isso é feito na camada de estratificação.
"""

from __future__ import annotations

import hashlib
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from ..manifest import build_manifest, write_manifest

BASE_URL = "https://geoftp.ibge.gov.br/informacoes_ambientais/vegetacao/vetores/escala_250_mil"
DEFAULT_VERSION = "2026"
LICENSE = "IBGE — dados públicos (verificar termos de uso e citação)"
SOURCE = f"{BASE_URL}/versao_{DEFAULT_VERSION}/"
USER_AGENT = "biomass-model/0.1 (+https://github.com/felipefalexandre/biomass_model)"

FILES = {
    "areas": "vege_area.zip",
    "pontos": "vege_ponto.zip",
    "tabelas": "vege_tabelas.zip",
    "atributos": "atributos_vege.pdf",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, out: Path) -> dict[str, Any]:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    bytes_written = 0
    with urllib.request.urlopen(request, timeout=120) as response, tmp.open("wb") as fh:
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
            digest.update(chunk)
            bytes_written += len(chunk)
    shutil.move(str(tmp), str(out))
    return {"path": str(out), "bytes": bytes_written, "sha256": digest.hexdigest(), "url": url}


def _extract(zip_path: Path, out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(out_dir)
    return [str(p) for p in sorted(out_dir.rglob("*.shp"))]


def fetch_ibge_vegetacao(
    out_dir: str | Path,
    *,
    version: str = DEFAULT_VERSION,
    include_points: bool = False,
    include_tables: bool = True,
    download: bool = True,
    manifest: bool = True,
) -> dict[str, Any]:
    """Baixa e extrai a vegetação 1:250.000 do IBGE.

    `download=False` apenas verifica arquivos existentes e extrai; útil para execuções
    retomáveis. O arquivo de áreas (~355 MB) é o insumo principal.
    """
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    base = f"{BASE_URL}/versao_{version}"
    wanted = ["areas"]
    if include_points:
        wanted.append("pontos")
    if include_tables:
        wanted.append("tabelas")
    wanted.append("atributos")

    downloaded = []
    for key in wanted:
        filename = FILES[key]
        target = root / filename
        url = f"{base}/{filename}"
        if target.exists() and target.stat().st_size > 0:
            downloaded.append({"path": str(target), "bytes": target.stat().st_size,
                               "sha256": _sha256(target), "url": url, "cached": True})
            continue
        if not download:
            raise FileNotFoundError(f"{target} ausente e download=False")
        if key == "atributos":
            target.write_bytes(urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": USER_AGENT}),
                timeout=120,
            ).read())
            downloaded.append({"path": str(target), "bytes": target.stat().st_size,
                               "sha256": _sha256(target), "url": url})
            continue
        downloaded.append(_download(url, target))

    extracted = {}
    for key in ("areas", "pontos"):
        if key not in wanted:
            continue
        zip_path = root / FILES[key]
        target_dir = root / key
        extracted[key] = _extract(zip_path, target_dir)

    summary = {
        "version": version,
        "out_dir": str(root),
        "downloaded": downloaded,
        "shapefiles": extracted,
        "license": LICENSE,
        "source": f"{base}/",
    }
    if manifest:
        outputs = [Path(item["path"]) for item in downloaded]
        for files in extracted.values():
            outputs.extend(Path(p) for p in files)
        write_manifest(
            build_manifest(
                "ibge_vegetacao",
                {"version": version, "include_points": include_points,
                 "include_tables": include_tables},
                outputs,
                license=LICENSE,
                account="nenhuma",
                source=f"{base}/",
                notes="Dados públicos IBGE 1:250.000; usar legenda_1/legenda_2/legenda conforme ADR-0029",
            )
        )
    return summary
