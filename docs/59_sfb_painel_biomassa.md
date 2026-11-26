# 59 — SFB: Painel de Biomassa e Carbono (leitura do arquivo `pontos_sfb.gpkg`)

**Status:** diagnóstico somente leitura + seleção de equação implementada e executada
(`tools/select_ifn_equation.py`) + ano por UA (§9) + crosswalk tipologia (§10) +
ingestão no store (§8), 2026-11-25. Resultados em `data/processed/ifn_selection/`.
**Arquivo analisado:** `C:\Users\FerreiraF1\Documents\Dados_Biomassa\SFB\pontos_sfb.gpkg`
(100 MB, 439.970 linhas).
**Insumos oficiais baixados** (gitignored, `data/raw/inventarios/sfb/`):
`metadados_painelbiomassacarbono.pdf`, `metadados_texto_extraido.txt`,
`equacoes_oficial.csv`, `teste_equacoes.csv`.
**Portal oficial:** <https://dados.florestal.gov.br/pt_BR/dataset/painel-de-biomassa-e-carbono>
(CKAN, CC BY, versão 2025, atualizado em 2026-07-30).

Este documento responde ao pedido de avaliação do dado SFB antes de usá-lo: o que ele
representa, a metodologia oficial, o que cada coluna significa, os achados do profile e a
regra de seleção de equação que permite extrair **um AGB por UA** de forma rastreável.

---

## 1. O que é

É o **CSV oficial do Painel de Biomassa e Carbono do Serviço Florestal Brasileiro**
(lançado em 30/03/2026) convertido para GeoPackage, com uma coluna de geometria adicionada.
Evidência: 439.970 linhas e as mesmas 16 colunas do CSV oficial do portal.

- **Representa:** estoques de AGB medidos em campo pelo **Inventário Florestal Nacional
  (IFN)**, processados em nível de Unidade Amostral (UA = conglomerado).
- **Licença:** CC BY · **Fonte:** SFB/Diretoria de Fomento Florestal (DFF).
- **Geometria:** um ponto por UA (7.466 pontos = 7.466 UAs). Verificado com PROJ: a
  geometria bate **exatamente** com `lon_pc`/`lat_pc` reprojetado em EPSG:5880
  (dx, dy ≈ 1e-9 m). **CRS declarado e coordenadas estão corretos.**

## 2. Metodologia oficial (PDF de metadados)

- **Desenho amostral:** conglomerados em **dois estágios** (fundamentação Cochran 1977;
  estimadores conforme Queiroz 2012, p. 300-307):
  1. **1º estágio:** sistemático, **espaçamento de 20 km** entre pontos centrais;
  2. **2º estágio:** subunidades sistemáticas, igualmente espaçadas, perpendiculares —
     1 a 4 subunidades por UA.
- **Componentes:** a) árvores vivas, b) mortas em pé, c) necromassa, d) sistema radicular.
  **Exclui** cultivos e pastagens plantadas.
- **Análise de equivalência entre equações:** *Regression-based TOST* com **1.000
  bootstraps** e faixa de equivalência **±25% (IC 95%)**
  (Robinson & Froese, *Ecological Modelling* 176, 2004). Saída em `teste_equacoes.csv`.
- **Aviso do SFB:** a tipologia da vegetação **não foi classificada em campo**; veio de
  informação secundária (espécies, localização, descritores ambientais).

## 3. Dicionário de colunas (oficial)

Extraído do PDF de metadados (texto preservado em
`data/raw/inventarios/sfb/metadados_texto_extraido.txt`).

| Coluna | Significado oficial | Observação do profile |
|---|---|---|
| `fid` | id do GeoPackage | — |
| `geom` | ponto no EPSG:5880 | = centroide do conglomerado; bate com lon/lat |
| `bioma` | bioma da UA | Cerrado 170.627; Amazônia 119.536; Caatinga 78.754; Mata Atlântica 61.836; Pampa 9.217 (linhas) |
| `uf` | Unidade Federativa | 27 UFs |
| `lon_pc`, `lat_pc` | longitude/latitude do **ponto central do conglomerado** (WGS 84) | **precisão heterogênea:** 77% com 2 casas (~1 km), 17% com 1 casa (~11 km), ~1,5% em **graus inteiros (~111 km)** |
| `ua` | Unidade Amostral (conglomerado) | 7.466 UAs; formato `GO_178`, `MA_415_F` |
| `n_subunidades` | nº de subunidades | 1–4 (média 2,9); varia dentro de 1.975 UAs |
| `sanidade` | sanidade do indivíduo (vivas/mortas) | **100% "Vivas"** — mortas/necromassa são CSVs separados |
| `classe_uso_da_terra` | classe de uso da terra **definida em campo** | Floresta Natural 250.435; Savana 106.553; Savana-estépica 46.183; Estepe 19.207; Palmeiral 10.875; Não classificado 2.596; Formação Pioneira 2.121; Campinarana 2.000 |
| `tipologia_da_vegetacao` | tipologia da vegetação (**classificada por informação secundária**) | 13 classes; candidata a crosswalk IBGE |
| `equacoes` | **código da equação** usada no cálculo da biomassa | 222 códigos distintos (`Eq.103`, `AGB_Chave`, ...) |
| `area_ha` | área = somatório das subparcelas da **mesma tipologia** na subunidade (ha) | 0,01–0,4 ha; **soma entre equações duplica a área** |
| `agb_media_kg_por_ha` | **média simples de AGB por UA** (kg/ha) | mediana 27.870 kg/ha = 27,9 Mg/ha; p95 = 260 Mg/ha |
| `agb_variancia_por_ua` | variância do AGB por UA | em (kg/ha)²; mediana 6,9e7 |
| `valor_r` | **fator de expansão de AGB seca → biomassa das raízes (BGB)** | **não é correlação!** valores discretos 0,20/0,24/0,28/0,29/0,37/0,40/0,49/0,56; média 0,406; 2.475 nulos (0,56%) |

> **Nota para a gestão:** `valor_r` é exatamente o fator AGB→BGB citado ("em torno de
> 0,4") — já vem embutido no dado, com valor por UA (0,37–0,56 na mediana). Escopo atual
> continua só AGB (ADR-0031); o fator fica registrado como insumo futuro.

## 4. Estrutura — o achado mais importante

```
1 linha = UA × classe_uso_da_terra × equação   (439.970 combinações únicas)
7.466 UAs × ~54 equações distintas = ~59 linhas por UA (máx. 86)
```

**O arquivo não contém "um AGB oficial por parcela"** — contém a **matriz completa de AGB
recalculado por todas as equações candidatas**. As equações discordam fortemente: dentro do
mesmo (UA, tipologia), a razão max/min entre equações tem **mediana de 76–83×**
(p95 ≈ 400–800×). Exemplo: uma UA com 231 linhas vai de 65 kg/ha (Eq.72) a centenas de
Mg/ha, todas rotuladas "Floresta Estacional Decidual".

**Consequência:** usar o arquivo como está multiplicaria cada parcela ~59× com valores
incompatíveis. É obrigatório **selecionar uma equação por parcela** — e o SFB publica os
insumos para isso:

- `equacoes_oficial.csv` (222 equações): `d.min`/`d.max`, `r2/r2aj`, `syx`, equação,
  compartimento, peso, autor, fonte, tipologia de referência;
- `teste_equacoes.csv`: pares de equações testados por bioma × tipologia com
  `reject_intercept`, `reject_slope` e `equivalente` (True/False).

## 5. Qualidade/limitações observadas

1. **Outliers impossíveis:** 715 linhas > 1.000 Mg/ha; 67 > 2.000; máximo 9.073 Mg/ha —
   provável equação aplicada fora do domínio `d.min/d.max`.
2. **Precisão de coordenada:** até 1° de arredondamento em ~1,5% das UAs — pareamento
   pixel a pixel inseguro nesses pontos; usar validação regional ou filtrar por precisão.
3. **Sem ano de medição:** o arquivo **não tem coluna de data/ano**. O ano por UA precisa
   vir de outra fonte (ex.: dataset "IFN — Coordenadas georreferenciadas das UAs" no
   mesmo portal) para aplicar o critério 2000+ do ADR-0031.
4. **Área não é aditiva** entre linhas da mesma UA (repetida por equação).
5. `valor_r` com 2.475 nulos; `sanidade` constante ("Vivas") — sem valor preditivo.

## 6. Regra de seleção de equação — IMPLEMENTADA

**Ferramenta:** `tools/select_ifn_equation.py` (somente stdlib; leitura somente
nos insumos). **Saídas** em `data/processed/ifn_selection/` (gitignored):
`ifn_tipologia_selected.csv` (8.185 linhas UA×tipologia),
`ifn_ua_selected.csv` (7.466 UAs), `relatorio_selecao.json`.

Reduz 439.970 linhas → **1 linha por UA** com proveniência da equação. A seleção é
por grupo **(bioma, tipologia)**, com ordenação determinística:

1. maior nº de pares "Equivalente" no teste oficial TOST do SFB;
2. equação coberta pelo teste do grupo;
3. bioma do catálogo igual ao bioma do grupo;
4. `fito` do catálogo igual à tipologia do grupo;
5. peso "Seco" sobre "Fresco";
6. maior `r2/r2aj` (normalizado para fração; ausente = −1);
7. menor `syx` (ausente = +∞);
8. `id` crescente (determinismo).

Se a equação ranqueada #1 não existe em uma UA do grupo, desce a lista
(`equation_fallback_rank_N`). Na agregação por UA: **média ponderada por
`area_ha` entre tipologias** (área é constante por UA×tipologia, verificado);
`agb_mg_ha = ÷1000`; `se = √(Σ wᵢ²·seᵢ²)` apenas com a variância entre
subunidades (componentes cobertos declarados no relatório).

**Diferenças em relação ao rascunho inicial desta seção:**

- **`d.min`/`d.max` NÃO foi usado como filtro** — o painel não publica DAP por
  árvore, então o domínio da equação não é verificável por linha. Fica pendente
  quando houver dado árvore-a-árvore. Os outliers impossíveis foram reduzidos
  pela seleção (715 linhas → **3 UAs** sinalizadas `agb_gt_1000_mg_ha`).
- Filtro `r2 ≥ 0,5` não aplicado como corte duro (14 equações sem r2; corte
  eliminaria equações legítimas). O r2 entra apenas como desempate.

**Armadilha de implementação registrada:** os CSVs oficiais do portal são
**UTF-8 com BOM**; ler como `latin-1` gera mojibake e casamento de chaves falha
silenciosamente (38/47 grupos "sem cobertura do teste"). Corrigido com
`utf-8-sig` + verificação de interseção de grupos.

### 6.1 Resultados da execução (dados reais, 2026-11-25)

- 439.970 linhas → 8.185 (UA×tipologia) → **7.466 UAs**; 47 grupos
  (bioma, tipologia), **39 com cobertura do teste TOST** (8 sem, 24 detalhes).
- Ranqueada #1 em **8.130/8.185 (99,3%)**; 55 fallbacks (ranks 3–35).
- AGB selecionado (Mg/ha): p05=1,7 · **p50=28,4** · p95=205,0 · máx=2.074;
  3 UAs >1.000 (flag), 207 <1 (flag).
- Comparação com o default atual (`AGB_Chave`): p50 28,4 vs 25,3
  (razão mediana 1,08); **782 UAs com razão >2**; 255 com <0,5.
- Sanity ecológico por bioma (p50): **Amazônia 117,5 · Mata Atlântica 67,8 ·
  Pampa 53,4 · Cerrado 21,4 · Caatinga 9,2** — ordem de grandeza esperada.
- Equações escolhidas: Eq.78 (Scolforo 2008, Cerrado), Eq.209 (Kenzo 2009),
  Eq.208 (Huy 2016), Eq.190/191 (Basuki 2009), Eq.55 (Oliveira 2019),
  Eq.212 (Ketterings 2001) — todas peso "Seco", r² ≥ 0,67 (a maioria ≥ 0,9).
- Flags por UA: `nao_equivalente_vs_agb_chave` **3.790** (a equação escolhida
  difere de Chave 2014 no teste do SFB — informativo, não é defeito),
  `coord_precision_gt_001deg` 1.362, `multi_equation_by_tipologia` 585,
  `agb_lt_1_mg_ha` 253, `equation_fallback` 52, `agb_gt_1000_mg_ha` 3.
- Conferência manual (GO_398): média ponderada reproduz exatamente o arquivo.

**Estado:** execução validada em dados reais; **não integrado** ao
`load_ifn_panel` (ambiente sem pandas/pytest — decisão do usuário de não
instalar agora). Pendente: portar a regra para o adaptador com testes.

## 7. Próximos passos

1. ~~Implementar a seleção (§6)~~ **feito** — `tools/select_ifn_equation.py`.
2. **Portar a regra para `load_ifn_panel`** (`src/biomass_model/inventory/adapters.py`),
   hoje limitado a `equation="AGB_Chave"` + fallback arbitrário, com testes
   (`tests/`) — requer ambiente montado (`docs/57`).
3. ~~Obter o **ano por UA** no portal SFB~~ **feito** — ver §9.
4. ~~Cruzar `tipologia_da_vegetacao` com o crosswalk IBGE~~ **feito** — ver §10;
   pendente: **integrar** o crosswalk no `classify_fitofisionomia` (junto com o
   item 2) e decidir a inconsistência de código `2` vs `12` (§10.3).
5. ~~Ingerir o resultado selecionado no store canônico~~ **feito para a versão
   default** (`AGB_Chave`) — ver §8; pendente: re-ingestir após o item 2
   (portar a seleção e o ano por UA, que hoje fica de fora do `reference_date`).

## 8. Ingestão no store canônico (2026-11-25)

**Ambiente:** `.venv` criado conforme `docs/57` (Python 3.12) com
`pip install -e ".[dev,ml,data,inventory]"`. **Testes: `python -m pytest` →
60 passed** (1 warning de depreciação do planetary-computer).

**Correção de dependência:** `planetary-computer` é importado em
`datasets/landsat.py` e citado no HANDOFF, mas **não estava declarado no
`pyproject.toml`** — adicionado ao extra `data`. A coleta de testes falhava sem
isso (`ModuleNotFoundError`).

**Comando e resultado:**

```
python -m biomass_model.cli inventory-store --source ifn \
  --path data/raw/inventarios/sfb/dadosbiomassa_painel.csv \
  --store data/processed/inventory_store --usage validation --notes "..."
```

- `status: ingested` → **7.466 observações** (1:1 com as UAs do painel),
  `rows_total: 7466`; fonte `IFN_SFB:painel_biomassa_carbono`, licença `CC BY`
  (do painel), sha256 no manifesto, notas com referência ao `docs/59`.
- `validate_observations`: **errors=[], warnings=[]**.
- Conteúdo: 100% `observation_type=field`, `model_status=validation`,
  `allometric_equation=AGB_Chave`; geometria completa; incerteza (SE de
  variância entre subunidades) em 5.833; 1.633 com flag
  `uncertainty_unavailable`; distribuição por bioma: Cerrado 2.537, Amazônia
  1.937, Caatinga 1.744, Mata Atlântica 1.078, Pampa 170.
- `reference_date` **vazio em todas** (esperado: a tabela de anos do §9 ainda
  não é conectada ao adaptador — pendência do item 2).
- **Idempotência verificada:** re-execução → `status: skipped`,
  `reason: mesma assinatura de fonte`.
- **Observação sobre o default:** `AGB_Chave` p50 = 23,8 Mg/ha no store vs 25,3
  na comparação do §6.1 — a diferença vem de o adaptador escolher a **primeira
  linha** da UA (classe depende da ordem do arquivo), não a média ponderada;
  mais um argumento para portar a regra do item 2.

**Limitação declarada:** este store é a versão **default** (equação fixa,
sem ano); a versão com seleção de equação (§6) e ano (§9) será a re-ingestão
após o port para `load_ifn_panel`.
6. Sensibilidade da regra (limiar de consenso, alternativa r2-first) e comparação
   com `AGB_Chave` em validação de campo — só com ambiente + dados.
7. Avaliar download dos CSVs de árvores mortas e necromassa (fora do escopo AGB atual).

## 9. Ano de coleta por UA (2026-11-25)

**Fonte:** dataset oficial *IFN — Unidades amostrais por UF* (CKAN SFB,
`unidades-amostrais-por-uf-ifn`, 27 CSVs por UF; recursos rotulados XLSX mas são
CSV UTF-8 com BOM). Coluna `data` = **"Data de coleta da informação em campo"**
(definição confirmada no PDF de metadados, extraído para
`data/raw/inventarios/sfb/metadados_ua_uf_texto.txt`).

- **10.201 UAs** com data; **100% com data válida** (formato `AAAA/MM/DD`);
  **nenhuma pré-2000** — a coerência com o critério 2000+ do ADR-0031 é total.
  O painel declara oficialmente **ano-base 2011 a 2024** (metadados); as datas por
  UA variam de **2012 a 2024**.
- Cobertura das UAs do painel: **7.009/7.466 (93,9%)** com data.
- **457 UAs sem data**, concentradas em **BA (253), PI (161), DF (43)** — UAs
  provavelmente de campanhas posteriores ao corte do arquivo UF (disp-mai2024) ou
  de códigos especiais (`BA_111_P43`, `BA_102_H`); ficam com a flag
  `reference_date_unknown`.
- Tabela gerada: `data/processed/ifn_selection/ifn_ua_collection_dates.csv`
  (10.201 linhas: ua, uf, data_coleta, ano, presente_no_painel, fonte; gitignored).
- **Licença:** o dataset UF **não tem licença declarada no portal**
  (`license_id` vazio no CKAN); metadados oficiais em PDF. Uso como metadado
  factual de data — registrar a lacuna se o dado for redistribuído.
- Distribuição das UAs do painel com data: 2013 (287), 2014 (855), 2015 (1.014),
  2016 (333), 2017 (1.270), 2018 (2.149), 2019 (22), 2020 (135), 2021 (156),
  2022 (110), 2023 (608), 2024 (68); 2012 (2).

## 10. Crosswalk tipologia IFN × IBGE/MapBiomas (2026-11-25; revisado 2026-11-26)

> **Revisão 2026-11-26:** o arquivo original desta seção
> (`ifn_tipologia_crosswalk.csv`) foi **substituído** por duas tabelas melhores,
> porque a correspondência com o MapBiomas depende do bioma e deve citar a
> evidência da legenda Col.11:
> - `data/reference/ifn_correspondencia_ibge.csv` — IFN → IBGE (temática, por campo);
> - `data/reference/ibge_legenda1_para_mapbiomas.csv` — IBGE legenda_1 → MapBiomas,
>   por bioma, com citação da legenda (ver `docs/60` §3).
> A análise abaixo é mantida como histórico da primeira rodada.

**Arquivo original:** `ifn_tipologia_crosswalk.csv` — 15 linhas
(13 tipologias do painel; `Savana` tem linha por bioma: Amazônia ≠ restante).
**Preservado** `data/reference/fitofisionomias_crosswalk.csv` (ADR-0029), que
continua sendo o crosswalk IBGE↔MapBiomas; o novo arquivo é a pontura
painel↔IBGE.

### 10.1 Correspondências (resumo)

- **Mapeados (10 tipologias):** Campinarana→3; Florestas Estacionais
  (Decidual/Semidecidual/Sempre-verde)→3; Ombrófilas (Aberta/Densa/Mista)→3;
  Savana→4 (fora da Amazônia); Estepe→12 (hipótese);
  Savana gramíneo-lenhosa→12 (hipótese, conforme legenda Col11).
- **Sem correspondência (1):** Contato (Ecótono e Encrave) — mosaico, sem código.
- **Conflito 1:N (1):** Formações Pioneiras — a legenda Col11 distribui por
  Mangue (5), Floresta Alagável (6), Formação Florestal (3) e Campestre (11/12)
  conforme subtipo.
- **Conflito (1):** Savana-estépica — Arborizada→4 vs Parque/Gramíneo→12; o
  painel não distingue subtipo. **Conflito bioma (1):** Savana na Amazônia →
  12 (legenda) vs 4 (crosswalk atual por "Savana Arborizada").

### 10.2 Comportamento atual do `classify_fitofisionomia` (simulado, sem código alterado)

13 tipologias × 5 biomas = 65 combinações: **exato 20, contém 8, fallback 37
(57%)**. Padrões:

- O crosswalk atual só tem linhas Amazônia/Cerrado → no **Cerrado** as florestas
  estacionais/ombrófilas caem em fallback (sem código); Caatinga/Mata
  Atlântica/Pampa usam a tabela cheia e casam por nome.
- `Floresta Ombrófila Mista` e `Estepe` **não existem** no crosswalk atual
  (gaps) → sempre fallback.
- Fallback de `Savana gramíneo-lenhosa` dá grupo **savanna** (token), mas a
  legenda Col11 a coloca em **Formação Campestre** — conflito documentado.
- `Formações Pioneiras` cai em grupo `unknown`.

### 10.3 Inconsistência encontrada (precisa de decisão)

O código e o crosswalk atual usam **`mapbiomas_codigo = 2` para campestre**
(`GROUP_BY_MAPBIOMAS` em `stratification/__init__.py` linhas 28-33; linhas 19-21
do crosswalk), mas **ADR-0010, docs/17, docs/22 e docs/26 dizem 11/12**, e a
legenda oficial Col11 (verificada em `brasil.mapbiomas.org`) tem
**12 = Formação Campestre** e **11 = Campo Alagado e Área Pantanosa** — não
existe classe 2 no nível 2 da legenda. O novo crosswalk usa **12** (oficial).
**Pendência:** alinhar código/crosswalk antigo para 11/12 com testes, ou
justificar o `2`; não alterado nesta etapa para não mudar comportamento sem
bateria de testes.

## 11. Método

- Leitura direta do GeoPackage via `sqlite3` (sem dependências); geometria validada com
  `rasterio`/PROJ (EPSG:4326 → EPSG:5880).
- Texto do PDF de metadados extraído com stdlib (`zlib` + CMaps ToUnicode + strings hex
  de 2 bytes); trecho útil preservado em `data/raw/inventarios/sfb/`.
- Ano por UA: 27 CSVs do CKAN SFB via `urllib` (§9); crosswalk montado a partir das
  descrições oficiais das tipologias no PDF do painel + legenda Col11 do MapBiomas;
  comportamento atual do `classify_fitofisionomia` reproduzido em simulador stdlib
  (§10.2) — **nenhum código de `src/` foi alterado**.
- Nenhum dado do arquivo original foi alterado; todos os diagnósticos foram somente
  leitura. O ambiente `.venv` foi montado nesta etapa (passo 4, §8) conforme
  `docs/57`; nenhuma credencial foi usada.
