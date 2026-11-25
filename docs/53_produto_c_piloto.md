# 53 — Produto C: piloto de estimativa por polígono (30 m)

**Data:** 2026-11-24 · **Status:** piloto funcional; não é produto MRV.

## 1. Objetivo

Demonstrar o Produto C (polígono arbitrário) com geometria real, área de interseção, incerteza,
AOA e individualização por fitofisionomia, usando o mapa AGB 30 m existente (baseline A0 GEDI,
Cerrado central 2021) e a fitofisionomia IBGE 1:250.000.

## 2. Entrada

- **Mapa AGB:** `derived\maps\cerrado_central_agb_2021_30m_aoa_ic.tif`
  - bandas: `agbd_mg_ha` (1), `domain_mask` (2), `s2_valid_fraction` (3), `aoa_inside` (4),
    `aoa_distance` (5), `agbd_lo90` (6), `agbd_hi90` (7).
  - resolução 30 m; EPSG:32722.
- **Fitofisionomia:** `derived\fitofisionomia_cerrado_central_2021_30m.tif` (IBGE 2026,
  `legenda_2`, reamostrada para a grade de 30 m por vizinho mais próximo).
- **Polígono:** quadrado de 5 × 5 km em EPSG:32722
  (`derived\polygon_piloto_cerrado_central.geojson`).

## 3. Comando

```powershell
python -m biomass_model.cli polygon `
  --input derived\polygon_piloto_cerrado_central.geojson `
  --raster derived\maps\cerrado_central_agb_2021_30m_aoa_ic.tif `
  --aoa-band 4 `
  --fitofisionomia-raster derived\fitofisionomia_cerrado_central_2021_30m.tif `
  --fitofisionomia-codes derived\fitofisionomia_cerrado_central_2021.json `
  --n-boot 200 --out derived\polygon_piloto_cerrado_central.json
```

## 4. Resultado

| Item | Valor |
|---|---:|
| Área do polígono | 2.500,0 ha |
| Área analisada (AGB válida) | 2.217,7 ha (88,7%) |
| Área excluída | 282,3 ha |
| AGB média | 14,02 Mg ha⁻¹ |
| AGB mediana | 9,87 Mg ha⁻¹ |
| Estoque total | 31.089 Mg (0,031 Tg) |
| IC90 do total | 29.217–47.598 Mg |
| Fração na AOA | 84,1% |
| Células / blocos | 24.742 / 4 |

### Por fitofisionomia IBGE

| Classe | Área (ha) | AGB média | AGB mediana | Estoque (Mg) |
|---|---:|---:|---:|---:|
| Pecuária (pastagens) | 869,0 | 11,83 | 8,98 | 10.284 |
| Savana Arborizada | 1.348,6 | 15,43 | 10,57 | 20.805 |

### Filtro de grupos fitofisionômicos elegíveis

Para excluir classes não vegetacionais (pastagem, agricultura, água), o CLI aceita:

```powershell
python -m biomass_model.cli polygon ... --fitofisionomia-groups forest,savanna,campestre
```

Com o filtro, a área analisada cai para **1.348,6 ha** (Savana Arborizada), a AGB média é
**15,43 Mg ha⁻¹**, o estoque é **20.805 Mg** (IC90 19.189–30.348) e a fração na AOA sobe para
**90,2%**. Os 869,0 ha de “Pecuária” ficam explicitamente fora da estimativa vegetacional,
embora permaneçam no mapa A0 por causa da máscara MapBiomas 3/4.

## 5. Leitura

- O Produto C está funcional: lê geometria, calcula área real de interseção, agrega AGB,
  propaga incerteza por blocos espaciais, reporta AOA e individualiza por fitofisionomia.
- O IC90 do total é largo (29–48 mil Mg), reflexo da incerteza do A0 e da agregação espacial.
- **Inconsistência relevante:** 39,2% da área analisada é classificada como “Pecuária” pelo IBGE
  1:250k, embora o mapa A0 já esteja mascarado por classes 3/4 do MapBiomas. Isso mostra que a
  correspondência IBGE–MapBiomas não é direta e precisa de reconciliação antes de usar a
  fitofisionomia como filtro de produto.
- O mapa A0 é o baseline GEDI experimental, não o modelo campo-first; o resultado serve para
  validar o **mecanismo do Produto C**, não a acurácia da AGB.
- O filtro por grupo é necessário: sem ele, 39,2% da área seria rotulada como pastagem pelo IBGE.
  No box inteiro, a discordância é de 12,3% (`docs/54`).
- Nenhum produto foi promovido; não usar para MRV/créditos.

## 6. Artefatos

- `E:\Mapbiomas\biomass\derived\polygon_piloto_cerrado_central.geojson`
- `E:\Mapbiomas\biomass\derived\fitofisionomia_cerrado_central_2021_30m.tif`
- `E:\Mapbiomas\biomass\derived\polygon_piloto_cerrado_central.json`

## 7. Próximos passos

1. Reconciliar classes IBGE e MapBiomas e decidir se “Pecuária” deve ser excluída do Produto C.
2. Expor no CLI um filtro explícito de grupos fitofisionômicos elegíveis.
3. Usar o modelo campo-first (quando houver mapa compatível) em vez do A0.
4. Separar no relatório o IC do modelo do IC de referência/alometria.
5. Validar o total do polígono contra campo independente.
