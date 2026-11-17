# 02 — Perguntas de pesquisa e hipóteses

## 1. Perguntas primárias

**P1. Qual é a AGBD média e total por bioma, ano e classe de vegetação, com incerteza de 90%?**
Requer: estimandos (01), desenho de inferência (12), validação (13).

**P2. É possível obter estimativas defensáveis apenas com dados abertos?**
Hipótese: sim, com desempenho inferior a levantamentos LiDAR dedicados, mas com incerteza
honesta. Teste: comparar com benchmarks publicados e com produtos globais (ver P6).

**P3. Modelos separados por bioma superam um modelo único?**
Hipótese H3: sim, especialmente no Cerrado, onde a relação estrutura–reflectância difere.
Teste: validação espacial cruzada com e sem estratificação por bioma.

**P4. Quais sensores contribuem de forma marginal significativa?**
Hipótese H4: Sentinel-2 (óptico) domina; Sentinel-1 (radar) agrega em áreas de nuvem e estrutura
vertical; DEM agrega pouco; clima agrega em escala regional.
Teste: ablação de features com validação espacial.

**P5. GEDI L4A é uma referência adequada para o Cerrado?**
Hipótese H5: parcialmente — boa em fisionomias arborizadas, fraca em campo sujo/limpo e em
biomassa muito baixa, com viés e menor cobertura.
Teste: comparação com parcelas independentes e análise de erro por faixa de AGBD.

**P6. Como as estimativas se comparam a produtos globais existentes?**
Produtos: CCI Biomass (Santoro 2021), GEDI L4B agregado, mapas globais de AGBD publicados.
Hipótese H6: divergências regionais grandes (>30%) em Amazônia; não há "verdade" única.
Teste: comparação de distribuições e mapas de diferença, não de um único número.

**P7. Qual é a incerteza dominante: amostragem, modelo ou referência?**
Hipótese H7: em domínios grandes, a incerteza de modelo/referência domina; em polígonos
pequenos, a de amostragem domina.
Teste: decomposição de variância (`docs/12`).

**P8. A estimativa de BGB no Cerrado é confiável?**
Hipótese H8: não no mesmo nível da AGB; a razão raiz/parte aérea varia com fogo, solo e
fisionomia. Teste: análise de sensibilidade a equações e razões.

**P9. A mudança temporal de AGB é detectável com a série disponível?**
Hipótese H9: mudanças grandes (desmatamento) sim; ganhos incrementais e degradação, apenas com
limitações e em janelas plurianuais.
Teste: simulação de poder de detecção e comparação com MapBiomas/desmatamento.

## 2. Hipóteses nulas e testes

| Hipótese | Nula | Estatística/abordagem |
|---|---|---|
| H3 (estratificação) | erro de validação igual entre modelos | diferença de RMSE pareada em blocos espaciais |
| H4 (features) | contribuição marginal = 0 | ablação + importância permutada + CV espacial |
| H5 (GEDI Cerrado) | erro independente da faixa de AGBD | regressão de resíduo vs AGBD, teste de Breusch–Pagan |
| H7 (variância) | componente de modelo = 0 | decomposição bootstrap |
| H9 (mudança) | ΔAGB indistinguível de 0 | intervalo de confiança da diferença |

## 3. Perguntas de engenharia

- E1. Como processar ~5472 janelas de 2048 px sem estourar memória? (já resolvido no pipeline de
  desmatamento; reutilizar padrão de janelas).
- E2. Como garantir que a grade de features coincida com a grade de saída? (contrato de grade;
  `docs/18`).
- E3. Como versionar modelos, features e máscaras de forma que uma estimativa antiga seja
  reproduzível? (`docs/19`).
- E4. Como responder consultas por polígono em tempo aceitável? (`docs/17`).

## 4. Perguntas que exigem decisão do usuário

Ver `docs/30`. Nenhuma delas deve ser respondida por suposição silenciosa.
