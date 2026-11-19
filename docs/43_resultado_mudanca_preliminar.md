# 43 — Resultado preliminar de mudança (pares anuais)

**Data:** 2026-11-18 · **Status:** teste preliminar; nenhuma conclusão de mudança promovida.

## 1. Desenho

- Células de 1 km (≥3 footprints) nos boxes Amazônia central e Cerrado central.
- Anos 2019–2022 (features anuais S2 já geradas); pares consecutivos na **mesma célula**.
- Alvo: ΔAGB observado entre anos (GEDI). Features: ΔNDVI, ΔNBR, ΔNDMI, Δamplitude, Δbandas,
  Δnobs/validade.
- Modelo: RandomForest em Δfeatures, CV por blocos espaciais de 5 km; comparação com Δ=0.

## 2. Resultados

| Bioma | Pares | SD ΔAGB | RMSE RF | RMSE Δ=0 | R² RF | Sinal correto | SD em “estável” (|ΔNDVI|<0,03) |
|---|---|---|---|---|---|---|---|
| Amazônia | 300 | 72,4 | 67,9 | 72,2 | 0,10 | 65% | 71,1 |
| Cerrado | 389 | 24,8 | 25,4 | 24,5 | −0,08 | 51% | 18,9 |

## 3. Interpretação

- O ruído de ΔAGB entre anos é enorme (SD 72 Mg ha⁻¹ na Amazônia), porque os footprints GEDI de
  anos diferentes não são os mesmos pontos e têm erro de modelo. Isso domina qualquer sinal.
- Na Amazônia há um ganho fraco (R² 0,10; RMSE 6% menor que Δ=0), insuficiente para uso.
- No Cerrado não há sinal (R² negativo; sinal 51%).
- “Estável” por NDVI ainda tem SD de 71/19 Mg ha⁻¹: a referência não permite separar mudança real
  de ruído.

**Conclusão:** este desenho não valida mudança e não deve ser usado para afirmar que o modelo
detecta desmatamento/regeneração. Confirma que a Linha T exige referência melhor (campo repetido,
LiDAR/ORNL, eventos com máscara) e não pares GEDI arbitrários.

## 4. Próximos passos para E2

1. Usar polígonos de evento (PRODES, MapBiomas, Fogo) e comparar ΔAGB dentro/fora, com buffer.
2. Construir pares **co-localizados** (mesma trilha/pegada) ou usar campo repetido.
3. Avaliar a resposta do modelo a mudanças sintéticas controladas (substituir features de uma
   célula por outra classe) como teste de sensibilidade, não de acurácia.
4. Só promover mudança quando houver sinal/contraste/magnitude consistentes em ≥3 eventos por tipo.

Artefatos: `data/reference/e2a_change_pairs.json`,
`E:\Mapbiomas\biomass\derived\e2a_delta_pairs_{amazonia,cerrado}.csv`.
