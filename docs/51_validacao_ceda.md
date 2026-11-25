# 51 — Validação independente inicial: CEDA/NCEO Manaus 2014

**Data:** 2026-11-24 · **Status:** experimento concluído; transferência entre biomas falhou.

## 1. Objetivo

Testar o modelo campo-first F0 (treinado apenas em PLOS 2018, Cerrado) em uma fonte
independente de campo na Amazônia: as 23 parcelas de 100 × 60 m do CEDA/NCEO Manaus 2014
(OGL, Carreiras 2025).

## 2. Dados

- **Referência:** CEDA/NCEO Manaus plots AGB 2014 v1.0; 23 parcelas; AGB por parcela.
- **Features:** Landsat C2 L2 em janela de 1 km na data de 2014, DEM GLO-30, ERA5-Land
  (climatologia recente como fallback), histórico MapBiomas.
- **Amostra com features completas:** 21 parcelas; 2 sem features completas.
- **Observado:** média 132,3 Mg ha⁻¹; faixa 66,1–201,8.
- **Modelo aplicado:** RF campo-first treinado em PLOS 2018 (Cerrado), sem dummies
  categóricas, 34 features (`alg_compare/rf_block200`).

## 3. Resultado

| Métrica | Valor |
|---|---:|
| n | 21 |
| AGB observada média | 132,3 Mg ha⁻¹ |
| AGB predita média | 28,1 Mg ha⁻¹ |
| R² | −8,20 |
| RMSE | 110,3 Mg ha⁻¹ |
| MAE | 104,2 Mg ha⁻¹ |
| Viés | −104,2 Mg ha⁻¹ |
| Correlação observado–predito | 0,03 |

O modelo praticamente ignora a variação da AGB amazônica e colapsa a predição em torno de
28 Mg ha⁻¹.

## 4. Por que falhou

As features da Amazônia estão fora do domínio de treino do PLOS (Cerrado):

| Feature | PLOS 2018 (média; faixa) | CEDA Manaus (média; faixa) |
|---|---|---|
| NDVI Landsat | 0,49; 0,26–0,75 | 0,82; 0,59–0,89 |
| NIR Landsat | 0,24; 0,17–0,33 | 0,36; 0,32–0,41 |
| Elevação (m) | 579; 90–1.312 | 124; 105–146 |
| Precipitação anual (mm) | 1.141; 795–1.632 | 2.177; 2.132–2.285 |

A combinação de dossel mais fechado, maior NIR, menor altitude e maior precipitação não tem
análogo no treino. É um caso claro de extrapolação; uma AOA baseada no treino também sinalizaria
esses pontos como fora do domínio.

## 5. Conclusão

- O modelo F0 é **específico do Cerrado** e **não transfere** para a Amazônia.
- CEDA é uma fonte independente valiosa, mas não pode ser usada para "validar" um modelo
  treinado apenas no Cerrado; o resultado é de extrapolação.
- Nenhum modelo foi promovido.
- Este resultado reforça a necessidade de:
  1. dados de campo amazônicos no treino (CEDA, RAINFOR, outras fontes);
  2. AOA e máscara de extrapolação no produto;
  3. modelos por bioma ou hierárquicos, não um modelo global treinado só no Cerrado.

## 6. Artefatos

- Observações CEDA: `E:\Mapbiomas\biomass\derived\observations_ceda.csv`
- Sites para Landsat: `E:\Mapbiomas\biomass\derived\ceda_manaus_sites.csv`
- Features: `E:\Mapbiomas\biomass\derived\ceda_manaus_features_landsat.csv`
- Predições: `E:\Mapbiomas\biomass\derived\ceda_manaus_pred_rf_block200.csv`

## 7. Próximos passos

1. Incorporar CEDA ao treino de um modelo amazônico, reservando outra fonte para validação.
2. Buscar RAINFOR/CEDA adicionais e inventários amazônicos recentes.
3. Implementar AOA para o modelo campo-first e reportar a fração dentro/fora.
4. Testar modelos por bioma e partial pooling.
5. Não usar o modelo F0 para a Amazônia.
