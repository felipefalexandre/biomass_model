# 26 — Registro de decisões de arquitetura (ADRs)

Índice dos ADRs. Cada decisão tem contexto, opções, decisão, consequências e status.

| ADR | Título | Status |
|---|---|---|
| ADR-0001 | Python local em vez de GEE como trilha principal | aceito |
| ADR-0002 | Dois modelos por bioma, escada de complexidade | aceito |
| ADR-0003 | GEDI L4A como referência principal (produto de modelo) | aceito com ressalva |
| ADR-0004 | Inferência híbrida com dois componentes de variância | aceito |
| ADR-0005 | BGB derivada com cenários, nunca "medida" | substituído por ADR-0011 |
| ADR-0006 | Validação por blocos espaciais e AOA | aceito |
| ADR-0007 | Carbono e CO₂e em módulo separado | aceito |
| ADR-0008 | Processamento por janelas e COG | aceito |
| ADR-0009 | Máscara de elegibilidade como domínio declarado | substituído por ADR-0010 |
| ADR-0010 | Domínio = classes brutas 3 e 4 do MapBiomas (Coleção 11) | aceito |
| ADR-0011 | BGB como modelo separado, não derivado da AGB | aceito |
| ADR-0012 | Filtro de qualidade do GEDI L4A | aceito |
| ADR-0013 | Grade de modelagem e amostragem nos footprints | aceito |
| ADR-0014 | Escala do piloto (~17 km por bioma) | aceito |
| ADR-0015 | Referência do Cerrado: campo primeiro, GEDI auxiliar | aceito |

## ADR-0001 — Python local em vez de GEE

**Contexto:** requisito de ferramentas gratuitas e reprodutibilidade; GEE é gratuito para
pesquisa, mas tem termos que podem restringir uso comercial e redistribuição, e cria dependência
de plataforma.

**Opções:** (a) GEE; (b) Python local; (c) híbrido.

**Decisão:** Python local como trilha principal; GEE apenas como alternativa documentada.

**Consequências:** maior esforço de engenharia e necessidade de infraestrutura; em troca,
controle total, reprodutibilidade e ausência de dependência de termos.

## ADR-0002 — Dois modelos por bioma e escada de complexidade

**Contexto:** Amazônia e Cerrado têm estruturas e faixas de biomassa distintas; modelos globais
degradam o Cerrado. Complexidade sem ganho é custo.

**Decisão:** modelos separados por bioma; começar em M0/M1 e subir apenas com ganho validado.

**Consequências:** mais artefatos e validações; melhor ajuste ao domínio; menor risco de
overfitting por complexidade desnecessária.

## ADR-0003 — GEDI L4A como referência principal

**Contexto:** GEDI oferece cobertura amostral ampla e estrutura vertical; porém L4A é produto de
modelo, com erro próprio, pior em alta AGB e em savana.

**Decisão:** usar L4A como referência principal, com filtros de qualidade, AOA e validação
independente; declarar que é produto de modelo.

**Consequências:** viável em escala, mas exige cuidado com circularidade e viés no Cerrado.

## ADR-0004 — Inferência híbrida

**Contexto:** nem design-based puro (GEDI não é amostra probabilística) nem model-based puro
(ignora incerteza de amostragem) são adequados.

**Decisão:** inferência híbrida/quasi-design, com decomposição de variância.

**Consequências:** IC mais honestos; necessidade de bootstrap espacial e declaração de
suposições.

## ADR-0005 — BGB derivada com cenários

**Status:** substituído por ADR-0011.

**Contexto:** BGB não é observável por satélite; razões e equações variam.

**Decisão:** BGB como módulo derivado, com cenários mínimo/central/máximo e fontes explícitas.

**Consequências:** transparência; impossibilidade de afirmar BGB "medida"; necessidade de
propagar incerteza.

## ADR-0006 — Validação por blocos espaciais e AOA

**Contexto:** CV aleatório superestima desempenho em dados espaciais.

**Decisão:** blocos espaciais como métrica principal; LORO como estresse; AOA obrigatória.

**Consequências:** métricas mais realistas (e piores); decisões mais defensáveis.

## ADR-0007 — Carbono e CO₂e em módulo separado

**Contexto:** confusão de unidades é erro recorrente e grave.

**Decisão:** conversões isoladas, com `f_C`, 44/12 e cenários explícitos; nenhum número de
carbono sem unidade.

**Consequências:** clareza; necessidade de manter fatores versionados.

## ADR-0008 — Janelas e COG

**Contexto:** raster nacional excede memória; leitura integral é inviável.

**Decisão:** processamento por janelas de 2048 px; saída COG.

**Consequências:** complexidade de código; escalabilidade e retomada.

## ADR-0009 — Máscara de elegibilidade como domínio

**Status:** substituído por ADR-0010.

**Contexto:** a etapa anterior definiu vegetação nativa estável (classe 3/4 em 2007–2016).

**Decisão:** usar essa máscara como domínio declarado; não confundir com "toda a vegetação".

**Consequências:** totais comparáveis aos da etapa anterior; exclusão de regeneração precisa ser
declarada como limitação de escopo.

## ADR-0010 — Domínio = classes brutas 3 e 4 do MapBiomas (Coleção 11)

**Status:** aceito.
**Substitui:** ADR-0009.

**Contexto:** o domínio herdado (classe 3/4 em todos os anos 2007–2016) foi desenhado para o
projeto de desmatamento e exclui regeneração e vegetação que mudou de classe. O usuário definiu
que a estimativa deve cobrir as áreas de classe 3 e 4 do MapBiomas no ano de referência.

**Decisão:** `dominio(t) = (classe(t) == 3) | (classe(t) == 4)`, com 3 = Formação Florestal e
4 = Formação Savânica (Coleção 11). A máscara 2007–2016 passa a ser estrato opcional ("vegetação
estável"), não o domínio. Mangue (5), floresta alagável (6) e formações campestres (11/12) ficam
fora da v1, por declaração.

**Consequências:** denominador anual; comparabilidade com a etapa anterior só com o estrato
estável explícito; separação definitiva entre códigos brutos e o `ClassCode` do pipeline de
desmatamento; estratificação bioma × classe × tipologia.

## ADR-0011 — BGB como modelo separado, não derivado da AGB

**Status:** aceito.
**Substitui:** ADR-0005.

**Contexto:** BGB não é observável por satélite e a relação AGB–BGB varia com solo, clima,
fisionomia, fogo e idade. O usuário decidiu que BGB deve ser um modelo próprio, focado em solo,
acoplado ao sistema apenas no relato.

**Decisão:** modelo central de BGB treinado em dados de raiz com preditores de solo (SoilGrids),
clima (ERA5-Land), fisionomia (classes 3/4 e tipologia) e estrutura (altura/AGB como covariável
opcional). R:S derivado da AGB fica apenas como linha de base, cenário de sensibilidade e
preenchimento rotulado. AGB e BGB compartilham grade, máscara e módulo de incerteza, mas são
estimados separadamente.

**Consequências:** incerteza maior e mais honesta; necessidade de inventariar dados de raiz;
produto distingue AGB, BGB e total; se faltarem dados de raiz, o modelo é rebaixado a cenário e a
limitação é declarada.

## ADR-0012 — Filtro de qualidade do GEDI L4A

**Status:** aceito. Ver `ADR/0012-filtro-qualidade-gedi.md`.

**Contexto:** `degrade_flag` é bitfield (0/30/70/80); exigir 0 elimina granulos diurnos válidos, e
granulos noturnos de 2021/2022 no piloto não têm predição L4A.

**Decisão:** filtro `l2==1 & l4==1 & agbd>=0 & 0.9<=sensitivity<=1.01`; `degrade_flag` vira
covariável e sensibilidade restrita a `degrade_zero`.

**Consequências:** amostra maior, viés de degradação testado explicitamente.

## ADR-0013 — Grade de modelagem e amostragem nos footprints

**Status:** aceito. Ver `ADR/0013-grade-e-amostragem.md`.

**Contexto:** camadas em CRS/resoluções distintas; pareamento exige grade única.

**Decisão:** grade do MapBiomas (~30 m, EPSG:4326); features reamostradas (bilinear/vizinho);
cada footprint no pixel que o contém; CV por bloco espacial; agregação de relato em 1 km.

**Consequências:** um só grid, detalhe de 10 m perdido (aceitável), sem inflar CV.

## ADR-0014 — Escala do piloto

**Status:** aceito. Ver `ADR/0014-escala-piloto.md`.

**Contexto:** inconsistência entre seleção (512 px) e aquisição (1600 px).

**Decisão:** caixa de ±0,08° (~17,8 km) por piloto para S2, DEM, ERA5 e GEDI.

**Consequências:** ~289 km² por piloto; restrição real passa a ser a densidade GEDI.

## ADR-0015 — Referência do Cerrado: campo primeiro, GEDI auxiliar

**Status:** aceito. Ver `ADR/0015-referencia-cerrado.md`.

**Contexto:** L4A no piloto do Cerrado tem mediana 6,2 Mg ha⁻¹ (59,6% < 10), contra 19,4 do IFN;
viés de savana aberta não corrigível por filtro.

**Decisão:** treinar o Cerrado em parcelas de campo com coordenadas; L4A vira covariável, benchmark e
diagnóstico de cobertura, não alvo.

**Consequências:** menos n, métricas mais fracas e honestas; prioridade para INV03–INV10.

## Modelo de novo ADR

```markdown
## ADR-XXXX — Título

**Contexto:** ...
**Opções:** ...
**Decisão:** ...
**Consequências:** ...
**Status:** proposto | aceito | substituído por ADR-YYYY
**Evidência:** (IDs da matriz)
```
