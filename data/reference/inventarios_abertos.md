# Inventários e dados de campo abertos — referência

Objetivo: reunir fontes **abertas** de inventário florestal e biomassa para calibração e,
principalmente, **validação independente** do mapa. Nada aqui é usado como verdade absoluta:
cada fonte tem protocolo, equação e data próprios.

Convenção de armazenamento:

- `data/raw/inventarios/` — arquivos baixados (não versionados; ver `.gitignore`).
- `data/reference/` — este documento, o CSV de fontes e os tiles piloto (versionados).

## 1. Fontes inventariadas

| ID | Fonte | Conteúdo | Período | Licença | Acesso | Status |
|---|---|---|---|---|---|---|
| INV01 | SFB — Painel de Biomassa e Carbono (IFN) | AGB por unidade amostral, bioma/UF, coordenadas (~0,1°), tipologia, equação, variância | IFN (2018–2020 no Cerrado; variado) | CC BY | aberto (CSV) | **baixado** |
| INV02 | Roitman et al. 2018 (PLOS ONE) — Cerrado s.s. | 77 sítios, 893 parcelas, 95.484 árvores; tabelas S1–S5 | décadas de levantamentos | CC BY | aberto (XLSX suplementar) | **baixado** (S3–S5) |
| INV03 | ORNL DAAC — Sustainable Landscapes Brazil | Inventário árvore-a-árvore (DAP, altura, espécie, coordenadas, AGB em sítios selecionados) | 2009–2018 | aberto (NASA) | requer login Earthdata (gratuito) | não baixado |
| INV04 | CEDA/NCEO — Manaus plots AGB 2014 | 22 parcelas com AGB, shapefile | 2014 | OGL | aberto | não baixado |
| INV05 | NERC EIDC — RAINFOR Amazon census | 29 parcelas, 8.729 árvores (DAP), Acre/MT/PA | 2017–2019 | OGL | aberto | não baixado |
| INV06 | Mendeley — Vourlitis (Cerrado MT) | Circunferência, DAP, altura, AGB e C por árvore; Pantanal e Cuiabá | 2011–2018 | aberto (Mendeley) | aberto | não baixado |
| INV07 | Mendeley — Maracá (RR) ecotone forests | 129 parcelas, AGB/C por parcela e por classe | censo 4 | aberto | aberto | não baixado |
| INV08 | LBA-ECO LC-05 (ORNL) | 50 parcelas de 1 ha, biomassa e solo, BDFFP (Manaus) | 1997–2001 | aberto (NASA) | login Earthdata | não baixado |
| INV09 | IFN — dados botânicos (SNIF) | Inventário árvore-a-árvore do IFN | 2018– | aberto (portal) | portal SNIF | não baixado |
| INV10 | Zenodo — EBA (Ometto et al.) | Mapa de AGB da Amazônia brasileira + incerteza (benchmark) | ~2018 | aberto | Zenodo (DOI) | não baixado |

## 2. O que já foi baixado

### 2.1 SFB — Painel de Biomassa e Carbono

Arquivos em `data/raw/inventarios/sfb/`:

- `biomassa.csv` (53 MB) — 439.970 registros;
- `equacoes.csv` — equações usadas, com referência e tipologia;
- `metadados.pdf` — metadados oficiais.

Colunas principais: `bioma`, `uf`, `lon_pc`, `lat_pc`, `ua`, `n_subunidades`, `sanidade`,
`classe_uso_da_terra`, `tipologia_da_vegetacao`, `equacoes`, `area_ha`,
`agb_media_kg_por_ha`, `agb_variancia_por_ua`, `valor_r`.

Estatísticas calculadas por nós sobre o CSV (não são estimativas oficiais do SFB):

| Bioma | Registros | AGB média (kg ha⁻¹) | AGB mediana (kg ha⁻¹) |
|---|---|---|---|
| Amazônia | 119.536 | 151.606,8 | 111.964,8 |
| Cerrado | 170.627 | 33.932,2 | 19.380,2 |

**Cuidados:**

1. A AGB é **calculada por equações distintas** (`AGB_Chave`, `Eq.183`, ...); comparar sem
   harmonizar é inválido.
2. As coordenadas têm ~0,1° de precisão — servem para validação regional, não para pareamento
   pixel a pixel.
3. `agb_variancia_por_ua` é a variância entre subunidades, não a variância da estimativa.
4. O painel inclui todos os biomas; filtrar por `bioma` e pela tipologia.

### 2.2 Roitman et al. 2018 (PLOS ONE)

Arquivos em `data/raw/inventarios/plos2018/`:

- `s003.xlsx` — 77 sítios com AGBD e IC;
- `s004.xlsx` — dados de parcela por sítio;
- `s005.xlsx` — AGBD por sítio, com diferenças estatísticas.

Uso: calibração/validação do modelo de Cerrado; referência de faixas por sítio.
DOI: `10.1371/journal.pone.0196742`.

## 3. Fontes ainda não baixadas (links)

- ORNL DAAC, Forest Inventory and Biophysical Measurements, Brazilian Amazon, 2009–2018:
  https://daac.ornl.gov/cgi-bin/dsviewer.pl?ds_id=1641 (login Earthdata).
- CEDA, NCEO Manaus plots AGB 2014:
  https://catalogue.ceda.ac.uk/uuid/c7aa24fb8d5c458daefdf0f4410ba830
- NERC EIDC, RAINFOR census 2017–2019:
  https://doi.org/10.5285/63d4b774-4e03-4db2-95ad-dcca18f0d681
- Mendeley, Vourlitis, Cerrado MT:
  https://doi.org/10.17632/2989vngvys.2
- Mendeley, Maracá (RR):
  https://doi.org/10.17632/2j354jtddx.2
- LBA-ECO LC-05:
  https://daac.ornl.gov/LBA/guides/LC05_Biomass_Soil_Fragmented_Forests.html
- SNIF, dados botânicos do IFN:
  https://snif.florestal.gov.br/pt-br/paineis-interativos/dados-botanicos-ifn-panorama
- Zenodo, EBA (mapa de AGB da Amazônia):
  https://doi.org/10.5281/zenodo.7647491

## 4. Harmonização necessária

| Item | Problema | Regra proposta |
|---|---|---|
| DAP mínimo | IFN Cerrado usa ≥10 cm; PLOS 2018 usa ≥5 cm; outros variam | registrar; filtrar para um mínimo comum na validação |
| Equação de AGB | cada fonte usa uma equação | recalcular quando houver dados por árvore; caso contrário, usar como referência da fonte, não como "verdade" |
| Densidade da madeira | nem sempre informada | usar GWDD e declarar |
| Coordenadas | 0,1° no painel SFB | validação regional; não parear pixel |
| Data | levantamentos em anos distintos | associar ao ano mais próximo e reportar defasagem |
| Componentes | AGB vs AGB+BGB vs incluindo necromassa | usar apenas AGB comparável |
| Unidades | kg ha⁻¹ vs Mg ha⁻¹ | converter explicitamente (÷1000) |

## 5. Uso previsto no projeto

1. **Validação independente** do mapa (fora do treino GEDI), por bioma e tipologia.
2. **Calibração** de equações de BGB quando houver dados de raiz.
3. **Benchmark** de plausibilidade (faixas por fitofisionomia).
4. **Priorização de campo** futuro (onde a cobertura é fraca).

## 6. Regra

Nenhuma fonte entra no treino e na validação ao mesmo tempo. Se uma fonte for usada no treino,
ela sai da validação independente e isso é registrado.

## 7. LiDAR e dados abertos da Embrapa (2026-11-25)

Estudo de consulta em [`docs/58_lidar_e_embrapa_abertos.md`](../../docs/58_lidar_e_embrapa_abertos.md)
(leitura; nada baixado). Resumo:

- **Embrapa:** sem banco de parcelas de campo aberto equivalente ao IFN (INV01). O que há é o
  WebGIS **Paisagens Sustentáveis** (LiDAR ALS de Amazônia/Cerrado/Mata Atlântica, cadastro
  gratuito, no ar) e o repositório **Redape** (coleção temática de biomassa, conteúdo não
  inspecionado).
- **LiDAR aberto com maior sinergia:** ORNL DAAC `10.3334/ORNLDAAC/1644` (nuvens ~10 pts/m² em
  tiles de 1 km² sobre sítios da Amazônia, 2008–2018) — mesmos sítios do inventário Sustainable
  Landscapes (INV03), que já estão geolocalizados em `ornl_sites_coords.csv`.
- **Auxiliares globais:** ICESat-2 ATL08 (novo) e GEDI (já em uso), sempre como camada
  auxiliar conforme ADR-0027/ADR-0022.
- **Não encontrado:** dataset aberto de LiDAR de drone; nuvens EBA/INPE com download confirmado.

Pendências: consultar Redape/catálogo Embrapa; testar download ORNL `1644`; verificar nuvens
EBA.
