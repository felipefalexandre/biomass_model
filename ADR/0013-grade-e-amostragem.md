# ADR-0013 — Grade de modelagem e amostragem nos footprints

**Status:** aceito
**Data:** 2026-11-17

## Contexto

As camadas têm resoluções e CRS distintos: Sentinel-2 em UTM 10 m, DEM em EPSG:4326 ~30 m,
ERA5-Land em 0,1°, MapBiomas em EPSG:4326 ~30 m. Parear GEDI (footprint ~25 m) com features exige
uma grade única, e parear em CRS errado introduz desalinhamento silencioso.

## Decisão

- **Grade de modelagem:** mesma grade do MapBiomas (EPSG:4326, ~30 m,
  `transform=(0.00026949458523585647, 0, -74.02073025380652, 0, -0.00026949458523585647,
  5.405791885246045)`), recortada ao bbox do piloto.
- **Features:** cada raster é reprojetado/reamostrado para essa grade; contínuas com bilinear,
  categóricas com vizinho mais próximo. Alinhamento verificado por `grid.RasterGrid`.
- **Amostragem:** cada footprint GEDI é associado ao pixel da grade que contém
  (`lon_lowestmode`, `lat_lowestmode`); não se interpola AGB. Vários footprints no mesmo pixel são
  mantidos como observações repetidas e o CV agrupa por bloco espacial, não por pixel.
- **Máscara:** domínio `classe(t) ∈ {3, 4}` (ADR-0010) aplicado no ano de referência; footprints
  fora do domínio não entram no treino.
- **Resolução de análise:** agregados de 30 m para treino; relato e validação também em células de
  1 km e por bloco, para não fingir precisão de 30 m.

## Consequências

- Um único grid para todas as camadas, com teste de compatibilidade.
- Perda de detalhe do S2 de 10 m na grade de 30 m; aceitável porque o alvo GEDI já é ~25 m.
- Repetição de footprints no mesmo pixel não infla o CV por causa dos blocos espaciais.
- A grade nacional usa a mesma convenção, permitindo expandir o piloto sem reformular o pipeline.

## Evidência

- `src/biomass_model/grid.py`; `docs/17`; `docs/18`; ADR-0006 e ADR-0008.
