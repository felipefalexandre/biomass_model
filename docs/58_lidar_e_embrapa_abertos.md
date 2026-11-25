# 58 — LiDAR e dados abertos da Embrapa (estudo de consulta)

**Status:** estudo somente leitura, 2026-11-25. Nenhum dado foi baixado e nenhum código foi alterado.
**Origem:** pedido da gestão (item 5 das perguntas de escopo) — "estudar a Embrapa e
inventários/datasets de LiDAR que estejam abertos para consulta".
**Registro complementar:** `data/reference/inventarios_abertos.md` (seção 7).

Legenda de verificação:

- **✅ verificado** — página acessada/URL confirmada nesta data;
- **⚠️ pendente** — referência encontrada em busca, mas conteúdo não inspecionado;
- **hipótese** — dedução, não confirmada.

---

## 1. Embrapa

| Fonte | Conteúdo | Acesso | Status |
|---|---|---|---|
| **Redape** — Repositório de Dados de Pesquisa da Embrapa, `https://www.redape.dados.embrapa.br/` | Repositório FAIR com coleção temática de **biomassa** entre as nove categorias | aberto | ⚠️ portal existe (confirmado em `embrapa.br/dados-de-pesquisa` e `gov.br`); **datasets de biomassa/parcelas não inspecionados** |
| **WebGIS Paisagens Sustentáveis** — `https://www.paisagenslidar.cnptia.embrapa.br/webgis` | **LiDAR aerotransportado (ALS)** da Amazônia, Cerrado e Mata Atlântica; projeto Embrapa + USFS (Michael Keller, Labex), desde 2011 | gratuito **mediante cadastro** | ✅ no ar em 2026-11-25 (retorna tela "Tipo do dado: Lidar Forest Inventory / Estados") |
| Catálogo de dados — `https://dados.embrapa.br/catalogue/` | Catálogo geral de dados Embrapa | aberto | ⚠️ citado em publicação da Embrapa; busca por "biomassa" **pendente** |
| Protocolo Doc. 266 — *Protocolo de medição e estimativa de biomassa e carbono florestal* (`infoteca.cnptia.embrapa.br`) | Metodologia de campo e equações | aberto | ✅ existe; é referência de **método**, não dataset de parcelas |

### 1.1 Leitura

- A gestão citou a Embrapa como fonte de valores de biomassa. O levantamento **não encontrou**
  um banco de parcelas de campo aberto da Embrapa equivalente ao Painel de Biomassa do SFB/IFN
  (INV01). O que a Embrapa oferece de consulta aberta é, até aqui: (a) **LiDAR** via WebGIS
  Paisagens Sustentáveis e (b) dados de pesquisa no Redape.
- **Hipótese (não verificada):** o Redape pode conter conjuntos de parcelas de Cerrado
  (Embrapa Cerrados/Recursos Genéticos) que ajudariam no gap de campo do Cerrado. Depende de
  consulta ao catálogo.
- **Restrição de acesso:** o WebGIS exige cadastro e é interativo — pode não ser automatizável
  como os fetchers de `src/biomass_model/datasets/`; caso avancemos, prever download manual +
  adaptador (mesmo padrão de PLOS/ORNL).

## 2. Datasets de LiDAR abertos

### 2.1 Brasil

| # | Dataset | Conteúdo | Acesso | Status |
|---|---|---|---|---|
| L1 | **ORNL DAAC — "LiDAR Surveys over Selected Forest Research Sites, Brazilian Amazon, 2008–2018"** (dos-Santos et al. 2019, DOI `10.3334/ORNLDAAC/1644`, guia `daac.ornl.gov/CMS/guides/LiDAR_Forest_Inventory_Brazil.html`) | Nuvens de pontos ~10 pts/m² em tiles de 1 km² sobre sítios de pesquisa da Amazônia, 2008–2018 (programa Sustainable Landscapes Brazil) | Earthdata (token já configurado no ambiente, ver `HANDOFF` §2) | ✅ guia/dataset documentados; download **não testado** |
| L2 | **Embrapa — WebGIS Paisagens Sustentáveis** (§1) | ALS de Amazônia, Cerrado e Mata Atlântica | cadastro gratuito | ✅ no ar; download **não testado** |
| L3 | **EBA/INPE — transectos LiDAR** (`ccst.inpe.br/projetos/eba-estimativa-de-biomassa-na-amazonia/`) | 836+ transectos LiDAR usados no mapa EBA; mapa disponível no Zenodo (`10.5281/zenodo.7647491`, já INV10) | página do projeto existe | ⚠️ **disponibilidade das nuvens de pontos não verificada** |
| L4 | **OpenTopography** (`portal.opentopography.org`) | Repositório global com coleções brasileiras (ex.: São Paulo 2017) | aberto | ✅ conhecido; baixa relevância para floresta |
| L5 | **Projeto Amazônia Revelada / LiDAR citado pelo MapBiomas** | LiDAR aerotransportado usado em notas técnicas do MapBiomas (BR319) | não claro | ⚠️ **não confirmado como dataset aberto para download** |

### 2.2 Globais (camada auxiliar — ADR-0027)

| # | Dataset | Conteúdo | Uso previsto |
|---|---|---|---|
| G1 | **ICESat-2 ATL08** (NSIDC, versão 7) | Altura de terreno e copa em segmentos de 100 m | observação estrutural **auxiliar** de calibração/avaliação; nunca variável de inferência |
| G2 | **GEDI L2A/L2B/L4A** | Footprints de altura/AGB | já em uso no repo (ADR-0022: só calibração/avaliação) |
| G3 | **AWS Open Data — coleção open-lidar** (`registry.opendata.aws/open-lidar-data/`) | Agregador global de nuvens de pontos | cobertura brasileira irregular; consulta pontual |

### 2.3 NÃO encontrado

- **LiDAR de drone** (censo "drone voando a parcela" citado pela gestão): **não existe dataset
  aberto** no levantamento. Todos os abertos são aerotransportados (ALS) ou de satélite.
  Drone seria dado próprio do projeto, se existir aquisição própria.
- **Dataset Embrapa de parcelas de campo aberto equivalente ao IFN:** não encontrado.

## 3. Implicação para a hierarquia de referência (ADR-0027)

- LiDAR **pareado com campo** entra como **referência secundária com suporte, erro e origem
  documentados** — não como verdade. O esquema canônico já prevê `observation_type` distinto.
- Candidato prioritário de pareamento: **L1 (ORNL LiDAR) + INV03/ORNL Sustainable Landscapes**,
  porque campo e LiDAR coincidem nos mesmos sítios — já ingeridos no store
  (`HANDOFF` §10.2). **Hipótese:** é o caminho mais curto para a "equação sensor × campo"
  citada pela gestão; depende de teste de download e extração de métricas.
- GEDI e ICESat-2 permanecem auxiliares, sem uso como variável/prior na inferência.

## 4. Próximos passos (não executados)

1. Consultar Redape e `dados.embrapa.br/catalogue` por datasets de biomassa/parcelas.
2. Testar download do L1 (ORNL `1644`) com o token Earthdata existente; avaliar densidade,
   cobertura sobre os 25 sítios geolocalizados (`data/reference/ornl_sites_coords.csv`) e
   tamanho em disco antes de qualquer ingestão.
3. Verificar disponibilidade das nuvens EBA (L3) junto ao CCST/INPE.
4. Se positivo: registrar as fontes em `data/reference/inventarios_abertos.md` e decidir
   adaptador em `datasets/` + esquema canônico (`observation_type = lidar`).
5. Confirmar com a gestão se há aquisição própria de LiDAR de drone no projeto (fora de
   dados abertos).

## 5. Método

Buscas web (2026-11-25) por "Embrapa dados abertos biomassa", "Embrapa SGB parcelas",
"dados LiDAR abertos Brasil", "Paisagens Sustentáveis download", "ORNL DAAC LiDAR Brazilian
Amazon", "Redape biomassa", "ICESat-2 ATL08 Brasil", "EBA INPE LiDAR dados abertos",
"MapBiomas LiDAR". Acesso direto ao WebGIS da Embrapa. Nenhum download, login ou execução de
código de ingestão foi realizado.
