# ADR-0012 — Filtro de qualidade do GEDI L4A

**Status:** aceito
**Data:** 2026-11-17

## Contexto

O GEDI L4A traz `l2_quality_flag`, `l4_quality_flag`, `degrade_flag` e `sensitivity` por
footprint. Sondagem de 6 granulos no piloto amazônico (2019–2024) mostrou:

- `degrade_flag` é um campo de bits com valores 0, 30, 70 e 80; exigir `degrade_flag == 0` elimina
  **todo** o granulo diurno de 2019 e o de 2023, que têm predições com `l4_quality_flag == 1`.
- Granulos noturnos de 2021 e 2022 no bbox têm `l2=0`, `l4=0` e `agbd=-9999` em todos os tiros; são
  inutilizáveis, não é falha de filtro.
- `sensitivity` acima de 1,01 aparece em poucos registros e é fisicamente impossível.

O produto já aplica controle de qualidade interno; `degrade_flag` sinaliza condições que afetam a
estimativa, mas não invalida automaticamente a predição.

## Decisão

Filtro primário:

```
l2_quality_flag == 1
l4_quality_flag == 1
agbd >= 0
0.9 <= sensitivity <= 1.01
```

`degrade_flag` **não** é filtro rígido na v1. Ele é mantido na tabela como `degrade_flag` e
`degrade_zero`, e toda modelagem roda também a sensibilidade restrita a `degrade_zero == True`.
A diferença de métricas entre os dois conjuntos é reportada.

## Consequências

- Amostra maior e uso de dados diurnos válidos; risco de viés por degradação é explicitado e
  testado, não escondido.
- Se a sensibilidade restrita degradar muito o desempenho, a decisão é revisada com evidência.
- O filtro fica em `biomass_model.datasets.gedi.quality_mask`, testado unitariamente.

## Evidência

- `probe_quality_summary.json` em `E:\Mapbiomas\biomass\gedi`.
- Duncanson et al. (2022), GEDI L4A Algorithm Theoretical Basis Document.
- Ver `docs/32` e `docs/15`.
