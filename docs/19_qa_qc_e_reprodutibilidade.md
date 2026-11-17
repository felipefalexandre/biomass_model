# 19 — QA/QC e reprodutibilidade

## 1. Objetivo

Garantir que qualquer número publicado possa ser **reproduzido** e **auditado**: mesma entrada +
mesmo código + mesma configuração ⇒ mesmo resultado, com evidência.

## 2. Níveis de controle

| Nível | Controle | Evidência |
|---|---|---|
| L1 | validação de entrada | schema, ranges, CRS, nodata |
| L2 | contrato entre etapas | testes de alinhamento e unidade |
| L3 | QA do artefato | estatísticas, mapas de controle, hash |
| L4 | QA científico | métricas de validação, AOA, plausibilidade |
| L5 | QA do relatório | unidades, máscaras declaradas, limitações |

## 3. Checagens automáticas obrigatórias

### 3.1 Rasters

- CRS e transform idênticos entre camadas empilhadas.
- `width`/`height` consistentes.
- dtype e nodata declarados.
- Valores dentro de faixa física (AGBD ≥ 0; ≤ limite de plausibilidade definido).
- Sem `NaN` onde deveria haver nodata.
- Cobertura: fração válida por janela/domínio.
- Compressão e tiling (COG) válidos.

### 3.2 Vetores

- Geometria válida (`is_valid`), sem autointerseção.
- CRS único e declarado.
- Sem duplicatas de ID.
- Áreas > 0 e soma coerente.

### 3.3 Tabelas

- Esquema fixo (nomes, tipos, unidades).
- Chaves únicas.
- Sem nulos em campos obrigatórios.
- Contagens e somas reconciliadas entre etapas.

### 3.4 Modelo

- Seed registrada.
- Versões de bibliotecas registradas.
- Conjunto de treino/validação congelado e identificado.
- Métricas recalculáveis a partir do artefato.

## 4. Manifesto de execução

Cada execução grava `run_manifest.json`:

```json
{
  "run_id": "...",
  "started_at": "...",
  "git_commit": "...",
  "git_dirty": false,
  "config_hash": "...",
  "python": "3.x",
  "packages": {"rasterio": "...", "geopandas": "...", "scikit-learn": "..."},
  "inputs": [{"path": "...", "sha256": "..."}],
  "outputs": [{"path": "...", "sha256": "...", "bytes": 0}],
  "seeds": {"numpy": 0, "sklearn": 0},
  "warnings": []
}
```

## 5. Versionamento

- **Código:** git, tags semânticas (`v0.1.0`).
- **Dados:** não versionar brutos grandes; versionar **referências** (URL, versão, data de acesso,
  hash) no catálogo.
- **Modelos:** arquivo + cartão de modelo (model card) com treino, métricas, limitações e AOA.
- **Artefatos:** hash SHA-256 + data.
- **Relatórios:** link para o `run_id` que os gerou.

## 6. Reprodutibilidade ambiental

- Ambiente declarado (requirements/conda/uv lock).
- Versões fixadas, não faixas.
- Container (Docker) opcional, recomendado para o produto final.
- Teste de reprodução: rodar em ambiente limpo e comparar hashes de saída.

## 7. QA científico

1. Plausibilidade: AGBD média dentro de faixas da literatura por estrato.
2. Consistência: mapa vs benchmark (divergência explicada).
3. Estabilidade: métricas entre folds e entre anos.
4. Sensibilidade: efeito de hiperparâmetros e features.
5. AOA: fração coberta e desempenho dentro/fora.

## 8. Logs

- Log estruturado (JSON lines) com nível, etapa, janela, tempo, mensagem.
- **Atenção:** no pipeline anterior, logs de 0 bytes ocorreram porque não havia chamadas de
  `logger.info/warning` em execução limpa — não é bug. Aqui, definir explicitamente logs de
  progresso por etapa/janela e verificar que são escritos.
- Nunca logar credenciais ou caminhos sensíveis.

## 9. Critérios de bloqueio de publicação

Não publicar se:

- QA L1–L3 falhou;
- métricas de validação ausentes;
- AOA não calculada;
- unidade ou máscara ambígua;
- manifesto incompleto;
- divergência com benchmark não explicada.

## 10. Checklist final

- [ ] Config versionada e validada
- [ ] Entradas com hash
- [ ] Saídas com hash
- [ ] Testes passando
- [ ] Métricas por estrato
- [ ] AOA e mapa de incerteza
- [ ] Model card e relatório de validação
- [ ] Limitações e redflags declaradas
- [ ] Reprodutibilidade testada em ambiente limpo
