# ADR-0022 — GEDI apenas como calibração e avaliação

- **Data:** 2026-11-18
- **Status:** proposto (aguarda aprovação)
- **Contexto:** o objetivo é estimar biomassa sem depender de outro produto no momento da estimativa. GEDI L4A é modelado e tem cobertura temporal limitada (2019–2023/24).
- **Decisão:**
  1. Nenhum produto de biomassa (GEDI L4A/L4B, CCI, EBA, mapas nacionais) entra como feature, prior ou ajuste no inference.
  2. GEDI é usado apenas para treinar/calibrar a relação satélite→AGB e para a Linha A de avaliação.
  3. Auditoria de independência obrigatória em cada modelo promovido: lista de features, proveniência e teste de que a predição funciona sem GEDI.
- **Consequências:** features precisam ser anuais e disponíveis em toda a série; a calibração fica restrita a 2019–2024 e depende de campo/ORNL para anos anteriores.
- **Arquivos:** docs/35, docs/37, docs/38.