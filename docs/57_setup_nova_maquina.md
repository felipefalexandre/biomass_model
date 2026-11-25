# 57 — Setup em nova máquina e retomada do zero

**Data:** 2026-11-24 · **Objetivo:** permitir clonar o repositório em outra máquina, instalar,
testar e continuar o trabalho sem depender do estado local desta máquina.

## 1. O que vem no git e o que não vem

**Versionado:**
- código em `src/biomass_model/`;
- testes em `tests/`;
- documentação em `docs/`, ADRs, `README.md`, `HANDOFF.md`;
- catálogo, matriz de evidências, crosswalks e referências pequenas em `data/reference/`;
- manifestos de downloads em `data/manifests/`.

**Não versionado (`.gitignore`):**
- `data/raw/` — PLOS, IFN, CEDA e outros brutos;
- `*.tif`, `*.gpkg`, `*.shp`, `*.parquet`, etc.;
- dados derivados, modelos `.joblib`, predições e mapas;
- credenciais (`.cdsapirc`, token Earthdata).

Sem os dados externos, os **testes automatizados continuam passando** (usam dados sintéticos).
Os experimentos científicos, mapas e validações exigem baixar/fornecer os dados externos.

## 2. Requisitos

- Python **3.11+** (testado em 3.15 no Windows).
- Git.
- Espaço em disco: ~1–2 GB para código/testes; vários GB para MapBiomas e derivados.
- Conta Earthdata (gratuita) para ORNL e GEDI.
- Conta CDS (gratuita) para ERA5-Land.
- Opcional: `pyarrow` para Parquet.

## 3. Instalação

```bash
git clone https://github.com/felipefalexandre/biomass_model.git
cd biomass_model
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[dev,ml,data,inventory]"
```

`parquet` é um extra separado:

```bash
python -m pip install -e ".[parquet]"
```

Verificação rápida:

```bash
python -c "import rasterio, geopandas, sklearn, openpyxl; print('ok')"
python -m pytest -q
```

Esperado no estado atual: **60 passed** (os testes não dependem dos dados externos).
Se `python -m pytest` não achar o pacote, rode com `PYTHONPATH=src` (Windows:
`$env:PYTHONPATH="src"`).

## 4. Credenciais (nunca commitar)

### Earthdata

1. Crie conta em <https://urs.earthdata.nasa.gov>.
2. Autorize as aplicações necessárias (LP DAAC/ORNL DAAC) em *Authorized Apps*.
3. Gere um token e salve em:

```text
%USERPROFILE%\.config\biomass_model\earthdata_token
```

ou defina `EARTHDATA_TOKEN`.

### CDS / ERA5

Crie `~/.cdsapirc`:

```text
url: https://cds.climate.copernicus.eu/api
key: <UID>:<CHAVE>
```

## 5. Dados externos necessários

### 5.1 MapBiomas Coleção 11

Necessário: arquivos anuais `mapbiomas_col11_YYYY.tif` e o limite de biomas
(`Biomas_250mil/lm_bioma_250.shp`). Não há downloader no pacote; copie do armazenamento do
projeto ou baixe do MapBiomas respeitando a licença CC BY-SA.

Os comandos abaixo usam `E:\Mapbiomas` como exemplo; substitua pelo seu caminho.

### 5.2 PLOS 2018

- Fonte: <https://doi.org/10.1371/journal.pone.0196742> (CC BY).
- Coloque `s003.xlsx` em `data/raw/inventarios/plos2018/`.
- Ingestão:

```bash
python -m biomass_model.cli inventory --source plos2018 \
  --path data/raw/inventarios/plos2018/s003.xlsx \
  --out <root>/derived/observations_plos2018.csv
```

### 5.3 IFN/SFB

- Fonte: Painel de Biomassa e Carbono (SFB), CSV `biomassa.csv` (CC BY).
- Coloque em `data/raw/inventarios/sfb/biomassa.csv`.
- Ingestão:

```bash
python -m biomass_model.cli inventory --source ifn \
  --path data/raw/inventarios/sfb/biomassa.csv \
  --out <root>/derived/observations_ifn.csv
```

### 5.4 CEDA/NCEO Manaus 2014

```bash
python -m biomass_model.cli ceda-manaus --out-dir <root>/fields/ceda_manaus
python -m biomass_model.cli inventory --source ceda \
  --path <root>/fields/ceda_manaus/Manaus2014_Plots100x60m_AGB.shp \
  --out <root>/derived/observations_ceda.csv
```

### 5.5 ORNL Sustainable Landscapes Brazil

```bash
python -m biomass_model.cli ornl-plots --out-dir <root>/fields/ornl_brazil/plots
python -m biomass_model.cli ornl-coords \
  --plots-dir <root>/fields/ornl_brazil/plots \
  --out data/reference/ornl_sites_coords.csv
python -m biomass_model.cli inventory --source ornl \
  --path <root>/fields/ornl_brazil \
  --coords data/reference/ornl_sites_coords.csv \
  --out <root>/derived/observations_ornl.csv
```

Os CSVs de inventário ORNL devem estar em `<root>/fields/ornl_brazil/` (o `inventory` varre
`*nventory*.csv`). O comando `ornl-plots` baixa os shapefiles de transectos via Earthdata.

### 5.6 IBGE vegetação 1:250.000

```bash
python -m biomass_model.cli ibge-vegetacao --out-dir <root>/ibge/versao_2026 --version 2026
```

Gera `vege_area.zip` e extrai `areas/vege_area.shp`.

## 6. Store canônico

O store é idempotente e protegido por lock. Ordem recomendada (sequencial):

```bash
python -m biomass_model.cli inventory-store --source plos2018 --path data/raw/inventarios/plos2018/s003.xlsx --store <root>/inventory_store
python -m biomass_model.cli inventory-store --source ifn --path data/raw/inventarios/sfb/biomassa.csv --store <root>/inventory_store
python -m biomass_model.cli inventory-store --source ornl --path <root>/fields/ornl_brazil --coords data/reference/ornl_sites_coords.csv --store <root>/inventory_store
python -m biomass_model.cli inventory-store --source ceda --path <root>/fields/ceda_manaus/Manaus2014_Plots100x60m_AGB.shp --store <root>/inventory_store
```

Estado esperado: **7.576 observações** (IFN 7.466, PLOS 77, CEDA 23, ORNL 10).

## 7. Reproduzir os experimentos principais

### 7.1 Features PLOS + modelo Cerrado F0

```bash
python -m biomass_model.cli features-observations \
  --observations <root>/derived/observations_plos2018.csv \
  --out <root>/derived/plos2018_features_landsat.csv \
  --optical-dir <root>/fields/plos2018 \
  --optical-pattern "site_{site_int:03d}/landsat_{year}.tif" \
  --dem-dir <root>/fields/plos2018 \
  --dem-pattern "site_{site_int:03d}/dem.tif" \
  --era5 <root>/era5/cerrado_era5land_2019_2024_bbox.nc \
  --mapbiomas-dir <root> --history-start 2004 --history-end 2018

python -m biomass_model.cli train-field \
  --csv <root>/derived/plos2018_features_landsat.csv \
  --out-dir <root>/derived/field_plos2018_rf_block200 \
  --block-size-m 200000 --buffer-m 25000 --domain-classes 3,4
```

As janelas Landsat/DEM por sítio PLOS podem ser obtidas com:

```bash
python -m biomass_model.cli sites-fetch --csv data/reference/plos2018_sites.csv \
  --out-dir <root>/fields/plos2018 --start 2024-05-01 --end 2024-10-31
python -m biomass_model.cli landsat-sites --sites data/reference/plos2018_sites.csv \
  --out-dir <root>/fields/plos2018 --year-start 2004 --year-end 2014
```

### 7.2 Validação CEDA/ORNL

```bash
python -m biomass_model.cli features-observations \
  --observations <root>/derived/observations_ceda.csv \
  --out <root>/derived/ceda_manaus_features_landsat.csv \
  --optical-dir <root>/fields/ceda_manaus_landsat \
  --optical-pattern "site_{site_int:03d}/landsat_{year}.tif" \
  --dem-dir <root>/fields/ceda_manaus_landsat \
  --dem-pattern "site_{site_int:03d}/dem.tif" \
  --era5 <root>/era5/manaus_era5land_2019_2024_bbox.nc \
  --mapbiomas-dir <root> --history-start 2004 --history-end 2018

python -m biomass_model.cli predict-field \
  --model <root>/derived/field_plos2018_rf_block200_nocat.joblib \
  --csv <root>/derived/ceda_manaus_features_landsat.csv \
  --out <root>/derived/ceda_manaus_pred_rf_block200_nocat.csv
```

Os resultados atuais (negativos) estão em `docs/47`, `docs/51` e `docs/56`.

### 7.3 Produto C

```bash
python -m biomass_model.cli polygon \
  --input <poligono>.geojson \
  --raster <mapa_agb_30m>.tif \
  --aoa-band 4 \
  --fitofisionomia-raster <fitofisionomia_30m>.tif \
  --fitofisionomia-codes <fitofisionomia>.json \
  --fitofisionomia-groups forest,savanna,campestre \
  --out <relatorio>.json
```

## 8. Regenerar fitofisionomia e reconciliação

```bash
python -m biomass_model.cli fitofisionomia \
  --vector <root>/ibge/versao_2026/areas/vege_area.shp \
  --template <raster>.tif --attribute legenda_2 --out <fit>.tif

python -m biomass_model.cli fitofisionomia-reclassify --codes <fit>.json
python -m biomass_model.cli fitofisionomia-reconcile \
  --fit-raster <fit_30m>.tif --mapbiomas-raster <root>/mapbiomas_col11_2021.tif \
  --codes <fit>.json --classes 3,4 --out <root>/derived/reconcile.csv
```

## 9. Testes e estado esperado

```bash
python -m pytest -q
```

- 60 testes no estado desta versão.
- Não requerem `E:\Mapbiomas` nem credenciais.
- Testes de aquisição/adaptação usam arquivos sintéticos.

## 10. Onde continuar

Leia, nesta ordem:

1. `HANDOFF.md` (estado e comandos);
2. `docs/46` (auditoria e plano);
3. `docs/47` (model card campo-first);
4. `docs/51`/`56` (falhas de transferência entre biomas);
5. `docs/55` (coordenadas ORNL);
6. `docs/52` (store canônico);
7. `docs/53`/`54` (Produto C e reconciliação).

Próximos passos científicos:

1. Construir um modelo amazônico com CEDA + ORNL e validação leave-one-source/region-out.
2. Buscar mais inventários amazônicos independentes (RAINFOR, novos campos).
3. Alinhar features Landsat/S2 antes de gerar mapa 30 m campo-first.
4. Completar critérios de aceite e portões G0–G7.

## 11. Problemas comuns

- **`h5py` não instala:** o GEDI é lido via GDAL/rasterio; não instale h5py.
- **PowerShell/UTF-8:** o console pode exibir mojibake; os arquivos do git são UTF-8. Evite
  `Set-Content` com BOM; use as ferramentas do projeto ou `UTF8Encoding($false)`.
- **CDS lento:** ERA5 pode demorar; use `--start-year/--end-year` mínimos.
- **Earthdata 401/403:** verifique token e autorização das aplicações LP DAAC/ORNL DAAC.
- **Caminhos `E:\`:** todos os comandos são exemplos; adapte ao seu filesystem.
- **pyarrow ausente:** use CSV; Parquet é opcional (`.[parquet]`).

## 12. Regras de ouro

- Nunca commitar credenciais, `data/raw` ou dados volumosos.
- Preservar resultados anteriores; novas versões não sobrescrevem as antigas.
- Registrar decisões em ADR e atualizar `HANDOFF.md`.
- Não promover modelo a champion sem validação independente e critérios de `docs/37`.
- Não chamar o produto de MRV enquanto G0–G7 não estiverem completos.
