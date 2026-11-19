# 37 — Plano experimental: estimativa anual de biomassa

**Data:** 2026-11-18 · **Status:** plano revisado; nada implementado nesta etapa.
**Objetivo:** dado um ano t, estimar AGBD (Mg ha⁻¹) e estoque a partir de dados abertos **do ano
t**. O modelo **não estima desmatamento nem reflorestamento**: mapas e modelos de atividade são
externos e usam a biomassa como insumo. GEDI é referência de calibração/avaliação, não entrada.

## 1. O que está sendo estimado

- **AGBD_t(x):** densidade de biomassa aérea (Mg ha⁻¹) em cada célula de 1 km (produto oficial
  candidato) e 30 m (diagnóstico), para o ano t.
- **Estoque_t(P):** integral de AGBD_t sobre o polígono P, com incerteza.
- **Por estrato:** estoque por fitofisionomia/classe, quando houver composição confiável.
- **Diferenças entre anos** podem ser calculadas pelo usuário (mapa_t − mapa_{t−1}) e combinadas
  com mapas externos de desmatamento/fogo/regeneração. O modelo não faz essa combinação nem
  estima a atividade.

## 2. Princípios de desenho

1. **Independência operacional:** no inference, apenas dados abertos do ano (S2/S1/Landsat,
   clima, solo, MapBiomas). Nenhum produto de biomassa (GEDI L4B, CCI, EBA) entra como feature ou
   prior.
2. **Features do ano:** cada ano tem seu próprio cubo; proibido compósito multi-ano único para
   todos os footprints (limitação atual, `docs/35`).
3. **Sem modelo de atividade:** desmatamento, fogo e regeneração entram, se entrarem, apenas como
   covariáveis de estado (ex.: idade secundária, histórico de fogo) que ajudem a estimar AGBD —
   nunca como alvo, detecção ou contabilidade de perda/ganho.
4. **Escala de relatório:** 1 km oficial; 30 m diagnóstico. A resolução não será promovida sem
   evidência de validação/polígono.
5. **Incerteza separada:** erro GEDI (referência), erro do modelo, erro de validação de campo,
   erro de agregação por polígono.
6. **Reprodutibilidade:** cada ano/experimento tem manifesto, versão de features, sementes e
   métricas persistidas.

## 3. Cubo de features anual (proposto)

| Bloco | Variáveis | Fonte | Papel |
|---|---|---|---|
| Óptico S2 | 6 bandas (mediana anual ou estação seca), NDVI/NDMI/NBR/NDII/EVI, percentis, amplitude sazonal, fração válida | S2 L2A (2015+) | Estado do ano |
| Radar S1 | VV/VH em dB, razão, RVI, estatísticas anuais | S1 RTC (2014+) | Estrutura/umidade |
| Landsat | 6 bandas + índices, mediana anual | C2 L2 (1984+) | Série histórica e anos pré-S2 |
| Cobertura | classe MapBiomas do ano; histórico/idade secundária (opcional) | MapBiomas | Estado/domínio |
| Fogo (opcional) | cicatriz do ano, anos desde o último fogo | MapBiomas Fogo | Covariável de estado |
| Clima | climatologia + anomalia anual | ERA5 | Estresse/crescimento |
| Solo | argila, areia, carbono orgânico | SoilGrids | Estático |
| Topografia | elevação, declividade, aspecto | GLO-30 | Estático |

**Não usar no inference:** GEDI, produtos de AGB de terceiros, incremento PRODES (atividade
externa, não covariável de biomassa).

## 4. Arquiteturas candidatas

| ID | Arquitetura | Descrição | Testa |
|---|---|---|---|
| A0 | Baseline atual (M0) | RF estático com compósito multi-ano | Referência |
| A1 | RF anual direto | RF com features do ano t | H1 |
| A2 | Anual + histórico/estado | A1 + idade secundária/fogo/transições como covariáveis | H2 |
| A3 | Hierárquico/fisionômico | Efeitos parciais por bioma/fisionomia/box | H3 |
| A7 | Mixture of experts | Especialistas por cluster ambiental, gate por ambiente | H3 (opcional) |

Modelos de mudança/estado-espaço (ΔAGB, filtro temporal) **não fazem parte** do escopo: a
diferença entre mapas anuais é cálculo externo. Testes de consistência temporal são diagnóstico
de qualidade, não critério de promoção.

## 5. Protocolo de avaliação

### 5.1 Divisões

- **Espacial:** leave-one-box-out (11 boxes), com boxes de teste intocados no ajuste.
- **Temporal:** leave-one-year-out (2019–2023) como robustez a anos, não como validação de
  desmatamento.
- **Calibração local:** sem calibração e com 5–200 células (curvas de aprendizado).

### 5.2 Métricas

- Por box, ano, fisionomia e classe de AGB: R², RMSE, MAE, viés, inclinação; R² após remover viés.
- Erro por quantil (especialmente >200 e <20 Mg ha⁻¹).
- Cobertura e largura do IC90.
- AOA: fração dentro e erro dentro/fora.
- Polígono: RMSE do total, viés agregado, IC do total.
- Consistência temporal (diagnóstico): distribuição de Δ entre anos em áreas sem mudança de
  features; não usar mapas externos de desmatamento como rótulo do modelo.

### 5.3 Validação independente

- **PLOS 2018:** 42 sítios no domínio; Landsat na data.
- **ORNL 2009–2018:** recuperar AGB/ha via DDLS (pendente fator/datum; ver `docs/38`).
- **IFN:** totais regionais, não pixels.
- **Nunca** usar os mesmos sítios para escolher modelo e reportar acurácia final.

## 6. Critérios de aceitação (provisórios)

1. **Espacial:** RMSE mediano por box não pior que A0; nenhum box >5% pior; redução ≥15% em
   metade dos boxes.
2. **Campo:** R² ≥0,40 e |viés| ≤15% em validação independente.
3. **Incerteza:** cobertura IC90 85–95% por bioma/ano; largura reportada por célula e polígono.
4. **Polígono:** erro do total compatível com o IC declarado; sem viés agregado >15%.
5. **Independência:** zero GEDI/derivados no inference (auditado).
6. **Estabilidade:** nenhuma oscilação anual sistemática atribuível a ruído de features; versões
   anuais documentadas. (Não é critério de detecção de desmatamento.)
7. **Reprodutibilidade:** pipeline anual completo com manifesto e testes.

Não aprovar por R² médio contra GEDI. Ganho tem que ser consistente entre boxes e anos.

## 7. Experimentos e decisões

| Exp. | Hipótese | Dados | Divisão | Métrica decisiva | Decide |
|---|---|---|---|---|---|
| E0 | Reproduzir A0 | atuais | LOO | métricas atuais | Congela baseline |
| E1 | Features anuais capturam estado | S2/S1/Landsat por ano | LOO + LOYO | RMSE por box/ano | Se A1 > A0 |
| E2 | Histórico/idade/fogo ajudam | + secundária/fogo | LOO + LOYO | RMSE/viés | Se A2 > A1 |
| E3 | Fisionomia/hierarquia ajuda | taxonomia nível 1–2 | LOO | viés por fisionomia | Se A3 > A2 |
| E7 | Calibração pode ser reduzida | curvas 5–200 células | LOO | nº de células p/ meta | Se H6 |
| E8 | Filtros/pesos GEDI mudam conclusão | GEDI bruto | LOO | sensibilidade | Robustez |
| E9 | Polígono e incerteza | células + covariância | bootstrap espacial | cobertura do total | Se incerteza defensável |

## 8. O que já é possível com os dados atuais

- E0 e E1 parcial (2019–2024, S2/S1 disponíveis); GEDI cobre 2019–2023/24.
- E8 com os CSVs já baixados; E9 em 1 km com os boxes atuais.
- Validação PLOS com Landsat anual (2004–2014).

## 9. O que depende de novos dados

- **MapBiomas pré-2004** (25 sítios PLOS e série histórica).
- **ORNL** com fator/datum resolvidos.
- **Solo (SoilGrids)** e **secundária/fogo** como covariáveis (opcionais).
- **Campo independente pós-2019 na Amazônia** (não existe hoje).

## 10. Riscos

- **Não estacionariedade:** relações treinadas em 2019–2023 podem não valer para 2025+.
- **Cobertura GEDI desigual:** calibração restrita a certas órbitas/regiões.
- **Saturação óptica:** AGB >250 Mg ha⁻¹ difícil; declarar limite.
- **Instabilidade anual:** features ruidosas podem gerar saltos; diagnosticar e estabilizar
  features, não modelar desmatamento.
- **MapBiomas:** erro de classe propaga; quantificar.
- **Escopo:** não prometer detecção de desmatamento; isso é produto externo.
