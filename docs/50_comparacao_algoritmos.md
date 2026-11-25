# 50 — Comparação de algoritmos no modelo campo-first F0

**Data:** 2026-11-24 · **Status:** experimento concluído; nenhum modelo promovido.

## 1. Pergunta

Algoritmos mais complexos que RandomForest melhoram o modelo campo-first F0 (PLOS 2018,
Cerrado) sob a mesma validação espacial com buffer?

## 2. Desenho

- Base: `plos2018_features_landsat.csv`; 40 sítios no domínio 3/4; 34 features numéricas
  (sem dummies categóricas, para comparação justa).
- Alvo: `agb_mg_ha`.
- Validação primária: blocos de 200 km, buffer de 25 km, `min_test=3`.
- Sensibilidade: leave-one-block-out de 100 km, buffer de 25 km.
- Algoritmos: RandomForest, ExtraTrees, GradientBoosting, HistGradientBoosting e Ridge.
- 400 estimadores (quando aplicável), `min_samples_leaf=3`, seed 42.
- IC90 cross-conformal por fold em todos.

## 3. Resultados

| Algoritmo | Validação | n | R² | RMSE | MAE | Viés | Cobertura IC90 | Largura IC90 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| RandomForest | bloco 200 km | 16 | 0,259 | 10,83 | 7,90 | −3,52 | 0,813 | 33,8 |
| ExtraTrees | bloco 200 km | 16 | 0,162 | 11,52 | 8,56 | −4,18 | 0,813 | 33,7 |
| GradientBoosting | bloco 200 km | 16 | 0,032 | 12,38 | 9,44 | −3,48 | 0,813 | 36,9 |
| HistGradientBoosting | bloco 200 km | 16 | −0,000 | 12,59 | 9,43 | −3,73 | 0,813 | 36,4 |
| Ridge | bloco 200 km | 16 | −0,622 | 16,03 | 12,35 | −7,36 | 0,813 | 50,8 |
| RandomForest | LOO 100 km | 40 | 0,201 | 9,51 | 7,13 | +0,14 | 0,900 | 28,5 |
| ExtraTrees | LOO 100 km | 40 | 0,198 | 9,53 | 7,29 | −0,07 | 0,900 | 29,2 |
| GradientBoosting | LOO 100 km | 40 | 0,116 | 10,01 | 7,95 | −0,17 | 0,875 | 30,6 |
| HistGradientBoosting | LOO 100 km | 40 | 0,032 | 10,47 | 8,43 | +0,37 | 0,850 | 30,6 |
| Ridge | LOO 100 km | 40 | −5,650 | 27,46 | 14,27 | −2,75 | 0,875 | 45,6 |

## 4. Leitura

- RandomForest é o melhor ou empatado com ExtraTrees nos dois esquemas.
- Boosting não supera RF nesta amostra pequena; Ridge é inadequado para a relação não linear.
- O ganho do RF sobre o baseline por estrato já foi mostrado em `docs/47`; aqui não há ganho
  adicional de complexidade.
- As diferenças são pequenas e a amostra é de 40 sítios; não há evidência para mudar o algoritmo.
- A cobertura do IC90 no cenário de blocos permanece 0,813, abaixo do nominal.

## 5. Decisão

Manter **RandomForest** como algoritmo do baseline F0. Não promover nenhum modelo por esta
comparação. O resultado é registrado como evidência de que complexidade adicional não é
justificada com os dados atuais.

## 6. Artefatos

- `E:\Mapbiomas\biomass\derived\alg_compare\comparison.csv`
- Métricas/modelos por algoritmo em `E:\Mapbiomas\biomass\derived\alg_compare\<algoritmo>_<validação>.*`

## 7. Limitações

- Amostra pequena, antiga e restrita ao Cerrado.
- Sem holdout independente.
- Sem ajuste de hiperparâmetros; comparação controlada, não exaustiva.
- A validação LOO tem 31 folds de um sítio; a primária cobre 16 sítios.
