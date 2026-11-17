# 24 — Plano de implementação e fases

## 1. Filosofia

Entregar valor incremental com **critérios de saída** claros. Nenhuma fase avança sem QA e sem
decisão registrada. O escopo pode ser reduzido, mas não silenciosamente.

## 2. Fases

### Fase 0 — Fundação (curta)

- [x] Planejamento documental (este repositório).
- [ ] Resolver perguntas abertas críticas (`docs/30`).
- [ ] Definir licença dos produtos.
- [ ] Congelar escopo (biomas, anos, domínio).

**Saída:** escopo aprovado; perguntas críticas respondidas; catálogo com licenças.

### Fase 1 — Piloto de dados e features

- Escolher 2 regiões piloto (1 Amazônia, 1 Cerrado), ~1–2 tiles.
- Baixar S2, S1, DEM, clima; gerar features; verificar cobertura.
- Baixar GEDI L4A do piloto; parear.
- Rodar baseline (M0/M1) e CV espacial.

**Saída:** pipeline mínimo reprodutível; relatório de viabilidade; estimativa de custo/tempo
para escala nacional.

**Critério de saída:** features abrem, alinhamento validado, baseline com métricas, nenhum
bloqueio estrutural.

### Fase 2 — Referência e validação

- Consolidar GEDI filtrado; compilar parcelas disponíveis.
- Definir estratos e AOA.
- Validar baseline; comparar com benchmarks.
- Decidir se o modelo precisa subir de complexidade.

**Saída:** relatório de referência; métricas por estrato; decisão de modelo (ADR).

### Fase 3 — Modelo principal

- Treinar M1–M3 por bioma; seleção por CV espacial.
- Calibrar; gerar mapa piloto com incerteza.
- Análise de sensibilidade.

**Saída:** modelo selecionado; mapa piloto; model card.

### Fase 4 — Escala nacional

- Predição wall-to-wall por ano.
- Estimativas por domínio com IC.
- QA completo; comparação com benchmarks.

**Saída:** mapas COG, tabelas de estimativa, relatório de validação, manifesto.

### Fase 5 — Produtos e consultas

- Consulta por polígono.
- Relatórios por bioma/município/UC/TI.
- Publicação e documentação.

**Saída:** produto utilizável, documentado e citável.

### Fase 6 — Extensões (opcional)

- Mudança temporal e emissões por desmatamento.
- Degradação (exploratória).
- BGB refinada.
- Atualização anual.

## 3. Cronograma indicativo

| Fase | Duração estimada | Dependência |
|---|---|---|
| 0 | 1–2 semanas | decisões do usuário |
| 1 | 3–6 semanas | acesso a dados |
| 2 | 2–4 semanas | campo/compilação |
| 3 | 3–6 semanas | Fase 1–2 |
| 4 | 4–8 semanas | Fase 3 + infraestrutura |
| 5 | 2–4 semanas | Fase 4 |
| 6 | contínuo | Fase 5 |

São estimativas de ordem de grandeza; devem ser revistas após o piloto.

## 4. Papéis (mínimo)

| Papel | Responsabilidade |
|---|---|
| Ciência | estimandos, método, validação |
| Dados | catálogo, aquisição, QA |
| Engenharia | pipeline, performance, reprodutibilidade |
| Governança | licenças, ética, publicação |
| Revisão | auditoria independente |

## 5. Critérios de parada

Parar e reavaliar se:

- a referência não sustenta a estimativa no estrato-alvo;
- o custo computacional excede o disponível;
- a licença impede o uso pretendido;
- o escopo muda de forma que invalide decisões anteriores.

## 6. Entregáveis por fase (checklist)

**Fase 0**
- [ ] Escopo assinado
- [ ] Licença definida
- [ ] Perguntas críticas respondidas

**Fase 1**
- [ ] Pipeline piloto
- [ ] Relatório de viabilidade
- [ ] Estimativa de custo

**Fase 2**
- [ ] Referência consolidada
- [ ] Métricas por estrato
- [ ] AOA

**Fase 3**
- [ ] Modelo selecionado
- [ ] Mapa piloto
- [ ] Model card

**Fase 4**
- [ ] Mapas nacionais
- [ ] Tabelas com IC
- [ ] Relatório de validação

**Fase 5**
- [ ] Consultas por polígono
- [ ] Documentação
- [ ] Publicação

## 7. Riscos de cronograma

- Acesso a dados (IFN, GEE) pode atrasar.
- Qualidade do GEDI no Cerrado pode exigir campo extra.
- Escala nacional pode exigir mais disco do que o previsto.
- Revisão jurídica de licenças pode ser lenta.

Mitigação: começar pelo piloto; não prometer prazo nacional antes de medir.
