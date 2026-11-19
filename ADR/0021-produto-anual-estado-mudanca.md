# ADR-0021 — Produto anual de biomassa (sem modelar desmatamento)

- **Data:** 2026-11-18 · **Revisado:** 2026-11-18
- **Status:** aceito
- **Contexto:** o pipeline atual usa um compósito S2 multi-ano (2020–2024) para todos os
  footprints. Isso não representa o estado de um ano. O objetivo é estimar biomassa anual a partir
  de dados do ano, para alimentar cálculos de projetos (REDD+/ARR). Desmatamento/reflorestamento
  são mapas e modelos **externos**; o modelo de biomassa não os estima.
- **Decisão:**
  1. AGBD_t por célula (1 km oficial; 30 m diagnóstico), estimada com features do ano t.
  2. Estoque_t por polígono e por estrato, com incerteza.
  3. Diferenças entre mapas anuais são cálculo do usuário/externo; o modelo não faz contabilidade
     de perda/ganho, não detecta eventos e não prevê desmatamento.
  4. Covariáveis de estado (idade secundária, histórico de fogo) são opcionais e só entram se
     melhorarem a estimativa de AGBD; não são alvo nem critério de mudança.
- **Consequências:** features anuais obrigatórias; anos sem observação não são estimados;
  consistência temporal é diagnóstico de qualidade, não critério de detecção.
- **Arquivos:** `docs/37`, `docs/41`, `docs/44`.
