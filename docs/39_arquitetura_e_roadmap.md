# 39 — Arquitetura Python, sequência de implementação e riscos

**Data:** 2026-11-18 · **Status:** proposta; não implementar antes de aprovação.

## 1. Princípios de engenharia

- Preservar o pipeline atual e os resultados de `docs/33`; nada é sobrescrito.
- Um experimento = uma configuração versionada + manifesto + métricas + predições.
- Nenhuma dependência nova sem necessidade demonstrada; extras opcionais isolados.
- Todo produto anual é reprodutível por ano e por tile, com hash e versão de features.
- Testes de regressão comparam o baseline A0 antes/depois de cada mudança.

## 2. Módulos propostos

```
src/biomass_model/
  datasets/
    s2_annual.py        # compósito e métricas fenológicas por ano
    s1_annual.py        # estatísticas anuais VV/VH/RVI
    landsat_annual.py   # série anual 1984+ para anos pré-S2
    fire.py             # MapBiomas Fogo: cicatriz, idade, frequência
    prodes.py           # incremento anual e distância à borda
    secondary.py        # MapBiomas Vegetação Secundária (idade)
    soilgrids.py        # argila/areia/SOC (WCS, sem conta)
    gedi.py             # já existe; acrescentar leitura de L2B/L4C se aprovado
  features/
    annual.py           # monta o cubo anual por célula/tile
    fitofisionomia.py   # taxonomia e mapeamento de fontes
    change.py           # transições, perda/ganho, features de evento
  models/
    direct.py           # A1/A2 (RF/GBM)
    hierarchical.py     # A3 (partial pooling; statsmodels ou Bayes opcional)
    change.py           # A4 (ΔAGB)
    state_space.py      # A5/A6 (filtro/Kalman/partícula simplificado)
    registry.py         # versões, hiperparâmetros, seeds
  evaluation/
    spatial_cv.py       # LOO box (reaproveita modeling)
    temporal_cv.py      # leave-one-year-out
    change_tests.py     # sinal/contraste/falso alarme/defasagem
    conformal.py        # já existe; estratificar por ano/fisionomia
    aoa.py              # já existe; versionar
    polygon.py          # agregação, block bootstrap, cobertura
  inference/
    annual_map.py       # aplica modelo por tile/ano, máscaras, COG, IC
    accounting.py       # estoque e balanço de transições
  cli.py                # novos subcomandos
configs/
  experiments/E0.yaml ... E9.yaml
```

### 2.1 Interfaces principais

- `build_annual_cube(year, tile, out_dir, sensors=(s2,s1,landsat), change=True)` → COG/Parquet
  por tile com bandas nomeadas e metadados de data.
- `train(model_id, config, train_years, split)` → artefato + métricas + manifesto.
- `predict_map(model_id, year, tile)` → AGBD + IC + AOA + máscara de domínio.
- `evaluate(model_id, splits, metrics)` → relatório por box/ano/fisionomia/evento.
- `account(year, prev_year)` → estoque, perda, ganho, reconciliação.

### 2.2 Novos subcomandos (propostos)

`annual-features`, `annual-map`, `temporal-cv`, `change-tests`, `polygon-eval`,
`calibration-curve`, `fitofisionomia-map`.

## 3. Sequência de implementação

| Fase | Entrega | Depende de | Critério de saída |
|---|---|---|---|
| P1 | Features anuais S2/S1 (2019–2024) + E1 | Aprovação | A1 reproduzível; comparação com A0 |
| P2 | Fogo/PRODES/secundária + E2 + testes de mudança | P1 + dados | Sinal ≥ 80% em perda; estabilidade |
| P3 | Fisionomia (nível 1–2) + E3 | P2 + taxonomia | Viés por fisionomia reduzido |
| P4 | Hierárquico A3 + E4 | P3 | Partial pooling supera A1/A2 |
| P5 | Mudança/estado A4/A5 + E5/E6 | P1–P2 | Redução de falso ganho e melhor contraste |
| P6 | PLOS/ORNL + curvas de calibração E7 | P1 + dados de campo | Linha B com ≥ 30 sítios |
| P7 | Polígono/incerteza E9 | P1–P6 | Cobertura IC do estoque |
| P8 | Produto anual (COG + modelo card) | P7 | Aceite nos critérios de `docs/37` |

Cada fase termina com commit, ADR (se decisão), atualização do diário e relatório de métricas.

## 4. Dependências

- **Já disponíveis:** numpy, pandas, rasterio, geopandas, sklearn, scipy, pyproj, netCDF4,
  pystac-client, planetary-computer, cdsapi, earthaccess.
- **Novas prováveis:** `statsmodels` (mixed-effects) ou `pymc` (opcional, extra `bayes`);
  `pyarrow` (Parquet); `shapely` já vem com geopandas. Nada obrigatório para P1–P2.
- **Evitar:** GEE (ADR-0001), APIs pagas, dependência de h5py.

## 5. Riscos e mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Série S2 começar em 2015 | anos antigos sem óptico fino | Landsat anual 1984+ |
| GEDI só 2019–2023/24 | calibração não cobre anos futuros | reavaliação anual; campo; ORNL histórico |
| Drift de sensores/atmosfera | mudanças espúrias | harmonização, calibração por ano, testes de estável |
| Erro de MapBiomas | transições falsas | incerteza de classe; não usar como rótulo duro |
| Prior temporal suavizar demais | perda não detectada | perda assimétrica; testes de evento |
| Extrapolação em AGB alta/baixa | viés | AOA + limites declarados + modelos por estrato |
| Custo de campo | inviabiliza calibração | curvas de aprendizado; parcerias; ORNL/IFN |
| Complexidade de Bayes | prazo | começar por mixed-effects/approx; Bayes opcional |

## 6. ADRs propostas

- ADR-0020: validação em duas linhas (GEDI vs campo) + linha temporal.
- ADR-0021: produto anual de estado e mudança (não mapa estático).
- ADR-0022: GEDI apenas como calibração; auditoria de independência no inference.
- ADR-0023: taxonomia fitofisionômica e critérios de especialização.
- ADR-0024: critérios de aceitação e promoção de modelos.

## 7. Definition of done (por experimento)

1. Hipótese e critério de decisão escritos antes da execução.
2. Split espacial/temporal registrado; teste intocado até o fim.
3. Métricas por box/ano/fisionomia/evento, com IC.
4. Comparação com A0 e com o melhor candidato anterior.
5. Artefatos: config, manifesto, predições, métricas, figura/tabela.
6. Decisão registrada (adotado/rejeitado) e diário atualizado.
7. Se adotado: testes de regressão e model card atualizado.
