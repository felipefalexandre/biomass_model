# 56 — Validação independente: ORNL Sustainable Landscapes Brazil

**Data:** 2026-11-24 · **Status:** experimento concluído; transferência Cerrado→Amazônia falhou.

## 1. Objetivo

Aplicar o modelo campo-first F0 (treinado apenas em PLOS 2018, Cerrado) aos sítios ORNL da
Amazônia com AGB e feições completas, agora que as coordenadas foram recuperadas (`docs/55`).

## 2. Dados

- **Referência:** ORNL Sustainable Landscapes Brazil (DOI 10.3334/ORNLDAAC/2007).
- **Sítios-ano com AGB e features completas:** 10.
- **Features:** Landsat C2 L2 em janela de 1 km na data do inventário (2009–2013), DEM GLO-30,
  ERA5-Land (bbox amazônico), histórico MapBiomas.
- **Modelo aplicado:** RF campo-first PLOS 2018 sem categóricas
  (`field_plos2018_rf_block200_nocat`), 34 features.
- **AOA:** calculada contra o treino PLOS (limiar q95 = 7,44).

## 3. Resultado

| Métrica | Valor |
|---|---:|
| n | 10 |
| AGB observada média | 209,9 Mg ha⁻¹ |
| AGB predita média | 29,0 Mg ha⁻¹ |
| R² | −1,52 |
| RMSE | 233,7 Mg ha⁻¹ |
| MAE | 185,8 Mg ha⁻¹ |
| Viés | −180,9 Mg ha⁻¹ |
| Fração dentro da AOA | 0,00 (0 de 10) |

Detalhe:

| Sítio | Observado | Predito |
|---|---:|---:|
| FNA_A01 | 10,1 | 30,7 |
| FST_A01 | 463,1 | 28,0 |
| JAM_A01 | 254,7 | 28,3 |
| JAM_A02 | 308,3 | 29,5 |
| SFX_A01 | 31,4 | 29,2 |
| SFX_A02 | 26,6 | 30,4 |
| TAN_A01 | 144,5 | 29,9 |
| TAP_A01 | 321,4 | 27,9 |
| TAP_A04 | 345,4 | 27,9 |
| TAP_A05 | 193,6 | 27,9 |

## 4. Leitura

- O modelo PLOS (Cerrado) colapsa a predição em ~28–31 Mg ha⁻¹ e não reproduz nem o nível nem
  a variação da AGB amazônica.
- A AOA sinalizou **100% dos pontos fora do domínio**, coerente com o resultado.
- O erro não é ruído de features: os 10 sítios têm features completas; é extrapolação de
  domínio ecológico.
- ORNL é uma fonte independente valiosa, mas não valida um modelo treinado só no Cerrado.

## 5. Conclusão

1. O F0 é **específico do Cerrado**; não deve ser aplicado à Amazônia.
2. ORNL e CEDA devem ser usados para **treinar/validar um modelo amazônico**, não para validar
   o F0.
3. A AOA é um mecanismo de segurança eficaz; o produto deve mascarar áreas fora dela.
4. Nenhum modelo foi promovido.

## 6. Artefatos

- `derived\ornl_features_landsat.csv`
- `derived\ornl_pred_rf_block200_nocat.csv`
- `derived\observations_ornl.csv`
- `data/reference/ornl_sites_coords.csv`

## 7. Próximos passos

1. Construir um modelo amazônico com CEDA + ORNL e validação leave-one-source/region-out.
2. Buscar mais sítios amazônicos independentes (RAINFOR, novos inventários).
3. Alinhar features Landsat/S2 antes de aplicar ao mapa 30 m.
4. Manter ORNL como validação independente até haver um modelo amazônico promovido.
