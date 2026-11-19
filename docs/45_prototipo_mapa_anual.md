# 45 — Protótipo do mapa anual de AGB por pixel

**Data:** 2026-11-18 · **Status:** protótipo; não é produto MRV.

## 1. Requisito

O produto é um **mapa raster de AGB (Mg ha⁻¹) por pixel**. A soma/polígono é cálculo do usuário;
não é um produto separado do modelo.

## 2. O que foi gerado

- Box: Cerrado central; ano 2021.
- Grade: 16 × 16 células de **1 km** (a janela S2 tem 16 km).
- Modelo: RandomForest treinado nas features anuais S2 (2019–2022) + DEM/ERA5/histórico do box.
- Saída: GeoTIFF com 3 bandas (`agbd_mg_ha`, `domain_mask`, `s2_valid_fraction`) e JSON.
- Resultado: 194 células válidas; AGB média 15,9 Mg ha⁻¹ (faixa 2,1–101,0). A média GEDI das
  células do box é ~22,5: o mapa **subestima** o nível, como esperado sem calibração local.

Comando:

```powershell
python -m biomass_model.cli annual-map `
  --model E:\Mapbiomas\biomass\derived\e1_cerrado_central_annual_model.joblib `
  --s2 E:\Mapbiomas\biomass\pilots\annual\cerrado_central_2021_s2.tif `
  --dem E:\Mapbiomas\biomass\pilots\cerrado_dem30.tif `
  --era5 E:\Mapbiomas\biomass\pilots\cerrado_era5land_2018_2025.nc `
  --mapbiomas-dir E:\Mapbiomas --year 2021 --block 100 `
  --out E:\Mapbiomas\biomass\derived\maps\cerrado_central_agb_2021_1km.tif
```

## 3. Como funciona

1. Compósito S2 anual (16 bandas com fenologia) → média de blocos de 100 px (1 km).
2. DEM/ERA5/histórico MapBiomas amostrados nos centros das células.
3. Modelo RF aplica as features e prevê AGBD.
4. Máscara: classe 3/4 no ano e fração válida S2 > 0,3.

## 4. Limitações (explícitas)

- Protótipo em 1 km; 30 m ainda não implementado (exige predição em ~2,5 M pixels e chunking).
- Modelo treinado em features de footprints, não em médias de 1 km; há descasamento de suporte.
- Sem calibração local, sem IC conformal e sem AOA nesta versão.
- Um box/ano; não é mapa nacional nem base MRV.
- A média do mapa não deve ser comparada diretamente a GEDI como acurácia; falta validação.

## 5. Próximos passos para o produto

1. Predição em 30 m por tile (chunked), com a mesma máscara.
2. IC conformal por célula e AOA no mapa.
3. Calibração local por região e validação de campo (G2).
4. Rodar todos os boxes/anos e comparar com mapas externos de atividade (sobreposição do usuário).
5. Passar pelos portões G0–G7 antes de chamar de MRV.
