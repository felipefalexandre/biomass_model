# 55 — Recuperação de coordenadas dos sítios ORNL

**Data:** 2026-11-24 · **Status:** concluído; 25 sítios geolocalizados.

## 1. Problema

Os CSVs de inventário do ORNL Sustainable Landscapes Brazil trazem UTM Easting/Northing, mas
não a zona/datum. Sem coordenadas, os 10 sítios-ano com AGB ficavam fora de validação espacial
e de qualquer treinamento com sensores.

## 2. Solução

O ORNL DAAC publica, para cada sítio/ano, um `inventory_plots.zip` com os transectos em
shapefile. Baixamos os 60 arquivos de 30 granules via Earthdata/`earthaccess`, extraímos os
shapefiles e calculamos o centroide médio dos transectos de cada sítio. O CRS do shapefile
também resolve a zona/datum UTM.

- Fonte: `https://doi.org/10.3334/ORNLDAAC/2007`
- Licença: NASA open data
- Saída: `data/reference/ornl_sites_coords.csv` (25 sítios)
- Manifesto: `data/manifests/ornl_plot_companions_*.json`

## 3. Comandos

```powershell
python -m biomass_model.cli ornl-plots --out-dir E:\Mapbiomas\biomass\fields\ornl_brazil\plots
python -m biomass_model.cli ornl-coords `
  --plots-dir E:\Mapbiomas\biomass\fields\ornl_brazil\plots `
  --out data\reference\ornl_sites_coords.csv
python -m biomass_model.cli inventory --source ornl `
  --path E:\Mapbiomas\biomass\fields\ornl_brazil `
  --coords data\reference\ornl_sites_coords.csv `
  --out E:\Mapbiomas\biomass\derived\observations_ornl.csv
```

## 4. Resultado

Os 10 sítios-ano com AGB agora têm geometria e entram na tabela canônica sem warnings:

| Sítio | Lon | Lat | AGB (Mg ha⁻¹) |
|---|---:|---:|---:|
| FNA_A01 | −55,019 | −12,501 | 10,09 |
| FST_A01 | −56,222 | −1,618 | 463,15 |
| JAM_A01 | −62,795 | −9,065 | 254,66 |
| JAM_A02 | −63,008 | −9,145 | 308,30 |
| SFX_A01 | −52,904 | −6,412 | 31,39 |
| SFX_A02 | −51,799 | −6,603 | 26,56 |
| TAN_A01 | −52,401 | −13,086 | 144,53 |
| TAP_A01 | −54,955 | −2,859 | 321,45 |
| TAP_A04 | −54,955 | −2,859 | 345,37 |
| TAP_A05 | −54,955 | −2,859 | 193,62 |

- `FST_A01` (463 Mg ha⁻¹) permanece marcado como outlier potencial (`agb_gt_400_check`).
- As coordenadas são centroides de sítio, não de parcela; servem para validação regional e
  pareamento com janelas de ~1 km, não para pixel a pixel.
- Os três arquivos TAP_A01/A04/A05 compartilham o mesmo centroide de sítio; anos e transectos
  diferentes, mas a mesma paisagem.

## 5. Próximos passos

1. Gerar features Landsat/DEM/ERA5 para os 10 sítios-ano.
2. Validar o modelo campo-first neles (Amazônia, 2009–2012).
3. Avaliar `FST_A01` e a exclusão de palmeiras/lianas.
4. Usar ORNL como validação independente, não como treino, até haver mais dados.

## 6. Artefatos

- `data/reference/ornl_sites_coords.csv` (25 sítios)
- `E:\Mapbiomas\biomass\fields\ornl_brazil\plots\` (30 zips + manifests)
- `E:\Mapbiomas\biomass\derived\observations_ornl.csv`
- `E:\Mapbiomas\biomass\inventory_store\observations.csv`
