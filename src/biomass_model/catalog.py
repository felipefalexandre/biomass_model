"""Catalogo executavel de fontes de dados.

Complementa `data/catalogo_dados.csv` com a informacao que o codigo precisa:
modulo de aquisicao, conta exigida e documento de referencia.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetSpec:
    id: str
    name: str
    provider: str
    license: str
    account: str
    module: str | None
    doc: str


DATASETS: tuple[DatasetSpec, ...] = (
    DatasetSpec(
        id="s2",
        name="Sentinel-2 L2A",
        provider="Copernicus / AWS Open Data",
        license="Copernicus data policy (atribuicao)",
        account="nenhuma (COGs publicos via earth-search)",
        module="biomass_model.datasets.s2",
        doc="docs/32_aquisicao_de_dados.md#sentinel-2",
    ),
    DatasetSpec(
        id="dem",
        name="Copernicus DEM GLO-30",
        provider="ESA / AWS Open Data",
        license="Copernicus DEM (aberto, atribuicao)",
        account="nenhuma",
        module="biomass_model.datasets.dem",
        doc="docs/32_aquisicao_de_dados.md#dem",
    ),
    DatasetSpec(
        id="era5",
        name="ERA5-Land mensal",
        provider="Copernicus C3S (CDS)",
        license="Copernicus C3S",
        account="conta CDS + chave em ~/.cdsapirc",
        module="biomass_model.datasets.era5",
        doc="docs/32_aquisicao_de_dados.md#era5-land",
    ),
    DatasetSpec(
        id="gedi",
        name="GEDI L4A AGBD por footprint",
        provider="NASA LP DAAC / ORNL DAAC",
        license="NASA (aberto, atribuicao)",
        account="Earthdata Login + token + app LP DAAC autorizada",
        module="biomass_model.datasets.gedi",
        doc="docs/32_aquisicao_de_dados.md#gedi-l4a",
    ),
    DatasetSpec(
        id="s1",
        name="Sentinel-1 RTC (radar)",
        provider="ASF / Copernicus",
        license="ASF / Copernicus (aberto)",
        account="Earthdata Login + app ASF autorizada",
        module=None,
        doc="docs/32_aquisicao_de_dados.md#sentinel-1",
    ),
    DatasetSpec(
        id="mapbiomas",
        name="MapBiomas Colecao 11",
        provider="MapBiomas",
        license="CC BY-SA (confirmar)",
        account="nenhuma (arquivos locais)",
        module=None,
        doc="docs/32_aquisicao_de_dados.md#mapbiomas",
    ),
    DatasetSpec(
        id="sfb_panel",
        name="Painel de Biomassa e Carbono (IFN)",
        provider="SFB",
        license="CC BY",
        account="nenhuma (HTTP aberto)",
        module=None,
        doc="docs/32_aquisicao_de_dados.md#inventarios",
    ),
)


def get(dataset_id: str) -> DatasetSpec:
    for spec in DATASETS:
        if spec.id == dataset_id:
            return spec
    known = ", ".join(s.id for s in DATASETS)
    raise KeyError(f"dataset desconhecido: {dataset_id!r} (use: {known})")
