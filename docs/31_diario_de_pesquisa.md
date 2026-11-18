# 31 — Diário de pesquisa

Registro cronológico do que foi feito, decidido e descoberto. Complementa os ADRs (decisões) e
`docs/30` (pendências).

## 2026-11-17 — Sessão 1

### Decisões recebidas do usuário

1. Piloto: um tile pequeno por bioma, escolhido por nós, desde que tenha biomassa real.
2. Anos: intervalo de anos, preferencialmente recentes, para comparar com inventários, bases
   abertas e artigos.
3. Começar por AGB; BGB como modelo separado, focado em solo, acoplado (não derivado).
4. Dados e intermediários em `E:\Mapbiomas\biomass`.
5. Domínio: classes 3 e 4 do MapBiomas, Amazônia e Cerrado; estratificação por vegetação é
   desejável.
6. Referência obrigatória: legenda MapBiomas Coleção 11 e códigos IBGE de vegetação.
7. Inventários: buscar dados abertos e armazenar em pasta de referência.
8. Dúvidas não respondidas: seguir o padrão dos docs/ADRs.

### O que foi feito

- Download da legenda oficial Coleção 11 (PDF + texto extraído).
- Download do Painel de Biomassa e Carbono do SFB (IFN): `biomassa.csv` (53 MB, 439.970
  registros), `equacoes.csv`, `metadados.pdf`.
- Download dos suplementos S3–S5 do artigo de Cerrado (PLOS ONE 2018, DOI
  10.1371/journal.pone.0196742).
- Criação de `data/reference/inventarios_abertos.md` e `.csv` (10 fontes catalogadas).
- Ferramenta `tools/suggest_pilots_from_ifn.py`: cruza adensamento do IFN com fração de classes
  3/4 do MapBiomas.
- Seleção dos pilotos:
  - Amazônia: lon −60,45, lat −6,90; 512 px; 93,3% classe 3; 511 UAs do IFN na célula.
  - Cerrado: lon −47,70, lat −13,95; 512 px; 79,1% classes 3+4 (25,6% + 53,6%); 605 UAs.
- Scaffolding: `pyproject.toml`, `src/biomass_model/grid.py`, `tests/test_grid.py` (5 testes
  passando), `tools/select_pilots.py`.

### Achados

- O painel do SFB é aberto e tem coordenadas (~0,1°) e AGB por unidade amostral — serve para
  validação regional, não para pareamento pixel a pixel.
- Estatísticas calculadas por nós no CSV do SFB: Amazônia 151,6 Mg ha⁻¹ (média) / 112,0
  (mediana); Cerrado 33,9 / 19,4. A diferença média–mediana mostra distribuição assimétrica;
  não usar a média como "valor do bioma".
- O cluster do IFN em −60,45/−6,90 tem alta fração de floresta e muitas UAs; é melhor piloto
  amazônico do que Belterra, que não tinha UA do IFN em 50 km.
- A legenda confirma 3 = Formação Florestal e 4 = Formação Savânica; a distribuição empírica
  confirma (3 domina a Amazônia; 4 domina o Cerrado).

### Pendências geradas

- Baixar (ou obter via login gratuito) os inventários INV03–INV10.
- Harmonizar equações e DAP mínimo antes de qualquer validação.
- Definir o recorte temporal do piloto (ex.: 2018–2025) e a referência GEDI correspondente.
- Confirmar licença exata do MapBiomas e decidir licença dos produtos.

### Próximo passo

Fase 1: montar o cubo de features (S2, S1, DEM, clima) e extrair GEDI L4A nos dois tiles,
com validação espacial por blocos desde o início.

## 2026-11-17 — Sessão 2

### Credenciais e acessos

- CDS API configurada em `~/.cdsapirc`; teste de ERA5-Land mensal (2018–2025) **bem-sucedido**.
- Descoberta importante: Sentinel-2 L2A é acessível **sem conta** via `earth-search` STAC +
  COGs públicos na AWS. Testado nos dois pilotos.
- Copernicus DEM GLO-30 também é público na AWS (`copernicus-dem-30m`), sem conta.
- Pendente: token Earthdata (GEDI via LP DAAC; Sentinel-1 RTC via ASF) e autorização das
  aplicações no perfil Earthdata.

### Ferramentas novas

- `tools/fetch_s2_pilot.py` — janela de 1600 px (16 km a 10 m), 6 bandas + NDVI/NDMI/NIRv + SCL.
- `tools/fetch_dem_pilot.py` — mosaico GLO-30 recortado.
- `tools/fetch_era5_land.py` — médias mensais de 8 variáveis.

### Artefatos gerados (fora do git, em `E:\Mapbiomas\biomass\pilots\`)

- `amazonia_s2_2024.tif` (50,9 MB; cena 20240720, 0% nuvem; NDVI mediano 0,86).
- `cerrado_s2_2024.tif` (54,4 MB; cena 20240819, 0% nuvem; 97,9% válido).
- `amazonia_dem30.tif` e `cerrado_dem30.tif` (576×576; ~26–175 m e 0–1525 m).
- `amazonia_era5land_2018_2025.nc` (105 kB; 8 variáveis mensais).

### Observações técnicas

- A janela S2 precisa ser calculada em coordenadas UTM (o tile é EPSG:32720/32723), não em
  lat/lon; o erro inicial foi corrigido com `pyproj`.
- A cena de 2024 é um instantâneo; o produto final deve usar composições sazonais (mediana e
  percentis), não uma única data.
- O DEM do Cerrado tem 0,17% de zeros na costura entre tiles (tratados como nodata).

### Próximo passo

Obter token Earthdata, validar acesso a GEDI L4A e Sentinel-1 RTC; em paralelo, implementar
composição sazonal S2 e o alinhamento à grade comum de 30 m.
## 2026-11-17 — Sessão 3

### Refatoração para o pacote

- A aquisição deixou de ser script solto: src/biomass_model/datasets/{s2,dem,era5,gedi}.py, com
  credentials.py, manifest.py, catalog.py e cli.py; comandos python -m biomass_model.cli.
- 	ools/fetch_s2_pilot.py, 	ools/fetch_dem_pilot.py e 	ools/fetch_era5_land.py removidos.
- Todo download grava manifesto com parâmetros, URLs, hashes, licença e conta em
  data/manifests/; documentação em docs/32.
- ADRs novos: 0012 (filtro GEDI), 0013 (grade e amostragem), 0014 (escala do piloto, ±0,08°).

### GEDI L4A: extração validada

- Busca por CMR e leitura HDF5 via driver GDAL (asterio), sem h5py (não compila no Python
  3.15).
- Extração nos 6 grânulos de teste do piloto amazônico: 3.361 footprints válidos; AGB mediana
  192,6 Mg ha⁻¹; 69% com degrade_flag == 0. Grânulos noturnos de 2021 e 2022 não têm predição
  válida no bbox (0 footprints), como já indicado na sondagem.
- Filtro adotado: l2==1 & l4==1 & agbd>=0 & 0,9<=sensitivity<=1,01; degrade_flag é mantido
  como covariável e há sensibilidade restrita (ADR-0012).

### Próximo passo

- Rodar a extração GEDI em lote nos dois pilotos, montar o stack de features na grade de 30 m e a
  tabela de treino; baseline com CV por blocos espaciais.
