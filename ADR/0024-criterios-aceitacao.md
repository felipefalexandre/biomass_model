# ADR-0024 — Critérios de aceitação e promoção de modelos

- **Data:** 2026-11-18
- **Status:** proposto (aguarda aprovação)
- **Contexto:** R² médio contra GEDI pode melhorar sem ganho real de generalização, mudança ou campo.
- **Decisão:** promover um modelo só se atender a todos:
  1. espacial: RMSE mediano por box não pior que A0; nenhum box >5% pior; redução ≥15% em metade dos boxes;
  2. temporal: ≥80% de sinal correto em perda, ≥70% em ganho; |Δ| em áreas estáveis ≤10 Mg/ha/ano (p90); viés de tendência ≤2 Mg/ha/ano;
  3. contraste: Δ dentro do evento ≥3× o buffer em ≥70% dos eventos;
  4. campo: R² ≥0,40 e |viés| ≤15% em validação independente;
  5. incerteza: cobertura IC90 85–95% por bioma/ano;
  6. independência: zero GEDI no inference (auditado);
  7. reprodutibilidade: pipeline anual completo com manifesto e testes.
- **Consequências:** ausência de campo suficiente mantém o modelo como experimental; resultados negativos são registrados e o baseline é mantido.
- **Arquivos:** docs/37 §6, docs/39 §7.