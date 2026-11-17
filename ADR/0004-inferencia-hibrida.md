# ADR-0004 — Inferência híbrida

**Status:** aceito
**Data:** 2026-11-17

## Contexto

Design-based puro não se aplica (GEDI não é amostra probabilística). Model-based puro ignora a
incerteza de amostragem.

## Decisão

Inferência híbrida/quasi-design, com decomposição de variância em: amostragem, modelo e
referência. Bootstrap por blocos espaciais.

## Consequências

- IC mais honestos.
- Necessidade de declarar suposições e limitações.
- Maior custo computacional na validação.

Ver `docs/12` e `docs/26_registro_de_decisoes.md`.
