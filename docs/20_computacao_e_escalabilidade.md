# 20 — Computação e escalabilidade

## 1. Dimensão do problema (referência da etapa anterior)

- Grade nacional: 154.468 × 146.235 px (~22,6 bilhões de pixels), 30 m.
- Janelas de 2048 px: 76 por linha, 5.472 janelas no total.
- Série de desmatamento concluída em ~1,56 h no ambiente local (uma variável por ano).
- Produtos de desmatamento: 0,22–0,27 GB por ano; máscara: 0,30 GB (COG comprimido).

Para biomassa, o volume cresce por:

- múltiplas features (bandas, índices, texturas, radar, clima);
- múltiplos anos (2016–2025);
- modelo por pixel com incerteza (dois ou três rasters de saída por ano);
- validação e análise de sensibilidade.

Estimativa grosseira: 1–3 TB de intermediários se tudo for materializado. **Não materializar
tudo**: gerar features por janela e consumir no treino/predição, mantendo apenas o necessário.

## 2. Estratégia

### 2.1 Local-first

- Python + rasterio/GDAL + numpy + geopandas + scikit-learn/XGBoost.
- Processamento por janelas, paralelismo por processo (não thread, por causa do GIL e do I/O).
- `--max-workers` configurável; evitar saturar disco (o gargalo costuma ser I/O, não CPU).
- Disco: prever espaço; a etapa anterior exigiu ~800 GB livres.

### 2.2 Amostragem para treino

- Não treinar com todos os pixels: amostrar footprints/referências e pixels de features.
- Balancear por estrato e por faixa de AGBD, registrando os pesos.
- Manter o dataset de treino em Parquet, com índice espacial.

### 2.3 Predição em janelas

- Carregar modelo uma vez por processo.
- Para cada janela: ler features, prever, escrever COG.
- Calcular AOA por janela (dissimilaridade) e gravar junto.
- Retomada por arquivo de progresso.

### 2.4 Cloud (opcional)

- Alternativa gratuita: Google Earth Engine (ver redflag de termos), Brazil Data Cube, ou
  infraestrutura institucional.
- **Decisão:** cloud não é requisito da trilha principal; se usada, o resultado deve ser
  reproduzível fora dela ou documentado como dependência.

## 3. Requisitos mínimos (proposta)

| Recurso | Mínimo | Recomendado |
|---|---|---|
| CPU | 4 núcleos | 16+ núcleos |
| RAM | 16 GB | 64 GB |
| Disco | 1 TB livre | 4 TB (SSD/NVMe) |
| GPU | não necessária | opcional para DL |
| Rede | banda para downloads S2/S1 | cache local |

## 4. Tempo estimado

Ordens de grandeza (a confirmar com piloto):

- Features por ano (S2/S1/Landsat): dias, dependendo da área e da paralelização.
- Treino: horas (RF/XGBoost em milhões de linhas).
- Predição wall-to-wall: horas a dias por ano.
- Validação/bootstrap: horas a dias.

**Regra:** rodar piloto em 1–2 regiões antes de escalar; medir e extrapolar.

## 5. Otimizações

- COG com blocos 512 e DEFLATE (padrão já usado).
- Ler apenas bandas/janelas necessárias.
- Cache de features estáticas (DEM, clima).
- Downcast para float32; evitar float64 em rasters.
- Compressão de tabelas em Parquet.
- Evitar recomputar índices a partir de bandas em cada etapa (materializar uma vez por janela).

## 6. Paralelismo e determinismo

- Paralelizar por janela/tile, com ordem de escrita independente.
- Seeds por processo.
- Resultado final não deve depender da ordem de conclusão (redução determinística).
- Registrar tempos por etapa para identificar gargalos.

## 7. Monitoramento

- Progresso por janela (contagem/total).
- Taxa de falha por janela.
- Uso de memória/disco.
- Alertas de disco cheio e de queda de throughput.

## 8. Riscos computacionais

| Risco | Mitigação |
|---|---|
| disco cheio | limpeza de intermediários; monitoramento |
| memória | janelas menores; streaming |
| I/O lento | cache local; menos arquivos, maiores |
| downloads instáveis | retry com backoff; checksum |
| não determinismo | seeds e redução ordenada |
