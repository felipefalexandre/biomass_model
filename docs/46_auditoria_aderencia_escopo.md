# 46 — Auditoria de aderência ao escopo científico (2026-11-24)

**Status:** diagnóstico aprovado em 2026-11-24; reimplementação iniciada. Nenhum modelo, mapa,
tabela ou resultado anterior foi apagado. As decisões aprovadas estão nos ADRs 0027–0032.
**Commit auditado:** `4427545` (`docs: handoff completo para retomada apos reinicio`), árvore limpa.
**Testes no início da auditoria:** `python -m pytest` → 30 passed.
**Documento de referência:** premissas do prompt de revisão de escopo recebido em 2026-11-24.

Este documento responde à etapa 23 do prompt: examinar o estado atual, realizar a auditoria de
aderência, identificar o que deve ser mantido/corrigido/ampliado/descontinuado, avaliar a
disponibilidade real de inventários, listar lacunas, documentar a arquitetura proposta, elaborar
o plano de continuidade e apresentar perguntas objetivas de decisão.

**Regra desta etapa:** nenhuma mudança substancial de código ou de modelo deve ocorrer antes da
aprovação das premissas e das decisões listadas na seção 11.

---

## 1. Método e evidências consultadas

Foram lidos integralmente ou por seção:

- `HANDOFF.md`, `README.md`, `pyproject.toml`;
- `docs/00` a `docs/45`, com atenção a `docs/35` (auditoria), `docs/36` (base científica),
  `docs/37` (plano anual), `docs/38` (validação/incerteza), `docs/39` (arquitetura),
  `docs/40` (síntese), `docs/41` (mapa vs estrato), `docs/42` (E1), `docs/43` (estabilidade),
  `docs/44` (MRV/REDD+) e `docs/45` (protótipo de mapa);
- `ADR/0001` a `ADR/0026`;
- `src/biomass_model/` (CLI, catálogo, credenciais, features, grade, manifesto, modelagem,
  MRV, polígono, inferência e `datasets/`);
- `tests/` (10 arquivos, 30 testes);
- `data/catalogo_dados.csv`, `data/matriz_evidencias.csv`, `data/reference/` e `data/manifests/`;
- artefatos derivados em `E:\Mapbiomas\biomass\derived` e `E:\Mapbiomas\biomass\pilots\annual`.

Não foram executados downloads, treinamentos ou inferências nesta auditoria. A execução de
testes foi apenas de leitura/verificação.

---

## 2. Sumário executivo

### 2.1 Achado central

O sistema atual é, na prática, um **espacializador estático do GEDI L4A**: o alvo do modelo é o
`agbd` do GEDI (produto modelado, não medição direta de campo), as métricas principais são
calculadas contra GEDI e a validação independente de campo é limitada a 42 sítios antigos do
Cerrado. O sistema **não demonstra** estimar AGB real com a robustez exigida pelo novo escopo.

Isso não invalida o trabalho feito. A base de engenharia é boa: aquisição reprodutível com
manifestos, contrato de grade, validação espacial por região, calibração local, conformal, AOA,
testes e documentação de decisões. O problema é de **desenho científico e de prioridades**, não
de qualidade de código.

O novo escopo muda o centro de gravidade:

1. A referência primária deve ser **campo inventariado**, com GEDI como camada auxiliar de
   calibração/avaliação e nunca como verdade.
2. A **fitofisionomia** deve influenciar treinamento, calibração, validação, incerteza e
   apresentação, não apenas o filtro de domínio 3/4.
3. O produto inclui **mapa anual**, **tabela por fitofisionomia** e **estimativa por polígono
   arbitrário** com geometria real, área de interseção e incerteza propagada.
4. O sistema deve ser **evolutivo**: ingestão contínua de inventários, retreinamento,
   champion/challenger, versionamento e auditoria.

### 2.2 O que manter

- `datasets/` (S2, S1, Landsat, DEM, ERA5, GEDI, ORNL) e o padrão de manifestos;
- contrato de grade (`grid.py`) e testes de alinhamento;
- validação espacial por região (`leave-one-box-out`), calibração local e AOA como conceitos;
- split conformal como ponto de partida de incerteza por célula;
- protótipo de mapa 1 km/30 m e `polygon-stats` como provas de conceito, não como produto;
- `mrv-check` como embrião de QA/QC, `pytest` e a cultura de registrar resultados negativos;
- ADRs e diário de pesquisa, preservando resultados anteriores.

### 2.3 O que corrigir

- Hierarquia de referência: campo > LiDAR calibrado > GEDI > produto global; GEDI L4A é modelo.
- Ausência de fitofisionomia no modelo: hoje só há filtro 3/4 e modelos separados por bioma.
- Descasamento de suporte: modelo treinado em footprints de 30 m aplicado a médias de 1 km.
- Vazamento temporal: climatologia ERA5 2019–2024 e histórico MapBiomas fixo podem usar
  informação futura em reconstruções históricas.
- Calibração local com amostra aleatória intercalada ao teste: risco de vazamento espacial.
- Incerteza: GEDI `agbd_se`, alometria, máscaras e classe não entram na propagação.
- Polígono: não há leitura de geometria, interseção real de área, mediana nem relatório.
- Documentação: README e docs 00/01/33/39/45 têm afirmações desatualizadas ou contraditórias.

### 2.4 O que ampliar

- Ingestão canônica de inventários (IFN, PLOS, ORNL, RAINFOR, CEDA, LBA-ECO, Mendeley etc.).
- Módulo de alometria e harmonização de DAP, altura, densidade da madeira e componentes.
- Mapa de fitofisionomia IBGE 1:250.000 e tabela de correspondência com MapBiomas.
- Experimentos de arquitetura: global, por bioma, especialistas, hierárquico, multifonte,
  ensemble, com resoluções candidatas.
- Validação temporal, por fonte, por inventário e ecológica.
- Produtos A, B e C com incerteza, AOA, flags de qualidade e rastreabilidade.
- Registro de modelos e fluxo champion/challenger.

### 2.5 O que adiar ou retirar da prioridade

- BGB, carbono, CO₂e, desmatamento/reflorestamento, adicionalidade, vazamento, permanência,
  créditos de carbono e projeções futuras. Não há código implementado para esses itens; o excesso
  é principalmente documental (`docs/10`, `docs/11`, `docs/16`, `docs/00`, `docs/01`).
- Classes 2 (campestre) e 6 (florestal alagável): manter fora até decisão explícita.
- Expansão nacional antes de consolidar a base observacional e a fitofisionomia.

---

## 3. Matriz de aderência ao escopo

Legenda de estado:

- **A** = aderente;
- **P** = parcialmente aderente;
- **NV** = implementado, mas não validado;
- **NI** = não implementado;
- **FE** = fora do escopo prioritário;
- **DD** = depende de decisão do usuário.

| Componente | Objetivo esperado no novo escopo | Estado atual | Evidência | Desvio principal | Ação corretiva | Prioridade |
|---|---|---|---|---|---|---|
| Escopo e estimando | AGB real (Mg ha⁻¹ e Mg), anual, com incerteza, por fitofisionomia | AGB do GEDI L4A espacializada; produto experimental | `modeling.py` usa `agbd`; `docs/34`, `docs/35`; `baselines.csv` | Confunde produto modelado com observação; estimando não é AGB de campo | Redefinir estimando e hierarquia de referência; manter o atual como baseline A0 | P0 |
| Domínio geográfico | Amazônia e Cerrado, com arquitetura expansível | 11 boxes (~17,8 km), não nacional | `matriz_boxes.csv`; `docs/32` | Cobertura amostral, não domínio wall-to-wall | Manter boxes como piloto; separar “área de treino” de “domínio do produto” | P1 |
| Domínio de cobertura | Classes 3 e 4 do MapBiomas no ano, máscara dinâmica | Classe do ano usada no treino e na inferência | `features.build_training_table`, `inference/map.py` | Não há produto explícito de “não estimado”; classes 2/6 fora sem decisão | Gerar máscara anual, flags de nodata/não estimado e documentar exclusões | P1 |
| Estratificação fitofisionômica | IBGE 1:250k, crosswalk documentado, influência no modelo | Só classe 3/4 e bioma; crosswalk inicial não usado | `fitofisionomias_crosswalk.csv`; `feature_columns` não inclui fitofisionomia | Fitofisionomia não influencia treino, calibração, validação ou incerteza | Construir mapa/camada fitofisionômica; testar feature, estrato e hierarquia | P0 |
| Inventários de campo | Módulo permanente de descoberta, aquisição, ingestão e avaliação | PLOS 2018 (42 sítios no domínio) usado em baseline separado; ORNL parcial; IFN baixado e não ingerido | `inventarios_abertos.md`; `plos2018_auditoria.csv`; `ornl_agb_sites.csv` | Nenhum inventário de campo no treino principal; base insuficiente para AGB operacional | Fase 2: esquema canônico, adaptadores, harmonização, deduplicação e proveniência | P0 |
| LiDAR e observações estruturais | GEDI L2A/L2B/L4A, LiDAR aerotransportado, distinguir tipos e erros | Apenas L4A como alvo; `agbd_se` baixado e não usado | `datasets/gedi.py`; `docs/35` §3 | Trata estimativa modelada como observação; ignora erro GEDI | Separar tipos de observação; usar `agbd_se`/PI como erro ou peso; auditar filtros | P0 |
| Produtos globais de AGB | Benchmark, prior ou comparação, nunca verdade | Não usados | `docs/25`, `docs/36` | Falta benchmark independente; decisão deliberada correta | Implementar comparação de distribuição e divergência; nunca treinar e validar no mesmo produto | P2 |
| Ingestão evolutiva | Adaptadores, idempotência, controle de duplicidade, esquema canônico | Não existe | Código atual só tem fetchers de sensores; não há `data_ingestion` | Impossível incorporar novos inventários sem script manual | Criar esquema de observações e pipeline idempotente | P0 |
| Covariáveis | Óptico, SAR, topografia, solo, clima, histórico, perturbação | S2/S1/Landsat/DEM/ERA5/histórico MapBiomas; sem solo, fogo, secundária | `features.py`; `docs/37` §3; `docs/39` | Features anuais só em 2 boxes; clima/histórico com risco temporal | Completar cubo anual; adicionar covariáveis só com hipótese e validação | P1 |
| Arquiteturas de modelagem | Comparar global, bioma, especialista, hierárquico, multifonte, ensemble | Apenas Random Forest separado por bioma | `modeling.py`; `docs/37` §4 | Não há comparação científica de arquiteturas nem partial pooling | Implementar baselines e experimentos A–F com critérios pré-registrados | P1 |
| Uso de dados de campo | Campo como referência; GEDI/LiDAR calibrados; multifonte | Modelo principal treinado só em GEDI; PLOS em linha separada | `docs/34`; `docs/38`; `baselines.csv` | Ausência de treinamento/calibração com campo independente | Testar campo puro, GEDI pré-treino + campo, ponderação por fonte | P0 |
| Resolução e suporte | Avaliar 30/100/250/500/1.000 m e documentar suporte | 1 km oficial e 30 m diagnóstico; modelo treinado em footprint | `docs/45`; `inference/map.py` | Descasamento de suporte; 30 m com aparência de precisão | Formalizar mudança de suporte; testar resoluções; manter 1 km até evidência | P0 |
| Modelagem anual | Máscara do ano, features do ano, sem vazamento, coerência temporal | S2 anual só em 2 boxes; treino principal com compósito único; histórico/clima fixos | `docs/35` §3; `docs/42`; `features.py` | Não há pipeline anual completo nem controle de vazamento | Cubo anual por tile/ano; validação temporal; definir primeiro ano defensável | P0 |
| Retreinamento e promoção | Champion/challenger, registro, critérios, reprodutibilidade | Não existe | Ausência de `model_registry`; joblib + JSON isolados | Novos dados não entram de forma governada | Criar registro de modelos, splits congelados e promoção auditável | P1 |
| Validação científica | Blocos com buffer, temporal, por fonte, ecológica, métricas múltiplas | LOO por box, GroupKFold 5 km, AOA, conformal | `modeling.py`; `docs/38` | Sem buffer, sem CV temporal/fonte, sem fitofisionomia; calibração aleatória intercalada | Adicionar buffer, CV temporal/fonte, validação por fitofisionomia e métricas completas | P0 |
| Incerteza | Componentes de medição, alometria, GEDI, modelo, preditores, máscara, agregação | Conformal por célula; bootstrap de polígono | `docs/12`; `docs/38`; `modeling.py`; `polygon.py` | GEDI/alometria/máscara ignorados; agregação com área fixa e sem geometria | Decomposição de variância, QRF/conformal espacial e Monte Carlo | P0 |
| Produto A — mapas anuais | AGB, IC, AOA, domínio, fitofisionomia, qualidade, COG | Protótipo 1 km/30 m em 1 box/ano; 1 km sem IC/AOA | `docs/45`; `inference/map.py` | Não é série anual nem produto completo | Completar bandas, COG, AOA, IC, flags e todos os boxes/anos | P0 |
| Produto B — fitofisionomia | Tabela por ano/bioma/fitofisionomia com área, média, mediana, estoque, IC | Apenas `by_class` em `polygon_stats` | `polygon.py` | Não há fitofisionomia nem mediana/IC de estoque | Implementar tabela por estrato com incerteza e cobertura amostral | P0 |
| Produto C — polígono | Ler GeoJSON/GPKG/SHP, validar geometria, área real, incerteza, relatório | Apenas agregação de CSV por filtro | `polygon.py`; CLI `polygon-stats` | Não há geometria, interseção real, mediana, fitofisionomia ou relatório | Implementar módulo geoespacial de polígono e relatório | P0 |
| MRV G0–G7 | Portões completos e verificáveis | `mrv-check` cobre parte de G3/G4/G6; demais manuais | `mrv.py`; `docs/44` | G2 não atendido; G0/G1/G5/G7 parciais | Matriz de requisitos com evidência, lacuna e ação; nenhum produto “MRV” até G2 | P0 |
| Arquitetura computacional | Módulos conceituais e contratos claros | `datasets`, `features`, `modeling`, `inference`, `polygon`, `mrv` | `docs/39`; árvore `src` | Faltam ingestão, inventário, alometria, estratificação, registro, relatório, monitoramento | Evoluir sem refatoração total; criar módulos por necessidade | P1 |
| CLI | Comandos `data`, `train`, `calibrate`, `validate`, `model`, `predict`, `polygon` | Comandos de aquisição e análise de baixo nível | `cli.py` | Não há orquestração do fluxo científico | Adaptar comandos existentes; não duplicar funcionalidade | P1 |
| Governança documental | README/HANDOFF/ADRs/catálogo/model cards atualizados | Muita documentação, mas com contradições e escopo antigo | `README` §1; `docs/33`; `docs/39`; `docs/45` | Drift entre docs, código e resultados | Nova rodada de atualização após aprovação; ADRs novos para decisões | P1 |
| Testes e QA | Testes unitários, integração, regressão e CI | 30 testes unitários; sem testes de treino/mapa/polígono | `tests/` | Pode haver regressão silenciosa em modelagem/inferência | Adicionar testes de contrato e integração; CI | P1 |
| Versionamento e reprodutibilidade | Dados derivados, modelos, features e ambiente versionados | Git + manifestos de downloads; artefatos em `E:`; sem lockfile | `data/manifests`; `pyproject.toml` | Perda do `E:` quebra reprodutibilidade; ambiente não fixado | Manifesto de artefatos derivados, hash de features, lockfile e data/model cards | P1 |
| Classes 2 e 6 | Decisão explícita de inclusão/exclusão | Fora do domínio 3/4 | `docs/41` §6; ADR-0025 | Pendência pode bloquear comunicação do produto | Decidir com o usuário; manter exclusão declarada até então | DD |
| BGB, carbono, CO₂e | Fora da prioridade até consolidar AGB | Apenas documentação; sem código | `docs/10`, `docs/11`, ADR-0011 | Risco de dispersão de escopo | Arquivar como “fase futura”; não implementar agora | FE |

---

## 4. Classificação resumida dos componentes

### 4.1 Aderentes ou aproveitáveis

- Aquisição de sensores e manifestos (`datasets/`, `manifest.py`).
- Contrato de grade e testes de alinhamento (`grid.py`, `tests/test_grid.py`).
- Cultura de validação espacial por região e registro de resultados negativos.
- AOA, conformal e calibração local como componentes conceitualmente corretos.
- `mrv-check` como embrião de QA/QC, embora incompleto.
- Documentação de decisões (ADRs) e diário de pesquisa.

### 4.2 Parcialmente aderentes

- Domínio 3/4: implementado no treino/inferência, mas sem produto de máscara/flag.
- Covariáveis: existem, mas incompletas e com risco temporal.
- Validação espacial: existe, mas sem buffer e sem validação temporal/fonte.
- Incerteza: existe por célula, mas não decomposta nem propagada corretamente.
- Mapa e polígono: protótipos úteis, não produtos.

### 4.3 Implementados, mas não validados

- Calibração local por região.
- AOA em 1 km e 30 m.
- Conformal IC90 por célula.
- Mapa 1 km e 30 m do Cerrado central 2021.
- `polygon-stats`.
- ORNL com 3 sítios recuperados.
- PLOS 2018 com Landsat na data (R² 0,288; Cerrado apenas).

### 4.4 Não implementados

- Esquema canônico e ingestão de inventários.
- Módulo de alometria e harmonização de dados de campo.
- Mapa de fitofisionomia e estratificação efetiva.
- Modelos hierárquicos, multifonte, especialistas e ensemble.
- Validação temporal, por fonte e por fitofisionomia.
- Decomposição e propagação completa de incerteza.
- Produto B e Produto C com geometria real.
- Registro de modelos, champion/challenger, relatórios e monitoramento.
- CLI científica de orquestração.
- Testes de integração/regressão e CI.

### 4.5 Fora do escopo prioritário

- BGB, carbono, CO₂e.
- Desmatamento, reflorestamento, fogo como alvo ou contabilidade de atividade.
- Adicionalidade, vazamento, permanência, elegibilidade e créditos.
- Projeção futura de biomassa.
- Expansão nacional imediata.

### 4.6 Dependem de decisão do usuário

- Inclusão das classes 2 e 6.
- Resolução oficial e resolução diagnóstica.
- Orçamento/parceria para campo independente.
- Primeiro ano da reconstrução histórica.
- Produto C como produto de primeira classe (o novo prompt sugere que sim; ADR-0026 diz que não).
- Licença do produto derivado e implicações do share-alike do MapBiomas.
- Prioridade entre completar a base observacional e gerar mapas anuais.

---

## 5. Respostas explícitas às 14 perguntas da auditoria

### 5.1 O sistema atual estima AGB real ou reproduz predominantemente estimativas GEDI?

Predominantemente **reproduz GEDI**. O alvo de treino é `agbd` do GEDI L4A; o modelo aprende a
relação entre features de satélite e a estimativa modelada do GEDI. As métricas atuais
(R², RMSE, viés, conformal, AOA) são medidas contra GEDI. A única referência independente de
campo é o PLOS 2018, restrito ao Cerrado antigo (42 sítios no domínio), e não foi usada para
treinar o modelo principal. Portanto, o sistema **não demonstra** estimar AGB real; demonstra
reproduzir e espacializar GEDI. A distinção está correta em `docs/35` e `docs/38`, mas o produto
e o README ainda não a refletem com clareza suficiente.

### 5.2 Quantos inventários de campo estão efetivamente incorporados?

**Nenhum inventário de campo está incorporado ao treinamento principal.**

| Fonte | Situação | Uso efetivo |
|---|---|---|
| IFN/SFB — Painel de Biomassa e Carbono | 439.970 registros baixados; coordenadas ~0,1° | Usado apenas para escolher pilotos; não ingerido como tabela canônica |
| PLOS 2018 (Roitman et al.) | 77 sítios; 42 no domínio 3/4; Cerrado; 2004–2014 | Baseline/validação separada com Landsat na data (R² 0,288); não treina o modelo GEDI |
| ORNL Sustainable Landscapes Brazil | 31 CSVs (2009–2018); 3 sítios recuperados, 5 sítios-ano | Recuperação metodológica; não integrado ao treino nem a uma tabela de validação final |
| CEDA Manaus, RAINFOR, Vourlitis, Maracá, LBA-ECO, EBA | Catalogados | Não baixados ou não processados |

Consequência: a base observacional de campo é **insuficiente** para o produto operacional. Há
material para desenvolver método, mas não para afirmar acurácia de campo.

### 5.3 Qual é a representatividade amostral por fitofisionomia?

Não é possível afirmar representatividade por fitofisionomia no sentido do IBGE. O que existe é
representatividade por **classe MapBiomas 3/4** e por **bioma**:

- Amazônia: 5 boxes, todos dominados por classe 3; nenhum box de floresta aberta, estacional,
  campinarana, várzea/igapó ou secundária. A mediana de AGB nos boxes vai de ~107 a ~196 Mg ha⁻¹;
  não há cauda abaixo de ~100.
- Cerrado: 6 boxes; classe 4 domina apenas em central, nordeste e noroeste; classe 3 domina em
  oeste, floresta e sul. Há dois regimes de AGB (aproximadamente 2,8–7,6 e 52–83 Mg ha⁻¹) com
  vazio entre ~25 e ~50.
- Não há cronossequência de regeneração, pós-fogo, borda florestal, gradiente altitudinal ou
  várzea.
- A pseudo-replicação é alta: 16–25 blocos de 5 km por box para milhares de footprints. O número
  efetivo de observações independentes é muito menor.
- AOA abaixo de 0,75 em Amazônia leste (0,57) e Cerrado nordeste (0,67) indica extrapolação já
  dentro dos boxes.

### 5.4 A fitofisionomia influencia efetivamente o treinamento ou apenas a apresentação?

Apenas de forma indireta e fraca. O treinamento usa:

- filtro de domínio por classes 3/4 do MapBiomas;
- modelos separados por bioma (Amazônia e Cerrado);
- `mapbiomas_class` em métricas por classe (`run_baseline`), mas não como feature;
- nenhuma variável IBGE de fitofisionomia, nenhum estrato de calibração por fitofisionomia e
  nenhum modelo hierárquico.

O crosswalk `fitofisionomias_crosswalk.csv` existe, mas é uma tabela indicativa com faixas de
literatura “a calibrar”, não uma camada espacial. Portanto, a fitofisionomia **não influencia o
treinamento**; no máximo, a classe MapBiomas aparece na apresentação/avaliação.

### 5.5 Existem fitofisionomias sem suporte amostral?

Sim. Exemplos com suporte ausente ou insuficiente:

- classes 2 (Formação Campestre) e 6 (Floresta Alagável), excluídas do domínio;
- campo limpo, campo sujo, vereda/palmeiral;
- campinarana, várzea, igapó;
- floresta estacional decidual e formações secas de transição;
- cerrado rupestre e savanas abertas extremas;
- vegetação secundária em cronossequência;
- áreas pós-fogo recente;
- bordas florestais e gradientes altitudinais.

Além disso, dentro das classes 3/4, o MapBiomas não separa ombrófila densa/aberta, estacional,
cerradão, cerrado típico/ralo/rupestre. Sem uma camada IBGE ou classificação estrutural, não é
possível afirmar suporte por fitofisionomia fina.

### 5.6 A resolução atual possui fundamentação científica?

Parcialmente. A decisão de 1 km oficial e 30 m diagnóstico (`ADR-0026`, `docs/45`) é
pragmática e coerente com a literatura de agregação e AOA, mas **não foi demonstrada** por
validação independente. Há dois problemas:

1. O modelo é treinado em features de footprints (~25 m GEDI) e aplicado a médias de 1 km; há
   descasamento de suporte não resolvido.
2. O mapa de 30 m tem AOA de 87,5% no box central, mas o IC90 é apenas de resíduos OOF do modelo,
   sem erro GEDI, campo, alometria ou máscara. A aparência de 30 m é maior que a precisão real.

A resolução de 1 km é uma **decisão provisória defensável**, não uma conclusão validada. As
resoluções 100, 250 e 500 m não foram testadas.

### 5.7 Os mapas anuais representam mudanças reais ou principalmente variabilidade das covariáveis?

Não há evidência de que representem mudanças reais. O que existe:

- um protótipo de mapa para **um box e um ano** (Cerrado central 2021), em 1 km e 30 m;
- E1 (features anuais vs compósito) com resultado neutro/negativo;
- E2a (pares GEDI) dominado por ruído, com SD de ΔAGB de 72 Mg ha⁻¹ na Amazônia e 25 no Cerrado;
- nenhuma série anual completa, nenhuma validação temporal e nenhuma análise de consistência
  entre mapas sucessivos.

Portanto, diferenças entre mapas anuais, se geradas, devem ser tratadas como **não validadas** e
provavelmente dominadas por variabilidade de features, composição de amostra e erro do modelo.
Não se pode afirmar detecção de mudança real.

### 5.8 O sistema consegue incorporar novos inventários automaticamente?

Não. Não há:

- esquema canônico de observações;
- adaptadores por fonte;
- ingestão idempotente;
- controle de duplicidade entre repositórios;
- harmonização de unidades, DAP mínimo, equações e componentes;
- registro de proveniência/licença por observação;
- tabela única de observações em Parquet/GeoParquet.

O que existe são fetchers de sensores e scripts manuais para tabelas de treino/campo. A inclusão
de um novo inventário exige trabalho ad hoc e não deixa um registro científico completo.

### 5.9 Existe separação efetiva entre treinamento, calibração e validação independente?

Há separação **procedimental**, mas não **científica completa**:

- `run_region_cv`, `run_region_conformal` e `run_region_aoa` separam os índices de treino,
  calibração, conformal e teste; isso é correto no código.
- Porém, calibração e teste compartilham a mesma referência GEDI. Isso não é validação
  independente; é transferência dentro do produto GEDI.
- A amostra de calibração é sorteada aleatoriamente dentro do box e fica intercalada
  espacialmente com o teste; isso pode inflar o ganho da calibração local.
- Não há holdout de campo independente para o modelo principal, nem benchmark fixo protegido.
- O PLOS é independente do GEDI, mas é antigo, só do Cerrado e pequeno; o ORNL ainda não está
  integrado.

### 5.10 As incertezas são propagadas corretamente para polígonos?

Não. `polygon_stats` faz block bootstrap sobre blocos de 5 km das **predições**, o que é um
avanço em relação a `√n` de pixels, mas:

- usa `area_ha_per_row=100` fixo, sem área real de interseção célula–polígono;
- não recebe geometria nem CRS;
- não calcula mediana;
- não propaga erro GEDI, alometria, calibração, máscara de domínio, classe ou fitofisionomia;
- não separa intervalo de predição por célula de intervalo de confiança do estoque agregado;
- não valida a cobertura do IC no nível do polígono;
- pode subestimar a incerteza porque a covariância residual não é estimada fora dos blocos.

### 5.11 Quais requisitos de dMRV são atendidos?

Nenhum portão G0–G7 está completamente atendido para uso operacional. Situação aproximada:

| Portão | Situação | Evidência |
|---|---|---|
| G0 Escopo | Parcial | Model card existe, mas não por versão anual; README/docs com escopo antigo |
| G1 Dados/proveniência | Parcial | Manifestos de downloads; inventários sem proveniência canônica; MapBiomas local sem automação |
| G2 Validação | Não atendido | Sem campo independente pós-2019 na Amazônia; PLOS antigo/Cerrado; ORNL não integrado |
| G3 Incerteza | Parcial | Conformal por célula; sem decomposição; polígono incompleto |
| G4 Estratificação | Parcial | Domínio 3/4 e AOA; sem fitofisionomia IBGE; crosswalk inicial |
| G5 Reprodutibilidade | Parcial | Código/testes/manifestos; derivados fora do git; sem lockfile; sem versionamento de features |
| G6 QA/QC | Parcial | `mrv-check` cobre parte; sem verificação de raster, bordas, consistência anual ou duplicatas de inventário |
| G7 Auditoria | Parcial | ADRs e diário; sem model/data cards por versão e sem matriz de evidências dMRV completa |

O produto atual deve ser classificado como **experimental**, não como base MRV.

### 5.12 Quais limitações impedem o uso operacional?

1. Referência principal é GEDI L4A, um produto modelado, com erro e viés conhecidos.
2. Ausência de validação de campo independente, sobretudo na Amazônia pós-2019.
3. Base de inventários não ingerida e não harmonizada.
4. Fitofisionomia não integrada ao modelo nem à estratificação.
5. Descasamento de suporte entre treino (footprint) e produto (1 km/30 m).
6. Features anuais incompletas e risco de vazamento temporal.
7. Incerteza não decomposta nem propagada corretamente para estoques.
8. Produto C (polígono) sem geometria, área real e relatório.
9. Ausência de registro de modelos, champion/challenger e splits congelados.
10. Cobertura espacial restrita a 11 boxes, não ao domínio Amazônia/Cerrado.
11. Classes 2/6 e fitofisionomias finas sem decisão/suporte.
12. Documentação e resultados antigos com contradições que dificultam auditoria.

### 5.13 Quais decisões anteriores precisam ser revisadas?

- **ADR-0003 (GEDI como referência principal):** manter GEDI como referência de calibração/
  avaliação, mas subordinar a campo; explicitar que L4A é modelo.
- **ADR-0012 (filtro GEDI):** testar sensibilidade do limiar de 0,9, que pode excluir vegetação
  aberta e enviesar o Cerrado; avaliar `degrade_flag` e `agbd_se`.
- **ADR-0015 (campo primeiro no Cerrado):** correto em princípio, mas não implementado de fato.
- **ADR-0017 (calibração local):** manter, mas calibrar com campo e separar espacialmente a
  amostra de calibração do teste.
- **ADR-0019 (AOA):** manter, mas a implementação atual é uma distância euclidiana simples;
  testar alternativas e validar a cobertura.
- **ADR-0021 (produto anual):** manter, mas explicitar que “mudança” não é detecção de
  desmatamento e que a série anual ainda não está validada.
- **ADR-0022 (GEDI só calibração):** está “proposto”, mas o código já segue a regra no inference;
  atualizar status e auditoria.
- **ADR-0023 (taxonomia fitofisionômica):** está “proposto” e não implementado; priorizar.
- **ADR-0024 (critérios de aceite):** manter, mas completar métricas e critérios de promoção.
- **ADR-0025 (domínio 3/4 vs estrato):** correto; falta a camada de fitofisionomia.
- **ADR-0026 (mapa-first):** entra em conflito com o novo escopo, que exige **Produto C**
  (polígono arbitrário) como produto de primeira classe; revisar para “mapa + polígono”.
- **ADR-0002 (dois modelos por bioma):** testar hierárquico/partial pooling antes de fixar.

Além dos ADRs, revisar `docs/00`, `docs/01`, `docs/16`, `README.md` e `docs/45`, que ainda
contêm escopo antigo (BGB, carbono, desmatamento, 30 m como pixel, “não há modelo treinado” etc.).

### 5.14 Quais funcionalidades existentes extrapolam o objetivo principal?

Não há grandes funcionalidades **implementadas** fora do escopo. O excesso é principalmente
documental e de planejamento:

- BGB, carbono e CO₂e (`docs/10`, `docs/11`, ADR-0011): documentação, sem código;
- desmatamento/reflorestamento e contabilidade de atividade (`docs/16`, `docs/00/01`,
  `data/catalogo_dados.csv` com PRODES): documentação e catálogo, sem modelo;
- projeção futura: não implementada;
- créditos de carbono e certificação: não implementados;
- `README` ainda apresenta BGB e “planejamento completo” como se fossem escopo vigente.

A única funcionalidade implementada que precisa ser reinterpretada é o **mapa de AGB do GEDI**:
ele é útil como baseline A0 e prova de conceito, mas não deve ser apresentado como estimador de
AGB real.

---

## 6. Disponibilidade real de inventários de campo

### 6.1 Situação por fonte (na data da auditoria, antes da reimplementação)

> A seção 13 registra a atualização posterior: IFN com 7.466 UAs canônicas, PLOS com 77 sítios
> ingeridos, ORNL com 10 sítios-ano e IBGE 1:250k baixado.

| Fonte | Volume/cobertura | Status | Uso atual | Limitação principal |
|---|---|---|---|---|
| IFN/SFB — Painel de Biomassa e Carbono | 439.970 registros; Amazônia 119.536; Cerrado 170.627 | Baixado | Seleção de pilotos | Coordenadas ~0,1°; equações múltiplas; variância entre subunidades, não da estimativa |
| PLOS 2018 (Roitman et al.) | 77 sítios; 42 no domínio; Cerrado; 2004–2014 | Baixado | Baseline/validação separada com Landsat | Antigo, só Cerrado, uma parcela por sítio; não cobre Amazônia pós-2019 |
| ORNL Sustainable Landscapes Brazil | 31 CSVs; 2009–2018; 3 sítios recuperados (5 sítios-ano) | Parcialmente baixado/processado | Recuperação metodológica | Fator/datum, palmeiras/lianas, cobertura incompleta; não integrado |
| CEDA/NCEO Manaus plots | 22 parcelas; 2014 | Não baixado | — | Cobertura pequena e antiga |
| NERC EIDC RAINFOR | 29 parcelas; 8.729 árvores; 2017–2019 | Não baixado | — | Acesso e harmonização pendentes |
| Mendeley Vourlitis (Cerrado MT) | Parcelas; 2011–2018 | Não baixado | — | Escopo local |
| Mendeley Maracá (RR) | 129 parcelas; censo 4 | Não baixado | — | Ecótono, não representa o domínio |
| LBA-ECO LC-05 | 50 parcelas de 1 ha; 1997–2001 | Não baixado | — | Antigo e local |
| EBA (Zenodo) | Mapa de AGB da Amazônia ~2018 | Não baixado | — | É produto modelado; benchmark, não verdade |
| IFN dados botânicos (SNIF) | Inventário árvore-a-árvore | Não baixado | — | Termos e granularidade a confirmar |

### 6.2 Avaliação

- A base é **suficiente para pesquisa metodológica**, mas **insuficiente para operação**.
- O IFN é a maior fonte potencial, mas a coordenada ~0,1° impede pareamento pixel a pixel;
  serve para validação regional, calibração com erros nas covariáveis ou prior.
- O PLOS é a única referência independente já usada, mas é antigo, pequeno e restrito ao Cerrado.
- O ORNL é promissor para 2009–2018, mas precisa ser concluído e harmonizado.
- Não existe base de campo independente pós-2019 na Amazônia; isso é um bloqueio para G2.
- É necessário um esforço de curadoria, licença, harmonização e documentação antes de qualquer
  afirmação de acurácia.

---

## 7. Lacunas científicas prioritárias

### P0 — bloqueiam qualquer alegação de AGB operacional

1. **Hierarquia de referência e estimando:** campo como referência primária; GEDI como
   calibração/avaliação; distinguir medição, observação estrutural e produto modelado.
2. **Ingestão canônica de inventários:** esquema único, adaptadores, idempotência, deduplicação,
   proveniência, licença, harmonização de DAP/altura/densidade/equações/componentes.
3. **Fitofisionomia:** camada IBGE 1:250k, crosswalk documentado e teste de uso como feature,
   estrato, hierarquia ou especialista.
4. **Série anual sem vazamento:** cubo de features do ano, máscara do ano, validação temporal,
   primeiro ano defensável e política de dados disponíveis em t.
5. **Suporte e resolução:** formalizar mudança de suporte, testar 30/100/250/500/1.000 m e
   impedir que a resolução nominal seja confundida com acurácia.
6. **Incerteza e agregação:** decompor erro de referência, alometria, modelo, preditores,
   máscara e agregação; propagar para fitofisionomia e polígono com área real.
7. **Validação independente:** holdout de campo, validação espacial com buffer, temporal, por
   fonte e por fitofisionomia.

### P1 — necessárias para o produto

8. Comparação de arquiteturas (global, bioma, especialista, hierárquico, multifonte, ensemble).
9. Produto A completo (mapa, IC, AOA, domínio, fitofisionomia, qualidade, COG).
10. Produto B (tabela por fitofisionomia com área, média, mediana, estoque e IC).
11. Produto C (polígono com geometria, área de interseção, relatório e incerteza).
12. Registro de modelos, champion/challenger, splits congelados e model cards por versão.
13. CLI científica e orquestração do fluxo `data → features → train → calibrate → validate →
    predict → polygon → report`.
14. Matriz de requisitos dMRV com evidência, lacuna e ação.
15. Correção da documentação e remoção de contradições.

### P2 — melhorias e benchmarks

16. Produtos globais como benchmark (CCI, EBA etc.), nunca como verdade.
17. Covariáveis adicionais: solo, fogo, vegetação secundária, textura SAR, estrutura.
18. Classes 2 e 6, se decidido.
19. Expansão geográfica e nacional.
20. BGB, carbono e CO₂e, somente após consolidação da AGB.

---

## 8. Arquitetura proposta

### 8.1 Princípio

Não fazer uma reconstrução integral. Preservar o que funciona e evoluir por contratos. A
estrutura abaixo é conceitual; a organização física pode ser incremental.

```text
biomass_model/
  data_catalog/          # fontes, licenças, versões, status, cobertura
  data_ingestion/        # adaptadores, download, idempotência, deduplicação
  inventory/             # esquema canônico de observações e tabelas Parquet/GeoParquet
  allometry/             # equações, domínio de validade, incerteza
  lidar/                 # GEDI L2A/L2B/L4A, LiDAR aerotransportado, distinção de tipos
  harmonization/         # unidades, DAP mínimo, componentes, data, suporte
  stratification/        # IBGE, MapBiomas, fitofisionomia, crosswalk
  features/              # cubo anual, covariáveis, features de estado
  training/              # baselines, algoritmos, arquiteturas, hiperparâmetros
  calibration/           # calibração local/regional e validação da calibração
  validation/            # espacial, temporal, fonte, ecológica, métricas
  uncertainty/           # conformal/QRF, bootstrap espacial, Monte Carlo, decomposição
  applicability/         # AOA, extrapolação, domínio de aplicabilidade
  temporal/              # máscaras anuais, coerência, primeiro ano, vazamento
  inference/             # mapas, predição por tile, IC, AOA, flags
  aggregation/           # fitofisionomia, polígono, área real, estoque
  model_registry/        # versões, seeds, features, métricas, model cards
  reporting/             # relatórios, tabelas, metadados, limitações
  monitoring/            # drift, nova versão, champion/challenger
  cli/                   # comandos científicos
```

### 8.2 Contratos de dados

**Observação canônica (mínimo):** `observation_id`, `source`, `source_version`,
`observation_type` (campo, LiDAR, GEDI L4A, produto), `reference_date`, `geometry`, `crs`,
`location_accuracy_m`, `support_area_ha`, `biome`, `fitofisionomia`, `mapbiomas_class`,
`agb_mg_ha`, `agb_uncertainty_mg_ha`, `method`, `allometric_equation`, `quality_flags`,
`license`, `citation`, `model_status`.

**Registro de modelo:** `model_id`, `version`, `training_data_hash`, `feature_set_hash`,
`algorithm`, `hyperparameters`, `seed`, `validation_scheme`, `metrics`, `predictions_hash`,
`model_card`, `promotion_status`.

**Mapa (bandas mínimas):** `agbd_mg_ha`, `agbd_sd`, `agbd_lo90`, `agbd_hi90`, `aoa_inside`,
`aoa_distance`, `domain_mask`, `mapbiomas_class`, `fitofisionomia_id`, `quality_flags`.

**Polígono (relatório mínimo):** área do polígono, área elegível analisada, área por
fitofisionomia, média, mediana, estoque total, IC, número de células, fração na AOA, limitações
e versão do modelo/dados.

### 8.3 Stack e reprodutibilidade

- Python, ferramentas abertas, processamento local por blocos.
- Parquet/GeoParquet para observações; COG/GeoTIFF para mapas.
- Configuração declarativa (YAML) por experimento.
- Manifestos de execução com hash de inputs, features, modelo e saídas.
- Cache e reutilização de covariáveis; execuções retomáveis.
- Testes unitários e de integração; logs estruturados; seeds e lockfile.
- Preservar todos os artefatos anteriores; novas versões não sobrescrevem as antigas.

---

## 9. Plano de desenvolvimento por fases

### Fase 1 — Alinhamento de escopo e congelamento do baseline

- **Objetivo:** alinhar documentos, estimandos, ADRs e critérios; congelar o atual como A0.
- **Dependências:** aprovação das decisões da seção 11.
- **Tarefas:** revisar `README`, `HANDOFF`, `docs/00/01/16/33/39/45`; criar ADRs de substituição;
  definir estimando e hierarquia de referência; registrar que o produto atual é experimental.
- **Entregáveis:** ADRs revisados, documento de escopo v2, inventário de artefatos A0.
- **Critério de saída:** nenhuma contradição sobre “AGB real vs GEDI” e “mapa vs polígono”.

### Fase 2 — Inventários e dados de referência

- **Objetivo:** construir a base observacional canônica e avaliar sua qualidade.
- **Dependências:** Fase 1; acesso/licenças.
- **Tarefas:** adaptadores IFN/PLOS/ORNL/CEDA/RAINFOR/LBA-ECO/Mendeley; esquema canônico;
  harmonização de DAP, altura, densidade, equações, componentes e unidades; deduplicação;
  proveniência; avaliação de representatividade; allometria e incerteza.
- **Hipóteses:** H-A: a base de campo disponível permite validação independente por bioma;
  H-B: a harmonização reduz viés entre fontes.
- **Experimentos:** auditoria de cobertura; comparação de AGB por fonte; sensibilidade a DAP
  mínimo e equação; validação regional com IFN.
- **Entregáveis:** `observations.parquet`, catálogo de fontes, data cards, relatório de lacunas.
- **Critério de saída:** ≥30 sítios independentes por bioma, com suporte e incerteza documentados;
  ou declaração explícita de que o critério não foi atingido.

### Fase 3 — Estratificação fitofisionômica

- **Objetivo:** integrar IBGE–MapBiomas e testar o papel da fitofisionomia.
- **Dependências:** Fase 2; camada IBGE 1:250k.
- **Tarefas:** obter/mosaicar IBGE; construir crosswalk; mapear ambiguidades; medir
  representatividade por fitofisionomia; testar feature categórica, estrato de calibração,
  estrato de amostragem e modelo hierárquico.
- **Hipóteses:** H1 (fitofisionomia reduz viés), H2 (hierarquia supera modelos isolados),
  H6 (fitofisionomia reduz necessidade de calibração local).
- **Entregáveis:** camada de fitofisionomia, crosswalk versionado, tabela de representatividade,
  resultados dos testes.
- **Critério de saída:** decisão documentada sobre como a fitofisionomia entra no modelo.

### Fase 4 — Experimentos de modelagem

- **Objetivo:** comparar arquiteturas, algoritmos, estratégias e resoluções.
- **Dependências:** Fases 2–3; features anuais.
- **Tarefas:** baselines (média por estrato, regressão); RF, Extra Trees, XGBoost, LightGBM,
  CatBoost, GAM, hierárquico/partial pooling, multifonte, ensemble; ablação de features;
  resoluções 30/100/250/500/1.000 m; calibração local/regional.
- **Hipóteses:** H4 (features anuais), H5 (consistência temporal), H7 (GEDI como calibração),
  H8 (1 km vs 30 m).
- **Critério de seleção:** não apenas R²; viés, generalização espacial/temporal, estabilidade,
  interpretabilidade, desempenho por fitofisionomia, qualidade das incertezas e custo.
- **Entregáveis:** configs, manifestos, métricas, predições, relatório comparativo.
- **Critério de saída:** modelo candidato que supere A0 de forma consistente e passe pela
  validação independente.

### Fase 5 — Validação e incerteza

- **Objetivo:** validação independente, AOA e propagação de erros.
- **Dependências:** Fases 2–4.
- **Tarefas:** blocos espaciais com buffer; leave-one-region-out; leave-one-year-out;
  leave-one-inventory-out; leave-one-source-out; validação por fitofisionomia e faixa de AGB;
  conformal/QRF; bootstrap espacial; Monte Carlo; decomposição de variância; cobertura de IC
  por célula, estrato e polígono.
- **Entregáveis:** relatório de validação, mapas de AOA/IC, tabela de decomposição de incerteza.
- **Critério de saída:** critérios de `docs/37` §6 satisfeitos, incluindo G2.

### Fase 6 — Modelagem temporal

- **Objetivo:** série anual com máscaras e features do ano, sem vazamento.
- **Dependências:** Fases 1–5.
- **Tarefas:** cubo anual por tile/ano; S2/S1/Landsat anuais; máscara MapBiomas do ano;
  covariáveis disponíveis em t; validação temporal; consistência entre mapas; definição do
  primeiro ano defensável.
- **Entregáveis:** mapas anuais, séries de features, relatório de estabilidade.
- **Critério de saída:** mapas anuais reprodutíveis e validados; diferenças anuais com incerteza;
  nenhuma alegação de mudança real sem teste.

### Fase 7 — Estimativas por polígono e por fitofisionomia

- **Objetivo:** Produto B e Produto C.
- **Dependências:** Fases 3–6.
- **Tarefas:** ler GeoJSON/GPKG/SHP; validar geometria/CRS; interseção real célula–polígono;
  área elegível; zonal stats; média/mediana/estoque; IC por block bootstrap espacial; tabela por
  fitofisionomia; relatório e arquivos geoespaciais; distinção Mg/ha, Mg, Mg C e Mg CO₂e.
- **Entregáveis:** relatório JSON/CSV/GeoPackage, tabela por estrato, mapa recortado.
- **Critério de saída:** estoque reproduzível pela soma das células; cobertura de IC adequada;
  área elegível e limitações declaradas.

### Fase 8 — Aprendizado evolutivo

- **Objetivo:** ingestão, retreinamento, calibração e promoção governada.
- **Dependências:** Fases 2–7.
- **Tarefas:** detecção de novas fontes/versões; ingestão idempotente; catálogo; avaliação de
  representatividade; treino candidato; calibração; validação; comparação com champion;
  promoção somente com critérios; registro e model cards.
- **Entregáveis:** pipeline `update`, registro de modelos, champion/challenger documentado.
- **Critério de saída:** nenhuma substituição automática; histórico reproduzível.

### Fase 9 — Operacionalização científica

- **Objetivo:** testes, documentação, reprodutibilidade e aderência dMRV.
- **Dependências:** Fases 1–8.
- **Tarefas:** testes de integração/regressão; CI; lockfile; manifestos de artefatos; matriz
  G0–G7; model/data cards por versão; relatório de limitações; auditoria externa.
- **Entregáveis:** release candidata, documentação completa, matriz de evidências.
- **Critério de saída:** G0–G7 completos ou produto explicitamente marcado como experimental.

### 9.1 Riscos transversais e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Base de campo insuficiente | Bloqueia G2 e operação | Priorizar IFN/ORNL/RAINFOR; parceria de campo; declarar limitação |
| GEDI enviesado em savana | Viés no Cerrado | Campo como referência; sensibilidade de filtros; calibração local |
| Vazamento temporal | Estimativas históricas otimistas | Política de dados disponíveis em t; CV temporal; auditoria |
| Vazamento espacial | Ganho de calibração inflado | Blocos com buffer; calibração separada espacialmente |
| Fitofisionomia sem suporte | Estratos instáveis | Critérios objetivos de especialização; partial pooling |
| Incerteza otimista | Falsa confiança | Decomposição; cobertura empírica; Monte Carlo |
| Documentação divergente | Auditoria falha | Revisão documental na Fase 1; ADRs de substituição |
| Custo computacional | Atraso | Processamento por blocos, cache, execuções retomáveis |

---

## 10. O que fazer primeiro (sequência recomendada)

1. **Aprovar as decisões da seção 11.**
2. **Congelar A0** (modelo GEDI atual) e registrar que é baseline, não produto de AGB real.
3. **Fase 2 primeiro:** ingestão canônica de inventários e avaliação de representatividade.
4. **Fase 3 em paralelo:** obter IBGE e construir a camada de fitofisionomia.
5. **Fase 1 documental:** corrigir README/docs/ADRs e criar ADRs de substituição.
6. **Fase 4–5:** só então comparar arquiteturas e validar com campo.
7. **Fase 6–7:** mapas anuais e polígono após a base observacional e a validação.
8. **Fase 8–9:** automação e operacionalização depois de estabilizar o método.

Não recomendo começar expandindo mapas para todos os boxes/anos antes de resolver a referência,
a fitofisionomia e a validação de campo. Isso produziria mais mapas com o mesmo problema
científico.

---

## 11. Perguntas objetivas para decisão do usuário

1. **Hierarquia de referência:** aprovar que inventários de campo são a referência primária e
   que GEDI L4A é camada auxiliar de calibração/avaliação, nunca verdade de campo?
   (Recomendado: sim.)
2. **Status do produto atual:** aprovar que o modelo/mapa GEDI atual passa a ser **baseline A0
   experimental**, sem ser apresentado como estimador de AGB real?
   (Recomendado: sim.)
3. **Produto C:** aprovar que a estimativa por polígono arbitrário é produto de primeira classe,
   com geometria, área real, incerteza e relatório, revisando o ADR-0026?
   (Recomendado: sim.)
4. **Fitofisionomia:** aprovar o uso do IBGE 1:250k como referência, com crosswalk documentado,
   e testar formalmente feature, estrato, hierarquia e especialista?
   (Recomendado: sim.)
5. **Domínio:** manter apenas classes 3 e 4, deixando classes 2 e 6 fora até decisão posterior?
   (Recomendado: sim, com exclusão declarada.)
6. **Resolução:** manter 1 km como oficial e 30 m como diagnóstico até haver validação
   independente, testando também 100/250/500 m?
   (Recomendado: sim.)
7. **Campo:** autorizar a busca de parceria/orçamento para campo independente pós-2019 na
   Amazônia e para completar ORNL/IFN/RAINFOR?
   (Recomendado: sim; sem isso, G2 fica bloqueado.)
8. **Primeiro ano da série histórica:** definir o primeiro ano cientificamente defensável
   (por exemplo, 2015 com S2, 2004 com Landsat/MapBiomas ou 2019 com GEDI). Qual priorizar?
9. **Classes 2/6:** incluir ou excluir formalmente? Se incluir, exigir dados de campo e
   fitofisionomia específicos.
10. **Licença do produto:** definir a licença dos mapas/tabelas e como tratar o share-alike do
    MapBiomas.
11. **Prioridade imediata:** começar por inventários + fitofisionomia (recomendado) ou por
    completar features anuais/mapas de todos os boxes?
12. **Critérios de aceite:** confirmar os limites de `docs/37` §6 (RMSE relativo, viés, cobertura
    IC90, AOA) ou revisá-los antes dos experimentos?

---

## 12. Conclusão

O projeto tem uma base de engenharia sólida e resultados honestos, mas o estado atual **não
atende** ao novo escopo científico. O desvio não é de hiperparâmetro: é de **referência,
estratificação, suporte, temporalidade e produto**. A evolução recomendada é preservar o que
existe como A0, construir a base observacional canônica, integrar fitofisionomia, validar com
campo, decompor incerteza e só então produzir mapas anuais e estimativas por polígono como
produtos científicos.

## 13. Atualização 2026-11-24 — decisões aprovadas e início da reimplementação

O usuário aprovou as decisões da seção 11, com dois ajustes:

- **Resolução:** 30 m é a resolução oficial; 1 km passa a ser experimental/diagnóstico
  (ADR-0030).
- **Referência e escopo:** campo é a referência primária; GEDI é auxiliar; o modelo GEDI-only
  anterior é baseline A0 experimental, preservado mas não promovido a produto (ADR-0027 e
  ADR-0031).
- **Produto C:** polígono arbitrário é produto de primeira classe (ADR-0028).
- **Fitofisionomia:** IBGE 1:250k como camada estrutural (ADR-0029).
- **Inventários:** autorizada a aquisição de dados abertos de 2000 em diante, antigos e novos
  (ADR-0031), com ingestão canônica (ADR-0032).

Implementado nesta etapa (60 testes passando):

- `inventory/`: esquema canônico, validação, escrita e adaptadores PLOS, IFN, ORNL e GEDI L4A.
- `allometry/`: Chave 2005, palmeira e liana.
- `stratification/`: normalização, crosswalk e rasterização de fitofisionomia.
- `aggregation/polygon.py`: Produto C com geometria, área real, média, mediana, estoque, IC e
  tabelas por classe/fitofisionomia.
- CLI: `inventory`, `polygon`, `fitofisionomia` e `ibge-vegetacao`.
- ADRs 0027–0032; README/HANDOFF atualizados.
- IBGE vegetação 1:250.000 versão 2026 baixada e fitofisionomia rasterizada para os boxes
  centrais 2021 (Amazônia e Cerrado), com JSON de códigos, grupos e classe MapBiomas.
- `observation_features.py`: features Landsat/S2, DEM, ERA5 e histórico MapBiomas para a tabela
  canônica, sem vazamento temporal no histórico.
- `validation/spatial.py`: blocos espaciais com buffer.
- `training/field.py`: RandomForest campo-first com validação por bloco+buffer.
- Baseline campo-first F0 (PLOS 2018, Cerrado; `docs/47`): 40 sítios no domínio; validação
  primária 200 km/buffer 25 km, n=16, R²=0,262, RMSE=10,81, IC90 cobertura 0,813; sensibilidade
  100 km, n=40, R²=0,197, RMSE=9,54, cobertura 0,900. Não promovido: amostra antiga/pequena,
  sem holdout independente e IC otimista no cenário de blocos.

O diagnóstico original permanece como registro histórico. A próxima etapa é completar a ingestão
de IFN/ORNL, resolver coordenadas, obter IBGE 1:250k e migrar o treinamento para a tabela canônica.
