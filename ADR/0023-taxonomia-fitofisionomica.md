# ADR-0023 — Taxonomia fitofisionômica e critérios de especialização

- **Data:** 2026-11-18
- **Status:** aceito (2026-11-24); implementação detalhada em ADR-0029
- **Contexto:** classe de uso/cobertura do MapBiomas não é fitofisionomia; o domínio 3/4 agrupa fisionomias com relações AGB distintas.
- **Decisão:** adotar hierarquia em níveis (bioma; grupo de formação; fisionomia; estrutura contínua; estado sucessional/perturbação; contexto) conforme docs/36 §3, usando IBGE (Manual Técnico da Vegetação Brasileira), MapBiomas, MapBiomas Vegetação Secundária e estrutura derivada de satélite.
- **Especialização:** modelo por fisionomia só se houver ≥8 blocos de 5 km, ≥500 células de 1 km, ≥2 boxes e amplitude de AGB ≥50 Mg/ha; caso contrário, feature categórica ou partial pooling.
- **Limite:** não inventar fisionomias onde o mapa não separa; declarar granularidade efetiva.
- **Arquivos:** docs/36, docs/37.