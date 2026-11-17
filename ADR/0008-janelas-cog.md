# ADR-0008 — Janelas e COG

**Status:** aceito
**Data:** 2026-11-17

## Contexto

A grade nacional tem 154.468 × 146.235 px; ler o raster inteiro é inviável. O pipeline de
desmatamento já validou janelas de 2048 px (76 por linha, 5.472 no total) e COG.

## Decisão

Processar por janelas de 2048 × 2048 px, com validação de alinhamento antes de empilhar, e
gravar saídas em COG (blocos 512, DEFLATE).

## Consequências

- Complexidade de código e necessidade de retomada.
- Escalabilidade, baixo uso de memória e leitura eficiente.
- Reaproveitamento de padrão já testado.

Ver `docs/18` e `docs/26_registro_de_decisoes.md`.
