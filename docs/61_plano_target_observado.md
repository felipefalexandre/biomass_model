# 61 — Plano: mapa-alvo de inventário observado e bases auxiliares

**Data:** 2026-11-26 · **Status:** plano aprovado para execução; ingestões em andamento.

## 1. Objetivo

Construir um **mapa-alvo o mais confiável possível a partir de inventário observado** (AGB
medida, não modelada), para servir de target dos modelos; e usar as bases de inventário que
**não** puderam ser confirmadas espacialmente como **auxiliares** (calibração, validação,
estratificação), nunca como target nem como feature derivada de AGB.

## 2. Estado de partida (docs/59, docs/60)

| Conjunto | n | Confiança | Uso |
|---|---:|---|---|
| UAs elegíveis por fitofisionomia (atributo) | 6.838 | correspondência temática unívoca | calibração/validação |
| Candidatos **pixel** (30 m, centro na pegada) | 604 pixels / 96 UAs | precisão ≥3 casas, classe homogênea | target de alta confiança |
| Candidatos **célula** (≈1,1 km) | 1.088 | precisão =2 casas, célula homogênea | target de média confiança |

Cada candidato carrega `agb_min_mg_ha`, `agb_mediana_mg_ha`, `agb_max_mg_ha`, `n_equacoes`,
`spread_razao`, `mb_share_compativel` e `ibge_share_compativel`.

## 3. Hierarquia do target (tiers)

- **Tier A — pixel confirmado**: UA com precisão ≥3 casas, tipologia dominante ≥95%, classe
  única, correspondência unívoca, MapBiomas do ano com ≥90% da pegada compatível. Target:
  valor da UA nos pixels cujo centro cai na pegada.
- **Tier B — célula confirmada**: mesma regra, mas célula de ~1,1 km ≥95% homogênea; target
  na célula (upscaling declarado).
- **Tier C — somente atributo**: UA elegível sem confirmação espacial. **Não entra no
  mapa-alvo**; serve para calibração, validação e análise por estrato.
- **Fora**: sem ano, tipologia não dominante, classe ambígua, AGB implausível.

**Regra de independência:** o mapa-alvo é construído **uma linha por UA** (1.184 UAs
únicas: 96 + 1.088). Os 604 pixels são a representação espacial do mesmo valor; em treino,
contar a UA uma vez e manter os pixels no mesmo grupo de split.

## 4. Construção do mapa-alvo

1. Empilhar Tier A (pixel) e Tier B (célula) numa tabela de target por UA, com
   `suporte` = `pixel_30m` ou `celula_1km`, três valores de AGB e flags de confiança.
2. Rasterizar para visualização e para treino no suporte das features:
   - features de satélite em 30 m e 1 km calculadas **no mesmo suporte** do target;
   - nenhuma feature derivada da AGB do próprio target (sem vazamento).
3. Deduplicação: uma UA gera um target; pixels/células irmãos compartilham o valor.
4. Filtros de plausibilidade já aplicados (mediana ≤500 Mg/ha) e de classe
   (MapBiomas/IBGE compatíveis).
5. Documentar cobertura: área mapeada, fração na AOA, incerteza (faixa min–max entre
   equações e IC conformal).

## 5. Bases auxiliares (não confirmadas) — papel

- **Nunca** viram feature a partir da AGB (risco de vazamento e circularidade).
- Papéis permitidos:
  1. **calibração/validação** independente (se data ≥2000, área e coordenada conhecidas);
  2. **estratificação** por fitofisionomia/fonte;
  3. **prior** por estrato (média/mediana), explicitamente rotulado e validado;
  4. **benchmark** de plausibilidade (EBA e mapas globais).

## 6. Ingestão das demais bases (ordem e critérios)

| Fonte | Conteúdo | Critério de aceite | Status |
|---|---|---|---|
| RAINFOR (INV05) | 29 parcelas / 8.729 árvores, 2017–2019, OGL | árvore-a-árvore, área, coordenada, data; recalcular AGB com alometria única | **baixado; bloqueado para AGB** (sem área por parcela — 0,25 ou 1 ha — e sem altura/WD) |
| Maracá (INV07) | 129 parcelas, AGB/C, censo 4 | área e data por parcela; localização | **download bloqueado** nesta máquina (endpoint Mendeley) |
| Vourlitis (INV06) | DAP/altura/AGB, Cerrado MT, 2011–2018 | árvore-a-árvore + área + data | **download bloqueado** nesta máquina (endpoint Mendeley) |
| IFN dados botânicos (INV09) | árvore-a-árvore do IFN (2018+) | termos de uso; mesmas UAs (não independente) | **reclassificado: Darwin Core de espécies** (não fornece DAP/AGB) |
| LBA-ECO (INV08) | 50 parcelas 1 ha, 1997–2001 | pré-2000 | histórico apenas |
| JCarbon (INV11) | 1.984 formulários | sem área/data | **não utilizável** (INV11) |
| EBA / mapas globais | mapas modelados | — | benchmark |

### 6.1 Status de ingestão (2026-11-26)

- **RAINFOR:** `tree_data.csv` baixado (OGL; `data/raw/inventarios/rainfor/`). Tem DAP (mm),
  `Plot_number` e lat/long (2 casas ≈ 1 km), mas **não identifica a área de cada parcela**
  (0,25 ou 1 ha) e não traz altura, densidade da madeira ou espécie. Sem área, Mg/ha variaria
  4×; **não ingerir como AGB** com premissa arbitrária. Desbloqueio: metadados de área por
  parcela (ForestPlots.net) ou contato com os autores.
- **Maracá:** o arquivo baixado (`Downloads\dwca-maraca_comp_floristic-v1.25`) é o
  **Darwin Core de composição florística** (ocorrências de espécies; sem DAP/biomassa).
  O dataset de biomassa/carbono é o Mendeley `10.17632/2j354jtddx.2` (arquivos
  `location_plot` e `biomass_carbon`), ainda pendente de download. Quando obtido, é
  diretamente utilizável: 129 parcelas de 500 m² (Mg/ha = valor × 20), com lat/long e UTM.
- **IFN botânico:** é **Darwin Core de espécies** (30 CSVs por UF), não DAP/altura; serve
  para composição florística e priors de densidade da madeira, não como target.

Cada adaptador: `inventory/adapters.py`, comando `inventory`/`inventory-store`, proveniência
(licença, citação, versão), testes com fixture sintética e registro no catálogo
(`data/reference/inventarios_abertos.*`).

## 7. Validação do target e do modelo

1. Blocos espaciais com buffer; leave-one-region-out e leave-one-source-out.
2. Alvo intervalar: mín/mediana/máx entre equações; IC conformal para o resíduo do modelo.
3. AOA por suporte; cobertura de IC por estrato.
4. Comparação com o baseline A0 (GEDI) sob o mesmo protocolo; promoção conforme ADR-0033.
5. Relatório de cobertura amostral, viés, MAE/RMSE, R², cobertura de intervalos e AOA por
   fitofisionomia e por fonte.

## 8. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Pseudo-replicação de pixels | 1 target por UA; splits por conglomerado |
| Upscaling da célula (0,4 ha → 1,1 km) | flag `suporte`, validação separada por tier |
| Incerteza de equação dominante | alvo intervalar + `spread_razao` |
| Bases auxiliares enviesadas | só validação/estrato, nunca feature de AGB |
| Vazamento por proximidade | buffer nos blocos e exclusão de fontes do treino na validação |

## 9. Sequência de execução

1. Registrar este plano (feito).
2. Ingestão RAINFOR → Maracá → Vourlitis → IFN botânico (adaptador + teste + store).
3. Consolidar o target por UA (Tier A+B) e rasterizar no suporte das features.
4. Calcular features no mesmo suporte e treinar o challenger.
5. Validação independente e comparação com A0; só então promoção.
