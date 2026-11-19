# ADR-0021 — Produto anual de estado e mudança

- **Data:** 2026-11-18
- **Status:** proposto (aguarda aprovação)
- **Contexto:** o pipeline atual usa um compósito S2 multi-ano (2020–2024) para todos os footprints. Isso não representa o estado de um ano nem mudanças anuais.
- **Decisão:** o produto passa a ser:
  1. AGBD_t por célula (1 km oficial; 30 m diagnóstico), estimada com features do ano t;
  2. estoque_t por polígono, com incerteza;
  3. ΔAGB_{t−1→t} com contabilidade explícita de perda e ganho (transições), não apenas máscara 3/4.
- **Modelo:** estado temporal com processo (crescimento gradual, perda abrupta) e observação por satélite; modelos candidatos em docs/37 §4 (A1–A6).
- **Prior assimétrico:** perda pode ser abrupta; ganho é limitado por taxas de crescimento. Isso evita ganhos espúrios e permite rastrear quedas.
- **Consequências:** features anuais obrigatórias; anos sem observação não são estimados; mapa e balanço de estoque são produtos separados e reconciliáveis.
- **Arquivos:** docs/37, docs/39.