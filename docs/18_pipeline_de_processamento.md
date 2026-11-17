# 18 — Pipeline de processamento

## 1. Visão geral

O pipeline é uma sequência de etapas com artefatos versionados e contratos verificáveis. Inspira-se
no padrão já validado no pipeline de desmatamento (janelas de 2048 px, processamento por blocos,
QA por produto).

```
[1] config + validação
      │
[2] domínio (biomas, máscaras, grade)
      │
[3] features (S2, S1, Landsat, DEM, clima)
      │
[4] referência (GEDI, parcelas) + pareamento
      │
[5] dataset de treino (features + referência + pesos)
      │
[6] treino + validação (CV espacial, AOA)
      │
[7] predição wall-to-wall (janelas)
      │
[8] estimativa + incerteza (por domínio)
      │
[9] QA + relatórios + catálogo de artefatos
```

## 2. Etapas e artefatos

| Etapa | Entrada | Saída | Contrato |
|---|---|---|---|
| 1. Config | arquivo de config | config resolvido + hash | campos obrigatórios, paths válidos |
| 2. Domínio | biomas, MapBiomas, máscaras | raster de domínio + tabela de áreas | grade idêntica à de saída |
| 3. Features | cenas brutas | cubo de features por tile/ano | CRS/resolução/nodata iguais |
| 4. Referência | GEDI/parcelas | tabela pareada | posição, data, qualidade |
| 5. Dataset | features + referência | Parquet/feather + esquema | sem nulos silenciosos |
| 6. Modelo | dataset | modelo + métricas + AOA | reprodutível por seed |
| 7. Predição | modelo + features | COG por ano | dtype/ nodata/ compressão |
| 8. Estimativa | mapa + amostra | tabelas + IC | unidades declaradas |
| 9. QA | todos | relatório + manifesto | checagens automáticas |

## 3. Padrão de processamento por janelas

Reaproveitar o padrão do repositório de desmatamento:

- janela de 2048 × 2048 px;
- para a grade nacional (154.468 × 146.235 px), 76 janelas por linha, 5.472 no total;
- abrir todas as entradas na mesma janela; validar `window_bounds`/`window_intersects`;
- pular janelas sem pixels do domínio (economia);
- escrever saída por janela no COG;
- liberar memória explicitamente.

Regras:

1. **Nunca** ler o raster inteiro.
2. **Sempre** validar alinhamento antes de empilhar (mesma transform/dimensões).
3. **Nunca** assumir ordem de bandas; declarar.
4. **Sempre** tratar nodata de forma uniforme.

## 4. Configuração

Arquivo único (YAML/JSON) com:

```yaml
domain:
  biomes: [1, 3]
  classes: [...]
  year_start: 2016
  year_end: 2025
grid:
  crs: EPSG:4326
  res: 0.00026949458523585647
  window: 2048
features:
  sentinel2: {composites: [dry, wet], indices: [...]}
  sentinel1: {stats: [mean, p10, p90], polarizations: [VV, VH]}
reference:
  gedi: {product: L4A, filters: {...}}
model:
  algorithm: [glm, rf, xgb]
  cv: {type: spatial_blocks, block_km: 50}
output:
  dir: ...
```

Toda execução grava `run_manifest.json` com: versão do código (git), hash da config, versões de
bibliotecas, datas, seeds e caminhos.

## 5. Tratamento de falhas

- Cada etapa é idempotente e retomável.
- Artefatos parciais têm sufixo `.partial` e só são promovidos após validação.
- Falha em uma janela não derruba o lote; registra em `failures.csv` e continua.
- Reprocessamento por `--force` ou por detecção de hash divergente.

## 6. Testes

| Tipo | O que testa |
|---|---|
| unitário | funções puras (índices, área de pixel, conversões) |
| contrato de grade | alinhamento, CRS, nodata |
| integração | pipeline sintético pequeno ponta a ponta |
| regressão | resultados numéricos estáveis em dataset de fixture |
| propriedade | invariantes (área > 0, AGBD ≥ 0, máscara consistente) |

Fixtures: rasters sintéticos pequenos com valores conhecidos, como já feito no repositório de
desmatamento (GeoJSON de biomas, municípios, rasters 2004–2025).

## 7. Estrutura de pastas proposta

```
biomassa-br/
  configs/
  src/biomassa/
    domain/ features/ reference/ models/ inference/ io/ qa/
  tests/
  data/            (não versionar dados brutos grandes)
  outputs/
    features/
    models/
    maps/
    estimates/
    reports/
    logs/
```

## 8. Critérios de saída de etapa

- artefato existe, abre, tem hash e metadados;
- QA da etapa passou;
- manifesto atualizado;
- nenhum aviso crítico pendente.

## 9. Anti-padrões proibidos

- parâmetros mágicos no código;
- sobrescrever artefato sem versionar;
- usar `random` sem seed;
- ignorar warnings de CRS;
- medir desempenho no conjunto de treino;
- publicar mapa sem AOA.
