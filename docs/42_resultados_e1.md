# 42 — Resultados preliminares da E1 (features anuais vs compósito estático)

**Data:** 2026-11-18 · **Status:** experimento preliminar; nenhum modelo promovido.

## 1. Desenho

- Dois boxes: Amazônia central (19,9 mil footprints) e Cerrado central (14,4 mil).
- Anos: 2019, 2020, 2021, 2022 (GEDI; 2023 tem n muito pequeno e 2024 ainda sem features anuais).
- A1: S2 anual por ano (16 bandas: 6 reflectâncias, NDVI/NDMI/NIRv/NBR/NDII, p10/p90/amplitude de
  NDVI, nobs, fração válida) + DEM/ERA5/histórico.
- A0: mesmo conjunto de footprints, mas com o compósito S2 multi-ano já existente (2020–2024).
- Validação: leave-one-year-out (4 folds), métricas por fold; 30 m e 1 km.

## 2. Resultado (LOO por ano)

| Bioma | Modelo | Escala | n | R² | RMSE | Viés | R² por fold |
|---|---|---|---|---|---|---|---|
| Amazônia | A0 estático | 30 m | 14.735 | −0,171 | 106,6 | −14,1 | −0,46/−0,04/−0,18/−0,33 |
| Amazônia | A1 anual | 30 m | 14.735 | −0,150 | 105,7 | −4,0 | −0,38/0,00/−0,20/−0,85 |
| Amazônia | A0 estático | 1 km | 687 | −0,041 | 60,8 | −0,5 | −1,01/0,31/−0,21/−1,66 |
| Amazônia | A1 anual | 1 km | 687 | −0,261 | 67,0 | −12,5 | −1,54/−0,21/−0,21/−1,10 |
| Cerrado | A0 estático | 30 m | 11.954 | −0,041 | 43,1 | +5,5 | −0,60/0,08/0,18/0,03 |
| Cerrado | A1 anual | 30 m | 11.954 | −0,169 | 45,6 | +7,7 | −1,32/0,15/0,13/0,04 |
| Cerrado | A0 estático | 1 km | 734 | −0,021 | 27,1 | +2,2 | −0,87/0,22/0,36/0,00 |
| Cerrado | A1 anual | 1 km | 734 | −0,092 | 28,1 | +2,6 | −0,96/−0,03/0,28/0,01 |

**Leitura:** as features anuais não trouxeram ganho consistente. Na Amazônia 30 m houve pequena
melhora de viés/RMSE; em 1 km piorou. No Cerrado, piorou nas duas escalas. O resultado é neutro a
negativo e **não promove A1**.

## 3. Por que este teste é de robustez anual, não de mudança

- Cada ano tem **footprints diferentes** (órbitas/qualidade), então o fold anual mede também
  mudança de composição da amostra, não só mudança da relação features→AGB.
- 2022 tem n pequeno (861 Amazônia; 2.004 Cerrado); 2023 foi excluído (57–285).
- O compósito estático A0 também muda pouco entre folds, mas é uma referência válida.
- O teste decisivo é **validação de campo e consistência anual**; mudança de cobertura é atividade externa, não escopo
  agregado.

## 4. Bug encontrado e corrigido

`aggregate_cells` agrupava apenas por célula, colapsando anos diferentes na mesma célula (o 1 km
tinha 317–321 linhas em vez de ~700, com `year` do primeiro ano). Corrigido para agrupar por
**célula e ano** quando `year` existe; resultados acima já usam a correção. Isso afetava qualquer
análise temporal em 1 km.

## 5. Próximos passos (E2)

1. Adicionar 2024 (há footprints e S2) e os boxes restantes às features anuais.
2. Testar sensibilidade a `max_items`/estação (ano inteiro vs estação seca).
3. Avaliar consistência anual (mesma célula, variação de features e de mapa) como diagnóstico.
4. Só então decidir entre A1 e A2 (covariáveis de estado); modelos de mudança estão fora do escopo.
