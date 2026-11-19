# ADR-0024 — Critérios de aceitação e promoção de modelos

- **Data:** 2026-11-18 · **Revisado:** 2026-11-18
- **Status:** aceito
- **Contexto:** R² médio contra GEDI pode melhorar sem ganho real de generalização, campo ou
  robustez. O escopo do modelo é biomassa, não detecção de desmatamento.
- **Decisão:** promover um modelo só se atender a todos:
  1. espacial: RMSE mediano por box não pior que A0; nenhum box >5% pior; redução ≥15% em metade
     dos boxes;
  2. campo: R² ≥0,40 e |viés| ≤15% em validação independente;
  3. polígono: erro do total compatível com o IC declarado; sem viés agregado >15%;
  4. incerteza: cobertura IC90 85–95% por bioma/ano;
  5. independência: zero GEDI/derivados no inference (auditado);
  6. estabilidade: sem oscilação anual sistemática atribuível a ruído de features (diagnóstico,
     não detecção de desmatamento);
  7. reprodutibilidade: pipeline anual completo com manifesto e testes.
- **Consequências:** ausência de campo suficiente mantém o modelo como experimental; resultados
  negativos são registrados e o baseline é mantido. Detecção de desmatamento não é critério.
- **Arquivos:** `docs/37` §6, `docs/44`.
