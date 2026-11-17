# 15 — Sensores e engenharia de features

## 1. Princípios de feature engineering

1. **Física antes de algoritmo.** Cada feature deve ter justificativa físico-biológica.
2. **Estabilidade temporal.** Evitar features que mudam por calibração, não por vegetação.
3. **Redundância controlada.** Muitas features correlacionadas aumentam overfitting e custo.
4. **Cobertura.** Features ausentes por nuvem/órbita não podem virar zero silenciosamente.
5. **Versionamento.** O conjunto de features é um artefato versionado, não um script ad hoc.

## 2. Sentinel-2 (óptico, 10–20 m)

### 2.1 Composições

- Composições **sazonais** (seca e chuvosa) por ano, usando mediana e percentis (p10, p90).
- Mascaramento de nuvem/sombra com `SCL` (Scene Classification Layer) do L2A e/ou máscara própria.
- Registrar o número de observações válidas por pixel (feature de qualidade).

### 2.2 Bandas e índices

| Feature | Fórmula/definição | Racional |
|---|---|---|
| B02, B03, B04, B08, B11, B12 | reflectância | base espectral |
| NDVI | (B08−B04)/(B08+B04) | vigor/cobertura |
| EVI | 2,5(B08−B04)/(B08+6B04−7,5B02+1) | reduz saturação |
| SAVI | (B08−B04)(1+L)/(B08+B04+L) | solo exposto |
| NDII | (B08−B11)/(B08+B11) | umidade da vegetação |
| NBR | (B08−B12)/(B08+B12) | severidade de fogo |
| NDMI | (B08−B11)/(B08+B11) | umidade |
| MSAVI2 | forma autoajustável | solo |
| Índices de clorofila/red-edge | B05–B07 | estresse/composição |

### 2.3 Textura

- GLCM (contraste, homogeneidade, entropia, correlação) em janelas 3×3 a 11×11.
- Variograma local ou desvio-padrão local.
- Racional: dossel heterogêneo vs homogêneo; savana esparsa vs floresta contínua.

## 3. Landsat 8/9 (óptico, 30 m)

- Necessário para série histórica anterior a 2015 e para consistência.
- Harmonização entre OLI/TIRS e com Sentinel-2 (coeficientes publicados ou calibração empírica
  documentada).
- Features: bandas, índices, tendências (Theil–Sen), anomalias em relação à mediana histórica.

## 4. Sentinel-1 (radar C-band, 10 m)

- Pré-processamento: órbita, calibração, correção de terreno, speckle filter.
- Features: VV, VH, VH/VV, estatísticas temporais (média, desvio, percentis), coerência
  interferométrica (se disponível), métricas de estabilidade.
- Racional: estrutura e umidade; complementa óptico sob nuvem.
- Cuidado: geometria ascendente/descendente e ângulo de incidência; tratar separadamente ou
  normalizar.

## 5. Topografia e clima

- DEM: elevação, declividade, aspecto, posição topográfica (TPI), rugosidade.
- Clima: precipitação anual, sazonalidade, déficit hídrico, temperatura; ERA5-Land para variação
  interanual, WorldClim/CHELSA para normais.
- Solo: textura, carbono orgânico, drenagem (SoilGrids), com ressalva de resolução (250 m).

## 6. Estrutura vertical

- GEDI/ICESat-2: altura máxima, percentis de altura, cobertura de dossel, índice de rugosidade.
- Produtos globais de altura de dossel (ex.: ETH/GLAD) como feature auxiliar, com caveat de
  origem/modelo.
- Racional: altura é preditor forte de AGBD; ajuda a reduzir saturação óptica.

## 7. Seleção e redução

1. Remover features com variância quase nula.
2. Remover duplicatas (correlação > 0,98) mantendo a mais interpretável.
3. Avaliar importância por permutação **em CV espacial**.
4. Ablação por grupo (óptico, radar, topo, clima) para medir contribuição marginal.
5. Manter conjunto enxuto: preferir 15–40 features estáveis a centenas instáveis.

## 8. Controle de qualidade das features

| Verificação | Critério |
|---|---|
| Cobertura | % de pixels com valor válido por feature |
| Distribuição | sem caudas anômalas fora de faixa física |
| Estabilidade temporal | sem saltos inexplicáveis entre anos |
| Consistência espacial | sem costuras/artefatos de mosaico |
| Vazamento | nenhuma feature derivada do alvo (ex.: AGB de produto global) |

**Regra anti-vazamento:** features derivadas de produtos de AGB (CCI, Spawn) **não** entram no
modelo; entram apenas na comparação.

## 9. Artefato de features

- Cada camada de feature tem: nome, versão, fonte, data, CRS, resolução, unidade, método,
  cobertura e hash.
- O conjunto é descrito em um arquivo `features.yaml` (ou equivalente) versionado.
