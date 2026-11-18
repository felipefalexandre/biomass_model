# ADR-0015 — Referência do Cerrado: campo primeiro, GEDI como auxiliar

**Status:** aceito
**Data:** 2026-11-17

## Contexto

O ADR-0003 definiu GEDI L4A como referência principal. A extração em lote no piloto do Cerrado
(`-47,70, -13,95`; 2019–2024) produziu 16.851 footprints válidos com **mediana de 6,2 Mg ha⁻¹** e
**59,6% abaixo de 10 Mg ha⁻¹**. No mesmo piloto, o painel do IFN/SFB tem mediana de 19,4 Mg ha⁻¹
para o Cerrado. A subestimação do L4A em savana aberta é conhecida (viés de modelo em AGB baixa e
estrutura esparsa) e não é corrigível por filtro de qualidade.

Treinar o modelo do Cerrado em L4A reproduziria esse viés e o esconderia atrás de boas métricas
contra o próprio L4A.

## Decisão

- **Cerrado (v1):** referência primária são **parcelas de campo com coordenadas** (IFN/SFB,
  PLOS 2018, RAINFOR e demais fontes do `data/reference/inventarios_abertos`). GEDI L4A passa a
  (a) covariável auxiliar de estrutura, (b) benchmark externo e (c) diagnóstico de cobertura —
  **não** alvo de treino.
- **Amazônia:** mantém L4A como referência principal (ADR-0003), com validação em parcelas.
- A comparação L4A × campo no Cerrado é reportada explicitamente como evidência de limitação.
- Se o número de parcelas de campo for insuficiente, o modelo do Cerrado é rebaixado a cenário
  regional estratificado, e isso é declarado — não se volta a treinar em L4A por conveniência.

## Consequências

- Menos observações de treino no Cerrado e necessidade de harmonizar equações/Diâmetro mínimo.
- Métricas do Cerrado serão mais fracas e mais honestas; nenhuma métrica contra L4A será
  apresentada como validação.
- Reforça a prioridade de obter INV03–INV10 e parcelas do Cerrado.
- Documentado em `docs/09`, `docs/22` (RC03) e `docs/31`.

## Evidência

- `E:\Mapbiomas\biomass\gedi\cerrado_l4a_v21_2019_2024.csv` e resumo em
  `data/reference/gedi_pilotos_resumo.csv`.
- Painel SFB: mediana 19,4 Mg ha⁻¹ (Cerrado).
- Duncanson et al. (2022), ATBD GEDI L4A; literatura de viés em savana.
