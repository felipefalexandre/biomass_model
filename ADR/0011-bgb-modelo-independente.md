# ADR-0011 — BGB como modelo separado, não derivado da AGB

**Status:** aceito
**Data:** 2026-11-17
**Substitui:** ADR-0005

## Contexto

O ADR-0005 tratava BGB como módulo derivado da AGB por razão raiz/parte aérea (R:S) e equações,
com três cenários. O usuário decidiu que BGB deve ser um **modelo próprio, focado em solo**,
acoplado ao sistema de AGB "de alguma forma", e não uma estimativa que interfira na AGB (nem seja
apenas AGB × fator).

BGB não é observável por satélite; a relação AGB–BGB varia com bioma, fisionomia, solo, fogo e
idade. Assumir R:S constante é uma simplificação forte, especialmente no Cerrado.

## Opções

1. R:S/equação a partir da AGB (ADR-0005).
2. Modelo independente de BGB com preditores de solo, clima e estrutura.
3. Híbrido: modelo independente como central; R:S como cenário/base de comparação.

## Decisão

Adotar a opção 3:

- **Modelo central de BGB:** treinado em dados de raiz (escavações/monolitos) e preditores de
  solo (SoilGrids: textura, carbono, profundidade, drenagem), clima (ERA5-Land), fisionomia
  (classe 3/4, tipologia) e, quando disponível, estrutura da vegetação (altura/AGB como
  covariável **opcional**, não como única entrada).
- **R:S derivado da AGB:** mantido apenas como (a) linha de base para comparação, (b) cenário de
  sensibilidade e (c) preenchimento onde não há modelo aplicável — sempre rotulado.
- **Acoplamento:** AGB e BGB compartilham grade, máscara, domínio e módulo de incerteza, mas são
  estimados separadamente; a variância total soma as duas com a covariância declarada.
- **Cerrado:** BGB é material no total (Ribeiro et al. 2011: 37,5 Mg ha⁻¹ para AGB de 63,0
  Mg ha⁻¹); o modelo de solo é obrigatório, não opcional.

## Consequências

- Incerteza de BGB maior e mais honesta; não se afirma "BGB medida por satélite".
- Necessidade de inventariar dados de raiz (Ribeiro 2011; Oliveira 2019; RAINFOR/ESCANA;
  literatura de Cerrado) e declarar a escassez.
- O produto final distingue claramente: AGB observada/modelada, BGB modelada, total.
- Se não houver dados de raiz suficientes para um bioma, o modelo independente é rebaixado a
  cenário e isso é registrado como limitação, não escondido.

## Evidência

- Ribeiro et al. 2011, DOI 10.1016/j.foreco.2011.04.017.
- Oliveira et al. 2019, DOI 10.1186/s13021-019-0121-0.
- Ver `docs/10`, `docs/22` (RC04/RE05) e `docs/26`.
