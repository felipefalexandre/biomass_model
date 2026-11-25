# ADR-0003 — GEDI L4A como referência principal

**Status:** aceito com ressalva; substituído parcialmente por ADR-0027 (campo primário, GEDI auxiliar)
**Data:** 2026-11-17

## Contexto

GEDI oferece cobertura amostral ampla e estrutura vertical. Porém L4A é produto de modelo, com
erro próprio, pior em AGB alta e em savana, e cobertura não aleatória.

## Decisão

Usar L4A como referência principal, com filtros de qualidade, AOA e validação independente.
Declarar explicitamente que é produto de modelo.

## Consequências

- Viável em escala.
- Exige cuidado com circularidade e viés no Cerrado.
- Inferência classificada como quasi-design.

Ver `docs/26_registro_de_decisoes.md` e redflag RF06.
