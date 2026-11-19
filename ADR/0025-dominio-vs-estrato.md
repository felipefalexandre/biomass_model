# ADR-0025 — Domínio 3/4 é filtro espacial; fitofisionomia é estrato separado

- **Data:** 2026-11-18
- **Status:** aceito (decorre da clarificação do usuário)
- **Contexto:** as classes 3 (Formação Florestal) e 4 (Formação Savânica) da Coleção 11 são
  classes agregadas, cujas descrições remetem a várias fitofisionomias IBGE. Elas não separam
  ombrófila densa/aberta/estacional nem cerrado típico/rupestre por pixel.
- **Decisão:**
  1. 3/4 definem o **domínio espacial** (onde o produto é válido), não a taxonomia final.
  2. Fitofisionomia/estrato é uma camada separada, derivada de IBGE 1:250k, MapBiomas Vegetação
     Secundária, estrutura de satélite e/ou composição fornecida pelo usuário.
  3. Nenhuma fórmula alométrica de árvore será aplicada a pixel; priors/médias por estrato são
     calibrados com campo/modelo e declarados com incerteza.
- **Consequências:** o produto reporta por domínio 3/4 e por estrato; classes 2 (campestre) e 6
  (floresta alagável) ficam fora até decisão explícita.
- **Arquivos:** `docs/36`, `docs/41`, `data/reference/fitofisionomias_crosswalk.csv`.
