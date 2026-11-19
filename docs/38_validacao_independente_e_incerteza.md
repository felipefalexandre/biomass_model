# 38 — Validação independente, mudança e incerteza por polígono

**Data:** 2026-11-18 · **Status:** plano e auditoria; sem uso dos dados para ajustar modelos.

## 1. Duas linhas de avaliação (obrigatório)

- **Linha A — fidelidade ao GEDI:** o modelo reproduz/espacializa o L4A em regiões não usadas?
  É o que os R² atuais medem. Não é acurácia de biomassa verdadeira.
- **Linha B — concordância com campo:** o modelo concorda com inventários independentes,
  respeitando escala, suporte, data e método?
- **Linha T — dinâmica:** o modelo responde corretamente a mudanças conhecidas e permanece
  estável onde não há mudança?

Nenhuma melhoria na Linha A será apresentada como melhoria na Linha B.

## 2. PLOS 2018 — auditoria completa

Arquivo: `data/reference/plos2018_auditoria.csv`.

| Situação | n |
|---|---|
| Total no arquivo | 77 |
| Bioma Cerrado | 75 |
| Fora do Cerrado (Amazônia, Caatinga) | 2 |
| Cerrado com inventário 2004–2014 e Landsat | 50 |
| No domínio 3/4 no ano | **42 (usados)** |
| Anteriores a 2004 (MapBiomas local) | 25 |
| 2004–2014 fora do domínio | 8 |

- **Viés de seleção:** usados têm mediana 24,2 Mg ha⁻¹ (12,9–37,0); não usados 18,8
  (10,7–27,5). O domínio exclui a cauda baixa.
- **Recuperação possível:** obter MapBiomas 1985–2003 para reclassificar os 25 sítios antigos;
  eles usam Landsat, não S2. Se a classe no ano for 3/4, entram como validação histórica.
- **Sítios fora do domínio:** 8 podem ser usados em um **estrato campestre separado**, sem
  misturar com 3/4; isso testa justamente onde o GEDI erra.
- **Data e suporte:** inventário de 1 parcela por sítio; comparar com janela Landsat de 1 km é
  compatível em ordem de grandeza, mas não em suporte estatístico. Reportar como validação
  regional, não pixel a pixel.
- **Alometria:** o artigo usa equações próprias; registrar equação e incerteza; não recalcular
  sem necessidade.

**Experimentos imediatos:** comparar A1/A2/A3 com os 42 sítios usando features Landsat do ano;
reservar 1/3 dos sítios (por bloco espacial) para teste final, nunca para escolha de modelo.

## 3. ORNL Sustainable Landscapes Brazil — plano de recuperação

**Fonte:** DOI 10.3334/ORNLDAAC/2007; 31 CSV de inventário (2009–2018), KMZ com transectos;
LiDAR DOI 10.3334/ORNLDAAC/1644.

**Desenho:** *diameter-dependent line sampling* (DDLS) com fator 10, 5 transectos de 500 m,
árvores ≥5 cm, DBH/altura/copa/WSD por árvore (Hunter et al. 2013,
DOI 10.5194/bg-10-8385-2013; Schreuder et al. 1987).

**Estimador confirmado (2026-11-18):** o dicionário de dados traz `AGB` (Mg por fuste) e
`area_sampled` (ha), e os arquivos JAM permitem verificar a geometria. A área de inclusão é
`2 · 500 m · (DBH/10) / 10.000` ha, ou seja **w = DBH/10 m (fator 10 confirmado)** — não era
necessário inferir datum nem fator.

```
densidade_transecto = Σ_i AGB_i / area_i          [Mg ha⁻¹]
densidade_sitio     = média entre transectos
SE                  = desvio entre transectos / √n
```

- JAM_A01/A02: `AGB` e `area_sampled` fornecidos; estimador aplicado diretamente.
- TAP_A01: sem coluna AGB; AGB individual calculada por Chave 2005
  (`0,0509·WSD·DBH²·Htot/1000` Mg), **somente árvores tipo O**; palmeiras e lianas exigem
  alometria própria e ficam fora nesta versão.

**Resultados (dados reais, não publicados como validação final):**

| Sítio | Ano | AGBD (Mg ha⁻¹) | SE | Transectos | Método |
|---|---|---|---|---|---|
| JAM_A01 | 2011 | 254,7 | 71,4 | 2 | AGB/área fornecidos |
| JAM_A02 | 2011 | 308,3 | 13,7 | 6 | AGB/área fornecidos |
| TAP_A01 | 2009 | 329,8 | 22,4 | 6 | Chave 2005, árvores O |
| TAP_A01 | 2010 | 323,0 | 21,4 | 6 | idem |
| TAP_A01 | 2011 | 321,4 | 21,3 | 6 | idem |

TAP_A01 fica acima da mediana GEDI do box de Tapajós usado no piloto (~146 Mg ha⁻¹). Isso pode
ser subestimação do L4A, diferença de sítio/estrutura ou efeito de excluir palmeiras/lianas; só
será interpretado após pareamento espacial/temporal.

**Próximos passos:** extrair coordenadas dos KMZ; aplicar o estimador a todos os sítios (com o
readme de cada um para comprimento de transecto); incluir alometria de palmeiras/lianas; parear
com Landsat/S2/GEDI do ano; montar a tabela de validação. Não usar os números como verdade até o
pareamento e a checagem de suporte.

**Critério de aceite:** se a AGBD do sítio for compatível com a literatura regional e a variância
entre transectos for razoável, o ORNL entra como validação histórica (2009–2018) e possível
treino. Se não, registrar a lacuna e não usar.

## 4. IFN (Inventário Florestal Nacional)

- Usar apenas para **validação regional/totais**, não para pareamento pixel: coordenadas ~0,1°.
- Verificar licença e granularidade antes de qualquer uso; hoje foi usado só para escolher
  pilotos.
- Comparar distribuições por bioma/UF com o produto agregado, não células individuais.

## 5. Validação de mudança (Linha T)

Referências abertas por ano:

| Evento | Fonte | Uso |
|---|---|---|
| Desmatamento | PRODES (INPE), MapBiomas Alertas | Perda; sinal, magnitude, contraste |
| Transições de cobertura | MapBiomas Coleção 11 | Perda/ganho por classe |
| Fogo | MapBiomas Fogo | Perda abrupta; persistência |
| Regeneração | MapBiomas Vegetação Secundária (idade) | Ganho gradual por idade |
| Estabilidade | áreas 3/4 sem transição | Falso alarme e deriva |

Testes mínimos (definidos em `docs/37`): sinal, magnitude, contraste com buffer, falso alarme,
defasagem, persistência e estabilidade. Nenhum resultado de mudança será declarado sem esses
testes.

## 6. Incerteza: componentes e propagação

| Componente | Como estimar | Onde entra |
|---|---|---|
| GEDI L4A (referência) | `agbd_se` + validação literatura | Incerteza da calibração, não do pixel |
| Alometria de campo | Chave 2014/2005; erro de equação | Linha B |
| Amostragem de campo | bootstrap de transectos/parcelas | Linha B |
| Modelo de espacialização | resíduos LOO/conformal | IC por célula |
| Agregação espacial | covariância residual; blocos de 5 km | IC do estoque por polígono |
| Mudança | resíduos de Δ; testes de evento | IC da mudança |

**Regra:** não somar em quadratura componentes que não são independentes (ex.: erro GEDI e erro
de calibração compartilham modelo). Reportar separadamente e usar simulação (Monte Carlo) com
estrutura de correlação declarada.

**Polígono:** IC do total via block bootstrap sobre blocos de 5 km (ou variograma), não
`√n` de pixels. Validar cobertura por leave-one-polygon-out em áreas com referência.

## 7. Critérios de suficiência

- Linha B com ≥ 30 sítios independentes por bioma (hoje: 42 Cerrado, 0 Amazônia pós-2019).
- Linha T com ≥ 3 eventos por tipo (perda, fogo, ganho) e ≥ 100 células por evento.
- Se não houver dados para um critério, o modelo correspondente não é promovido; fica como
  experimental.
