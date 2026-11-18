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

**Importante:** limites **aceitos** (Q6 respondida em `docs/30`), calibrados pela literatura:
erro relativo ~30% é a ordem de grandeza em produtos de AGB tropical (Avitabile et al. 2016;
Santoro et al. 2021) e 30–40% no GEDI L4A (Duncanson et al. 2022). O limite do Cerrado é mais
frouxo por heterogeneidade e escassez de campo. Revisões exigem evidência e registro.

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
## 10. Resultado do baseline inicial (2026-11-17)

Primeiro experimento registrado, para calibrar expectativas — **não** é o modelo do produto:

| Item | Valor |
|---|---|
| Bioma / referência | Amazônia / GEDI L4A V2.1 (2019–2024) |
| n (blocos) | 19.869 (25 blocos de ~5 km) |
| Features | 9 S2 (uma data) + 13 ERA5 + elevação/declividade/aspecto |
| R² (OOF) | 0,097 |
| RMSE / MAE | 92,4 / 70,2 Mg ha⁻¹ |
| Viés | +1,6 Mg ha⁻¹ |
| Subconjunto degrade_zero | R² 0,098; RMSE 91,9 (n = 16.314) |
| S2 mediana de 10 datas (footprint) | R² 0,094; RMSE 92,5 — sem ganho |
| Agregado em 1 km (327 células) | R² 0,285; RMSE 34,3; MAE 26,3; folds 0,10–0,31 |
| Cerrado, campo PLOS 2018 (45 sítios, 1 km) | R² 0,328; RMSE 8,34; MAE 6,53; 2 folds negativos |

Leitura: dentro de um piloto uniforme de floresta densa, uma única data óptica satura e explica
quase nada da variação do L4A. Compor 10 datas não muda isso; o gargalo é o ruído do L4A e a
homogeneidade local. Ao agregar em 1 km, o RMSE cai para 34,3 Mg ha⁻¹ (R² 0,285), mas parte disso
é redução da variância do alvo — o produto em 30 m deve ser tratado como camada diagnóstica, não
como promessa de acurácia. Artefatos: `data/reference/baselines.csv`,
`biomass_model.modeling.run_baseline`.
