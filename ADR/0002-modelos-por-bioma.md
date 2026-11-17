# ADR-0002 — Dois modelos por bioma e escada de complexidade

**Status:** aceito
**Data:** 2026-11-17

## Contexto

Amazônia e Cerrado têm estruturas e faixas de biomassa distintas; modelos globais degradam o
Cerrado. Complexidade sem ganho é custo.

## Decisão

Modelos separados por bioma. Começar em M0 (média estratificada) e M1 (GLM), subindo para
RF/XGBoost somente com ganho validado por CV espacial.

## Consequências

- Mais artefatos e validações.
- Menor risco de overfitting por complexidade desnecessária.
- Empate técnico favorece o modelo mais interpretável.

Ver `docs/26_registro_de_decisoes.md`.
