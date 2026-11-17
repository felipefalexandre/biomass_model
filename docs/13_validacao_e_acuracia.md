# 13 — Validação e acurácia

## 1. Princípio

Validação não é "medir R²". É responder: **o modelo generaliza para dados que ele não viu, em
condições realistas?** Em dados espaciais, isso exige desenho de validação que respeite a
dependência espacial.

## 2. Desenhos de validação

| Desenho | O que mede | Quando usar | Risco |
|---|---|---|---|
| k-fold aleatório | ajuste interpolativo | diagnóstico rápido | otimista |
| blocos espaciais (spatial k-fold) | generalização espacial | padrão do projeto | escolha do tamanho do bloco |
| leave-one-region-out (LORO) | extrapolação regional | teste de robustez | poucos grupos |
| NNDM-LOO | validação de mapa com distâncias comparáveis | mapa final | implementação |
| holdout temporal | generalização no tempo | série histórica | dados escassos |
| validação independente (campo) | acurácia real | sempre que possível | disponibilidade |

**Decisão:** relatar **blocos espaciais** como métrica principal, LORO como teste de estresse e
k-fold aleatório apenas como diagnóstico (nunca como métrica de aceite).

## 3. Métricas

Para AGBD (contínua):

- **RMSE** (Mg ha⁻¹) e **RMSE relativo** (% da média observada).
- **MAE**.
- **Viés médio** (ME) e viés relativo (%).
- **R²** (com ressalva: sensível a amplitude).
- **Coeficiente de concordância** (Lin) ou similar.
- **Cobertura do intervalo de predição** (fração de observações dentro do IP 90%).
- **Erro por faixa de AGBD** (baixa/média/alta) e por estrato.

Para a estimativa de área/total:

- viés relativo do total;
- cobertura do IC 90% da estimativa;
- erro relativo padrão.

## 4. Métricas por estrato (obrigatório)

Nunca reportar só a métrica agregada. A agregada esconde falhas:

- Amazônia: por sub-região e por faixa de AGBD.
- Cerrado: por grupo fisionômico (G1–G4) e por faixa.
- Todos: dentro e fora da AOA.

## 5. Tamanho de amostra de validação

- Precisa ser suficiente para estimar erro com precisão útil; calcular antes (análise de poder).
- Como regra prática, não usar < 30 unidades independentes por estrato para métricas de erro;
  para IC de estimativa, o requisito é maior.
- Se não houver amostra independente suficiente, **declarar** que a validação é limitada e não
  apresentar métricas como se fossem conclusivas.

## 6. Circularidade

Cenários de circularidade a evitar:

1. Treinar e validar no mesmo conjunto de GEDI footprints.
2. Treinar em GEDI e comparar com produto derivado de GEDI (L4B).
3. Usar a mesma parcela em treino e validação.
4. Selecionar features e hiperparâmetros no conjunto de teste.

Mitigação: separação espacial/temporal rígida, validação externa e registro do que foi usado onde.

## 7. Comparação com benchmarks

Comparar com CCI Biomass, Spawn, Avitabile e produtos nacionais:

- comparar **distribuições** (não só médias);
- mapear diferenças e explicar padrões (ex.: saturação, várzea, Cerrado);
- não tratar nenhum produto como verdade;
- registrar divergências como resultado, não como falha.

## 8. Critérios de aceite (proposta inicial, ajustável)

| Critério | Limite inicial sugerido |
|---|---|
| Viés relativo do total (blocos espaciais) | ≤ 10% |
| RMSE relativo | ≤ 30% (Amazônia), ≤ 40% (Cerrado) — a calibrar |
| Cobertura do IC 90% | 80–95% (nem otimista, nem excessivamente conservador) |
| Fração da área dentro da AOA | ≥ 90% do domínio de interesse |
| Estabilidade entre folds | variação do RMSE ≤ 20% |

Esses limites são **propostas** e precisam de aprovação (`docs/30`, Q6). Devem ser revistos com
base na literatura e no uso pretendido (MRV exige mais rigor que comunicação).

## 9. Relatório de validação (template)

1. Desenho de validação e por quê.
2. Conjuntos usados (com contagens e mapas).
3. Métricas por estrato e faixa.
4. Cobertura dos ICs.
5. Análise de resíduos (viés por AGBD, por região, por classe).
6. Comparação com benchmarks.
7. Ameaças à validade e o que não foi testado.
8. Veredito: aprovado / aprovado com ressalvas / reprovado, com justificativa.
