# 37 — Plano experimental: estimativa anual e atualização do estoque

**Data:** 2026-11-18 · **Status:** plano; nada implementado nesta etapa.
**Objetivo:** dado um ano t, estimar AGBD (Mg ha⁻¹) e estoque a partir de dados abertos **do ano
t**, atualizar o estoque em relação a t−1 e responder a mudanças reais observadas por satélite.
GEDI é referência de calibração/avaliação, **não** é entrada do estimador.

## 1. O que está sendo estimado

- **AGBD_t(x):** densidade de biomassa aérea (Mg ha⁻¹) em cada célula de 1 km (produto oficial
  candidato) e 30 m (diagnóstico), para o ano t.
- **Estoque_t(P):** integral de AGBD_t sobre o polígono P, com incerteza.
- **ΔAGB_{t−1→t}(x):** mudança anual, decomposta em perda (desmatamento, fogo, corte) e ganho
  (regeneração, crescimento), com contabilidade explícita das áreas que saem/entram no domínio
  3/4.
- **Não é previsão:** o modelo não projeta anos futuros sem observação; ele estima o estado do
  ano observado e o atualiza quando nova observação chega.

## 2. Princípios de desenho

1. **Independência operacional:** no inference, apenas dados abertos do ano (S2/S1/Landsat,
   clima, solo, MapBiomas, fogo, PRODES). Nenhum produto de biomassa (GEDI L4B, CCI, EBA) entra
   como feature ou prior.
2. **Features do ano:** cada ano tem seu próprio cubo de features; proibido compósito multi-ano
   único para todos os footprints (limitação atual, §3 de `docs/35`).
3. **Estado + mudança:** a estimativa anual não é um ajuste independente por ano; há um estado
   temporal com processo (crescimento gradual, perda abrupta) e observação (satélite).
4. **Prior assimétrico:** perda pode ser abrupta (desmatamento/fogo); ganho é limitado por
   taxas de crescimento da literatura. Isso evita “ganhos” espúrios e permite rastrear quedas.
5. **Contabilidade de transições:** áreas que deixam o domínio 3/4 no ano t não desaparecem; são
   reportadas como perda. Áreas que entram (regeneração) são ganho. O mapa de densidade e o
   balanço de estoque são produtos separados e reconciliáveis.
6. **Incerteza separada:** erro GEDI (referência), erro do modelo de espacialização, erro de
   validação de campo, erro de agregação por polígono. Não somar como se fossem independentes.
7. **Reprodutibilidade:** cada ano/experimento tem manifesto, versão de features, sementes e
   métricas persistidas.

## 3. Cubo de features anual (proposto)

| Bloco | Variáveis | Fonte | Papel temporal |
|---|---|---|---|
| Óptico S2 | 6 bandas (mediana da estação seca), NDVI/NDMI/NBR/NDII/EVI, percentis 10/50/90, amplitude sazonal, data do pico, fração válida SCL | S2 L2A (2015+) | Estado do ano |
| Radar S1 | VV/VH em dB, razão, RVI, estatísticas anuais (mediana, IQR), contagem | S1 RTC (2014+) | Estrutura/umidade; nuvem |
| Landsat | 6 bandas + índices, mediana anual | C2 L2 (1984+) | Série histórica e anos pré-S2 |
| Fogo | cicatriz do ano, anos desde o último fogo, frequência 5/10 anos | MapBiomas Fogo | Perturbação |
| Desmatamento | incremento PRODES do ano, distância à borda, alertas | PRODES/MapBiomas | Perda |
| Cobertura/transição | classe MapBiomas do ano, transição t−1→t, idade secundária | MapBiomas | Estado/ganho |
| Clima | climatologia + anomalia anual de chuva, temperatura, déficit | ERA5 | Estresse/ crescimento |
| Solo | argila, areia, carbono orgânico, profundidade | SoilGrids | Estático |
| Topografia | elevação, declividade, aspecto, posição topográfica | GLO-30 | Estático |
| Estrutura (se disponível) | altura/cobertura derivadas de S2/S1/Landsat | séries | Estado |

**Não usar no inference:** GEDI L4A/L4B, métricas GEDI, mapas de AGB de terceiros.

## 4. Arquiteturas candidatas

| ID | Arquitetura | Descrição | Testa |
|---|---|---|---|
| A0 | Baseline atual (M0) | RF estático com compósito multi-ano | Referência |
| A1 | RF anual direto | RF treinado com features do ano t | H4 |
| A2 | RF anual + histórico | A1 + transições, idade, fogo | H3 |
| A3 | Hierárquico | Efeitos parciais por bioma/fisionomia/box (mixed-effects ou Bayesian) | H1/H2 |
| A4 | Modelo de mudança | ΔAGB = f(Δfeatures, distúrbio), treinado em pares GEDI/ campo | H5 |
| A5 | Estado-espaço | AGB_t latente; processo com crescimento e perda; observação S2/S1 | H5 |
| A6 | Híbrido | A5 + A4 + restrições de transição (perda/ganho) | H5 |
| A7 | Mixture of experts | Especialistas por cluster ambiental/fisionomia, gate por ambiente | H2 |

A ordem de implementação é A0 → A1 → A2 → A3 → A4/A5 → A6. A7 só se A1–A3 indicarem ganho de
especialização.

## 5. Protocolo de avaliação

### 5.1 Divisões

- **Espacial:** leave-one-box-out (11 boxes), com boxes de teste intocados no ajuste de
  hiperparâmetros (nested CV quando houver tuning).
- **Temporal:** leave-one-year-out dentro de 2019–2023 (anos GEDI), com features do ano
  correspondente.
- **Espaço-temporal:** leave-one-box-one-year-out para checar interação; relatar separadamente.
- **Calibração local:** sempre avaliada em dois regimes: sem calibração e com 10% (curvas de
  aprendizado de 5–200 células).

### 5.2 Métricas

- Por box, por ano, por fisionomia e por classe de AGB: R², RMSE, MAE, viés, inclinação
  observado~predito e predito~observado (convenção explícita), R² após remover viés.
- Erro por quantil (especialmente > 200 Mg ha⁻¹ e < 20).
- Cobertura e largura do IC90.
- AOA: fração dentro e erro dentro/fora.
- Agregação: RMSE do total por polígono, viés agregado, IC do total.

### 5.3 Testes de mudança (obrigatórios)

Para cada evento conhecido (PRODES, MapBiomas, Fogo, regeneração), comparar ΔAGB previsto:

1. **Sinal:** proporção de células com sinal correto.
2. **Magnitude:** mediana de ΔAGB dentro do evento vs literatura (ex.: perda de floresta densa;
   ganho em regeneração por classe de idade).
3. **Contraste:** Δ dentro vs fora do evento (buffer).
4. **Falso alarme:** taxa de Δ “grande” em áreas estáveis (sem transição).
5. **Defasagem:** ano em que o modelo detecta a mudança vs ano do evento.
6. **Persistência:** se a mudança é única ou se o modelo “volta” indevidamente.
7. **Estabilidade:** distribuição de Δ em florestas maduras sem perturbação.

### 5.4 Validação independente

- **PLOS 2018:** 42 sítios no domínio; reavaliar com features anuais Landsat; testar modelo
  global vs fisionômico vs hierárquico.
- **ORNL 2009–2018:** recuperar AGB/ha via DDLS (pendente de confirmar fator/datum; ver
  `docs/39`); usar como validação e possivelmente treino.
- **IFN:** validar totais regionais, não pixels.
- **Nunca** usar os mesmos sítios para escolher modelo e reportar acurácia final.

## 6. Critérios de aceitação (provisórios, para aprovação)

Um candidato só substitui o baseline se **todos** forem atendidos:

1. **Espacial:** RMSE mediano por box não pior que A0; nenhum box pior > 5%; redução mediana de
   RMSE ≥ 15% em pelo menos metade dos boxes.
2. **Temporal (mudança):** ≥ 80% de sinal correto nos eventos de perda; ≥ 70% nos de ganho;
   mediana de |Δ| em áreas estáveis ≤ 10 Mg ha⁻¹ ano⁻¹; nenhuma tendência sistemática em áreas
   estáveis (|viés| ≤ 2 Mg ha⁻¹ ano⁻¹).
3. **Contraste:** Δ dentro do evento ≥ 3× o Δ do buffer em pelo menos 70% dos eventos.
4. **Campo:** R² ≥ 0,40 e |viés| ≤ 15% em validação independente (PLOS/ORNL) — se não houver
   campo suficiente, o candidato fica “não promovido”.
5. **Incerteza:** cobertura IC90 entre 85% e 95% por bioma/ano; largura reportada por célula e
   por polígono.
6. **Independência:** auditoria mostra zero uso de GEDI/derivados no inference.
7. **Reprodutibilidade:** pipeline do ano roda de ponta a ponta com manifesto e testes.

Não aprovar por R² médio contra GEDI. Ganho tem que ser consistente entre boxes e anos.

## 7. Experimentos e decisões

| Exp. | Hipótese | Dados | Divisão | Métrica decisiva | Decide |
|---|---|---|---|---|---|
| E0 | Reproduzir A0 | atuais | LOO | métricas atuais | Congela baseline |
| E1 | Features anuais capturam estado | S2/S1/Landsat por ano | LOO + LOYO | RMSE por box/ano | Se A1 > A0 |
| E2 | Histórico/transição melhora | + fogo/idade/PRODES | LOO + LOYO | Δ em eventos | Se A2 > A1 |
| E3 | Fisionomia categórica ajuda | taxonomia nível 1–2 | LOO | viés por fisionomia | Se A3 > A2 |
| E4 | Hierarquia supera isolados | A3 + partial pooling | LOO | RMSE/estabilidade | Se A3 > A1/A2 |
| E5 | Mudança modelada explicitamente | pares GEDI 2019–23 + eventos | LOO temporal | sinal/contraste | Se A4/A5 > A2 |
| E6 | Estado-espaço com prior assimétrico | A5 | LOYO + eventos | falso ganho/estabilidade | Se A5 > A4 |
| E7 | Calibração pode ser reduzida | curvas 5–200 células | LOO | nº de células p/ meta | Se H6 |
| E8 | Filtros/pesos GEDI mudam conclusão | GEDI bruto | LOO | sensibilidade | Robustez |
| E9 | Polígono e incerteza | células + covariância | bootstrap espacial | cobertura do total | Se incerteza defensável |

## 8. O que já é possível com os dados atuais

- E0 (baseline) e E1 parcial (2019–2024, S2/S1 disponíveis). Limitação: GEDI só 2019–2023/24;
  anos fora disso exigem campo/ORNL.
- E8 (auditoria de filtros) com os CSVs já baixados.
- E9 em 1 km com os boxes atuais (sem mapa anual completo).
- Validação PLOS com Landsat anual (2004–2014) imediatamente.

## 9. O que depende de novos dados

- **MapBiomas pré-2004** (para recuperar 25 sítios PLOS e estender a série).
- **ORNL** com fator/datum resolvidos e AGB/ha calculada (validação/treino histórico).
- **PRODES/MapBiomas Fogo/Vegetação Secundária** organizados por ano (aquisição e catálogo).
- **Solo (SoilGrids)** para o bloco de solo.
- **Campos independentes pós-2019** para validar o modelo anual na Amazônia (hoje não há).

## 10. Riscos

- **Não estacionariedade:** relações treinadas em 2019–2023 podem não valer para 2025+; mitigar
  com reavaliação anual e detecção de drift.
- **Cobertura GEDI desigual:** calibração pode ficar restrita a certas órbitas/regiões.
- **Saturação óptica:** AGB > 250 Mg ha⁻¹ continua difícil; declarar limite e usar S1/Landsat.
- **Máscara anual:** transições podem criar saltos artificiais se não houver contabilidade
  explícita.
- **Mudança real vs ruído:** prior assimétrico e testes de falso alarme são obrigatórios.
- **Dependência de MapBiomas:** erro de classificação propaga; quantificar.
