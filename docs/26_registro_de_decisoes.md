# 26 — Registro de decisões de arquitetura (ADRs)

Índice dos ADRs. Cada decisão tem contexto, opções, decisão, consequências e status.

| ADR | Título | Status |
|---|---|---|
| ADR-0001 | Python local em vez de GEE como trilha principal | aceito |
| ADR-0002 | Dois modelos por bioma, escada de complexidade | aceito |
| ADR-0003 | GEDI L4A como referência principal (produto de modelo) | aceito com ressalva |
| ADR-0004 | Inferência híbrida com dois componentes de variância | aceito |
| ADR-0005 | BGB derivada com cenários, nunca "medida" | aceito |
| ADR-0006 | Validação por blocos espaciais e AOA | aceito |
| ADR-0007 | Carbono e CO₂e em módulo separado | aceito |
| ADR-0008 | Processamento por janelas e COG | aceito |
| ADR-0009 | Máscara de elegibilidade como domínio declarado | aceito |

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

**Contexto:** a etapa anterior definiu vegetação nativa estável (classe 3/4 em 2007–2016).

**Decisão:** usar essa máscara como domínio declarado; não confundir com "toda a vegetação".

**Consequências:** totais comparáveis aos da etapa anterior; exclusão de regeneração precisa ser
declarada como limitação de escopo.

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
