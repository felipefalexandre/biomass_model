# 25 — Plano de avaliação e benchmarks

## 1. Objetivo

Definir, **antes de executar**, como decidir se um modelo é aceitável e como compará-lo a
alternativas. Sem isso, a escolha vira preferência pessoal.

## 2. Experimentos obrigatórios

| ID | Experimento | Pergunta | Métrica principal |
|---|---|---|---|
| X1 | M0 (média estratificada) | piso de referência | RMSE em CV espacial |
| X2 | M1 (GLM) | o simples já explica? | RMSE, viés |
| X3 | M2 (RF) | ganho não linear? | RMSE, estabilidade |
| X4 | M3 (XGBoost) | ganho adicional? | RMSE, viés |
| X5 | Ablação de features | qual grupo importa? | ΔRMSE |
| X6 | Estratificação por bioma | modelo único vs dois | ΔRMSE por bioma |
| X7 | Transformação do alvo | log/raiz vs linear | RMSE, viés em faixas |
| X8 | Duas etapas (cobertura + AGBD) | melhora o Cerrado? | RMSE por grupo |
| X9 | AOA | onde o modelo é válido? | fração coberta, erro dentro/fora |
| X10 | Comparação com benchmarks | onde divergimos? | distribuição, mapas de diferença |
| X11 | Sensibilidade a hiperparâmetros | resultado é frágil? | variação de RMSE |
| X12 | Holdout temporal | generaliza no tempo? | RMSE no ano separado |

## 3. Desenho de validação

- **Principal:** blocos espaciais de 50–100 km (testar 50 e 100; escolher e justificar).
- **Estresse:** leave-one-region-out.
- **Diagnóstico:** k-fold aleatório (apenas para comparação).
- **Final:** validação independente com campo, se disponível.
- **Nunca:** selecionar hiperparâmetros no conjunto de teste.

## 4. Métricas e limites

| Métrica | Limite inicial | Observação |
|---|---|---|
| Viés relativo do total | ≤ 10% | por bioma e por estrato |
| RMSE relativo | ≤ 30% (Amazônia), ≤ 40% (Cerrado) | calibrar com literatura |
| Cobertura IC90 | 80–95% | nem otimista nem frouxo |
| Estabilidade entre folds | ΔRMSE ≤ 20% | robustez |
| Fração na AOA | ≥ 90% | domínio de interesse |
| Erro por faixa | sem viés sistemático > 15% | diagnóstico |

**Importante:** limites são propostas. Precisam de aprovação (`docs/30`, Q6) e podem ser
revisados com base em evidência, mas a revisão deve ser registrada.

## 5. Benchmarks

| Benchmark | Uso | Cuidado |
|---|---|---|
| CCI Biomass 2010 (Santoro 2021) | comparação de distribuição | 100 m; ano único |
| Spawn 2020 | AGB/BGB 2010 | 1 km |
| Avitabile 2016 | pan-tropical | resolução grosseira |
| Saatchi 2011 / Baccini 2012 | contexto histórico | métodos antigos |
| PRODES/MapBiomas desmatamento | validação de área de conversão | não é AGB |
| Literatura de parcelas (Ribeiro 2011 etc.) | plausibilidade | sítios específicos |

**Regra:** benchmark não é verdade. Divergência é resultado a explicar, não erro a esconder.

## 6. Análise de resíduos

Para cada modelo:

1. resíduo vs AGBD observada (detectar saturação/curvatura);
2. resíduo vs região (detectar viés geográfico);
3. resíduo vs classe MapBiomas;
4. resíduo vs distância à estrada/borda (acessibilidade);
5. resíduo vs ano (consistência temporal);
6. resíduo vs cobertura de nuvem/qualidade.

## 7. Critério de seleção de modelo

Selecionar o **modelo mais simples** que:

- atende aos limites de viés e RMSE;
- tem IC com cobertura adequada;
- é estável entre folds/regiões;
- tem AOA ampla;
- não apresenta viés sistemático por estrato.

Empate técnico ⇒ escolher o mais interpretável/menos custoso (ADR-0002).

## 8. Relatório de avaliação

1. Objetivo e critérios (este documento).
2. Dados e splits.
3. Resultados por experimento.
4. Tabelas por estrato/faixa.
5. Resíduos.
6. Benchmarks.
7. Decisão e justificativa.
8. Ameaças à validade.

## 9. Reprodutibilidade dos experimentos

- Cada experimento tem `run_id`, config e seed.
- Tabelas de resultados geradas por script, não digitadas.
- Figuras geradas por script.
- Comparações sempre com a mesma versão de dados.
