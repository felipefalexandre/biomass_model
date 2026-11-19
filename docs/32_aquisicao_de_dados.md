# 32 — Aquisição de dados (pacote `biomass_model.datasets`)

Toda aquisição de dados do projeto é **código versionado do pacote**, não script solto. Cada
execução grava um **manifesto** em `data/manifests/` com parâmetros, URLs, hashes SHA-256, licença
e conta usada. Assim um terceiro consegue reproduzir o insumo sem depender de downloads manuais.

Substitui os antigos `tools/fetch_s2_pilot.py`, `tools/fetch_dem_pilot.py` e
`tools/fetch_era5_land.py` (removidos no commit de refatoração).

## Instalação

```powershell
python -m pip install -e ".[dev,data]"
python -m biomass_model.cli list
```

Dependências de aquisição (extra `data`): `pystac-client`, `cdsapi`, `earthaccess`. Leitura de
HDF5 (GEDI) usa o driver HDF5 do GDAL via `rasterio`; **não** é necessário `h5py`.

## Contas e credenciais

| Fonte | Conta | Onde fica a credencial |
|---|---|---|
| Sentinel-2 L2A (earth-search/AWS) | nenhuma | — |
| Copernicus DEM GLO-30 (AWS) | nenhuma | — |
| ERA5-Land (CDS) | conta gratuita no CDS | `~/.cdsapirc` |
| GEDI L4A (LP DAAC/ORNL) | Earthdata Login | `EARTHDATA_TOKEN` ou `~/.config/biomass_model/earthdata_token` |
| Sentinel-1 RTC (Microsoft Planetary Computer) | nenhuma | — (MPC assina o SAS) |

### Earthdata

1. Criar conta em <https://urs.earthdata.nasa.gov>.
2. Autorizar as aplicações **LP DAAC Data Pool** e **NASA GESDISC DATA ARCHIVE** em
   *Applications → Authorized Apps*.
3. Gerar token em *Applications → Generate Token*.
4. Salvar em `%USERPROFILE%\.config\biomass_model\earthdata_token` (uma linha, sem espaços) ou
   definir `EARTHDATA_TOKEN`. O arquivo está no `.gitignore` e tem ACL restrita.
5. Rotacionar o token periodicamente e **nunca** colar em issues/commits.

### CDS

1. Criar conta em <https://cds.climate.copernicus.eu>.
2. Copiar a URL e a chave da página *How to use the API* para `%USERPROFILE%\.cdsapirc`:

```
url: https://cds.climate.copernicus.eu/api
key: <UID>:<CHAVE>
```

## Comandos

Coordenadas dos boxes (ADR-0014/0016):

| Bioma | Box | Lon, Lat | Período GEDI |
|---|---|---|---|
| Amazônia | central | -60.45, -6.90 | 2019-2024 |
| Amazônia | leste (Tapajós) | -54.95, -3.15 | 2020-2024 |
| Amazônia | oeste (Acre) | -67.30, -9.40 | 2020-2024 |
| Amazônia | sul (PA/MT) | -53.00, -11.00 | 2020-2024 |
| Cerrado | central | -47.70, -13.95 | 2019-2024 |
| Cerrado | nordeste (MG) | -45.30, -16.70 | 2020-2024 |
| Cerrado | oeste (MT) | -52.20, -12.80 | 2020-2024 |
| Cerrado | floresta (MT) | -58.50, -12.00 | 2020-2024 |
| Cerrado | noroeste (BA) | -45.80, -12.50 | 2020-2024 |

Cada box usa ±0,08° (~17,8 km) para GEDI e 1600 px de 10 m para S2.

### Sentinel-2 L2A

### Sentinel-2 L2A

```powershell
python -m biomass_model.cli s2 --lon -60.45 --lat -6.90 `
  --start 2024-06-01 --end 2024-09-30 --out E:\Mapbiomas\biomass\pilots\amazonia_s2_2024.tif
```

- Janela centrada no ponto (`--size`, padrão 1600 px), cena de menor `eo:cloud_cover` no período.
- Bandas: `blue, green, red, nir, swir16, swir22` + `ndvi, ndmi, nirv` + `scl`.
- Sem conta; COGs públicos na AWS. Sidecar `.json` documenta a cena escolhida e os candidatos.

### Sentinel-2 composto (mediana multi-data)

```powershell
python -m biomass_model.cli s2-composite --lon -60.45 --lat -6.9 `
  --start 2019-01-01 --end 2024-12-31 --max-items 10 `
  --out E:\Mapbiomas\biomass\pilots\amazonia_s2comp_2019_2024.tif
```

Mediana das N cenas menos nubladas (mesmo tile), com máscara SCL por cena; bandas e índices
medianos + `nobs` (número de observações válidas). No piloto amazônico não superou uma data única
em R² no footprint (`docs/25`, `docs/31`), mas serve para composições sazonais futuras e para
reduzir buracos de nuvem no mapa. Manifesto `s2_composite`.

### Copernicus DEM GLO-30

```powershell
python -m biomass_model.cli dem --lon -60.45 --lat -6.90 `
  --out E:\Mapbiomas\biomass\pilots\amazonia_dem30.tif
```

Mosaico `--half` graus em torno do ponto (padrão 0,08°), EPSG:4326, nodata 0. Sem conta.

### ERA5-Land mensal

```powershell
python -m biomass_model.cli era5 --lon -60.45 --lat -6.90 `
  --start-year 2018 --end-year 2025 --out E:\Mapbiomas\biomass\pilots\amazonia_era5land_2018_2025.nc
```

8 variáveis mensais (temperatura, precipitação, evaporação potencial, radiação solar, umidade do
solo em 4 camadas), grade `0.1° × 0.1°`. Exige `download_format: unarchived` (o script já envia).

### GEDI L4A

```powershell
python -m biomass_model.cli gedi --west -60.53 --south -6.98 --east -60.37 --north -6.82 `
  --start 2019-01-01 --end 2024-12-31 `
  --out E:\Mapbiomas\biomass\gedi\piloto_amazonia.csv `
  --work-dir E:\Mapbiomas\biomass\gedi\h5
```

- Busca via CMR (`earthaccess.search_data`), baixa para `--work-dir` e extrai in-place.
- Versões: `V2_1` (padrão, `GEDI_L4A_AGB_Density_V2_1_2056`) e `V3`
  (`GEDI_L4A_AGB_Density_V3_2508`).
- Filtro de qualidade padrão e justificativa em `ADR/0012`; `--min-sensitivity` ajusta o limite.
- Saída: CSV por footprint com `agbd`, incerteza (`agbd_se`, PI), qualidade, `sensitivity`,
  coordenadas, `degrade_zero`, `granule` e `granule_time`.

### Sítios de campo (Cerrado)

```powershell
python -m biomass_model.cli sites-fetch --csv data\reference\plos2018_sites.csv `
  --out-dir E:\Mapbiomas\biomass\fields\plos2018 --start 2024-05-01 --end 2024-10-31
```

Baixa uma janela S2 de 4 km e um DEM de ~4 km por sítio (75 sítios do PLOS 2018), com um manifesto
agregado. Depois:

```powershell
python -m biomass_model.cli era5-bbox --west -57 --south -20 --east -41 --north -3 `
  --start-year 2019 --end-year 2024 --out E:\Mapbiomas\biomass\era5\cerrado_era5land_2019_2024_bbox.nc
python -m biomass_model.cli field-table --sites data\reference\plos2018_sites.csv `
  --work-root E:\Mapbiomas\biomass\fields\plos2018 `
  --era5 E:\Mapbiomas\biomass\era5\cerrado_era5land_2019_2024_bbox.nc `
  --mapbiomas-dir E:\Mapbiomas --out E:\Mapbiomas\biomass\derived\cerrado_field_plos2018.csv
python -m biomass_model.cli field-baseline --csv E:\Mapbiomas\biomass\derived\cerrado_field_plos2018.csv `
  --out-dir E:\Mapbiomas\biomass\derived\cerrado_field_baseline
```

### Sentinel-1 RTC (Microsoft Planetary Computer)

Coleção `sentinel-1-rtc` do STAC do MPC; COGs assinados pelo pacote
`planetary-computer`, **sem conta**. Composição por mediana em potência linear e conversão para
dB; 5 bandas: `vv_db`, `vh_db`, `vh_vv_db` (razão), `rvi` e `nobs`.

```powershell
python -m biomass_model.cli s1 --lon -60.45 --lat -6.90 `
  --start 2024-05-01 --end 2024-10-31 --max-items 8 `
  --out E:\Mapbiomas\biomass\pilots\amazonia_s1_2024.tif
```

Saída tem ~1600 px de 10 m (16 km). O treino aceita `--s1 <tif>` para anexar as bandas como
features `s1_*`.

### Landsat C2 L2 (sítios de campo antigos)

Mesma rota MPC (`landsat-c2-l2`), sem conta. Janela de 1 km em 30 m, mediana de cenas em
±45 dias da data do inventário, máscara de nuvem por `qa_pixel` e reflectância
`DN*0.0000275 − 0.2`. Necessário porque os inventários do PLOS 2018 são de 1988–2014.

```powershell
python -m biomass_model.cli landsat --lon -47.61692 --lat -15.18033 `
  --date 2012-09-01 --out E:\Mapbiomas\biomass\fields\plos2018\site_001\landsat_2012.tif
python -m biomass_model.cli landsat-sites --sites data\reference\plos2018_sites.csv `
  --out-dir E:\Mapbiomas\biomass\fields\plos2018 --year-start 2004 --year-end 2014
python -m biomass_model.cli landsat-field-table --sites data\reference\plos2018_sites.csv `
  --work-root E:\Mapbiomas\biomass\fields\plos2018 `
  --era5 E:\Mapbiomas\biomass\era5\cerrado_era5land_2019_2024_bbox.nc `
  --mapbiomas-dir E:\Mapbiomas `
  --out E:\Mapbiomas\biomass\derived\cerrado_field_landsat.csv
```

Datas sujas do PLOS (`2010`, `Mar/Apr- 2008`) são normalizadas; só 2004–2014 entra porque o
MapBiomas/Collection 11 local começa em 2004.

### MapBiomas

MapBiomas Coleção 11 já está local em `E:\Mapbiomas` (`mapbiomas_col11_*.tif` e
`Biomas_250mil\lm_bioma_250.shp`); a aquisição/reprodutibilidade desses arquivos ainda não está
automatizada no pacote.

## Manifestos

`data/manifests/<dataset>_<UTC>.json`:

```json
{
  "dataset": "gedi",
  "created_at": "2026-11-18T01:00:00+00:00",
  "git_commit": "...",
  "params": {"bbox": [...], "start": "...", "version": "V2_1"},
  "license": "NASA (aberto, atribuicao)",
  "account": "Earthdata Login + token + app LP DAAC autorizada",
  "source": "https://doi.org/10.5067/GEDI/GEDI04_A.002",
  "outputs": [{"path": "...", "bytes": 123, "sha256": "..."}]
}
```

Manifestos são pequenos e **vão para o git**; os dados brutos não.

## Licenças

| Fonte | Licença | Observação |
|---|---|---|
| Sentinel-2 | Copernicus data policy | atribuição |
| Copernicus DEM | Copernicus DEM, aberto | atribuição |
| ERA5-Land | Copernicus C3S | atribuição; não redistribuir como produto próprio sem checar termos |
| GEDI L4A | NASA, aberto | atribuição e citação do DOI |
| Landsat C2 L2 | USGS, aberto | atribuição |
| MapBiomas | CC BY-SA | *share-alike*: confirmar efeito em produto derivado |

## Limitações conhecidas

- `h5py` não compila no Python 3.15 deste ambiente; a leitura HDF5 via GDAL/rasterio é o caminho
  suportado (`HDF5:"arquivo"://BEAM0000/agbd`).
- Granulos noturnos de 2021/2022 no piloto amazônico não têm predição L4A válida no bbox
  (`l2=0`, `l4=0`, `agbd=-9999`); ver `ADR/0012`.
- `earthaccess` 0.19: usar `search_data(count=-1, ...)`; `count=True` e `page_size` causam erro de
  paginação.
- A cena S2 é um instantâneo; o produto final deve usar composições sazonais (ver `docs/15`).
