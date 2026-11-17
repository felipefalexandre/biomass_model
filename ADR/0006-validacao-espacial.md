# ADR-0006 — Validação por blocos espaciais e AOA

**Status:** aceito
**Data:** 2026-11-17

## Contexto

CV aleatório superestima o desempenho de mapas espaciais por autocorrelação (Roberts et al.
2017; Ploton et al. 2020).

## Decisão

Blocos espaciais (50–100 km) como métrica principal; LORO como teste de estresse; k-fold aleatório
apenas como diagnóstico. AOA obrigatória (Meyer & Pebesma 2021), com NNDM-LOO como opção
(Milà et al. 2022).

## Consequências

- Métricas mais realistas (e piores).
- Decisões mais defensáveis.
- Nenhum produto publicado sem AOA.

Ver `docs/13`, `docs/25` e `docs/26_registro_de_decisoes.md`.
