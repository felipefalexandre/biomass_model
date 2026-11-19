# ADR-0020 — Validação em duas linhas e linha temporal

- **Data:** 2026-11-18
- **Status:** proposto (aguarda aprovação)
- **Contexto:** o alvo atual é GEDI L4A, um produto modelado. R² GEDI-versus-GEDI não mede acurácia de biomassa verdadeira, e o objetivo passou a ser estimativa anual do estoque a partir de satélite.
- **Decisão:** separar explicitamente três linhas:
  - Linha A: fidelidade/transferência ao GEDI (espacial).
  - Linha B: concordância com campo independente (PLOS, ORNL, IFN, novos campos).
  - Linha T: resposta temporal a mudanças conhecidas (perda, fogo, regeneração) e estabilidade onde não há mudança.
- **Regra:** nenhum resultado da Linha A será chamado de validação de campo; nenhuma melhoria só em A promove modelo.
- **Consequências:** relatórios passam a ter três blocos; critérios de aceite incluem A, B e T (docs/37).
- **Arquivos:** docs/35, docs/37, docs/38.