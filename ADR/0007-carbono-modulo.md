# ADR-0007 — Carbono e CO₂e em módulo separado

**Status:** aceito
**Data:** 2026-11-17

## Contexto

Confusão entre biomassa, carbono e CO₂e é erro recorrente e grave. Fatores (f_C, 44/12) precisam
ser explícitos e versionados.

## Decisão

Módulo separado de conversão, com `f_C` declarado (padrão 0,47, a confirmar por tabela IPCC),
CO₂e = C × 44/12, e somente CO₂ por padrão.

## Consequências

- Nenhum número de carbono/CO₂e sem unidade e fator.
- Propagação de incerteza das conversões.
- Clareza para auditoria.

Ver `docs/11` e `docs/26_registro_de_decisoes.md`.
