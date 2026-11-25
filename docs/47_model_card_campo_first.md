# 47 — Model card: baseline campo-first F0 (PLOS 2018, Cerrado)

**Data:** 2026-11-24 · **Status:** experimental; não é produto operacional nem base MRV.

## 1. O que é

Primeiro modelo treinado com **referência de campo** (PLOS 2018, Cerrado) e features extraídas
para a tabela canônica. Substitui, como experimento, o hábito de treinar apenas contra GEDI.

- **Referência:** PLOS 2018 (Roitman et al., DOI 10.1371/journal.pone.0196742), 77 sítios.
- **Amostra usada:** 40 sítios no domínio 3/4, com data entre 2004 e 2014 e features Landsat.
- **Descartes:** 30 sítios sem features (principalmente inventários anteriores a 2004 ou sem
  Landsat na data) e 7 sítios fora do domínio 3/4.
- **Features (36):** bandas Landsat C2 L2 e índices (NDVI, NDMI, NBR, NDII, EVI), elevação,
  declividade, aspecto, ERA5 e features de histórico MapBiomas.
- **Modelo:** RandomForest (400 árvores, `min_samples_leaf=3`), alvo `agb_mg_ha`.
- **Código:** `src/biomass_model/observation_features.py`, `src/biomass_model/training/field.py`,
  `src/biomass_model/validation/spatial.py`.

## 2. Construção das features

- Janela de ~1 km (`half_m=500`) sobre Landsat e DEM de cada sítio.
- AGB de referência é a do PLOS, sem recálculo alométrico.
- Classe MapBiomas do ano do inventário; histórico usa apenas anos **anteriores** ao ano-alvo
  (sem vazamento temporal).
- O clima histórico usa fallback para a climatologia recente quando o ano do inventário não
  existe no arquivo ERA5; isso é uma limitação registrada.
- Nenhum produto de AGB (GEDI, CCI, EBA) entra como feature.

## 3. Validação

### 3.1 Primária: blocos de 200 km com buffer de 25 km

- Folds: 5 blocos; OOF = 16 sítios.
- R² = 0,262; RMSE = 10,81 Mg ha⁻¹; MAE = 7,88; viés = −3,59; MedAE = 4,92.
- Baseline (média por fitofisionomia/bioma): R² = −0,130; RMSE = 13,38; viés = −0,87.
- R² após remover viés: 0,343.

### 3.2 Sensibilidade: leave-one-block-out de 100 km com buffer de 25 km

- 35 folds; OOF = 40 sítios (31 folds com n=1).
- R² = 0,197; RMSE = 9,54; MAE = 7,15; viés = +0,15; MedAE = 5,35.
- Baseline: R² = −0,063; RMSE = 10,98; viés = −0,03.

### 3.3 Incerteza (cross-conformal por fold)

- Blocos de 200 km: cobertura empírica do IC90 = 0,813; largura média = 33,8 Mg ha⁻¹ (n=16).
- Sensibilidade 100 km: cobertura = 0,900; largura média = 28,5 Mg ha⁻¹ (n=40).
- Os intervalos são calculados com resíduos absolutos dos outros folds. No cenário de blocos,
  a cobertura ficou abaixo do nominal (0,813 < 0,90), indicando intervalos otimistas.
- A incerteza cobre apenas erro de modelo OOF; não inclui erro de referência, alometria,
  amostragem de campo ou representatividade.

### 3.4 Leitura

O modelo supera o baseline, mas o ganho é modesto e a amostra é pequena, antiga e restrita ao
Cerrado. O resultado **não** demonstra acurácia operacional. A validação primária cobre apenas
16 sítios; a sensibilidade cobre 40, mas com folds de um sítio. Nenhuma das duas é validação
independente: os sítios PLOS são a única fonte de campo e foram usados para treinar e testar.
A cobertura conformal abaixo do nominal no cenário de blocos reforça que o produto não está
pronto para uso operacional.

## 4. Artefatos

- Features: `E:\Mapbiomas\biomass\derived\plos2018_features_landsat.csv`
- Modelo/validação primária:
  `E:\Mapbiomas\biomass\derived\field_plos2018_rf_block200.{joblib,metrics.json,predictions.csv}`
- Sensibilidade:
  `E:\Mapbiomas\biomass\derived\field_plos2018_rf.{joblib,metrics.json,predictions.csv}`

Comandos:

```powershell
python -m biomass_model.cli features-observations `
  --observations E:\Mapbiomas\biomass\derived\observations_plos2018.csv `
  --out E:\Mapbiomas\biomass\derived\plos2018_features_landsat.csv `
  --optical-dir E:\Mapbiomas\biomass\fields\plos2018 `
  --optical-pattern "site_{site_int:03d}/landsat_{year}.tif" `
  --dem-dir E:\Mapbiomas\biomass\fields\plos2018 `
  --dem-pattern "site_{site_int:03d}/dem.tif" `
  --era5 E:\Mapbiomas\biomass\era5\cerrado_era5land_2019_2024_bbox.nc `
  --mapbiomas-dir E:\Mapbiomas --history-start 2004 --history-end 2018

python -m biomass_model.cli train-field `
  --csv E:\Mapbiomas\biomass\derived\plos2018_features_landsat.csv `
  --out-dir E:\Mapbiomas\biomass\derived\field_plos2018_rf_block200 `
  --block-size-m 200000 --buffer-m 25000 --domain-classes 3,4
```

## 5. Limitações

1. Referência de campo antiga (2004–2014), apenas Cerrado e Cerrado sensu stricto.
2. Amostra pequena; 40 sítios no domínio e 16 na validação primária.
3. A mesma fonte é usada para treino e teste; falta holdout independente.
4. Clima histórico usa fallback de climatologia recente.
5. Sem incerteza de referência, alometria ou modelo; sem intervalo de predição.
6. Sem Amazônia no treino/modelo; a base CEDA/NCEO Manaus 2014 (23 parcelas) foi ingerida e
   fica reservada para validação independente, mas ainda não foi usada neste modelo.
7. A fitofisionomia disponível é apenas `savanna`; a variante com IBGE `legenda_2` foi testada
   em `docs/48` e não trouxe ganho consistente (30 `savanna` + 10 `unknown`).
8. As features são Landsat; o mapa operacional em 30 m usa S2, então este modelo **não** é
   diretamente aplicável ao pipeline de mapa atual.
9. O modelo não foi promovido; é baseline F0 para comparação.

## 6. Próximos passos

1. Adicionar inventários independentes e recentes (especialmente Amazônia pós-2019).
2. Construir features para ORNL e IFN; resolver coordenadas ORNL e data do IFN.
3. Testar fitofisionomia como feature/estrato e partial pooling.
4. Implementar incerteza (conformal/QRF) para o modelo campo-first.
5. Alinhar features de treino e inferência (Landsat vs S2) antes de gerar mapas.
6. Repetir a validação com holdout independente e por fitofisionomia.

## 7. Status de promoção

**Não promovido.** Baseline experimental F0. Não usar para MRV, créditos, decisões fundiárias
ou comunicação pública como estimativa de AGB real.
