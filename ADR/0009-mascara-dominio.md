# ADR-0009 — Máscara de elegibilidade como domínio

**Status:** substituído por ADR-0010
**Data:** 2026-11-17

## Contexto

A etapa anterior definiu elegibilidade como classe 3/4 do MapBiomas em **todos** os anos
2007–2016, produzindo uma máscara (1 elegível, 0 não elegível, 255 fora/nodata). Isso exclui
regeneração e vegetação que mudou de classe no período.

## Decisão

Usar essa máscara como domínio declarado do produto de biomassa, mantendo comparabilidade com os
totais da etapa anterior. Declarar explicitamente que o total é de **vegetação nativa estável**,
não de toda a cobertura lenhosa.

## Consequências

- Totais comparáveis (622.532.566,8 ha de área de estudo; 386.714.878,6 ha elegíveis).
- Limitação de escopo documentada (RE01).
- Necessidade de produto alternativo se o usuário quiser toda a vegetação.

Ver `docs/17`, `docs/22` e `docs/26_registro_de_decisoes.md`.
