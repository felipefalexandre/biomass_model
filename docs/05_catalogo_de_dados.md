# 05 — Catálogo de dados

Catálogo das fontes candidatas, com papel no sistema, acesso e status de verificação. A versão
legível por máquina está em `data/catalogo_dados.csv`.

**Legenda de status:** `verificado` = URL/licença confirmadas nesta fase; `a_verificar` = fonte
conhecida, mas versão/licença/URL precisam ser confirmadas antes do uso; `restrito` = acesso
condicionado (cadastro, solicitação ou termo).

## 1. Camada de referência (alvo)

| ID | Fonte | Tipo | Resolução | Período | Papel | Acesso | Status |
|---|---|---|---|---|---|---|---|
| D01 | GEDI L4A (AGBD por footprint) | LiDAR espacial (produto de modelo) | ~25 m footprint | 2019–2023 | referência principal de treino | NASA LP DAAC, aberto | verificado (missão/documentação) |
| D02 | GEDI L4B (AGBD agregado) | LiDAR (produto de modelo) | 1 km | 2019–2023 | benchmark/estratificação | NASA LP DAAC, aberto | a_verificar (versão) |
| D03 | ICESat-2 ATL08 | LiDAR fotoncontagem | ~100 m segmentos | 2018– | referência auxiliar de altura | NSIDC, aberto | a_verificar |
| D04 | IFN — Inventário Florestal Nacional (SFB) | inventário de campo | parcelas | 2012– | validação/calibração | SFB/SNIF | verificado (painel aberto) |
| D05 | Parcelas de literatura/teses (Cerrado/Amazônia) | campo | ponto | variado | validação independente | publicações | a_verificar (compilação) |
| D06 | Base global de densidade da madeira (GWDD v1/v2) | trait | táxon | — | allometria | Dryad/Zenodo, aberto | verificado (v1 DOI) |

## 2. Camada de predição (features)

| ID | Fonte | Tipo | Resolução | Período | Papel | Acesso | Status |
|---|---|---|---|---|---|---|---|
| D10 | Sentinel-2 MSI L2A | óptico | 10–20 m | 2015– | features espectrais/fenológicas | Copernicus, aberto | verificado (programa) |
| D11 | Landsat 8/9 OLI/TIRS C2 L2 | óptico | 30 m | 2013– | features e série histórica | USGS, domínio público | verificado |
| D12 | Sentinel-1 GRD | radar C-band | 10 m | 2014– | estrutura/umidade | Copernicus, aberto | verificado (programa) |
| D13 | ALOS PALSAR / PALSAR-2 mosaicos | radar L-band | 25 m | 2007– | estrutura (histórico) | JAXA, a_verificar termos | a_verificar |
| D14 | SRTM | topografia | 30 m | 2000 | elevação/declividade | USGS, domínio público | verificado |
| D15 | Copernicus DEM GLO-30 | topografia | 30 m | 2011–2015 | elevação (alternativa) | ESA, aberto | a_verificar (termos) |
| D16 | ERA5-Land | clima (reanálise) | ~9 km | 1950– | clima/temporada | Copernicus C3S, aberto | verificado (DOI) |
| D17 | CHIRPS | precipitação | 0,05° | 1981– | clima | UCSB, aberto | a_verificar (licença) |
| D18 | WorldClim / CHELSA | clima (normais) | 1 km / 30" | 1970–2000 / 1981–2010 | clima estático | aberto | a_verificar (versão) |
| D19 | SoilGrids | solo | 250 m | estático | preditor de BGB/estrutura | ISRIC, CC BY | a_verificar (versão) |

## 3. Camada de estratificação e máscara

| ID | Fonte | Tipo | Resolução | Período | Papel | Acesso | Status |
|---|---|---|---|---|---|---|---|
| D20 | MapBiomas Coleção 11 (uso e cobertura) | classificação | 30 m | 1985–2024/2025 | estratificação, máscara | MapBiomas, aberto (CC BY-SA a confirmar) | verificado (dados locais em uso) |
| D21 | MapBiomas desmatamento (produto derivado, etapa anterior) | série anual | 30 m | 2014–2025 | mudança/emissões | gerado localmente | verificado |
| D22 | PRODES (INPE) | desmatamento | 30 m/regional | 1988– | validação de mudança | TerraBrasilis, aberto | a_verificar (URL/versão) |
| D23 | Limites de biomas (IBGE, `lm_bioma_250`) | vetor | 1:250.000 | — | domínio | IBGE, aberto | verificado (shapefile local) |
| D24 | Municípios, UFs, UCs, TIs | vetor | variado | — | relato/consulta | IBGE/ICMBio/FUNAI | a_verificar |
| D25 | Hydrography / água (MapBiomas ou ANA) | vetor/raster | variado | — | exclusão de água | aberto | a_verificar |

## 4. Produtos de comparação

| ID | Fonte | Tipo | Resolução | Período | Papel | Acesso | Status |
|---|---|---|---|---|---|---|---|
| D30 | CCI Biomass 2010 (Santoro et al. 2021) | AGB global | 100 m | 2010 | benchmark | ESA CCI, aberto | verificado (DOI) |
| D31 | Mapas harmonizados AGB/BGB (Spawn et al. 2020) | AGB/BGB | 1 km | 2010 | benchmark | Dryad/PNAS, aberto | verificado (DOI) |
| D32 | Mapa pan-tropical Avitabile et al. 2016 | AGB | 1 km | ~2000s | benchmark | aberto | a_verificar |
| D33 | Global Forest Watch / alertas | mudança | 10–30 m | 2001– | contexto de mudança | WRI, aberto | a_verificar (termos) |

## 4.1 Legenda, inventários e dados de campo (adicionados em 2026-11-17)

| ID | Fonte | Tipo | Resolução | Período | Papel | Acesso | Status |
|---|---|---|---|---|---|---|---|
| D34 | Legenda MapBiomas Coleção 11 | metadado oficial | — | 2026 | classes, códigos e códigos IBGE | MapBiomas, aberto | verificado (PDF baixado) |
| D35 | Painel de Biomassa e Carbono (IFN/SFB) | AGB por unidade amostral | ponto/UA | IFN | calibração/validação regional | SFB, CC BY | verificado (CSV baixado) |
| D36 | Roitman et al. 2018 (PLOS ONE) | Cerrado s.s., parcelas e árvores | 77 sítios / 893 parcelas | variado | calibração/validação | PLOS, CC BY | verificado (DOI + XLSX) |
| D37 | ORNL DAAC — Sustainable Landscapes Brazil | inventário árvore-a-árvore | sítios | 2009–2018 | validação | NASA, login Earthdata | a_verificar (download) |
| D38 | CEDA — Manaus plots AGB 2014 | AGB por parcela | 22 parcelas | 2014 | validação | CEDA, OGL | a_verificar (download) |
| D39 | NERC EIDC — RAINFOR census | DAP por árvore | 29 parcelas | 2017–2019 | validação | EIDC, OGL | verificado (DOI) |
| D40 | Mendeley — Vourlitis (Cerrado MT) | DAP/altura/AGB por árvore | parcelas | 2011–2018 | validação | Mendeley, aberto | verificado (DOI) |
| D41 | Mendeley — Maracá (RR) | AGB/C por parcela | 129 parcelas | censo 4 | validação | Mendeley, aberto | verificado (DOI) |
| D42 | Zenodo — EBA (mapa de AGB da Amazônia) | AGB + incerteza | 30 m | ~2018 | benchmark | Zenodo, aberto | verificado (DOI) |

Detalhes, colunas e regras de harmonização: `data/reference/inventarios_abertos.md`.

### 4.2 Pilotos

| Bioma | Nome | lon | lat | Janela | f3 | f4 | f3+4 | UAs IFN |
|---|---|---|---|---|---|---|---|---|
| Amazônia | piloto_amazonas_sul | −60,45 | −6,90 | 512 px | 0,933 | 0,000 | 0,933 | 511 |
| Cerrado | piloto_chapada_veadeiros | −47,70 | −13,95 | 512 px | 0,256 | 0,536 | 0,791 | 605 |

Critério: fração de classes 3/4 no MapBiomas 2025 × densidade de unidades amostrais do IFN.
Arquivo: `data/reference/pilotos_selecionados.csv`.

## 5. Critérios de aceitação de uma fonte

Uma fonte só entra no pipeline se atender a todos:

1. **Licença compatível** com uso e, se necessário, redistribuição (`docs/21`).
2. **Acesso reprodutível** (URL estável, versão identificável, autenticação documentada).
3. **Metadados suficientes** (CRS, unidade, data, processamento, nodata).
4. **Cobertura** do domínio no período necessário.
5. **Qualidade documentada** ou avaliável (`docs/06`).
6. **Custo zero** na trilha principal — caso contrário, redflag (`docs/22`).

## 6. Ordem de aquisição sugerida

1. Limites e máscaras (D23, D20, D21) — pequenos, imediatos.
2. Topografia e clima (D14, D16) — estáveis, baixo volume.
3. Sentinel-2 e Landsat por região/ano (D10, D11) — maior volume; começar por amostra.
4. Sentinel-1 (D12) — depois da linha de base óptica.
5. GEDI L4A (D01) — recorte por tiles/região; validar geometria antes de baixar tudo.
6. Produtos de benchmark (D30, D31) — leves e úteis cedo para comparação.
