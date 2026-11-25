# ADR-0028 — Produto C: estimativa por polígono arbitrário

- **Data:** 2026-11-24
- **Status:** aceito (decisão do usuário)
- **Substitui parcialmente:** ADR-0026 (mapa-first com polígono apenas como cálculo do usuário)

## Contexto

O novo escopo exige que o sistema receba polígonos em formatos geoespaciais amplamente
utilizados, informe o ano de referência e produza estoque de AGB com incerteza, área elegível,
individualização por fitofisionomia e limitações de aplicabilidade. O `polygon-stats` atual
agrega CSV por filtro; não lê geometria, não calcula interseção real e não gera relatório.

## Decisão

1. O **Produto C** (polígono arbitrário) é produto de primeira classe, não apenas utilidade de
   QA.
2. O módulo deve aceitar GeoJSON, GeoPackage e Shapefile; validar geometria e CRS; reprojetar
   para o CRS do raster.
3. A área elegível deve considerar a **interseção real célula–polígono**, inclusive células de
   borda e furos.
4. O resultado deve conter, no mínimo: área do polígono, área elegível analisada, área excluída,
   AGB média, mediana, estoque total, intervalo de incerteza, número de células, fração na AOA,
   resultados por fitofisionomia e limitações.
5. O Produto A (mapa por pixel) permanece necessário como base espacial e para sobreposição com
   mapas externos de atividade. O Produto C não substitui o mapa; ele o consulta.
6. Diferenciar explicitamente Mg ha⁻¹, Mg, Mg C e Mg CO₂e. Conversões para carbono/CO₂e ficam em
   módulo posterior.

## Consequências

- `ADR-0026` deixa de afirmar que o polígono é apenas cálculo do usuário.
- A agregação deve usar área real, não um número fixo de hectares por linha.
- A incerteza do estoque deve ser propagada por blocos espaciais e declarar os componentes
  incluídos e excluídos.

## Arquivos

`docs/41`, `docs/46`, `src/biomass_model/aggregation/`, `src/biomass_model/polygon.py`.
