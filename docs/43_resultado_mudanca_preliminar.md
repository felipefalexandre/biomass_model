# 43 — Diagnóstico de estabilidade temporal (pares anuais)

**Data:** 2026-11-18 · **Status:** diagnóstico; não é validação de mudança nem detecção de desmatamento.

## 1. Por que este teste existe

O modelo estima biomassa por ano. Se as features anuais forem ruidosas, o mapa pode oscilar sem
mudança real. Este teste mede **estabilidade**, não capacidade de detectar desmatamento (que é
atividade externa, fora do escopo).

## 2. Desenho

- Células de 1 km (≥3 footprints) nos boxes Amazônia central e Cerrado central.
- Anos 2019–2022 (features anuais S2 já geradas); pares consecutivos na **mesma célula**.
- Alvo: ΔAGB observado entre anos (GEDI) — usado como referência ruidosa, não verdade.
- Features: ΔNDVI, ΔNBR, ΔNDMI, Δamplitude, Δbandas, Δnobs/validade.
- Modelo: RandomForest em Δfeatures, CV por blocos espaciais de 5 km; comparação com Δ=0.

## 3. Resultados

| Bioma | Pares | SD ΔAGB | RMSE RF | RMSE Δ=0 | R² RF | Sinal correto | SD em “estável” (|ΔNDVI|<0,03) |
|---|---|---|---|---|---|---|---|
| Amazônia | 300 | 72,4 | 67,9 | 72,2 | 0,10 | 65% | 71,1 |
| Cerrado | 389 | 24,8 | 25,4 | 24,5 | −0,08 | 51% | 18,9 |

## 4. Interpretação

- O ruído de ΔAGB entre anos é enorme (SD 72 Mg ha⁻¹ na Amazônia), porque os footprints GEDI de
  anos diferentes não são os mesmos pontos e têm erro de modelo.
- Na Amazônia há um ganho fraco (R² 0,10; RMSE 6% menor que Δ=0), insuficiente para uso.
- No Cerrado não há sinal (R² negativo; sinal 51%).
- “Estável” por NDVI ainda tem SD de 71/19 Mg ha⁻¹: a referência não permite separar variação real
  de ruído.

**Conclusão:** o diagnóstico mostra que a estimativa anual precisa de **estabilidade de features e
de modelo**, e que pares GEDI não servem para medir mudança. Ele **não** autoriza afirmar detecção
de desmatamento/reflorestamento. A atividade continua sendo fornecida por mapas externos.

## 5. Próximos passos (estabilidade, não mudança)

1. Adicionar 2024 e os boxes restantes às features anuais; verificar se a oscilação cai.
2. Testar sensibilidade a `max_items`, estação (ano inteiro vs seca) e composição (p10/p50/p90).
3. Definir um teste de consistência: mesma célula, anos consecutivos, Δfeatures pequeno ⇒
   |ΔAGB_map| abaixo de um limiar; relatar distribuição.
4. Não promover modelo por este teste; usar campo e polígono para acurácia.

Artefatos: `data/reference/e2a_change_pairs.json`,
`E:\Mapbiomas\biomass\derived\e2a_delta_pairs_{amazonia,cerrado}.csv`.
