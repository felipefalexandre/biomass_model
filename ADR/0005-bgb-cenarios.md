# ADR-0005 — BGB derivada com cenários

**Status:** substituído por ADR-0011
**Data:** 2026-11-17

## Contexto

Biomassa abaixo do solo não é observável por sensoriamento remoto; razões e equações variam com
bioma, fisionomia, solo e fogo.

## Decisão

BGB como módulo derivado, com três cenários (mínimo, central, máximo) e fonte explícita do
parâmetro. Nunca apresentar BGB como "medida".

## Consequências

- Transparência sobre a incerteza.
- Necessidade de propagar variância (AGB + parâmetro).
- No Cerrado, BGB é material no total (ver Ribeiro et al. 2011).

Ver `docs/10` e `docs/26_registro_de_decisoes.md`.
